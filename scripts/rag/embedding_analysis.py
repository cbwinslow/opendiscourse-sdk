#!/usr/bin/env python3
"""Compute embeddings for a sample text set."""
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
texts = [
    "The quick brown fox jumps over the lazy dog",
    "Congress passed a new bill regarding environmental policy",
]

for t in texts:
    resp = client.embeddings.create(model="text-embedding-3-small", input=t)
    embedding = resp.data[0].embedding
    print(t, embedding[:5], "...")
