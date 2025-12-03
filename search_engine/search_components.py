from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

@dataclass
class SearchResult:
    """Class representing a single search result."""
    id: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = None
    vector: np.ndarray = None

class UnifiedSearcher:
    """Class for performing unified search across multiple vector stores."""
    
    def __init__(self, vector_stores: List[Any]):
        """Initialize with list of vector store clients."""
        self.vector_stores = vector_stores

    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        """
        Search across all vector stores and return unified ranked results.
        
        Args:
            query: Search query string
            k: Number of top results to return
            
        Returns:
            List of SearchResult objects containing the top k results
        """
        # Query all vector stores in parallel
        all_results = []
        for store in self.vector_stores:
            store_results = store.search(query, k=k)
            all_results.extend(store_results)
            
        # Merge results and normalize scores
        for result in all_results:
            # Min-max normalization of scores within each source
            result.score = (result.score - min(r.score for r in all_results)) / \
                         (max(r.score for r in all_results) - min(r.score for r in all_results))
                         
        # Remove duplicates by content similarity
        unique_results = self._deduplicate_results(all_results)
        
        # Sort by normalized score
        ranked_results = sorted(unique_results, key=lambda x: x.score, reverse=True)
        
        return ranked_results[:k]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content similarity."""
        unique_results = []
        seen_content = set()
        
        for result in results:
            # Simple content-based deduplication
            content_hash = hash(result.content.lower().strip())
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
                
        return unique_results


class ResultAggregator:
    """Class for aggregating and ranking search results."""
    
    def __init__(self, score_weights: Dict[str, float] = None):
        """
        Initialize with optional score weights for different sources.
        
        Args:
            score_weights: Dictionary mapping source names to weight multipliers
        """
        self.score_weights = score_weights or {}
        
    def aggregate(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Aggregate results by normalizing scores, removing duplicates, and reranking.
        
        Args:
            results: List of SearchResult objects to aggregate
            
        Returns:
            List of aggregated and reranked SearchResult objects
        """
        if not results:
            return []
            
        # Group results by source
        source_groups = defaultdict(list)
        for result in results:
            source_groups[result.source].append(result)
            
        # Normalize scores within each source group
        normalized_results = []
        for source, group in source_groups.items():
            weight = self.score_weights.get(source, 1.0)
            
            # Min-max normalization
            scores = [r.score for r in group]
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score
            
            for result in group:
                if score_range > 0:
                    normalized_score = (result.score - min_score) / score_range
                else:
                    normalized_score = 1.0
                    
                # Apply source weight
                result.score = normalized_score * weight
                normalized_results.append(result)
                
        # Remove duplicates
        unique_results = self._remove_duplicates(normalized_results)
        
        # Rerank based on final scores
        reranked_results = self._rerank_results(unique_results)
        
        return reranked_results
        
    def _remove_duplicates(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content and metadata similarity."""
        unique_results = []
        seen_contents = set()
        
        for result in results:
            # Create a unique identifier based on content and key metadata
            content_key = self._get_content_key(result)
            
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_results.append(result)
                
        return unique_results
        
    def _get_content_key(self, result: SearchResult) -> str:
        """Generate a unique key for a result based on content and metadata."""
        content = result.content.lower().strip()
        
        # Include key metadata fields in uniqueness check
        metadata_str = ""
        if result.metadata:
            # Sort metadata keys for consistent ordering
            sorted_keys = sorted(result.metadata.keys())
            metadata_str = "_".join(
                f"{k}:{str(result.metadata[k])}" 
                for k in sorted_keys 
                if k in ('id', 'url', 'title')
            )
            
        return f"{content}_{metadata_str}"
        
    def _rerank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Rerank results based on multiple factors."""
        # Could implement more sophisticated reranking here
        # For now, just sort by normalized scores
        return sorted(results, key=lambda x: x.score, reverse=True)


class SearchOptimizer:
    """Class for optimizing search queries."""
    
    def __init__(self, 
                 expansion_model: Any = None,
                 context_embedder: Any = None):
        """
        Initialize with optional query expansion and context models.
        
        Args:
            expansion_model: Model for query expansion
            context_embedder: Model for embedding context
        """
        self.expansion_model = expansion_model
        self.context_embedder = context_embedder
        
    def optimize_query(self, query: str, context: str = None) -> str:
        """
        Optimize the search query through expansion and context addition.
        
        Args:
            query: Original search query
            context: Optional context string to help optimize the query
            
        Returns:
            Optimized query string
        """
        optimized_query = query
        
        # Expand query with related terms
        if self.expansion_model:
            expanded_terms = self._expand_query(optimized_query)
            optimized_query = self._merge_query_terms(optimized_query, expanded_terms)
            
        # Add context if provided
        if context and self.context_embedder:
            context_terms = self._extract_context_terms(context)
            optimized_query = self._add_context(optimized_query, context_terms)
            
        return optimized_query
        
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with related terms using expansion model."""
        if not self.expansion_model:
            return []
            
        # Use the expansion model to get related terms
        expanded_terms = self.expansion_model.expand(query)
        
        # Filter and clean expanded terms
        cleaned_terms = [
            term.strip().lower() 
            for term in expanded_terms 
            if term.strip() and term.strip().lower() != query.lower()
        ]
        
        return cleaned_terms
        
    def _merge_query_terms(self, original_query: str, expanded_terms: List[str]) -> str:
        """Merge original query with expanded terms."""
        if not expanded_terms:
            return original_query
            
        # Combine original query with top expanded terms
        merged_query = f"{original_query} {' '.join(expanded_terms[:3])}"
        return merged_query
        
    def _extract_context_terms(self, context: str) -> List[str]:
        """Extract relevant terms from context using embedder."""
        if not self.context_embedder or not context:
            return []
            
        # Embed context and extract key terms
        context_embedding = self.context_embedder.embed(context)
        context_terms = self.context_embedder.extract_terms(context_embedding)
        
        return context_terms
        
    def _add_context(self, query: str, context_terms: List[str]) -> str:
        """Add context terms to query."""
        if not context_terms:
            return query
            
        # Add top context terms to query
        contextualized_query = f"{query} {' '.join(context_terms[:2])}"
        return contextualized_query
