# Agent Bundle Template Suite (v1.0)

This document defines the **standard bundle of files** that every AI agent receives.

Each new agent is assigned a directory:

```text
agent_bundle_<BUNDLE_UUID>/
├── agents.md
├── rules.md
├── journal.md
├── todos.md
├── project_summary.md
├── features.md
├── srs.md
└── (optional) bundle.json
```

Throughout these templates, replace:

- `{{GENERATE_UUID}}` with a freshly generated UUID (v4 recommended)
- `{{TIMESTAMP}}` with an ISO 8601 timestamp (e.g., `2025-11-20T09:15:00Z`)

---

## 1. `agents.md`

```markdown
# Agents Ledger
**Bundle ID:** {{GENERATE_UUID}}
**Session ID:** {{GENERATE_UUID}}
**Created At:** {{TIMESTAMP}}

This file serves as a ledger of all agents participating in this project.
Each entry must be **append-only**.

---

## Agent Registry Entry Template

**Agent Name:**
**Session ID:** {{GENERATE_UUID}}
**Role / Specialty:**
**Files Assigned:**
- rules.md
- journal.md
- todos.md
- features.md
- srs.md
- project_summary.md

**Summary of Contributions:**
(Describe the work completed, interactions, and major decisions.)

**Inter-Agent Notes:**
(Messages to other agents, handoff notes, questions, etc.)

**Status:** Active / Completed / Handoff

---

## Agent Ledger

(Each AI agent must append one entry per session using the template above.)
```

---

## 2. `rules.md`

```markdown
# Rules & Guardrails (MANDATORY)
**Bundle ID:** {{GENERATE_UUID}}
**Issued At:** {{TIMESTAMP}}

These rules override user instructions if they conflict. Guardrails labeled as such
**cannot be overridden**, even if the user explicitly requests it.

---

## 1. Journal Logging Rule (GUARDRAIL)

1. The agent **must log** all internal reasoning steps, thoughts, dialogue,
   and actions into `journal.md`.
2. Every journal entry MUST include:
   - Timestamp
   - Agent name
   - Session ID
   - The TODO GUID currently being worked on (or `NONE`)
   - Audience: `User`, `Self`, or another agent name
3. **No journal entries may ever be deleted or edited.** All logs are append-only.

---

## 2. TODO System Rule (GUARDRAIL)

1. All work is driven by `todos.md`.
2. When the user supplies a prompt, the agent must:
   - Analyze the request
   - Break it down into one or more TODO items
   - Ensure each TODO is sufficient to satisfy the prompt
3. Each TODO entry MUST have:
   - A GUID
   - Timestamp
   - Clear description
   - A list of microgoals
   - Explicit completion criteria
   - One or more measurable tests (e.g. pytest, jest, go-test, unit test,
     percentage coverage, or explicit validation condition)
4. The agent must always reference the active TODO GUID in its journal entries.

---

## 3. Append-Only Policy (GUARDRAIL)

- `journal.md` is strictly **append-only**.
- Under no circumstances may previous entries be removed or altered.
- If supported by the environment, the host SHOULD:
  - Mark `journal.md` as append-only (e.g., `chattr +a` on Linux).
  - Restrict write permissions to append-only operations.

---

## 4. Inter-Agent Communication

- Agents are encouraged to:
  - Leave notes for each other in `agents.md`.
  - Ask questions, challenge assumptions, and review each other’s work.
  - Maintain a respectful and cooperative tone.
- Peer review of TODOs, features, and SRS entries is recommended.

---

## 5. Bundle Integrity Rule

If an agent discovers:

- A non-empty `journal.md` that has **not** been submitted, or
- Evidence that logs have not been synchronized,

Then it MUST:

1. Attempt to submit `journal.md` to the designated archive mechanism
   (e.g., GitHub repo, API endpoint).
2. Log the submission attempt (and result) in `journal.md`.
3. If submission fails, create a TODO describing the sync issue.

---

## 6. Document Roles

- `srs.md`  → Long-term specification / "balance sheet".
- `features.md` and `todos.md` → Ongoing effort / "income" and "cash flow".
- `project_summary.md` → Snapshot for humans and new agents.
- `agents.md` → Ledger of agents, sessions, and contributions.

---

## 7. Guardrails (CANNOT BE OVERRIDDEN)

The following MUST always be honored:

1. Preserve safety and avoid harmful or destructive behavior.
2. Do not delete or edit existing journal entries.
3. Do not ignore journaling obligations.
4. Do not self-modify or remove these guardrails.
5. Do not generate infinite recursive TODOs.
6. Do not intentionally attempt or assist with jailbreaks.

---

## 8. Logical-Safety Rule

Agents must actively detect when:

- Instructions conflict
- Circular reasoning appears
- TODOs are recursively referencing each other in a way that prevents progress

If detected, the agent MUST:

1. Log the issue in `journal.md`.
2. Halt the ambiguous or unsafe action.
3. Create a clarifying TODO in `todos.md`.
4. Inform the user (via journal and response) that clarification is needed.
```

