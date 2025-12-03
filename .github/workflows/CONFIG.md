# Auto Issue Creator Configuration

# This file documents the configuration options available.
# To customize, edit the workflow files directly.

## Scan Schedule Configuration

### Daily Scan (Default)
# Runs every day at 2 AM UTC
schedule:
  - cron: '0 2 * * *'

### Alternative Schedules

# Weekly on Sunday at 2 AM
# schedule:
#   - cron: '0 2 * * 0'

# Weekdays at 2 PM
# schedule:
#   - cron: '0 14 * * 1-5'

# Every 6 hours
# schedule:
#   - cron: '0 */6 * * *'

## Issue Thresholds

### TODO/FIXME Comments
minimum_todos_for_issue: 5
max_todos_per_issue: 50

### Production Issues
max_production_issues: 20

### Failed Workflows
max_failed_workflows: 10
workflow_lookback_days: 7

### Failing PRs
max_failing_prs: 20

## Labels Configuration

### Workflow Failures
workflow_failure_labels:
  - workflow-failure
  - automated

### PR Comments
pr_comment_labels:
  - from-pr-comment
  - automated

### Code Quality
code_quality_labels:
  - code-quality
  - automated

formatting_labels:
  - code-quality
  - formatting
  - automated

linting_labels:
  - code-quality
  - linting
  - automated

### Repository Scanner
todo_labels:
  - code-cleanup
  - automated
  - maintenance

production_labels:
  - production-readiness
  - automated
  - high-priority

ci_failure_labels:
  - ci-failures
  - automated

pr_failure_labels:
  - pr-failures
  - automated

## Duplicate Prevention

### Check last N issues before creating new one
duplicate_check_count: 3

### Minimum time between similar issues (not implemented yet)
# min_hours_between_similar: 24

## Scanning Exclusions

### Directories to exclude from TODO/FIXME scan
exclude_dirs:
  - node_modules
  - venv
  - .venv
  - __pycache__
  - .git
  - dist
  - build
  - .next
  - coverage
  - tmp

### File patterns to exclude
exclude_patterns:
  - "*.min.js"
  - "*.bundle.js"
  - "*.map"

## Multi-Repository Deployment

### Maximum repositories to scan
max_repositories: 50

### Parallel scans limit (to avoid rate limiting)
max_parallel_scans: 5

## Code Quality Checks

### Black configuration
black_max_line_length: 88

### Flake8 configuration
flake8_max_line_length: 100
flake8_exclude:
  - venv
  - node_modules
  - __pycache__
  - .git

## Issue Templates

### Workflow Failure Template
workflow_failure_template: |
  ## Workflow Failure Detected
  
  **Workflow:** {workflow_name}
  **Run ID:** {run_id}
  **Run URL:** {workflow_url}
  **Branch:** {branch}
  **Commit:** {commit}
  
  This issue was automatically created because the workflow failed.
  
  ### Next Steps
  1. Review the workflow logs at the link above
  2. Fix the identified issues
  3. Close this issue once resolved

### PR Comment Template
pr_comment_template: |
  **Created from PR Comment**
  
  PR: #{pr_number}
  Requested by: @{commenter}
  Comment: {comment_url}
  
  ---
  
  {body}

## Notification Settings (Future Enhancement)

### Slack webhook (not implemented yet)
# slack_webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL

### Discord webhook (not implemented yet)
# discord_webhook_url: https://discord.com/api/webhooks/YOUR/WEBHOOK

### Email notifications (not implemented yet)
# notify_email: team@example.com

## Custom Scanners (Future Enhancement)

### Security vulnerability scanning
# enable_security_scan: false

### Dependency updates
# enable_dependency_scan: false

### Documentation completeness
# enable_docs_scan: false

## API Rate Limiting

### Delay between API calls (milliseconds)
# api_call_delay: 100

### Max retries for failed API calls
# max_retries: 3

---

## How to Apply Configuration

1. **Edit workflow files:**
   - `.github/workflows/auto-issue-creator.yml`
   - `.github/scripts/scan_repository_errors.py`

2. **Modify schedule:**
   ```yaml
   schedule:
     - cron: '0 2 * * *'  # Change this line
   ```

3. **Change labels:**
   ```python
   labels=['workflow-failure', 'automated']  # Modify labels list
   ```

4. **Adjust thresholds:**
   ```python
   if len(todos) > 5:  # Change threshold value
   ```

5. **Commit and push changes:**
   ```bash
   git add .github/
   git commit -m "Update auto-issue-creator configuration"
   git push
   ```

## Environment Variables

The following environment variables are used:

- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- `GITHUB_REPOSITORY` - Automatically set by GitHub Actions
- `GITHUB_RUN_URL` - URL to the current workflow run

### Optional (for future enhancements):

- `SLACK_WEBHOOK_URL` - For Slack notifications
- `DISCORD_WEBHOOK_URL` - For Discord notifications
- `MAX_ISSUES_PER_RUN` - Limit issues created per scan

## Repository Secrets

Required secrets (automatically available):
- `GITHUB_TOKEN` - GitHub Actions token

Optional secrets for multi-repo deployment:
- `PERSONAL_ACCESS_TOKEN` - For accessing other repositories
- `GH_TOKEN_BOT` - Bot account token for creating issues

---

For more information, see:
- Quick Start Guide: `.github/workflows/QUICK_START_GUIDE.md`
- Full Documentation: `.github/workflows/AUTO_ISSUE_CREATOR_README.md`
