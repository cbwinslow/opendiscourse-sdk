# Automated Issue Creator - Implementation Summary

## Overview

This implementation provides a comprehensive GitHub Actions workflow system that automatically creates issues from multiple sources across your repositories.

## What Was Created

### 1. Main Workflow: `auto-issue-creator.yml`
**Location:** `.github/workflows/auto-issue-creator.yml`

**Features:**
- ✅ Detects workflow failures and creates issues automatically
- ✅ Monitors PR comments for `gh create issue` commands
- ✅ Runs daily repository scans for outstanding issues
- ✅ Checks code quality (Black formatting, Flake8 linting)

**Triggers:**
- Workflow failures (automatic)
- PR comments with `gh create issue` (automatic)
- Daily at 2 AM UTC (scheduled)
- Pull request updates (automatic)
- Manual trigger (via Actions UI)

### 2. Repository Scanner: `scan_repository_errors.py`
**Location:** `.github/scripts/scan_repository_errors.py`

**Scans for:**
- TODO/FIXME/HACK/XXX/BUG comments in code
- Outstanding items in PRODUCTION.md
- Failed workflow runs (last 7 days)
- Open PRs with failing checks

**Smart Features:**
- Duplicate prevention (checks for similar open issues)
- Configurable thresholds
- Detailed issue descriptions with file locations and line numbers
- Automatic labeling

### 3. Multi-Repository Deployment: `deploy-multi-repo-scanner.yml`
**Location:** `.github/workflows/deploy-multi-repo-scanner.yml`

**Capabilities:**
- Scans top 50 repositories (by stars)
- Works across personal and organization repos
- Dry-run mode for testing
- Parallel processing with rate limiting
- Comprehensive summary reporting

## Documentation Files

1. **AUTO_ISSUE_CREATOR_README.md** - Full technical documentation
2. **QUICK_START_GUIDE.md** - Getting started and examples
3. **CONFIG.md** - Configuration options and customization
4. **VISUAL_EXAMPLES.md** - Visual flows and use case examples

## Quick Start

### For This Repository
Already active! The workflow will:
- Monitor for failures automatically
- Scan daily at 2 AM UTC
- Respond to `gh create issue` in PR comments

### Create an Issue from a PR Comment
In any PR, comment:
```
gh create issue Add feature X
Detailed description of what needs to be done...
```

### Manual Scan
1. Go to **Actions** → **Auto Issue Creator**
2. Click **Run workflow**
3. Wait 1-2 minutes for results

### Deploy to Other Repositories
```bash
# Copy to another repo
curl -o .github/workflows/auto-issue-creator.yml \
  https://raw.githubusercontent.com/cbwinslow/opendiscourse/main/.github/workflows/auto-issue-creator.yml

curl -o .github/scripts/scan_repository_errors.py \
  https://raw.githubusercontent.com/cbwinslow/opendiscourse/main/.github/scripts/scan_repository_errors.py

chmod +x .github/scripts/scan_repository_errors.py
```

### Deploy to Top 50 Repositories
1. Go to **Actions** → **Deploy Auto Issue Creator to Top Repos**
2. Select **dry_run: true** (test first)
3. Review output
4. Run again with **dry_run: false**

## Issue Types Created

| Type | Label | Trigger | Frequency |
|------|-------|---------|-----------|
| Workflow Failures | `workflow-failure`, `automated` | On failure | Immediate |
| PR Comments | `from-pr-comment`, `automated` | On comment | Immediate |
| TODO Comments | `code-cleanup`, `automated` | Daily scan | Daily |
| Production Items | `production-readiness`, `automated` | Daily scan | Daily |
| Code Quality | `code-quality`, `automated` | On PR | Per PR |
| Failed Workflows Summary | `ci-failures`, `automated` | Daily scan | Daily |
| Failing PRs Summary | `pr-failures`, `automated` | Daily scan | Daily |

## Example Workflow

```
Day 1: Install action
├─> Runs daily scan
├─> Finds 23 TODO comments → Creates issue #1
├─> Finds 12 production items → Creates issue #2
└─> Summary: 2 issues created

Day 2: Developer uses it
├─> CI fails → Creates issue #3 automatically
├─> Developer comments "gh create issue" → Creates issue #4
└─> Daily scan runs → No duplicates created

Day 3: Clean up
├─> Team fixes issues #1 and #3
├─> Closes issues
└─> Daily scan finds fewer TODOs (20 vs 23)
```

