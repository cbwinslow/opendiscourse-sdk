"""
Orchestrator functions for GovInfo CLI bulk data ingestion with sophisticated coordination.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..utils.config import get_config
from ..utils.logger import get_logger
from .bulk_ingestor import GovInfoBulkIngestor


@dataclass
class GovInfoIngestionPlan:
    """Comprehensive GovInfo ingestion plan with dependencies and priorities."""

    name: str
    endpoints: List[str]
    dependencies: List[str] = None
    priority: int = 1
    parallel_safe: bool = False
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_minutes: int = 60
    progress_callback: Optional[Callable[[str, int, int], None]] = None


class GovInfoIngestionOrchestrator:
    """Sophisticated orchestration of GovInfo data ingestion with dependency management."""

    def __init__(self, config=None):
        """Initialize orchestrator with configuration."""
        self.config = config or get_config()
        self.bulk_ingestor = GovInfoBulkIngestor(config)
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
        """Setup comprehensive GovInfo ingestion plans with dependencies."""
        self.ingestion_plans = {
            # Foundation plans (must run first)
            'bootstrap_schema': GovInfoIngestionPlan(
                name="Bootstrap GovInfo Database Schema",
                endpoints=[],
                dependencies=[],
                priority=1,
                parallel_safe=False,
                timeout_minutes=30
            ),

            # Reference data plans (high priority)
            'committees_house': GovInfoIngestionPlan(
                name="House Committees",
                endpoints=['committees_house'],
                dependencies=['bootstrap_schema'],
                priority=2,
                parallel_safe=False,
                timeout_minutes=45
            ),

            'committees_senate': GovInfoIngestionPlan(
                name="Senate Committees",
                endpoints=['committees_senate'],
                dependencies=['bootstrap_schema'],
                priority=3,
                parallel_safe=False,
                timeout_minutes=45
            ),

            # Congressional Directory plans (members)
            'congressional_directory_118': GovInfoIngestionPlan(
                name="Congressional Directory 118",
                endpoints=['congressional_directory'],
                dependencies=['bootstrap_schema'],
                priority=4,
                parallel_safe=False,
                timeout_minutes=60
            ),

            'congressional_directory_117': GovInfoIngestionPlan(
                name="Congressional Directory 117",
                endpoints=['congressional_directory'],
                dependencies=['bootstrap_schema'],
                priority=5,
                parallel_safe=False,
                timeout_minutes=60
            ),

            'congressional_directory_116': GovInfoIngestionPlan(
                name="Congressional Directory 116",
                endpoints=['congressional_directory'],
                dependencies=['bootstrap_schema'],
                priority=6,
                parallel_safe=False,
                timeout_minutes=60
            ),

            # Bills collections (parallel safe after committees)
            'bills_118': GovInfoIngestionPlan(
                name="Bills Collection 118",
                endpoints=['collections_bills'],
                dependencies=['committees_house', 'committees_senate'],
                priority=7,
                parallel_safe=True,
                timeout_minutes=120
            ),

            'bills_117': GovInfoIngestionPlan(
                name="Bills Collection 117",
                endpoints=['collections_bills'],
                dependencies=['committees_house', 'committees_senate'],
                priority=8,
                parallel_safe=True,
                timeout_minutes=120
            ),

            'bills_116': GovInfoIngestionPlan(
                name="Bills Collection 116",
                endpoints=['collections_bills'],
                dependencies=['committees_house', 'committees_senate'],
                priority=9,
                parallel_safe=True,
                timeout_minutes=120
            ),

            # Congressional Record (parallel safe)
            'congressional_record_118': GovInfoIngestionPlan(
                name="Congressional Record 118",
                endpoints=['collections_crec'],
                dependencies=['bootstrap_schema'],
                priority=10,
                parallel_safe=True,
                timeout_minutes=90
            ),

            'congressional_record_117': GovInfoIngestionPlan(
                name="Congressional Record 117",
                endpoints=['collections_crec'],
                dependencies=['bootstrap_schema'],
                priority=11,
                parallel_safe=True,
                timeout_minutes=90
            ),

            # Committee Hearings (parallel safe)
            'committee_hearings_118': GovInfoIngestionPlan(
                name="Committee Hearings 118",
                endpoints=['collections_chrg'],
                dependencies=['committees_house', 'committees_senate'],
                priority=12,
                parallel_safe=True,
                timeout_minutes=120
            ),

            'committee_hearings_117': GovInfoIngestionPlan(
                name="Committee Hearings 117",
                endpoints=['collections_chrg'],
                dependencies=['committees_house', 'committees_senate'],
                priority=13,
                parallel_safe=True,
                timeout_minutes=120
            ),

            # Package content enrichment (depends on collections)
            'package_content_bills': GovInfoIngestionPlan(
                name="Bill Package Content",
                endpoints=['package_content'],
                dependencies=['bills_118', 'bills_117', 'bills_116'],
                priority=14,
                parallel_safe=False,  # Requires individual package processing
                timeout_minutes=180
            ),

            'package_content_crec': GovInfoIngestionPlan(
                name="Congressional Record Content",
                endpoints=['package_content'],
                dependencies=['congressional_record_118', 'congressional_record_117'],
                priority=15,
                parallel_safe=False,
                timeout_minutes=180
            ),

            'package_content_chrg': GovInfoIngestionPlan(
                name="Committee Hearing Content",
                endpoints=['package_content'],
                dependencies=['committee_hearings_118', 'committee_hearings_117'],
                priority=16,
                parallel_safe=False,
                timeout_minutes=180
            )
        }

    def execute_plan(self, plan_name: str, **params) -> Dict[str, Any]:
        """Execute a specific GovInfo ingestion plan."""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown GovInfo ingestion plan: {plan_name}")

        plan = self.ingestion_plans[plan_name]
        self.orchestration_stats['current_plan'] = plan_name

        self.logger.info(f"Executing GovInfo ingestion plan: {plan.name}")

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
                raise RuntimeError(f"Dependencies not met for GovInfo plan: {plan_name}")

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

                    # Longer pause between GovInfo endpoints due to rate limits
                    time.sleep(5)

                except Exception as e:
                    self.logger.error(f"GovInfo endpoint {endpoint} failed in plan {plan_name}: {e}")

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

            self.logger.info(f"GovInfo plan {plan_name} completed: {plan_stats['total_processed']} records, {plan_stats['total_errors']} errors")

            return plan_stats

        except Exception as e:
            plan_stats['success'] = False
            plan_stats['end_time'] = datetime.now()
            plan_stats['duration'] = (plan_stats['end_time'] - plan_start).total_seconds()
            plan_stats['error'] = str(e)

            self.orchestration_stats['plans_failed'].append(plan_stats)
            self.orchestration_stats['total_errors'] += 1

            self.logger.error(f"GovInfo plan {plan_name} failed: {e}")
            raise

    def execute_sequential_plan(self, plan_names: List[str], **params) -> Dict[str, Any]:
        """Execute multiple GovInfo plans sequentially with dependency checking."""
        self.logger.info(f"Executing sequential GovInfo plan with {len(plan_names)} steps")

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

                # Longer pause between GovInfo plans due to rate limits
                time.sleep(10)

            except Exception as e:
                self.logger.error(f"GovInfo plan {plan_name} failed in sequence: {e}")
                sequence_stats['plans_failed'].append({'plan_name': plan_name, 'error': str(e)})
                sequence_stats['total_errors'] += 1

                # Decide whether to continue or stop
                if plan_name in ['bootstrap_schema']:  # Critical plans
                    raise

        sequence_stats['end_time'] = datetime.now()
        sequence_stats['duration'] = (sequence_stats['end_time'] - sequence_start).total_seconds()
        sequence_stats['success'] = len(sequence_stats['plans_failed']) == 0

        return sequence_stats

    def execute_parallel_plan(self, plan_names: List[str], max_workers: int = 2, **params) -> Dict[str, Any]:
        """Execute multiple GovInfo plans in parallel where safe (limited workers due to rate limits)."""
        import concurrent.futures
        from threading import Lock

        self.logger.info(f"Executing parallel GovInfo plan with {len(plan_names)} plans, max_workers={max_workers}")

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
            """Execute GovInfo plan in thread with error handling."""
            try:
                return self.execute_plan(plan_name, **params)
            except Exception as e:
                return {'plan_name': plan_name, 'success': False, 'error': str(e)}

        # Filter for parallel-safe plans
        safe_plans = [name for name in plan_names if self.ingestion_plans[name].parallel_safe]
        unsafe_plans = [name for name in plan_names if not self.ingestion_plans[name].parallel_safe]

        if unsafe_plans:
            self.logger.warning(f"Skipping non-parallel-safe GovInfo plans: {unsafe_plans}")

        # Execute parallel plans with limited workers due to rate limits
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_plan = {executor.submit(execute_plan_thread, plan_name): plan_name
                            for plan_name in safe_plans}

            for future in concurrent.futures.as_completed(future_to_plan, timeout=7200):  # 2 hour timeout
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
                    self.logger.error(f"Parallel GovInfo plan {plan_name} failed: {e}")

                    with stats_lock:
                        parallel_stats['plans_failed'].append({'plan_name': plan_name, 'error': str(e)})
                        parallel_stats['total_errors'] += 1

        parallel_stats['end_time'] = datetime.now()
        parallel_stats['duration'] = (parallel_stats['end_time'] - parallel_start).total_seconds()
        parallel_stats['success'] = len(parallel_stats['plans_failed']) == 0

        return parallel_stats

    def execute_full_ingestion(self, congresses: List[int] = None, include_content: bool = True,
                            parallel: bool = False) -> Dict[str, Any]:
        """Execute comprehensive GovInfo ingestion for all data types."""
        if not congresses:
            congresses = [118, 117, 116]  # Default to recent congresses

        self.logger.info(f"Starting full GovInfo ingestion for congresses {congresses}")

        full_start = datetime.now()

        # Build plan sequence
        plan_sequence = ['bootstrap_schema']

        # Add committee plans (high priority)
        plan_sequence.extend(['committees_house', 'committees_senate'])

        # Add congressional directory plans
        for congress in congresses:
            plan_sequence.append(f'congressional_directory_{congress}')

        # Add collection plans (parallel safe)
        for congress in congresses:
            plan_sequence.extend([
                f'bills_{congress}',
                f'congressional_record_{congress}',
                f'committee_hearings_{congress}'
            ])

        # Add package content if requested
        if include_content:
            plan_sequence.extend([
                'package_content_bills',
                'package_content_crec',
                'package_content_chrg'
            ])

        # Execute based on parallel preference
        if parallel:
            # Split into phases for parallel execution
            foundation_plans = ['bootstrap_schema']
            committee_plans = ['committees_house', 'committees_senate']
            directory_plans = [p for p in plan_sequence if 'congressional_directory_' in p]
            collection_plans = [p for p in plan_sequence if any(x in p for x in ['bills_', 'congressional_record_', 'committee_hearings_'])]
            content_plans = [p for p in plan_sequence if 'package_content_' in p]

            results = {}

            # Phase 1: Foundation (sequential)
            results['foundation'] = self.execute_sequential_plan(foundation_plans)

            # Phase 2: Committees (sequential due to dependencies)
            results['committees'] = self.execute_sequential_plan(committee_plans)

            # Phase 3: Directory (sequential due to rate limits)
            results['directory'] = self.execute_sequential_plan(directory_plans)

            # Phase 4: Collections (parallel by congress)
            for congress in congresses:
                congress_phase = [p for p in collection_plans if f'_{congress}' in p]
                if congress_phase:
                    results[f'collections_{congress}'] = self.execute_parallel_plan(congress_phase, max_workers=2)

            # Phase 5: Content (sequential due to individual package processing)
            if content_plans:
                results['content'] = self.execute_sequential_plan(content_plans)

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
            'include_content': include_content,
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

        self.logger.info(f"Full GovInfo ingestion completed: {total_processed} records, {total_errors} errors, {summary['duration']:.1f}s")
        return summary

    def _check_dependencies(self, plan: GovInfoIngestionPlan) -> bool:
        """Check if all dependencies for a GovInfo plan are satisfied."""
        if not plan.dependencies:
            return True

        executed_plan_names = [p['plan_name'] for p in self.orchestration_stats['plans_executed']]

        for dependency in plan.dependencies:
            if dependency not in executed_plan_names:
                self.logger.warning(f"Dependency {dependency} not satisfied for GovInfo plan {plan.name}")
                return False

        return True

    def _build_endpoint_params(self, endpoint: str, plan_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build parameters for GovInfo endpoint based on plan and user params."""
        endpoint_params = {}

        # Extract congress number from plan name
        if 'congressional_directory_' in plan_name:
            import re
            match = re.search(r'congressional_directory_(\d+)', plan_name)
            if match:
                congress = int(match.group(1))
                # Calculate start date for the congress
                start_year = 1789 + (congress - 1) * 2
                endpoint_params['date'] = f"{start_year}-01-03"
                endpoint_params['collection_code'] = 'CDIR'

        elif 'bills_' in plan_name:
            import re
            match = re.search(r'bills_(\d+)', plan_name)
            if match:
                congress = int(match.group(1))
                start_year = 1789 + (congress - 1) * 2
                endpoint_params['date'] = f"{start_year}-01-03"
                endpoint_params['collection_code'] = 'BILLS'

        elif 'congressional_record_' in plan_name:
            import re
            match = re.search(r'congressional_record_(\d+)', plan_name)
            if match:
                congress = int(match.group(1))
                start_year = 1789 + (congress - 1) * 2
                endpoint_params['date'] = f"{start_year}-01-03"
                endpoint_params['collection_code'] = 'CREC'

        elif 'committee_hearings_' in plan_name:
            import re
            match = re.search(r'committee_hearings_(\d+)', plan_name)
            if match:
                congress = int(match.group(1))
                start_year = 1789 + (congress - 1) * 2
                endpoint_params['date'] = f"{start_year}-01-03"
                endpoint_params['collection_code'] = 'CHRG'

        elif endpoint == 'committees_house':
            endpoint_params['chamber'] = 'HOUSE'
        elif endpoint == 'committees_senate':
            endpoint_params['chamber'] = 'SENATE'

        # Add user parameters
        endpoint_params.update(params)

        return endpoint_params

    def get_available_plans(self) -> Dict[str, GovInfoIngestionPlan]:
        """Get all available GovInfo ingestion plans."""
        return self.ingestion_plans.copy()

    def get_plan_status(self, plan_name: str) -> Dict[str, Any]:
        """Get status of a specific GovInfo plan."""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown GovInfo plan: {plan_name}")

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
        """Get comprehensive GovInfo orchestration statistics."""
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
