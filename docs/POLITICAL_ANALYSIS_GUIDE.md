# OpenDiscourse Political Analysis - Complete Guide

## Overview

This system provides comprehensive political analysis of congressional bills, including:
- **Political Bias Classification**: Democrat vs Republican leaning (-1 to +1 scale)
- **Freedom Impact Scoring**: Restrictive vs Freedom-enhancing (-1 to +1 scale)  
- **Economic Impact Analysis**: Anti-rich vs Anti-poor bias detection
- **Content Safety Analysis**: Hate speech and problematic language detection
- **Similarity Analysis**: Find politically similar bills

## Database Schema

### New Tables Created

#### `analysis.bill_political_scores`
- `political_bias_score`: -1 (Republican) to +1 (Democrat)
- `bias_confidence`: Confidence in bias classification (0-1)
- `freedom_score`: -1 (Restrictive) to +1 (Freedom-enhancing)
- `overall_political_lean`: 'Far Left', 'Left', 'Center-Left', 'Center', 'Center-Right', 'Right', 'Far Right', 'Neutral'

#### `analysis.bill_content_analysis`
- `hate_speech_score`: Hate speech detection (0-1)
- `inflammatory_language_score`: Inflammatory content (0-1)
- `divisive_language_score`: Divisive language (0-1)
- `exclusionary_language_score`: Exclusionary language (0-1)
- `authoritarian_language_score`: Authoritarian language (0-1)
- `content_safety_rating`: 'Safe', 'Concerning', 'Problematic', 'Harmful'

#### `analysis.bill_statement_analysis`
- Statement-level political analysis
- Individual bias scores for each legislative statement
- Hate speech, authoritarian, populist indicators

#### `analysis.political_keywords`
- Comprehensive keyword dictionary with weights
- Categories: 'democrat', 'republican', 'freedom', 'restrictive', 'hate'
- Weighted scoring system

## Setup Instructions

### 1. Install Database Schema
```bash
psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -f political_analysis_functions.sql
```

### 2. Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv political_env
source political_env/bin/activate

# Install dependencies
pip install psycopg2-binary python-dotenv

# For advanced features (optional)
pip install scikit-learn numpy pandas matplotlib seaborn
```

### 3. Run Political Analysis

#### Setup Database Functions
```bash
python3 political_analysis_processor.py --setup
```

#### Analyze Specific Bill
```bash
python3 political_analysis_processor.py --bill-id "your-bill-id-here"
```

#### Show Political Statistics
```bash
python3 political_analysis_processor.py --stats --congress 118
python3 political_analysis_processor.py --stats --party "Democrat"
```

#### Show Problematic Bills
```bash
python3 political_analysis_processor.py --problematic
```

#### Generate Full Report
```bash
python3 political_analysis_processor.py --report
```

#### Analyze All Bills
```bash
python3 political_analysis_processor.py --full-analysis --batch-size 50
```

## SQL Query Examples

### Get Political Analysis for Specific Bill
```sql
SELECT * FROM analysis.get_bill_political_analysis('your-bill-id-here');
```

### Find Politically Similar Bills
```sql
SELECT * FROM analysis.find_politically_similar_bills(
    'your-bill-id-here',
    0.2,  -- bias tolerance
    0.2,  -- freedom tolerance
    10     -- limit results
);
```

### Get Political Statistics by Congress
```sql
SELECT * FROM analysis.get_political_statistics(118);
```

### Get Party-Specific Analysis
```sql
SELECT * FROM analysis.get_political_statistics(NULL, 'Democrat');
SELECT * FROM analysis.get_political_statistics(NULL, 'Republican');
```

### Find Problematic Content
```sql
SELECT 
    bill_title,
    sponsor_name,
    overall_political_lean,
    hate_speech_score,
    content_safety_rating,
    flagged_phrases
FROM analysis.problematic_bills
WHERE hate_speech_score > 0.1
ORDER BY hate_speech_score DESC;
```

### Political Distribution Analysis
```sql
SELECT 
    overall_political_lean,
    COUNT(*) as bill_count,
    AVG(political_bias_score) as avg_bias,
    AVG(freedom_score) as avg_freedom,
    AVG(hate_speech_score) as avg_hate_speech
FROM analysis.political_analysis_summary
GROUP BY overall_political_lean
ORDER BY bill_count DESC;
```

### Cross-Party Bill Comparison
```sql
WITH democrat_bills AS (
    SELECT * FROM analysis.political_analysis_summary 
    WHERE sponsor_party = 'Democrat'
),
republican_bills AS (
    SELECT * FROM analysis.political_analysis_summary 
    WHERE sponsor_party = 'Republican'
)
SELECT 
    d.overall_political_lean as democrat_lean,
    r.overall_political_lean as republican_lean,
    d.political_bias_score as democrat_bias,
    r.political_bias_score as republican_bias,
    d.freedom_score as democrat_freedom,
    r.freedom_score as republican_freedom,
    d.hate_speech_score as democrat_hate,
    r.hate_speech_score as republican_hate
