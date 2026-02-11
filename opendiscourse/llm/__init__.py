"""LLM integration module for OpenDiscourse."""

from .ollama_client import (
    LangChainOllamaLLM,
    OllamaClient,
    OllamaConfig,
    OllamaResponse,
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
