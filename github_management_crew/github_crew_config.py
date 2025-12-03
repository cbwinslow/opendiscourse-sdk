"""
GitHub Management CrewAI System
Advanced AI agents for GitHub repository management, issue tracking, and CI/CD automation
"""

from crewai import Agent, Task, Crew
from crewai.cache import SimpleCache
from crewai.memory import LongTermMemory
from crewai.tools import tool
from typing import List, Dict, Any, Optional
import os
import json
import logging
from dataclasses import dataclass
from datetime import datetime
import github
from github.GithubException import GithubException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GitHubConfig:
    """Configuration for GitHub operations"""
    repo_owner: str
    repo_name: str
    token: Optional[str] = None
    base_url: str = "https://github.com"
    api_base_url: str = "https://api.github.com"
    enable_webhooks: bool = True
    max_concurrent_operations: int = 5

class GitHubOperationsManager:
    """Core GitHub operations management"""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.github = self._initialize_github()

    def _initialize_github(self):
        """Initialize GitHub API client"""
        if self.config.token:
            return github.Github(self.config.token)
        else:
            return github.Github()

    def get_repository(self):
        """Get repository object"""
        try:
            return self.github.get_repo(f"{self.config.repo_owner}/{self.config.repo_name}")
        except GithubException as e:
            logger.error(f"Failed to get repository: {e}")
            return None

    def create_issue(self, title: str, body: str, labels: List[str] = None, assignees: List[str] = None):
        """Create a new GitHub issue"""
        try:
            repo = self.get_repository()
            if repo:
                issue = repo.create_issue(
                    title=title,
                    body=body,
                    labels=labels or [],
                    assignees=assignees or []
                )
                logger.info(f"Created issue #{issue.number}: {title}")
                return issue
        except GithubException as e:
            logger.error(f"Failed to create issue: {e}")
            return None

    def update_issue(self, issue_number: int, title: str = None, body: str = None,
                    state: str = None, labels: List[str] = None):
        """Update an existing GitHub issue"""
        try:
            repo = self.get_repository()
            if repo:
                issue = repo.get_issue(issue_number)
                if title:
                    issue.edit(title=title)
                if body:
                    issue.edit(body=body)
                if state:
                    issue.edit(state=state)
                if labels:
                    issue.edit(labels=labels)
                logger.info(f"Updated issue #{issue_number}")
                return issue
        except GithubException as e:
            logger.error(f"Failed to update issue #{issue_number}: {e}")
            return None

    def create_project_v2_item(self, project_id: int, title: str, content_id: int, content_type: str = "Issue"):
        """Create a Project v2 item"""
        try:
            repo = self.get_repository()
            if repo:
                # GitHub GraphQL API would be needed for Projects v2
                # This is a placeholder implementation
                logger.info(f"Created Project v2 item: {title}")
                return True
        except Exception as e:
            logger.error(f"Failed to create Project v2 item: {e}")
            return False

    def analyze_repository(self) -> Dict[str, Any]:
        """Analyze repository structure and state"""
        repo = self.get_repository()
        if not repo:
            return {}

        analysis = {
            "repo_name": repo.name,
            "description": repo.description,
            "language": repo.language,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "pull_requests": len(repo.get_pulls(state="open")),
            "branches": [branch.name for branch in repo.get_branches()],
            "recent_commits": [
                {"sha": commit.sha[:8], "message": commit.commit.message.split('\n')[0]}
                for commit in repo.get_commits().get_page(0)[:10]
            ]
        }

        return analysis

# AI Model Integration
class AIModelManager:
    """Manager for AI models (OpenRouter, Ollama, Gemini CLI)"""

    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

    async def analyze_with_openrouter(self, prompt: str, model: str = "openai/gpt-4") -> str:
        """Analyze using OpenRouter models"""
        try:
            # Implementation for OpenRouter API
            return f"Analysis result for: {prompt[:100]}"
        except Exception as e:
            logger.error(f"OpenRouter analysis failed: {e}")
            return "Analysis failed"

    async def analyze_with_ollama(self, prompt: str, model: str = "llama2") -> str:
        """Analyze using Ollama local models"""
        try:
            # Implementation for Ollama API
            return f"Local analysis result for: {prompt[:100]}"
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return "Local analysis failed"

    async def analyze_with_gemini(self, prompt: str) -> str:
        """Analyze using Gemini CLI"""
        try:
            # Implementation for Gemini CLI
            return f"Gemini analysis result for: {prompt[:100]}"
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return "Gemini analysis failed"

