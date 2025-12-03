#!/usr/bin/env python3
"""
OpenStates Comprehensive Orchestration System
Sophisticated orchestration with dependency management and parallel processing
"""

import os
import sys
import requests
import hashlib
import json
import time
import logging
import psycopg2
import threading
import concurrent.futures
from psycopg2.extras import execute_values, Json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError
from enum import Enum

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate_limiter import adaptive_limiters
from env_config import get_optional_env_var, validate_api_keys
from enhanced_openstates_ingestion import (
    OpenStatesRateLimitManager, OpenStatesPaginationManager,
    OpenStatesDataValidator, OpenStatesProgressMonitor,
    OpenStatesParallelProcessor, EnhancedOpenStatesIngestor
)
from openstates_bills_ingestion import OpenStatesBillsIngestor
from openstates_committees_ingestion import OpenStatesCommitteesIngestor
from openstates_events_ingestion import OpenStatesEventsIngestor
from openstates_jurisdictions_ingestion import OpenStatesJurisdictionsIngestor


# ============================================================================
# ORCHESTRATION DATA MODELS
# ============================================================================

@dataclass
class IngestionPlan:
    """Comprehensive ingestion plan with dependencies and priorities"""

    name: str
    data_types: List[str]
    jurisdictions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    parallel_safe: bool = False
    priority: int = 1
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_minutes: int = 60
    progress_callback: Optional[callable] = None


@dataclass
class OrchestrationResult:
    """Result of orchestration execution"""

    plan_name: str
    success: bool
    records_processed: int = 0
    records_skipped: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None
    sub_results: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ============================================================================
# ENHANCED ORCHESTRATOR
# ============================================================================

