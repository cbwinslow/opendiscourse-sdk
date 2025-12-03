#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path

# Define base directory for generated GitHub project files
base_dir = Path("github_sync_package")
labels_file = base_dir / "labels.yaml"
milestones_file = base_dir / "milestones.yaml"
issues_dir = base_dir / "issues"
scripts_dir = base_dir / "scripts"

# Ensure directories exist
issues_dir.mkdir(parents=True, exist_ok=True)
scripts_dir.mkdir(parents=True, exist_ok=True)

# 1. Define labels.yaml
labels_content = """\n- name: enhancement
  color: "84b6eb"
  description: "Improvement to existing features"

- name: feature
  color: "0e8a16"
  description: "New functionality"

- name: bug
  color: "d73a4a"
  description: "Something isn't working"

- name: documentation
  color: "0075ca"
  description: "Improvements or additions to docs"

- name: ci/cd
  color: "5319e7"
  description: "Build or deployment tasks"

- name: agent-logs
  color: "f9d0c4"
  description: "Automatically generated from agent logs"
"""

# 2. Define milestones.yaml
milestones_content = f"""\n- title: Data Ingestion & Automation
  description: "Bias detection, agent logging, and real-time media ingestion"
  due_on: {datetime(2025, 7, 1).isoformat()}

- title: Entity Tracking & Fact‑Check
  description: "Entity DB and fact-check pipeline"
  due_on: {datetime(2025, 7, 15).isoformat()}

- title: Dashboard & Deployment
  description: "Frontend, CI/CD, and final polish"
  due_on: {datetime(2025, 7, 31).isoformat()}
"""

# 3. Define sample issues
issue_templates = {
    "bias_detection.md": """\n---
title: Implement Ensemble Bias Detection Module
labels: [enhancement, feature]
milestone: Data Ingestion & Automation
---

Build an LLM-based ensemble model that ingests news content and assigns a bias
rating based on:
- Language polarity
- Sentiment toward political entities
- Alignment with partisan narratives
- Fact-based scoring

**Requirements**:
- Use open-source LLMs (e.g. Mistral, Phi-3)
- Output scores stored in the database
- Unit testable and modular pipeline
""",
    "agent_log_sync.md": """\n---
title: Implement Agent Log → GitHub Issue Sync System
labels: [enhancement, agent-logs, ci/cd]
milestone: Data Ingestion & Automation
---

Create a Python script or GitHub Action that:
- Parses logs or JSON output from AI agents
- Detects failures, exceptions, or TODOs
- Automatically creates GitHub Issues with relevant tags and tracebacks

Example input:
```json
{
  "agent": "RAGPipelineChecker",
  "error": "MissingEmbeddingVector",
  "timestamp": "2025-06-15T14:02Z"
}
```
""",
}

# 4. Define agent-log parser script
agent_log_parser = """#!/usr/bin/env python3
import json, os
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "cbwinslow/opendiscourse"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO)

def parse_log_and_create_issue(log_path):
    with open(log_path) as f:
        entries = json.load(f)
    for entry in entries:
        title = f"[Agent Error] {entry['agent']} - {entry['error']}"
        body = (
            f"**Agent**: {entry['agent']}\n"
            f"**Error**: {entry['error']}\n"
            f"**Time**: {entry['timestamp']}"
        )
        repo.create_issue(title=title, body=body, labels=["agent-logs"])

# Example usage
# parse_log_and_create_issue("logs/agent-failures.json")
"""

# Write everything to disk
labels_file.write_text(labels_content)
milestones_file.write_text(milestones_content)
for name, content in issue_templates.items():
    (issues_dir / name).write_text(content)
(scripts_dir / "agent_log_issue_sync.py").write_text(agent_log_parser)

print(f"GitHub sync package created at: {base_dir.resolve()}")
