"""
Orchestrator functions for OpenStates CLI bulk data ingestion with sophisticated coordination.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..utils.config import get_config
from ..utils.logger import get_logger
from .bulk_ingestor import OpenStatesBulkIngestor


@dataclass
class OpenStatesIngestionPlan:
    """Comprehensive OpenStates ingestion plan with dependencies and priorities."""

    name: str
    endpoints: List[str]
    dependencies: List[str] = None
    priority: int = 1
    parallel_safe: bool = False
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_minutes: int = 60
    progress_callback: Optional[Callable[[str, int, int], None]] = None


class OpenStatesIngestionOrchestrator:
    """Sophisticated orchestration of OpenStates data ingestion with dependency management."""

    def __init__(self, config=None):
        """Initialize orchestrator with configuration."""
        self.config = config or get_config()
        self.bulk_ingestor = OpenStatesBulkIngestor(config)
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
        """Setup comprehensive OpenStates ingestion plans with dependencies."""
        self.ingestion_plans = {
            # Foundation plans (must run first)
            'bootstrap_schema': OpenStatesIngestionPlan(
                name="Bootstrap OpenStates Database Schema",
                endpoints=[],
                dependencies=[],
                priority=1,
                parallel_safe=False,
                timeout_minutes=30
            ),

            # Jurisdictions foundation (highest priority)
            'jurisdictions': OpenStatesIngestionPlan(
                name="Load All Jurisdictions",
                endpoints=['jurisdictions'],
                dependencies=['bootstrap_schema'],
                priority=2,
                parallel_safe=False,
                timeout_minutes=45
            ),

            # State-by-state plans (can be parallelized by region)
            'northeast_states': OpenStatesIngestionPlan(
                name="Northeast States Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=3,
                parallel_safe=True,
                timeout_minutes=180
            ),

            'southeast_states': OpenStatesIngestionPlan(
                name="Southeast States Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=4,
                parallel_safe=True,
                timeout_minutes=180
            ),

            'midwest_states': OpenStatesIngestionPlan(
                name="Midwest States Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=5,
                parallel_safe=True,
                timeout_minutes=180
            ),

            'west_states': OpenStatesIngestionPlan(
                name="Western States Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=6,
                parallel_safe=True,
                timeout_minutes=180
            ),

            'southwest_states': OpenStatesIngestionPlan(
                name="Southwest States Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=7,
                parallel_safe=True,
                timeout_minutes=180
            ),

            # Individual state plans (for targeted ingestion)
            'california': OpenStatesIngestionPlan(
                name="California Complete Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=8,
                parallel_safe=False,
                timeout_minutes=120
            ),

            'texas': OpenStatesIngestionPlan(
                name="Texas Complete Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=9,
                parallel_safe=False,
                timeout_minutes=120
            ),

            'florida': OpenStatesIngestionPlan(
                name="Florida Complete Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=10,
                parallel_safe=False,
                timeout_minutes=120
            ),

            'new_york': OpenStatesIngestionPlan(
                name="New York Complete Data",
                endpoints=['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'],
                dependencies=['jurisdictions'],
                priority=11,
                parallel_safe=False,
                timeout_minutes=120
            ),

            # Detail enrichment plans (parallel safe)
            'people_details': OpenStatesIngestionPlan(
                name="People Details Enrichment",
                endpoints=['person_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                priority=12,
                parallel_safe=True,
                timeout_minutes=240
            ),

            'bill_details': OpenStatesIngestionPlan(
                name="Bill Details Enrichment",
                endpoints=['bill_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                priority=13,
                parallel_safe=True,
                timeout_minutes=360
            ),

            'committee_details': OpenStatesIngestionPlan(
                name="Committee Details Enrichment",
                endpoints=['committee_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                priority=14,
                parallel_safe=True,
                timeout_minutes=180
            ),

            'event_details': OpenStatesIngestionPlan(
                name="Event Details Enrichment",
                endpoints=['event_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                priority=15,
                parallel_safe=True,
                timeout_minutes=180
            ),

            # Relationship plans
            'person_bills': OpenStatesIngestionPlan(
                name="Person-Bill Relationships",
                endpoints=['bills_by_person'],
                dependencies=['people_details'],
                priority=16,
                parallel_safe=True,
                timeout_minutes=240
            ),

            # Global search plans
            'people_search': OpenStatesIngestionPlan(
                name="Global People Search",
                endpoints=['people_search'],
                dependencies=['jurisdictions'],
                priority=17,
                parallel_safe=True,
                timeout_minutes=120
            ),

            'bills_search': OpenStatesIngestionPlan(
                name="Global Bills Search",
                endpoints=['bills_search'],
                dependencies=['jurisdictions'],
                priority=18,
                parallel_safe=True,
                timeout_minutes=120
            )
        }

    def execute_plan(self, plan_name: str, **params) -> Dict[str, Any]:
        """Execute a specific OpenStates ingestion plan."""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown OpenStates ingestion plan: {plan_name}")

        plan = self.ingestion_plans[plan_name]
        self.orchestration_stats['current_plan'] = plan_name

        self.logger.info(f"Executing OpenStates ingestion plan: {plan.name}")

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
                raise RuntimeError(f"Dependencies not met for OpenStates plan: {plan_name}")

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

                    # Pause between endpoints
                    time.sleep(3)

                except Exception as e:
                    self.logger.error(f"OpenStates endpoint {endpoint} failed in plan {plan_name}: {e}")

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

            self.logger.info(f"OpenStates plan {plan_name} completed: {plan_stats['total_processed']} records, {plan_stats['total_errors']} errors")

            return plan_stats

        except Exception as e:
            plan_stats['success'] = False
            plan_stats['end_time'] = datetime.now()
            plan_stats['duration'] = (plan_stats['end_time'] - plan_start).total_seconds()
            plan_stats['error'] = str(e)

            self.orchestration_stats['plans_failed'].append(plan_stats)
            self.orchestration_stats['total_errors'] += 1

            self.logger.error(f"OpenStates plan {plan_name} failed: {e}")
            raise

    def execute_sequential_plan(self, plan_names: List[str], **params) -> Dict[str, Any]:
        """Execute multiple OpenStates plans sequentially with dependency checking."""
        self.logger.info(f"Executing sequential OpenStates plan with {len(plan_names)} steps")

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

                # Pause between OpenStates plans due to rate limits
                time.sleep(8)

            except Exception as e:
                self.logger.error(f"OpenStates plan {plan_name} failed in sequence: {e}")
                sequence_stats['plans_failed'].append({'plan_name': plan_name, 'error': str(e)})
                sequence_stats['total_errors'] += 1

                # Decide whether to continue or stop
                if plan_name in ['bootstrap_schema', 'jurisdictions']:  # Critical plans
                    raise

        sequence_stats['end_time'] = datetime.now()
        sequence_stats['duration'] = (sequence_stats['end_time'] - sequence_start).total_seconds()
        sequence_stats['success'] = len(sequence_stats['plans_failed']) == 0

        return sequence_stats

    def execute_parallel_plan(self, plan_names: List[str], max_workers: int = 2, **params) -> Dict[str, Any]:
        """Execute multiple OpenStates plans in parallel where safe (limited workers due to rate limits)."""
        import concurrent.futures
        from threading import Lock

        self.logger.info(f"Executing parallel OpenStates plan with {len(plan_names)} plans, max_workers={max_workers}")

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
            """Execute OpenStates plan in thread with error handling."""
            try:
                return self.execute_plan(plan_name, **params)
            except Exception as e:
                return {'plan_name': plan_name, 'success': False, 'error': str(e)}

        # Filter for parallel-safe plans
        safe_plans = [name for name in plan_names if self.ingestion_plans[name].parallel_safe]
        unsafe_plans = [name for name in plan_names if not self.ingestion_plans[name].parallel_safe]

        if unsafe_plans:
            self.logger.warning(f"Skipping non-parallel-safe OpenStates plans: {unsafe_plans}")

        # Execute parallel plans with limited workers due to rate limits
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_plan = {executor.submit(execute_plan_thread, plan_name): plan_name
                            for plan_name in safe_plans}

            for future in concurrent.futures.as_completed(future_to_plan, timeout=10800):  # 3 hour timeout
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
                    self.logger.error(f"Parallel OpenStates plan {plan_name} failed: {e}")

                    with stats_lock:
                        parallel_stats['plans_failed'].append({'plan_name': plan_name, 'error': str(e)})
                        parallel_stats['total_errors'] += 1

        parallel_stats['end_time'] = datetime.now()
        parallel_stats['duration'] = (parallel_stats['end_time'] - parallel_start).total_seconds()
        parallel_stats['success'] = len(parallel_stats['plans_failed']) == 0

        return parallel_stats

    def execute_full_ingestion(self, regions: List[str] = None, include_details: bool = True,
                            include_search: bool = True, parallel: bool = False) -> Dict[str, Any]:
        """Execute comprehensive OpenStates ingestion for all state data."""
        if not regions:
            regions = ['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states']

        self.logger.info(f"Starting full OpenStates ingestion for regions {regions}")

        full_start = datetime.now()

        # Build plan sequence
        plan_sequence = ['bootstrap_schema', 'jurisdictions']

        # Add regional plans
        plan_sequence.extend(regions)

        # Add detail enrichment if requested
        if include_details:
            plan_sequence.extend(['people_details', 'bill_details', 'committee_details', 'event_details'])

        # Add relationships if requested
        if include_details:
            plan_sequence.append('person_bills')

        # Add global search if requested
        if include_search:
            plan_sequence.extend(['people_search', 'bills_search'])

        # Execute based on parallel preference
        if parallel:
            # Split into phases for parallel execution
            foundation_plans = ['bootstrap_schema', 'jurisdictions']
            regional_plans = regions
            detail_plans = ['people_details', 'bill_details', 'committee_details', 'event_details', 'person_bills']
            search_plans = ['people_search', 'bills_search']

            results = {}

            # Phase 1: Foundation (sequential)
            results['foundation'] = self.execute_sequential_plan(foundation_plans)

            # Phase 2: Regional (parallel by region)
            results['regional'] = self.execute_parallel_plan(regional_plans, max_workers=2)

            # Phase 3: Details (parallel)
            if include_details:
                results['details'] = self.execute_parallel_plan(detail_plans, max_workers=2)

            # Phase 4: Search (parallel)
            if include_search:
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
            'regions': regions,
            'include_details': include_details,
            'include_search': include_search,
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

        self.logger.info(f"Full OpenStates ingestion completed: {total_processed} records, {total_errors} errors, {summary['duration']:.1f}s")
        return summary

    def execute_state_ingestion(self, state: str, include_details: bool = True) -> Dict[str, Any]:
        """Execute ingestion for a specific state."""
        self.logger.info(f"Starting OpenStates ingestion for state: {state}")

        state_start = datetime.now()

        # Build state-specific plan sequence
        plan_sequence = ['bootstrap_schema', 'jurisdictions']

        # Add state plan if it exists
        state_plan = state.lower()
        if state_plan in self.ingestion_plans:
            plan_sequence.append(state_plan)
        else:
            # Create ad-hoc state plan
            plan_sequence.extend(['people_by_state', 'bills_by_state', 'committees_by_state', 'events_by_state'])

        # Add details if requested
        if include_details:
            plan_sequence.extend(['people_details', 'bill_details', 'committee_details', 'event_details'])

        # Execute sequential
        results = self.execute_sequential_plan(plan_sequence, state=state)

        # Generate summary
        summary = {
            'state': state,
            'include_details': include_details,
            'total_processed': results.get('total_processed', 0),
            'total_errors': results.get('total_errors', 0),
            'success_rate': (results.get('total_processed', 0) / max(1, results.get('total_processed', 0) + results.get('total_errors', 0))) * 100,
            'start_time': state_start,
            'end_time': datetime.now(),
            'duration': (datetime.now() - state_start).total_seconds(),
            'results': results
        }

        self.logger.info(f"State {state} ingestion completed: {summary['total_processed']} records, {summary['total_errors']} errors")
        return summary

    def _check_dependencies(self, plan: OpenStatesIngestionPlan) -> bool:
        """Check if all dependencies for an OpenStates plan are satisfied."""
        if not plan.dependencies:
            return True

        executed_plan_names = [p['plan_name'] for p in self.orchestration_stats['plans_executed']]

        for dependency in plan.dependencies:
            if dependency not in executed_plan_names:
                self.logger.warning(f"Dependency {dependency} not satisfied for OpenStates plan {plan.name}")
                return False

        return True

    def _build_endpoint_params(self, endpoint: str, plan_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build parameters for OpenStates endpoint based on plan and user params."""
        endpoint_params = {}

        # Extract state from plan name or params
        if 'california' in plan_name:
            endpoint_params['state'] = 'CA'
        elif 'texas' in plan_name:
            endpoint_params['state'] = 'TX'
        elif 'florida' in plan_name:
            endpoint_params['state'] = 'FL'
        elif 'new_york' in plan_name:
            endpoint_params['state'] = 'NY'
        elif 'northeast_states' in plan_name:
            # Northeast states
            northeast_states = ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA']
            endpoint_params['states'] = northeast_states
        elif 'southeast_states' in plan_name:
            # Southeast states
            southeast_states = ['DE', 'MD', 'DC', 'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'TN', 'KY']
            endpoint_params['states'] = southeast_states
        elif 'midwest_states' in plan_name:
            # Midwest states
            midwest_states = ['OH', 'MI', 'IN', 'IL', 'WI', 'MN', 'IA', 'MO', 'KS', 'NE', 'SD', 'ND']
            endpoint_params['states'] = midwest_states
        elif 'west_states' in plan_name:
            # Western states
            west_states = ['MT', 'WY', 'CO', 'NM', 'AZ', 'UT', 'ID', 'WA', 'OR', 'NV', 'CA', 'AK', 'HI']
            endpoint_params['states'] = west_states
        elif 'southwest_states' in plan_name:
            # Southwest states
            southwest_states = ['TX', 'OK', 'NM', 'AZ']
            endpoint_params['states'] = southwest_states

        # Add user parameters
        endpoint_params.update(params)

        return endpoint_params

    def get_available_plans(self) -> Dict[str, OpenStatesIngestionPlan]:
        """Get all available OpenStates ingestion plans."""
        return self.ingestion_plans.copy()

    def get_plan_status(self, plan_name: str) -> Dict[str, Any]:
        """Get status of a specific OpenStates plan."""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown OpenStates plan: {plan_name}")

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
        """Get comprehensive OpenStates orchestration statistics."""
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
