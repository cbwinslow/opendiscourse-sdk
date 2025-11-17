# Pull Request Review Checklist

Use this checklist when reviewing pull requests to ensure code quality, security, and maintainability.

## Pre-Review Checks

- [ ] PR has a clear, descriptive title following conventional commits format
- [ ] PR description includes purpose, changes, and testing information
- [ ] PR is linked to related issues
- [ ] PR is appropriately sized (not too large)
- [ ] CI/CD checks are passing
- [ ] No merge conflicts with target branch

## Code Quality

### General Code Quality
- [ ] Code follows project coding standards ([CODING_STANDARDS.md](../CODING_STANDARDS.md))
- [ ] Code is readable and self-documenting
- [ ] No unnecessary complexity or over-engineering
- [ ] No code duplication (DRY principle followed)
- [ ] Consistent naming conventions used
- [ ] No commented-out code blocks (unless with explanation)
- [ ] No debug statements or console.logs left in production code

### Python Specific
- [ ] Follows PEP 8 style guide
- [ ] Type hints are present on all function signatures
- [ ] Docstrings follow Google style format
- [ ] Proper exception handling with specific exceptions
- [ ] No use of bare `except:` clauses
- [ ] Imports are properly organized (stdlib, third-party, local)
- [ ] No use of mutable default arguments
- [ ] Async/await used appropriately for I/O operations

### TypeScript/JavaScript Specific
- [ ] TypeScript strict mode enabled and no `any` types
- [ ] Proper type definitions for all parameters and returns
- [ ] React components use appropriate patterns (functional, hooks)
- [ ] No unnecessary re-renders in React components
- [ ] Proper use of useMemo/useCallback where appropriate
- [ ] No direct DOM manipulation in React code
- [ ] Promises handled correctly with proper error handling
- [ ] No missing dependencies in useEffect arrays

## Architecture & Design

- [ ] Changes fit within existing architecture
- [ ] Appropriate design patterns used
- [ ] Separation of concerns maintained
- [ ] Components/modules have single, well-defined responsibilities
- [ ] Proper abstraction levels maintained
- [ ] Dependencies are injected, not hardcoded
- [ ] Interface/API contracts are clear and documented

## Security

### Input Validation
- [ ] All user inputs are validated
- [ ] Input validation uses appropriate libraries (Pydantic, Zod, etc.)
- [ ] No SQL injection vulnerabilities (parameterized queries used)
- [ ] No XSS vulnerabilities (proper sanitization)
- [ ] File uploads are properly validated (type, size, content)
- [ ] Path traversal attacks prevented

### Authentication & Authorization
- [ ] Authentication is properly implemented
- [ ] Authorization checks are in place
- [ ] No hard-coded credentials or secrets
- [ ] Proper use of environment variables for sensitive data
- [ ] Session management is secure
- [ ] CORS configured appropriately

### Data Protection
- [ ] Sensitive data is encrypted at rest and in transit
- [ ] No sensitive information in logs
- [ ] No exposure of internal system details in error messages
- [ ] Proper data sanitization before output
- [ ] Rate limiting implemented where appropriate

### Dependencies
- [ ] No new dependencies with known vulnerabilities
- [ ] New dependencies are justified and necessary
- [ ] Dependencies are pinned to specific versions
- [ ] License compatibility verified for new dependencies

## Performance

- [ ] No obvious performance bottlenecks
- [ ] Database queries are optimized (appropriate indexes, no N+1 queries)
- [ ] Appropriate caching strategy implemented
- [ ] No unnecessary network requests
- [ ] Large lists/collections are paginated
- [ ] Expensive operations are async where appropriate
- [ ] Memory leaks prevented (proper cleanup in useEffect, context managers, etc.)
- [ ] Bundle size impact considered for frontend changes

## Testing

### Test Coverage
- [ ] New functionality has appropriate tests
- [ ] Tests cover happy path scenarios
- [ ] Tests cover error cases and edge cases
- [ ] Test coverage meets project minimum (80%)
- [ ] No flaky tests introduced

