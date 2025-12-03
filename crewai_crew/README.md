# CrewAI Multi-Agent System for OpenDiscourse

A comprehensive multi-agent codebase review and analysis system using CrewAI framework and CodeRabbit AI integration.

## 🎯 Overview

This CrewAI system provides automated analysis of the OpenDiscourse codebase using multiple specialized AI agents, each with specific expertise in different domains:

- **Strategic Analysis** (CTO, CEO)
- **Technical Review** (Senior Engineer, Python Expert, Database Admin)
- **AI/ML Assessment** (AI Specialist, Algorithm Expert)
- **Quality Assurance** (Documentation Expert, Business Analyst)
- **Operations** (DevOps Engineer, Security Specialist)

## 🛠️ System Components

### 1. Crew Configuration (`crew_config.py`)
- **11 specialized agents** with distinct roles and expertise
- **Sequential task execution** for comprehensive analysis
- **Memory and caching** for improved performance
- **Configurable execution parameters**

### 2. CodeRabbit AI Integration (`coderabbit_config.py`)
- **Automated code review** with security and performance analysis
- **Custom configuration** for Python-specific analysis
- **Fallback analysis** when CLI is not available
- **Structured reporting** with JSON summaries

### 3. Diagram Generation (`diagram_generator.py`)
- **System architecture diagrams** (Mermaid format)
- **Data flow visualization** through ingestion pipeline
- **Database schema relationships** (ER diagrams)
- **API workflow sequences**
- **Monitoring architecture** layouts

### 4. Main Execution (`main_execution.py`)
- **Complete analysis pipeline** orchestration
- **Environment setup** and dependency checking
- **Executive summary generation** with strategic recommendations
- **Comprehensive reporting** with actionable insights

## 🚀 Quick Start

### Prerequisites
```bash
# Install required dependencies
pip install -r crewai_crew/requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"  # Optional
export GITHUB_TOKEN="your_github_token"  # For GitHub integration
```

### Running the Analysis

#### Method 1: Complete Analysis Pipeline
```bash
cd /home/cbwinslow/Videos/opendiscourse
python3 crewai_crew/main_execution.py
```

#### Method 2: Individual Components

**CodeRabbit AI Analysis:**
```bash
python3 scripts/run_coderabbit_review.py
```

**CrewAI Multi-Agent Analysis:**
```bash
python3 -c "
from crewai_crew.main_execution import OpenDiscourseCrewOrchestrator
orchestrator = OpenDiscourseCrewOrchestrator()
result = orchestrator.run_crewai_analysis()
print('CrewAI Analysis Result:', result)
"
```

**Diagram Generation Only:**
```bash
python3 -c "
from crewai_crew.diagram_generator import DiagramGenerator
dg = DiagramGenerator()
result = dg.generate_all_diagrams()
print('Diagrams Generated:', result)
"
```

## 📊 Output Structure

### Directory Organization
```
crewai_crew/
├── reports/           # Analysis reports and summaries
├── diagrams/          # Generated architecture diagrams
├── logs/             # Execution logs
└── artifacts/        # Additional analysis artifacts
```

### Key Output Files
- **`executive_summary.md`** - High-level strategic analysis
- **`complete_analysis_results.json`** - Detailed technical results
- **`diagrams/`** - System architecture visualizations
- **`coderabbit_*.json`** - Automated code review results

## 🤖 Agent Specializations

### Strategic Leadership
- **CTO (Chief Technology Officer)**: Architecture and technology strategy
- **CEO (Chief Executive Officer)**: Business alignment and stakeholder value

### Technical Experts
- **Senior Software Engineer**: Code quality and implementation practices
- **Python Expert**: Python-specific optimization and best practices
- **Database Administrator**: Schema design and query optimization
- **Algorithm Expert**: Data processing efficiency and complexity analysis

### Domain Specialists
- **AI Specialist**: Machine learning and NLP component analysis
- **Documentation Expert**: Technical writing and documentation standards
- **Business Analyst**: Requirements alignment and user experience
- **DevOps Engineer**: Infrastructure and deployment optimization
- **Security Specialist**: Security posture and vulnerability assessment

## 📋 Analysis Tasks

### 1. Architecture Review
- System design patterns and scalability
- Component integration and coupling
- Technology stack alignment
- Strategic recommendations for Project v2

