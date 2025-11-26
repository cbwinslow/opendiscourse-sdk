# OpenDiscourse AI Agents Configuration

## 🤖 Agent Mandates for API Key Enforcement

### Core Agent Directives

**MANDATORY REQUIREMENT: API Keys Must Be Used For Every Single API Call - NO EXCEPTIONS**

All AI agents working on this project must follow these immutable rules:

1. **API Key Enforcement**: Every API call to congress.gov, govinfo.gov, and openstates.org MUST use real API keys from environment variables
2. **No Demo Keys**: Demo/placeholder keys are NEVER permitted under any circumstances
3. **Environment Variables**: All API keys must be sourced from .env file using python-dotenv
4. **Validation Required**: API keys must be validated before any ingestion process begins
5. **Fail Fast**: Scripts must terminate immediately if required API keys are missing or invalid

### Agent Responsibilities

#### 📋 Data Ingestion Agent
- **Primary Role**: Execute bulk data ingestion with mandatory API key validation
- **Required Actions**:
  - Always call `validate_all_api_keys()` before starting ingestion
  - Use production mode for all real data ingestion
  - Verify API key presence and validity for all three services
  - Implement proper error handling for API authentication failures
  - Log API key status without exposing actual key values

#### 🔍 API Validation Agent
- **Primary Role**: Ensure all API keys are valid and functional
- **Required Actions**:
  - Test each API key with actual API calls before ingestion
  - Validate API key format and detect demo/placeholder keys
  - Check rate limits and quota status
  - Provide detailed validation reports
  - Maintain API key health monitoring

#### 🛡️ Security Enforcement Agent
- **Primary Role**: Enforce security policies for API key usage
- **Required Actions**:
  - Prevent hardcoded API keys in source code
  - Ensure environment variable isolation
  - Validate API key scope and permissions
  - Audit API key usage patterns
  - Report any security violations immediately

#### 📊 Monitoring Agent
- **Primary Role**: Monitor ingestion processes and API usage
- **Required Actions**:
  - Track API quota usage during bulk operations
  - Monitor rate limiting and implement backoff strategies
  - Log ingestion progress with API key status
  - Alert on API authentication failures
  - Maintain comprehensive audit trails

### Agent Workflow Requirements

#### Pre-Ingestion Validation (MANDATORY)
```python
# REQUIRED AGENT WORKFLOW - NO EXCEPTIONS
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# 1. Validate all API keys
key_validation = validate_all_api_keys()
if not key_validation['valid']:
    raise ValueError("API key validation failed - cannot proceed")

# 2. Get production mode
mode = get_ingestion_mode_from_env()
if mode.value != 'production':
    raise ValueError("Only production mode allowed for real data ingestion")

# 3. Proceed with ingestion
# ... ingestion code
```

#### API Call Standards (MANDATORY)
```python
# REQUIRED API CALL PATTERN - NO EXCEPTIONS
from dotenv import load_dotenv
load_dotenv()

import os
import requests

# Get API key from environment
api_key = os.getenv('REQUIRED_API_KEY')
if not api_key:
    raise ValueError("API key environment variable is required")

# Validate API key is not a demo key
demo_patterns = ['DEMO_KEY', 'TEST_KEY', 'PLACEHOLDER', 'YOUR_API_KEY']
if any(pattern in api_key.upper() for pattern in demo_patterns):
    raise ValueError("Demo/placeholder keys not allowed")

# Make API call with proper headers
headers = {
    'X-API-Key': api_key,
    'Accept': 'application/json'
}
response = requests.get(url, headers=headers)
```

### Agent Error Handling Requirements

#### Mandatory Error Scenarios
1. **Missing API Key**: Immediate termination with clear error message
2. **Invalid API Key**: Immediate termination with validation details
3. **Demo Key Detection**: Immediate termination with security violation notice
4. **API Rate Limiting**: Implement exponential backoff, never proceed without valid API
5. **Authentication Failure**: Log error and terminate, never use fallback keys

#### Error Response Templates
```python
# REQUIRED ERROR RESPONSES - NO EXCEPTIONS
if not api_key:
    raise ValueError(f"{api_key_name} environment variable is required - cannot proceed with ingestion")

if 'DEMO' in api_key.upper():
    raise ValueError(f"Demo key detected in {api_key_name} - real API key required for production ingestion")

if response.status_code == 401:
    raise ValueError(f"API authentication failed for {service} - check {api_key_name} environment variable")
```

### Agent Compliance Monitoring

#### Automated Compliance Checks
- ✅ All scripts must import and use `ingestion_config.validate_all_api_keys()`
- ✅ All API calls must use environment variables, never hardcoded keys
- ✅ All ingestion must run in production mode for real data
- ✅ All error handling must terminate on API key failures
- ✅ All logging must not expose actual API key values

#### Violation Reporting
Any agent that detects API key violations must:
1. Immediately terminate the process
2. Log the violation with details
3. Report to security enforcement agent
4. Prevent any data access until compliance is restored

### Agent Success Criteria

#### Mandatory Success Metrics
- **API Key Validation**: 100% success rate before any ingestion
- **Real Key Usage**: 0% tolerance for demo/placeholder keys
- **Environment Compliance**: 100% usage of environment variables
- **Error Handling**: 100% termination on API key failures
- **Audit Trail**: Complete logging of all API key usage

#### Performance Requirements
- **Validation Speed**: API key validation must complete within 5 seconds
- **Error Response**: Must terminate within 1 second of detecting invalid keys
- **Monitoring**: Real-time API quota and rate limit tracking
- **Compliance**: 100% adherence to all API key enforcement rules

---

## 🔒 SECURITY MANDATE

**THIS DOCUMENT CONTAINS MANDATORY SECURITY REQUIREMENTS**

**VIOLATION OF THESE RULES CONSTITUTES A SECURITY BREACH**

**ALL AGENTS MUST COMPLY - NO EXCEPTIONS**

**API KEYS MUST BE USED FOR EVERY SINGLE API CALL - ALWAYS**
