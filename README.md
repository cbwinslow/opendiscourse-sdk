# OpenDiscourse Analysis Suite

A comprehensive legislative analysis system for political bias detection, content safety analysis, and semantic similarity analysis of congressional bills.

## 📁 **Project Structure**

```
opendiscourse/
├── scripts/
│   ├── analysis/           # Bill analysis and NLP processing
│   │   ├── bills_analysis.py
│   │   └── bills_analysis_simple.py
│   ├── database/          # Database setup and schema management
│   │   ├── setup_analysis_schema_simple.sql
│   │   └── setup_analysis_schema.sql
│   ├── embeddings/         # Text embedding generation and processing
│   │   └── embeddings_processor.py
│   ├── similarity/         # Similarity analysis and clustering
│   │   └── similarity_analyzer.py
│   ├── poltical/          # Political bias and content analysis
│   │   ├── political_analysis_processor.py
│   │   └── political_analysis_functions_fixed.sql
│   └── utils/             # Utility scripts
│       ├── setup.py
│       ├── setup_project_v2.py
│       └── setup_vector_databases.py
├── docs/                 # Documentation and guides
│   ├── EMBEDDINGS_ANALYSIS_STRATEGY.md
│   ├── EMBEDDINGS_SETUP_GUIDE.md
│   ├── POLITICAL_ANALYSIS_GUIDE.md
│   ├── POLITICAL_ANALYSIS_COMPLETE.md
│   └── IMPLEMENTATION_SUMMARY.md
├── config/               # Configuration files
├── tests/                # Test suites
│   ├── unit/           # Unit tests for individual components
│   └── integration/    # Integration tests for full workflows
├── analysis_env/          # Virtual environment for analysis
└── .env.example          # Environment variables template
```

## 🚀 **Quick Start**

### 1. **Environment Setup**
```bash
# Create virtual environment
python3 -m venv analysis_env
source analysis_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# For embeddings (optional)
pip install ollama  # Local processing
# OR
pip install openai  # Cloud processing
```

### 2. **Database Setup**
```bash
# Setup analysis schema
psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -f scripts/database/setup_analysis_schema_simple.sql

# Setup political analysis functions
psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -f scripts/database/political_analysis_functions_fixed.sql
```

### 3. **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database and API keys
nano .env
```

## 📊 **Analysis Capabilities**

### **Political Analysis**
- **Bias Classification**: Democrat (-1) to Republican (+1) scale
- **Freedom Impact**: Restrictive (-1) to Freedom-enhancing (+1) scale
- **Economic Impact**: Anti-rich (-1) to Anti-poor (+1) scale
- **Content Safety**: Hate speech and problematic language detection
- **7 Categories**: Far Left, Left, Center-Left, Center, Center-Right, Right, Far Right

### **Text Analysis**
- **Statement Extraction**: 10 types of legislative actions
- **Pattern Recognition**: Commitments, prohibitions, requirements
- **Complexity Analysis**: Simple, moderate, complex classification
- **Multi-dimensional Binning**: Policy, temporal, sponsor analysis

### **Embeddings & Similarity**
- **Semantic Clustering**: Group similar legislation
- **Vector Search**: Find related bills by content
- **Model Support**: Ollama (local) and OpenRouter (cloud)
- **Batch Processing**: Scalable for large datasets

## 🗄️ **Database Schema**

### **Analysis Tables**
- `analysis.bill_political_scores`: Political bias and freedom scores
- `analysis.bill_content_analysis`: Content safety and hate speech detection
- `analysis.bill_statement_analysis`: Statement-level political analysis
- `analysis.bill_embeddings`: Text embeddings for similarity analysis
- `analysis.bill_similarity`: Similarity scores between bills
- `analysis.political_keywords`: 100+ weighted political keywords

### **Views**
- `analysis.political_analysis_summary`: Complete bill analysis
- `analysis.problematic_bills`: Bills flagged for problematic content
- `analysis.bills_with_sponsors`: Enriched bill data

## 🔧 **Usage Examples**

### **Basic Analysis**
```bash
# Analyze specific bill
python3 scripts/political/political_analysis_processor.py --bill-id "your-bill-id-here"

# Show political statistics
python3 scripts/political/political_analysis_processor.py --stats --congress 118

# Find problematic content
python3 scripts/political/political_analysis_processor.py --problematic
```

### **Advanced Analysis**
```bash
# Generate comprehensive report
python3 scripts/political/political_analysis_processor.py --report

# Full analysis of all bills
python3 scripts/political/political_analysis_processor.py --full-analysis --batch-size 50
```

### **Embeddings Analysis**
```bash
# Process embeddings (requires Ollama)
ollama pull all-minilm:l6-v2
python3 scripts/embeddings/embeddings_processor.py --model all-minilm:l6-v2 --batch-size 50

