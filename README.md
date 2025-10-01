# Brand Analyzer - Comprehensive Documentation

A sophisticated brand analysis tool that uses LLM-powered web search to provide comprehensive brand insights with advanced tokenization optimization techniques.

## 🎯 **Main Idea**

The Brand Analyzer is designed to answer questions about brands and companies by:
1. **Web Search Integration**: Using LLM to perform intelligent web searches
2. **Citation Extraction**: Automatically extracting and categorizing citations from responses
3. **Brand Mention Analysis**: Identifying and analyzing brand mentions in various formats
4. **Token Optimization**: Implementing advanced techniques to reduce token usage while maintaining quality
5. **Performance Evaluation**: Comprehensive testing and analysis of different approaches

## 🔧 **Technical Implementation Details**

### **Citation and Mention Detection System**

#### **Key Definitions**:
- **Citations**: Any mention of entities that include URLs (all URL patterns detected)
- **Sources**: Unique URLs (each unique URL = 1 source, deduplicated)
- **Searches**: Unique domains (each unique domain = 1 search)
- **Linked Mentions**: Brand mentions with associated URLs
- **Unlinked Mentions**: Standalone brand references without URLs

#### **Citation Detection** (`extract_citations`):
The system detects **ALL unique URLs** using 4 different patterns:

```python
# Pattern 1: [text](url) - markdown links (priority)
pattern1 = r'\[([^\]]+)\]\(([^)]+)\)'

# Pattern 2: source[...] patterns (case insensitive)  
pattern2 = r'(?:Source|source)\[([^\]]+)\]'

# Pattern 3: text[url] patterns (any text attached to URL)
pattern3 = r'(\w+(?:\s+\w+)*)\[([^\]]+)\]'

# Pattern 4: Plain URLs (only if not already found)
pattern4 = r'https?://[^\s\)]+'
```

**Detection Process**:
1. **Markdown Links**: `[text](url)` - highest priority
2. **Source Patterns**: `Source[url]` or `source[url]` - case insensitive
3. **Text-URL Patterns**: `anytext[url]` - captures any text before URL in brackets
4. **Plain URLs**: Standalone `https://` or `http://` URLs (after removing other patterns)

**Features**:
- **Duplicate Prevention**: Uses `found_urls` set to prevent counting same URL multiple times
- **Basic URL Validation**: Checks for `http://` or `https://` prefixes only
- **Type Classification**: Each citation tagged with pattern type (`markdown_link`, `source_pattern`, `text_url_pattern`, `plain_url`)
- **Text Extraction**: Captures associated text for context

#### **Brand Mention Detection** (`extract_mentions`):
The system detects brand mentions and classifies them as **linked** or **unlinked**:

```python
# Pattern 1: Brand[url] patterns (linked)
pattern1 = r'\b' + re.escape(brand_name) + r'\b\[([^\]]+)\]'

# Pattern 2: [Brand](url) - markdown links (linked)
pattern2 = r'\[' + re.escape(brand_name) + r'\]\(([^)]+)\)'

# Pattern 3: Brand variations with [url] (linked)
# Handles spaces, underscores, hyphens: "Brand Name", "Brand_Name", "Brand-Name"

# Pattern 4: Simple brand mentions (unlinked)
patterns_unlinked = [
    r'\b' + re.escape(brand_name) + r'\b',      # Exact brand name
    r'\b' + re.escape(brand_name) + r"'s\b"     # Brand's possessive
]
```

**Linked Mentions** (have associated URLs):
- **Brand[url]**: `Tesla[https://tesla.com]`
- **[Brand](url)**: `[Tesla](https://tesla.com)`
- **Variations**: Handles `Brand Name`, `Brand_Name`, `Brand-Name` formats

**Unlinked Mentions** (standalone brand references):
- **Exact Match**: `Tesla` (case insensitive)
- **Possessive**: `Tesla's` (case insensitive)
- **URL Exclusion**: Ignores mentions within URLs (e.g., "tesla.com")

**Smart Filtering**:
- **Position Tracking**: Records exact character positions to avoid double-counting
- **URL Context Detection**: Checks 50 characters around each mention for URL patterns
- **Linked Position Tracking**: Prevents unlinked mentions from overlapping with linked ones
- **Case Insensitive**: Matches brand names regardless of capitalization

