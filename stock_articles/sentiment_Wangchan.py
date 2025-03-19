# from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
# import pandas as pd
# import torch

# model_name = "airesearch/wangchanberta-base-att-spm-uncased"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSequenceClassification.from_pretrained(model_name)
# sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)

# def analyze_sentiment(text):
#     if not text or len(text) < 10:
#         return "Neutral"
#     result = sentiment_pipeline(text[:512])
#     return result[0]["label"]


# df = pd.read_csv("kaohoon_news.csv")
# df["sentiment"] = df["content"].apply(analyze_sentiment)

# df.to_csv("kaohoon_news_analyzed.csv", index=False, encoding="utf-8-sig")

# print("✅ Save hoon_news_analyzed.csv")
