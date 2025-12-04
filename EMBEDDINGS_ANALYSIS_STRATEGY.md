# OpenDiscourse Embeddings Analysis Strategy

## Recommended Embeddings Models

### 1. **Ollama (Recommended for Local Processing)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models
ollama pull all-minilm:l6-v2          # Fast, lightweight (384-dim)
ollama pull nomic-embed-text          # Good balance (768-dim)
ollama pull mxbai-embed-large         # High quality (1024-dim)
```

**Advantages:**
- Free, local processing
- No API rate limits
- Multiple model sizes available
- Easy integration with Python

### 2. **OpenRouter (Recommended for Cloud Processing)**
```python
# Install OpenRouter SDK
pip install openrouter

# Recommended free models
models = [
    "microsoft/wizardlm-2-8x22b",     # Good for legislative text
    "meta-llama/llama-3.1-8b-instruct",  # General purpose
    "google/gemma-2-9b-it"           # Fast, efficient
]
```

### 3. **Hybrid Approach (Recommended)**
- **Ollama** for batch processing (all bills)
- **OpenRouter** for real-time queries and similarity search

## Database Analysis Procedure

### Phase 1: Non-Invasive Analysis Setup

#### 1.1 Create Analysis Schema
```sql
-- Create separate analysis schema (doesn't touch original data)
CREATE SCHEMA IF NOT EXISTS analysis;

-- Grant permissions
GRANT ALL ON SCHEMA analysis TO cbwinslow;
GRANT ALL ON ALL TABLES IN SCHEMA analysis TO cbwinslow;
```

#### 1.2 Create Analysis Views (Read-Only)
```sql
-- View for bills with sponsor information
CREATE OR REPLACE VIEW analysis.bills_with_sponsors AS
SELECT 
    b.bill_id,
    b.congress_number,
    b.bill_type,
    b.bill_number,
    b.official_title,
    b.summary_text,
    b.policy_area,
    b.sponsor_bioguide_id,
    b.introduced_date,
    b.latest_action_date,
    b.latest_action_text,
    m.first_name || ' ' || m.last_name as sponsor_name,
    mt.party_code as sponsor_party,
    mt.state_code as sponsor_state,
    -- Combined text for embedding
    COALESCE(b.official_title, '') || ' ' || COALESCE(b.summary_text, '') as combined_text
FROM congress.bills b
LEFT JOIN congress.members m ON b.sponsor_bioguide_id = m.bioguide_id
LEFT JOIN congress.member_terms mt ON b.sponsor_bioguide_id = mt.bioguide_id 
    AND mt.start_date <= b.introduced_date 
    AND (mt.end_date >= b.introduced_date OR mt.end_date IS NULL)
WHERE b.official_title IS NOT NULL;
```

#### 1.3 Create Temporary Analysis Tables
```sql
-- Table for storing embeddings (temporary, can be recreated)
CREATE TABLE IF NOT EXISTS analysis.bill_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES congress.bills(bill_id),
    model_name TEXT NOT NULL,
    embedding_vector VECTOR(1024), -- Supports different dimensions
    embedding_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status TEXT DEFAULT 'pending',
    INDEX (bill_id),
    INDEX (model_name),
    INDEX (processing_status)
);

-- Table for similarity results
CREATE TABLE IF NOT EXISTS analysis.bill_similarity (
    similarity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id_1 UUID NOT NULL REFERENCES congress.bills(bill_id),
    bill_id_2 UUID NOT NULL REFERENCES congress.bills(bill_id),
    similarity_score FLOAT NOT NULL,
    model_name TEXT NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX (bill_id_1),
    INDEX (bill_id_2),
    INDEX (similarity_score)
);

-- Table for clustering results
CREATE TABLE IF NOT EXISTS analysis.bill_clusters (
    cluster_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES congress.bills(bill_id),
    cluster_number INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    clustering_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score FLOAT,
    INDEX (cluster_number),
    INDEX (bill_id)
);
```

### Phase 2: Embeddings Processing Pipeline

#### 2.1 Python Processing Functions
```python
# embeddings_processor.py
import ollama
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any
import logging

