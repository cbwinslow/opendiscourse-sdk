# Auto Issue Creator - Visual Examples

## How It Works: Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTO ISSUE CREATOR                        │
│                                                               │
│  Automatically creates GitHub issues from multiple sources   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │      TRIGGER EVENTS                  │
        └──────────────────────────────────────┘
                      │
         ┌────────────┼────────────┬────────────┬──────────────┐
         │            │            │            │              │
         ▼            ▼            ▼            ▼              ▼
    ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    ┌──────────┐
    │Workflow│  │   PR   │  │ Daily  │  │  Pull  │    │  Manual  │
    │Failure │  │Comment │  │Schedule│  │Request │    │  Trigger │
    └────────┘  └────────┘  └────────┘  └────────┘    └──────────┘
         │            │            │            │              │
         └────────────┴────────────┴────────────┴──────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │     SCANNING & DETECTION             │
        └──────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Scan    │         │ Check   │         │ Analyze │
    │ Code    │         │Workflows│         │  Docs   │
    └─────────┘         └─────────┘         └─────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │    ISSUE CREATION                    │
        └──────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Create  │         │  Add    │         │ Notify  │
    │ Issues  │         │ Labels  │         │  Team   │
    └─────────┘         └─────────┘         └─────────┘
```

## Example 1: Workflow Failure Detection

### Scenario
A CI workflow fails on the main branch.

### Flow
```
1. GitHub Workflow "CI" runs
   └─> ❌ FAILS at step "Run Tests"

2. Auto Issue Creator detects failure
   └─> Workflow: workflow_failure_issues
   └─> Trigger: workflow_run.conclusion == 'failure'

3. Issue Created Automatically
   └─> Title: "🚨 Workflow Failure: CI"
   └─> Labels: workflow-failure, automated
   └─> Body contains:
       • Workflow name
       • Run ID and URL
       • Branch and commit
       • Next steps
```

### Result
![Workflow Failure Issue](example-workflow-failure.png)

```markdown
Title: 🚨 Workflow Failure: CI

## Workflow Failure Detected

**Workflow:** CI
**Run ID:** 1234567890
**Run URL:** https://github.com/cbwinslow/opendiscourse/actions/runs/1234567890
**Branch:** main
**Commit:** abc123def456

This issue was automatically created because the workflow failed.

### Next Steps
1. Review the workflow logs at the link above
2. Fix the identified issues
3. Close this issue once resolved

---
Labels: workflow-failure, automated
```

---

## Example 2: PR Comment Issue Creation

### Scenario
Developer finds a bug while reviewing a PR and wants to create an issue.

### Flow
```
1. Developer adds comment in PR #42:
   "gh create issue Fix memory leak in data processor
   
   The data processor is not releasing memory properly after
   processing large datasets. This causes the application to
   crash after processing ~1000 documents.
   
   Steps to reproduce:
   1. Process 1000+ documents
   2. Monitor memory usage
   3. Observe increasing memory consumption"

2. Auto Issue Creator detects comment
   └─> Workflow: pr_comment_issues
   └─> Trigger: comment contains "gh create issue"

3. Issue Created Automatically
   └─> Title: "Fix memory leak in data processor"
   └─> Labels: from-pr-comment, automated
   └─> Links to PR and comment

4. Confirmation comment added to PR
   └─> "✅ Issue created: #123"
```

### Result

**Original PR Comment:**
```
👤 @developer
gh create issue Fix memory leak in data processor

The data processor is not releasing memory properly after
processing large datasets. This causes the application to
crash after processing ~1000 documents.

Steps to reproduce:
1. Process 1000+ documents
2. Monitor memory usage
3. Observe increasing memory consumption
```

**Created Issue #123:**
```markdown
Title: Fix memory leak in data processor

**Created from PR Comment**

PR: #42
Requested by: @developer
Comment: https://github.com/.../pull/42#issuecomment-...

---

The data processor is not releasing memory properly after
processing large datasets. This causes the application to
crash after processing ~1000 documents.

