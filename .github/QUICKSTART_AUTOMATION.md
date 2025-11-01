# Quick Start Guide: Repository Automation

This guide helps you quickly understand and use the automation features in this repository.

## For Contributors

### Opening a Pull Request

1. **Use Conventional Commits** for your commit messages:
   ```
   feat: add new search feature
   fix: resolve pagination bug
   docs: update README
   ```

2. **Fill out the PR template** - it will appear automatically

3. **Link related issues** using:
   - `Closes #123`
   - `Fixes #456`
   - `Resolves #789`

4. **Expect automation to**:
   - Add labels based on files changed
   - Add size labels (XS, S, M, L, XL)
   - Assign reviewers based on CODEOWNERS
   - Check if tests are included
   - Validate commit messages
   - Remind you about documentation

### Opening an Issue

1. **Choose the right template**:
   - Bug Report
   - Feature Request
   - Security Vulnerability
   - Performance Issue
   - Custom

2. **Fill out all sections** completely

3. **Expect automation to**:
   - Check for duplicate issues
   - Assign to appropriate team members
   - Add relevant labels
   - Greet first-time contributors

## For Maintainers

### Reviewing PRs

- **Auto-assigned PRs** will appear in your notifications based on CODEOWNERS
- **Review reminders** sent weekdays at 9 AM for pending PRs
- **Auto-approved** documentation-only PRs can be merged quickly
- **Dependabot PRs** will auto-merge for patch/minor updates after CI passes

### Managing Issues

- **Duplicate detection** helps identify similar issues
- **Auto-triage** creates issues for CI failures
- **Stale management** marks inactive items after 30 days, closes after 60 days
- **Project boards** automatically updated with status labels

### Security & Dependencies

- **Daily security scans** at 2 AM
- **Weekly dependency updates** on Mondays
- **Vulnerability issues** created automatically
- **Dependabot PRs** for all ecosystems (pip, npm, Docker, Actions)

### Releases

- **Tag a version** with `v*.*.*` format (e.g., `v1.2.3`)
- **Changelog generated** automatically from commits
- **GitHub release** created with categorized changes
- **Pre-releases** detected (alpha, beta, rc)

## Common Workflows

### Merging Dependabot PRs

1. Check the PR - auto-labeled with `dependencies`
2. Review the changes
3. Wait for CI to pass
4. Patch/minor updates auto-merge
5. Major updates need manual approval

### Handling Stale PRs

1. PRs inactive for 30 days get `stale` label
2. PRs inactive for 60 days get auto-closed
3. Add `keep-open` label to prevent auto-close
4. Comment or push to remove stale label

### Creating Releases

1. Ensure all changes are merged to main
2. Tag with version: `git tag v1.2.3`
3. Push tag: `git push origin v1.2.3`
4. Automation creates release with changelog
5. Edit release notes if needed

## Labels Used by Automation

### Automatically Added
- `size/XS`, `size/S`, `size/M`, `size/L`, `size/XL` - PR size
- `work-in-progress` - Draft PRs or WIP in title
- `breaking-change` - Breaking changes detected
- `first-time-contributor` - First PR from contributor
- `auto-approved` - Documentation-only PRs
- `potential-duplicate` - Similar issues found
- `needs-tests` - Code changes without tests
- `needs-description` - PR missing description
- `needs-better-commits` - Non-conventional commits
- `stale` - Inactive for 30 days
- `dependencies` - Dependency updates
- Path-based labels: `documentation`, `tests`, `database`, `scripts`, etc.

### Manual Labels
- `keep-open` - Prevent auto-close
- `priority: low/medium/high/critical` - Issue priority
- `status: backlog/in-progress/done` - Work status

## Disabling Automation

To skip automation on specific PRs:
- Add `skip-automation` label (create if needed)
- Use `keep-open` for preventing auto-close
- Close and reopen to re-trigger workflows

## Getting Help

- Read detailed docs: `.github/AUTOMATION.md`
- Review workflows: `.github/workflows/`
- Check logs in Actions tab
- Open an issue for automation problems

## Tips

✅ **DO**:
- Write descriptive commit messages
- Add tests with code changes
- Link related issues in PRs
- Respond to automation comments
- Update documentation

❌ **DON'T**:
- Ignore automation suggestions
- Remove labels without reason
- Push without testing
- Skip PR template sections
- Leave stale PRs open indefinitely

## Quick Reference

| Action | Trigger | Result |
|--------|---------|--------|
| Open PR | Any PR | Auto-label, assign, check quality |
| Tag version | `v*.*.*` | Create release with changelog |
| Inactive PR | 30 days | Mark as stale |
| Inactive PR | 60 days | Auto-close |
| Dependabot PR | Patch/minor | Auto-merge after CI |
| First contribution | First PR/issue | Welcome message |
| Commit message | Non-conventional | Linting comment |
| New issue | Duplicate detected | Comment with similar issues |
| CI failure | Build fails | Create issue |
| Security issue | Daily scan | Create issue if found |

## Questions?

See `.github/AUTOMATION.md` for comprehensive documentation.
