# Development Workflow Guide

This document describes the recommended development workflow for the opendiscourse project, including multi-agent collaboration, microgoal-driven task management, and automation practices.

## Key Practices

- Use microgoals: Break down features and fixes into small, measurable, attainable tasks.
- Multi-agent workflow: Delegate tasks to AI agents (Ollama, Agent-Zero, OpenAI Codex) for code generation, review, and planning.
- Document all changes: Update documentation and project task lists with every change.
- Use scripts for automation: Scripts are provided for migrations, health checks, and agent orchestration.

## Multi-Agent Workflow

1. Task Planning Phase:
   - Break down task into microgoals
   - Identify required agent capabilities
   - Create agent delegation plan

2. Agent Assignment:
   - Ollama: Local code generation, RAG tasks
   - Agent-Zero: Code review, PR management
   - OpenAI Codex: Complex code generation

3. Orchestration:
   - Use `agentOrchestrator.ts` for workflow management
   - Monitor agent health with `monitorAgent.ts`
   - Track metrics using `agentMetrics.ts`

4. Quality Control:
   - Automated testing via CI/CD
   - Agent-Zero code review
   - Human review of critical changes

## Microgoal Tracking Process

1. Definition:
   - Clear, measurable outcome
   - Acceptance criteria
   - Dependencies identified

2. Documentation:
   - Update `project_tasks.md`
   - Reference in SRS.md
   - Add to traceability matrix

3. Progress Tracking:
   - Use project board for status
   - Link to relevant PRs/commits
   - Document blockers/dependencies

4. Completion:
   - Verify acceptance criteria
   - Update documentation
   - Mark as complete in tracking

## Code Review Guidelines

1. Automated Checks:
   - Linting (ESLint)
   - Type checking (TypeScript)
   - Unit tests pass
   - Integration tests pass

2. Agent-Zero Review:
   - Code style compliance
   - Security best practices
   - Performance considerations
   - Documentation completeness

3. Human Review Focus:
   - Business logic accuracy
   - Edge case handling
   - Security implications
   - Architecture alignment

4. Review Process:
   - Create PR with clear description
   - Reference microgoals/issues
   - Address feedback promptly
   - Update documentation

## Example Microgoal

- "Implement NIM API health check script"
  - Criteria: Script exists, runs, logs health status, documented in `PROJECT_STRUCTURE.md`.
  - Status: Tracked in project board
  - Dependencies: NIM API access
  - Documentation: Updated in PROJECT_STRUCTURE.md

- "Integrate Ollama for local LLM agent"
  - Criteria: Ollama installed, model running, API accessible
  - Status: Completed
  - Documentation: Described in AGENTS.md

- "Set up OpenAI Codex for code generation"
  - Criteria: API key configured, script runs, code generated
  - Status: Completed
  - Documentation: Described in PROJECT_STRUCTURE.md

---

See `AGENT.md` for agent setup and delegation details.