Steps to reproduce:
1. Process 1000+ documents
2. Monitor memory usage
3. Observe increasing memory consumption

---
Labels: from-pr-comment, automated
```

**PR Comment Response:**
```
🤖 Auto Issue Creator Bot
✅ Issue created: #123
```

---

## Example 3: Daily Repository Scan

### Scenario
Daily automated scan finds multiple issues in the codebase.

### Flow
```
1. Scheduled trigger (Daily at 2 AM UTC)
   └─> Workflow: scan_repository_errors

2. Scanner runs multiple checks:
   ├─> Scan TODO/FIXME comments (found 23)
   ├─> Scan PRODUCTION.md issues (found 12)
   ├─> Scan failed workflows (found 3)
   └─> Scan failing PRs (found 2)

3. Issues created based on thresholds:
   ├─> TODO Comments (23 > 5) ✓ Create Issue #124
   ├─> Production Issues (12) ✓ Create Issue #125
   ├─> Failed Workflows (3) ✓ Create Issue #126
   └─> Failing PRs (2) ✓ Create Issue #127

4. Scanner output:
   ✅ Scan complete!
      - TODO/FIXME comments: 23
      - Production issues: 12
      - Failed workflows: 3
      - Failing PRs: 2
```

### Result: Multiple Issues Created

**Issue #124: TODO/FIXME Comments**
```markdown
Title: 📝 TODO/FIXME Comments Found - 2025-01-15

## Code Comments Requiring Attention

Found 23 TODO/FIXME comments in the codebase.

### TODO Comments (15)
- `opendiscourse/api/routes.py:45` - Add authentication middleware
- `webui/pages/index.tsx:102` - Implement loading state
- `tests/test_api.py:67` - Add more edge case tests
...

### FIXME Comments (8)
- `opendiscourse/db/models.py:23` - Fix race condition
- `scripts/data_import.py:156` - Handle duplicate entries
...

---
Labels: code-cleanup, automated, maintenance
```

**Issue #125: Production Readiness**
```markdown
Title: 🚀 Production Readiness Issues - 2025-01-15

## Outstanding Production Readiness Items

Found 12 items in PRODUCTION.md that need attention:

### Fix all failing tests
- Resolve API key configuration issues
- Fix import errors in entity utils tests
- Complete test suite implementation

### Implement comprehensive security measures
- Configure API key management
- Implement authentication/authorization
...

---
Labels: production-readiness, automated, high-priority
```

---

## Example 4: Code Quality Detection

### Scenario
A pull request is opened with formatting issues.

### Flow
```
1. PR #43 opened or updated
   └─> Workflow: code_quality_issues

2. Code quality checks run:
   ├─> Black formatter check
   │   └─> ❌ FAILED: 5 files need formatting
   └─> Flake8 linter check
       └─> ❌ FAILED: 12 linting issues

3. Issues created (if no recent similar issues):
   ├─> Black Formatting Issue #128
   └─> Flake8 Linting Issue #129
```

### Result

**Issue #128: Formatting**
```markdown
Title: 🎨 Code Formatting Issues Detected - 2025-01-15

## Black Formatting Issues

The following files need to be formatted with Black:

```
would reformat opendiscourse/api/routes.py
would reformat webui/pages/index.tsx
would reformat tests/test_entity_utils.py
would reformat scripts/data_import.py
would reformat github_sync_setup.py

5 files would be reformatted
```

**To fix:** Run `black .` in the repository root.

This issue was automatically created by the code quality scanner.

---
Labels: code-quality, formatting, automated
```

---

## Timeline Example: A Week in Auto Issue Creator

```
Monday 2:00 AM
├─> Daily scan runs
├─> Creates issue #130: TODO Comments Found (23 items)
└─> Creates issue #131: Production Readiness (12 items)

Monday 10:23 AM
├─> PR #44 opened
├─> Code quality check runs
└─> Creates issue #132: Formatting Issues (3 files)

