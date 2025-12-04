# Embeddings Analysis Strategy

## 🎯 Overview

This document outlines the comprehensive embeddings strategy for analyzing congressional legislation using vector embeddings and semantic similarity analysis.

## 🏗️ Architecture

### Vector Storage Options
1. **pgvector** (Primary) - Native PostgreSQL vector extension
2. **Qdrant** (Alternative) - Dedicated vector database
3. **Chroma** (Alternative) - Local vector storage

### Embedding Models
1. **Ollama Local Models**
   - `nomic-embed-text` (default)
   - `all-minilm`
   - `mxbai-embed-large`

2. **OpenRouter API Models**
   - `text-embedding-3-small`
   - `text-embedding-3-large`
   - Custom fine-tuned models

## 📊 Database Schema

### Core Tables
```sql
-- Embedding storage
CREATE TABLE analysis.bill_embeddings (
    bill_id VARCHAR(20) PRIMARY KEY,
    embedding vector(1536),  -- Adjust size based on model
    model_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Similarity analysis
CREATE TABLE analysis.bill_similarity (
    bill_id_1 VARCHAR(20),
    bill_id_2 VARCHAR(20),
    similarity_score FLOAT,
    similarity_type VARCHAR(50),  -- 'semantic', 'political', 'combined'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Clustering results
CREATE TABLE analysis.bill_clusters (
    bill_id VARCHAR(20),
    cluster_id INTEGER,
    cluster_confidence FLOAT,
    cluster_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Analysis Views
```sql
-- Complete similarity analysis
CREATE VIEW analysis.similarity_summary AS
SELECT 
    b1.bill_id,
    b1.official_title as bill_title,
    b2.official_title as similar_bill_title,
    bs.similarity_score,
    bs.similarity_type,
    ps1.political_bias_score as bill1_political,
    ps2.political_bias_score as bill2_political
FROM analysis.bill_similarity bs
JOIN congress.bills b1 ON bs.bill_id_1 = b1.bill_id
JOIN congress.bills b2 ON bs.bill_id_2 = b2.bill_id
LEFT JOIN analysis.bill_political_scores ps1 ON b1.bill_id = ps1.bill_id
LEFT JOIN analysis.bill_political_scores ps2 ON b2.bill_id = ps2.bill_id;
```

## 🚀 Implementation Strategy

### Phase 1: Basic Embeddings
1. **Setup pgvector extension**
2. **Generate embeddings for all bills**
3. **Implement basic similarity search**
4. **Create similarity analysis views**

### Phase 2: Advanced Analysis
1. **Implement clustering algorithms**
2. **Add political similarity analysis**
3. **Create hybrid similarity scoring**
4. **Build similarity-based recommendations**

### Phase 3: Real-time Processing
1. **Streaming embeddings for new bills**
2. **Automatic similarity detection**
3. **Real-time clustering updates**
4. **Similarity-based alerts**

## 🔧 Technical Implementation

### Embedding Generation
```python
import ollama
import numpy as np
from psycopg2.extras import execute_values

class EmbeddingProcessor:
    def __init__(self, model_name="nomic-embed-text"):
        self.model_name = model_name
        self.embedding_dim = 768  # Adjust based on model
    
    def generate_embedding(self, text):
        """Generate embedding for bill text"""
        response = ollama.embeddings(
            model=self.model_name,
            prompt=text
        )
        return np.array(response['embedding'])
    
    def process_bill(self, bill_text, bill_id):
        """Process single bill and store embedding"""
        embedding = self.generate_embedding(bill_text)
        
        # Store in database
        query = """
        INSERT INTO analysis.bill_embeddings 
        (bill_id, embedding, model_name) 
        VALUES (%s, %s, %s)
        ON CONFLICT (bill_id) DO UPDATE SET
        embedding = EXCLUDED.embedding,
        model_name = EXCLUDED.model_name,
        created_at = NOW()
        """
        
        cursor.execute(query, (bill_id, embedding.tolist(), self.model_name))
```

### Similarity Analysis
```python
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityAnalyzer:
    def __init__(self, similarity_threshold=0.7):
        self.similarity_threshold = similarity_threshold
    
    def compute_similarity(self, embedding1, embedding2):
        """Compute cosine similarity between embeddings"""
        return cosine_similarity(
            embedding1.reshape(1, -1), 
            embedding2.reshape(1, -1)
        )[0][0]
    
    def find_similar_bills(self, target_bill_id, limit=10):
        """Find bills similar to target bill"""
        query = """
        SELECT 
            b2.bill_id,
            b2.official_title,
            (e1.embedding <=> e2.embedding) * -1 + 1 as similarity_score
        FROM analysis.bill_embeddings e1
        JOIN analysis.bill_embeddings e2 ON e1.bill_id != e2.bill_id
        JOIN congress.bills b2 ON e2.bill_id = b2.bill_id
        WHERE e1.bill_id = %s
        ORDER BY similarity_score DESC
        LIMIT %s
        """
        
        cursor.execute(query, (target_bill_id, limit))
        return cursor.fetchall()
```

### Clustering Analysis
```python
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