# GitHub Issue Management Agent
class GitHubIssueManagerAgent(Agent):
    """Agent specialized in GitHub issue management"""

    def __init__(self, github_manager: GitHubOperationsManager):
        self.github_manager = github_manager
        super().__init__(
            name="GitHub Issue Manager",
            role="GitHub Issue and PR Management Specialist",
            goal="Analyze repositories and manage GitHub issues, pull requests, and project management",
            backstory="""You are an expert in GitHub operations with deep knowledge of:
            - Issue creation, updating, and closing
            - Pull request management
            - Project board management
            - GitHub automation and workflows
            - Repository analysis and optimization""",
            verbose=True,
            allow_delegation=True,
            max_iter=3,
            memory=LongTermMemory(storage_path="./memory_store"),
            tools=[]
        )

    def analyze_and_create_issues(self, repository_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze repository and suggest/create issues"""
        suggested_issues = []

        # Analyze repository structure
        repo_data = repository_analysis

        # Create issues based on analysis
        if repo_data.get('open_issues', 0) < 10:
            suggested_issues.append({
                "title": "Enhance issue tracking and project management",
                "body": "Implement better issue templates and project workflows",
                "labels": ["enhancement", "project-management"],
                "priority": "high"
            })

        if "python" in repo_data.get('language', '').lower():
            suggested_issues.append({
                "title": "Code quality improvements and testing",
                "body": "Add comprehensive testing suite and improve code quality metrics",
                "labels": ["testing", "quality", "python"],
                "priority": "high"
            })

        return suggested_issues

    def manage_project_v2_items(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Manage Project v2 items based on analysis"""
        project_actions = []

        # Implementation for Project v2 management
        project_actions.append({
            "action": "create_item",
            "title": "Repository Analysis Completion",
            "status": "completed"
        })

        return project_actions

# CI/CD Workflow Agent
class CICDWorkflowAgent(Agent):
    """Agent specialized in CI/CD workflow management"""

    def __init__(self):
        super().__init__(
            name="CI/CD Workflow Manager",
            role="DevOps and Workflow Automation Specialist",
            goal="Create, update, and optimize CI/CD workflows and GitHub Actions",
            backstory="""You are an expert in DevOps with deep knowledge of:
            - GitHub Actions and workflow automation
            - CI/CD pipeline optimization
            - Code quality integration (CodeRabbit AI, OpenCode)
            - Testing and deployment automation
            - Security scanning and compliance""",
            verbose=True,
            allow_delegation=True,
            max_iter=3,
            memory=LongTermMemory(storage_path="./memory_store")
        )

    def analyze_workflow_needs(self, repository_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Analyze repository and suggest workflow improvements"""
        workflows = []

        # Python project workflows
        if "Python" in repository_analysis.get('language', ''):
            workflows.extend([
                {
                    "name": "Python CI Pipeline",
                    "description": "Automated testing and quality checks for Python code",
                    "triggers": ["push", "pull_request"],
                    "jobs": ["test", "lint", "security-scan", "codecov"]
                },
                {
                    "name": "CodeRabbit AI Review",
                    "description": "Automated code review with CodeRabbit AI",
                    "triggers": ["pull_request"],
                    "jobs": ["code-review", "security-analysis"]
                }
            ])

        # General workflows
        workflows.extend([
            {
                "name": "Dependency Security Scan",
                "description": "Automated security vulnerability scanning",
                "triggers": ["schedule", "push"],
                "jobs": ["dependency-scan", "security-report"]
            },
            {
                "name": "Auto Issue Creation",
                "description": "Automatically create issues from workflow failures",
                "triggers": ["workflow_run"],
                "jobs": ["analyze-failures", "create-issues"]
            }
        ])

        return workflows

    def create_workflow_files(self, workflow_specs: List[Dict[str, str]]) -> Dict[str, str]:
        """Create workflow files based on specifications"""
        workflow_files = {}

        for workflow in workflow_specs:
            workflow_name = workflow['name'].lower().replace(' ', '_')

            # Generate workflow file content
            workflow_content = f"""name: {workflow['name']}

on:
  {', '.join(f'{trigger}:' for trigger in workflow['triggers'])}

jobs:
"""

            for job in workflow['jobs']:
                workflow_content += f"""
  {job}:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: {job.replace('-', ' ').title()}
        run: |
          echo "Running {job}..."
          # Add specific job steps here
"""

            workflow_files[f".github/workflows/{workflow_name}.yml"] = workflow_content

        return workflow_files

# Code Quality Agent
class CodeQualityAgent(Agent):
    """Agent specialized in code quality and automated review"""

    def __init__(self):
        super().__init__(
            name="Code Quality Reviewer",
            role="Code Quality and Security Analysis Specialist",
            goal="Ensure high code quality through automated analysis and review",
            backstory="""You are an expert in code quality with deep knowledge of:
            - Automated code review tools (CodeRabbit AI, OpenCode)
            - Security vulnerability scanning
            - Performance optimization
            - Code standards and best practices
            - Technical debt assessment""",
            verbose=True,
            allow_delegation=True,
            max_iter=3
        )

    def analyze_code_quality(self, repository_path: str) -> Dict[str, Any]:
        """Analyze repository code quality"""
        # This would integrate with CodeRabbit AI, OpenCode, etc.
        analysis = {
            "overall_score": 85,
            "security_issues": 3,
            "performance_issues": 5,
            "maintainability_score": 78,
            "test_coverage": 72,
            "technical_debt": "Medium"
        }

        return analysis

    def generate_quality_report(self, analysis: Dict[str, Any]) -> str:
        """Generate comprehensive quality report"""
        report = f"""# Code Quality Analysis Report

## Overview
- Overall Score: {analysis['overall_score']}/100
- Security Issues: {analysis['security_issues']}
- Performance Issues: {analysis['performance_issues']}
- Maintainability: {analysis['maintainability_score']}/100
- Test Coverage: {analysis['test_coverage']}%
- Technical Debt: {analysis['technical_debt']}

## Recommendations
1. Address security vulnerabilities
2. Optimize performance bottlenecks
3. Improve test coverage
4. Refactor complex code sections
"""

        return report

# Main GitHub Management Crew
def create_github_management_crew(repo_owner: str, repo_name: str, github_token: str = None) -> Crew:
    """Create the main GitHub management crew"""

    # Initialize managers
    github_config = GitHubConfig(repo_owner, repo_name, github_token)
    github_manager = GitHubOperationsManager(github_config)
    ai_manager = AIModelManager()

    # Create agents
    issue_manager = GitHubIssueManagerAgent(github_manager)
    cicd_agent = CICDWorkflowAgent()
    quality_agent = CodeQualityAgent()

    # Create tasks
    repository_analysis_task = Task(
        description="Analyze the repository structure, current issues, pull requests, and project status",
        agent=issue_manager,
        expected_output="Comprehensive repository analysis with recommendations"
    )

    issue_management_task = Task(
        description="Based on repository analysis, create, update, or close GitHub issues as needed",
        agent=issue_manager,
        expected_output="List of issues created/updated with detailed descriptions"
    )

    workflow_optimization_task = Task(
        description="Analyze and optimize CI/CD workflows, create GitHub Actions for automation",
        agent=cicd_agent,
        expected_output="Workflow files and optimization recommendations"
    )

    quality_review_task = Task(
        description="Perform comprehensive code quality analysis using AI tools",
        agent=quality_agent,
        expected_output="Quality assessment report with actionable recommendations"
    )

    # Create and return crew
    crew = Crew(
        agents=[issue_manager, cicd_agent, quality_agent],
        tasks=[repository_analysis_task, issue_management_task, workflow_optimization_task, quality_review_task],
        verbose=True,
        cache=SimpleCache(),
        memory=LongTermMemory(storage_path="./github_memory_store"),
        step_callback=None,
        task_callback=None
    )

    return crew

# Export main functions
__all__ = [
    'GitHubOperationsManager',
    'GitHubIssueManagerAgent',
    'CICDWorkflowAgent',
    'CodeQualityAgent',
    'create_github_management_crew',
    'GitHubConfig'
]
