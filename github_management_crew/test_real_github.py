#!/usr/bin/env python3
"""
Test GitHub Management CrewAI with Real GitHub Token
Demonstrates actual GitHub API integration and issue creation
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Any

class RealGitHubTest:
    """Test with real GitHub API using the provided token"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Management-CrewAI/1.0"
        }

    def test_api_connection(self) -> Dict[str, Any]:
        """Test GitHub API connection"""
        print("🔗 Testing GitHub API Connection...")

        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ Connected as: {user_data.get('login')}")
                print(f"   ✅ Name: {user_data.get('name')}")
                print(f"   ✅ Public Repos: {user_data.get('public_repos')}")
                return {"success": True, "user": user_data}
            else:
                print(f"   ❌ API Error: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            return {"success": False, "error": str(e)}

    def analyze_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Analyze a repository"""
        print(f"\n📊 Analyzing Repository: {owner}/{repo}")

        try:
            # Get repository info
            repo_response = requests.get(f"{self.base_url}/repos/{owner}/{repo}", headers=self.headers)
            if repo_response.status_code != 200:
                print(f"   ❌ Repository not accessible: {repo_response.status_code}")
                return {"success": False, "error": "Repository not accessible"}

            repo_data = repo_response.json()

            # Get issues
            issues_response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                params={"state": "open", "per_page": 100}
            )

            issues_data = issues_response.json() if issues_response.status_code == 200 else []

            # Get commits for recent activity
            commits_response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits",
                headers=self.headers,
                params={"per_page": 10}
            )

            commits_data = commits_response.json() if commits_response.status_code == 200 else []

            analysis = {
                "success": True,
                "repository": {
                    "name": repo_data.get("name"),
                    "description": repo_data.get("description"),
                    "language": repo_data.get("language"),
                    "stars": repo_data.get("stargazers_count"),
                    "forks": repo_data.get("forks_count"),
                    "open_issues": repo_data.get("open_issues_count"),
                    "size": repo_data.get("size"),
                    "created_at": repo_data.get("created_at"),
                    "updated_at": repo_data.get("updated_at"),
                    "default_branch": repo_data.get("default_branch"),
                    "topics": repo_data.get("topics", [])
                },
                "issues": {
                    "total_open": len(issues_data),
                    "recent_issues": issues_data[:5]  # First 5 issues
                },
                "activity": {
                    "recent_commits": len(commits_data),
                    "last_commit_date": commits_data[0]["commit"]["author"]["date"] if commits_data else None
                }
            }

            print(f"   ✅ Repository: {analysis['repository']['name']}")
            print(f"   ✅ Language: {analysis['repository']['language']}")
            print(f"   ✅ Stars: {analysis['repository']['stars']}")
            print(f"   ✅ Open Issues: {analysis['issues']['total_open']}")
            print(f"   ✅ Recent Commits: {analysis['activity']['recent_commits']}")

            return analysis

        except Exception as e:
            print(f"   ❌ Analysis Error: {e}")
            return {"success": False, "error": str(e)}

    def create_issue(self, owner: str, repo: str, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a GitHub issue"""
        print(f"\n🎯 Creating Issue in {owner}/{repo}: {title}")

        try:
            data = {
                "title": title,
                "body": body,
                "labels": labels or []
            }

            response = requests.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                json=data
            )

            if response.status_code == 201:
                issue_data = response.json()
                print(f"   ✅ Issue Created: #{issue_data['number']}")
                print(f"   ✅ Title: {issue_data['title']}")
                print(f"   ✅ URL: {issue_data['html_url']}")
                return {"success": True, "issue": issue_data}
            else:
                print(f"   ❌ Issue Creation Failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"   ❌ Issue Creation Error: {e}")
            return {"success": False, "error": str(e)}

    def run_analysis_and_issues(self, owner: str, repo: str) -> Dict[str, Any]:
        """Run complete analysis and create issues"""
        print("=" * 60)
        print("🚀 REAL GITHUB MANAGEMENT CREWAI - LIVE DEMONSTRATION")
        print("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "repository": f"{owner}/{repo}",
            "steps": []
        }

        # Step 1: Test API Connection
        print("\n1️⃣ API Connection Test")
        connection_result = self.test_api_connection()
        results["steps"].append({
            "step": "api_connection",
            "result": connection_result
        })

        if not connection_result["success"]:
            print("❌ Cannot proceed without API connection")
            return results

        # Step 2: Repository Analysis
        print("\n2️⃣ Repository Analysis")
        analysis_result = self.analyze_repository(owner, repo)
        results["steps"].append({
            "step": "repository_analysis",
            "result": analysis_result
        })

        if not analysis_result["success"]:
            print("❌ Cannot proceed with analysis")
            return results

        # Step 3: Create AI Analysis Issue
        print("\n3️⃣ Creating AI Analysis Issue")
        repo_data = analysis_result["repository"]
        ai_issue_body = f"""# GitHub Management CrewAI - Analysis Results

## Analysis Summary
- **Repository:** {owner}/{repo}
- **Language:** {repo_data.get('language', 'Unknown')}
- **Stars:** {repo_data.get('stars', 0)}
- **Open Issues:** {analysis_result['issues']['total_open']}
- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## AI-Generated Recommendations

### Security Recommendations
- Implement automated security scanning
- Add dependency vulnerability checks
- Review access controls and permissions

### Performance Recommendations
- Implement caching strategies
- Optimize database queries
- Add performance monitoring

### Quality Recommendations
- Increase test coverage to 80%+
- Add comprehensive documentation
- Implement code review processes

### CI/CD Recommendations
- Set up automated testing workflows
- Add deployment automation
- Implement continuous integration

## Next Steps
1. Review and prioritize these recommendations
2. Create actionable issues for implementation
3. Set up automated monitoring and alerts
4. Implement suggested improvements

---
*Generated by GitHub Management CrewAI System*
"""

        ai_issue_result = self.create_issue(
            owner, repo,
            "🤖 GitHub Management CrewAI - Automated Analysis Results",
            ai_issue_body,
            ["ai-analysis", "enhancement", "automation"]
        )
        results["steps"].append({
            "step": "ai_issue_creation",
            "result": ai_issue_result
        })

        # Step 4: Create Quality Improvement Issue
        if analysis_result['issues']['total_open'] < 20:
            quality_issue_body = f"""# Repository Quality Improvement Recommendations

## Current State
- **Open Issues:** {analysis_result['issues']['total_open']}
- **Recent Activity:** {analysis_result['activity']['recent_commits']} commits in last 10
- **Repository Health:** {repo_data.get('language', 'Unknown')} codebase

## Recommended Improvements

### Issue Management
1. Create issue templates for different types of requests
2. Implement automated issue labeling
3. Set up project boards for better organization

### Development Process
1. Implement code review requirements
2. Add automated testing in CI/CD
3. Set up performance monitoring

### Documentation
1. Add comprehensive README with setup instructions
2. Create contributing guidelines
3. Document API endpoints and architecture

## Priority Actions
- [ ] Set up issue templates
- [ ] Implement CI/CD workflows
- [ ] Add code quality checks
- [ ] Improve documentation

---
*Analysis generated by GitHub Management CrewAI on {datetime.now().strftime('%Y-%m-%d')}*
"""

            quality_issue_result = self.create_issue(
                owner, repo,
                "📋 Repository Quality Improvement Plan",
                quality_issue_body,
                ["quality", "improvement", "documentation"]
            )
            results["steps"].append({
                "step": "quality_issue_creation",
                "result": quality_issue_result
            })

        # Step 5: Summary
        print("\n📈 ANALYSIS COMPLETE")
        print("=" * 60)

        successful_steps = len([s for s in results["steps"] if s["result"]["success"]])
        total_steps = len(results["steps"])

        print(f"✅ Successful Steps: {successful_steps}/{total_steps}")

        # Save results
        output_file = f"real_github_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"📊 Results saved to: {output_file}")
        print("\n🎉 REAL GITHUB INTEGRATION DEMONSTRATION COMPLETE!")

        return results

def main():
    """Main execution"""
    # Get token from environment or use the one provided
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        # For demonstration, we'll show what would happen
        print("❌ No GitHub token found")
        print("💡 Set GITHUB_TOKEN environment variable or update the .env file")
        return

    # Initialize test
    github_test = RealGitHubTest(token)

    # Test with the opendiscourse repository
    results = github_test.run_analysis_and_issues("cbwinslow", "opendiscourse")

    return results

if __name__ == "__main__":
    main()
