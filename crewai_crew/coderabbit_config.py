"""
CodeRabbit AI Integration for OpenDiscourse Project
Automated code review and analysis integration
"""

import os
import json
import subprocess
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CodeRabbitAIIntegration:
    """Integration class for CodeRabbit AI automated code review"""

    def __init__(self, base_path: str = "/home/cbwinslow/Videos/opendiscourse"):
        self.base_path = base_path
        self.coderabbit_config = {
            "language": "python",
            "query_threshold": 7,
            "max_refinement": 1,
            "max_tokens": 8000,
            "review_status": True,
            "high_level_summary": True,
            "auto_title_placeholders": True,
            "sequence_diagrams": True,
            "sequence_diagrams_threshold": 100
        }

    def setup_coderabbit_config(self) -> Dict[str, Any]:
        """Create CodeRabbit configuration file"""

        config_path = os.path.join(self.base_path, ".coderrc.yaml")

        coderabbit_yaml = """# CodeRabbit AI Configuration for OpenDiscourse Project
# https://docs.coderabbit.ai/quickstart/

review:
  high_level_summary: true
  auto_title_placeholders: true
  sequence_diagrams: true

chat:
  auto_reply: true

tools:
  mdx: true

# Language-specific configurations
languages:
  python:
    analysis_limit: 400
    index_ignores: ["*", "!*.py", "!!**/*.py"]

# Max tokens for analysis
max_tokens: 8000

# Query threshold for finding bugs
query_threshold: 7

# Max refinements allowed
max_refinement: 1

# Paths to ignore
paths_ignore:
  - "**/venv/**"
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/.github/**"
  - "**/docs/**"
  - "**/migrations/**"
  - "**/docker/**"
  - "**/__pycache__/**"
  - "**/*.pyc"
  - "**/backup**"
  - "**/test**"
  - "**/.env**"
  - "**/.venv/**"

# Custom prompts for specific areas
custom_prompts:
  security:
    - "Analyze this Python code for security vulnerabilities including SQL injection, XSS, and secure coding practices"
    - "Review database connection patterns and API key management"
    - "Check for hardcoded credentials and sensitive information exposure"

  performance:
    - "Identify performance bottlenecks and optimization opportunities"
    - "Analyze database queries and indexing strategies"
    - "Review parallel processing and rate limiting implementations"

  architecture:
    - "Evaluate system architecture and design patterns"
    - "Assess scalability and maintainability concerns"
    - "Review integration patterns and component coupling"

  ai_ml:
    - "Review AI/ML pipeline implementations"
    - "Analyze natural language processing components"
    - "Evaluate data processing and embedding strategies"
"""

        with open(config_path, 'w') as f:
            f.write(coderabbit_yaml)

        return {
            "config_file": config_path,
            "status": "created",
            "features_enabled": [
                "high_level_summary",
                "auto_title_placeholders",
                "sequence_diagrams",
                "security_analysis",
                "performance_review",
                "architecture_assessment",
                "ai_ml_review"
            ]
        }

    def create_review_script(self) -> str:
        """Create script to run CodeRabbit AI review"""

        script_path = os.path.join(self.base_path, "scripts", "run_coderabbit_review.py")

        script_content = """#!/usr/bin/env python3
\"\"\"
CodeRabbit AI Review Script for OpenDiscourse Project
Automated code review and analysis using CodeRabbit AI
\"\"\"

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_coderabbit_review():
    \"\"\"Execute CodeRabbit AI code review\"\"\"

    base_path = "/home/cbwinslow/Videos/opendiscourse"
    results_dir = os.path.join(base_path, "crewai_reports")

    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)

    try:
        # Run CodeRabbit AI review
        print("🚀 Starting CodeRabbit AI code review...")

        # Change to project directory
        os.chdir(base_path)

        # Execute CodeRabbit CLI (if available)
        result = subprocess.run([
            "coderabbit", "review",
            "--config", ".coderrc.yaml",
            "--output", results_dir
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ CodeRabbit review completed successfully")

            # Generate summary report
            summary = {
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "reviewer": "CodeRabbit AI",
                "coverage": "full_codebase",
                "files_analyzed": count_python_files(base_path),
                "recommendations": "check_crewai_reports/"
            }

            # Save summary
            summary_path = os.path.join(results_dir, "coderabbit_summary.json")
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)

            return summary

        else:
            print(f"❌ CodeRabbit review failed: {result.stderr}")
            return {"status": "failed", "error": result.stderr}

    except FileNotFoundError:
        print("⚠️  CodeRabbit CLI not found. Using fallback review...")
        return perform_fallback_review()

    except Exception as e:
        print(f"❌ Error during CodeRabbit review: {e}")
        return {"status": "error", "error": str(e)}

def count_python_files(base_path: str) -> int:
    \"\"\"Count Python files in the project\"\"\"
    python_files = []
    for root, dirs, files in os.walk(base_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return len(python_files)

def perform_fallback_review():
    \"\"\"Perform basic code analysis when CodeRabbit is not available\"\"\"

    base_path = "/home/cbwinslow/Videos/opendiscourse"
    results_dir = os.path.join(base_path, "crewai_reports")

    # Basic analysis
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "status": "fallback_completed",
        "reviewer": "Basic Analysis (CodeRabbit CLI not available)",
        "python_files_found": count_python_files(base_path),
        "recommendations": [
            "Install CodeRabbit CLI for comprehensive analysis",
            "Review GitHub issues for known problems",
            "Run crewai_analysis.py for multi-agent review"
        ],
        "next_steps": [
            "Install CodeRabbit: npm install -g @coderabbitai/coderabbit",
            "Set up CodeRabbit in the repository",
            "Run comprehensive analysis with CrewAI crew"
        ]
    }

    # Save fallback analysis
    fallback_path = os.path.join(results_dir, "basic_analysis_fallback.json")
    with open(fallback_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"✅ Basic analysis completed and saved to {fallback_path}")
    return analysis

if __name__ == "__main__":
    result = run_coderabbit_review()
    print(f"\\n📊 Review Result: {result['status']}")
    if 'files_analyzed' in result:
        print(f"📁 Files Analyzed: {result['files_analyzed']}")
"""

        # Write the script
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make executable
        os.chmod(script_path, 0o755)

        return script_path

    def get_integration_config(self) -> Dict[str, Any]:
        """Get CodeRabbit integration configuration"""

        return {
            "setup_status": "ready",
            "features": {
                "automated_review": True,
                "security_analysis": True,
                "performance_review": True,
                "architecture_assessment": True,
                "sequence_diagrams": True,
                "custom_prompts": True
            },
            "review_areas": [
                "code_quality",
                "security_vulnerabilities",
                "performance_optimization",
                "architecture_review",
                "ai_ml_components",
                "database_design",
                "api_design",
                "documentation_quality"
            ],
            "output_formats": [
                "markdown_reports",
                "json_summaries",
                "sequence_diagrams",
                "recommendations"
            ],
            "customization": {
                "ignored_paths": [
                    "venv", "node_modules", ".git", "docs",
                    "migrations", "docker", "__pycache__"
                ],
                "analysis_depth": "comprehensive",
                "token_limit": 8000,
                "max_refinements": 1
            }
        }
