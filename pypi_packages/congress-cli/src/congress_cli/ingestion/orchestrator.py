"""
Orchestrator functions for Congress CLI bulk data ingestion with sophisticated coordination.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..utils.config import get_config
from ..utils.logger import get_logger
from .bulk_ingestor import BulkDataIngestor
from .incremental import IncrementalIngestor


@dataclass
class IngestionPlan:
    """Comprehensive ingestion plan with dependencies and priorities."""

    name: str
    endpoints: List[str]
    dependencies: List[str] = None
    priority: int = 1
    parallel_safe: bool = False
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_minutes: int = 60
    progress_callback: Optional[Callable[[str, int, int], None]] = None


class CongressIngestionOrchestrator:
    """Sophisticated orchestration of Congress data ingestion with dependency management."""

    def __init__(self, config=None):
        """Initialize orchestrator with configuration."""
        self.config = config or get_config()
        self.bulk_ingestor = BulkDataIngestor(config)
        self.incremental_ingestor = IncrementalIngestor(config)
        self.logger = get_logger(__name__)

        # Track orchestration state
        self.orchestration_stats = {
            'start_time': datetime.now(),
            'plans_executed': [],
            'plans_failed': [],
            'total_records': 0,
            'total_errors': 0,
            'current_plan': None
        }

        # Define ingestion plans
        self._setup_ingestion_plans()

    def _setup_ingestion_plans(self):
        """Setup comprehensive ingestion plans with dependencies."""
        self.ingestion_plans = {
            # Foundation plans (must run first)
            'bootstrap_schema': IngestionPlan(
                name="Bootstrap Database Schema",
                endpoints=[],
                dependencies=[],
                priority=1,
                parallel_safe=False,
                timeout_minutes=30
            ),

            'jurisdictions': IngestionPlan(
                name="Load Jurisdictions",
                endpoints=['jurisdictions'],
                dependencies=['bootstrap_schema'],
                priority=2,
                parallel_safe=False,
                timeout_minutes=15
            ),

            # Congress-specific plans
            'congress_118_members': IngestionPlan(
                name="Congress 118 Members",
                endpoints=['members_by_congress'],
                dependencies=['bootstrap_schema'],
                priority=3,
                parallel_safe=False,
                timeout_minutes=45
            ),

            'congress_117_members': IngestionPlan(
                name="Congress 117 Members",
                endpoints=['members_by_congress'],
                dependencies=['bootstrap_schema'],
                priority=4,
                parallel_safe=False,
                timeout_minutes=45
            ),

            'congress_116_members': IngestionPlan(
                name="Congress 116 Members",
                endpoints=['members_by_congress'],
                dependencies=['bootstrap_schema'],
                priority=5,
                parallel_safe=False,
                timeout_minutes=45
            ),

            # Bills plans (depend on members for sponsor relationships)
            'congress_118_bills': IngestionPlan(
                name="Congress 118 Bills",
                endpoints=['bills_by_congress'],
                dependencies=['congress_118_members'],
                priority=6,
                parallel_safe=False,
                timeout_minutes=90
            ),

            'congress_117_bills': IngestionPlan(
                name="Congress 117 Bills",
                endpoints=['bills_by_congress'],
                dependencies=['congress_117_members'],
                priority=7,
                parallel_safe=False,
                timeout_minutes=90
            ),

            'congress_116_bills': IngestionPlan(
                name="Congress 116 Bills",
                endpoints=['bills_by_congress'],
                dependencies=['congress_116_members'],
                priority=8,
                parallel_safe=False,
                timeout_minutes=90
            ),

            # Current data plans (parallel safe)
            'current_members': IngestionPlan(
                name="Current Members",
                endpoints=['members_current'],
                dependencies=['bootstrap_schema'],
                priority=9,
                parallel_safe=True,
                timeout_minutes=30
            ),

            'current_bills': IngestionPlan(
                name="Current Bills",
                endpoints=['bills_current'],
                dependencies=['current_members'],
                priority=10,
                parallel_safe=True,
                timeout_minutes=60
            ),

            # Detailed enrichment plans (parallel safe)
            'member_details': IngestionPlan(
                name="Member Details Enrichment",
                endpoints=['member_details'],
                dependencies=['current_members', 'congress_118_members'],
                priority=11,
                parallel_safe=True,
                timeout_minutes=120
            ),

            'bill_details': IngestionPlan(
                name="Bill Details Enrichment",
                endpoints=['bill_details'],
                dependencies=['current_bills', 'congress_118_bills'],
                priority=12,
                parallel_safe=True,
                timeout_minutes=180
            ),

            # Search and discovery plans
            'bill_search': IngestionPlan(
                name="Bill Search Index",
                endpoints=['bill_search'],
                dependencies=['congress_118_bills'],
                priority=13,
                parallel_safe=True,
                timeout_minutes=60
            ),

            # Member-specific bills
            'member_bills': IngestionPlan(
                name="Member Bill Relationships",
                endpoints=['bills_by_member'],
                dependencies=['member_details'],
                priority=14,
                parallel_safe=True,
                timeout_minutes=90
            )
        }

    def execute_plan(self, plan_name: str, **params) -> Dict[str, Any]:
        """Execute a specific ingestion plan."""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown ingestion plan: {plan_name}")

        plan = self.ingestion_plans[plan_name]
        self.orchestration_stats['current_plan'] = plan_name

        self.logger.info(f"Executing ingestion plan: {plan.name}")

        plan_start = datetime.now()
        plan_stats = {
            'plan_name': plan_name,
            'plan_display_name': plan.name,
            'start_time': plan_start,
            'endpoints_processed': {},
            'total_processed': 0,
            'total_errors': 0,
            'success': False
        }

        try:
            # Check dependencies
            if not self._check_dependencies(plan):
                raise RuntimeError(f"Dependencies not met for plan: {plan_name}")

            # Execute endpoints in the plan
            for endpoint in plan.endpoints:
                endpoint_start = datetime.now()

                try:
                    # Build endpoint parameters
                    endpoint_params = self._build_endpoint_params(endpoint, plan_name, params)

                    # Execute endpoint ingestion
                    result = self.bulk_ingestor.ingest_endpoint(endpoint, **endpoint_params)

                    plan_stats['endpoints_processed'][endpoint] = {
                        'success': True,
                        'result': result,
                        'duration': (datetime.now() - endpoint_start).total_seconds()
                    }

                    plan_stats['total_processed'] += result.get('total_processed', 0)
                    plan_stats['total_errors'] += result.get('failed_batches', 0)

                    # Call progress callback if provided
                    if plan.progress_callback:
                        plan.progress_callback(endpoint, result.get('total_processed', 0), plan_stats['total_processed'])

                    # Brief pause between endpoints
                    time.sleep(2)

                except Exception as e:
                    self.logger.error(f"Endpoint {endpoint} failed in plan {plan_name}: {e}")

                    plan_stats['endpoints_processed'][endpoint] = {
                        'success': False,
                        'error': str(e),
                        'duration': (datetime.now() - endpoint_start).total_seconds()
                    }

                    plan_stats['total_errors'] += 1

                    if not plan.retry_on_failure:
                        raise

            plan_stats['success'] = True
            plan_stats['end_time'] = datetime.now()
            plan_stats['duration'] = (plan_stats['end_time'] - plan_start).total_seconds()

            self.orchestration_stats['plans_executed'].append(plan_stats)
            self.orchestration_stats['total_records'] += plan_stats['total_processed']
            self.orchestration_stats['total_errors'] += plan_stats['total_errors']

            self.logger.info(f"Plan {plan_name} completed: {plan_stats['total_processed']} records, {plan_stats['total_errors']} errors")

            return plan_stats

        except Exception as e:
            plan_stats['success'] = False
            plan_stats['end_time'] = datetime.now()
            plan_stats['duration'] = (plan_stats['end_time'] - plan_start).total_seconds()
            plan_stats['error'] = str(e)

            self.orchestration_stats['plans_failed'].append(plan_stats)
            self.orchestration_stats['total_errors'] += 1

            self.logger.error(f"Plan {plan_name} failed: {e}")
            raise

    def execute_sequential_plan(self, plan_names: List[str], **params) -> Dict[str, Any]:
        """Execute multiple plans sequentially with dependency checking."""
        self.logger.info(f"Executing sequential plan with {len(plan_names)} steps")

        sequence_start = datetime.now()
        sequence_stats = {
            'plans_executed': [],
            'plans_failed': [],
            'total_processed': 0,
            'total_errors': 0,
            'start_time': sequence_start
        }

        for plan_name in plan_names:
            try:
                plan_result = self.execute_plan(plan_name, **params)
                sequence_stats['plans_executed'].append(plan_result)
                sequence_stats['total_processed'] += plan_result['total_processed']
                sequence_stats['total_errors'] += plan_result['total_errors']

                # Pause between plans
                time.sleep(5)

            except Exception as e:
                self.logger.error(f"Plan {plan_name} failed in sequence: {e}")
                sequence_stats['plans_failed'].append({'plan_name': plan_name, 'error': str(e)})
                sequence_stats['total_errors'] += 1

                # Decide whether to continue or stop
                if plan_name in ['bootstrap_schema']:  # Critical plans
                    raise

        sequence_stats['end_time'] = datetime.now()
        sequence_stats['duration'] = (sequence_stats['end_time'] - sequence_stats['total_seconds']).total_seconds()
        sequence_stats['success'] = len(sequence_stats['plans_failed']) == 0

        return sequence_stats

    def execute_parallel_plan(self, plan_names: List[str], max_workers: int = 3, **params) -> Dict[str, Any]:
        """Execute multiple plans in parallel where safe."""
        import concurrent.futures
        from threading import Lock

        self.logger.info(f"Executing parallel plan with {len(plan_names)} plans, max_workers={max_workers}")

        parallel_start = datetime.now()
        parallel_stats = {
            'plans_executed': [],
            'plans_failed': [],
            'total_processed': 0,
            'total_errors': 0,
            'start_time': parallel_start
        }

        # Thread-safe statistics update
        stats_lock = Lock()

        def execute_plan_thread(plan_name: str) -> Dict[str, Any]:
            """Execute plan in thread with error handling."""
            try:
                return self.execute_plan(plan_name, **params)
            except Exception as e:
                return {'plan_name': plan_name, 'success': False, 'error': str(e)}

        # Filter for parallel-safe plans
        safe_plans = [name for name in plan_names if self.ingestion_plans[name].parallel_safe]
        unsafe_plans = [name for name in plan_names if not self.ingestion_plans[name].parallel_safe]

        if unsafe_plans:
            self.logger.warning(f"Skipping non-parallel-safe plans: {unsafe_plans}")

        # Execute parallel plans
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_plan = {executor.submit(execute_plan_thread, plan_name): plan_name
                            for plan_name in safe_plans}

            for future in concurrent.futures.as_completed(future_to_plan, timeout=3600):
                plan_name = future_to_plan[future]

                try:
                    result = future.result()

                    with stats_lock:
                        if result.get('success', True):
                            parallel_stats['plans_executed'].append(result)
                            parallel_stats['total_processed'] += result.get('total_processed', 0)
                            parallel_stats['total_errors'] += result.get('total_errors', 0)
                        else:
                            parallel_stats['plans_failed'].append(result)
                            parallel_stats['total_errors'] += 1

                except Exception as e:
                    self.logger.error(f"Parallel plan {plan_name} failed: {e}")

                    with stats_lock:
                        parallel_stats['plans_failed'].append({'plan_name': plan_name, 'error': str(e)})
                        parallel_stats['total_errors'] += 1

        parallel_stats['end_time'] = datetime.now()
        parallel_stats['duration'] = (parallel_stats['end_time'] - parallel_start).total_seconds()
        parallel_stats['success'] = len(parallel_stats['plans_failed']) == 0

        return parallel_stats

    def execute_full_ingestion(self, congresses: List[int] = None, include_current: bool = True,
                            include_details: bool = True, parallel: bool = False) -> Dict[str, Any]:
        """Execute comprehensive ingestion for all Congress data."""
        if not congresses:
            congresses = [118, 117, 116]  # Default to recent congresses

        self.logger.info(f"Starting full ingestion for congresses {congresses}")

        full_start = datetime.now()

        # Build plan sequence
        plan_sequence = ['bootstrap_schema']

        # Add congress-specific plans
        for congress in congresses:
            plan_sequence.extend([
                f'congress_{congress}_members',
                f'congress_{congress}_bills'
            ])

        # Add current data if requested
        if include_current:
            plan_sequence.extend(['current_members', 'current_bills'])

        # Add detailed enrichment if requested
        if include_details:
            plan_sequence.extend(['member_details', 'bill_details'])

        # Add search and relationships
        plan_sequence.extend(['bill_search', 'member_bills'])

        # Execute based on parallel preference
        if parallel:
            # Split into phases for parallel execution
            foundation_plans = ['bootstrap_schema']
            congress_plans = [p for p in plan_sequence if 'congress_' in p]
            current_plans = [p for p in plan_sequence if p in ['current_members', 'current_bills']]
            detail_plans = [p for p in plan_sequence if p in ['member_details', 'bill_details']]
            search_plans = [p for p in plan_sequence if p in ['bill_search', 'member_bills']]

            results = {}

            # Phase 1: Foundation (sequential)
            results['foundation'] = self.execute_sequential_plan(foundation_plans)

            # Phase 2: Congress data (parallel by congress)
            for congress in congresses:
                congress_phase = [p for p in congress_plans if f'congress_{congress}_' in p]
                if congress_phase:
                    results[f'congress_{congress}'] = self.execute_parallel_plan(congress_phase, max_workers=2)

            # Phase 3: Current data (parallel)
            if current_plans:
                results['current'] = self.execute_parallel_plan(current_plans, max_workers=2)

            # Phase 4: Details (parallel)
            if detail_plans:
                results['details'] = self.execute_parallel_plan(detail_plans, max_workers=2)

            # Phase 5: Search (parallel)
            if search_plans:
                results['search'] = self.execute_parallel_plan(search_plans, max_workers=2)

        else:
            # Sequential execution
            results = self.execute_sequential_plan(plan_sequence)

        # Generate comprehensive summary
        total_processed = 0
        total_errors = 0

        if isinstance(results, dict):
            for phase_result in results.values():
                if isinstance(phase_result, dict):
                    total_processed += phase_result.get('total_processed', 0)
                    total_errors += phase_result.get('total_errors', 0)
        else:
            total_processed = results.get('total_processed', 0)
            total_errors = results.get('total_errors', 0)

        summary = {
            'congresses': congresses,
            'include_current': include_current,
            'include_details': include_details,
            'parallel_execution': parallel,
            'total_processed': total_processed,
            'total_errors': total_errors,
            'success_rate': (total_processed / max(1, total_processed + total_errors)) * 100,
            'start_time': full_start,
            'end_time': datetime.now(),
            'duration': (datetime.now() - full_start).total_seconds(),
            'records_per_second': total_processed / max(1, (datetime.now() - full_start).total_seconds()),
            'results': results
        }

        self.logger.info(f"Full ingestion completed: {total_processed} records, {total_errors} errors, {summary['duration']:.1f}s")
        return summary

    def _check_dependencies(self, plan: IngestionPlan) -> bool:
        """Check if all dependencies for a plan are satisfied."""
        if not plan.dependencies:
            return True

        executed_plan_names = [p['plan_name'] for p in self.orchestration_stats['plans_executed']]

        for dependency in plan.dependencies:
            if dependency not in executed_plan_names:
                self.logger.warning(f"Dependency {dependency} not satisfied for plan {plan.name}")
                return False

        return True

    def _build_endpoint_params(self, endpoint: str, plan_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build parameters for endpoint based on plan and user params."""
        endpoint_params = {}

        # Extract congress number from plan name
        if 'congress_' in plan_name:
            import re
            match = re.search(r'congress_(\d+)', plan_name)
            if match:
                endpoint_params['congress'] = int(match.group(1))

        # Add user parameters
        endpoint_params.update(params)

        return endpoint_params

    def get_available_plans(self) -> Dict[str, IngestionPlan]:
        """Get all available ingestion plans."""
        return self.ingestion_plans.copy()

    def get_plan_status(self, plan_name: str) -> Dict[str, Any]:
        """Get status of a specific plan."""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown plan: {plan_name}")

        plan = self.ingestion_plans[plan_name]

        # Check if plan has been executed
        executed = [p for p in self.orchestration_stats['plans_executed'] if p['plan_name'] == plan_name]
        failed = [p for p in self.orchestration_stats['plans_failed'] if p['plan_name'] == plan_name]

        return {
            'plan_name': plan_name,
            'plan': plan,
            'dependencies_satisfied': self._check_dependencies(plan),
            'executed_count': len(executed),
            'failed_count': len(failed),
            'last_execution': executed[-1] if executed else None,
            'last_failure': failed[-1] if failed else None,
            'status': 'completed' if executed else 'failed' if failed else 'pending'
        }

    def get_orchestration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive orchestration statistics."""
        end_time = datetime.now()
        duration = (end_time - self.orchestration_stats['start_time']).total_seconds()

        return {
            'start_time': self.orchestration_stats['start_time'],
            'end_time': end_time,
            'duration_seconds': duration,
            'total_plans_executed': len(self.orchestration_stats['plans_executed']),
            'total_plans_failed': len(self.orchestration_stats['plans_failed']),
            'total_records_processed': self.orchestration_stats['total_records'],
            'total_errors': self.orchestration_stats['total_errors'],
            'success_rate': (self.orchestration_stats['total_records'] / max(1, self.orchestration_stats['total_records'] + self.orchestration_stats['total_errors'])) * 100,
            'records_per_second': self.orchestration_stats['total_records'] / max(1, duration),
            'current_plan': self.orchestration_stats['current_plan'],
            'executed_plans': [p['plan_name'] for p in self.orchestration_stats['plans_executed']],
            'failed_plans': [p['plan_name'] for p in self.orchestration_stats['plans_failed']]
        }
