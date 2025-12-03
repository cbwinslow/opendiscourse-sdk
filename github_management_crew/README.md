# GitHub Management CrewAI System

## 🤖 **Advanced AI-Powered GitHub Repository Management**

Comprehensive CrewAI system for automated GitHub repository analysis, issue management, project tracking, and CI/CD optimization using multiple AI services.

---

## 🎯 **System Overview**

The GitHub Management CrewAI system is an advanced multi-agent platform that automatically:

- **Analyzes repository structure and code quality** using AI models
- **Creates and manages GitHub issues** based on analysis findings
- **Sets up Project v2 tracking** for improved project management
- **Generates CI/CD workflow recommendations** and automation
- **Performs security and performance analysis** with AI-powered insights
- **Integrates with multiple AI services** (OpenRouter, Ollama, Gemini CLI)
- **Provides comprehensive reporting** and actionable recommendations

---

## 🏗️ **Architecture**

### **Core Components**

```
github_management_crew/
├── github_crew_config.py          # Core CrewAI configuration and agents
├── ai_services_integration.py     # AI service integrations (OpenRouter, Ollama, Gemini)
├── project_v2_management.py       # GitHub Projects v2 management
├── main_orchestrator.py           # Main execution pipeline
├── run_github_analysis.sh         # Startup script
├── requirements.txt               # Python dependencies
└── README.md                      # This documentation
```

### **AI Agents**

1. **GitHub Issue Manager** - Automated issue creation, updating, and management
2. **CI/CD Workflow Agent** - GitHub Actions and workflow automation
3. **Code Quality Agent** - CodeRabbit AI integration and quality assessment
4. **Project v2 Manager** - GitHub Projects v2 setup and tracking
5. **AI Analysis Manager** - Multi-service AI analysis coordination

### **AI Service Integrations**

- **OpenRouter** - Free access to GPT-4 and other models
- **Ollama** - Local AI model execution
- **Gemini CLI** - Google Gemini integration
- **CodeRabbit AI** - Automated code review and analysis

---

## 🚀 **Quick Start**

### **1. Environment Setup**

```bash
# Clone or download the github_management_crew directory
cd github_management_crew

# Run setup
./run_github_analysis.sh --setup
```

### **2. Configure Environment**

Edit the `.env` file created during setup:

```env
# GitHub Token (required)
GITHUB_TOKEN=your_github_token_here

# AI Service API Keys (optional, for enhanced analysis)
OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Local AI Models (if using Ollama)
OLLAMA_HOST=localhost:11434

# Output Configuration
ANALYSIS_OUTPUT_DIR=github_analysis_results
LOG_LEVEL=INFO
```

### **3. Run Analysis**

```bash
# Basic usage
./run_github_analysis.sh <repo_owner> <repo_name>

# Examples
./run_github_analysis.sh openai gpt-3
./run_github_analysis.sh microsoft vscode
./run_github_analysis.sh facebook react my_results
```

### **4. Test System**

```bash
# Test all components
./run_github_analysis.sh --test
```

---

## 📋 **Features**

### **🔍 Repository Analysis**
- **Structure Analysis** - Repository layout, languages, dependencies
- **Code Quality Assessment** - Python/JavaScript/TypeScript analysis
- **Security Scanning** - Vulnerability detection and recommendations
- **Performance Evaluation** - Bottleneck identification and optimization
- **Documentation Review** - Completeness and quality assessment

### **🎯 Issue Management**
- **Automatic Issue Creation** - Based on analysis findings
- **Smart Labeling** - AI-powered issue categorization
- **Priority Assessment** - Impact-based prioritization
- **Template Generation** - Comprehensive issue templates
- **Security Issue Tracking** - Dedicated security vulnerability tracking

### **📊 Project v2 Management**
- **Automated Project Creation** - Analysis results tracking
- **Smart Item Assignment** - AI-powered item categorization
- **Progress Monitoring** - Automated status updates
- **Workflow Integration** - GitHub Actions for project automation
- **Executive Reporting** - High-level project summaries

