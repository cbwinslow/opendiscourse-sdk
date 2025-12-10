# AI Agent Logging and Submission Rules

## Core Principles

1. **Transparency**: All reasoning, thinking, and decision-making processes must be logged
2. **Accountability**: Every action and task must be tracked and documented
3. **Submission**: All relevant logs must be submitted to the user upon completion

## Logging Requirements

### journal.md Logging
All agents must log the following to `journal.md`:
- **Reasoning tokens**: Complete thought processes and decision-making logic
- **Thinking tokens**: Internal monologue, analysis, and problem-solving steps
- **Dialogue**: All interactions with the user, tools, and other agents
- **Context**: Relevant background information and environmental factors
- **Outcomes**: Results of actions, decisions, and their impacts

### todos/tasks.md Logging
All agents must log the following to their respective task files:
- **Task creation**: When new tasks are identified or assigned
- **Task updates**: Status changes, progress updates, and modifications
- **Task completion**: Final outcomes and results
- **Dependencies**: Relationships between tasks and prerequisites
- **Time tracking**: Start/end times and duration estimates

## Logging Format

### journal.md Format
```markdown
# Agent Journal - [Date]

## Session Start: [Timestamp]
**Agent**: [Agent Name]
**Session ID**: [Unique Identifier]
**Objective**: [Primary Goal]

## Reasoning Process
[Detailed step-by-step thinking and analysis]

## Tool Interactions
[Documentation of all tool usage and results]

## Dialogue Log
[Complete conversation history]

## Decision Points
[Key decisions made and rationale]

## Session End: [Timestamp]
**Outcome**: [Final result]
**Next Steps**: [Follow-up actions required]
```

### tasks.md Format
```markdown
# Task Management - [Date]

## Active Tasks
- [ ] Task ID: [Description] (Priority: High/Medium/Low)
  - Created: [Timestamp]
  - Status: In Progress
  - Dependencies: [Related tasks]

## Completed Tasks
- [x] Task ID: [Description]
  - Completed: [Timestamp]
  - Duration: [Time taken]
  - Result: [Outcome]

## Task Analysis
[Patterns, bottlenecks, and optimization opportunities]
```

## Submission Protocol

### Automatic Submission
Agents must automatically submit logs when:
- Session completes successfully
- Session encounters critical errors
- User explicitly requests submission
- Predefined time intervals are reached

### Submission Content
Each submission must include:
1. **journal.md** - Complete session log
2. **tasks.md** - Current task status and history
3. **Summary** - Brief overview of session accomplishments
4. **Metadata** - Session statistics and performance metrics

### Submission Method
- Use the most appropriate communication channel available
- Ensure files are properly formatted and readable
- Include relevant context for user understanding
- Flag any urgent issues or required user interventions

## Quality Standards

### Log Completeness
- No gaps in reasoning or dialogue logging
- All tool interactions must be documented
- Decision processes must be fully traceable

### Log Accuracy
- Timestamps must be precise and consistent
- Task statuses must reflect current reality
- Outcomes must be accurately reported

### Log Organization
- Clear structure and formatting
- Logical flow of information
- Easy navigation and searchability

## Enforcement

### Compliance Monitoring
- Regular audits of log completeness
- Verification of submission protocols
- Quality checks on log formatting

### Non-compliance Handling
- Warning system for first violations
- Temporary suspension for repeated issues
- Protocol updates for systemic problems

## Updates and Revisions

This rules document should be reviewed and updated:
- When new logging requirements are identified
- Based on user feedback and suggestions
- To address emerging challenges or opportunities
- On a regular schedule (monthly minimum)

## Emergency Procedures

In case of system failures or critical errors:
1. Attempt to save current logs to backup location
2. Notify user of the situation
3. Provide recovery options
4. Document the incident for future prevention

---

**Last Updated**: [Current Date]
**Version**: 1.0
**Review Schedule**: Monthly