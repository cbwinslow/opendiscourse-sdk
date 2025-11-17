# OpenDiscourse Development Guide

## Ollama Delegation Workflow
```python
from scripts.ollama_delegator import OllamaDelegator

# Initialize with configuration from api_config.py
delegator = OllamaDelegator()

try:
    response = delegator.delegate(
        "Analyze this SQL query: SELECT * FROM users",
        model="codellama",
        timeout=60
    )
    print(f"Analysis results: {response}")
except OllamaDelegationError as e:
    print(f"Delegation failed after retries: {e}")

### Configuration
Update `api_config.py` with:
```python
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "default_model": "llama2",
    "timeout": 300,
    "max_retries": 3
}
```

## Agent Communication Patterns
[... existing content ...]
