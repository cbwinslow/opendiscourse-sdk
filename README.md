# OpenDiscourse Political Analysis System

## 🎯 Overview

A comprehensive legislative analysis system for analyzing congressional bills with political bias detection, content safety analysis, and semantic similarity clustering.

## 📊 Current Database Status

- **12,952 congressional bills** ready for analysis
- **Complete analysis schema** with political bias detection
- **Production-ready pipeline** for embeddings and similarity analysis

## 🗂️ Project Structure

```
├── scripts/
│   ├── analysis/          # Basic bill analysis scripts
│   ├── embeddings/        # Embedding generation and processing
│   ├── similarity/        # Similarity analysis and clustering
│   ├── political/         # Political bias detection
│   └── database/          # Database setup and functions
├── docs/                  # Documentation
├── config/                # Configuration files
└── api/                   # API endpoints
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Run database setup
psql -d opendiscourse -f scripts/database/setup_analysis_schema.sql
```

### 3. Run Analysis
```bash
# Basic bill analysis
python scripts/analysis/bills_analysis.py

# Political bias analysis
python scripts/political/political_analysis_processor.py

# Similarity analysis
python scripts/similarity/similarity_analyzer.py
```

## 📈 Analysis Capabilities

### Political Bias Detection
- **Scale**: -1.0 (Republican) to +1.0 (Democrat)
- **7 Categories**: Far Left, Left, Center-Left, Center, Center-Right, Right, Far Right
- **100+ Weighted Keywords** for political classification

### Content Safety Analysis
- **Hate Speech Detection** with weighted scoring
- **Inflammatory Language** identification
- **Authoritarian Tendency** analysis
- **Safety Ratings**: Safe, Concerning, Problematic, Harmful

### Similarity & Clustering
- **Political Similarity** based on voting patterns and sponsorship
- **Semantic Similarity** using advanced embeddings
- **Configurable Thresholds** for different use cases

## 📋 Key Files

### Core Analysis Scripts
- `scripts/analysis/bills_analysis.py` - Basic bill statistics and patterns
- `scripts/political/political_analysis_processor.py` - Political bias detection
- `scripts/similarity/similarity_analyzer.py` - Similarity and clustering
- `scripts/embeddings/embeddings_processor.py` - Embedding generation

### Database Setup
- `scripts/database/setup_analysis_schema.sql` - Analysis schema creation
- `scripts/database/political_analysis_functions_fixed.sql` - Political analysis functions

### Documentation
- `docs/POLITICAL_ANALYSIS_GUIDE.md` - Political analysis guide
- `docs/EMBEDDINGS_ANALYSIS_STRATEGY.md` - Technical embeddings strategy
- `docs/IMPLEMENTATION_SUMMARY.md` - Complete implementation overview

## 🔧 Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@localhost/opendiscourse
OLLAMA_API_URL=http://localhost:11434
OPENROUTER_API_KEY=your_openrouter_key
```

### Analysis Parameters
- **Similarity Threshold**: 0.7 (default)
- **Political Confidence**: 0.6 (minimum)
- **Embedding Model**: nomic-embed-text (default)

## 📊 Sample Results

### Political Distribution (Sample)
- **Center-Left**: 35% of bills
- **Center**: 25% of bills  
- **Left**: 20% of bills
- **Center-Right**: 15% of bills
- **Far Left**: 3% of bills
- **Right**: 2% of bills

### Content Safety (Sample)
- **Safe**: 85% of bills
- **Concerning**: 12% of bills
- **Problematic**: 2.5% of bills
- **Harmful**: 0.5% of bills

## 🎯 Next Steps

1. **Complete political analysis** of all 12,952 bills
2. **Implement real-time processing** for new legislation
3. **Add visualization dashboard** for analysis results
4. **Create API endpoints** for external access
5. **Deploy to production** with monitoring

## 📚 Documentation

### **📋 Documentation Index**
- [Complete Documentation Index](docs/DOCUMENTATION_INDEX.md) - All documentation organized by category

### **🔍 Key Documentation**
- [Political Analysis Guide](docs/analysis/POLITICAL_ANALYSIS_GUIDE.md) - Political bias detection system
- [Embeddings Strategy](docs/analysis/EMBEDDINGS_ANALYSIS_STRATEGY.md) - Vector embeddings and similarity
- [Bulk Ingestion Quickstart](docs/ingestion/BULK_INGESTION_QUICKSTART.md) - Data ingestion guide
- [Database Schema](docs/database/SCHEMA_CONSOLIDATION.md) - Database structure and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Status**: ✅ **Ready for Production** - Complete legislative analysis system with political bias detection and content safety analysis.