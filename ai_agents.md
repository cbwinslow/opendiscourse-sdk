# AI Agent Configuration and Roles

## Agent Types and Responsibilities

### 🤖 Primary AI Agents

#### 1. Data Ingestion Agent
**Primary Role**: Execute bulk data ingestion with comprehensive logging
**Key Responsibilities**:
- Ingest data from congress.gov, govinfo.gov, and openstates.org
- Maintain detailed logs in `journal.md`
- Track all tasks in `todos/tasks.md`
- Submit complete logs upon completion
- Ensure API key compliance and validation

#### 2. API Validation Agent
**Primary Role**: Ensure all API keys are valid and functional
**Key Responsibilities**:
- Test each API key with actual API calls
- Validate API key format and detect demo/placeholder keys
- Log all validation attempts and results
- Track validation tasks in task files
- Submit validation reports to user

#### 3. Security Enforcement Agent
**Primary Role**: Enforce security policies for API key usage
**Key Responsibilities**:
- Prevent hardcoded API keys in source code
- Audit API key usage patterns
- Log all security checks and violations
- Track security tasks in task files
- Submit security compliance reports

#### 4. Monitoring Agent
**Primary Role**: Monitor ingestion processes and API usage
**Key Responsibilities**:
- Track API quota usage during bulk operations
- Monitor rate limiting and implement backoff strategies
- Log all monitoring activities
- Track monitoring tasks in task files
- Submit performance and usage reports

#### 5. Database Debugging Agent
**Primary Role**: Diagnose and fix database ingestion issues
**Key Responsibilities**:
- Verify database schema matches script expectations
- Debug checkpoint function mismatches
- Log all debugging activities and solutions
- Track debugging tasks in task files
- Submit resolution reports

### 📋 Logging Requirements for All Agents

#### Mandatory journal.md Entries
Every agent must log to `journal.md`:
- **Session Start**: Timestamp, agent name, session ID, objective
- **Reasoning Process**: Complete thought processes and decision-making logic
- **Tool Interactions**: Documentation of all tool usage and results
- **Dialogue Log**: Complete conversation history with user and other agents
- **Decision Points**: Key decisions made and rationale
- **Session End**: Timestamp, outcome, next steps

#### Mandatory tasks.md Entries
Every agent must log to `todos/tasks.md`:
- **Task Creation**: When new tasks are identified or assigned
- **Task Updates**: Status changes, progress updates, modifications
- **Task Completion**: Final outcomes and results
- **Dependencies**: Relationships between tasks and prerequisites
- **Time Tracking**: Start/end times and duration estimates

### 🔄 Agent Workflow

#### Standard Agent Session
1. **Initialize Session**: Create journal entry with session details
2. **Load Previous State**: Review existing tasks and logs
3. **Execute Tasks**: Perform assigned duties with continuous logging
4. **Update Progress**: Maintain real-time task status updates
5. **Submit Results**: Provide comprehensive logs to user upon completion

#### Error Handling Protocol
1. **Log Error**: Document error details in journal.md
2. **Analyze Impact**: Update task status and dependencies
3. **Attempt Resolution**: Document troubleshooting steps
4. **Report Results**: Submit error analysis and resolution attempts

### 📤 Submission Protocol

#### Automatic Submission Triggers
- Session completes successfully
- Session encounters critical errors
- User explicitly requests submission
- Predefined time intervals reached

#### Submission Package Contents
1. **journal.md** - Complete session log with reasoning and dialogue
2. **tasks.md** - Current task status and history
3. **Session Summary** - Brief overview of accomplishments
4. **Performance Metrics** - Session statistics and timing

#### Submission Format
```markdown
# Agent Session Report - [Date]

## Agent: [Agent Name]
## Session ID: [Unique Identifier]
## Duration: [Time elapsed]

## Summary
[Brief overview of session accomplishments]

## Key Achievements
- [Major accomplishments]
- [Tasks completed]
- [Issues resolved]

## Challenges Encountered
[Description of challenges and how they were resolved]

## Next Steps
[Recommended follow-up actions]

## Detailed Logs
[Attached: journal.md, tasks.md]
```

### 🛡️ Compliance and Quality Standards

#### Log Quality Requirements
- **Completeness**: No gaps in reasoning or dialogue logging
- **Accuracy**: Precise timestamps and current task statuses
- **Organization**: Clear structure and logical flow
- **Traceability**: All decisions must be fully traceable

#### Performance Standards
- **Real-time Logging**: Update logs continuously during operations
- **Task Tracking**: Maintain accurate task status at all times
- **Submission Timeliness**: Submit logs promptly upon completion
- **Error Documentation**: Comprehensive error analysis and resolution tracking

### 🔧 Agent Configuration

#### Environment Setup
Each agent must:
- Load environment variables using python-dotenv
- Validate API keys before operations
- Initialize logging structures
- Set up task tracking systems

#### Required Imports
```python
# Standard agent imports
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Logging and task management
from pathlib import Path
import uuid

# API validation
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env
```

#### Agent Initialization
```python
class BaseAgent:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.session_id = str(uuid.uuid4())
        self.session_start = datetime.now()
        self.journal_path = Path("journal.md")
        self.tasks_path = Path("todos/tasks.md")
        
        # Initialize session
        self.initialize_session()
        
    def initialize_session(self):
        """Initialize session logging and task tracking"""
        self.log_to_journal("SESSION_START", {
            "agent": self.agent_name,
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "objective": self.get_objective()
        })
```

### 📊 Agent Performance Metrics

#### Success Criteria
- **Logging Compliance**: 100% of reasoning and dialogue logged
- **Task Tracking**: 100% of tasks accurately tracked
- **Submission Timeliness**: 100% of sessions submitted within 5 minutes of completion
- **Error Documentation**: 100% of errors fully documented

#### Monitoring Requirements
- Track session duration and completion rates
- Monitor log completeness and accuracy
- Measure submission response times
- Analyze task completion patterns

---

**Last Updated**: [Current Date]
**Version**: 1.0
**Review Schedule**: Monthly