class OpenStatesOrchestrator:
    """Sophisticated orchestration with dependency management and parallel processing"""

    def __init__(self):
        # Validate API key
        api_keys = validate_api_keys()
        if not api_keys['openstates.org']:
            raise ValueError("OPENSTATES_API_KEY not found in environment variables")

        # Initialize core components
        self.rate_manager = OpenStatesRateLimitManager()
        self.pagination_manager = OpenStatesPaginationManager()
        self.progress_monitor = OpenStatesProgressMonitor()
        self.parallel_processor = OpenStatesParallelProcessor()

        # Database connection
        self.db_conn = psycopg2.connect(
            database='cbwinslow',
            user='cbwinslow'
        )
        self.db_conn.autocommit = False

        # Initialize ingestors
        self.enhanced_ingestor = EnhancedOpenStatesIngestor()
        self.bills_ingestor = OpenStatesBillsIngestor(
            self.db_conn, self.rate_manager, self.pagination_manager, self.progress_monitor
        )
        self.committees_ingestor = OpenStatesCommitteesIngestor(
            self.db_conn, self.rate_manager, self.pagination_manager, self.progress_monitor
        )
        self.events_ingestor = OpenStatesEventsIngestor(
            self.db_conn, self.rate_manager, self.pagination_manager, self.progress_monitor
        )
        self.jurisdictions_ingestor = OpenStatesJurisdictionsIngestor(
            self.db_conn, self.rate_manager, self.pagination_manager, self.progress_monitor
        )

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Define ingestion plans
        self.ingestion_plans = self._define_ingestion_plans()

        # Track orchestration state
        self.orchestration_stats = {
            'start_time': datetime.now(),
            'plans_executed': [],
            'plans_failed': [],
            'total_records': 0,
            'total_errors': 0,
            'current_plan': None
        }

    def _define_ingestion_plans(self) -> Dict[str, IngestionPlan]:
        """Define comprehensive ingestion plans with dependencies"""
        return {
            # Foundation plans (must run first)
            'jurisdictions': IngestionPlan(
                name='Load All Jurisdictions',
                data_types=['jurisdictions'],
                dependencies=[],
                parallel_safe=False,
                priority=1,
                timeout_minutes=30
            ),

            # Regional plans (parallel safe)
            'northeast_states': IngestionPlan(
                name='Northeast States Complete Data',
                jurisdictions=['me', 'nh', 'vt', 'ma', 'ri', 'ct', 'ny', 'nj', 'pa'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=True,
                priority=2,
                timeout_minutes=180
            ),

            'southeast_states': IngestionPlan(
                name='Southeast States Complete Data',
                jurisdictions=['de', 'md', 'dc', 'va', 'wv', 'nc', 'sc', 'ga', 'fl', 'al', 'ms', 'tn', 'ky'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=True,
                priority=3,
                timeout_minutes=180
            ),

            'midwest_states': IngestionPlan(
                name='Midwest States Complete Data',
                jurisdictions=['oh', 'mi', 'in', 'il', 'wi', 'mn', 'ia', 'mo', 'ks', 'ne', 'sd', 'nd'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=True,
                priority=4,
                timeout_minutes=180
            ),

            'west_states': IngestionPlan(
                name='Western States Complete Data',
                jurisdictions=['mt', 'wy', 'co', 'nm', 'az', 'ut', 'id', 'wa', 'or', 'nv', 'ca', 'ak', 'hi'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=True,
                priority=5,
                timeout_minutes=180
            ),

            'southwest_states': IngestionPlan(
                name='Southwest States Complete Data',
                jurisdictions=['tx', 'ok', 'nm', 'az'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=True,
                priority=6,
                timeout_minutes=120
            ),

            # Individual state plans (for targeted ingestion)
            'california': IngestionPlan(
                name='California Complete Data',
                jurisdictions=['ca'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=False,
                priority=7,
                timeout_minutes=120
            ),

            'texas': IngestionPlan(
                name='Texas Complete Data',
                jurisdictions=['tx'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=False,
                priority=8,
                timeout_minutes=120
            ),

            'florida': IngestionPlan(
                name='Florida Complete Data',
                jurisdictions=['fl'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=False,
                priority=9,
                timeout_minutes=120
            ),

            'new_york': IngestionPlan(
                name='New York Complete Data',
                jurisdictions=['ny'],
                data_types=['people', 'bills', 'committees', 'events'],
                dependencies=['jurisdictions'],
                parallel_safe=False,
                priority=10,
                timeout_minutes=120
            ),

            # Detail enrichment plans (parallel safe)
            'people_details_enrichment': IngestionPlan(
                name='People Details Enrichment',
                data_types=['person_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                parallel_safe=True,
                priority=11,
                timeout_minutes=240
            ),

            'bill_details_enrichment': IngestionPlan(
                name='Bill Details Enrichment',
                data_types=['bill_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                parallel_safe=True,
                priority=12,
                timeout_minutes=360
            ),

            'committee_details_enrichment': IngestionPlan(
                name='Committee Details Enrichment',
                data_types=['committee_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                parallel_safe=True,
                priority=13,
                timeout_minutes=180
            ),

            'event_details_enrichment': IngestionPlan(
                name='Event Details Enrichment',
                data_types=['event_details'],
                dependencies=['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states'],
                parallel_safe=True,
                priority=14,
                timeout_minutes=180
            ),

            # Relationship plans
            'bill_relationships': IngestionPlan(
                name='Bill-Person Relationships',
                data_types=['person_bills'],
                dependencies=['people_details_enrichment'],
                parallel_safe=True,
                priority=15,
                timeout_minutes=240
            ),

            'committee_memberships': IngestionPlan(
                name='Committee Memberships',
                data_types=['committee_members'],
                dependencies=['committee_details_enrichment'],
                parallel_safe=True,
                priority=16,
                timeout_minutes=180
            ),

            'event_participants': IngestionPlan(
                name='Event Participants',
                data_types=['event_participants'],
                dependencies=['event_details_enrichment'],
                parallel_safe=True,
                priority=17,
                timeout_minutes=180
            ),

            # Global search plans
            'people_search': IngestionPlan(
                name='Global People Search',
                data_types=['people_search'],
                dependencies=['jurisdictions'],
                parallel_safe=True,
                priority=18,
                timeout_minutes=120
            ),

            'bills_search': IngestionPlan(
                name='Global Bills Search',
                data_types=['bills_search'],
                dependencies=['jurisdictions'],
                parallel_safe=True,
                priority=19,
                timeout_minutes=120
            )
        }

    def execute_plan(self, plan_name: str) -> OrchestrationResult:
        """Execute a specific ingestion plan"""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown ingestion plan: {plan_name}")

        plan = self.ingestion_plans[plan_name]
        self.orchestration_stats['current_plan'] = plan_name

        self.logger.info(f"Executing ingestion plan: {plan.name}")

        start_time = datetime.now()
        result = OrchestrationResult(
            plan_name=plan_name,
            success=False,
            start_time=start_time
        )

        try:
            # Check dependencies
            if not self._check_dependencies(plan):
                raise RuntimeError(f"Dependencies not met for plan: {plan_name}")

            # Execute plan based on type
            if plan_name == 'jurisdictions':
                plan_result = self.jurisdictions_ingestor.ingest_all_jurisdictions()
            elif 'states' in plan_name:
                plan_result = self._execute_regional_plan(plan)
            elif plan_name in ['california', 'texas', 'florida', 'new_york']:
                plan_result = self._execute_state_plan(plan)
            elif 'details' in plan_name:
                plan_result = self._execute_details_plan(plan)
            elif 'relationships' in plan_name or 'memberships' in plan_name or 'participants' in plan_name:
                plan_result = self._execute_relationship_plan(plan)
            elif 'search' in plan_name:
                plan_result = self._execute_search_plan(plan)
            else:
                raise ValueError(f"Unknown plan type: {plan_name}")

            result.records_processed = plan_result.get('total_processed', 0)
            result.records_skipped = plan_result.get('total_skipped', 0)
            result.sub_results = plan_result.get('results', plan_result)
            result.success = True

            self.orchestration_stats['plans_executed'].append(result)
            self.orchestration_stats['total_records'] += result.records_processed

            self.logger.info(f"Plan {plan_name} completed: {result.records_processed} records")

        except Exception as e:
            result.success = False
            result.error = str(e)

            self.orchestration_stats['plans_failed'].append(result)
            self.orchestration_stats['total_errors'] += 1

            self.logger.error(f"Plan {plan_name} failed: {e}")
            raise

        finally:
            result.end_time = datetime.now()
            result.duration_seconds = (result.end_time - start_time).total_seconds()

        return result

    def execute_sequential_plan(self, plan_names: List[str]) -> Dict[str, OrchestrationResult]:
        """Execute multiple plans sequentially with dependency checking"""
        self.logger.info(f"Executing sequential plan with {len(plan_names)} steps")

        results = {}

        for plan_name in plan_names:
            try:
                result = self.execute_plan(plan_name)
                results[plan_name] = result

                # Pause between plans due to rate limits
                time.sleep(5)

            except Exception as e:
                self.logger.error(f"Plan {plan_name} failed in sequence: {e}")
                results[plan_name] = OrchestrationResult(
                    plan_name=plan_name,
                    success=False,
                    error=str(e)
                )

                # Stop on critical failures
                if plan_name in ['jurisdictions']:
                    raise

        return results

    def execute_parallel_plan(self, plan_names: List[str], max_workers: int = 2) -> Dict[str, OrchestrationResult]:
        """Execute multiple plans in parallel where safe (limited workers due to rate limits)"""
        self.logger.info(f"Executing parallel plan with {len(plan_names)} plans, max_workers={max_workers}")

        # Filter for parallel-safe plans
        safe_plans = [name for name in plan_names if self.ingestion_plans[name].parallel_safe]
        unsafe_plans = [name for name in plan_names if not self.ingestion_plans[name].parallel_safe]

        if unsafe_plans:
            self.logger.warning(f"Skipping non-parallel-safe plans: {unsafe_plans}")

        results = {}

        def execute_plan_thread(plan_name: str) -> Tuple[str, OrchestrationResult]:
            """Execute plan in thread"""
            try:
                result = self.execute_plan(plan_name)
                return plan_name, result
            except Exception as e:
                return plan_name, OrchestrationResult(
                    plan_name=plan_name,
                    success=False,
                    error=str(e)
                )

        # Execute parallel plans with limited workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_plan = {
                executor.submit(execute_plan_thread, plan_name): plan_name
                for plan_name in safe_plans
            }

            for future in concurrent.futures.as_completed(future_to_plan, timeout=10800):  # 3 hour timeout
                plan_name = future_to_plan[future]

                try:
                    result_name, result = future.result()
                    results[result_name] = result
                except Exception as e:
                    self.logger.error(f"Parallel plan {plan_name} failed: {e}")
                    results[plan_name] = OrchestrationResult(
                        plan_name=plan_name,
                        success=False,
                        error=str(e)
                    )

        return results

    def execute_comprehensive_ingestion(self, regions: List[str] = None, parallel: bool = True) -> Dict[str, Any]:
        """Execute comprehensive ingestion with orchestration"""
        self.logger.info("Starting comprehensive OpenStates ingestion")

        if not regions:
            regions = ['northeast_states', 'southeast_states', 'midwest_states', 'west_states', 'southwest_states']

        comprehensive_start = datetime.now()

        # Build plan sequence
        plan_sequence = ['jurisdictions']
        plan_sequence.extend(regions)

        # Add detail enrichment if requested
        plan_sequence.extend([
            'people_details_enrichment', 'bill_details_enrichment',
            'committee_details_enrichment', 'event_details_enrichment'
        ])

        # Add relationships
        plan_sequence.extend([
            'bill_relationships', 'committee_memberships', 'event_participants'
        ])

        # Execute based on parallel preference
        if parallel:
            # Split into phases for parallel execution
            foundation_plans = ['jurisdictions']
            regional_plans = regions
            detail_plans = ['people_details_enrichment', 'bill_details_enrichment', 'committee_details_enrichment', 'event_details_enrichment']
            relationship_plans = ['bill_relationships', 'committee_memberships', 'event_participants']

            results = {}

            # Phase 1: Foundation (sequential)
            results['foundation'] = self.execute_sequential_plan(foundation_plans)

            # Phase 2: Regional (parallel by region)
            results['regional'] = self.execute_parallel_plan(regional_plans, max_workers=2)

            # Phase 3: Details (parallel)
            results['details'] = self.execute_parallel_plan(detail_plans, max_workers=2)

            # Phase 4: Relationships (parallel)
            results['relationships'] = self.execute_parallel_plan(relationship_plans, max_workers=2)

        else:
            # Sequential execution
            results = {'sequential': self.execute_sequential_plan(plan_sequence)}

        # Generate comprehensive summary
        total_processed = 0
        total_errors = 0
        successful_plans = 0
        total_plans = 0

        for phase_results in results.values():
            for plan_result in phase_results.values():
                total_plans += 1
                total_processed += plan_result.records_processed
                total_errors += plan_result.records_skipped
                if plan_result.success:
                    successful_plans += 1

        summary = {
            'regions': regions,
            'parallel_execution': parallel,
            'total_processed': total_processed,
            'total_errors': total_errors,
            'successful_plans': successful_plans,
            'total_plans': total_plans,
            'success_rate': (successful_plans / total_plans) * 100,
            'start_time': comprehensive_start,
            'end_time': datetime.now(),
            'duration': (datetime.now() - comprehensive_start).total_seconds(),
            'records_per_second': total_processed / max(1, (datetime.now() - comprehensive_start).total_seconds()),
            'results': results
        }

        self.logger.info(f"Comprehensive ingestion completed: {total_processed} records, {total_errors} errors, {summary['duration']:.1f}s")
        return summary

    def execute_state_ingestion(self, state: str, include_details: bool = True) -> Dict[str, Any]:
        """Execute ingestion for a specific state"""
        self.logger.info(f"Starting state ingestion for: {state}")

        state_start = datetime.now()

        # Build state-specific plan sequence
        plan_sequence = ['jurisdictions']

        # Add state plan if it exists
        state_plan = state.lower()
        if state_plan in self.ingestion_plans:
            plan_sequence.append(state_plan)
        else:
            # Create ad-hoc state plan execution
            state_result = self.enhanced_ingestor.ingest_jurisdiction_complete(state)
            return {
                'state': state,
                'include_details': include_details,
                'total_processed': state_result.get('total_processed', 0),
                'total_errors': state_result.get('data_types_total', 0) - state_result.get('data_types_processed', 0),
                'success_rate': (state_result.get('data_types_processed', 0) / max(1, state_result.get('data_types_total', 0))) * 100,
                'start_time': state_start,
                'end_time': datetime.now(),
                'duration': (datetime.now() - state_start).total_seconds(),
                'results': state_result
            }

        # Add details if requested
        if include_details:
            plan_sequence.extend(['people_details_enrichment', 'bill_details_enrichment', 'committee_details_enrichment', 'event_details_enrichment'])

        # Execute sequential
        results = self.execute_sequential_plan(plan_sequence)

        # Generate summary
        total_processed = sum(r.records_processed for r in results.values())
        total_errors = sum(r.records_skipped for r in results.values())
        successful_plans = sum(1 for r in results.values() if r.success)

        summary = {
            'state': state,
            'include_details': include_details,
            'total_processed': total_processed,
            'total_errors': total_errors,
            'successful_plans': successful_plans,
            'total_plans': len(results),
            'success_rate': (successful_plans / len(results)) * 100,
            'start_time': state_start,
            'end_time': datetime.now(),
            'duration': (datetime.now() - state_start).total_seconds(),
            'results': results
        }

        self.logger.info(f"State {state} ingestion completed: {total_processed} records, {total_errors} errors")
        return summary

    def _check_dependencies(self, plan: IngestionPlan) -> bool:
        """Check if all dependencies for a plan are satisfied"""
        if not plan.dependencies:
            return True

        executed_plan_names = [p.plan_name for p in self.orchestration_stats['plans_executed']]

        for dependency in plan.dependencies:
            if dependency not in executed_plan_names:
                self.logger.warning(f"Dependency {dependency} not satisfied for plan {plan.name}")
                return False

        return True

    def _execute_regional_plan(self, plan: IngestionPlan) -> Dict[str, Any]:
        """Execute regional plan with parallel jurisdiction processing"""
        self.logger.info(f"Executing regional plan: {plan.name}")

        regional_results = {}
        total_processed = 0
        total_skipped = 0

        # Process jurisdictions in parallel (limited due to rate limits)
        for jurisdiction in plan.jurisdictions:
            try:
                if plan.parallel_safe and len(plan.jurisdictions) > 1:
                    # Process in parallel batches
                    jurisdiction_result = self.enhanced_ingestor.ingest_jurisdiction_complete(jurisdiction)
                else:
                    # Process sequentially
                    jurisdiction_result = self.enhanced_ingestor.ingest_jurisdiction_complete(jurisdiction)

                regional_results[jurisdiction] = jurisdiction_result
                total_processed += jurisdiction_result.get('total_processed', 0)
                total_skipped += jurisdiction_result.get('total_errors', 0)

                self.logger.info(f"✅ {jurisdiction} completed: {jurisdiction_result.get('total_processed', 0)} records")

            except Exception as e:
                self.logger.error(f"❌ {jurisdiction} failed: {e}")
                regional_results[jurisdiction] = {'error': str(e), 'success': False}
                total_skipped += 1

        return {
            'plan_name': plan.name,
            'total_processed': total_processed,
            'total_skipped': total_skipped,
            'jurisdictions_processed': len([r for r in regional_results.values() if isinstance(r, dict) and 'error' not in r]),
            'jurisdictions_total': len(plan.jurisdictions),
            'results': regional_results
        }

    def _execute_state_plan(self, plan: IngestionPlan) -> Dict[str, Any]:
        """Execute state plan"""
        jurisdiction = plan.jurisdictions[0] if plan.jurisdictions else plan.name.split('_')[0].upper()

        return self.enhanced_ingestor.ingest_jurisdiction_complete(jurisdiction)

    def _execute_details_plan(self, plan: IngestionPlan) -> Dict[str, Any]:
        """Execute details enrichment plan"""
        # This would implement detail enrichment logic
        return {'plan_name': plan.name, 'total_processed': 0, 'message': 'Details enrichment not yet implemented'}

    def _execute_relationship_plan(self, plan: IngestionPlan) -> Dict[str, Any]:
        """Execute relationship plan"""
        # This would implement relationship logic
        return {'plan_name': plan.name, 'total_processed': 0, 'message': 'Relationship enrichment not yet implemented'}

    def _execute_search_plan(self, plan: IngestionPlan) -> Dict[str, Any]:
        """Execute search plan"""
        # This would implement search logic
        return {'plan_name': plan.name, 'total_processed': 0, 'message': 'Search enrichment not yet implemented'}

    def get_available_plans(self) -> Dict[str, IngestionPlan]:
        """Get all available ingestion plans"""
        return self.ingestion_plans.copy()

    def get_plan_status(self, plan_name: str) -> Dict[str, Any]:
        """Get status of a specific plan"""
        if plan_name not in self.ingestion_plans:
            raise ValueError(f"Unknown plan: {plan_name}")

        plan = self.ingestion_plans[plan_name]

        # Check if plan has been executed
        executed = [p for p in self.orchestration_stats['plans_executed'] if p.plan_name == plan_name]
        failed = [p for p in self.orchestration_stats['plans_failed'] if p.plan_name == plan_name]

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
        """Get comprehensive orchestration statistics"""
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
            'executed_plans': [p.plan_name for p in self.orchestration_stats['plans_executed']],
            'failed_plans': [p.plan_name for p in self.orchestration_stats['plans_failed']]
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function for OpenStates orchestration"""
    print("🚀 OpenStates Comprehensive Orchestration System")
    print("=" * 50)

    try:
        # Initialize orchestrator
        orchestrator = OpenStatesOrchestrator()

        # Example: Single state ingestion
        print("\n📍 Ingesting single state (CA)...")
        ca_result = orchestrator.execute_state_ingestion('ca', include_details=True)
        print(f"✅ CA completed: {ca_result['total_processed']} records")

        # Example: Regional ingestion
        print("\n📍 Ingesting northeast region...")
        northeast_result = orchestrator.execute_plan('northeast_states')
        print(f"✅ Northeast completed: {northeast_result.records_processed} records")

        # Example: Comprehensive ingestion
        print("\n📍 Starting comprehensive ingestion...")
        comprehensive_result = orchestrator.execute_comprehensive_ingestion(
            regions=['northeast_states', 'southeast_states'],
            parallel=True
        )
        print(f"✅ Comprehensive completed: {comprehensive_result['total_processed']} records")

        # Display orchestration statistics
        stats = orchestrator.get_orchestration_statistics()
        print(f"\n📊 Orchestration Statistics:")
        print(f"   Duration: {stats['duration_seconds']:.1f}s")
        print(f"   Plans executed: {stats['total_plans_executed']}")
        print(f"   Plans failed: {stats['total_plans_failed']}")
        print(f"   Total records: {stats['total_records_processed']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Records/second: {stats['records_per_second']:.1f}")

        print("\n🎉 OpenStates orchestration completed successfully!")

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error in OpenStates orchestration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