FROM democrat_bills d
JOIN republican_bills r ON ABS(d.political_bias_score - r.political_bias_score) < 0.1
ORDER BY ABS(d.political_bias_score - r.political_bias_score);
```

## Analysis Scoring System

### Political Bias Score (-1 to +1)
- **+1.0**: Strong Democrat leaning
- **+0.6**: Moderate Democrat leaning  
- **+0.3**: Lean Democrat
- **0.0**: Neutral/Centrist
- **-0.3**: Lean Republican
- **-0.6**: Moderate Republican leaning
- **-1.0**: Strong Republican leaning

### Freedom Impact Score (-1 to +1)
- **+1.0**: Strong freedom-enhancing (civil rights, free speech)
- **+0.5**: Moderate freedom-enhancing
- **0.0**: Neutral impact
- **-0.5**: Moderate restrictive
- **-1.0**: Strong restrictive (bans, prohibitions)

### Content Safety Rating
- **Safe**: No problematic content detected
- **Concerning**: Minor issues (low inflammatory language)
- **Problematic**: Significant issues (hate speech indicators)
- **Harmful**: Severe issues (direct hate speech, authoritarian language)

### Hate Speech Indicators
Keywords with highest weights (1.0):
- 'nazi', 'white supremacist', 'supremacist', 'terrorist'
- 'infidel', 'traitor', 'treason', 'destroy', 'eliminate'

### Inflammatory Language
- 'radical', 'extremist', 'violent', 'dangerous'
- 'threat', 'enemy', 'destroy', 'eliminate'

## Advanced Analysis Examples

### 1. Political Polarization Analysis
```sql
SELECT 
    congress_number,
    AVG(ABS(political_bias_score)) as avg_polarization,
    COUNT(*) as total_bills,
    COUNT(CASE WHEN ABS(political_bias_score) > 0.7 THEN 1 END) as extreme_bills
FROM analysis.political_analysis_summary
GROUP BY congress_number
ORDER BY congress_number;
```

### 2. Hate Speech Trend Analysis
```sql
SELECT 
    DATE_TRUNC('month', b.introduced_date) as month,
    COUNT(*) as total_bills,
    AVG(ca.hate_speech_score) as avg_hate_speech,
    COUNT(CASE WHEN ca.hate_speech_score > 0.1 THEN 1 END) as problematic_count
FROM congress.bills b
JOIN analysis.bill_content_analysis ca ON b.bill_id = ca.bill_id
GROUP BY DATE_TRUNC('month', b.introduced_date)
ORDER BY month;
```

### 3. Cross-Party Collaboration Detection
```sql
WITH bipartisan_bills AS (
    SELECT 
        ps.bill_id,
        b.official_title,
        COUNT(DISTINCT mt.party_code) as party_count
    FROM analysis.bill_political_scores ps
    JOIN congress.bills b ON ps.bill_id = b.bill_id
    JOIN congress.bill_cosponsors bc ON b.bill_id = bc.bill_id
    JOIN congress.members m ON bc.cosponsor_bioguide_id = m.bioguide_id
    JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id 
        AND mt.start_date <= b.introduced_date 
        AND (mt.end_date >= b.introduced_date OR mt.end_date IS NULL)
    GROUP BY ps.bill_id, b.official_title
    HAVING COUNT(DISTINCT mt.party_code) > 1
)
SELECT * FROM bipartisan_bills
WHERE party_count >= 2
ORDER BY party_count DESC;
```

### 4. Authoritarian Language Detection
```sql
SELECT 
    bill_title,
    sponsor_name,
    authoritarian_language_score,
    flagged_phrases
FROM analysis.political_analysis_summary
WHERE authoritarian_language_score > 0.3
ORDER BY authoritarian_language_score DESC;
```

## Integration with Embeddings

### Combine Political and Semantic Analysis
```sql
-- Find bills that are semantically similar AND politically aligned
WITH semantic_similar AS (
    SELECT bill_id_2, similarity_score
    FROM analysis.bill_similarity
    WHERE bill_id_1 = 'target-bill-id'
        AND similarity_score > 0.8
),
politically_aligned AS (
    SELECT bill_id, political_bias_score
    FROM analysis.bill_political_scores
    WHERE ABS(political_bias_score - (
        SELECT political_bias_score FROM analysis.bill_political_scores 
        WHERE bill_id = 'target-bill-id'
    )) < 0.2
)
SELECT 
    b.official_title,
    ps.overall_political_lean,
    ss.similarity_score,
    ps.political_bias_score
