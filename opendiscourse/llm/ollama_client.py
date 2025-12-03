"""Ollama client for LLM interactions."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Configuration for Ollama client."""
    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    timeout: int = 30
    max_retries: int = 3


class OllamaResponse(BaseModel):
    """Response from Ollama API."""
    model: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, config: OllamaConfig = None):
        """Initialize Ollama client."""
        self.config = config or OllamaConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> OllamaResponse:
        """Generate a response using Ollama."""
        model = model or self.config.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        if options:
            payload["options"] = options

        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return OllamaResponse(**data)
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise ConnectionError(f"Ollama connection failed: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Ollama API error: {e.response.status_code}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> OllamaResponse:
        """Have a conversation using Ollama chat API."""
        model = model or self.config.model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        if options:
            payload["options"] = options

        try:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            
            data = response.json()
            # Convert chat response format to generate response format
            return OllamaResponse(
                model=data["model"],
                response=data["message"]["content"],
                done=data["done"],
                total_duration=data.get("total_duration"),
                load_duration=data.get("load_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                prompt_eval_duration=data.get("prompt_eval_duration"),
                eval_count=data.get("eval_count"),
                eval_duration=data.get("eval_duration")
            )
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise ConnectionError(f"Ollama connection failed: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Ollama API error: {e.response.status_code}")

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        payload = {"name": model}
        
        try:
            response = await self.client.post("/api/pull", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if Ollama service is healthy."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False


class LangChainOllamaLLM:
    """LangChain-compatible wrapper for Ollama."""

    def __init__(self, config: OllamaConfig = None):
        """Initialize LangChain Ollama LLM."""
        self.config = config or OllamaConfig()
        self.ollama = OllamaClient(config)

    async def agenerate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate responses for multiple prompts."""
        tasks = [self._generate_single(prompt, **kwargs) for prompt in prompts]
        responses = await asyncio.gather(*tasks)
        return [r.response for r in responses]

    async def _generate_single(self, prompt: str, **kwargs) -> OllamaResponse:
        """Generate response for a single prompt."""
        async with self.ollama as client:
            return await client.generate(prompt, **kwargs)

    async def acall(self, prompt: str, **kwargs) -> str:
        """Single prompt generation."""
        async with self.ollama as client:
            response = await client.generate(prompt, **kwargs)
            return response.response


# Utility functions for RAG integration
async def generate_embeddings(
    texts: List[str],
    model: str = "nomic-embed-text"
) -> List[List[float]]:
    """Generate embeddings for text using Ollama."""
    config = OllamaConfig(model=model)
    
    async with OllamaClient(config) as client:
        embeddings = []
        for text in texts:
            try:
                response = await client.client.post(
                    "/api/embeddings",
                    json={"model": model, "prompt": text}
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"])
            except Exception as e:
                logger.error(f"Failed to generate embedding for text: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 384)  # Default dimension
        
        return embeddings


async def rag_query(
    question: str,
    context_documents: List[str],
    model: str = "llama2",
    max_context_length: int = 4000
) -> str:
    """Perform RAG query with context documents."""
    # Truncate context if too long
    context = "\n\n".join(context_documents)
    if len(context) > max_context_length:
        context = context[:max_context_length] + "..."

    system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
Use only the information in the context to answer questions. If the answer is not in the context, 
say "I don't have enough information to answer that question based on the provided context."
Always cite relevant parts of the context in your response."""

    prompt = f"""Context:
{context}

Question: {question}

Answer:"""

    config = OllamaConfig(model=model)
    async with OllamaClient(config) as client:
        response = await client.generate(
            prompt=prompt,
            system=system_prompt,
            options={
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        )
        return response.response
