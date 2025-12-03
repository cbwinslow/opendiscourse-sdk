"""LLM integration module for OpenDiscourse."""

from .ollama_client import (
    OllamaClient,
    OllamaConfig,
    OllamaResponse,
    LangChainOllamaLLM,
    generate_embeddings,
    rag_query,
)

__all__ = [
    "OllamaClient",
    "OllamaConfig", 
    "OllamaResponse",
    "LangChainOllamaLLM",
    "generate_embeddings",
    "rag_query",
]