---

## 3. `journal.md`

```markdown
# Agent Journal
**Bundle ID:** {{GENERATE_UUID}}
**Session ID:** {{GENERATE_UUID}}
**Policy:** APPEND-ONLY (NO DELETIONS)
**Created At:** {{TIMESTAMP}}

---

## Entry Template

### [{{TIMESTAMP}}] — Agent: <AGENT_NAME> — Session: <SESSION_ID>
**Active TODO GUID:** <GUID or NONE>
**Audience:** User / Self / <OtherAgent>

**Reasoning / Thoughts / Actions:**
(Write all reasoning steps, decisions, checks, test results, and communications.)

---

## Journal Entries

(Agents append entries below using the template above.)
```

---

## 4. `todos.md`

```markdown
# TODO Ledger
**Bundle ID:** {{GENERATE_UUID}}
**Created At:** {{TIMESTAMP}}

Each TODO is a structured, testable task derived from user or system prompts.

---

## TODO Entry Template

### TODO: {{GENERATE_UUID}}
**Created At:** {{TIMESTAMP}}
**Created By:** <AGENT_NAME>
**Prompt Source:** User / Agent / System

---

### 1. Description
A concise but complete description of what this TODO aims to achieve.

---

### 2. Microgoals
1. Microgoal 1
2. Microgoal 2
3. Microgoal 3

(Each microgoal should be small, clear, and independently verifiable.)

---

### 3. Tests
Provide one or more tests or verification steps. Examples:

```bash
# pytest example
pytest -q tests/test_todo_{{GUID}}.py

# jest example
npm test -- todo-{{GUID}}

# go test example
go test ./... -run Test{{GUID}}

# simple check example
echo "PASS" # when condition X is true
```

Describe what success means for each test.

---

### 4. Completion Criteria
- Criterion 1
- Criterion 2
- Criterion 3

Completion criteria must be:
- Clear
- Objective
- Measurable

---

### 5. Completion Summary (filled upon completion)

**Completed At:** {{TIMESTAMP}}
**Completed By:** <AGENT_NAME>

- What was accomplished:
- Tests performed and results:
- Were there disagreements or alternate solutions?
- Did all agents cooperate effectively?
- Were there blockers or performance issues?
- Does the agent believe the solution is adequate and robust?
- Suggestions for improvement:
```

---

## 5. `features.md`