### Test Quality
- [ ] Tests are clear and well-named
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] Tests are isolated and don't depend on order
- [ ] Appropriate use of mocks and fixtures
- [ ] Integration tests for critical paths
- [ ] Tests actually test the intended functionality

## Database Changes

- [ ] Database migrations are reversible
- [ ] Migrations are tested (up and down)
- [ ] No breaking changes to database schema without migration path
- [ ] Indexes added for new query patterns
- [ ] Foreign key constraints are appropriate
- [ ] Default values set appropriately for new columns
- [ ] Data migrations preserve existing data

## API Changes

- [ ] API changes are backward compatible (or versioned)
- [ ] API documentation updated (OpenAPI/Swagger)
- [ ] Request/response models properly defined
- [ ] Appropriate HTTP status codes used
- [ ] Error responses follow standard format
- [ ] Rate limiting considered
- [ ] API endpoints follow RESTful conventions

## Documentation

- [ ] Code changes are reflected in documentation
- [ ] Public APIs have clear docstrings/comments
- [ ] README updated if necessary
- [ ] CHANGELOG.md updated for user-facing changes
- [ ] Complex logic has explanatory comments
- [ ] Configuration changes documented
- [ ] Migration guides provided for breaking changes

## Frontend Specific

- [ ] UI is responsive and works on different screen sizes
- [ ] Accessibility considerations (ARIA labels, keyboard navigation)
- [ ] Loading states implemented
- [ ] Error states handled gracefully
- [ ] User feedback provided for actions
- [ ] No console errors or warnings
- [ ] Images optimized and have alt text
- [ ] Forms have proper validation and error messages

## Configuration & Infrastructure

- [ ] Environment variables properly documented
- [ ] Configuration changes backward compatible
- [ ] Docker/deployment configurations updated if needed
- [ ] No breaking changes to CI/CD pipeline
- [ ] Resource limits appropriate (memory, CPU)

## Git & Version Control

- [ ] Commit messages follow conventional commits format
- [ ] Commits are logical and atomic
- [ ] No sensitive information in commit history
- [ ] Branch naming follows conventions
- [ ] No unnecessary files committed (build artifacts, IDE configs)

## Maintainability

- [ ] Code will be easy to maintain and extend
- [ ] Technical debt is not increased unnecessarily
- [ ] TODO comments have associated issues
- [ ] Deprecated code is removed or marked clearly
- [ ] Breaking changes are clearly documented

## Final Checks

- [ ] All automated checks pass (linting, type checking, tests)
- [ ] Manual testing performed if applicable
- [ ] No obvious bugs or issues
- [ ] Changes align with project roadmap and goals
- [ ] Performance impact acceptable
- [ ] Security implications considered

## Approval Decision

### Approve ✅
Ready to merge. All critical items checked and any issues resolved.

### Request Changes 🔄
Issues found that must be addressed before merge. Provide clear, actionable feedback.

### Comment 💬
Minor suggestions or questions that don't block merge. Author can address at their discretion.

---

## Tips for Reviewers

1. **Be Constructive**: Provide specific, actionable feedback
2. **Explain Why**: Help the author understand the reasoning behind suggestions
3. **Praise Good Work**: Acknowledge well-written code and clever solutions
4. **Ask Questions**: If something is unclear, ask rather than assume
5. **Consider Context**: Understand the trade-offs and constraints
6. **Be Timely**: Try to review within 24 hours
7. **Focus on Important Issues**: Don't nitpick style if automated tools handle it
8. **Test It**: Check out the branch and test changes when possible

## Tips for Authors

1. **Self-Review First**: Review your own PR before requesting reviews
2. **Keep PRs Small**: Smaller PRs are easier to review and less likely to have issues
3. **Provide Context**: Explain why changes were made, not just what changed
4. **Address All Feedback**: Respond to every comment, even if just to acknowledge
5. **Be Open to Feedback**: View reviews as opportunities to improve
6. **Update PR Description**: Keep description current if changes are made during review
7. **Test Thoroughly**: Test your changes before requesting review

---

**Last Updated**: 2025-11-17
