from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import pandas as pd
import torch
import os

# Load WangchanBERTa model
model_name = "airesearch/wangchanberta-base-att-spm-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
device = 0 if torch.cuda.is_available() else -1  # Use GPU if available

# Sentiment analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=device)

# Map model labels to sentiment categories
label_mapping = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

# Function to analyze sentiment
def analyze_sentiment(text):
    if not isinstance(text, str) or len(text.strip()) < 10:
        return "Neutral"  # Default to Neutral for short/invalid text
    
    try:
        result = sentiment_pipeline(text[:512])  # Limit to 512 tokens
        return label_mapping.get(result[0]["label"], "Unknown")
    except Exception as e:
        print(f"❌ Sentiment analysis error: {e}")
        return "Unknown"

# File paths
input_csv = "kaohoon_news.csv"
output_csv = "kaohoon_news_analyzed.csv"

# Load news data
df = pd.read_csv(input_csv)

# Load previously analyzed data (if exists)
if os.path.exists(output_csv):
    df_existing = pd.read_csv(output_csv)
    analyzed_titles = set(df_existing["title"].dropna().str.strip()) if "title" in df_existing.columns else set()
else:
    df_existing = pd.DataFrame(columns=["title", "content", "sentiment"])
    analyzed_titles = set()

# Filter out already analyzed articles
df_new = df[~df["title"].fillna("").str.strip().isin(analyzed_titles)]

if df_new.empty:
    print("✅ No new articles to analyze")
else:
    print(f"📌 Analyzing {len(df_new)} new articles...")

    # Perform sentiment analysis
    df_new["sentiment"] = df_new["content"].fillna("Neutral").astype(str).apply(analyze_sentiment)

    # Merge with existing data and save
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Saved results to: {output_csv}")
