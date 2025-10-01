#!/usr/bin/env python3
"""
Brand Analyzer - Utility Functions
Core helper functions for brand analysis
"""

import json
import re
import os
from urllib.parse import urlparse
import tiktoken

from transformers import pipeline

# Load once at module import
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def hf_summarize(text: str, ratio: float = 0.3, min_length: int = 20) -> str:
    """
    Summarize text with Hugging Face (BART) using ratio control.
    ratio: fraction of original words/tokens to keep (0.0 - 1.0).
    min_length: minimum tokens in the summary.
    """
    if not text.strip():
        return ""

    # Approximate token length by word count
    orig_len = len(text.split())
    target_len = max(min_length, int(orig_len * ratio))

    # Hugging Face wants max_length, min_length in tokens (approx. words)
    result = summarizer(
        text,
        max_length=target_len,
        min_length=min_length,
        do_sample=False
    )
    return result[0]["summary_text"]


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

def base_create_prompt(brand_name: str, website_url: str, question: str, max_searches: int, max_sources: int) -> str:
    """
    Create a prompt for brand analysis 
    """
    # Start with the full prompt
    prompt = f"""

Please provide a comprehensive, accurate answer about the brand. 
Include relevant citations with markdown links [text](url) when referencing sources.


IMPORTANT CONSTRAINTS:
- You have a maximum of {max_searches} web searches available (unique domains)
- You can include at most {max_sources} unique sources (urls) in your response
- Use web search to find current, accurate information
- These limits CANNOT be exceeded under any circumstances
- If needed summarize the information to fit the limits.

Brand Information:
- Brand Name: {brand_name}
- Website: {website_url}

Question: {question}

Answer:"""
    
    # Fallback to original prompt if tokenizers not available
    return prompt



# def create_prompt(brand_name: str, website_url: str, question: str, max_searches: int, max_sources: int) -> str:
#     """
#     Create an optimized prompt for brand analysis 
#     """
#     prompt = f"""

# Give an accurate answer. Cite sources as [text](url). Do not exceed budgets.

# CONSTRAINTS
# - Max web searches: {max_searches}
# - Max sources: {max_sources}

# FORMAT
# - Write in plain markdown.
# - Include citations inline next to claims.

# Brand: {brand_name}
# Website: {website_url}
# Question: {question}

# Answer:"""
#     return prompt


# def create_prompt(
#     brand_name: str,
#     website_url: str,
#     question: str,
#     max_searches: int,
#     max_sources: int,
#     *,
#     question_token_threshold: int = 10,   # if question exceeds this, compress it
#     question_ratio: float = 0.6           # how aggressively to compress when needed
# ) -> str:
#     """
#     Hierarchical prompt:
#       - If question tokens <= threshold: use question verbatim.
#       - Else: compress the *question* with Hugging Face.
#     """
#     q_tokens = count_tokens(question)
#     print("q_tokens: ", q_tokens)
#     final_question = question
    

#     if q_tokens > question_token_threshold:
#         try:
#             final_question = hf_summarize(question, ratio=question_ratio)
#             if count_tokens(final_question) < q_tokens:
#                 print('Hr worked')
#                 print("final_question: ", final_question)
#         except Exception as e:
#             print(f"⚠️ Compression failed: {e}")
#             final_question = question

#     prompt = f"""
# Give an accurate answer. Cite sources as [text](url). Do not exceed budgets.

# CONSTRAINTS
# - Max web searches: {max_searches}
# - Max sources: {max_sources}

# FORMAT
# - Write in plain markdown.
# - Include citations inline next to claims.

# Brand: {brand_name}
# Website: {website_url}
# Question: {final_question}

# Answer:""".strip()

#     return prompt


import re