### **⚙️ CI/CD Automation**
- **Workflow Generation** - Python CI, security scanning, testing
- **CodeRabbit AI Integration** - Automated code review workflows
- **Security Pipeline** - Dependency scanning and vulnerability assessment
- **Performance Monitoring** - Automated performance testing
- **Documentation Generation** - Auto-generated workflow documentation

### **🤖 AI-Powered Analysis**
- **Multi-Service Analysis** - OpenRouter, Ollama, Gemini coordination
- **Code Quality Assessment** - Comprehensive quality scoring
- **Security Vulnerability Detection** - AI-powered security analysis
- **Performance Optimization** - Automated performance recommendations
- **Architecture Review** - System design and scalability assessment

---

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `OPENROUTER_API_KEY` | No | OpenRouter API key for AI models |
| `GEMINI_API_KEY` | No | Google Gemini API key |
| `OLLAMA_HOST` | No | Ollama service host (default: localhost:11434) |
| `ANALYSIS_OUTPUT_DIR` | No | Output directory (default: github_analysis_results) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

### **GitHub Token Setup**

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate new token with these scopes:
   - `repo` (Full control of private repositories)
   - `project` (Manage projects)
   - `workflow` (Update GitHub Action workflows)
3. Copy token to `.env` file

### **API Keys Setup**

