# OpenDiscourse Embeddings Analysis - Setup and Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv embeddings_env
source embeddings_env/bin/activate

# Install Python packages
pip install psycopg2-binary python-dotenv ollama scikit-learn numpy

# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull embedding models
ollama pull all-minilm:l6-v2          # Fast, lightweight (384-dim)
ollama pull nomic-embed-text          # Good balance (768-dim)
```

### 2. Setup Database Schema

```bash
# Run the schema setup
psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -f setup_analysis_schema.sql
```

### 3. Process Embeddings

```bash
# Process all bills (this will take time)
python3 embeddings_processor.py --model all-minilm:l6-v2 --batch-size 50

# Check progress
python3 embeddings_processor.py --status

# Process with different model
python3 embeddings_processor.py --model nomic-embed-text --batch-size 25
```

### 4. Analyze Similarities

```bash
# Calculate similarities for all processed embeddings
python3 similarity_analyzer.py --model all-minilm:l6-v2 --threshold 0.7

# Show similarity statistics
python3 similarity_analyzer.py --stats

# Find similar bills for a specific bill
python3 similarity_analyzer.py --bill-id "your-bill-id-here" --threshold 0.8
```

## Database Tables Affected

### Original Tables (READ-ONLY)
- `congress.bills` - Source bill data
- `congress.members` - Sponsor information  
- `congress.member_terms` - Party/state affiliations
- `congress.bill_actions` - Legislative actions

### New Analysis Tables (SEPARATE SCHEMA)
- `analysis.bill_embeddings` - Generated embeddings
- `analysis.bill_similarity` - Similarity scores
- `analysis.bill_clusters` - Clustering results

### Analysis Views (READ-ONLY)
- `analysis.bills_with_sponsors` - Bills with enriched sponsor data
- `analysis.cluster_summary` - Cluster statistics
- `analysis.high_similarity_pairs` - Very similar bills
- `analysis.embedding_progress` - Processing status

## Usage Examples

### SQL Queries for Analysis

```sql
-- Find similar bills to a specific bill
SELECT * FROM analysis.get_similar_bills(
    'your-bill-id-here',
    0.7,  -- similarity threshold
    10     -- limit results
);

-- Get cluster analysis
SELECT 
    cluster_number,
    bill_count,
    avg_confidence,
    array_agg(DISTINCT bill_type) as bill_types
FROM analysis.cluster_summary 
WHERE model_name = 'all-minilm:l6-v2'
ORDER BY bill_count DESC;

-- Find very similar bill pairs
SELECT * FROM analysis.high_similarity_pairs 
WHERE similarity_score >= 0.9
LIMIT 20;

-- Check embedding processing progress
SELECT * FROM analysis.embedding_progress;

-- Get bills by complexity and similarity
SELECT 
    b.bill_id,
    b.official_title,
    b.bill_type,
    LENGTH(b.official_title + ' ' + COALESCE(b.summary_text, '')) as text_length,
    CASE 
        WHEN LENGTH(b.official_title + ' ' + COALESCE(b.summary_text, '')) < 50 THEN 'simple'
        WHEN LENGTH(b.official_title + ' ' + COALESCE(b.summary_text, '')) <= 200 THEN 'moderate'
        ELSE 'complex'
    END as complexity_level
FROM congress.bills b
WHERE b.bill_id IN (
    SELECT DISTINCT bill_id_1 FROM analysis.bill_similarity 
    WHERE similarity_score >= 0.8
);
```

### Python Integration Examples

```python
# Example: Find similar bills and analyze patterns
import psycopg2
from psycopg2.extras import DictCursor

# Connect to database
conn = psycopg2.connect(
    dbname="opendiscourse",
    user="cbwinslow", 
    host="/var/run/postgresql",
    port="5432"
)
cursor = conn.cursor(cursor_factory=DictCursor)

# Get high-similarity pairs
cursor.execute("""
    SELECT * FROM analysis.high_similarity_pairs 
    WHERE similarity_score >= 0.85
    ORDER BY similarity_score DESC
    LIMIT 10
""")

similar_pairs = cursor.fetchall()

# Analyze patterns
for pair in similar_pairs:
    print(f"Bills {pair['bill_id_1']} and {pair['bill_id_2']}")
    print(f"  Similarity: {pair['similarity_score']:.3f}")
    print(f"  {pair['title_1']}")
    print(f"  {pair['title_2']}")
    print(f"  Types: {pair['type_1']} vs {pair['type_2']}")
    print()

# Get cluster information
cursor.execute("""
    SELECT * FROM analysis.cluster_summary 
    WHERE model_name = 'all-minilm:l6-v2'
    ORDER BY bill_count DESC
    LIMIT 5
""")

