#!/usr/bin/env python3
"""
Brand Analyzer - CLI Tool for Brand Analysis
Comprehensive brand analysis using LLM-powered web search
"""

import click
import json
import os
from dotenv import load_dotenv
import sys
sys.path.append('.')
from utils import (
    count_tokens, generate_llm_response, create_prompt,
    extract_citations, extract_mentions, classify_sources,
    parse_search_usage_from_response
)

# Load environment variables
load_dotenv()

# Using optimized create_prompt from utils.py for better token efficiency

@click.group()
@click.version_option(version='1.0.0', prog_name='brand-analyzer')
def cli():
    """
    Brand Analyzer - Comprehensive brand analysis using LLM-powered web search
    
    Analyze brands and companies with intelligent web search capabilities,
    automatic citation extraction, and detailed performance metrics.
    """
    pass

@cli.command()
@click.option('--brand', required=True, help='Brand name to analyze')
@click.option('--url', required=True, help='Brand website URL')
@click.option('--question', required=True, help='Question to ask about the brand')
@click.option('--max-searches', default=3, help='Maximum number of web searches (default: 5)')
@click.option('--max-sources', default=6, help='Maximum number of sources to include (default: 10)')
@click.option('--output', default='output/output.json', help='Output file for results (default: output/output.json)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed analysis metrics')
def analyze(brand, url, question, max_searches, max_sources, output, verbose):
    """
    Analyze a brand with comprehensive web search and citation extraction.
    
    Examples:
        brand-analyzer analyze --brand "Tesla" --url "https://tesla.com" --question "What are Tesla's latest innovations?"
        brand-analyzer analyze --brand "Google" --url "https://google.com" --question "Tell me about Google's AI initiatives" --max-searches 8 --max-sources 15
    """
    click.echo(f"🔍 Analyzing {brand}...")

    # Step 1: Create prompt using the optimized create_prompt function from utils
    prompt = create_prompt(brand, url, question, max_searches, max_sources)
    
    # Step 2: Generate LLM response
    with click.progressbar(length=1, label='Generating response') as bar:
        response = generate_llm_response(prompt, brand)
        bar.update(1)
    
    # Step 3: Extract and analyze response
    click.echo("📊 Analyzing response...")
    citations = extract_citations(response)
    mentions = extract_mentions(response, brand)
    owned_sources, external_sources = classify_sources(citations, url)
    search_stats = parse_search_usage_from_response(response, max_searches, max_sources)
    
    # Count linked vs unlinked mentions
    linked_mentions = [m for m in mentions if m.get('type') == 'linked']
    unlinked_mentions = [m for m in mentions if m.get('type') == 'unlinked']
    
    # Calculate token counts
    input_tokens = count_tokens(prompt)
    output_tokens = count_tokens(response)
    total_tokens = input_tokens + output_tokens
    
    # Step 4: Create optimized JSON output and save it
    all_sources = owned_sources + external_sources
    
    result = {
        "human_response_markdown": response,
        "citations": citations,
        "mentions": mentions,
        "sources": external_sources,  # External sources only
        "owned_sources": owned_sources,  # Owned sources only
        "metadata": {
            "brand_name": brand,
            "website_url": url,
            "question": question,
            "token_counts": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            },
            "totals": {
                "citations": len(citations),
                "mentions": {
                    "total": len(mentions),
                    "linked": len(linked_mentions),
                    "unlinked": len(unlinked_mentions)
                },
                "sources": len(external_sources),
                "owned_sources": len(owned_sources),
                "searches_used": search_stats['searches_used'],
                "max_searches": search_stats['max_searches'],
                "max_sources": search_stats['max_sources'],
                "budget_respected": search_stats['budget_respected']
            }
        }
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    # Save to JSON file (append to list)
    try:
        with open(output, 'r', encoding='utf-8') as f:
            existing_results = json.load(f)
        if not isinstance(existing_results, list):
            existing_results = [existing_results]
    except (FileNotFoundError, json.JSONDecodeError):
        existing_results = []
    
    existing_results.append(result)
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(existing_results, f, indent=2, ensure_ascii=False)
    
    # Display results
    click.echo(f"✅ Analysis complete! Results saved to {output}")
    
    if verbose:
        click.echo("\n📈 Analysis Summary:")
        click.echo(f"  Citations: {len(citations)}")
        click.echo(f"  Mentions: {len(mentions)} ({len(linked_mentions)} linked, {len(unlinked_mentions)} unlinked)")
        click.echo(f"  Sources: {len(external_sources)}")
        click.echo(f"  Owned Sources: {len(owned_sources)}")
        click.echo(f"  Searches Used: {search_stats['searches_used']}/{search_stats['max_searches']}")
        click.echo(f"  Tokens: {total_tokens} total ({input_tokens} input, {output_tokens} output)")
        click.echo(f"  Budget Compliance: {'✅ PASSED' if search_stats['budget_respected'] else '❌ FAILED'}")
    
    # Display the response
    click.echo(f"\n📝 Response for {brand}:")
    click.echo("=" * 50)
    click.echo(response)

