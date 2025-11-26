#!/usr/bin/env python3
"""
Multi-Agent Orchestration Framework

This framework coordinates multiple sub-agents for parallel data ingestion
while maintaining proper synchronization, error handling, and progress tracking.
"""

import os
import sys
import json
import asyncio
import subprocess
import threading
import time
import signal
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
from pathlib import Path

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class AgentStatus(Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentTask:
    """Individual agent task definition"""
    agent_id: str
    phase_number: int
    script_path: str
    arguments: List[str]
    dependencies: List[str]
    max_retries: int = 3
    timeout_seconds: int = 3600
    priority: int = 0
    parallel_group: Optional[str] = None

@dataclass
class AgentResult:
    """Result from agent execution"""
    agent_id: str
    status: AgentStatus
    start_time: datetime
    end_time: Optional[datetime]
    exit_code: int
    output: str
    error: Optional[str]
    retry_count: int = 0

class Orchestrator:
    """Multi-agent orchestration system"""

    def __init__(self):
        self.orchestration_start = datetime.now()
        self.agents: Dict[str, AgentTask] = {}
        self.results: Dict[str, AgentResult] = {}
        self.running_agents: Dict[str, subprocess.Popen] = {}
        self.completed_dependencies: Dict[str, bool] = {}
        self.max_concurrent_agents = 4
        self.shutdown_requested = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Validate environment
        self._validate_environment()

    def _validate_environment(self):
        """Validate orchestration environment"""
        print("🔍 Validating orchestration environment...")

        # Check API keys
        key_validation = validate_all_api_keys()
        if not key_validation['valid']:
            raise ValueError("API key validation failed - cannot orchestrate")

        # Check production mode
        mode = get_ingestion_mode_from_env()
        if mode.value != 'production':
            raise ValueError("Production mode required for orchestration")

        print("✅ Environment validated for orchestration")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        self._shutdown_all_agents()

    def register_agent(self, task: AgentTask):
        """Register an agent task"""
        self.agents[task.agent_id] = task
        self.results[task.agent_id] = AgentResult(
            agent_id=task.agent_id,
            status=AgentStatus.PENDING,
            start_time=datetime.now(),
            end_time=None,
            exit_code=-1,
            output="",
            error=None
        )

        print(f"📝 Registered agent: {task.agent_id} (Phase {task.phase_number})")

    def _get_default_agents(self) -> List[AgentTask]:
        """Get default agent configuration"""
        return [
            AgentTask(
                agent_id="validation_agent",
                phase_number=1,
                script_path="scripts/ingestion_phase_1_validation.py",
                arguments=["--save"],
                dependencies=[],
                timeout_seconds=300,
                priority=10
            ),
            AgentTask(
                agent_id="congress_members_agent",
                phase_number=2,
                script_path="scripts/ingestion_phase_2_congress_members.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=1800,
                priority=8,
                parallel_group="data_ingestion"
            ),
            AgentTask(
                agent_id="congress_bills_agent",
                phase_number=3,
                script_path="scripts/ingestion_phase_3_congress_bills.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=3600,
                priority=7,
                parallel_group="data_ingestion"
            ),
            AgentTask(
                agent_id="govinfo_bills_agent",
                phase_number=4,
                script_path="scripts/ingestion_phase_4_govinfo_bills.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=5400,
                priority=6,
                parallel_group="data_ingestion"
            ),
            AgentTask(
                agent_id="openstates_agent",
                phase_number=5,
                script_path="scripts/ingestion_phase_5_openstates.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=7200,
                priority=5,
                parallel_group="data_ingestion"
            ),
            AgentTask(
                agent_id="verification_agent",
                phase_number=6,
                script_path="scripts/ingestion_phase_6_verification.py",
                arguments=["--save"],
                dependencies=["congress_members_agent", "congress_bills_agent",
                           "govinfo_bills_agent", "openstates_agent"],
                timeout_seconds=600,
                priority=1
            )
        ]

    def _dependencies_satisfied(self, agent_id: str) -> bool:
        """Check if agent dependencies are satisfied"""
        agent = self.agents[agent_id]

        for dep_id in agent.dependencies:
            if dep_id not in self.completed_dependencies:
                return False
            if not self.completed_dependencies[dep_id]:
                return False

        return True

    def _execute_agent(self, agent_id: str) -> AgentResult:
        """Execute a single agent"""
        agent = self.agents[agent_id]
        result = self.results[agent_id]

        print(f"🚀 Starting agent: {agent_id} (Phase {agent.phase_number})")

        start_time = datetime.now()
        result.status = AgentStatus.RUNNING
        result.start_time = start_time

        try:
            # Build command
            cmd = ["python", agent.script_path] + agent.arguments
            cmd_str = " ".join(cmd)

            print(f"📋 Executing: {cmd_str}")

            # Execute with timeout
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            self.running_agents[agent_id] = process

            try:
                stdout, stderr = process.communicate(timeout=agent.timeout_seconds)
                exit_code = process.returncode

                result.output = stdout
                result.error = stderr if stderr else None
                result.exit_code = exit_code
                result.end_time = datetime.now()

                if exit_code == 0:
                    result.status = AgentStatus.COMPLETED
                    self.completed_dependencies[agent_id] = True
                    print(f"✅ Agent {agent_id} completed successfully")
                else:
                    result.status = AgentStatus.FAILED
                    print(f"❌ Agent {agent_id} failed with exit code {exit_code}")
                    if stderr:
                        print(f"   Error: {stderr.strip()}")

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

                result.status = AgentStatus.FAILED
                result.error = f"Process timed out after {agent.timeout_seconds} seconds"
                result.end_time = datetime.now()
                result.exit_code = -1

                print(f"⏰ Agent {agent_id} timed out")

            finally:
                if agent_id in self.running_agents:
                    del self.running_agents[agent_id]

        except Exception as e:
            result.status = AgentStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            result.exit_code = -1

            print(f"❌ Agent {agent_id} failed with exception: {e}")

        return result

    def _retry_agent(self, agent_id: str) -> bool:
        """Retry a failed agent"""
        agent = self.agents[agent_id]
        result = self.results[agent_id]

        if result.retry_count >= agent.max_retries:
            print(f"🚫 Agent {agent_id} max retries ({agent.max_retries}) exceeded")
            return False

        result.retry_count += 1
        print(f"🔄 Retrying agent {agent_id} (attempt {result.retry_count}/{agent.max_retries})")

        # Reset result for retry
        result.status = AgentStatus.PENDING
        result.output = ""
        result.error = None
        result.exit_code = -1

        return True

    def _get_ready_agents(self) -> List[str]:
        """Get agents that are ready to run"""
        ready_agents = []

        for agent_id, agent in self.agents.items():
            result = self.results[agent_id]

            # Skip if already completed or running
            if result.status in [AgentStatus.COMPLETED, AgentStatus.RUNNING]:
                continue

            # Check dependencies
            if not self._dependencies_satisfied(agent_id):
                continue

            ready_agents.append(agent_id)

        # Sort by priority (higher priority first)
        ready_agents.sort(key=lambda aid: self.agents[aid].priority, reverse=True)

        return ready_agents

    def _get_parallel_groups(self, ready_agents: List[str]) -> Dict[str, List[str]]:
        """Group agents by parallel execution capability"""
        groups = {}

        for agent_id in ready_agents:
            agent = self.agents[agent_id]
            group_name = agent.parallel_group or f"serial_{agent_id}"

            if group_name not in groups:
                groups[group_name] = []

            groups[group_name].append(agent_id)

        return groups

    def orchestrate_sequential(self) -> Dict[str, Any]:
        """Orchestrate agents in sequential mode"""
        print("\n" + "="*60)
        print("🔄 SEQUENTIAL ORCHESTRATION MODE")
        print("="*60)

        while True:
            ready_agents = self._get_ready_agents()

            if not ready_agents:
                # Check if all agents are completed
                all_completed = all(
                    self.results[aid].status == AgentStatus.COMPLETED
                    for aid in self.agents.keys()
                )

                if all_completed:
                    print("✅ All agents completed successfully")
                    break

                # Check if any agents can still run
                any_pending = any(
                    self.results[aid].status in [AgentStatus.PENDING, AgentStatus.FAILED]
                    for aid in self.agents.keys()
                )

                if not any_pending:
                    print("⚠️  Orchestration stuck - no agents ready to run")
                    break

                # Wait and retry
                time.sleep(5)
                continue

            # Execute the highest priority ready agent
            agent_id = ready_agents[0]
            self._execute_agent(agent_id)

            # Handle retries if needed
            result = self.results[agent_id]
            if result.status == AgentStatus.FAILED:
                if self._retry_agent(agent_id):
                    continue  # Retry immediately
                else:
                    print(f"❌ Agent {agent_id} failed permanently")

        return self._generate_orchestration_report("sequential")

    def orchestrate_parallel(self) -> Dict[str, Any]:
        """Orchestrate agents in parallel mode"""
        print("\n" + "="*60)
        print("⚡ PARALLEL ORCHESTRATION MODE")
        print("="*60)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_agents) as executor:
            futures = {}

            while True:
                ready_agents = self._get_ready_agents()

                if not ready_agents and not futures:
                    # Check if all agents are completed
                    all_completed = all(
                        self.results[aid].status == AgentStatus.COMPLETED
                        for aid in self.agents.keys()
                    )

                    if all_completed:
                        print("✅ All agents completed successfully")
                        break

                    # Check if any agents can still run
                    any_pending = any(
                        self.results[aid].status in [AgentStatus.PENDING, AgentStatus.FAILED]
                        for aid in self.agents.keys()
                    )

                    if not any_pending:
                        print("⚠️  Orchestration stuck - no agents ready to run")
                        break

                    # Wait and retry
                    time.sleep(5)
                    continue

                # Get parallel groups
                groups = self._get_parallel_groups(ready_agents)

                # Submit one agent from each parallel group
                for group_name, group_agents in groups.items():
                    if len(futures) >= self.max_concurrent_agents:
                        break

                    # Find first agent in group that's not already running
                    for agent_id in group_agents:
                        if agent_id not in futures and self.results[agent_id].status == AgentStatus.PENDING:
                            future = executor.submit(self._execute_agent, agent_id)
                            futures[future] = agent_id
                            break

                # Wait for at least one agent to complete
                if futures:
                    completed_futures = []
                    for future in concurrent.futures.as_completed(futures, timeout=10):
                        agent_id = futures[future]
                        result = future.result()

                        # Handle retries
                        if result.status == AgentStatus.FAILED:
                            if self._retry_agent(agent_id):
                                # Resubmit for retry
                                new_future = executor.submit(self._execute_agent, agent_id)
                                futures[new_future] = agent_id

                        completed_futures.append(future)
                        break  # Only wait for one completion at a time

                    # Remove completed futures
                    for future in completed_futures:
                        del futures[future]

                # Check for shutdown
                if self.shutdown_requested:
                    print("🛑 Shutdown requested, cancelling remaining agents...")
                    for future in futures:
                        future.cancel()
                    break

        return self._generate_orchestration_report("parallel")

    def _shutdown_all_agents(self):
        """Shutdown all running agents"""
        print("🛑 Shutting down all running agents...")

        for agent_id, process in self.running_agents.items():
            try:
                process.terminate()
                process.wait(timeout=10)
                print(f"✅ Agent {agent_id} terminated")
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                print(f"🔫 Agent {agent_id} killed")
            except Exception as e:
                print(f"❌ Error terminating agent {agent_id}: {e}")

        self.running_agents.clear()

    def _generate_orchestration_report(self, mode: str) -> Dict[str, Any]:
        """Generate comprehensive orchestration report"""
        end_time = datetime.now()
        duration = (end_time - self.orchestration_start).total_seconds()

        # Calculate statistics
        total_agents = len(self.agents)
        completed_agents = sum(1 for r in self.results.values() if r.status == AgentStatus.COMPLETED)
        failed_agents = sum(1 for r in self.results.values() if r.status == AgentStatus.FAILED)

        # Get agent details
        agent_details = {}
        for agent_id, result in self.results.items():
            agent = self.agents[agent_id]
            agent_details[agent_id] = {
                'phase': agent.phase_number,
                'script': agent.script_path,
                'status': result.status.value,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat() if result.end_time else None,
                'duration_seconds': (result.end_time - result.start_time).total_seconds() if result.end_time else None,
                'exit_code': result.exit_code,
                'retry_count': result.retry_count,
                'output_preview': result.output[:500] if result.output else None,
                'error': result.error
            }

        report = {
            'orchestration_mode': mode,
            'start_time': self.orchestration_start.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'total_agents': total_agents,
            'completed_agents': completed_agents,
            'failed_agents': failed_agents,
            'success_rate': (completed_agents / total_agents * 100) if total_agents > 0 else 0,
            'max_concurrent_agents': self.max_concurrent_agents,
            'agent_details': agent_details,
            'overall_status': 'SUCCESS' if failed_agents == 0 else 'PARTIAL_SUCCESS' if completed_agents > 0 else 'FAILURE'
        }

        return report

    def orchestrate(self, mode: str = "parallel", max_concurrent: int = 4) -> Dict[str, Any]:
        """Main orchestration method"""
        print("\n" + "="*80)
        print("🚀 MULTI-AGENT DATA INGESTION ORCHESTRATION")
        print("="*80)

        self.max_concurrent_agents = max_concurrent

        # Register default agents if none registered
        if not self.agents:
            default_agents = self._get_default_agents()
            for agent in default_agents:
                self.register_agent(agent)

        print(f"📊 Registered {len(self.agents)} agents")
        print(f"⚡ Orchestration mode: {mode}")
        print(f"🔢 Max concurrent agents: {max_concurrent}")

        # Run orchestration
        if mode == "sequential":
            report = self.orchestrate_sequential()
        else:
            report = self.orchestrate_parallel()

        # Print final summary
        print("\n" + "="*80)
        print(f"🏁 ORCHESTRATION COMPLETE: {report['overall_status']}")
        print(f"📊 Success Rate: {report['success_rate']:.1f}%")
        print(f"✅ Completed: {report['completed_agents']}/{report['total_agents']}")
        print(f"❌ Failed: {report['failed_agents']}/{report['total_agents']}")
        print(f"⏱️  Duration: {report['duration_seconds']:.1f} seconds")
        print("="*80)

        return report

    def save_orchestration_report(self, filename: str = None, mode: str = "parallel") -> str:
        """Save orchestration report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"orchestration_report_{mode}_{timestamp}.json"

        report = self.orchestrate(mode)

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"📄 Orchestration report saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving orchestration report: {e}")
            return ""

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Agent Orchestration Framework')
    parser.add_argument('--mode', '-m', choices=['sequential', 'parallel'],
                       default='parallel', help='Orchestration mode')
    parser.add_argument('--max-concurrent', '-c', type=int, default=4,
                       help='Maximum concurrent agents (parallel mode only)')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save report to file')

    args = parser.parse_args()

    try:
        orchestrator = Orchestrator()

        if args.save:
            orchestrator.save_orchestration_report(args.output, args.mode)
        else:
            orchestrator.orchestrate(args.mode, args.max_concurrent)

    except Exception as e:
        print(f"❌ Orchestration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
