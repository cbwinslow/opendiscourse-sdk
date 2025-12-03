# Quick Start Guide: Auto Issue Creator

## What This Does

The Auto Issue Creator automatically monitors your repository and creates GitHub issues for:

1. ❌ **Workflow Failures** - When CI/CD fails
2. 💬 **PR Comments** - When someone types `gh create issue` in a comment
3. 📝 **TODO Comments** - Outstanding TODO/FIXME in your code
4. 🚀 **Production Issues** - Items from PRODUCTION.md checklist
5. 🔍 **Code Quality** - Formatting and linting issues

## Getting Started

### For This Repository (OpenDiscourse)

The action is already installed and will run automatically:

✅ **Automatically on workflow failures**
✅ **Daily at 2 AM UTC** (full repository scan)
✅ **On PR comments** with `gh create issue`
✅ **On pull request updates** (code quality checks)

No setup needed - it's working now!

### Using PR Comments to Create Issues

In any pull request, add a comment like this:

```
gh create issue Fix the authentication bug

The authentication system is not properly validating tokens in the
/api/auth endpoint. This needs to be addressed before the next release.

Steps to reproduce:
1. Make a request to /api/auth with an invalid token
2. System accepts it instead of rejecting
```

An issue will be automatically created with:
- Title: "Fix the authentication bug"
- Body: Your full comment
- Link back to the PR
- Labels: `from-pr-comment`, `automated`

You'll get a confirmation comment in the PR.

### Manual Scan

Want to scan immediately? 

1. Go to: **Actions** → **Auto Issue Creator**
2. Click **Run workflow**
3. Select the branch
4. Click **Run workflow**

Results appear in 1-2 minutes.

## Installing in Other Repositories

### Option 1: Copy Files (Single Repo)

```bash
# In your target repository
mkdir -p .github/workflows .github/scripts

# Copy the workflow file
curl -o .github/workflows/auto-issue-creator.yml \
  https://raw.githubusercontent.com/cbwinslow/opendiscourse/main/.github/workflows/auto-issue-creator.yml

# Copy the scanner script
curl -o .github/scripts/scan_repository_errors.py \
  https://raw.githubusercontent.com/cbwinslow/opendiscourse/main/.github/scripts/scan_repository_errors.py

chmod +x .github/scripts/scan_repository_errors.py

# Commit and push
git add .github/
git commit -m "Add auto issue creator"
git push
```

### Option 2: Deploy to Multiple Repos

Use the included `deploy-multi-repo-scanner.yml` workflow:

1. **In OpenDiscourse repository:**
   - Go to **Actions** → **Deploy Auto Issue Creator to Top Repos**
   - Click **Run workflow**
   - Choose **dry_run: true** first (to test)
   - Review the output
   - Run again with **dry_run: false** to actually create issues

2. **This will scan your top 50 repositories** based on:
   - Your personal repositories (by stars)
   - Organization repositories you have access to

## Examples

### Example 1: Workflow Failure Issue

When a CI workflow fails, you'll get:

```
🚨 Workflow Failure: CI

Workflow: CI
Run ID: 123456789
Run URL: https://github.com/user/repo/actions/runs/123456789
Branch: main
Commit: abc123def

This issue was automatically created because the workflow failed.

Next Steps
1. Review the workflow logs at the link above
2. Fix the identified issues
3. Close this issue once resolved
```

Labels: `workflow-failure`, `automated`

### Example 2: Code Quality Issue

From Black formatter:

```
🎨 Code Formatting Issues Detected - 2025-01-15

The following files need to be formatted with Black:

Would reformat opendiscourse/api/routes.py
Would reformat tests/test_entity_utils.py
...

To fix: Run `black .` in the repository root.

This issue was automatically created by the code quality scanner.
```

Labels: `code-quality`, `formatting`, `automated`

### Example 3: TODO Comments Found

```
📝 TODO/FIXME Comments Found - 2025-01-15

Found 23 TODO/FIXME comments in the codebase.

TODO Comments (15)
- `opendiscourse/api/routes.py:45` - Add authentication
- `webui/pages/index.tsx:102` - Implement loading state
...

FIXME Comments (8)
- `tests/test_api.py:23` - Fix flaky test
...

This issue was automatically created by the repository scanner.
```

