# Automated Issue Creator

This GitHub Action automatically creates issues for various types of problems found in the repository.

## Features

### 1. Workflow Failure Detection
Automatically creates issues when GitHub Actions workflows fail:
- Monitors all workflow runs
- Creates issues with links to failed runs
- Updates existing issues if similar failures occur
- Labels: `workflow-failure`, `automated`

### 2. PR Comment Issue Creation
Allows creating issues directly from pull request comments:
- **Trigger**: Comment `gh create issue` in any PR comment
- Extracts title and body from the comment
- Links back to the original PR and comment
- Labels: `from-pr-comment`, `automated`

**Example Usage:**
```
gh create issue Fix the authentication bug
The authentication system is not properly validating tokens.
This needs to be addressed before the next release.
```

### 3. Repository Error Scanner
Runs daily to scan the repository for outstanding issues:
- **TODO/FIXME comments** in code
- **Production readiness items** from PRODUCTION.md
- **Recent failed workflows** (last 7 days)
- **Open PRs with failing checks**
- Labels: Various based on issue type

### 4. Code Quality Issues
Runs on pull requests and scheduled scans:
- **Black formatting issues**
- **Flake8 linting issues**
- Creates issues only if similar ones don't exist
- Labels: `code-quality`, `formatting`, `linting`, `automated`

## Triggers

The action runs on:
- **Workflow failures**: Automatically when any workflow fails
- **PR comments**: When someone comments with `gh create issue`
- **Pull requests**: When PRs are opened or updated (for code quality)
- **Daily schedule**: At 2 AM UTC (for repository scan)
- **Manual trigger**: Can be run manually from Actions tab

## Configuration

### Required Permissions
The workflow requires:
- `contents: read` - To checkout the repository
- `issues: write` - To create issues
- `pull-requests: write` - To comment on PRs

### GitHub Token
Uses the default `GITHUB_TOKEN` secret, which is automatically available in all workflows.

## Created Issue Labels

The action uses the following labels (will be created automatically):
- `workflow-failure` - For workflow run failures
- `from-pr-comment` - For issues created from PR comments
- `code-quality` - For code quality issues
- `formatting` - For Black formatting issues
- `linting` - For Flake8 linting issues
- `code-cleanup` - For TODO/FIXME comments
- `production-readiness` - For production checklist items
- `ci-failures` - For CI/CD failures
- `pr-failures` - For PRs with failing checks
- `automated` - Applied to all automatically created issues
- `maintenance` - For maintenance tasks
- `high-priority` - For critical production issues

## Duplicate Prevention

The action includes logic to prevent duplicate issues:
- Checks for similar open issues before creating new ones
- Updates existing issues with new information when appropriate
- Limits issue creation frequency for recurring problems

## Disabling the Action

To disable specific features:
1. Edit `.github/workflows/auto-issue-creator.yml`
2. Comment out or remove the unwanted job(s)
3. Commit the changes

To disable entirely:
- Delete the workflow file or
- Rename it to not end in `.yml`

## Testing

### Test Workflow Failures
Create a failing workflow and verify an issue is created.

### Test PR Comments
1. Create a test PR
2. Add a comment with `gh create issue Test Issue Title`
3. Verify the issue is created

### Test Manual Scan
1. Go to Actions tab
2. Select "Auto Issue Creator" workflow
3. Click "Run workflow"
4. Check for created issues

## Extending to Multiple Repositories

To use this action across the top 50 repositories:

1. **GitHub App Approach** (Recommended):
   - Create a GitHub App with issue write permissions
   - Install on target repositories
   - Use app credentials in workflow

2. **Organization Workflow**:
   - Store workflow in `.github` repository
   - Reuse across organization repositories

3. **Manual Installation**:
   - Copy workflow file to each repository
   - Adjust `GITHUB_REPOSITORY` variable if needed

## Example Workflow for Multiple Repos

```yaml
name: Multi-Repo Issue Creator

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  scan-repos:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        repo:
          - cbwinslow/opendiscourse
          - org/repo2
          - org/repo3
          # ... add up to 50 repos
    steps:
      - uses: actions/checkout@v4
        with:
          repository: ${{ matrix.repo }}
          
      - name: Run scanner
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ matrix.repo }}
        run: |
          python3 .github/scripts/scan_repository_errors.py
```

## Troubleshooting

### Issues not being created
- Check workflow permissions in repository settings
- Verify `GITHUB_TOKEN` has required permissions
- Check workflow logs for errors

### Too many issues created
- Adjust duplicate detection logic
- Increase time windows for checking similar issues
- Add more filters in the scanner script

### Rate limiting
- GitHub API has rate limits
- For large repositories, consider:
  - Reducing scan frequency
  - Limiting number of items scanned
  - Using GitHub App for higher limits

## Support

For issues or questions:
1. Check workflow logs in Actions tab
2. Review created issues for patterns
3. Open an issue in the repository

## License

This action is part of the OpenDiscourse project and follows the same license.
