# Open Discourse Developer Guide

## Universal Development Rules
- Use Python 3.10 (see `.python-version`)
- Track all dependencies in `requirements.txt` and `requirements-dev.txt`
- Use `.editorconfig` for consistent formatting
- Store secrets in `.env` (never commit real secrets)
- All agent thought processes must be logged to `agent.log`
- For every feature: update docs, add/modify unit tests, update dependencies, log agent reasoning