def _preserve_tail_two_sentences(text: str):
    """
    Returns (head, tail) where tail = [sentence_before_question + question_sentence]
    If no question is found, returns (text, "").
    """
    sentences = re.split(r'(?<=[.?!])\s+', (text or "").strip())
    if not sentences:
        return text, ""

    # Find the last sentence ending with '?'
    q_idx = None
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].strip().endswith("?"):
            q_idx = i
            break

    if q_idx is None:
        # No question mark at all
        return text, ""

    start_idx = max(0, q_idx - 1)  # preserve the question and one sentence before it
    head = " ".join(sentences[:start_idx]).strip()
    tail = " ".join(sentences[start_idx:q_idx + 1]).strip()
    return head, tail


def create_prompt(
    brand_name: str,
    website_url: str,
    question: str,
    max_searches: int,
    max_sources: int,
    *,
    question_token_threshold: int = 120,  # if question exceeds this, compress it
    question_ratio: float = 0.4           # how aggressively to compress when needed
) -> str:
    """
    Hierarchical prompt:
      - If the text contains a final question (ends with '?'), preserve the question
        and the sentence immediately before it; summarize only the earlier background.
      - If no '?' is present and tokens exceed threshold, summarize the whole text.
    """
    q_tokens = count_tokens(question)
    print("q_tokens:", q_tokens)

    head, tail = _preserve_tail_two_sentences(question)
    if tail:  # we found a question to preserve
        # If the background (head) is long, summarize it; otherwise keep as-is
        if count_tokens(head) > question_token_threshold:
            try:
                compressed_head = hf_summarize(head, ratio=question_ratio)
                if count_tokens(compressed_head) < count_tokens(head):
                    print("HF worked on head (background).")
            except Exception as e:
                print(f"⚠️ Compression failed on head: {e}")
                compressed_head = head
        else:
            compressed_head = head

        final_question_text = (compressed_head.strip() + " " if compressed_head else "") + tail
    else:
        # No explicit question found: fall back to your original threshold logic
        if q_tokens > question_token_threshold:
            try:
                compressed_all = hf_summarize(question, ratio=question_ratio)
                if count_tokens(compressed_all) < q_tokens:
                    print("HF worked on full text.")
                final_question_text = compressed_all
            except Exception as e:
                print(f"⚠️ Compression failed on full text: {e}")
                final_question_text = question
        else:
            final_question_text = question
    print("final_question_text: ", final_question_text)
    prompt = f"""
Give an accurate answer. Cite sources as [text](url). Do not exceed budgets.

CONSTRAINTS
- Max web searches: {max_searches}
- Max sources: {max_sources}

FORMAT
- Write in plain markdown.
- Include citations inline next to claims.

Brand: {brand_name}
Website: {website_url}
Question: {final_question_text}

Answer:""".strip()

    return prompt



def generate_llm_response(prompt: str, brand_name: str) -> str:
    """
    Generate LLM response using OpenAI API
    """
    from openai import OpenAI
    
    client = OpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "nousresearch/hermes-2-pro-llama-3-8b"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions about brands and companies."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=int(os.getenv("MAX_TOKENS", 4000)),
            temperature=0.7
        )
        
        return response.choices[0].message.content
            
    except Exception as e:
        # Let the error propagate so we can see actual failures
        raise Exception(f"Model call failed for {brand_name}: {str(e)}")