clusters = cursor.fetchall()
for cluster in clusters:
    print(f"Cluster {cluster['cluster_number']}: {cluster['bill_count']} bills")
    print(f"  Average confidence: {cluster['avg_confidence']:.3f}")
    print(f"  Bill types: {cluster['bill_types']}")
    print()
```

## Performance Considerations

### Batch Processing
- **Embeddings**: Process 50-100 bills at a time
- **Similarities**: Use threshold to limit comparisons
- **Memory**: Monitor RAM usage with large datasets

### Database Optimization
```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM analysis.bill_similarity 
WHERE similarity_score >= 0.8;

-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'analysis'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Model Selection Guidelines
- **all-minilm:l6-v2** (384-dim): Fast, good for initial analysis
- **nomic-embed-text** (768-dim): Better quality, moderate speed
- **mxbai-embed-large** (1024-dim): Highest quality, slower

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Check if Ollama is running
   ollama list
   
   # Start Ollama service
   ollama serve
   ```

2. **Database Connection Issues**
   ```bash
   # Test connection
   psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -c "SELECT 1;"
   ```

3. **Memory Issues with Large Datasets**
   ```python
   # Reduce batch size
   python3 embeddings_processor.py --batch-size 25
   
   # Use smaller model
   python3 embeddings_processor.py --model all-minilm:l6-v2
   ```

4. **Slow Similarity Calculations**
   ```bash
   # Increase threshold to reduce comparisons
   python3 similarity_analyzer.py --threshold 0.8 --max-comparisons 5000
   ```

### Monitoring Progress

```sql
-- Check embedding progress
SELECT * FROM analysis.embedding_progress;

-- Monitor processing errors
SELECT 
    COUNT(*) as error_count,
    error_message
FROM analysis.bill_embeddings 
WHERE processing_status = 'failed'
GROUP BY error_message
ORDER BY error_count DESC;

-- Check database performance
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
WHERE query LIKE '%analysis.%'
ORDER BY total_time DESC
LIMIT 10;
```

## Advanced Analysis

### Cross-Model Comparison
```sql
-- Compare embeddings from different models
SELECT 
    bs1.bill_id_1,
    bs1.bill_id_2,
    bs1.similarity_score as similarity_model1,
    bs2.similarity_score as similarity_model2,
    ABS(bs1.similarity_score - bs2.similarity_score) as difference
FROM analysis.bill_similarity bs1
JOIN analysis.bill_similarity bs2 ON 
    bs1.bill_id_1 = bs2.bill_id_1 AND 
    bs1.bill_id_2 = bs2.bill_id_2
WHERE bs1.model_name = 'all-minilm:l6-v2'
    AND bs2.model_name = 'nomic-embed-text'
ORDER BY difference DESC;
```

### Temporal Analysis
```sql
-- Analyze similarity trends over time
SELECT 
    DATE_TRUNC('month', b.introduced_date) as month,
    COUNT(*) as bill_count,
    AVG(bs.similarity_score) as avg_similarity
FROM congress.bills b
JOIN analysis.bill_similarity bs ON b.bill_id = bs.bill_id_1
WHERE bs.model_name = 'all-minilm:l6-v2'
    AND b.introduced_date >= '2023-01-01'
GROUP BY DATE_TRUNC('month', b.introduced_date)
ORDER BY month;
```

### Party-Based Analysis
```sql
-- Analyze cross-party bill similarities
SELECT 
    mt1.party_code as party_1,
    mt2.party_code as party_2,
    COUNT(*) as similar_pairs,
    AVG(bs.similarity_score) as avg_similarity
FROM analysis.bill_similarity bs
JOIN congress.bills b1 ON bs.bill_id_1 = b1.bill_id
JOIN congress.bills b2 ON bs.bill_id_2 = b2.bill_id
JOIN congress.member_terms mt1 ON b1.sponsor_bioguide_id = mt1.bioguide_id
JOIN congress.member_terms mt2 ON b2.sponsor_bioguide_id = mt2.bioguide_id
WHERE bs.model_name = 'all-minilm:l6-v2'
    AND bs.similarity_score >= 0.7
GROUP BY mt1.party_code, mt2.party_code
ORDER BY similar_pairs DESC;
```

## Data Safety

### Backup Analysis Tables
```bash
# Export analysis results
pg_dump -h /var/run/postgresql -U cbwinslow -d opendiscourse \
    -t analysis.bill_embeddings \
    -t analysis.bill_similarity \
    -t analysis.bill_clusters \
    > analysis_backup_$(date +%Y%m%d).sql
```

### Recreate Analysis Schema
```bash
# Clean start - drop and recreate
psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -c "
    DROP SCHEMA IF EXISTS analysis CASCADE;
    \i setup_analysis_schema.sql;
"
```

This comprehensive setup ensures safe, non-invasive analysis while providing powerful similarity and clustering capabilities for legislative insights.