@cli.command()
@click.option('--file', default='output/output.json', help='JSON file to analyze (default: output/output.json)')
def stats(file):
    """
    Show statistics from previous analyses.
    
    Examples:
        brand-analyzer stats
        brand-analyzer stats --file my_analyses.json
    """
    try:
        with open(file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        if not isinstance(results, list):
            results = [results]
        
        click.echo(f"📊 Analysis Statistics from {file}")
        click.echo("=" * 50)
        
        total_analyses = len(results)
        total_citations = sum(r.get('metadata', {}).get('totals', {}).get('citations', 0) for r in results)
        total_mentions = sum(r.get('metadata', {}).get('totals', {}).get('mentions', {}).get('total', 0) for r in results)
        total_tokens = sum(r.get('metadata', {}).get('token_counts', {}).get('total_tokens', 0) for r in results)
        
        click.echo(f"Total Analyses: {total_analyses}")
        click.echo(f"Total Citations: {total_citations}")
        click.echo(f"Total Mentions: {total_mentions}")
        click.echo(f"Total Tokens: {total_tokens}")
        
        if total_analyses > 0:
            click.echo(f"Average Citations per Analysis: {total_citations / total_analyses:.1f}")
            click.echo(f"Average Mentions per Analysis: {total_mentions / total_analyses:.1f}")
            click.echo(f"Average Tokens per Analysis: {total_tokens / total_analyses:.0f}")
        
        # Show recent analyses
        click.echo(f"\n📋 Recent Analyses:")
        for i, result in enumerate(results[-5:], 1):  # Show last 5
            brand = result.get('metadata', {}).get('brand_name', 'Unknown')
            question = result.get('metadata', {}).get('question', 'Unknown')[:50] + "..."
            citations = result.get('metadata', {}).get('totals', {}).get('citations', 0)
            click.echo(f"  {i}. {brand}: {question} ({citations} citations)")
            
    except FileNotFoundError:
        click.echo(f"❌ File {file} not found. Run some analyses first!")
    except json.JSONDecodeError:
        click.echo(f"❌ Invalid JSON in {file}")

@cli.command()
def config():
    """
    Show current configuration and environment setup.
    """
    click.echo("⚙️  Brand Analyzer Configuration")
    click.echo("=" * 40)
    
    # Check environment variables
    model_name = os.getenv('MODEL_NAME', 'Not set')
    api_key_set = bool(os.getenv('OPENAI_API_KEY'))
    base_url = os.getenv('OPENROUTER_BASE_URL', 'Not set')
    max_tokens = os.getenv('MAX_TOKENS', 'Not set')
    
    click.echo(f"Model: {model_name}")
    click.echo(f"API Key: {'✅ Set' if api_key_set else '❌ Not set'}")
    click.echo(f"Base URL: {base_url}")
    click.echo(f"Max Tokens: {max_tokens}")
    
    if not api_key_set:
        click.echo("\n⚠️  Warning: OPENAI_API_KEY not set. Please configure your .env file.")

def main():
    """Main entry point for the CLI"""
    cli()

if __name__ == "__main__":
    main()