class EmbeddingsProcessor:
    def __init__(self, db_config: Dict[str, str], model_name: str = "all-minilm:l6-v2"):
        self.db_config = db_config
        self.model_name = model_name
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        
    def get_pending_bills(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Get bills pending embedding processing"""
        query = """
        SELECT bill_id, combined_text, congress_number, bill_type, bill_number
        FROM analysis.bills_with_sponsors 
        WHERE bill_id NOT IN (
            SELECT bill_id FROM analysis.bill_embeddings 
            WHERE model_name = %s AND processing_status = 'completed'
        )
        LIMIT %s
        """
        self.cursor.execute(query, (self.model_name, batch_size))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Ollama"""
        try:
            response = ollama.embeddings(
                model=self.model_name,
                prompt=text
            )
            return np.array(response['embedding'])
        except Exception as e:
            logging.error(f"Embedding generation failed: {e}")
            return None
    
    def store_embeddings(self, embeddings_data: List[Dict[str, Any]]):
        """Store embeddings in analysis table"""
        if not embeddings_data:
            return
            
        values = [
            (
                data['bill_id'],
                self.model_name,
                data['embedding'].tolist(),
                'completed'
            )
            for data in embeddings_data
        ]
        
        query = """
        INSERT INTO analysis.bill_embeddings 
        (bill_id, model_name, embedding_vector, processing_status)
        VALUES %s
        """
        execute_values(self.cursor, query, values)
        self.conn.commit()
        
    def process_batch(self, batch_size: int = 100):
        """Process a batch of bills"""
        bills = self.get_pending_bills(batch_size)
        if not bills:
            return False
            
        embeddings_data = []
        for bill in bills:
            embedding = self.generate_embedding(bill['combined_text'])
            if embedding is not None:
                embeddings_data.append({
                    'bill_id': bill['bill_id'],
                    'embedding': embedding
                })
                
        self.store_embeddings(embeddings_data)
        logging.info(f"Processed {len(embeddings_data)} embeddings")
        return True
```

#### 2.2 Similarity Analysis Functions
```python
# similarity_analyzer.py
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SimilarityAnalyzer:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        
    def calculate_similarities(self, bill_id: str, threshold: float = 0.7):
        """Calculate similarities for a specific bill"""
        # Get target embedding
        self.cursor.execute("""
            SELECT embedding_vector 
            FROM analysis.bill_embeddings 
            WHERE bill_id = %s AND processing_status = 'completed'
        """, (bill_id,))
        target_result = self.cursor.fetchone()
        
        if not target_result:
            return []
            
        target_embedding = np.array(target_result[0])
        
        # Get all other embeddings
        self.cursor.execute("""
            SELECT bill_id, embedding_vector 
            FROM analysis.bill_embeddings 
            WHERE bill_id != %s AND processing_status = 'completed'
        """, (bill_id,))
        
        similarities = []
        for row in self.cursor.fetchall():
            other_id, other_embedding = row[0], np.array(row[1])
            similarity = cosine_similarity(
                target_embedding.reshape(1, -1),
                other_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity >= threshold:
                similarities.append({
                    'bill_id_1': bill_id,
                    'bill_id_2': other_id,
                    'similarity_score': float(similarity)
                })
                
        return similarities
    
    def store_similarities(self, similarities: List[Dict[str, Any]]):
        """Store similarity results"""
        if not similarities:
            return
            
        values = [
            (sim['bill_id_1'], sim['bill_id_2'], sim['similarity_score'], self.model_name)
            for sim in similarities
        ]
        
        query = """
        INSERT INTO analysis.bill_similarity 
        (bill_id_1, bill_id_2, similarity_score, model_name)
        VALUES %s
        ON CONFLICT DO NOTHING
        """
        execute_values(self.cursor, query, values)
        self.conn.commit()
```

### Phase 3: Clustering Analysis

#### 3.1 Clustering Functions
```python
# clustering_analyzer.py
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import numpy as np

class ClusteringAnalyzer:
    def __init__(self, db_config: Dict[str, str], n_clusters: int = 50):
        self.db_config = db_config
        self.n_clusters = n_clusters
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        
    def get_all_embeddings(self) -> tuple:
        """Get all embeddings for clustering"""
        self.cursor.execute("""
            SELECT bill_id, embedding_vector 
            FROM analysis.bill_embeddings 
            WHERE processing_status = 'completed'
        """)
        
        bill_ids = []
        embeddings = []
        
        for row in self.cursor.fetchall():
            bill_ids.append(row[0])
            embeddings.append(np.array(row[1]))
            
        return bill_ids, np.array(embeddings)
    
    def perform_clustering(self):
        """Perform K-means clustering"""
        bill_ids, embeddings = self.get_all_embeddings()
        
        if len(embeddings) < self.n_clusters:
            self.n_clusters = len(embeddings)
            
        # Perform clustering
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Store results
        for bill_id, cluster_id in zip(bill_ids, cluster_labels):
            self.cursor.execute("""
                INSERT INTO analysis.bill_clusters 
                (bill_id, cluster_number, model_name, confidence_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (bill_id, model_name) 
                DO UPDATE SET 
                    cluster_number = EXCLUDED.cluster_number,
                    confidence_score = EXCLUDED.confidence_score
            """, (bill_id, int(cluster_id), self.model_name, 1.0))
            
        self.conn.commit()
        
        return {
            'n_clusters': self.n_clusters,
            'n_bills': len(bill_ids),
            'model_name': self.model_name
        }
```

### Phase 4: Analysis Functions and Views

#### 4.1 Create Analysis Functions
```sql
-- Function to get similar bills
CREATE OR REPLACE FUNCTION analysis.get_similar_bills(
    target_bill_id UUID,
    similarity_threshold FLOAT DEFAULT 0.7,
    limit_count INTEGER DEFAULT 10
) RETURNS TABLE (
    similar_bill_id UUID,
    similarity_score FLOAT,
    bill_title TEXT,
    bill_type TEXT,
    sponsor_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bs.bill_id_2 as similar_bill_id,
        bs.similarity_score,
        b.official_title as bill_title,
        b.bill_type,
        m.first_name || ' ' || m.last_name as sponsor_name
    FROM analysis.bill_similarity bs
    JOIN congress.bills b ON bs.bill_id_2 = b.bill_id
    LEFT JOIN congress.members m ON b.sponsor_bioguide_id = m.bioguide_id
    WHERE bs.bill_id_1 = target_bill_id
        AND bs.similarity_score >= similarity_threshold
    ORDER BY bs.similarity_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get cluster members
CREATE OR REPLACE FUNCTION analysis.get_cluster_members(
    cluster_number INTEGER,
    model_name TEXT DEFAULT 'all-minilm:l6-v2'
) RETURNS TABLE (
    bill_id UUID,
    bill_title TEXT,
    bill_type TEXT,
    sponsor_name TEXT,
    confidence_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bc.bill_id,
        b.official_title as bill_title,
        b.bill_type,
        m.first_name || ' ' || m.last_name as sponsor_name,
        bc.confidence_score
    FROM analysis.bill_clusters bc
    JOIN congress.bills b ON bc.bill_id = b.bill_id
    LEFT JOIN congress.members m ON b.sponsor_bioguide_id = m.bioguide_id
    WHERE bc.cluster_number = cluster_number
        AND bc.model_name = model_name
    ORDER BY bc.confidence_score DESC;
END;
$$ LANGUAGE plpgsql;
```

#### 4.2 Create Analysis Views
```sql
-- View for cluster analysis
CREATE OR REPLACE VIEW analysis.cluster_summary AS
SELECT 
    cluster_number,
    model_name,
    COUNT(*) as bill_count,
    AVG(confidence_score) as avg_confidence,
    array_agg(bill_type) as bill_types,
    array_agg(sponsor_bioguide_id) as sponsors
FROM analysis.bill_clusters bc
JOIN congress.bills b ON bc.bill_id = b.bill_id
GROUP BY cluster_number, model_name
ORDER BY bill_count DESC;

-- View for similarity analysis
CREATE OR REPLACE VIEW analysis.high_similarity_pairs AS
SELECT 
    bs.bill_id_1,
    bs.bill_id_2,
    bs.similarity_score,
    b1.official_title as title_1,
    b2.official_title as title_2,
    b1.bill_type as type_1,
    b2.bill_type as type_2
FROM analysis.bill_similarity bs
JOIN congress.bills b1 ON bs.bill_id_1 = b1.bill_id
JOIN congress.bills b2 ON bs.bill_id_2 = b2.bill_id
WHERE bs.similarity_score >= 0.8
ORDER BY bs.similarity_score DESC;
```

## Database Tables and Fields Documentation

### Original Tables (READ-ONLY ACCESS)
```
congress.bills
├── bill_id (UUID, PK)
├── congress_number (INTEGER)
├── bill_type (TEXT)
├── bill_number (INTEGER)
├── official_title (TEXT)
├── summary_text (TEXT)
├── policy_area (TEXT)
├── sponsor_bioguide_id (TEXT)
├── introduced_date (DATE)
├── latest_action_date (DATE)
├── latest_action_text (TEXT)
└── [other fields...]

congress.members
├── bioguide_id (TEXT, PK)
├── first_name (TEXT)
├── last_name (TEXT)
├── [other fields...]

congress.member_terms
├── term_id (UUID, PK)
├── bioguide_id (TEXT)
├── congress_number (INTEGER)
├── party_code (TEXT)
├── state_code (TEXT)
├── [other fields...]

congress.bill_actions
├── bill_action_id (UUID, PK)
├── bill_id (UUID, FK)
├── action_date (TEXT)
├── action_text (TEXT)
├── action_code (TEXT)
└── [other fields...]
```

### Analysis Tables (NEW, SEPARATE SCHEMA)
```
analysis.bill_embeddings
├── embedding_id (UUID, PK)
├── bill_id (UUID, FK to congress.bills)
├── model_name (TEXT)
├── embedding_vector (VECTOR)
├── embedding_date (TIMESTAMP)
├── processing_status (TEXT)
└── [indexes...]

analysis.bill_similarity
├── similarity_id (UUID, PK)
├── bill_id_1 (UUID, FK)
├── bill_id_2 (UUID, FK)
├── similarity_score (FLOAT)
├── model_name (TEXT)
├── analysis_date (TIMESTAMP)
└── [indexes...]

analysis.bill_clusters
├── cluster_id (UUID, PK)
├── bill_id (UUID, FK)
├── cluster_number (INTEGER)
├── model_name (TEXT)
├── clustering_date (TIMESTAMP)
├── confidence_score (FLOAT)
└── [indexes...]
```

### Analysis Views (READ-ONLY)
```
analysis.bills_with_sponsors (View)
├── bill_id
├── congress_number
├── bill_type
├── bill_number
├── official_title
├── summary_text
├── combined_text (derived)
├── sponsor_name (derived)
├── sponsor_party (derived)
├── sponsor_state (derived)
└── [other fields...]

analysis.cluster_summary (View)
├── cluster_number
├── model_name
├── bill_count
├── avg_confidence
├── bill_types (array)
└── sponsors (array)

analysis.high_similarity_pairs (View)
├── bill_id_1
├── bill_id_2
├── similarity_score
├── title_1
├── title_2
├── type_1
└── type_2
```

## Processing Workflow

### Step 1: Setup
```bash
# 1. Install dependencies
pip install ollama psycopg2-binary numpy scikit-learn

# 2. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 3. Pull models
ollama pull all-minilm:l6-v2
ollama pull nomic-embed-text

# 4. Create analysis schema (run SQL above)
psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -f setup_analysis_schema.sql
```

### Step 2: Batch Processing
```python
# process_embeddings.py
from embeddings_processor import EmbeddingsProcessor

db_config = {
    'dbname': 'opendiscourse',
    'user': 'cbwinslow',
    'host': '/var/run/postgresql',
    'port': '5432'
}

processor = EmbeddingsProcessor(db_config, 'all-minilm:l6-v2')
processor.connect_db()

# Process all bills in batches
while True:
    success = processor.process_batch(batch_size=50)
    if not success:
        break  # No more bills to process
```

### Step 3: Similarity Analysis
```python
# analyze_similarities.py
from similarity_analyzer import SimilarityAnalyzer

analyzer = SimilarityAnalyzer(db_config)

# Get all bill IDs
analyzer.cursor.execute("SELECT DISTINCT bill_id FROM analysis.bill_embeddings")
bill_ids = [row[0] for row in analyzer.cursor.fetchall()]

# Calculate similarities for each bill
for bill_id in bill_ids:
    similarities = analyzer.calculate_similarities(bill_id, threshold=0.7)
    analyzer.store_similarities(similarities)
    print(f"Processed similarities for {bill_id}")
```

### Step 4: Clustering
```python
# cluster_analysis.py
from clustering_analyzer import ClusteringAnalyzer

clusterer = ClusteringAnalyzer(db_config, n_clusters=50)
results = clusterer.perform_clustering()
print(f"Created {results['n_clusters']} clusters for {results['n_bills']} bills")
```

## Safety and Preservation Measures

### 1. **Original Data Protection**
- All analysis tables in separate `analysis` schema
- Only read access to original `congress` schema
- No modifications to original table structures
- Views used for data access (read-only)

### 2. **Reproducibility**
- All analysis tables include `model_name` field
- Timestamps for all processing operations
- Processing status tracking
- Easy to recreate/drop analysis tables

### 3. **Performance Considerations**
- Batch processing to avoid memory issues
- Indexes on all foreign keys and search fields
- Vector operations optimized with pgvector extension
- Configurable batch sizes and thresholds

### 4. **Data Quality**
- Processing status tracking (`pending`, `processing`, `completed`, `failed`)
- Confidence scores for all results
- Easy identification and reprocessing of failed items

## Usage Examples

### Find Similar Bills
```sql
-- Find bills similar to a specific bill
SELECT * FROM analysis.get_similar_bills(
    'your-bill-id-here',
    0.7,  -- similarity threshold
    10     -- limit results
);
```

### Analyze Clusters
```sql
-- Get cluster summary
SELECT * FROM analysis.cluster_summary 
WHERE model_name = 'all-minilm:l6-v2'
ORDER BY bill_count DESC;

-- Get members of a specific cluster
SELECT * FROM analysis.get_cluster_members(5);
```

### High Similarity Pairs
```sql
-- Find very similar bill pairs
SELECT * FROM analysis.high_similarity_pairs 
WHERE similarity_score >= 0.9;
```

This approach ensures complete separation of analysis from production data while providing powerful similarity and clustering capabilities for legislative analysis.