### 2. Code Quality Assessment
- Python code standards and best practices
- Performance optimization opportunities
- Error handling and maintainability
- Implementation quality analysis

### 3. Database Analysis
- Schema design and normalization
- Query optimization and indexing
- Data integrity and consistency
- Migration and growth planning

### 4. AI/ML Components Review
- RAG implementation assessment
- Document processing pipeline
- Natural language processing efficiency
- Vector database integration

### 5. Documentation Review
- Documentation completeness and quality
- API documentation coverage
- User guide effectiveness
- Standards compliance assessment

### 6. Security & Infrastructure
- Security vulnerability assessment
- API key management practices
- Infrastructure configuration review
- Compliance and best practices

### 7. Business Alignment
- Requirements traceability
- User experience evaluation
- Stakeholder value assessment
- Strategic roadmap alignment

## 🛡️ CodeRabbit AI Features

### Automated Analysis
- **Code Quality**: Static analysis and best practice recommendations
- **Security**: Vulnerability detection and secure coding assessment
- **Performance**: Bottleneck identification and optimization suggestions
- **Architecture**: Design pattern evaluation and improvement recommendations

### Custom Configuration
- **Language Support**: Optimized for Python codebase
- **Analysis Depth**: Comprehensive 8000-token limit analysis
- **Custom Prompts**: Specialized analysis for security, performance, and architecture
- **Ignored Paths**: Automatic exclusion of test, documentation, and build files

### Reporting
- **High-level summaries** with strategic insights
- **Detailed recommendations** with implementation guidance
- **Sequence diagrams** for complex workflows
- **JSON summaries** for programmatic processing

## 🎨 Diagram Generation

### System Architecture
- Complete platform overview with all components
- Data flow through ingestion and processing layers
- Database relationships and storage architecture
- API and web layer interactions

### Data Flow Visualization
- Source APIs (Congress, OpenStates, GovInfo)
- Rate limiting and processing queues
- Validation and transformation pipelines
- Storage and retrieval systems

### Database Schema
- Entity-relationship diagrams
- Foreign key relationships
- Indexing strategies
- Constraint definitions

### Monitoring Architecture
- Metrics collection and aggregation
- Alerting and notification systems
- Dashboard and reporting infrastructure
- Performance monitoring workflows

## ⚙️ Configuration

### Environment Variables
```bash
# Required for CrewAI
OPENAI_API_KEY=your_openai_api_key

# Optional but recommended
ANTHROPIC_API_KEY=your_anthropic_key
GITHUB_TOKEN=your_github_token

# Project-specific
OPENSTATES_API_KEY=your_openstates_key
CONGRESS_API_KEY=your_congress_key
GOVINFO_API_KEY=your_govinfo_key
```

### CrewAI Configuration
- **Memory**: Long-term memory for context retention
- **Caching**: Simple cache for performance optimization
- **Timeouts**: Configurable execution time limits
- **Iteration Limits**: Maximum attempts per agent

### CodeRabbit Configuration
- **Analysis Limit**: 400 lines per file (Python optimized)
- **Token Limit**: 8000 tokens for comprehensive analysis
- **Query Threshold**: 7 for finding critical issues
- **Max Refinements**: 1 for focused recommendations

## 📈 Usage Examples

### Single Agent Analysis
```python
from crewai_crew.crew_config import OpenDiscourseCrewConfig

# Initialize configuration
config = OpenDiscreteCrewConfig()

# Create specific agents
agents = config.get_specialized_agents()
cto_agent = agents['cto']
python_expert = agents['python_expert']

# Run targeted analysis
from crewai import Task
task = Task(
    description="Review Python code quality in scripts/",
    agent=python_expert
)
```

### Custom Analysis Pipeline
```python
# Custom pipeline for specific components
from crewai_crew.main_execution import OpenDiscourseCrewOrchestrator

orchestrator = OpenDiscourseCrewOrchestrator()

# Run only specific analysis phases
coderabbit_result = orchestrator.run_coderabbit_analysis()
diagram_result = orchestrator.diagram_generator.generate_all_diagrams()
```

### Integration with CI/CD
```bash
#!/bin/bash
# GitHub Actions integration example

# Run CrewAI analysis
python3 crewai_crew/main_execution.py

# Archive results
tar -czf crewai_analysis_results.tar.gz crewai_reports/ crewai_diagrams/

# Upload to artifacts
# Use upload-artifact action to store results
```

