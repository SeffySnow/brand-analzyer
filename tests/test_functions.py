#!/usr/bin/env python3
"""
Test file to evaluate mention detection and citation extraction functions
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils import extract_citations, extract_mentions, classify_sources, parse_search_usage_from_response

def test_functions():
    """Test the mention detection and citation extraction functions"""
    
    print("🧪 Testing Mention Detection and Citation Extraction")
    print("=" * 60)
    
    # Sample long text with various mention patterns and citations
    sample_text = """
    Tesla's latest innovations in electric vehicles have reshaped industry expectations. Founded by Elon Musk, **[Tesla](https://www.tesla.com)** continues to push boundaries in powertrain efficiency, safety software, and manufacturing scale (Source[https://www.tesla.com/about]). Tesla's commitment to innovation drives the entire industry forward.

**Model S Plaid.** The Model S Plaid delivers sub-2s 0–60 mph performance with a tri-motor setup and high-efficiency thermal management — details are outlined here: Source[https://www.tesla.com/models/plaid]. For an external perspective, see engineering notes compiled after launch (source[https://www.caranddriver.com/tesla-model-s-plaid/]) and comparative testing by independent reviewers (source[https://www.motortrend.com/reviews/tesla-model-s-plaid-test/]). Note: some reviewers cite differences in rollout assumptions; see discussion (source[https://www.sae.org/news/2021/sae-j2990-rollout-standards]).

**Cybertruck.** The **Tesla[https://www.tesla.com/cybertruck]** design combines an exoskeleton body and 48V low-voltage architecture; early owner documentation and delivery event recaps: source[https://www.reuters.com/markets/companies/tesla-cybertruck-deliveries-2023-11-30/]. Additional specs appear in official FAQs (source[https://www.tesla.com/support/cybertruck-faq]) and teardown snippets (source[https://www.teslarati.com/tesla-cybertruck-teardown/]).  
 https://shop.tesla.com/category/cybertruck?variant=toolbox.

**Energy & Storage.** Residential **Tesla Solar Roof** integrates textured glass tiles with Powerwall buffering (Source[https://www.tesla.com/solarroof]; Source[https://www.tesla.com/powerwall]). For grid-scale projects, **Megapack** sits here: source[https://www.tesla.com/megapack]. External reporting on utility deployments: source[https://www.bloomberg.com/news/articles/2023-08-30/tesla-megapack-utility-storage-growth] and market context from IEA (source[https://www.iea.org/reports/grid-scale-storage]).

**Autopilot & FSD.** Tesla’s driver-assistance stack (vision networks, planner, OTA cadence) is documented at **Tesla[https://www.tesla.com/autopilot]** with expanded notes on supervised FSD Beta (source[https://www.tesla.com/support/full-self-driving-capability]). Regulatory and safety context: NHTSA resources (source[https://www.nhtsa.gov/vehicle-manufacturers/automated-driving-systems]) and a neutral overview (source[https://en.wikipedia.org/wiki/Tesla_Autopilot#Full_Self-Driving]).  
Edge case with anchors & query params: Source[https://www.tesla.com/support/full-self-driving-capability#beta?ref=docs&utm_source=nav].

**Charging.** The Supercharger network enables reliable long-distance travel: Source[https://www.tesla.com/supercharger]. Third-party coverage of NACS adoption: source[https://www.nytimes.com/2023/06/09/business/energy-environment/tesla-charging-ford-gm.html] and standardization notes (source[https://www.sae.org/news/2023/10/sae-adopts-nacs]).

**Manufacturing.** Giga-castings, structural battery packs, and dry-electrode coating are frequently cited as cost and throughput levers (source[https://www.tesla.com/blog/battery-day-highlights]). Independent coverage: source[https://www.ft.com/content/tesla-battery-day-manufacturing] (paywall), plus teardown-focused analysis (source[https://munrolive.com/]).

A quick plain-URL line (simple case): https://www.tesla.com/news  
Another plain URL with trailing punctuation for parser robustness: https://www.tesla.com/impact-report-2023.

---

### Compact “Sources & References” roundup (mixed styles)
- [Tesla Model S Plaid](https://www.tesla.com/models/plaid)  
- Tesla[https://www.tesla.com/cybertruck]  
- Source[https://www.tesla.com/solarroof] • Source[https://www.tesla.com/powerwall] • Source[https://www.tesla.com/megapack]  
- source[https://www.nhtsa.gov/vehicle-manufacturers/automated-driving-systems]  
- source[https://www.nytimes.com/2023/06/09/business/energy-environment/tesla-charging-ford-gm.html]
- source[https://www.sae.org/news/2023/10/sae-adopts-nacs]  
- [Autopilot Overview](https://www.tesla.com/autopilot)  
- Plain URL (owned): https://www.tesla.com/about


"""


    
    brand_name = "Tesla"
    brand_url = "https://www.tesla.com"
    max_searches = 5
    max_sources = 8
    
    print(f"Brand: {brand_name}")
    print(f"Brand URL: {brand_url}")
    print(f"Sample text length: {len(sample_text)} characters")
    print()
    
    # Test citation extraction
    print("📝 Testing Citation Extraction:")
    print("-" * 40)
    citations = extract_citations(sample_text)
    print(f"Total citations found: {len(citations)}")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. [{citation['type']}] {citation['text']} -> {citation['url']}")
    print()
    
    # Test mention extraction
    print("🔗 Testing Mention Extraction:")
    print("-" * 40)
    mentions = extract_mentions(sample_text, brand_name)
    linked_mentions = [m for m in mentions if m.get('type') == 'linked']
    unlinked_mentions = [m for m in mentions if m.get('type') == 'unlinked']
    
    print(f"Total mentions found: {len(mentions)}")
    print(f"Linked mentions: {len(linked_mentions)}")
    print(f"Unlinked mentions: {len(unlinked_mentions)}")
    print()
    
    print("Linked mentions:")
    for i, mention in enumerate(linked_mentions, 1):
        print(f"  {i}. {mention['text']} -> {mention.get('url', 'N/A')}")
    print()
    
    print("Unlinked mentions:")
    for i, mention in enumerate(unlinked_mentions, 1):
        print(f"  {i}. '{mention['text']}' (pos: {mention['start']}-{mention['end']})")
    print()
    
    # Test source classification
    print("🏢 Testing Source Classification:")
    print("-" * 40)
    owned_sources, external_sources = classify_sources(citations, brand_url)
    print(f"Owned sources: {len(owned_sources)}")
    for i, source in enumerate(owned_sources, 1):
        print(f"  {i}. {source}")
    print()
    print(f"External sources: {len(external_sources)}")
    for i, source in enumerate(external_sources, 1):
        print(f"  {i}. {source}")
    print()
    
    # Test search usage parsing
    print("📊 Testing Search Usage Parsing:")
    print("-" * 40)
    search_stats = parse_search_usage_from_response(sample_text, max_searches, max_sources)
    print(f"Searches used: {search_stats['searches_used']}/{search_stats['max_searches']}")
    print(f"Sources used: {search_stats['sources_used']}/{search_stats['max_sources']}")
    print(f"Unique domains: {search_stats['unique_domains']}")
    print(f"Budget respected: {search_stats['budget_respected']}")
    print(f"Search efficiency: {search_stats['search_efficiency']:.2f} sources per search")
    print()
    
    # Test case sensitivity
    print("🔤 Testing Case Sensitivity:")
    print("-" * 40)
    test_cases = ["Tesla", "tesla", "TESLA", "Tesla's", "tesla's", "TESLA'S"]
    for test_case in test_cases:
        test_mentions = extract_mentions(sample_text, test_case)
        print(f"Brand '{test_case}': {len(test_mentions)} mentions found")
    print()
    
    # Summary
    print("📋 Summary:")
    print("-" * 40)
    print(f"✅ Citations: {len(citations)} (should be 8)")
    print(f"✅ Mentions: {len(mentions)} (should include 'Tesla' and 'Tesla's')")
    print(f"✅ Sources: {len(owned_sources + external_sources)} total")
    print(f"✅ Case insensitive: {'✅' if all(len(extract_mentions(sample_text, case)) > 0 for case in ['Tesla', 'tesla', 'TESLA']) else '❌'}")
    print(f"✅ Possessive forms: {'✅' if any('Tesla\'s' in m['text'] for m in mentions) else '❌'}")

if __name__ == "__main__":
    test_functions()