Labels: `code-cleanup`, `automated`, `maintenance`

## Configuration

### Adjusting Scan Frequency

Edit `.github/workflows/auto-issue-creator.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM UTC
  # Change to:
  - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  # Or:
  - cron: '0 14 * * 1-5'  # Weekdays at 2 PM
```

### Disabling Specific Features

Comment out jobs you don't want:

```yaml
jobs:
  # workflow_failure_issues:
  #   ... (disabled)
  
  pr_comment_issues:
    ... (enabled)
```

### Customizing Labels

In the workflow file, change label names:

```python
labels=['workflow-failure', 'automated']
# Change to:
labels=['ci-error', 'bot', 'high-priority']
```

### Preventing Too Many Issues

The scanner includes duplicate prevention:
- Checks for similar open issues
- Only creates if no similar issue exists in last 3 open issues
- Update frequency: Daily for scans, immediate for failures

To adjust, edit `.github/scripts/scan_repository_errors.py`:

```python
# Line ~238
if any('TODO/FIXME Comments' in i.title for i in existing[:3]):
# Change [:3] to [:5] to check more issues
```

## Troubleshooting

### "Action didn't run"

**Check:** Repository Settings → Actions → General
- Ensure "Allow all actions" is enabled
- Verify "Read and write permissions" for workflows

### "Issues not created"

**Check:** Repository Settings → Actions → General → Workflow permissions
- Select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

### "Too many issues created"

Adjust the frequency or add filters:

```python
# In scan_repository_errors.py, limit results:
if len(todos) > 10:  # Change threshold
    self._create_todo_issue(todos[:20])  # Limit to top 20
```

### "Rate limiting errors"

GitHub has API rate limits:
- **Workflow runs:** 1,000 per hour per repository
- **API calls:** 5,000 per hour (authenticated)

For large repos:
- Reduce scan frequency
- Limit items scanned
- Use GitHub App for higher limits

## Advanced Usage

### Custom Issue Templates

Modify issue creation in scanner script:

```python
def _create_todo_issue(self, todos: List[Dict[str, Any]]):
    title = f"📝 TODO Comments - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Add custom sections
    body = f"""## Custom Section
    
    Add your custom content here...
    
    """
```

### Webhook Integration

For real-time notifications, add webhook:

```python
# In scan_repository_errors.py
import requests

def notify_webhook(issue):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json={
            'text': f'New issue created: {issue.title}'
        })
```

Then add webhook URL to repository secrets.

### Custom Scanners

Add your own scanning logic:

```python
def scan_security_vulnerabilities(self) -> List[Dict[str, Any]]:
    """Scan for security issues."""
    vulnerabilities = []
    # Add your scanning logic
    return vulnerabilities

# In create_summary_issues():
security_issues = self.scan_security_vulnerabilities()
if security_issues:
    self._create_security_issues(security_issues)
```

## Best Practices

1. **Start with dry run** - Test before deploying to multiple repos
2. **Review regularly** - Check created issues weekly
3. **Close resolved issues** - Keep your issue tracker clean
4. **Customize labels** - Match your project's labeling scheme
5. **Adjust thresholds** - Fine-tune based on your project size
6. **Add team members** - Assign issues to appropriate people

## Getting Help

- 📖 Full documentation: `.github/workflows/AUTO_ISSUE_CREATOR_README.md`
- 🐛 Found a bug? Open an issue with label `auto-issue-creator`
- 💡 Want a feature? Comment on existing issues or create new one
- 📧 Questions? Tag maintainers in an issue

## What's Next?

1. ✅ **Review created issues** - Check what the scanner found
2. 🔧 **Customize settings** - Adjust to your needs
3. 🚀 **Deploy to other repos** - Use multi-repo deployment
4. 📊 **Monitor results** - Track issue trends over time
5. 🎯 **Close issues** - As you fix problems

Happy automating! 🤖
