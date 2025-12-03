#!/usr/bin/env python3
"""
Scan repository for outstanding errors and create GitHub issues.

This script scans the repository for:
1. Failed workflow runs
2. Open pull requests with failing checks
3. TODO/FIXME comments in code
4. Errors in log files
5. Issues mentioned in PRODUCTION.md or other documentation
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any
from github import Github
from datetime import datetime, timedelta


class RepositoryErrorScanner:
    def __init__(self, repo_name: str, github_token: str):
        """Initialize the scanner."""
        self.g = Github(github_token)
        self.repo = self.g.get_repo(repo_name)
        self.repo_path = Path.cwd()
        self.errors_found = []

    def scan_todo_fixme_comments(self) -> List[Dict[str, Any]]:
        """Scan for TODO and FIXME comments in code files."""
        print("Scanning for TODO/FIXME comments...")
        todos = []

        # Patterns to search for
        patterns = [
            (r'#\s*(TODO|FIXME|HACK|XXX|BUG)[\s:]+(.+)', ['.py']),
            (r'//\s*(TODO|FIXME|HACK|XXX|BUG)[\s:]+(.+)', ['.js', '.ts', '.tsx', '.jsx', '.go']),
            (r'/\*\s*(TODO|FIXME|HACK|XXX|BUG)[\s:]+(.+?)\*/', ['.js', '.ts', '.tsx', '.jsx', '.css']),
        ]

        # Directories to exclude
        exclude_dirs = {
            'node_modules', 'venv', '.venv', '__pycache__', '.git',
            'dist', 'build', '.next', 'coverage', 'tmp'
        }

        for py_file in self.repo_path.rglob('*'):
            # Skip excluded directories
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue

            if not py_file.is_file():
                continue

            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')

                for pattern, extensions in patterns:
                    if py_file.suffix in extensions:
                        for match in re.finditer(pattern, content):
                            todos.append({
                                'file': str(py_file.relative_to(self.repo_path)),
                                'line': content[:match.start()].count('\n') + 1,
                                'type': match.group(1),
                                'message': match.group(2).strip()
                            })
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return todos

    def scan_production_issues(self) -> List[Dict[str, Any]]:
        """Scan PRODUCTION.md for outstanding issues."""
        print("Scanning PRODUCTION.md...")
        issues = []

        prod_file = self.repo_path / 'PRODUCTION.md'
        if not prod_file.exists():
            return issues

        try:
            content = prod_file.read_text(encoding='utf-8')

            # Look for unchecked items (- [ ])
            for match in re.finditer(r'- \[ \] \*\*(.+?)\*\*(.+?)(?=\n(?:- |\n|$))', content, re.DOTALL):
                title = match.group(1).strip()
                description = match.group(2).strip()
                issues.append({
                    'source': 'PRODUCTION.md',
                    'title': title,
                    'description': description
                })

            # Look for ❌ markers
            for match in re.finditer(r'- ❌ (.+)', content):
                issues.append({
                    'source': 'PRODUCTION.md',
                    'title': 'Production Issue',
                    'description': match.group(1).strip()
                })
        except Exception as e:
            print(f"Error reading PRODUCTION.md: {e}")

        return issues

    def scan_failed_workflows(self) -> List[Dict[str, Any]]:
        """Scan for recent failed workflow runs."""
        print("Scanning for failed workflows...")
        failed = []

        try:
            # Get workflow runs from the last 7 days
            since = datetime.now() - timedelta(days=7)
            workflows = self.repo.get_workflow_runs(
                status='completed',
                conclusion='failure',
                created=f'>={since.isoformat()}'
            )

            for run in workflows[:10]:  # Limit to 10 most recent
                failed.append({
                    'workflow': run.name,
                    'run_id': run.id,
                    'url': run.html_url,
                    'branch': run.head_branch,
                    'created_at': run.created_at.isoformat()
                })
        except Exception as e:
            print(f"Error fetching workflows: {e}")

        return failed

    def scan_open_prs_with_failures(self) -> List[Dict[str, Any]]:
        """Scan for open PRs with failing checks."""
        print("Scanning for PRs with failing checks...")
        failing_prs = []

        try:
            prs = self.repo.get_pulls(state='open')

            for pr in prs[:20]:  # Limit to 20 most recent
                # Check if any checks failed
                commits = pr.get_commits()
                if commits.totalCount > 0:
                    last_commit = list(commits)[-1]
                    status = last_commit.get_combined_status()

                    if status.state in ['failure', 'error']:
                        failing_prs.append({
                            'pr_number': pr.number,
                            'title': pr.title,
                            'url': pr.html_url,
                            'status': status.state
                        })
        except Exception as e:
            print(f"Error fetching PRs: {e}")

        return failing_prs

    def create_summary_issues(self):
        """Create GitHub issues for found errors."""
        print("\nCreating GitHub issues...")

        # Scan for all types of errors
        todos = self.scan_todo_fixme_comments()
        production_issues = self.scan_production_issues()
        failed_workflows = self.scan_failed_workflows()
        failing_prs = self.scan_open_prs_with_failures()

        # Create issue for TODO/FIXME comments if significant number found
        if len(todos) > 5:
            self._create_todo_issue(todos[:50])  # Limit to top 50

        # Create issues for production checklist items
        if production_issues:
            self._create_production_issues(production_issues[:20])  # Limit to 20

        # Create issue for failed workflows
        if failed_workflows:
            self._create_workflow_failure_summary(failed_workflows)

        # Create issue for failing PRs
        if failing_prs:
            self._create_failing_pr_summary(failing_prs)

        print(f"\n✅ Scan complete!")
        print(f"   - TODO/FIXME comments: {len(todos)}")
        print(f"   - Production issues: {len(production_issues)}")
        print(f"   - Failed workflows: {len(failed_workflows)}")
        print(f"   - Failing PRs: {len(failing_prs)}")

    def _create_todo_issue(self, todos: List[Dict[str, Any]]):
        """Create issue for TODO/FIXME comments."""
        # Check if similar issue exists
        existing = list(self.repo.get_issues(
            state='open',
            labels=['code-cleanup', 'automated']
        ))

        if any('TODO/FIXME Comments' in i.title for i in existing[:3]):
            print("  ℹ️  Skipping TODO issue (recent one exists)")
            return

        title = f"📝 TODO/FIXME Comments Found - {datetime.now().strftime('%Y-%m-%d')}"

        # Group by type
        by_type = {}
        for todo in todos:
            todo_type = todo['type']
            if todo_type not in by_type:
                by_type[todo_type] = []
            by_type[todo_type].append(todo)

        body = f"""## Code Comments Requiring Attention

