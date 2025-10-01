from transformers import pipeline

# Create summarizer (model = BART, but you can swap)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def hf_summarize(text: str, max_length: int = 150, min_length: int = 40) -> str:
    """
    Summarize text with Hugging Face BART model.
    max_length and min_length are in tokens (approx. words).
    """
    result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return result[0]["summary_text"]
if __name__ == "__main__":
    text = """Given Google's dominant position in search, digital advertising, cloud computing,
    and artificial intelligence technologies, what are the most effective pathways for an individual 
    or small business to create a million dollars in value—whether by optimizing campaigns through Google Ads, 
    building successful products on Google Cloud or Android, leveraging YouTube for scalable content monetization, 
    or identifying new niches within Google's expansive platform ecosystem?"""

    compressed = hf_summarize(text, max_length=60, min_length=20)
    print("Original:", len(text.split()), "words")
    print("Summary:", len(compressed.split()), "words")
    print(compressed)
