# Claude-Specific Development Notes
## OpenDiscourse CLI Tools

**Agent**: Anthropic Claude 3.5 Sonnet
**Last Updated**: 2025-12-03

---

## 1. Claude Strengths for This Project

### 1.1 Precise Code Generation
- **Excellent at**: Following exact specifications
- **Use for**: Implementing specific features
- **Example task**:
  ```
  Implement export_to_parquet() function with these exact requirements:
  1. Accept List[Dict] as input
  2. Use pyarrow for conversion
  3. Support Snappy compression
  4. Handle schema inference
  5. Write to file path
  ```

### 1.2 Debugging & Problem Solving
- **Excellent at**: Step-by-step debugging
- **Use for**: Fixing bugs, diagnosing issues
- **Example task**:
  ```
  This code is failing with "IntegrityError: duplicate key":

  ```python
  {buggy_code}
  ```

  Debug and fix the issue. Explain the root cause.
  ```

### 1.3 Clear Technical Writing
- **Excellent at**: User-facing documentation
- **Use for**: CLI help text, README, tutorials
- **Example task**:
  ```
  Write a beginner-friendly guide for:
  - Installing the CLI
  - Configuring API keys
  - Running first ingestion
  - Exporting data

  Use clear examples and explain common pitfalls.
  ```

---

## 2. Optimal Prompts for Claude

### 2.1 Feature Implementation
```
Implement the {feature_name} feature.

Specifications:
- Input: {input_spec}
- Output: {output_spec}
- Constraints: {constraints}

Requirements:
1. {req1}
2. {req2}

Location: scripts/ingestion/{file}.py

Follow the existing code style and patterns.
Show the complete implementation with:
- Type hints
- Docstring (Google style)
- Error handling
- Logging
- Tests
```

### 2.2 Bug Fixing
```
Fix this bug:

Error: {error_message}

Code:
```python
{code}
```

Steps to reproduce: {steps}

Explain:
1. Root cause
2. Fix (with code)
3. How to prevent similar bugs
4. Test to catch regression
```

---

## 3. Claude Limitations & Workarounds

### 3.1 Verbose Explanations
**Problem**: Claude can be overly explanatory

**Mitigation**:
- Request concise responses for routine tasks
- Ask for "code only" when appropriate
- Use "brief explanation" modifier

**Example prompts**:
```
// Detailed explanation wanted:
Explain how the rate limiting works and implement improvements

// Code-focused:
Add rate limiting to this function. Code only, minimal comments.
```

### 3.2 Conservative Approach
**Problem**: May suggest safe but not optimal solutions

**Mitigation**:
- Request "optimized" or "performant" versions
- Ask for trade-off analysis
- Compare multiple approaches

**Example**:
```
Implement CSV export.

Show 3 approaches:
1. Simple (pandas)
2. Memory-efficient (streaming)
3. Fastest (native Python csv)

Compare memory usage and speed.
```

---

## 4. Best Practices for Claude Usage

### 4.1 Structured Conversations
**Approach**:
- One clear task per prompt
- Provide complete context upfront
- Use numbered lists for multi-step tasks

**Good structure**:
```
Task: Add --format option to bills command

Context:
- File: scripts/ingestion/congress_cli.py
- Supported formats: json, csv, parquet
- Export functions exist in utils/export.py

Steps:
1. Add --format argument to ArgumentParser
2. Call appropriate export function
3. Add tests for each format
4. Update documentation

Please implement steps 1-2 first.
```

### 4.2 Leveraging Artifacts
**Use for**:
- Complete file implementations
- Configuration examples
- Test suites
- Documentation

Claude will present these in readable, copyable format.

---

## 5. Common Tasks for Claude

### 5.1 CLI Command Implementation
**Template**:
```
Add a new CLI command: {command_name}

Purpose: {description}

Arguments:
- {arg1}: {description}
- {arg2}: {description}

Options:
- --{opt1}: {description}
- --{opt2}: {description}

Examples:
```bash
{example1}
{example2}
```

Implementation requirements:
- Add to subparsers
- Implement handler method
- Add validation
- Write tests
- Update help text
```

### 5.2 Test Suite Generation
**Template**:
```
Generate comprehensive tests for:

```python
{function_or_class}
```

Cover:
- Valid inputs (parametrize 5+ cases)
- Invalid inputs (ValueError, TypeError)
- Edge cases (empty, None, large data)
- External failures (API, DB)

Use:
- pytest
- pytest-mock for mocking
- fixtures for setup
- parametrize for multiple cases
```

---

## 6. Claude-Specific Workflows

### 6.1 Incremental Development
**Process**:
1. Design interface
2. Implement core logic
3. Add validation
4. Add error handling
5. Add logging
6. Write tests
7. Document

**Conversation flow**:
```
User: Design the interface for advanced bill filtering

Claude: [Proposes interface]

User: Approved. Implement core logic only.

Claude: [Implements]

User: Add input validation.

Claude: [Adds validation]

...continue step by step
```