Found {len(todos)} TODO/FIXME comments in the codebase.

"""
        for todo_type, items in sorted(by_type.items()):
            body += f"\n### {todo_type} Comments ({len(items)})\n\n"
            for item in items[:10]:  # Limit per type
                body += f"- `{item['file']}:{item['line']}` - {item['message']}\n"
            if len(items) > 10:
                body += f"\n_... and {len(items) - 10} more_\n"

        body += "\n\n---\n*This issue was automatically created by the repository scanner.*"

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=['code-cleanup', 'automated', 'maintenance']
            )
            print(f"  ✅ Created TODO issue: #{issue.number}")
        except Exception as e:
            print(f"  ❌ Error creating TODO issue: {e}")

    def _create_production_issues(self, issues: List[Dict[str, Any]]):
        """Create issues for production checklist items."""
        # Check if similar issue exists
        existing = list(self.repo.get_issues(
            state='open',
            labels=['production-readiness', 'automated']
        ))

        if any('Production Readiness' in i.title for i in existing[:3]):
            print("  ℹ️  Skipping production issues (recent one exists)")
            return

        title = f"🚀 Production Readiness Issues - {datetime.now().strftime('%Y-%m-%d')}"

        body = f"""## Outstanding Production Readiness Items

Found {len(issues)} items in PRODUCTION.md that need attention:

"""
        for issue in issues[:15]:
            body += f"\n### {issue['title']}\n\n"
            body += f"{issue['description']}\n"

        if len(issues) > 15:
            body += f"\n_... and {len(issues) - 15} more items_\n"

        body += "\n\n---\n*This issue was automatically created by the repository scanner.*"

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=['production-readiness', 'automated', 'high-priority']
            )
            print(f"  ✅ Created production readiness issue: #{issue.number}")
        except Exception as e:
            print(f"  ❌ Error creating production issue: {e}")

    def _create_workflow_failure_summary(self, failures: List[Dict[str, Any]]):
        """Create summary issue for workflow failures."""
        # Check if similar issue exists
        existing = list(self.repo.get_issues(
            state='open',
            labels=['ci-failures', 'automated']
        ))

        if any('Workflow Failures' in i.title for i in existing[:3]):
            print("  ℹ️  Skipping workflow failures (recent one exists)")
            return

        title = f"🔥 Recent Workflow Failures - {datetime.now().strftime('%Y-%m-%d')}"

        body = f"""## Recent Workflow Failures

Found {len(failures)} failed workflow runs in the last 7 days:

"""
        for failure in failures:
            body += f"\n- **{failure['workflow']}** ([Run #{failure['run_id']}]({failure['url']}))\n"
            body += f"  - Branch: `{failure['branch']}`\n"
            body += f"  - Date: {failure['created_at']}\n"

        body += "\n\n---\n*This issue was automatically created by the repository scanner.*"

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=['ci-failures', 'automated']
            )
            print(f"  ✅ Created workflow failures issue: #{issue.number}")
        except Exception as e:
            print(f"  ❌ Error creating workflow failures issue: {e}")

    def _create_failing_pr_summary(self, prs: List[Dict[str, Any]]):
        """Create summary issue for PRs with failing checks."""
        # Check if similar issue exists
        existing = list(self.repo.get_issues(
            state='open',
            labels=['pr-failures', 'automated']
        ))

        if any('PRs with Failing Checks' in i.title for i in existing[:3]):
            print("  ℹ️  Skipping PR failures (recent one exists)")
            return

        title = f"⚠️  PRs with Failing Checks - {datetime.now().strftime('%Y-%m-%d')}"

        body = f"""## Open PRs with Failing Checks

Found {len(prs)} open pull requests with failing status checks:

"""
        for pr in prs:
            body += f"\n- [#{pr['pr_number']}: {pr['title']}]({pr['url']})\n"
            body += f"  - Status: `{pr['status']}`\n"

        body += "\n\n---\n*This issue was automatically created by the repository scanner.*"

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=['pr-failures', 'automated']
            )
            print(f"  ✅ Created PR failures issue: #{issue.number}")
        except Exception as e:
            print(f"  ❌ Error creating PR failures issue: {e}")


def main():
    """Main function."""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        return 1

    repo_name = os.environ.get('GITHUB_REPOSITORY', 'cbwinslow/opendiscourse')

    print(f"🔍 Scanning repository: {repo_name}\n")

    scanner = RepositoryErrorScanner(repo_name, github_token)
    scanner.create_summary_issues()

    return 0


if __name__ == '__main__':
    exit(main())
