#!/usr/bin/env python3
"""
Enhanced Multi-Agent Orchestration Framework

This enhanced orchestrator integrates with existing infrastructure including:
- Existing verification scripts (verify_complete_ingestion.py)
- Data status queries (data_status_queries.py)
- Monitoring infrastructure (job_monitor.py)
- Existing ingestion managers
- Complete bulk ingestion orchestrator
"""

import concurrent.futures
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from complete_bulk_ingestion import BulkIngestionOrchestrator
from data_status_queries import DataStatusDiagnostics

# Load environment variables
from dotenv import load_dotenv
from ingestion_config import get_ingestion_mode_from_env, validate_all_api_keys

# Import existing components
from verify_complete_ingestion import IngestionVerifier

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    use_existing_infrastructure: bool = False

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
    verification_results: Optional[Dict[str, Any]] = None

class EnhancedOrchestrator:
    """Enhanced multi-agent orchestration system with existing infrastructure integration"""

    def __init__(self):
        self.orchestration_start = datetime.now()
        self.agents: Dict[str, AgentTask] = {}
        self.results: Dict[str, AgentResult] = {}
        self.running_agents: Dict[str, subprocess.Popen] = {}
        self.completed_dependencies: Dict[str, bool] = {}
        self.max_concurrent_agents = 4
        self.shutdown_requested = False

        # Existing infrastructure components
        self.ingestion_verifier = None
        self.data_diagnostics = None
        self.bulk_orchestrator = None

        # Monitoring
        self.monitoring_log_path = Path(f"orchestration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.monitoring_thread = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize logging
        self._setup_logging()

        # Validate environment
        self._validate_environment()

    def _setup_logging(self):
        """Setup comprehensive logging"""
        self.logger = logging.getLogger(f"orchestrator_{id(self)}")

        # File handler for orchestration logs
        file_handler = logging.FileHandler(self.monitoring_log_path)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        self.logger.info("Enhanced orchestrator initialized")

    def _validate_environment(self):
        """Validate orchestration environment"""
        self.logger.info("Validating orchestration environment...")

        # Check API keys
        key_validation = validate_all_api_keys()
        if not key_validation['valid']:
            error_msg = "API key validation failed - cannot orchestrate"
            self.logger.error(error_msg)
            for error in key_validation['errors']:
                self.logger.error(f"  - {error}")
            raise ValueError(error_msg)

        # Check production mode
        mode = get_ingestion_mode_from_env()
        if mode.value != 'production':
            error_msg = f"Production mode required for orchestration, got {mode.value}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Initialize existing infrastructure
        try:
            self.ingestion_verifier = IngestionVerifier()
            self.data_diagnostics = DataStatusDiagnostics()
            self.bulk_orchestrator = BulkIngestionOrchestrator()
            self.logger.info("Existing infrastructure components initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize some existing components: {e}")

        self.logger.info("Environment validated for orchestration")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
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

        self.logger.info(f"Registered agent: {task.agent_id} (Phase {task.phase_number})")

    def _get_enhanced_agents(self) -> List[AgentTask]:
        """Get enhanced agent configuration with existing infrastructure integration"""
        return [
            AgentTask(
                agent_id="validation_agent",
                phase_number=1,
                script_path="scripts/ingestion_phase_1_validation.py",
                arguments=["--save"],
                dependencies=[],
                timeout_seconds=300,
                priority=10,
                use_existing_infrastructure=True
            ),
            AgentTask(
                agent_id="congress_members_agent",
                phase_number=2,
                script_path="scripts/ingestion_phase_2_congress_members.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=1800,
                priority=8,
                parallel_group="data_ingestion",
                use_existing_infrastructure=True
            ),
            AgentTask(
                agent_id="congress_bills_agent",
                phase_number=3,
                script_path="scripts/ingestion_phase_3_congress_bills.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=3600,
                priority=7,
                parallel_group="data_ingestion",
                use_existing_infrastructure=True
            ),
            AgentTask(
                agent_id="govinfo_bills_agent",
                phase_number=4,
                script_path="scripts/ingestion_phase_4_govinfo_bills.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=5400,
                priority=6,
                parallel_group="data_ingestion",
                use_existing_infrastructure=True
            ),
            AgentTask(
                agent_id="openstates_agent",
                phase_number=5,
                script_path="scripts/ingestion_phase_5_openstates.py",
                arguments=["--save"],
                dependencies=["validation_agent"],
                timeout_seconds=7200,
                priority=5,
                parallel_group="data_ingestion",
                use_existing_infrastructure=True
            ),
            AgentTask(
                agent_id="verification_agent",
                phase_number=6,
                script_path="scripts/ingestion_phase_6_verification.py",
                arguments=["--save"],
                dependencies=["congress_members_agent", "congress_bills_agent",
                           "govinfo_bills_agent", "openstates_agent"],
                timeout_seconds=600,
                priority=1,
                use_existing_infrastructure=True
            ),
            # Additional agents using existing infrastructure
            AgentTask(
                agent_id="legacy_verification_agent",
                phase_number=7,
                script_path="scripts/verify_complete_ingestion.py",
                arguments=[],
                dependencies=["verification_agent"],
                timeout_seconds=300,
                priority=0,
                use_existing_infrastructure=True
            ),
            AgentTask(
                agent_id="data_diagnostics_agent",
                phase_number=8,
                script_path="scripts/data_status_queries.py",
                arguments=[],
                dependencies=["legacy_verification_agent"],
                timeout_seconds=300,
                priority=0,
                use_existing_infrastructure=True
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

    def _execute_agent_with_monitoring(self, agent_id: str) -> AgentResult:
        """Execute a single agent with enhanced monitoring"""
        agent = self.agents[agent_id]
        result = self.results[agent_id]

        self.logger.info(f"Starting agent: {agent_id} (Phase {agent.phase_number})")

        start_time = datetime.now()
        result.status = AgentStatus.RUNNING
        result.start_time = start_time

        try:
            # Build command
            cmd = ["python", agent.script_path] + agent.arguments
            cmd_str = " ".join(cmd)

            self.logger.info(f"Executing: {cmd_str}")

            # Execute with timeout and enhanced monitoring
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

                # Enhanced verification for specific agents
                if agent.use_existing_infrastructure and exit_code == 0:
                    result.verification_results = self._run_enhanced_verification(agent_id, agent.phase_number)

                if exit_code == 0:
                    result.status = AgentStatus.COMPLETED
                    self.completed_dependencies[agent_id] = True
                    self.logger.info(f"Agent {agent_id} completed successfully")

                    # Log verification results if available
                    if result.verification_results:
                        self.logger.info(f"Verification results for {agent_id}: {result.verification_results}")
                else:
                    result.status = AgentStatus.FAILED
                    self.logger.error(f"Agent {agent_id} failed with exit code {exit_code}")
                    if stderr:
                        self.logger.error(f"Error output: {stderr.strip()}")

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

                result.status = AgentStatus.FAILED
                result.error = f"Process timed out after {agent.timeout_seconds} seconds"
                result.end_time = datetime.now()
                result.exit_code = -1

                self.logger.error(f"Agent {agent_id} timed out after {agent.timeout_seconds} seconds")

            finally:
                if agent_id in self.running_agents:
                    del self.running_agents[agent_id]

        except Exception as e:
            result.status = AgentStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            result.exit_code = -1

            self.logger.error(f"Agent {agent_id} failed with exception: {e}")

        return result

    def _run_enhanced_verification(self, agent_id: str, phase_number: int) -> Optional[Dict[str, Any]]:
        """Run enhanced verification using existing infrastructure"""
        try:
            verification_results = {}

            # Use existing verification components based on phase
            if phase_number in [6, 7]:  # Verification phases
                if self.ingestion_verifier:
                    self.logger.info(f"Running enhanced verification for {agent_id}")
                    # Run verification queries
                    verification_results['checkpoint_status'] = self._run_checkpoint_verification()
                    verification_results['data_integrity'] = self._run_data_integrity_check()

            if phase_number == 8:  # Data diagnostics
                if self.data_diagnostics:
                    self.logger.info(f"Running comprehensive data diagnostics for {agent_id}")
                    verification_results['data_status'] = self._run_data_diagnostics()

            return verification_results

        except Exception as e:
            self.logger.warning(f"Enhanced verification failed for {agent_id}: {e}")
            return None

    def _run_checkpoint_verification(self) -> Dict[str, Any]:
        """Run checkpoint verification using existing infrastructure"""
        try:
            if self.ingestion_verifier:
                return self.ingestion_verifier.get_checkpoint_status()
        except Exception as e:
            self.logger.warning(f"Checkpoint verification failed: {e}")
        return {}

    def _run_data_integrity_check(self) -> Dict[str, Any]:
        """Run data integrity check using existing infrastructure"""
        try:
            if self.ingestion_verifier:
                return self.ingestion_verifier.get_data_integrity_metrics()
        except Exception as e:
            self.logger.warning(f"Data integrity check failed: {e}")
        return {}

    def _run_data_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive data diagnostics"""
        try:
            if self.data_diagnostics:
                return self.data_diagnostics.generate_comprehensive_report()
        except Exception as e:
            self.logger.warning(f"Data diagnostics failed: {e}")
        return {}

    def _retry_agent(self, agent_id: str) -> bool:
        """Retry a failed agent"""
        agent = self.agents[agent_id]
        result = self.results[agent_id]

        if result.retry_count >= agent.max_retries:
            self.logger.error(f"Agent {agent_id} max retries ({agent.max_retries}) exceeded")
            return False

        result.retry_count += 1
        self.logger.info(f"Retrying agent {agent_id} (attempt {result.retry_count}/{agent.max_retries})")

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

    def _start_monitoring(self):
        """Start background monitoring"""
        def monitor():
            while not self.shutdown_requested:
                try:
                    # Check for errors in log file
                    if self.monitoring_log_path.exists():
                        from monitoring.job_monitor import check_log
                        alerts = check_log(self.monitoring_log_path)
                        if alerts > 0:
                            self.logger.warning(f"Found {alerts} alerts in monitoring log")

                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(60)

        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Background monitoring started")

    def orchestrate_sequential(self) -> Dict[str, Any]:
        """Orchestrate agents in sequential mode with enhanced monitoring"""
        self.logger.info("Starting sequential orchestration mode")
        self._start_monitoring()

        while True:
            ready_agents = self._get_ready_agents()

            if not ready_agents:
                # Check if all agents are completed
                all_completed = all(
                    self.results[aid].status == AgentStatus.COMPLETED
                    for aid in self.agents.keys()
                )

                if all_completed:
                    self.logger.info("All agents completed successfully")
                    break

                # Check if any agents can still run
                any_pending = any(
                    self.results[aid].status in [AgentStatus.PENDING, AgentStatus.FAILED]
                    for aid in self.agents.keys()
                )

                if not any_pending:
                    self.logger.warning("Orchestration stuck - no agents ready to run")
                    break

                # Wait and retry
                time.sleep(5)
                continue

            # Execute the highest priority ready agent
            agent_id = ready_agents[0]
            self._execute_agent_with_monitoring(agent_id)

            # Handle retries if needed
            result = self.results[agent_id]
            if result.status == AgentStatus.FAILED:
                if self._retry_agent(agent_id):
                    continue  # Retry immediately
                else:
                    self.logger.error(f"Agent {agent_id} failed permanently")

        return self._generate_enhanced_report("sequential")

    def orchestrate_parallel(self) -> Dict[str, Any]:
        """Orchestrate agents in parallel mode with enhanced monitoring"""
        self.logger.info("Starting parallel orchestration mode")
        self._start_monitoring()

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
                        self.logger.info("All agents completed successfully")
                        break

                    # Check if any agents can still run
                    any_pending = any(
                        self.results[aid].status in [AgentStatus.PENDING, AgentStatus.FAILED]
                        for aid in self.agents.keys()
                    )

                    if not any_pending:
                        self.logger.warning("Orchestration stuck - no agents ready to run")
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
                            future = executor.submit(self._execute_agent_with_monitoring, agent_id)
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
                                new_future = executor.submit(self._execute_agent_with_monitoring, agent_id)
                                futures[new_future] = agent_id

                        completed_futures.append(future)
                        break  # Only wait for one completion at a time

                    # Remove completed futures
                    for future in completed_futures:
                        del futures[future]

                # Check for shutdown
                if self.shutdown_requested:
                    self.logger.warning("Shutdown requested, cancelling remaining agents...")
                    for future in futures:
                        future.cancel()
                    break

        return self._generate_enhanced_report("parallel")

    def _shutdown_all_agents(self):
        """Shutdown all running agents"""
        self.logger.warning("Shutting down all running agents...")

        for agent_id, process in self.running_agents.items():
            try:
                process.terminate()
                process.wait(timeout=10)
                self.logger.info(f"Agent {agent_id} terminated")
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                self.logger.warning(f"Agent {agent_id} killed")
            except Exception as e:
                self.logger.error(f"Error terminating agent {agent_id}: {e}")

        self.running_agents.clear()

    def _generate_enhanced_report(self, mode: str) -> Dict[str, Any]:
        """Generate comprehensive enhanced orchestration report"""
        end_time = datetime.now()
        duration = (end_time - self.orchestration_start).total_seconds()

        # Calculate statistics
        total_agents = len(self.agents)
        completed_agents = sum(1 for r in self.results.values() if r.status == AgentStatus.COMPLETED)
        failed_agents = sum(1 for r in self.results.values() if r.status == AgentStatus.FAILED)

        # Get agent details with verification results
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
                'error': result.error,
                'verification_results': result.verification_results,
                'use_existing_infrastructure': agent.use_existing_infrastructure
            }

        # Generate final verification using existing infrastructure
        final_verification = None
        try:
            if self.ingestion_verifier:
                final_verification = {
                    'checkpoint_status': self._run_checkpoint_verification(),
                    'data_integrity': self._run_data_integrity_check()
                }
        except Exception as e:
            self.logger.warning(f"Final verification failed: {e}")

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
            'final_verification': final_verification,
            'monitoring_log_path': str(self.monitoring_log_path),
            'existing_infrastructure_used': True,
            'overall_status': 'SUCCESS' if failed_agents == 0 else 'PARTIAL_SUCCESS' if completed_agents > 0 else 'FAILURE'
        }

        return report

    def orchestrate(self, mode: str = "parallel", max_concurrent: int = 4) -> Dict[str, Any]:
        """Main orchestration method with existing infrastructure integration"""
        self.logger.info(f"Starting enhanced multi-agent orchestration in {mode} mode")

        self.max_concurrent_agents = max_concurrent

        # Register enhanced agents if none registered
        if not self.agents:
            enhanced_agents = self._get_enhanced_agents()
            for agent in enhanced_agents:
                self.register_agent(agent)

        self.logger.info(f"Registered {len(self.agents)} enhanced agents")
        self.logger.info(f"Max concurrent agents: {max_concurrent}")

        # Run orchestration
        if mode == "sequential":
            report = self.orchestrate_sequential()
        else:
            report = self.orchestrate_parallel()

        # Log final summary
        self.logger.info(f"Orchestration complete: {report['overall_status']}")
        self.logger.info(f"Success rate: {report['success_rate']:.1f}%")
        self.logger.info(f"Completed: {report['completed_agents']}/{report['total_agents']}")
        self.logger.info(f"Duration: {report['duration_seconds']:.1f} seconds")

        return report

    def save_enhanced_report(self, filename: str = None, mode: str = "parallel") -> str:
        """Save enhanced orchestration report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"enhanced_orchestration_report_{mode}_{timestamp}.json"

        report = self.orchestrate(mode)

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            self.logger.info(f"Enhanced orchestration report saved to: {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error saving enhanced orchestration report: {e}")
            return ""

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Multi-Agent Orchestration with Existing Infrastructure')
    parser.add_argument('--mode', '-m', choices=['sequential', 'parallel'],
                       default='parallel', help='Orchestration mode')
    parser.add_argument('--max-concurrent', '-c', type=int, default=4,
                       help='Maximum concurrent agents (parallel mode only)')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save report to file')
    parser.add_argument('--use-existing', action='store_true', default=True,
                       help='Use existing infrastructure components')

    args = parser.parse_args()

    try:
        orchestrator = EnhancedOrchestrator()

        if args.save:
            orchestrator.save_enhanced_report(args.output, args.mode)
        else:
            orchestrator.orchestrate(args.mode, args.max_concurrent)

    except Exception as e:
        logger.error(f"Enhanced orchestration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
