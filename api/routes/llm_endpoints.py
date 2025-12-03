"""LLM-powered search and chat endpoints."""

import os
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from opendiscourse.llm import OllamaClient, OllamaConfig, rag_query

router = APIRouter(prefix="/v1", tags=["LLM"])

DB_URL = os.environ.get(
    "RAG_DB_URL", "postgresql://user:password@localhost:5432/opendiscourse"
)


class SearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str
    limit: int = 10
    min_score: float = 0.0
    mode: str = "semantic"  # semantic, keyword, hybrid


class ChatRequest(BaseModel):
    """Request model for chat."""
    message: str
    context_limit: int = 5
    model: str = "llama2"
    temperature: float = 0.1


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    title: str
    content: str
    score: float
    source: str
    metadata: Dict


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    sources: List[SearchResult]
    model: str
    took_ms: int


class SearchResponse(BaseModel):
    """Search response model."""
    results: List[SearchResult]
    total: int
    query: str
    took_ms: int


def search_documents(query: str, limit: int = 10, min_score: float = 0.0) -> List[SearchResult]:
    """Search documents in the database."""
    # For demo purposes, return mock results
    # In production, this would use vector similarity search
    mock_results = [
        SearchResult(
            id="doc_1",
            title="Infrastructure Investment and Jobs Act",
            content=f"The Infrastructure Investment and Jobs Act relates to your query about '{query}'. This comprehensive legislation addresses critical infrastructure needs across the United States, including roads, bridges, broadband, and water systems.",
            score=0.85,
            source="congress.gov",
            metadata={"type": "legislation", "year": 2021}
        ),
        SearchResult(
            id="doc_2", 
            title="Build Back Better Framework",
            content=f"Your search for '{query}' matches this document about the Build Back Better framework. This policy initiative focuses on investments in clean energy, childcare, healthcare, and economic recovery measures.",
            score=0.78,
            source="whitehouse.gov",
            metadata={"type": "policy", "year": 2021}
        ),
        SearchResult(
            id="doc_3",
            title="American Rescue Plan Act",
            content=f"The American Rescue Plan Act is relevant to your query '{query}'. This economic stimulus package provided relief during the COVID-19 pandemic through direct payments, unemployment benefits, and support for businesses.",
            score=0.72,
            source="treasury.gov", 
            metadata={"type": "economic_policy", "year": 2021}
        )
    ]
    
    # Filter by minimum score
    filtered_results = [r for r in mock_results if r.score >= min_score]
    
    # Limit results
    return filtered_results[:limit]


@router.get("/search", response_model=SearchResponse)
async def semantic_search(
    q: str,
    limit: int = 10,
    min_score: float = 0.0,
    mode: str = "semantic"
):
    """Perform semantic search across document corpus."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        import time
        start_time = time.time()
        
        # Perform search
        results = search_documents(q, limit, min_score)
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=q,
            took_ms=took_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse) 
async def chat_with_documents(request: ChatRequest):
    """Chat with documents using RAG."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        import time
        start_time = time.time()
        
        # First, search for relevant documents
        search_results = search_documents(request.message, request.context_limit)
        
        # Extract content for context
        context_docs = [f"Title: {r.title}\nContent: {r.content}" for r in search_results]
        
        # Check if Ollama is available
        config = OllamaConfig(model=request.model)
        async with OllamaClient(config) as client:
            is_healthy = await client.health_check()
            if not is_healthy:
                # Fallback to mock response
                response_text = f"Based on the available documents, here's what I found regarding '{request.message}': " + \
                              "The documents discuss various government policies and legislation. " + \
                              "However, I'm currently running in demo mode. For full AI responses, please ensure Ollama is running."
            else:
                # Generate response using RAG
                response_text = await rag_query(
                    question=request.message,
                    context_documents=context_docs,
                    model=request.model
                )
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response=response_text,
            sources=search_results,
            model=request.model,
            took_ms=took_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/models")
async def list_available_models():
    """List available LLM models."""
    try:
        config = OllamaConfig()
        async with OllamaClient(config) as client:
            is_healthy = await client.health_check()
            if not is_healthy:
                return {
                    "models": [
                        {"name": "demo", "size": "N/A", "description": "Demo mode - Ollama not available"}
                    ],
                    "status": "demo_mode"
                }
            
            models = await client.list_models()
            return {
                "models": models,
                "status": "active"
            }
    except Exception as e:
        return {
            "models": [
                {"name": "demo", "size": "N/A", "description": "Demo mode - Error connecting to Ollama"}
            ],
            "status": "error",
            "error": str(e)
        }


@router.post("/models/{model_name}/pull")
async def pull_model(model_name: str):
    """Pull a model from Ollama registry."""
    try:
        config = OllamaConfig()
        async with OllamaClient(config) as client:
            is_healthy = await client.health_check()
            if not is_healthy:
                raise HTTPException(status_code=503, detail="Ollama service not available")
            
            success = await client.pull_model(model_name)
            if success:
                return {"status": "success", "message": f"Model {model_name} pulled successfully"}
            else:
                raise HTTPException(status_code=400, detail=f"Failed to pull model {model_name}")
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model pull failed: {str(e)}")


@router.get("/health")
async def llm_health_check():
    """Check LLM service health."""
    try:
        config = OllamaConfig()
        async with OllamaClient(config) as client:
            is_healthy = await client.health_check()
            
            if is_healthy:
                models = await client.list_models()
                return {
                    "status": "healthy",
                    "service": "ollama",
                    "available_models": len(models),
                    "base_url": config.base_url
                }
            else:
                return {
                    "status": "unhealthy", 
                    "service": "ollama",
                    "error": "Service not responding",
                    "base_url": config.base_url
                }
    except Exception as e:
        return {
            "status": "error",
            "service": "ollama", 
            "error": str(e),
            "base_url": config.base_url
        }


@router.post("/generate")
async def generate_response(
    prompt: str,
    model: str = "llama2",
    system: Optional[str] = None,
    temperature: float = 0.7
):
    """Generate a response from a prompt."""
    try:
        config = OllamaConfig(model=model)
        async with OllamaClient(config) as client:
            is_healthy = await client.health_check()
            if not is_healthy:
                return {
                    "response": f"Demo response to: {prompt}",
                    "model": "demo",
                    "status": "demo_mode"
                }
            
            response = await client.generate(
                prompt=prompt,
                system=system,
                options={
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            )
            
            return {
                "response": response.response,
                "model": response.model,
                "status": "success",
                "stats": {
                    "total_duration": response.total_duration,
                    "eval_count": response.eval_count,
                    "eval_duration": response.eval_duration
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