## Configuration

All configurable via workflow file edits:

```yaml
# Adjust scan frequency
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM

# Change thresholds (in Python script)
if len(todos) > 5:  # Minimum TODOs before creating issue
  self._create_todo_issue(todos[:50])  # Max to include
```

## Architecture

```
┌──────────────────────────────────────────────────┐
│              GitHub Events                       │
│  (workflow_run, issue_comment, schedule, etc)   │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│         Auto Issue Creator Workflow              │
│  (.github/workflows/auto-issue-creator.yml)     │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌──────────────────┐
│  Python Script  │  │  Inline Python   │
│  (scanner)      │  │  (in workflow)   │
└────────┬────────┘  └────────┬─────────┘
         │                    │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────┐
         │ GitHub Issues  │
         │    Created     │
         └────────────────┘
```

## Security & Permissions

The workflow requires:
- `contents: read` - Read repository files
- `issues: write` - Create issues
- `pull-requests: write` - Comment on PRs

Uses `GITHUB_TOKEN` which is automatically provided by GitHub Actions.

## Best Practices

1. ✅ **Start with dry-run** when deploying to multiple repos
2. ✅ **Review created issues** weekly
3. ✅ **Customize labels** to match your workflow
4. ✅ **Adjust thresholds** based on repo size
5. ✅ **Close resolved issues** to keep tracker clean

## Limitations & Considerations

### Rate Limiting
- GitHub API: 5,000 requests/hour (authenticated)
- Workflow runs: 1,000/hour per repository
- Multi-repo deployment: Limited to 5 parallel scans

### Duplicate Prevention
- Checks last 3 open issues for similar titles
- Updates existing issues when appropriate
- Prevents spam from recurring issues

### File Size Limits
- Issue body limited to reasonable size
- Long reports truncated with "..." indicator
- Full details available in workflow logs

## Troubleshooting

### Issues Not Created
**Check:** Repository Settings → Actions → Workflow permissions
- Enable "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

### Too Many Issues
**Solution:** Adjust thresholds in `scan_repository_errors.py`:
```python
if len(todos) > 10:  # Increase from 5 to 10
```

### Rate Limiting
**Solution:** 
- Reduce scan frequency
- Limit items per issue
- Use GitHub App for higher limits

## Future Enhancements

Potential additions:
- [ ] Slack/Discord notifications
- [ ] Custom webhook support
- [ ] Security vulnerability scanning
- [ ] Dependency update detection
- [ ] Documentation completeness checks
- [ ] Automatic issue assignment
- [ ] Priority scoring algorithm
- [ ] Integration with project boards

## Testing

The implementation includes:
- ✅ YAML syntax validation
- ✅ Python script syntax validation
- ✅ Pattern matching tests
- ✅ Markdown parsing tests

All tests passed before commit.

## Files Overview

```
.github/
├── workflows/
│   ├── auto-issue-creator.yml              # Main workflow (293 lines)
│   ├── deploy-multi-repo-scanner.yml       # Multi-repo deployment (169 lines)
│   ├── AUTO_ISSUE_CREATOR_README.md        # Full documentation (191 lines)
│   ├── QUICK_START_GUIDE.md                # Getting started (330 lines)
│   ├── CONFIG.md                           # Configuration guide (258 lines)
│   └── VISUAL_EXAMPLES.md                  # Visual examples (487 lines)
└── scripts/
    └── scan_repository_errors.py           # Scanner script (367 lines)
```

**Total:** ~2,095 lines of code and documentation

## Support

- 📖 **Documentation:** See files in `.github/workflows/`
- 🐛 **Issues:** Create issue with label `auto-issue-creator`
- 💡 **Features:** Open issue with enhancement request
- 📧 **Help:** Tag maintainers in issue

## License

Part of the OpenDiscourse project. Same license applies.

## Credits

Created as an automated solution for managing repository health and tracking outstanding work across projects.

---

**Status:** ✅ Ready to use
**Version:** 1.0.0
**Last Updated:** 2025-01-15

For detailed usage instructions, see **QUICK_START_GUIDE.md**.
