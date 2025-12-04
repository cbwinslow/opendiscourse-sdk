# Gemini-Specific Development Notes
## OpenDiscourse CLI Tools

**Agent**: Google Gemini 2.0 Flash (Thinking Mode)
**Last Updated**: 2025-12-03

---

## 1. Gemini Strengths for This Project

### 1.1 Code Analysis
- **Excellent at**: Understanding large codebases
- **Use for**: Refactoring existing CLIs
- **Example task**:
  ```
  Analyze scripts/ingestion/congress_cli.py and suggest improvements for:
  - Error handling
  - Code organization
  - Performance optimization
  ```

### 1.2 Documentation Generation
- **Excellent at**: Creating comprehensive docs from code
- **Use for**: API documentation, README generation
- **Example task**:
  ```
  Generate API documentation for all public methods in CongressCLI class
  in Google docstring format with examples
  ```

### 1.3 Large-Scale Refactoring
- **Excellent at**: Multi-file changes
- **Use for**: Migrating from argparse to Click/Typer
- **Example task**:
  ```
  Refactor congress_cli.py to use Click framework:
  1. Convert ArgumentParser to Click commands
  2. Add click.option decorators
  3. Maintain backward compatibility
  4. Update tests
  ```

---

## 2. Optimal Prompts for Gemini

### 2.1 Feature Implementation
```
I need to add {feature_name} to the {cli_name} CLI.

Context:
- Current file: scripts/ingestion/{cli_name}_cli.py
- Similar feature in: {reference_file}
- Database schema: migrations/{schema_file}

Requirements:
1. {requirement1}
2. {requirement2}

Please:
1. Show the implementation
2. Add type hints and docstrings
3. Include error handling
4. Write pytest tests
5. Update docs/cli_documentation.md

Think through the design first, then implement.
```

### 2.2 Code Review
```
Review this code for production readiness:

```python
{code_block}
```

Check for:
- Type safety
- Error handling
- SQL injection risks
- Rate limiting
- Memory efficiency
- Edge cases

Provide specific fixes with line numbers.
```

---

## 3. Gemini Limitations & Workarounds

### 3.1 Over-Engineering Risk
**Problem**: Gemini may suggest overly complex solutions

**Mitigation**:
- Specify "Keep it simple" in prompts
- Provide concrete examples of desired approach
- Ask for incremental changes

**Example prompt**:
```
Implement this feature using the SIMPLEST approach possible.
Follow the existing pattern in {reference_file}.
```

### 3.2 Hallucinated APIs
**Problem**: May suggest non-existent library methods

**Mitigation**:
- Provide documentation links
- Show existing code patterns
- Request citation of sources

**Example prompt**:
```
Add export to Parquet format.
Use the pyarrow library (https://arrow.apache.org/docs/python/).
Show imports and verify method names against official docs.
```

---

## 4. Best Practices for Gemini Usage

### 4.1 Iterative Development
**Approach**:
1. Start with design/pseudocode
2. Implement core functionality
3. Add error handling
4. Write tests
5. Polish and optimize

**Example conversation**:
```
User: Design an advanced filtering system for bills

Gemini: [Provides design]

User: Looks good. Implement step 1 (filter builder class)

Gemini: [Implements]

User: Add type hints and docstrings

Gemini: [Enhances]
```

### 4.2 Providing Context
**Always include**:
- Relevant file paths
- Similar existing code
- Database schema
- API documentation links

**Template**:
```
Working on: {file_path}
Similar code: {reference_file}
Schema: {migration_file}
API docs: {url}

Task: {description}
```

---

## 5. Common Tasks for Gemini

### 5.1 Database Query Optimization
**Good prompt**:
```
Optimize this query for better performance:

```python
{current_query}
```

Database: PostgreSQL 14
Table stats: 1M rows, indexed on (congress_number, bill_type)
Current execution time: 2.5s
Goal: <500ms

Suggest:
1. Query rewrite
2. Index recommendations
3. Explain plan analysis
```