**OpenRouter (Optional):**
- Visit [OpenRouter.ai](https://openrouter.ai)
- Create account and generate API key
- Add to `.env` file

**Gemini CLI (Optional):**
- Install Gemini CLI: `npm install -g @google/generative-ai`
- Set `GEMINI_API_KEY` environment variable

**Ollama (Optional):**
- Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
- Start service: `ollama serve`
- Models will be auto-downloaded on first use

---

## 📊 **Output**

### **Generated Reports**

After analysis, you'll find:

```
github_analysis_results/
├── analysis_results_YYYYMMDD_HHMMSS.json    # Complete analysis data
├── analysis_summary_YYYYMMDD_HHMMSS.md      # Executive summary
├── project_v2_items.json                    # Project tracking data
├── workflow_specifications.json            # CI/CD workflow details
└── ai_analysis_reports/                     # Detailed AI analysis
```

### **GitHub Actions**

The system creates:
- **Issue automation** - Auto-labeling and assignment
- **Security scanning** - Automated vulnerability detection
- **Quality gates** - Code quality enforcement
- **Project tracking** - Automated progress monitoring

### **Executive Dashboard**

Real-time insights including:
- Repository health score
- Security risk assessment
- Performance metrics
- Development velocity
- Technical debt analysis

---

## 🎛️ **Usage Examples**

### **Basic Repository Analysis**

```bash
# Analyze a public repository
./run_github_analysis.sh openai gpt-3

# Analyze with custom output directory
./run_github_analysis.sh facebook react ./results
```

### **Development Team Integration**

```bash
# For team repositories
./run_github_analysis.sh your-org your-repo

# The system will:
# 1. Analyze repository structure
# 2. Create improvement issues
# 3. Set up Project v2 tracking
# 4. Generate CI/CD workflows
# 5. Provide security recommendations
```

### **CI/CD Integration**

The system automatically creates:

**Python CI Pipeline:**
```yaml
name: Python CI Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: python -m pytest
```

**Security Scanning:**
```yaml
name: Security Analysis
on: [schedule, push]
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security Analysis
        run: # AI-powered security scanning
```

---

## 🔍 **Advanced Features**

### **Custom Analysis Types**

```python
# Run specific analysis types
ai_manager = AIServicesManager()
results = await ai_manager.comprehensive_code_analysis(
    code_content,
    analysis_types=["security", "performance", "architecture"]
)
```

### **Project v2 Automation**

```python
# Set up automated project tracking
project_id = await project_manager.create_project_for_analysis(
    repo_owner, repo_name, analysis_results
)

# Add tracking items automatically
tracking_items = await project_manager.create_tracking_items(
    project_id, analysis_results
)
```

### **Multi-Service AI Analysis**

```python
# Combine multiple AI services
analysis_results = await ai_manager.comprehensive_code_analysis(
    code_content,
    repository_context=repo_analysis
)

# Generate consolidated report
report = ai_manager.generate_consolidated_report(
    analysis_results, repository_analysis
)
```

---

## 🛠️ **Development**

### **Adding New AI Services**

```python
class CustomAIIntegration:
    async def analyze_code(self, content: str) -> AIAnalysisResult:
        # Implement your AI service integration
        pass
```

### **Extending Agents**

```python
class CustomAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Custom Analysis Agent",
            role="Custom Domain Expert",
            goal="Analyze specific repository aspects"
        )
```

### **Custom Workflows**

```python
# Add custom CI/CD workflows
workflow_spec = {
    "name": "Custom Analysis",
    "description": "Custom workflow for specific needs",
    "triggers": ["push"],
    "jobs": ["custom-analysis"]
}
```

---

## 📈 **Metrics & Analytics**

### **Repository Health Scoring**

- **Code Quality** (0-100) - Based on AI analysis
- **Security Score** (0-100) - Vulnerability assessment
- **Performance Score** (0-100) - Optimization opportunities
- **Documentation Score** (0-100) - Completeness and quality
- **Test Coverage** (0-100) - Automated testing coverage

### **Development Velocity**

- **Issue Resolution Rate** - Average time to close issues
- **PR Merge Time** - Time from PR creation to merge
- **Code Review Efficiency** - Review completion time
- **Deployment Frequency** - Release cadence analysis

### **AI Analysis Accuracy**

- **Confidence Scores** - AI model reliability metrics
- **False Positive Rate** - Accuracy of security findings
- **Recommendation Adoption** - Implementation success rate

---

## 🚨 **Troubleshooting**

### **Common Issues**

**GitHub Token Issues:**
```bash
# Verify token permissions
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
```

**AI Service Connection:**
```bash
# Test OpenRouter
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Test Ollama
curl http://localhost:11434/api/tags
```

**Python Environment:**
```bash
# Recreate virtual environment
rm -rf github_crew_env
./run_github_analysis.sh --setup
```

### **Debug Mode**

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./run_github_analysis.sh owner repo
```

### **System Test**

```bash
# Run comprehensive system test
./run_github_analysis.sh --test
```

---

## 📚 **API Reference**

### **Main Classes**

**GitHubManagementOrchestrator:**
```python
orchestrator = GitHubManagementOrchestrator(
    repo_owner="owner",
    repo_name="repo",
    github_token="token"
)

results = await orchestrator.run_complete_analysis()
```

**AIServicesManager:**
```python
ai_manager = AIServicesManager()
analysis = await ai_manager.comprehensive_code_analysis(
    code_content, repository_context
)
```

**ProjectV2ManagementAgent:**
```python
project_manager = ProjectV2ManagementAgent(github_manager)
project_id = await project_manager.create_project_for_analysis(
    owner, repo, analysis_results
)
```

---

## 🤝 **Contributing**

### **Development Setup**

```bash
# Clone repository
git clone <repository-url>
cd github_management_crew

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/

# Code formatting
black .
flake8 .
```

### **Adding Features**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### **Code Standards**

- **PEP 8** compliance for Python code
- **Type hints** for all function parameters
- **Docstrings** for all public methods
- **Unit tests** for new features
- **Error handling** for all API calls

---

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 **Acknowledgments**

- **CrewAI** - Multi-agent framework
- **GitHub API** - Repository management capabilities
- **OpenRouter** - AI model access
- **Ollama** - Local AI model execution
- **Gemini** - Google's AI services
- **CodeRabbit AI** - Automated code review

---

## 📞 **Support**

For support and questions:
- **Documentation**: Check this README and inline code documentation
- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

---

**🎯 Ready to revolutionize your GitHub repository management with AI-powered automation!**