class ClusterAnalyzer:
    def __init__(self, n_clusters=10):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.pca = PCA(n_components=50)  # Dimensionality reduction
    
    def cluster_bills(self, embeddings):
        """Perform K-means clustering on bill embeddings"""
        # Reduce dimensionality for better clustering
        reduced_embeddings = self.pca.fit_transform(embeddings)
        
        # Perform clustering
        cluster_labels = self.kmeans.fit_predict(reduced_embeddings)
        
        return cluster_labels, self.kmeans.cluster_centers_
    
    def analyze_clusters(self, cluster_labels, bill_ids):
        """Analyze cluster characteristics"""
        cluster_analysis = {}
        
        for cluster_id in range(self.n_clusters):
            cluster_bills = [
                bill_ids[i] for i in range(len(bill_ids)) 
                if cluster_labels[i] == cluster_id
            ]
            
            cluster_analysis[cluster_id] = {
                'bill_count': len(cluster_bills),
                'bill_ids': cluster_bills,
                'percentage': len(cluster_bills) / len(bill_ids) * 100
            }
        
        return cluster_analysis
```

## 📈 Analysis Capabilities

### Semantic Similarity
- **Content-based similarity** using bill text embeddings
- **Configurable thresholds** for different use cases
- **Batch processing** for large datasets
- **Real-time similarity** for new legislation

### Political Similarity
- **Ideological alignment** based on political bias scores
- **Partisanship analysis** using voting patterns
- **Cross-party collaboration** detection
- **Polarization measurement** over time

### Hybrid Similarity
- **Combined scoring** using semantic and political factors
- **Weighted similarity** for different analysis types
- **Context-aware similarity** based on bill categories
- **Multi-dimensional similarity** analysis

### Clustering Analysis
- **K-means clustering** for bill grouping
- **Hierarchical clustering** for taxonomy creation
- **Topic-based clustering** using content analysis
- **Temporal clustering** for trend analysis

## 🎯 Use Cases

### Research Applications
1. **Legislative Trend Analysis**: Track emerging policy themes
2. **Partisanship Studies**: Measure political polarization
3. **Policy Impact Assessment**: Find similar historical legislation
4. **Collaboration Detection**: Identify cross-party initiatives

### Practical Applications
1. **Bill Recommendation**: Suggest related legislation
2. **Duplicate Detection**: Find redundant or similar bills
3. **Policy Analysis**: Group bills by topic and approach
4. **Voting Guidance**: Provide context for legislative decisions

### Advanced Analytics
1. **Predictive Analysis**: Forecast bill success based on similarity
2. **Influence Tracking**: Trace policy idea propagation
3. **Network Analysis**: Build legislative similarity networks
4. **Temporal Analysis**: Track evolution of policy themes

## 🔧 Configuration

### Model Selection
```python
EMBEDDING_CONFIGS = {
    'nomic-embed-text': {
        'dimension': 768,
        'context_length': 8192,
        'similarity_threshold': 0.7
    },
    'text-embedding-3-small': {
        'dimension': 1536,
        'context_length': 8191,
        'similarity_threshold': 0.8
    },
    'text-embedding-3-large': {
        'dimension': 3072,
        'context_length': 8191,
        'similarity_threshold': 0.85
    }
}
```

### Analysis Parameters
```python
SIMILARITY_CONFIG = {
    'semantic_weight': 0.6,
    'political_weight': 0.4,
    'min_similarity_threshold': 0.5,
    'max_results': 20,
    'batch_size': 100
}

CLUSTERING_CONFIG = {
    'n_clusters': 15,
    'clustering_method': 'kmeans',
    'dimensionality_reduction': True,
    'n_components': 50
}
```

## 📊 Performance Optimization

### Database Optimization
```sql
-- Vector indexes for similarity search
CREATE INDEX ON analysis.bill_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Similarity table indexes
CREATE INDEX ON analysis.bill_similarity (bill_id_1, similarity_score);
CREATE INDEX ON analysis.bill_similarity (bill_id_2, similarity_score);

-- Cluster analysis indexes
CREATE INDEX ON analysis.bill_clusters (cluster_id, cluster_confidence);
```

### Processing Optimization
- **Batch processing** for embedding generation
- **Parallel processing** for similarity computation
- **Caching** for frequently accessed embeddings
- **Incremental updates** for new bills

### Memory Management
- **Streaming processing** for large datasets
- **Chunked processing** for memory efficiency
- **Garbage collection** for embedding cleanup
- **Resource monitoring** for performance tracking

## 🔍 Quality Assurance

### Validation Metrics
1. **Similarity Accuracy**: Manual verification of similar bills
2. **Cluster Quality**: Silhouette score analysis
3. **Coverage Analysis**: Percentage of bills with embeddings
4. **Performance Metrics**: Query response times

### Testing Framework
```python
def test_embedding_quality():
    """Test embedding generation quality"""
    test_bills = get_test_bills()
    
    for bill in test_bills:
        embedding = generate_embedding(bill['text'])
        
        # Check embedding dimensions
        assert len(embedding) == expected_dimension
        
        # Check for NaN values
        assert not np.isnan(embedding).any()
        
        # Check embedding magnitude
        norm = np.linalg.norm(embedding)
        assert 0.1 < norm < 10.0

def test_similarity_accuracy():
    """Test similarity calculation accuracy"""
    similar_pairs = get_similar_bill_pairs()
    
    for bill1, bill2, expected_similarity in similar_pairs:
        computed_similarity = compute_similarity(
            get_embedding(bill1), 
            get_embedding(bill2)
        )
        
        # Check similarity is in valid range
        assert 0 <= computed_similarity <= 1.0
        
        # Check similarity matches expectation
        assert abs(computed_similarity - expected_similarity) < 0.1
```

## 📚 Related Documentation

- [Political Analysis Guide](POLITICAL_ANALYSIS_GUIDE.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Database Schema](DATABASE_SCHEMA.md)

---

**Status**: ✅ **Production Ready** - Comprehensive embeddings system with semantic similarity, clustering, and political analysis capabilities.