# 🚀 Multi-Agent Orchestration Guide

## 📋 **OVERVIEW**

This guide explains how to use the multi-agent orchestration system to coordinate parallel data ingestion across multiple AI agents while maintaining proper synchronization, error handling, and progress tracking.

---

## 🏗️ **ORCHESTRATION ARCHITECTURE**

### **Core Components**

1. **Orchestrator Framework** (`orchestrator_framework.py`)
   - Manages agent lifecycle and dependencies
   - Handles parallel/sequential execution modes
   - Provides retry logic and error recovery
   - Generates comprehensive reports

2. **Sub-Agent Manager** (`subagent_manager.py`)
   - Manages individual sub-agent communication
   - Handles task assignment and monitoring
   - Provides heartbeat monitoring
   - Supports WebSocket-based communication

3. **Main Runner** (`run_orchestrated_ingestion.py`)
   - Simple interface for running orchestrations
   - Interactive menu system
   - Environment validation
   - Demo modes for testing

---

## 🎯 **EXECUTION MODES**

### **1. Interactive Mode** (Recommended for first-time users)
```bash
python scripts/run_orchestrated_ingestion.py --mode interactive
```

**Features:**
- 📋 Menu-driven interface
- 🔍 Environment validation
- 🎮 Demo modes for testing
- 📊 Agent configuration viewing
- 🛑 Graceful shutdown handling

### **2. Sequential Mode**
```bash
python scripts/run_orchestrated_ingestion.py --mode sequential
```

**Characteristics:**
- 🔄 One agent at a time
- 🔒 Maximum resource utilization
- 📊 Easy debugging
- ⏱️ Longer execution time (~2-4 hours)

### **3. Parallel Mode** (Recommended for production)
```bash
python scripts/run_orchestrated_ingestion.py --mode parallel --max-concurrent 4
```

**Characteristics:**
- ⚡ Multiple agents simultaneously
- 🚀 Faster execution (~1-2 hours)
- 📊 Resource monitoring
- 🔧 Complex dependency management

### **4. Demo Modes**
```bash
# Sequential demo (simulated execution)
python scripts/run_orchestrated_ingestion.py --mode demo-sequential

# Parallel demo (simulated execution)
python scripts/run_orchestrated_ingestion.py --mode demo-parallel
```

**Purpose:**
- 🎮 Test orchestration logic
- 📊 Verify agent configuration
- 🕐 Quick validation without real API calls
- 🔍 Debug dependency resolution

---

## 🤖 **AGENT CONFIGURATION**

### **Default Agent Setup**

| Agent ID | Phase | Script | Dependencies | Parallel Group | Priority |
|----------|-------|--------|--------------|----------------|----------|
| `validation_agent` | 1 | `ingestion_phase_1_validation.py` | None | Serial | 10 |
| `congress_members_agent` | 2 | `ingestion_phase_2_congress_members.py` | validation_agent | data_ingestion | 8 |
| `congress_bills_agent` | 3 | `ingestion_phase_3_congress_bills.py` | validation_agent | data_ingestion | 7 |
| `govinfo_bills_agent` | 4 | `ingestion_phase_4_govinfo_bills.py` | validation_agent | data_ingestion | 6 |
| `openstates_agent` | 5 | `ingestion_phase_5_openstates.py` | validation_agent | data_ingestion | 5 |
| `verification_agent` | 6 | `ingestion_phase_6_verification.py` | All data agents | Serial | 1 |

### **Parallel Groups**

- **Serial**: Must run alone (validation, verification)
- **data_ingestion**: Can run in parallel after validation

### **Priority System**
- Higher numbers = higher priority
- Used for conflict resolution
- Determines execution order in sequential mode

---

## 🔄 **EXECUTION FLOW**

### **Sequential Mode Flow**
```
1. validation_agent (Phase 1)
   ↓
2. congress_members_agent (Phase 2)
   ↓
3. congress_bills_agent (Phase 3)
   ↓
4. govinfo_bills_agent (Phase 4)
   ↓
5. openstates_agent (Phase 5)
   ↓
6. verification_agent (Phase 6)
```

### **Parallel Mode Flow**
```
1. validation_agent (Phase 1) - Serial
   ↓
2. [congress_members_agent, congress_bills_agent,
    govinfo_bills_agent, openstates_agent] - Parallel
   ↓
3. verification_agent (Phase 6) - Serial
```

---

## 📊 **MONITORING & REPORTING**

### **Real-time Monitoring**
- 📊 Agent status updates
- 🔄 Progress tracking
- ❌ Error reporting
- ⏱️ Execution timing
- 🔄 Retry attempts

### **Comprehensive Reports**
Each orchestration generates:
- 📈 Overall success statistics
- 📊 Individual agent performance
- ⏱️ Timing analysis
- ❌ Error details
- 🔄 Retry history
- 📄 JSON report file

### **Report Structure**
```json
{
  "orchestration_mode": "parallel",
  "start_time": "2025-11-23T10:30:00",
  "end_time": "2025-11-23T12:15:00",
  "duration_seconds": 6300,
  "total_agents": 6,
  "completed_agents": 5,
  "failed_agents": 1,
  "success_rate": 83.3,
  "agent_details": {...},
  "overall_status": "PARTIAL_SUCCESS"
}
```