# Calculate similarities
python3 scripts/similarity/similarity_analyzer.py --model all-minilm:l6-v2 --threshold 0.7
```

### **SQL Queries**
```sql
-- Get political analysis for specific bill
SELECT * FROM analysis.get_bill_political_analysis('bill-uuid-here');

-- Find politically similar bills
SELECT * FROM analysis.find_politically_similar_bills('bill-uuid-here', 0.2, 0.2, 10);

-- Get political statistics
SELECT * FROM analysis.get_political_statistics(118);

-- Find problematic content
SELECT * FROM analysis.problematic_bills WHERE hate_speech_score > 0.1;
```

## 📈 **Key Features**

### **Political Bias Scoring**
- **Scale**: -1.0 (Strong Republican) to +1.0 (Strong Democrat)
- **Categories**: 7 political lean categories with confidence scores
- **Keyword Dictionary**: 100+ weighted political keywords
- **Context Awareness**: Considers legislative intent vs. impact

### **Content Safety Analysis**
- **Hate Speech Detection**: 0-1 scale with high-weight keywords
- **Inflammatory Language**: Divisive and radical content detection
- **Authoritarian Language**: Mandatory vs. voluntary language analysis
- **Safety Ratings**: Safe, Concerning, Problematic, Harmful

### **Similarity Analysis**
- **Political Similarity**: Find bills with similar political characteristics
- **Semantic Similarity**: Content-based similarity using embeddings
- **Configurable Tolerance**: Adjustable similarity thresholds
- **Cross-Party Analysis**: Identify bipartisan collaboration

## 🔍 **Safety & Ethics**

### **Data Protection**
- ✅ **Separate Schema**: All analysis in `analysis` schema
- ✅ **Read-Only Access**: Original tables never modified
- ✅ **Comprehensive Audit**: All operations timestamped and logged
- ✅ **No Data Loss**: Original data preserved completely

### **Bias Mitigation**
- ✅ **Transparent Scoring**: All weights and thresholds documented
- ✅ **Context Awareness**: Considers legislative intent vs. impact
- ✅ **Validation Framework**: Multiple confidence metrics
- ✅ **Review Mechanisms**: Flagged content for manual review

## 🚀 **Deployment Ready**

### **Production Setup**
```bash
# 1. Environment setup
python3 -m venv prod_env
source prod_env/bin/activate
pip install -r requirements.txt

# 2. Database setup
psql -h /var/run/postgresql -U cbwinslow -d opendiscourse -f scripts/database/setup_analysis_schema_simple.sql

# 3. Run full analysis
python3 scripts/political/political_analysis_processor.py --full-analysis
```

### **Monitoring**
```bash
# Check analysis progress
python3 scripts/political/political_analysis_processor.py --stats

# Monitor problematic content
python3 scripts/political/political_analysis_processor.py --problematic
```

## 📋 **Documentation**

### **Core Guides**
- `docs/EMBEDDINGS_ANALYSIS_STRATEGY.md`: Technical strategy for embeddings
- `docs/EMBEDDINGS_SETUP_GUIDE.md`: Setup and usage guide
- `docs/POLITICAL_ANALYSIS_GUIDE.md`: Political analysis comprehensive guide
- `docs/POLITICAL_ANALYSIS_COMPLETE.md`: Implementation summary
- `docs/IMPLEMENTATION_SUMMARY.md`: Complete implementation overview

### **API Documentation**
- Complete function documentation with examples
- SQL query examples for all analysis types
- Configuration options and tuning guides

## 🧪 **Testing**

### **Test Structure**
```bash
# Run unit tests
python3 -m pytest tests/unit/

# Run integration tests
python3 -m pytest tests/integration/

# Coverage report
python3 -m pytest --cov=scripts tests/
```

## 🎯 **Current Status**

### **✅ IMPLEMENTATION COMPLETE**
- **12,952 bills** ready for analysis
- **100+ political keywords** with weighted scoring
- **Multiple analysis dimensions** (bias, freedom, economic, content safety)
- **Advanced similarity detection** for political clustering
- **Production-ready system** with comprehensive documentation

### **🚀 READY FOR PRODUCTION**
The analysis suite is fully implemented and ready for deployment with comprehensive political bias detection, content safety analysis, and semantic similarity analysis capabilities while maintaining the highest standards of data integrity and analytical rigor.

---

## 🚀 **GETTING STARTED**

1. **Clone Repository**: `git clone <repository-url>`
2. **Environment Setup**: Follow quick start guide above
3. **Database Setup**: Run schema setup scripts
4. **Start Analysis**: Begin with basic bill analysis
5. **Review Documentation**: Check comprehensive guides in `docs/` folder

**For detailed setup and usage instructions, see the comprehensive documentation in the `docs/` folder.**