### 5.2 Test Generation
**Good prompt**:
```
Generate comprehensive pytest tests for this function:

```python
{function_code}
```

Include tests for:
- Happy path
- Invalid inputs (ValueError)
- Database errors
- API failures
- Edge cases (empty results, large datasets)

Use pytest fixtures for database and API mocking.
```

---

## 6. Gemini-Specific Workflows

### 6.1 Multi-File Refactoring
**Process**:
1. Gemini analyzes all affected files
2. Creates refactoring plan
3. Implements changes file-by-file
4. Updates tests
5. Verifies no breaking changes

**Prompt structure**:
```
I need to refactor the CLI tools to use Click framework.

Files to change:
- scripts/ingestion/congress_cli.py (500 lines)
- scripts/ingestion/openstates_cli.py (600 lines)
- scripts/ingestion/govinfo_cli.py (400 lines)

Create a refactoring plan that:
1. Minimizes breaking changes
2. Maintains test compatibility
3. Improves code organization
4. Can be done incrementally

Show the plan first, then implement one file at a time.
```

### 6.2 Documentation from Code
**Process**:
1. Gemini reads codebase
2. Generates API reference
3. Creates usage examples
4. Builds tutorial

**Prompt**:
```
Generate user documentation from:
- scripts/ingestion/congress_cli.py
- scripts/ingestion/openstates_cli.py
- scripts/ingestion/govinfo_cli.py

Create:
1. API Reference (all commands, options, examples)
2. Quick Start Guide
3. Common Use Cases
4. Troubleshooting Section

Format: Markdown for MkDocs
```

---

## 7. Quality Assurance with Gemini

### 7.1 Code Review Checklist
```
Review this PR for production readiness:

Files changed: {list}

Verify:
- [ ] Type hints on all functions
- [ ] Docstrings with examples
- [ ] Error handling
- [ ] SQL injection prevention
- [ ] Rate limiting compliance
- [ ] Memory efficiency
- [ ] Test coverage >80%
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Changelog entry

Provide detailed feedback with specific line numbers.
```

### 7.2 Performance Analysis
```
Analyze performance bottlenecks in:
{file_or_function}

Metrics:
- Current: {current_performance}
- Goal: {target_performance}

Suggest:
1. Hotspot identification
2. Optimization strategies
3. Profiling commands
4. Expected improvements
```

---

## 8. Integration Examples

### 8.1 With pytest
```
Generate unit tests using pytest for:

```python
{function_code}
```

Requirements:
- Use pytest fixtures
- Mock external dependencies (API, DB)
- Test edge cases
- Achieve >90% coverage
- Follow AAA pattern (Arrange, Act, Assert)
```

### 8.2 With mypy
```
Add type hints to make this code pass mypy --strict:

```python
{code}
```

Ensure:
- All parameters typed
- Return types specified
- Generic types for collections
- Optional for nullable values
```

---

## 9. Advanced Gemini Features

### 9.1 Thinking Mode
**When to use**: Complex design decisions, architectural choices

**Example**:
```
Design a distributed ingestion system that can:
1. Process 100K bills/hour
2. Handle API failures gracefully
3. Ensure data consistency
4. Support horizontal scaling

Think through:
- Architecture patterns
- Technology choices
- Trade-offs
- Failure modes

Then provide detailed design document.
```

### 9.2 Multi-Modal Capabilities
**Use cases**:
- Analyze database diagrams
- Review architecture diagrams
- Process API documentation screenshots

---

## 10. Gemini Configuration for This Project

### 10.1 Recommended Settings
- **Temperature**: 0.3 (for code generation)
- **Max Tokens**: 8000 (for large responses)
- **Stop Sequences**: None
- **Context Window**: Use full context

### 10.2 Prompt Templates
**Save these as snippets**:
1. Feature implementation
2. Code review
3. Test generation
4. Documentation creation
5. Refactoring plan

---

## 11. Success Metrics

Track Gemini's effectiveness:
- Code quality (linter score)
- Test coverage achieved
- Documentation completeness
- Time saved vs manual coding
- Bug introduction rate

Adjust prompts based on outcomes.