Tuesday 3:45 PM
├─> Workflow "CI" fails
└─> Creates issue #133: Workflow Failure: CI

Wednesday 9:10 AM
├─> Developer comments on PR #44: "gh create issue Add rate limiting"
└─> Creates issue #134: Add rate limiting

Thursday 2:00 AM
├─> Daily scan runs
├─> Skips TODO issue (recent one exists)
└─> Updates issue #131 with comment (new production item found)

Friday 4:30 PM
├─> PR #45 opened
├─> All checks pass ✓
└─> No issues created (everything looks good!)

Saturday 2:00 AM
├─> Daily scan runs
└─> All thresholds normal, no new issues
```

---

## Issue Dashboard View

After one week, your Issues tab might look like:

```
🔴 #133 - 🚨 Workflow Failure: CI                      [workflow-failure] [automated]
🟡 #134 - Add rate limiting                            [from-pr-comment] [automated]
🟡 #132 - 🎨 Code Formatting Issues Detected           [code-quality] [automated]
🟢 #131 - 🚀 Production Readiness Issues (✓ updated)   [production-readiness] [automated]
🟡 #130 - 📝 TODO/FIXME Comments Found                 [code-cleanup] [automated]
```

Legend:
- 🔴 High priority (workflow failures, production issues)
- 🟡 Medium priority (code quality, TODOs)
- 🟢 Low priority (maintenance)

---

## Multi-Repository Deployment Example

### Scenario
Deploy scanner to top 50 repositories.

### Flow
```
1. Manual trigger: Deploy to Top Repos
   └─> With dry_run: true (test mode)

2. Scanner fetches repositories:
   ├─> Your personal repos (sorted by stars)
   ├─> Organization repos (sorted by stars)
   └─> Total: 50 repositories

3. For each repository (parallel, max 5):
   ├─> Check if scanner script exists
   ├─> Run scanner (dry run)
   └─> Report what would be created

4. Review results, then re-run with dry_run: false

5. Issues created across all 50 repositories
   └─> Summary report generated
```

### Result Summary
```
## Multi-Repository Scan Complete 🎉

Scanned 50 repositories

### Issues Created:
- 🚨 Workflow failures: 12 issues across 8 repos
- 📝 TODO comments: 23 issues across 18 repos
- 🚀 Production items: 15 issues across 12 repos
- 🎨 Code quality: 18 issues across 15 repos

### Repositories with Most Issues:
1. repo-alpha: 8 issues
2. repo-beta: 6 issues
3. repo-gamma: 5 issues

### Next Steps:
1. Review created issues
2. Prioritize by label and repository
3. Address high-priority items first
```

---

## Command Cheat Sheet

### PR Comment Commands
```bash
# Basic issue creation
gh create issue Issue title here
Additional details...

# With detailed description
gh create issue Fix authentication bug
The login system has a security vulnerability that needs immediate attention.

Steps to reproduce:
1. Navigate to /login
2. Enter invalid credentials
3. System grants access anyway

Expected: Access denied
Actual: Access granted
```

### Manual Workflow Triggers
```bash
# From GitHub UI:
Actions → Auto Issue Creator → Run workflow

# From CLI (gh):
gh workflow run auto-issue-creator.yml

# From CLI with dry run:
gh workflow run deploy-multi-repo-scanner.yml -f dry_run=true
```

### Quick Fixes
```bash
# Fix formatting issues
black .

# Fix linting issues
flake8 . --fix

# Run tests
pytest

# Check workflows
gh run list --workflow=auto-issue-creator.yml
```

---

## Summary

The Auto Issue Creator:
- ✅ **Monitors** your repository 24/7
- ✅ **Detects** issues automatically
- ✅ **Creates** organized issues with proper labels
- ✅ **Prevents** duplicates intelligently
- ✅ **Scales** to multiple repositories
- ✅ **Saves** your team time

Get started in minutes, customize as needed, and let automation handle the busywork!
