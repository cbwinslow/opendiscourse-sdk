#!/usr/bin/env python3
"""Create GitHub issue from PR comment."""
import os
import re
from github import Github

try:
    g = Github(os.environ['GITHUB_TOKEN'])
    repo = g.get_repo(os.environ.get('GITHUB_REPOSITORY', 'cbwinslow/opendiscourse-sdk'))
    
    comment_body = os.environ.get('COMMENT_BODY', '')
    pr_number = int(os.environ.get('PR_NUMBER', '0'))
    
    # Extract issue content
    match = re.search(r'gh create issue\s*(.*)', comment_body, re.DOTALL | re.IGNORECASE)
    if match:
        issue_content = match.group(1).strip()
        lines = issue_content.split('\n')
        title = lines[0].strip() if lines else f"Issue from PR #{pr_number}"
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else 'No details provided'
        
        full_body = f"""**Created from PR Comment**
PR: #{pr_number}

---

{body}
"""
        
        issue = repo.create_issue(
            title=title,
            body=full_body,
            labels=['from-pr-comment', 'automated']
        )
        print(f"Created issue #{issue.number}")
        
        # Comment back
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(f"✅ Issue created: #{issue.number}")
except Exception as e:
    print(f"Failed to create issue: {e}")
