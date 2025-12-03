"""
GitHub Management CrewAI Main Orchestrator
Comprehensive orchestration for GitHub repository management with AI agents
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from github_crew_config import (
    GitHubOperationsManager,
    create_github_management_crew,
    GitHubConfig,
    CICDWorkflowAgent,
    CodeQualityAgent
)

from ai_services_integration import AIServicesManager
from project_v2_management import ProjectV2ManagementAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubManagementOrchestrator:
    """Main orchestrator for GitHub Management CrewAI system"""

    def __init__(self, repo_owner: str, repo_name: str, github_token: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')

        self.github_config = GitHubConfig(repo_owner, repo_name, self.github_token)
        self.github_manager = GitHubOperationsManager(self.github_config)
        self.ai_manager = AIServicesManager()
        self.project_manager = ProjectV2ManagementAgent(self.github_manager)

        self.analysis_results = {}
        self.action_results = {}

        self.output_dir = Path("github_analysis_results")
        self.output_dir.mkdir(exist_ok=True)

    async def run_complete_analysis(self) -> Dict[str, Any]:
        """Run complete GitHub repository analysis and management"""
        logger.info(f"Starting complete analysis for {self.repo_owner}/{self.repo_name}")

        try:
            logger.info("Phase 1: Repository Structure Analysis")
            repository_analysis = await self._analyze_repository()

            logger.info("Phase 2: AI-Powered Code Analysis")
            ai_analysis = await self._run_ai_code_analysis(repository_analysis)

            logger.info("Phase 3: GitHub Issues Management")
            issue_actions = await self._manage_github_issues(repository_analysis, ai_analysis)

            logger.info("Phase 4: Project v2 Management")
            project_actions = await self._manage_projects_v2(repository_analysis, ai_analysis)

            logger.info("Phase 5: CI/CD Workflow Management")
            workflow_actions = await self._manage_cicd_workflows(repository_analysis, ai_analysis)

            logger.info("Phase 6: Code Quality Assessment")
            quality_actions = await self._assess_code_quality(repository_analysis)

            final_results = {
                "repository": repository_analysis,
                "ai_analysis": ai_analysis,
                "actions": {
                    "issues": issue_actions,
                    "projects": project_actions,
                    "workflows": workflow_actions,
                    "quality": quality_actions
                },
                "timestamp": datetime.now().isoformat(),
                "summary": await self._generate_executive_summary()
            }

            await self._save_results(final_results)

            logger.info("Complete analysis finished successfully")
            return final_results

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    async def _analyze_repository(self) -> Dict[str, Any]:
        """Analyze repository structure and current state"""
        try:
            analysis = self.github_manager.analyze_repository()

            repo = self.github_manager.get_repository()
            if repo:
                analysis.update({
                    "analysis_timestamp": datetime.now().isoformat(),
                    "repository_url": f"https://github.com/{self.repo_owner}/{self.repo_name}",
                    "default_branch": repo.default_branch,
                    "repository_size": repo.size,
                    "last_commit_date": repo.pushed_at.isoformat(),
                    "has_wiki": repo.has_wiki,
                    "has_issues": repo.has_issues,
                    "has_projects": repo.has_projects
                })

            return analysis

        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return {"error": str(e)}

    async def _run_ai_code_analysis(self, repository_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Run AI-powered code analysis"""
        try:
            repo = self.github_manager.get_repository()
            if not repo:
                return {"error": "Repository not accessible"}

            file_patterns = ["*.py", "*.js", "*.ts", "*.go", "*.java", "*.md"]
            ai_results = {}

            for pattern in file_patterns:
                try:
                    files = list(repo.get_contents("", ref="HEAD"))[:5]

                    for file in files:
                        if file.type == "file" and any(file.name.endswith(ext) for ext in ['.py', '.js', '.ts', '.go', '.java']):
                            content = file.decoded_content.decode('utf-8')

                            analysis_result = await self.ai_manager.comprehensive_code_analysis(
                                content[:2000],
                                repository_analysis
                            )

                            ai_results[f"{pattern}_{file.name}"] = analysis_result
                            break

                except Exception as e:
                    logger.warning(f"Failed to analyze files with pattern {pattern}: {e}")

            consolidated_report = self.ai_manager.generate_consolidated_report(
                ai_results, repository_analysis
            )

            return {
                "file_analyses": ai_results,
                "consolidated_report": consolidated_report,
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"AI code analysis failed: {e}")
            return {"error": str(e)}

    async def _manage_github_issues(self, repository_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Manage GitHub issues based on analysis"""
        try:
            actions_taken = []

            open_issues = repository_analysis.get('open_issues', 0)

            if open_issues < 20:
                new_issue = self.github_manager.create_issue(
                    title="Enhance Issue Tracking and Project Management",
                    body=f"""
                    ## Analysis Results from {datetime.now().strftime('%Y-%m-%d')}

                    Current repository has only {open_issues} open issues.

                    ### AI Analysis Summary:
                    {ai_analysis.get('consolidated_report', 'No AI analysis available')}

                    ### Recommendations:
                    1. Create comprehensive issue templates
                    2. Set up automated issue creation from CI/CD failures
                    3. Implement issue labeling automation
                    4. Add issue templates for bug reports and feature requests
                    5. Create project boards for better organization

                    ### Actions Taken:
                    - Issue created automatically by GitHub Management CrewAI
                    - Labels: enhancement, project-management, ai-analysis
                    - Priority: high
                    """,
                    labels=["enhancement", "project-management", "ai-analysis"],
                    assignees=[]
                )

                if new_issue:
                    actions_taken.append({
                        "action": "created_issue",
                        "issue_number": new_issue.number,
                        "title": new_issue.title
                    })

            if ai_analysis.get('file_analyses'):
                for file_key, analysis in ai_analysis['file_analyses'].items():
                    if analysis:
                        security_issue = self.github_manager.create_issue(
                            title="Security Analysis - AI-Generated Findings",
                            body=f"""
                            ## AI Security Analysis Results

                            File analyzed: {file_key}

                            ### Findings:
                            {ai_analysis.get('consolidated_report', 'No specific findings')}

                            ### Recommendations:
                            - Review security vulnerabilities
                            - Implement security best practices
                            - Add security testing to CI/CD
                            - Consider using security scanning tools
                            """,
                            labels=["security", "ai-analysis", "high-priority"]
                        )

                        if security_issue:
                            actions_taken.append({
                                "action": "created_security_issue",
                                "issue_number": security_issue.number,
                                "title": security_issue.title
                            })
                        break

            return {
                "actions_taken": actions_taken,
                "total_actions": len(actions_taken),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"GitHub issue management failed: {e}")
            return {"error": str(e)}

    async def _manage_projects_v2(self, repository_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Manage GitHub Projects v2 based on analysis"""
        try:
            project_actions = []

            project_analysis = await self.project_manager.analyze_project_structure(
                self.repo_owner, self.repo_name
            )

            if project_analysis["total_projects"] == 0:
                project_id = await self.project_manager.create_project_for_analysis(
                    self.repo_owner, self.repo_name, ai_analysis
                )

                if project_id:
                    project_actions.append({
                        "action": "created_project_v2",
                        "project_id": project_id,
                        "title": f"Repository Analysis - {datetime.now().strftime('%Y-%m-%d')}"
                    })

                    tracking_items = await self.project_manager.create_tracking_items(
                        project_id, ai_analysis
                    )

                    project_actions.append({
                        "action": "created_tracking_items",
                        "count": len(tracking_items),
                        "project_id": project_id
                    })

            if project_analysis.get("projects"):
                project_id = project_analysis["projects"][0]["id"]
                auto_update_success = await self.project_manager.setup_automatic_project_updates(
                    self.repo_owner, self.repo_name, project_id
                )

                if auto_update_success:
                    project_actions.append({
                        "action": "setup_auto_updates",
                        "project_id": project_id
                    })

            return {
                "project_analysis": project_analysis,
                "actions_taken": project_actions,
                "total_actions": len(project_actions),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Project v2 management failed: {e}")
            return {"error": str(e)}

    async def _manage_cicd_workflows(self, repository_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Manage CI/CD workflows based on analysis"""
        try:
            workflow_actions = []

            cicd_agent = CICDWorkflowAgent()

            workflow_specs = cicd_agent.analyze_workflow_needs(repository_analysis)

            workflow_files = cicd_agent.create_workflow_files(workflow_specs)

            for file_path, content in workflow_files.items():
                workflow_actions.append({
                    "action": "created_workflow",
                    "file_path": file_path,
                    "workflow_name": workflow_specs[list(workflow_files.keys()).index(file_path)]["name"]
                })

            return {
                "workflow_specifications": workflow_specs,
                "workflow_files_created": len(workflow_files),
                "workflow_files": workflow_files,
                "actions_taken": workflow_actions,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"CI/CD workflow management failed: {e}")
            return {"error": str(e)}

    async def _assess_code_quality(self, repository_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess code quality using CodeQualityAgent"""
        try:
            quality_agent = CodeQualityAgent()

            quality_analysis = quality_agent.analyze_code_quality(".")

            quality_report = quality_agent.generate_quality_report(quality_analysis)

            quality_actions = []

            if quality_analysis.get("security_issues", 0) > 0:
                security_issue = self.github_manager.create_issue(
                    title="Security Issues Identified - Code Quality Assessment",
                    body=f"""
                    ## Security Analysis Results

                    {quality_report}

                    ### Immediate Actions Required:
                    - Address {quality_analysis['security_issues']} security vulnerabilities
                    - Implement security best practices
                    - Add security testing to CI/CD pipeline
                    - Review and update dependencies
                    """,
                    labels=["security", "quality", "high-priority"]
                )

                if security_issue:
                    quality_actions.append({
                        "action": "created_security_issue",
                        "issue_number": security_issue.number
                    })

            if quality_analysis.get("test_coverage", 0) < 80:
                testing_issue = self.github_manager.create_issue(
                    title="Improve Test Coverage - Code Quality Assessment",
                    body=f"""
                    ## Testing Analysis Results

                    Current test coverage: {quality_analysis['test_coverage']}%
                    Target: 80%+

                    {quality_report}

                    ### Recommendations:
                    - Increase test coverage to 80%+
                    - Add integration tests
                    - Implement test automation
                    - Use test coverage reporting
                    """,
                    labels=["testing", "quality", "enhancement"]
                )

                if testing_issue:
                    quality_actions.append({
                        "action": "created_testing_issue",
                        "issue_number": testing_issue.number
                    })

            return {
                "quality_analysis": quality_analysis,
                "quality_report": quality_report,
                "actions_taken": quality_actions,
                "total_actions": len(quality_actions),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Code quality assessment failed: {e}")
            return {"error": str(e)}

    async def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary of all activities"""
        return {
            "total_issues_created": len([a for a in self.action_results.get('issues', {}).get('actions_taken', [])
                                       if a.get('action') == 'created_issue']),
            "total_projects_created": len([a for a in self.action_results.get('projects', {}).get('actions_taken', [])
                                         if a.get('action') == 'created_project_v2']),
            "total_workflows_created": self.action_results.get('workflows', {}).get('workflow_files_created', 0),
            "security_issues_identified": sum(1 for a in self.action_results.get('issues', {}).get('actions_taken', [])
                                            if 'security' in a.get('title', '').lower()),
            "next_recommended_actions": [
                "Review and prioritize created issues",
                "Set up project boards for better organization",
                "Implement suggested CI/CD workflows",
                "Address security vulnerabilities",
                "Improve test coverage"
            ]
        }

    async def _save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to files"""
        try:
            json_path = self.output_dir / f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            summary_path = self.output_dir / f"analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(summary_path, 'w') as f:
                f.write("# GitHub Repository Analysis Summary\n\n")
                f.write(f"**Repository:** {self.repo_owner}/{self.repo_name}\n")
                f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("## Executive Summary\n\n")
                f.write(f"- **Issues Created:** {results['summary'].get('total_issues_created', 0)}\n")
                f.write(f"- **Projects Created:** {results['summary'].get('total_projects_created', 0)}\n")
                f.write(f"- **Workflows Created:** {results['summary'].get('total_workflows_created', 0)}\n")
                f.write(f"- **Security Issues:** {results['summary'].get('security_issues_identified', 0)}\n\n")

                f.write("## Repository Overview\n\n")
                repo_data = results.get('repository', {})
                f.write(f"- **Language:** {repo_data.get('language', 'Unknown')}\n")
                f.write(f"- **Stars:** {repo_data.get('stars', 0)}\n")
                f.write(f"- **Forks:** {repo_data.get('forks', 0)}\n")
                f.write(f"- **Open Issues:** {repo_data.get('open_issues', 0)}\n\n")

                f.write("## AI Analysis\n\n")
                f.write(results.get('ai_analysis', {}).get('consolidated_report', 'No AI analysis available')[:1000] + "...")

            logger.info(f"Results saved to {self.output_dir}")

        except Exception as e:
            logger.error(f"Failed to save results: {e}")

async def main():
    """Main execution function for GitHub Management CrewAI"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Management CrewAI")
    parser.add_argument("repo_owner", help="Repository owner/organization")
    parser.add_argument("repo_name", help="Repository name")
    parser.add_argument("--token", help="GitHub token (or use GITHUB_TOKEN env var)")
    parser.add_argument("--output", help="Output directory", default="github_analysis_results")

    args = parser.parse_args()

    orchestrator = GitHubManagementOrchestrator(
        args.repo_owner,
        args.repo_name,
        args.token
    )
    orchestrator.output_dir = Path(args.output)
    orchestrator.output_dir.mkdir(exist_ok=True)

    try:
        results = await orchestrator.run_complete_analysis()
        print(f"✅ Analysis completed successfully!")
        print(f"📁 Results saved to: {orchestrator.output_dir}")
        print(f"🎯 Issues created: {results['summary'].get('total_issues_created', 0)}")
        print(f"📋 Projects created: {results['summary'].get('total_projects_created', 0)}")
        print(f"🔄 Workflows created: {results['summary'].get('total_workflows_created', 0)}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

__all__ = [
    'GitHubManagementOrchestrator',
    'main'
]