FROM congress.bills b
JOIN semantic_similar ss ON b.bill_id = ss.bill_id_2
JOIN politically_aligned pa ON b.bill_id = pa.bill_id
JOIN analysis.bill_political_scores ps ON b.bill_id = ps.bill_id
ORDER BY ss.similarity_score DESC;
```

## Monitoring and Quality Assurance

### 1. Analysis Quality Metrics
```sql
-- Check confidence levels
SELECT 
    AVG(bias_confidence) as avg_bias_confidence,
    AVG(freedom_confidence) as avg_freedom_confidence,
    AVG(hate_speech_confidence) as avg_hate_confidence,
    COUNT(*) as total_analyzed
FROM analysis.bill_political_scores ps
JOIN analysis.bill_content_analysis ca ON ps.bill_id = ca.bill_id;
```

### 2. Keyword Performance Analysis
```sql
-- Most frequently flagged keywords
SELECT 
    pk.keyword,
    pk.category,
    COUNT(*) as usage_count,
    AVG(ps.bias_confidence) as avg_confidence
FROM analysis.political_keywords pk
JOIN analysis.bill_content_analysis ca ON ca.flagged_phrases && ARRAY[pk.keyword]
JOIN analysis.bill_political_scores ps ON ca.bill_id = ps.bill_id
GROUP BY pk.keyword, pk.category
ORDER BY usage_count DESC;
```

### 3. Error Detection and Monitoring
```sql
-- Bills with low confidence scores (may need manual review)
SELECT 
    b.official_title,
    ps.bias_confidence,
    ca.hate_speech_confidence,
    ps.overall_political_lean
FROM analysis.political_analysis_summary
WHERE ps.bias_confidence < 0.3 
   OR ca.hate_speech_confidence < 0.3
ORDER BY ps.bias_confidence ASC;
```

## Ethical Considerations

### 1. Bias Mitigation
- Regular validation of keyword weights
- Manual review of edge cases
- Cross-validation with multiple models
- Transparency in scoring methodology

### 2. Context Awareness
- Consider historical context of legislation
- Account for regional political differences
- Understand legislative intent vs. impact
- Avoid over-reliance on keyword matching

### 3. Privacy and Safety
- Anonymize individual analysis where appropriate
- Secure storage of sensitive analysis results
- Regular audit of analysis accuracy
- Clear documentation of limitations

## Performance Optimization

### 1. Database Indexes
All critical indexes are created automatically:
- Political bias scores
- Content safety ratings
- Keyword searches (trigram)
- Similarity scores

### 2. Batch Processing
- Configurable batch sizes (default: 100)
- Progress tracking and error handling
- Automatic retry on failures
- Memory-efficient processing

### 3. Caching Strategy
- Cache frequently accessed analysis results
- Materialized views for complex queries
- Periodic refresh of cached data
- Query optimization monitoring

## Troubleshooting

### Common Issues

1. **Low Confidence Scores**
   - Check bill text quality
   - Verify keyword dictionary completeness
   - Consider context-specific language

2. **False Positives in Hate Speech**
   - Review keyword weights
   - Add contextual exceptions
   - Implement phrase-level analysis

3. **Performance Issues**
   - Reduce batch size
   - Check database indexes
   - Monitor memory usage

### Debug Queries
```sql
-- Check analysis progress
SELECT 
    COUNT(*) as total_bills,
    COUNT(CASE WHEN ps.bill_id IS NOT NULL THEN 1 END) as analyzed_bills,
    COUNT(CASE WHEN ca.bill_id IS NOT NULL THEN 1 END) as content_analyzed
FROM congress.bills b
LEFT JOIN analysis.bill_political_scores ps ON b.bill_id = ps.bill_id
LEFT JOIN analysis.bill_content_analysis ca ON b.bill_id = ca.bill_id;

-- Find bills with conflicting scores
SELECT 
    b.official_title,
    ps.political_bias_score,
    ps.overall_political_lean,
    ca.hate_speech_score,
    ca.content_safety_rating
FROM analysis.political_analysis_summary
WHERE (ps.political_bias_score > 0.5 AND ca.hate_speech_score > 0.1)
   OR (ps.political_bias_score < -0.5 AND ca.hate_speech_score > 0.1)
ORDER BY ps.political_bias_score;
```

This comprehensive political analysis system provides deep insights into legislative content while maintaining ethical standards and performance optimization.