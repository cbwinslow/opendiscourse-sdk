# GitHub Automation Rules Documentation

This document describes all the automated workflows and rules configured for this repository.

## Table of Contents

1. [Code Review Automation](#code-review-automation)
2. [Issue Management](#issue-management)
3. [Pull Request Management](#pull-request-management)
4. [Security & Dependencies](#security--dependencies)
5. [Quality Checks](#quality-checks)
6. [Release Management](#release-management)
7. [Performance Monitoring](#performance-monitoring)

## Code Review Automation

### Auto-Assign (`.github/workflows/auto-assign.yml`)
- **Trigger**: Issues and PRs opened
- **Actions**: Automatically assigns issues and PRs based on file paths changed
- **Assignment Logic**:
  - `.github/` changes → repository owner
  - `web/` or `webui/` changes → frontend team
  - `.py` files → backend team
  - `docs/` changes → documentation team

### Auto-Review Bot (`.github/workflows/auto-review.yml`)
- **Trigger**: PR opened, synchronized, or reopened
- **Actions**:
  - Checks if tests are included with code changes
  - Checks if documentation is updated
  - Auto-approves documentation-only PRs
  - Flags dependency updates
  - Adds appropriate labels

### Review Reminder (`.github/workflows/review-reminder.yml`)
- **Trigger**: Scheduled (weekdays at 9 AM)
- **Actions**:
  - Reminds reviewers of pending PRs
  - Notifies when PRs have been waiting for >2 days
  - Alerts when changes have been made after review requests

### CODEOWNERS (`.github/CODEOWNERS`)
- **Purpose**: Automatic reviewer assignment based on file ownership
- **Owners**: Defined per directory and file type

## Issue Management

### Auto-Issue Creator (`.github/workflows/auto-issue-creator.yml`)
- **Triggers**: Workflow failures, PR comments with "gh create issue", scheduled scans
- **Actions**:
  - Creates issues for workflow failures
  - Creates issues from PR comments
  - Scans repository for outstanding errors
  - Detects code quality issues

### Auto-Issue Triage (`.github/workflows/auto-issue-triage.yml`)
- **Trigger**: CI workflow completion
- **Actions**: Creates issue when CI fails

### Duplicate Issue Detection (`.github/workflows/duplicate-issue-detection.yml`)
- **Trigger**: New issue opened
- **Actions**:
  - Scans for similar existing issues (>70% title similarity or >80% body similarity)
  - Comments with potential duplicates
  - Adds 'potential-duplicate' label

### First-Time Contributor Greeting (`.github/workflows/greet-first-time.yml`)
- **Trigger**: Issue or PR opened
- **Actions**:
  - Welcomes first-time contributors
  - Provides helpful information and guidelines
  - Adds 'first-time-contributor' label to PRs

### Project Board Automation (`.github/workflows/project-board-automation.yml`)
- **Trigger**: Issues/PRs opened, closed, labeled
- **Actions**:
  - Auto-adds items to project boards
  - Updates status labels based on state
  - Manages priority labels

### Stale Issues/PRs (`.github/workflows/stale.yml`)
- **Trigger**: Scheduled (daily)
- **Actions**: Marks inactive issues and PRs as stale

### Auto-Close Inactive PRs (`.github/workflows/auto-close-inactive.yml`)
- **Trigger**: Scheduled (weekly on Sunday)
- **Actions**:
  - Marks PRs as stale after 30 days of inactivity
  - Closes PRs after 60 days of inactivity
  - Skips PRs with 'keep-open' label

## Pull Request Management

### PR Labeler (`.github/workflows/pr-labeler.yml`)
- **Trigger**: PR opened, synchronized, or reopened
- **Actions**:
  - Labels PRs based on changed files (uses `.github/labeler.yml`)
  - Adds size labels (XS, S, M, L, XL) based on lines changed
  - Adds 'work-in-progress' label for draft PRs or WIP in title
  - Adds 'breaking-change' label when detected

### Labeler (`.github/workflows/label.yml`)
- **Trigger**: PR opened
- **Actions**: Applies labels based on file paths using `.github/labeler.yml` configuration

### Branch Protection Enforcement (`.github/workflows/branch-protection.yml`)
- **Trigger**: PR opened, synchronized, reopened, edited
- **Actions**:
  - Checks PR title format (conventional commits)
  - Ensures PR has meaningful description
  - Encourages linking related issues
  - Adds reminder labels

### Commit Message Linter (`.github/workflows/commit-lint.yml`)
- **Trigger**: PR opened, synchronized, reopened
- **Actions**:
  - Validates commit messages follow Conventional Commits spec
  - Comments with format guidance
  - Adds 'needs-better-commits' label if invalid

### PR Template (`.github/pull_request_template.md`)
- **Purpose**: Standard PR template with checklist
- **Sections**: Description, type, changes, testing, documentation, checklist

## Security & Dependencies

### Dependabot (`.github/dependabot.yml`)
- **Schedule**: Weekly on Mondays at 9 AM
- **Ecosystems**:
  - Python (pip)
  - npm (root and /web)
  - GitHub Actions
  - Docker
- **Actions**: Creates PRs for dependency updates

### Auto-Merge Dependabot (`.github/workflows/auto-merge-dependabot.yml`)
- **Trigger**: Dependabot PR opened/updated
- **Actions**:
  - Auto-merges patch and minor updates after CI passes
  - Comments on major updates for manual review

### Security Scanner (`.github/workflows/security-scanner.yml`)
- **Trigger**: Scheduled (daily at 2 AM), PR to main/develop
- **Actions**:
  - Runs safety and pip-audit for Python
  - Runs npm audit for JavaScript
  - Creates issues for discovered vulnerabilities
  - Uploads security reports as artifacts

### Auto-Update Dependencies (`.github/workflows/auto-update-deps.yml`)
- **Trigger**: Scheduled (weekly on Monday)
- **Actions**:
  - Updates Python dependencies with pip-compile
  - Updates npm dependencies with npm-check-updates
  - Creates PRs for updates

### CodeQL (`.github/workflows/codeql.yml`)
- **Trigger**: Push, PR, scheduled
- **Actions**: Advanced code scanning for security vulnerabilities

## Quality Checks

### Comprehensive CI (`.github/workflows/comprehensive-ci.yml`)
- **Trigger**: Push to main/develop, PRs
- **Jobs**:
  - Python tests with coverage
  - Frontend tests
  - API tests
  - Security scans
  - Markdown linting
  - Docker build tests

### CI (`.github/workflows/ci.yml`)
- **Trigger**: Push, PR
- **Actions**: Runs basic lint and test suite

### Documentation CI (`.github/workflows/documentation-ci.yml`)
- **Trigger**: Changes to documentation
- **Actions**: Validates documentation builds correctly

## Release Management

### Release Automation (`.github/workflows/release-automation.yml`)
- **Trigger**: Version tags pushed (v*.*.*)
- **Actions**:
  - Auto-generates changelog from commits
  - Categorizes changes (features, fixes, breaking, chores)
  - Creates GitHub release
  - Marks pre-releases (alpha, beta, rc)

## Performance Monitoring

### Performance Monitoring (`.github/workflows/performance-monitoring.yml`)
- **Trigger**: PR opened/synchronized, push to main/develop
- **Actions**:
  - Checks frontend bundle size
  - Profiles Python import times
  - Comments on PRs with performance metrics
  - Flags slow imports (>100ms)

## Issue Templates

### Bug Report (`.github/ISSUE_TEMPLATE/bug_report.md`)
Standard bug report template with environment details

### Feature Request (`.github/ISSUE_TEMPLATE/feature_request.md`)
Standard feature request template

### Security Vulnerability (`.github/ISSUE_TEMPLATE/security_vulnerability.md`)
Security issue template with severity levels

### Performance Issue (`.github/ISSUE_TEMPLATE/performance_issue.md`)
Performance problem template with metrics

### Custom Template (`.github/ISSUE_TEMPLATE/custom.md`)
Blank template for other issues

## Configuration Files

### Labeler Configuration (`.github/labeler.yml`)
Defines path-based label mappings for PRs:
- `ingestion` - opendiscourse/ingestion/**
- `documentation` - *.md, docs/**
- `tests` - tests/**
- `database` - *.sql, src/database/**
- `scripts` - scripts/**
- `dependencies` - requirements/**, pyproject.toml, setup.py
- `github-actions` - .github/**

## Best Practices

### For Contributors

1. **Write Good Commit Messages**: Follow Conventional Commits format
2. **Link Issues**: Use "Closes #123" in PR descriptions
3. **Add Tests**: Include tests with code changes
4. **Update Docs**: Keep documentation current
5. **Small PRs**: Break large changes into smaller PRs
6. **Respond to Automation**: Address bot comments and suggestions

### For Maintainers

1. **Review Bot Comments**: Bot insights can help with review
2. **Use Labels**: Labels help track and organize work
3. **Keep Dependencies Updated**: Regularly review Dependabot PRs
4. **Monitor Security**: Address security issues promptly
5. **Maintain Templates**: Keep issue/PR templates up to date

## Troubleshooting

### Workflow Failures

If a workflow fails:
1. Check the Actions tab for error details
2. Review the auto-created issue (if one was created)
3. Fix the underlying problem
4. Re-run the workflow if needed

### False Positives

If automation creates incorrect labels or comments:
1. Manually remove/correct the label
2. Consider adjusting the workflow configuration
3. Report persistent issues to maintainers

### Disabling Automation

To temporarily disable automation on a PR:
- Add the `skip-automation` label (if needed, create this label)
- For keeping PRs open indefinitely, add `keep-open` label

## Contributing to Automation

To improve or add automation:
1. Propose changes in an issue first
2. Test workflows thoroughly
3. Document any new automation
4. Update this document with changes
5. Consider backward compatibility

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot)
- [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
