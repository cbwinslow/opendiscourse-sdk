from abc import ABC, abstractmethod
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from typing import List

class EmbeddingStrategy(ABC):
    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """Convert text into a dense vector representation."""
        pass

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Convert a batch of texts into dense vector representations."""
        return np.vstack([self.embed(text) for text in texts])

class SentenceTransformerStrategy(EmbeddingStrategy):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        
    def embed(self, text: str) -> np.ndarray:
        # Generate embeddings using sentence-transformers
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
        
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        # More efficient batch processing
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings

class OpenAIEmbeddingStrategy(EmbeddingStrategy):
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
    def embed(self, text: str) -> np.ndarray:
        # Generate embeddings using OpenAI API
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        embedding = np.array(response.data[0].embedding)
        return embedding
        
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        # Batch process texts through OpenAI API
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        embeddings = np.array([data.embedding for data in response.data])
        return embeddings
