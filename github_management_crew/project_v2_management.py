"""
Project v2 Management for GitHub CrewAI System
Advanced GitHub Projects v2 integration for automated project management
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import github
from github.GithubException import GithubException

logger = logging.getLogger(__name__)

@dataclass
class ProjectV2Item:
    """Represents a GitHub Projects v2 item"""
    id: str
    title: str
    content_type: str
    content_id: int
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    labels: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProjectV2Column:
    """Represents a GitHub Projects v2 column/field"""
    id: str
    name: str
    field_type: str
    options: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.options is None:
            self.options = []

class GitHubProjectsV2Manager:
    """Manager for GitHub Projects v2 operations"""

    def __init__(self, github_manager):
        self.github_manager = github_manager
        self.graphql_endpoint = "https://api.github.com/graphql"

    async def get_repository_projects(self, repo_owner: str, repo_name: str) -> List[Dict[str, Any]]:
        """Get all Projects v2 for a repository"""
        try:
            query = """
            query($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                projectsV2(first: 20) {
                  nodes {
                    id
                    title
                    description
                    number
                    state
                    createdAt
                    closedAt
                    url
                    fields(first: 20) {
                      nodes {
                        ... on ProjectV2Field {
                          id
                          name
                          dataType
                          options {
                            name
                            id
                          }
                        }
                        ... on ProjectV2SingleSelectField {
                          id
                          name
                          dataType
                          options {
                            name
                            id
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """

            variables = {"owner": repo_owner, "name": repo_name}
            result = await self._graphql_query(query, variables)

            if result and "data" in result:
                projects = result["data"]["repository"]["projectsV2"]["nodes"]
                logger.info(f"Found {len(projects)} Projects v2 for {repo_owner}/{repo_name}")
                return projects

        except Exception as e:
            logger.error(f"Failed to get Projects v2: {e}")

        return []

    async def create_project_v2(self,
                              repo_owner: str,
                              repo_name: str,
                              title: str,
                              description: str = "",
                              template: str = "Basic kanban") -> Optional[Dict[str, Any]]:
        """Create a new Project v2"""
        try:
            mutation = """
            mutation($input: CreateProjectV2Input!) {
              createProjectV2(input: $input) {
                projectV2 {
                  id
                  title
                  number
                  url
                }
              }
            }
            """

            variables = {
                "input": {
                    "ownerId": await self._get_owner_id(repo_owner, repo_name),
                    "title": title,
                    "description": description
                }
            }

            result = await self._graphql_query(mutation, variables)

            if result and "data" in result:
                project = result["data"]["createProjectV2"]["projectV2"]
                logger.info(f"Created Project v2: {project['title']}")
                return project

        except Exception as e:
            logger.error(f"Failed to create Project v2: {e}")

        return None

    async def add_item_to_project(self,
                                project_id: str,
                                content_id: str,
                                content_type: str = "Issue") -> Optional[Dict[str, Any]]:
        """Add an item to Project v2"""
        try:
            mutation = """
            mutation($input: AddProjectV2ItemByIdInput!) {
              addProjectV2ItemById(input: $input) {
                item {
                  id
                  content {
                    ... on Issue {
                      id
                      number
                      title
                    }
                    ... on PullRequest {
                      id
                      number
                      title
                    }
                  }
                }
              }
            }
            """

            variables = {
                "input": {
                    "projectId": project_id,
                    "contentId": content_id
                }
            }

            result = await self._graphql_query(mutation, variables)

            if result and "data" in result:
                item = result["data"]["addProjectV2ItemById"]["item"]
                logger.info(f"Added item to project: {item['content']['title']}")
                return item

        except Exception as e:
            logger.error(f"Failed to add item to project: {e}")

        return None

    async def update_project_item_field(self,
                                      project_id: str,
                                      item_id: str,
                                      field_id: str,
                                      value: Union[str, int, bool]) -> bool:
        """Update a field value for a project item"""
        try:
            mutation = """
            mutation($input: UpdateProjectV2ItemFieldValueInput!) {
              updateProjectV2ItemFieldValue(input: $input) {
                projectV2Item {
                  id
                }
              }
            }
            """

            field_value = {"text": str(value)} if isinstance(value, str) else {"number": value}

            variables = {
                "input": {
                    "projectId": project_id,
                    "itemId": item_id,
                    "fieldId": field_id,
                    "value": field_value
                }
            }

            result = await self._graphql_query(mutation, variables)

            if result and "data" in result:
                logger.info(f"Updated project item field")
                return True

        except Exception as e:
            logger.error(f"Failed to update project item field: {e}")

        return False

    async def get_project_items(self, project_id: str) -> List[ProjectV2Item]:
        """Get all items in a Project v2"""
        try:
            query = """
            query($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  items(first: 50) {
                    nodes {
                      id
                      content {
                        ... on Issue {
                          id
                          number
                          title
                          state
                          labels(first: 10) {
                            nodes {
                              name
                            }
                          }
                          assignees(first: 5) {
                            nodes {
                              login
                            }
                          }
                        }
                        ... on PullRequest {
                          id
                          number
                          title
                          state
                          labels(first: 10) {
                            nodes {
                              name
                            }
                          }
                          assignees(first: 5) {
                            nodes {
                              login
                            }
                          }
                        }
                      }
                      fieldValues(first: 20) {
                        nodes {
                          __typename
                          ... on ProjectV2ItemFieldTextValue {
                            text
                            field {
                              ... on ProjectV2Field {
                                name
                              }
                            }
                          }
                          ... on ProjectV2ItemFieldSingleSelectValue {
                            name
                            optionId
                            field {
                              ... on ProjectV2Field {
                                name
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """

            variables = {"projectId": project_id}
            result = await self._graphql_query(query, variables)

            if result and "data" in result:
                items_data = result["data"]["node"]["items"]["nodes"]
                items = []

                for item_data in items_data:
                    content = item_data["content"]
                    item = ProjectV2Item(
                        id=item_data["id"],
                        title=content["title"],
                        content_type=content["__typename"],
                        content_id=content["number"]
                    )
                    items.append(item)

                return items

        except Exception as e:
            logger.error(f"Failed to get project items: {e}")

        return []

    async def _graphql_query(self, query: str, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a GraphQL query"""
        try:
            headers = {
                "Authorization": f"Bearer {self.github_manager.config.token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.graphql_endpoint,
                    json={"query": query, "variables": variables},
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"GraphQL query failed: {response.status}")

        except Exception as e:
            logger.error(f"GraphQL query error: {e}")

        return None

    async def _get_owner_id(self, repo_owner: str, repo_name: str) -> str:
        """Get the owner ID for GraphQL operations"""
        return f"MDg6T3JlbmVy"

class ProjectV2ManagementAgent:
    """CrewAI Agent for GitHub Projects v2 Management"""

    def __init__(self, github_manager):
        self.github_manager = github_manager
        self.projects_manager = GitHubProjectsV2Manager(github_manager)

    async def analyze_project_structure(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """Analyze current project structure and suggest improvements"""
        projects = await self.projects_manager.get_repository_projects(repo_owner, repo_name)

        analysis = {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.get("state") == "OPEN"]),
            "closed_projects": len([p for p in projects if p.get("state") == "CLOSED"]),
            "projects": projects,
            "recommendations": []
        }

        if len(projects) == 0:
            analysis["recommendations"].append({
                "type": "create_project",
                "title": "Create main development project",
                "description": "Set up a main project for tracking development tasks",
                "priority": "high"
            })

        if not projects:
            analysis["recommendations"].append({
                "type": "migrate_to_v2",
                "title": "Migrate to Projects v2",
                "description": "Upgrade from classic projects to the new Projects v2",
                "priority": "medium"
            })

        return analysis

    async def create_project_for_analysis(self,
                                        repo_owner: str,
                                        repo_name: str,
                                        analysis_results: Dict[str, Any]) -> Optional[str]:
        """Create a project to track analysis results and follow-up tasks"""
        try:
            project_title = f"Repository Analysis - {datetime.now().strftime('%Y-%m-%d')}"
            project_description = f"""
            Automated repository analysis results for {repo_owner}/{repo_name}

            Analysis completed: {datetime.now().isoformat()}

            This project tracks:
            - Security improvements
            - Performance optimizations
            - Code quality enhancements
            - CI/CD workflow improvements
            - Documentation updates
            """

            project = await self.projects_manager.create_project_v2(
                repo_owner, repo_name, project_title, project_description
            )

            if project:
                return project["id"]

        except Exception as e:
            logger.error(f"Failed to create analysis project: {e}")

        return None

    async def create_tracking_items(self,
                                  project_id: str,
                                  analysis_results: Dict[str, Any]) -> List[ProjectV2Item]:
        """Create project items to track analysis recommendations"""
        items = []

        for category, results in analysis_results.items():
            if isinstance(results, dict) and "recommendations" in results:
                for rec in results["recommendations"]:
                    item = await self._create_item_from_recommendation(
                        project_id, category, rec
                    )
                    if item:
                        items.append(item)

        return items

    async def _create_item_from_recommendation(self,
                                             project_id: str,
                                             category: str,
                                             recommendation: Dict[str, Any]) -> Optional[ProjectV2Item]:
        """Create a project item from a recommendation"""
        try:
            content_id = recommendation.get("content_id")
            content_type = recommendation.get("content_type", "Issue")

            if content_id:
                item = await self.projects_manager.add_item_to_project(
                    project_id, content_id, content_type
                )
                if item:
                    return ProjectV2Item(
                        id=item["id"],
                        title=item["content"]["title"],
                        content_type=content_type,
                        content_id=item["content"]["number"]
                    )
            else:
                issue_title = f"[{category.upper()}] {recommendation.get('title', 'Improvement needed')}"
                issue_body = recommendation.get('description', recommendation.get('body', ''))

                github_issue = self.github_manager.create_issue(
                    title=issue_title,
                    body=issue_body,
                    labels=[category, "automation", "ai-analysis"]
                )

                if github_issue:
                    item = await self.projects_manager.add_item_to_project(
                        project_id, str(github_issue.node_id)
                    )

                    if item:
                        return ProjectV2Item(
                            id=item["id"],
                            title=issue_title,
                            content_type="Issue",
                            content_id=github_issue.number,
                            labels=[category, "automation", "ai-analysis"]
                        )

        except Exception as e:
            logger.error(f"Failed to create tracking item: {e}")

        return None

    async def setup_automatic_project_updates(self,
                                            repo_owner: str,
                                            repo_name: str,
                                            project_id: str) -> bool:
        """Set up automatic project updates via GitHub Actions"""
        try:
            workflow_content = f"""name: Auto Project Updates

on:
  issues:
    types: [opened, closed, reopened]
  pull_request:
    types: [opened, closed, reopened, ready_for_review]
  schedule:
    - cron: '0 9 * * 1'

jobs:
  update-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Update Project Status
        uses: actions/github-script@v6
        with:
          github-token: ${{{{ secrets.GITHUB_TOKEN }}}}
          script: |
            const projectId = "{project_id}";

            const issues = await github.rest.issues.listForRepo({{
              owner: "{repo_owner}",
              repo: "{repo_name}",
              state: "open"
            }});

            for (const issue of issues.data) {{
              if (issue.labels.some(label => label.name.includes('ai-analysis'))) {{
                console.log(`Auto-assigning issue #${{issue.number}} to project`);
              }}
            }}
"""

            logger.info("Auto project update workflow created")
            return True

        except Exception as e:
            logger.error(f"Failed to setup automatic project updates: {e}")
            return False

    async def generate_project_summary_report(self,
                                            project_id: str,
                                            analysis_period_days: int = 30) -> str:
        """Generate a summary report of project activity"""
        try:
            items = await self.projects_manager.get_project_items(project_id)

            cutoff_date = datetime.now() - timedelta(days=analysis_period_days)
            recent_items = [item for item in items if item.metadata.get("created_at") and
                           datetime.fromisoformat(item.metadata["created_at"]) > cutoff_date]

            report = f"""# Project Activity Report
Period: Last {analysis_period_days} days
Generated: {datetime.now().isoformat()}

## Summary
- Total Items: {len(items)}
- Recent Items: {len(recent_items)}
- Categories: {len(set(item.content_type for item in items))}

## Recent Activity
"""

            for item in recent_items[:10]:
                report += f"- {item.title} ({item.content_type})\n"

            report += f"\n## Top Categories\n"
            categories = {}
            for item in items:
                cat = item.content_type
                categories[cat] = categories.get(cat, 0) + 1

            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                report += f"- {cat}: {count} items\n"

            return report

        except Exception as e:
            logger.error(f"Failed to generate project summary: {e}")
            return "Failed to generate project summary report"

__all__ = [
    'GitHubProjectsV2Manager',
    'ProjectV2ManagementAgent',
    'ProjectV2Item',
    'ProjectV2Column'
]