def extract_citations(response_text: str) -> list:
    """
    Extract citations from response text - ALL unique URLs
    
    Patterns to capture:
    1. [text](url) - markdown links  
    2. source[...] patterns
    3. Brand[url] patterns
    4. Plain URLs
    """
    citations = []
    found_urls = set()

    # Pattern 1: [text](url) - markdown links (priority)
    pattern1 = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(pattern1, response_text):
        text = match.group(1).strip()
        url = match.group(2).strip()

        if url.startswith(('http://', 'https://')) and url not in found_urls:
            citations.append({
                "text": text,
                "url": url,
                "type": "markdown_link"
            })
            found_urls.add(url)

    # Pattern 2: source[...] patterns (case insensitive)
    pattern2 = r'(?:Source|source)\[([^\]]+)\]'
    for match in re.finditer(pattern2, response_text, re.IGNORECASE):
        url = match.group(1).strip()
        
        if url.startswith(('http://', 'https://')) and url not in found_urls:
            citations.append({
                "text": f"Source: {url[:50]}...",
                "url": url,
                "type": "source_pattern"
            })
            found_urls.add(url)

    # Pattern 3: text[url] patterns (any text attached to URL in brackets)
    # This captures patterns like "textattachedtothis[url]", "Brand[url]", etc.
    pattern3 = r'(\w+(?:\s+\w+)*)\[([^\]]+)\]'
    for match in re.finditer(pattern3, response_text):
        text = match.group(1).strip()
        url = match.group(2).strip()
        
        if url.startswith(('http://', 'https://')) and url not in found_urls:
            citations.append({
                "text": text,
                "url": url,
                "type": "text_url_pattern"
            })
            found_urls.add(url)

    # Pattern 4: Plain URLs (only if not already found)
    # Remove all previously captured patterns
    text_cleaned = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', response_text)
    text_cleaned = re.sub(r'(?:Source|source)\[([^\]]+)\]', '', text_cleaned, flags=re.IGNORECASE)
    text_cleaned = re.sub(r'\w+(?:\s+\w+)*\[([^\]]+)\]', '', text_cleaned)
    
    pattern4 = r'https?://[^\s\)]+'
    for match in re.finditer(pattern4, text_cleaned):
        url = match.group().rstrip('.,;!?)')
        
        if url not in found_urls and url.startswith(('http://', 'https://')):
            citations.append({
                "text": f"Source: {url[:50]}...",
                "url": url,
                "type": "plain_url"
            })
            found_urls.add(url)

    return citations

def extract_mentions(response_text: str, brand_name: str) -> list:
    """
    Extract brand mentions from response text, handling various patterns:
    1. Brand[url] patterns (attached link, not within URL)
    2. Brand name standalone (case insensitive)
    3. Brand name possessive (Tesla's, tesla's, etc.)
    """
    mentions = []
    linked_positions = set()
    
    # Pattern 1: Brand[url] patterns (attached link, not within URL)
    # This captures Tesla[https://url], Tesla[https://url], etc.
    pattern1 = r'\b' + re.escape(brand_name) + r'\b\[([^\]]+)\]'
    for match in re.finditer(pattern1, response_text, re.IGNORECASE):
        url = match.group(1).strip()
        start, end = match.span()
        mentions.append({
            "text": brand_name,
            "url": url,
            "type": "linked",
            "start": start,
            "end": end
        })
        linked_positions.update(range(start, end))
    
    # Pattern 2: [Brand](url) - markdown link (exact brand name only)
    pattern2 = r'\[' + re.escape(brand_name) + r'\]\(([^)]+)\)'
    for match in re.finditer(pattern2, response_text, re.IGNORECASE):
        url = match.group(1).strip()
        start, end = match.span()
        mentions.append({
            "text": brand_name,
            "url": url,
            "type": "linked",
            "start": start,
            "end": end
        })
        linked_positions.update(range(start, end))
    
    # Pattern 3: Brand variations with [url] (handle spaces, underscores, etc.)
    brand_variations = [
        brand_name.replace(' ', '_'),
        brand_name.replace(' ', '-'),
        brand_name.replace('_', ' '),
        brand_name.replace('-', ' ')
    ]
    
    for variation in brand_variations:
        if variation != brand_name:
            pattern3 = r'\b' + re.escape(variation) + r'\b\[([^\]]+)\]'
            for match in re.finditer(pattern3, response_text, re.IGNORECASE):
                url = match.group(1).strip()
                start, end = match.span()
                mentions.append({
                    "text": variation,
                    "url": url,
                    "type": "linked",
                    "start": start,
                    "end": end
                })
                linked_positions.update(range(start, end))
    
    # Pattern 4: Simple brand mentions (unlinked) - including possessive forms
    # Match both "Brand" and "Brand's" - but exclude those inside URLs
    patterns_unlinked = [
        r'\b' + re.escape(brand_name) + r'\b',  # Exact brand name
        r'\b' + re.escape(brand_name) + r"'s\b"  # Brand's possessive
    ]
    
    for pattern in patterns_unlinked:
        for match in re.finditer(pattern, response_text, re.IGNORECASE):
            start, end = match.span()
            
            # Check if this position is already captured as linked
            if not any(pos in linked_positions for pos in range(start, end)):
                # Check if this mention is inside a URL (exclude URLs)
                is_in_url = False
                context_start = max(0, start - 50)
                context_end = min(len(response_text), end + 50)
                context = response_text[context_start:context_end]
                
                # Look for URL patterns around this position
                url_patterns = [
                    r'https?://[^\s]+',
                    r'www\.[^\s]+',
                    r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*'
                ]
                
                for url_pattern in url_patterns:
                    for url_match in re.finditer(url_pattern, context, re.IGNORECASE):
                        url_start = context_start + url_match.start()
                        url_end = context_start + url_match.end()
                        if url_start <= start <= url_end:
                            is_in_url = True
                            break
                    if is_in_url:
                        break
                
                if not is_in_url:
                    mentions.append({
                        "text": match.group(),
                        "type": "unlinked",
                        "start": start,
                        "end": end
                    })
    
    return mentions