### 6.2 Code Review Mode
**Process**:
1. Submit code for review
2. Claude provides detailed feedback
3. Iterate on fixes
4. Final approval

**Prompt**:
```
Review this code for production deployment:

```python
{code}
```

Check for:
- Correctness
- Security (SQL injection, XSS)
- Performance (N+1, memory leaks)
- Maintainability
- Test coverage
- Documentation

Rate each category 1-10 and provide specific improvements.
```

---

## 7. Quality Assurance with Claude

### 7.1 Security Review
```
Security audit this database query function:

```python
{function}
```

Check for:
- SQL injection vulnerabilities
- Improper input validation
- Connection/cursor leaks
- Transaction safety
- Privilege escalation risks

Provide:
- Vulnerability severity (Critical/High/Medium/Low)
- Exploit examples
- Secure implementation
```

### 7.2 Testing Strategy
```
Create a testing strategy for {feature}:

1. Unit tests (what to test)
2. Integration tests (scenarios)
3. Edge cases (list them)
4. Mocking strategy (what to mock)
5. Test data (fixtures needed)

Then implement the highest priority tests.
```

---

## 8. Integration Examples

### 8.1 With Click Framework
```
Convert this argparse command to Click:

```python
{argparse_code}
```

Requirements:
- Maintain same CLI interface
- Use click.option decorators
- Add click.echo for output
- Preserve help text
- Add click.confirm for dangerous operations
```

### 8.2 With SQLAlchemy
```
Convert these raw SQL queries to SQLAlchemy ORM:

```python
{raw_queries}
```

Use:
- SQLAlchemy 2.0 style
- Type hints
- Async if beneficial
- Query composition for reusability
```

---

## 9. Documentation with Claude

### 9.1 API Reference
**Prompt**:
```
Generate API reference documentation for:

```python
{module_code}
```

Format: Markdown

Include:
- Module docstring
- Class descriptions
- Method signatures with types
- Parameter descriptions
- Return value descriptions
- Usage examples
- Exceptions raised
```

### 9.2 Tutorial Creation
**Prompt**:
```
Write a tutorial: "Getting Started with {CLI_NAME}"

Audience: Developers new to the tool

Sections:
1. Installation
2. Configuration
3. Basic commands
4. Common workflows
5. Troubleshooting

Use:
- Real examples
- Expected output
- Common errors and fixes
- Tips and best practices
```

---

## 10. Advanced Claude Features

### 10.1 Step-by-Step Reasoning
**When to use**: Complex logic, algorithm design

**Example**:
```
Design an algorithm optimal for incremental sync:

Requirements:
- Minimize API calls
- Avoid duplicate processing
- Handle failures gracefully
- Resume from last checkpoint

Think through:
1. Data structures needed
2. Algorithm steps
3. Edge cases
4. Recovery strategy

Then implement.
```

### 10.2 Comparative Analysis
**Use case**: Choosing between approaches

**Example**:
```
Compare these 3 approaches for exporting large datasets:

1. pandas.to_csv()
2. Python csv module with streaming
3. Direct SQL COPY command

Compare:
- Memory usage
- Speed
- Code complexity
- Error handling

Recommend best for our use case (10M+ rows).
```

---

## 11. Claude Configuration

### 11.1 Recommended Approach
- **Mode**: Extended thinking for complex tasks
- **Follow-ups**: Ask for clarification
- **Format**: Request artifacts for code
- **Iteration**: One feature at a time

### 11.2 Prompt Modifiers
**Concise mode**:
```
[Brief explanation] {task}
```

**Detailed mode**:
```
[Detailed explanation] {task}
Explain your reasoning.
```

**Code-focused**:
```
[Code only] {task}
```

---

## 12. Success Patterns

### 12.1 Effective Communication
- Provide complete context
- Use specific examples
- Request structured output
- Iterate incrementally

### 12.2 Quality Metrics
Track Claude's output quality:
- Code correctness (passes tests)
- Documentation clarity (user feedback)
- Problem-solving effectiveness (bugs fixed)
- Time efficiency (vs manual coding)

### 12.3 Common Pitfalls to Avoid
- Vague requirements → Be specific
- Missing context → Provide files/schemas
- Too many tasks at once → Break down
- Accepting first solution → Ask for alternatives

---

## 13. Project-Specific Tips

### 13.1 Database Operations
Always remind Claude:
```
Use parameterized queries with %s
Never use f-strings for SQL
Always commit/rollback in try/except
Close cursors in finally
```

### 13.2 API Integration
Always specify:
```
Use rate_limiter.wait() before requests
Implement exponential backoff for 429
Maximum 3 retries
Log all API errors
```

### 13.3 CLI Best Practices
Request:
```
Add --dry-run for dangerous operations
Use click.echo (not print)
Show progress bars for long operations
Colorize output (with --no-color option)
```
