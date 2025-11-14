# Project Task Board

This document tracks all current and upcoming tasks, microgoals, and agent assignments for the opendiscourse project.

## Task Table

| Task/Microgoal                                      | Criteria/Definition                                      | Status    | Assigned Agent |
|-----------------------------------------------------|---------------------------------------------------------|-----------|---------------|
| Integrate Ollama for local LLM agent                | Ollama installed, model running, API accessible         | TODO      | Ollama        |
| Add Agent-Zero for code review/planning             | Agent-Zero app added to repo, PRs reviewed              | TODO      | Agent-Zero    |
| Set up OpenAI Codex for code generation             | API key configured, script runs, code generated         | TODO      | OpenAI Codex  |
| Create DEVELOPMENT.md and AGENT.md docs             | Docs exist, describe workflow and agent setup           | DONE      | Copilot       |
| Create SRS with microgoals and measurable criteria  | SRS exists, microgoals listed, criteria defined         | TODO      | Copilot       |
| Automate db migration/health scripts                | Scripts exist, run, and are documented                  | DONE      | Copilot       |
| Document all new scripts in PROJECT_STRUCTURE.md    | PROJECT_STRUCTURE.md updated with new scripts           | DONE      | Copilot       |
| Implement Codex delegation workflow                 | Script exists, documented, can send prompt to Codex and save result | DONE      | Copilot       |
| Implement Ollama delegation workflow                | Script exists, documented, can send prompt to Ollama and save result | TODO      | Copilot       |
| Implement Ollama agent API for workload submission  | API endpoint exists, accepts prompt, returns ID          | DONE      | Copilot       |
| Implement Ollama agent background worker            | Worker processes prompt, stores result, handles errors   | DONE      | Copilot       |
| Implement Ollama agent webhook/callback             | Webhook endpoint exists, receives and logs notifications | DONE      | Copilot       |
| Implement Ollama agent result/status API            | API endpoint returns status/result for given ID          | DONE      | Copilot       |
| Document MCP server API endpoints                   | API reference exists in docs, endpoints described        | DONE      | Copilot       |
| Integrate MCP server endpoints with UI              | UI can submit, poll, and display results from MCP server | TODO      | Copilot       |
| GovInfo: Data Download                             | Identify target collections, create download script, set up storage | TODO      | Copilot       |
| GovInfo: Database Design                           | Design tables/relationships, implement schema, load data | TODO      | Copilot       |
| GovInfo: ERD Creation                              | Generate/validate/export ERD                             | TODO      | Copilot       |
| GovInfo: Documentation                             | Create project docs, write README                        | TODO      | Copilot       |
| Committee: Database Design                         | Finalize schema, implement structure, load data          | TODO      | Copilot       |
| Committee: ERD Creation                            | Generate/validate/export ERD                             | TODO      | Copilot       |
| Committee: Documentation                           | Create docs, write README                                | TODO      | Copilot       |
| Member: Data Extraction                            | Extraction script, pagination, historical data           | TODO      | Copilot       |
| Member: Data Processing                            | Parse/transform data, create schema                      | TODO      | Copilot       |
| Member: Data Validation                            | Validation scripts, quality checks, error handling       | TODO      | Copilot       |
| Member: Database Design                            | Design/implement schema, load data                       | TODO      | Copilot       |
| Member: ERD Creation                               | Generate/validate/export ERD                             | TODO      | Copilot       |
| Member: Documentation                              | Create docs, write README                                | TODO      | Copilot       |

---

## Completed Tasks (Satisfied)
- API setup, data validation, and processing for all pipelines
- Database migration/health scripts automated
- Documentation for new scripts in PROJECT_STRUCTURE.md
- Codex and Ollama agent API, background worker, webhook, and result/status API
- MCP server API endpoints documented

Update this file as tasks are completed or new microgoals are defined.
