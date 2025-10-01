import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv




# Load environment variables
load_dotenv()

# Add project root to path (go up 3 levels: scripts -> evaluation -> brand_analzyer)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add src directory to path
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from utils import (
    base_create_prompt, generate_llm_response, extract_citations, 
    extract_mentions, classify_sources, parse_search_usage_from_response,
    count_tokens
)
from compressor.semantic import compress_text




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



def test_prompt_variations():
    """Test 3 different prompt variations and measure effectiveness"""
    
    # Load test inputs
    test_inputs_path = Path(__file__).parent / "test_inputs.json"
    
    try:
        with open(test_inputs_path, 'r') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print(f"❌ Test inputs file not found: {test_inputs_path}")
        return
    
    print("🚀 Token Optimization Test Suite")
    print("=" * 60)
    print(f"📋 Found {len(test_cases)} test cases")
    print("🎯 Running ALL test cases")
 
    all_results = []
    all_prompt_answers = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['brand']}")
        print("=" * 40)
        print(f"Brand: {test_case['brand']}")
        print(f"URL: {test_case['url']}")
        print(f"Question: {test_case['question']}")
        print(f"Max searches: {test_case['max_searches']}")
        print(f"Max sources: {test_case['max_sources']}")
        
        brand_name = test_case['brand']
        website_url = test_case['url']
        question = test_case['question']
        max_searches = test_case['max_searches']
        max_sources = test_case['max_sources']
        
        # Create 3 prompt variations
        prompt_1 = base_create_prompt(brand_name, website_url, question, max_searches, max_sources)
        
        prompt_2 = f"""

                    Give an accurate answer. Cite sources as [text](url). Do not exceed budgets.

                    CONSTRAINTS
                    - Max web searches: {max_searches}
                    - Max sources: {max_sources}

                    FORMAT
                    - Write in plain markdown.
                    - Include citations inline next to claims.

                    Brand: {brand_name}
                    Website: {website_url}
                    Question: {question}

                    Answer:"""
        
        try:
            # question_compressed = compress_text(question, compression_rate=0.4)
            # prompt_3 = base_create_prompt(brand_name, website_url, question_compressed, max_searches, max_sources)
            question_compressed = hf_summarize(question, 0.2)
            prompt_3 = base_create_prompt(brand_name, website_url, question_compressed, max_searches, max_sources)
                # Compress the FULL prompt
        except Exception as e:
            print(f"Warning: Compression failed: {e}")
          
        
        # Test each variation
        variations = [
            ("Original Prompt", prompt_1),
            ("Optimized Prompt", prompt_2),
            ("Compressed Prompt", prompt_3)
        ]
        
        case_results = []
        
        for variation_name, prompt in variations:
            print(f"\n🧪 Testing {variation_name}")
            print("-" * 30)
            
            try:
                # Generate response using utils function
                response = generate_llm_response(prompt, brand_name)
                
                # Extract metrics using utils functions
                citations = extract_citations(response)
                mentions = extract_mentions(response, brand_name)
                owned_sources, external_sources = classify_sources(citations, website_url)
                search_stats = parse_search_usage_from_response(response, max_searches, max_sources)
                
                # Count tokens
                input_tokens = count_tokens(prompt)
                output_tokens = count_tokens(response)
                total_tokens = input_tokens + output_tokens
                
                # Calculate metrics
                unique_sources = len(set(citation["url"] for citation in citations))
                linked_mentions = [m for m in mentions if m.get('type') == 'linked']
                unlinked_mentions = [m for m in mentions if m.get('type') == 'unlinked']
                
                # Fidelity metrics
                token_efficiency = output_tokens / input_tokens if input_tokens > 0 else 0
                
                metrics = {
                    "variation": variation_name,
                    "response_length": len(response),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "token_efficiency": token_efficiency,
                    "citations_count": len(citations),  # Total citations found
                    "unique_sources": search_stats['sources_used'],  # Unique URLs (sources)
                    "searches_used": search_stats['searches_used'],  # Unique domains (searches)
                    "owned_sources": len(owned_sources),
                    "external_sources": len(external_sources),
                    "mentions_total": len(mentions),
                    "mentions_linked": len(linked_mentions),
                    "mentions_unlinked": len(unlinked_mentions),
                    "search_budget": search_stats,
                    "type": test_case.get("type", "short")
                }
                
                # Save prompt and response separately
                prompt_answer_data = {
                    "test_case": test_case,
                    "variation": variation_name,
                    "prompt": prompt,
                    "answer": response
                }
                
                # Print results
                print(f"✅ Response generated")
                print(f"📊 Metrics:")
                print(f"   Response length: {metrics['response_length']} chars")
                print(f"   Tokens: {metrics['input_tokens']} input + {metrics['output_tokens']} output = {metrics['total_tokens']} total")
                print(f"   Token efficiency: {metrics['token_efficiency']:.2f} (output/input)")
                print(f"   Citations: {metrics['citations_count']} total, {metrics['unique_sources']} unique sources")
                print(f"   Searches: {metrics['searches_used']}/{max_searches} unique domains")
                print(f"   Source breakdown: {metrics['owned_sources']} owned, {metrics['external_sources']} external")
                print(f"   Mentions: {metrics['mentions_total']} ({metrics['mentions_linked']} linked, {metrics['mentions_unlinked']} unlinked)")
                print(f"   Budget compliance: {'✅ PASSED' if search_stats['budget_respected'] else '❌ FAILED'}")
                
                case_results.append(metrics)
                all_prompt_answers.append(prompt_answer_data)
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                case_results.append({
                    "variation": variation_name,
                    "error": str(e),
                    "response_length": 0,
                    "total_tokens": 0,
                    "citations_count": 0,
                    "owned_sources": 0,
                    "external_sources": 0,
                    "mentions_total": 0,
                    "mentions_linked": 0,
                    "mentions_unlinked": 0,
                    "search_budget": {},
                    "type": test_case.get("type", "short")
                })
        
        all_results.append({
            "test_case": test_case,
            "results": case_results
        })
    
    # Generate summary report
    print(f"\n📊 SUMMARY REPORT")
    print("=" * 60)
    
    for i, test_result in enumerate(all_results, 1):
        print(f"\n🔍 Test Case {i}: {test_result['test_case']['brand']}")
        print("-" * 40)
        
        for result in test_result['results']:
            if 'error' in result:
                print(f"❌ {result['variation']}: ERROR - {result['error']}")
            else:
                print(f"✅ {result['variation']}:")
                print(f"   Tokens: {result['total_tokens']}")
                print(f"   Citations: {result['citations_count']} total, {result['unique_sources']} unique sources")
                print(f"   Searches: {result['searches_used']} unique domains")
                print(f"   Mentions: {result['mentions_total']}")
    
    # Save detailed results (append to existing file)
    results_file = Path(__file__).parent / "token_optimization_results.json"
    
    # Load existing results if file exists
    existing_results = []
    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                existing_results = json.load(f)
        except:
            existing_results = []
    
    # Append new results
    existing_results.extend(all_results)
    
    # Save combined results
    with open(results_file, 'w') as f:
        json.dump(existing_results, f, indent=2)
    
    # Save prompt/answer data separately
    prompt_answer_file = Path(__file__).parent / "prompt_answer_data.json"
    with open(prompt_answer_file, 'w') as f:
        json.dump(all_prompt_answers, f, indent=2)
    
    print(f"\n💾 Detailed results appended to: {results_file}")
    print(f"💾 Prompt/Answer data saved to: {prompt_answer_file}")
    print(f"📊 Total test cases in file: {len(existing_results)}")
    print(f"📊 Total prompt/answer pairs: {len(all_prompt_answers)}")

if __name__ == "__main__":
    test_prompt_variations()
   
    

    