#### **Source Classification** (`classify_sources`):
Classifies citations as **owned** (brand's domain) or **external** (all other domains):

```python
def classify_sources(citations: list, brand_url: str) -> tuple:
    brand_domain = urlparse(brand_url).netloc.lower()
    brand_domain_clean = brand_domain.replace('www.', '')
    
    for citation in citations:
        citation_domain = urlparse(citation["url"]).netloc.lower()
        citation_domain_clean = citation_domain.replace('www.', '')
        
        # Check if domains match (ignoring www prefix and subdomains)
        if citation_domain_clean == brand_domain_clean or citation_domain_clean.endswith('.' + brand_domain_clean):
            # Owned source
        else:
            # External source
```

**Classification Logic**:
- **Owned Sources**: URLs matching the brand's domain or its subdomains
- **External Sources**: All other URLs
- **Domain Matching**: Uses `urlparse` for accurate domain extraction
- **www Handling**: Removes `www.` prefix for comparison
- **Subdomain Support**: `blog.tesla.com` matches `tesla.com`
- **Deduplication**: Returns unique URLs only (no duplicates)

**Examples**:
- **Brand URL**: `https://tesla.com`
- **Owned**: `https://tesla.com`, `https://www.tesla.com`, `https://blog.tesla.com`
- **External**: `https://google.com`, `https://cnn.com`, `https://reuters.com`

## 🚀 **Token Optimization Techniques**

### **Three Evaluation Techniques**

The system evaluates three different prompt approaches in `token_optimization.py`:

#### **1. Original Prompt** (`base_create_prompt`):
- **Description**: Full prompt with comprehensive constraints and instructions
- **Usage**: Uses the complete `base_create_prompt` function
- **Purpose**: Baseline for comparison
- **Characteristics**: Verbose with detailed instructions

#### **2. Optimized Prompt**:
- **Description**: Streamlined version with essential constraints only
- **Template**: 
```python
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
```
- **Purpose**: Removes verbose instructions while maintaining core functionality
- **Characteristics**: Less verbose, more direct

#### **3. Compressed Prompt**:
- **Description**: Uses Hugging Face BART to compress the question before creating the prompt
- **Process**: 
  1. Applies `hf_summarize(question, ratio=0.2)` to compress the question
  2. Uses `base_create_prompt` with the compressed question
- **Model**: `facebook/bart-large-cnn` from Hugging Face
- **Purpose**: Reduces question length while preserving meaning
- **Characteristics**: Compresses only the question text, not the entire prompt

### **Hierarchical Prompting** (Current Implementation)

The current implementation uses a more sophisticated approach in `create_prompt`:

```python
def create_prompt(brand_name, website_url, question, max_searches, max_sources):
    q_tokens = count_tokens(question)
    
    # Preserve question and background context intelligently
    head, tail = _preserve_tail_two_sentences(question)
    if tail:  # Found a question to preserve
        if count_tokens(head) > question_token_threshold:  # Default: 120 tokens
            compressed_head = hf_summarize(head, ratio=question_ratio)  # Default: 0.4
            final_question = compressed_head + " " + tail
        else:
            final_question = question
    else:
        # No question found, compress entire text if needed
        if q_tokens > question_token_threshold:
            final_question = hf_summarize(question, ratio=question_ratio)
        else:
            final_question = question
```

**Key Features**:
- **Smart Question Preservation**: Uses `_preserve_tail_two_sentences` to keep questions and recent context intact
- **Hierarchical Compression**: Only compresses background text, preserves questions
- **Threshold-Based**: Only compresses when > 120 tokens (not 10 as in evaluation)
- **Ratio Control**: Maintains 40% of original content (0.4 ratio, not 0.2)
- **Fallback Safety**: Uses original question if compression fails

**Differences from Evaluation**:
- **Evaluation**: Tests 3 fixed approaches for comparison
- **Current Implementation**: Uses smart hierarchical compression with question preservation
- **Threshold**: 120 tokens (not 10 as in evaluation)
- **Ratio**: 0.4 for current implementation (0.2 for evaluation compressed prompt)

## 📊 **Performance Results**

### **Token Optimization Performance Analysis**

Based on comprehensive testing across different question lengths and brands:

| Technique | Short Questions | Long Questions | Best Use Case |
|-----------|----------------|----------------|---------------|
| **Original Prompt** | Baseline (0% optimization) | Baseline (0% optimization) | Reference standard |
| **Optimized Prompt** | ✅ **30% token reduction** | ✅ **20% token reduction** | **Short questions** |
| **Compressed Prompt** | ❌ **-8% token increase** | ✅ **30% token reduction** | **Long questions** |

### **Key Performance Insights**

#### **Short Questions Performance**:
- **Optimized Prompt**: Best choice for short questions
  - 30.16% token reduction (Apple)
  - 29.92% token reduction (Google)
  - ✅ Maintains budget compliance
  - ✅ Consistent performance across brands

- **Compressed Prompt**: Poor performance on short questions
  - -10.32% token increase (Apple)
  - -6.3% token increase (Google)
  - ❌ Budget violations
  - ❌ Over-compression leads to inefficiency

#### **Long Questions Performance**:
- **Compressed Prompt**: Best choice for long questions
  - 29.38% token reduction (Apple)
  - 29.74% token reduction (Google)
  - ✅ Highest token savings
  - ✅ Effective compression of complex content

- **Optimized Prompt**: Moderate performance on long questions
  - 19.59% token reduction (Apple)
  - 19.49% token reduction (Google)
  - ⚠️ Some budget violations
  - ⚠️ Less effective on complex content

### **Strategic Recommendations**

1. **Use Optimized Prompt for Short Questions**: Achieves 30% token reduction with reliable budget compliance
2. **Use Compressed Prompt for Long Questions**: Achieves 30% token reduction on complex content
3. **Avoid Compressed Prompt for Short Questions**: Causes token increase and budget violations
4. **Consider Original Prompt**: When quality is paramount and token efficiency is secondary

## 🚀 **How to Run the Program**

### **1. Setup Environment**
```bash
# Clone and navigate to the project
cd /path/to/brand_analyzer

# Activate virtual environment
source venv/bin/activate

# Install the package (this installs dependencies and creates global command)
cd src
pip install -e .
```

### **2. Configure Environment Variables**
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=nousresearch/hermes-2-pro-llama-3-8b
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MAX_TOKENS=4000
```

### **3. Main Brand Analysis (CLI)**

#### **Basic Analysis**
```bash
# Method 1: Global command (recommended - works from anywhere)
brand-analyzer analyze --brand "Tesla" --url "https://tesla.com" --question "What are Tesla's latest innovations?"

# Method 2: Root executable (works from project directory)
./brand-analyzer analyze --brand "Tesla" --url "https://tesla.com" --question "What are Tesla's latest innovations?"

# Method 3: Direct Python execution (works from src directory)
cd src
python main.py analyze --brand "Tesla" --url "https://tesla.com" --question "What are Tesla's latest innovations?"

# With custom parameters
brand-analyzer analyze --brand "Google" --url "https://google.com" --question "Tell me about Google's AI initiatives" --max-searches 8 --max-sources 15

# With verbose output
brand-analyzer analyze --brand "Tesla" --url "https://tesla.com" --question "What are Tesla's latest innovations?" --verbose
```

#### **Statistics and Configuration**
```bash
# Show analysis statistics from output/output.json
brand-analyzer stats

# Show current configuration
brand-analyzer config
```

### **4. Token Optimization Evaluation**

#### **Run Token Optimization Tests**
```bash
# Navigate to evaluation scripts
cd evaluation/scripts

# Run the token optimization evaluation
python token_optimization.py

# Generate analysis and visualizations
python analysis_result.py
```

#### **View Results**
```bash
# Check generated files
ls ../results/

# View CSV results
cat ../results/token_analysis_results.csv

# View generated visualizations
open ../results/token_efficiency_overview.png
```

## 🏗️ **Project Architecture**

```
brand_analyzer/
├── src/
│   ├── main.py                    # Main CLI application
│   ├── utils.py                   # Core utility functions
│   ├── requirements.txt           # Dependencies
│   └── setup.py                  # Package setup
├── evaluation/                    # Evaluation and analysis
│   ├── scripts/                  # Executable scripts
│   │   ├── token_optimization.py # Token optimization evaluation
│   │   ├── analysis_result.py    # Results analysis and visualization
│   │   └── test_inputs.json     # Test cases
│   └── results/                  # Analysis results
│       ├── token_analysis_results.csv
│       └── *.png                 # Generated visualizations
├── output/                       # Analysis output
│   └── output.json              # Brand analysis results
└── README.md                    # This documentation
```

## 📋 **Core Components**

### **1. Citation and Mention Detection**
- **4 Citation Patterns**: Markdown links, source patterns, text-URL patterns, plain URLs
- **Linked/Unlinked Classification**: Smart detection of brand mentions with/without URLs
- **Position Tracking**: Exact character position mapping for analysis
- **Duplicate Prevention**: Ensures unique URL counting

### **2. Source Classification**
- **Owned vs External**: Domain-based classification using `urlparse`
- **Subdomain Support**: Handles `blog.tesla.com` as owned for `tesla.com`
- **www Handling**: Removes `www.` prefix for accurate matching
- **Deduplication**: Returns unique URLs only

### **3. Token Optimization**
- **3 Evaluation Techniques**: Original, Optimized, Compressed prompts
- **Hierarchical Compression**: Smart question preservation with background compression
- **Hugging Face Integration**: Uses `facebook/bart-large-cnn` for text summarization
- **Performance Monitoring**: Real-time token counting and efficiency metrics

### **4. Web Search and Budget Management**
- **Search Limits**: Hard limits on unique domains searched
- **Source Limits**: Hard limits on total unique sources
- **Budget Compliance**: Monitors and reports budget adherence
- **Graceful Degradation**: Continues analysis even with budget violations

## 🎯 **Key Features**

### **Intelligent Detection**:
- Multi-pattern citation extraction
- Smart brand mention classification
- Context-aware URL exclusion
- Position-based duplicate prevention

### **Token Efficiency**:
- Hierarchical compression with question preservation
- Hugging Face BART integration
- Performance-based technique selection
- Real-time optimization monitoring

### **Quality Preservation**:
- Maintains answer fidelity while optimizing tokens
- Comprehensive citation requirements
- Source diversity enforcement
- Error handling with graceful degradation

### **Production Ready**:
- Robust error handling
- Comprehensive logging
- Performance metrics tracking
- CLI interface with rich options

---

The Brand Analyzer represents a sophisticated approach to brand analysis, combining intelligent LLM integration, advanced token optimization, comprehensive evaluation, and production-ready implementation for reliable brand insights.