def classify_sources(citations: list, brand_url: str) -> tuple:
    """
    Classify sources as owned (by the brand) or external
    Returns unique sources (deduplicated) for owned_sources and external_sources
    """
    try:
        brand_domain = urlparse(brand_url).netloc.lower()
        # Remove 'www.' prefix for comparison
        brand_domain_clean = brand_domain.replace('www.', '')
    except ValueError:
        # Handle invalid URLs
        brand_domain_clean = ""
    
    owned_sources = []
    external_sources = []
    owned_urls = set()
    external_urls = set()
    
    for citation in citations:
        try:
            citation_domain = urlparse(citation["url"]).netloc.lower()
            # Remove 'www.' prefix for comparison
            citation_domain_clean = citation_domain.replace('www.', '')
            
            # Check if domains match (ignoring www prefix and subdomains)
            if citation_domain_clean == brand_domain_clean or citation_domain_clean.endswith('.' + brand_domain_clean):
                if citation["url"] not in owned_urls:
                    owned_sources.append(citation["url"])
                    owned_urls.add(citation["url"])
            else:
                if citation["url"] not in external_urls:
                    external_sources.append(citation["url"])
                    external_urls.add(citation["url"])
        except ValueError:
            # Handle invalid URLs
            if citation["url"] not in external_urls:
                external_sources.append(citation["url"])
                external_urls.add(citation["url"])
    
    return owned_sources, external_sources

def parse_search_usage_from_response(response_text: str, max_searches: int, max_sources: int) -> dict:
    """
    Parse search usage information from response text
    
    Definitions:
    - Citations: Any mention of entities that include URLs
    - Searches: Unique domains (each unique domain = 1 search)
    - Sources: Unique URLs (each unique URL = 1 source)
    """
    from urllib.parse import urlparse
    
    # Extract all citations (URLs mentioned in the response)
    citations = extract_citations(response_text)
    
    # Count unique sources (unique URLs)
    unique_urls = set(citation["url"] for citation in citations)
    sources_used = len(unique_urls)
    
    # Count unique domains (searches)
    unique_domains = set()
    for url in unique_urls:
        try:
            domain = urlparse(url).netloc.lower()
            # Remove 'www.' prefix for domain counting
            domain_clean = domain.replace('www.', '')
            unique_domains.add(domain_clean)
        except ValueError:
            # Handle invalid URLs
            continue
    
    searches_used = len(unique_domains)
    
    return {
        "max_searches": max_searches,
        "max_sources": max_sources,
        "searches_used": searches_used,
        "sources_used": sources_used,
        "unique_sources": sources_used,  # Same as sources_used
        "unique_domains": list(unique_domains),  # For debugging
        "searches_remaining": max_searches - searches_used,
        "sources_remaining": max_sources - sources_used,
        "budget_respected": searches_used <= max_searches and sources_used <= max_sources,
        "search_efficiency": sources_used / max(searches_used, 1),
        "search_method": "domain_based_counting"
    }