---

## 🛠️ **CUSTOMIZATION**

### **Adding New Agents**

1. **Create Agent Task**
```python
from orchestrator_framework import AgentTask

new_agent = AgentTask(
    agent_id="custom_agent",
    phase_number=7,
    script_path="scripts/custom_phase.py",
    arguments=["--save"],
    dependencies=["validation_agent"],
    timeout_seconds=1800,
    priority=4,
    parallel_group="data_ingestion"
)
```

2. **Register with Orchestrator**
```python
orchestrator = Orchestrator()
orchestrator.register_agent(new_agent)
```

### **Modifying Execution Parameters**

```python
# Custom orchestration
orchestrator = Orchestrator()
orchestrator.max_concurrent_agents = 8  # More parallelism
orchestrator.orchestrate("parallel", max_concurrent=8)
```

### **Custom Retry Logic**
```python
# Modify agent task for more retries
agent.max_retries = 5
agent.timeout_seconds = 7200  # 2 hours
```

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

#### **Environment Validation Failures**
```bash
❌ API key validation failed
```
**Solution**: Check `.env` file for valid API keys

#### **Database Connectivity Issues**
```bash
❌ Database connectivity failed
```
**Solution**: Verify PostgreSQL is running and accessible

#### **Agent Timeouts**
```bash
⏰ Agent timed out after 3600 seconds
```
**Solution**: Increase timeout or check network connectivity

#### **Dependency Resolution**
```bash
⚠️ Orchestration stuck - no agents ready to run
```
**Solution**: Check if dependencies completed successfully

### **Debug Mode**
```bash
# Run with detailed logging
python scripts/run_orchestrated_ingestion.py --mode sequential --validate

# Check individual agent logs
ls -la orchestration_report_*.json
cat orchestration_report_*.json | jq '.agent_details'
```

### **Recovery from Failures**
1. **Identify failed agents** from report
2. **Fix underlying issues** (API keys, network, etc.)
3. **Rerun specific phases** if needed
4. **Continue with verification**

---

## 📈 **PERFORMANCE OPTIMIZATION**

### **Parallel Execution Tuning**
```bash
# Conservative (stable)
python scripts/run_orchestrated_ingestion.py --mode parallel --max-concurrent 2

# Balanced (recommended)
python scripts/run_orchestrated_ingestion.py --mode parallel --max-concurrent 4

# Aggressive (fastest)
python scripts/run_orchestrated_ingestion.py --mode parallel --max-concurrent 8
```

### **Resource Monitoring**
- 🖥️ **CPU Usage**: Monitor during parallel execution
- 💾 **Memory Usage**: Each agent uses ~100-200MB
- 🌐 **Network**: API rate limiting prevents overload
- 💽 **Disk**: ~1GB space required for all data

### **Expected Performance**
| Mode | Execution Time | Resource Usage | Complexity |
|------|----------------|----------------|------------|
| Sequential | 2-4 hours | Low | Simple |
| Parallel (2 agents) | 1.5-3 hours | Medium | Moderate |
| Parallel (4 agents) | 1-2 hours | High | Complex |
| Parallel (8 agents) | 45-90 minutes | Very High | Complex |

---

## 🎯 **BEST PRACTICES**

### **Before Running**
1. ✅ Validate environment: `--validate --quick-validate`
2. ✅ Check API quotas and rate limits
3. ✅ Ensure sufficient disk space
4. ✅ Test with demo mode first

### **During Execution**
1. 📊 Monitor agent progress
2. 🔄 Check for retry attempts
3. ⏱️ Watch for timeout warnings
4. 🛑 Use Ctrl+C for graceful shutdown

### **After Execution**
1. 📄 Review orchestration report
2. 🔍 Check verification results
3. 📊 Analyze performance metrics
4. 🗂️ Archive report files

---

## 🚀 **QUICK START**

### **First Time Setup**
```bash
# 1. Validate environment
python scripts/run_orchestrated_ingestion.py --validate --quick-validate

# 2. Test with demo
python scripts/run_orchestrated_ingestion.py --mode demo-parallel

# 3. Run interactive mode
python scripts/run_orchestrated_ingestion.py --mode interactive
```

### **Production Run**
```bash
# Full parallel orchestration
python scripts/run_orchestrated_ingestion.py --mode parallel --max-concurrent 4 --save-report
```

### **Development/Testing**
```bash
# Sequential for easier debugging
python scripts/run_orchestrated_ingestion.py --mode sequential --save-report
```

---

## 📞 **SUPPORT**

### **Getting Help**
1. 📋 Check orchestration report for error details
2. 🔍 Review individual agent logs
3. 📊 Monitor system resources during execution
4. 🎮 Use demo mode to test configuration

### **Report Issues**
Include in bug reports:
- 📄 Orchestration report JSON
- 🔍 Environment validation output
- 📊 System resource usage
- 🎯 Exact command line used

---

**🎉 This orchestration system enables efficient, scalable multi-agent data ingestion with comprehensive monitoring and error handling.**