## 🔧 Advanced Configuration

### Agent Customization
```python
# Custom agent with specific tools and memory
from crewai import Agent

custom_agent = Agent(
    role="Custom Specialist",
    goal="Specific analysis objectives",
    backstory="Domain expertise and background",
    tools=[custom_tool1, custom_tool2],
    memory=custom_memory_config,
    max_iter=5,
    max_execution_time=600
)
```

### Task Customization
```python
# Complex task with multiple outputs
from crewai import Task

complex_task = Task(
    description="Multi-phase analysis with documentation generation",
    agent=specialist_agent,
    expected_output="Structured analysis with diagrams and recommendations",
    context_files=["specific_files_to_analyze"],
    output_format="markdown_with_diagrams"
)
```

### Memory Configuration
```python
from crewai.memory import LongTermMemory

# Configure persistent memory
memory = LongTermMemory(
    storage_path="./crewai_memory",
    embeddings_config={
        "provider": "openai",
        "config": {"model": "text-embedding-ada-002"}
    }
)
```

## 📊 Monitoring and Logging

### Execution Monitoring
- **Real-time progress tracking** during analysis
- **Agent performance metrics** and timing
- **Error handling and recovery** mechanisms
- **Resource usage monitoring** and optimization

### Logging Configuration
- **File logging** with rotation and retention
- **Console output** with colored formatting
- **Structured logs** in JSON format for analysis
- **Performance metrics** collection and reporting

### Results Tracking
- **Analysis history** with timestamp and version tracking
- **Comparison capabilities** between different analysis runs
- **Trend analysis** for improvement tracking
- **Executive dashboard** with key metrics visualization

## 🚨 Troubleshooting

### Common Issues

#### 1. CrewAI Installation Problems
```bash
# Update pip and install
pip install --upgrade pip
pip install crewai crewai-tools

# If issues persist, try
pip install --no-cache-dir crewai
```

#### 2. API Key Configuration
```bash
# Verify environment variables
echo $OPENAI_API_KEY
echo $GITHUB_TOKEN

# Check if keys are valid
python3 -c "
import os
print('OpenAI Key:', 'Set' if os.getenv('OPENAI_API_KEY') else 'Missing')
print('GitHub Token:', 'Set' if os.getenv('GITHUB_TOKEN') else 'Missing')
"
```

#### 3. Memory Issues
```python
# Reduce agent memory usage
agents = config.get_specialized_agents()
for agent in agents.values():
    agent.memory = None  # Disable memory for large analyses
```

#### 4. Timeout Issues
```python
# Increase timeouts for complex analyses
for agent in agents.values():
    agent.max_execution_time = 1800  # 30 minutes
```

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
orchestrator = OpenDiscourseCrewOrchestrator()
result = orchestrator.run_complete_analysis()
```

## 📚 Additional Resources

### Documentation
- [CrewAI Official Documentation](https://docs.crewai.com/)
- [CodeRabbit AI Documentation](https://docs.coderabbit.ai/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

### Examples and Tutorials
- [CrewAI Examples Repository](https://github.com/joaomdmoura/crewai-examples)
- [CodeRabbit AI Tutorials](https://docs.coderabbit.ai/tutorials)

### Community Support
- [CrewAI Discord](https://discord.gg/crewai)
- [GitHub Issues](https://github.com/cbwinslow/opendiscourse/issues)

## 🤝 Contributing

To contribute to the CrewAI system:

1. **Fork the repository**
2. **Create a feature branch**
3. **Implement improvements** with tests
4. **Document changes** in README updates
5. **Submit pull request** with detailed description

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/cbwinslow/opendiscourse.git
cd opendiscourse/crewai_crew

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/
```

## 📄 License

This CrewAI system is part of the OpenDiscourse project and follows the same MIT License terms.

## 🆘 Support

For support and questions:

1. **Check the troubleshooting section** above
2. **Review the logs** in `crewai_execution.log`
3. **Search existing GitHub issues** in the OpenDiscourse repository
4. **Create a new issue** with detailed description and logs

---

**Last Updated**: December 3, 2025
**Version**: 1.0.0
**Compatibility**: Python 3.8+, CrewAI 0.28.0+