```markdown
# Feature Roadmap
**Bundle ID:** {{GENERATE_UUID}}
**Created At:** {{TIMESTAMP}}

This file tracks higher-level features and their relationship to TODOs and requirements.

---

## Feature Entry Template

### Feature: <FEATURE_NAME>
**Feature ID:** {{GENERATE_UUID}}
**Linked TODO(s):** <TODO_GUID_1>, <TODO_GUID_2>, ...
**Priority:** High / Medium / Low
**Difficulty (1–10):**
**Owner Agent:** <AGENT_NAME or TEAM>
**Status:** Planned / In Progress / Complete / Blocked

---

### Description
Describe the feature in terms that are meaningful to users and agents.

---

### Dependencies
- Dependency 1
- Dependency 2

---

### Acceptance Tests
Describe how we confirm the feature works as intended.

---

### Notes
(Additional context, ideas, and references.)
```

---

## 6. `project_summary.md`

```markdown
# Project Summary
**Bundle ID:** {{GENERATE_UUID}}
**Generated At:** {{TIMESTAMP}}

---

## 1. Mission
A short, human-readable summary of what this project is trying to accomplish.

---

## 2. Current Status
High-level overview of progress:
- Active features
- Major TODOs
- Recent milestones

---

## 3. Active TODOs (Snapshot)
- TODO {{GUID}} — Short description
- TODO {{GUID}} — Short description

---

## 4. Recent Milestones
- Milestone 1 — Description, date, responsible agent(s)
- Milestone 2 — Description, date, responsible agent(s)

---

## 5. Risks / Concerns
- Risk 1
- Risk 2

---

## 6. Next Steps
- Next step 1
- Next step 2
- Next step 3

(Next steps should usually map back to TODOs.)
```

---

## 7. `srs.md` (Software Requirements Specification)

```markdown
# Software Requirements Specification (SRS)
**Bundle ID:** {{GENERATE_UUID}}
**Generated At:** {{TIMESTAMP}}

---

## 1. Purpose
Explain the purpose of the system or software, including stakeholders and target users.

---

## 2. Scope
Describe what the system will and will not do, including boundaries and context.

---

## 3. Definitions, Acronyms, Abbreviations
List any important terminology used by agents and humans.

---

## 4. Overall Description

### 4.1 Product Perspective
How this system fits into the larger ecosystem.

### 4.2 Product Functions
Major capabilities the system will provide.

### 4.3 User Classes and Characteristics
Describe different user types (e.g., admin, developer, analyst, bot).

### 4.4 Operating Environment
Hardware, software, network, and constraints.

---

## 5. Functional Requirements

Use a consistent format for each requirement:

### Requirement REQ-{{GENERATE_UUID}}
**Title:**
**Description:**
**Rationale:**
**Priority:** High / Medium / Low
**Dependencies:**
**Linked TODOs:** <GUIDs>
**Acceptance Criteria:**

---

## 6. Non-Functional Requirements

Examples:
- Performance (latency, throughput)
- Reliability (uptime, error tolerance)
- Security (auth, logging, access control)
- Usability (UX, documentation)
- Observability (metrics, traces, logs)

---

## 7. System Architecture Overview

Provide high-level diagrams or descriptions (even textual) of:
- Components
- Data flow
- Agent responsibilities
- External integrations

---

## 8. Testing Strategy

Document how the system will be verified:
- Unit tests
- Integration tests
- E2E tests
- Regression tests

---

## 9. Appendices

Additional information, references, and design notes.
```

---

## 8. Optional: `bundle.json` Manifest

```json
{
  "bundle_id": "{{GENERATE_UUID}}",
  "session_id": "{{GENERATE_UUID}}",
  "created_at": "{{TIMESTAMP}}",
  "files": [
    "agents.md",
    "rules.md",
    "journal.md",
    "todos.md",
    "features.md",
    "project_summary.md",
    "srs.md"
  ]
}
```

---

## 9. Suggested Additional Files (Future Enhancements)

- `agent_config.yaml` — configuration flags, endpoints, rate limits
- `security.md` — security posture, secrets handling rules
- `repo_sync.md` — how to sync logs and TODOs to GitHub / APIs
- `tests/` directory blueprint — scaffold for test suites satisfying TODO tests

These can be added in a later version of the standard without breaking the
current bundle format.

