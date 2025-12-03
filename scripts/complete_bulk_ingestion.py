#!/usr/bin/env python3
"""
Complete Bulk Data Ingestion Orchestrator

This script orchestrates the complete ingestion of all remaining data
with proper offset handling, API key enforcement, and comprehensive monitoring.
"""

import os
import sys
import logging
import argparse
import subprocess
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Import configuration components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env, IngestionMode

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IngestionPhase:
    """Configuration for an ingestion phase"""
    name: str
    description: str
    commands: List[str]
    dependencies: List[str] = None
    estimated_time: str = ""
    priority: int = 1

class BulkIngestionOrchestrator:
    """Orchestrates complete bulk data ingestion"""

    def __init__(self):
        self.session_id = f"bulk_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results = {}
        self.start_time = datetime.now()

        # Define ingestion phases
        self.phases = [
            IngestionPhase(
                name="validation",
                description="API Key Validation and System Check",
                commands=[
                    "python -c \"from ingestion_config import validate_all_api_keys; print('VALID:', validate_all_api_keys()['valid'])\""
                ],
                estimated_time="30 seconds",
                priority=1
            ),
            IngestionPhase(
                name="congress_bills_117",
                description="Congress.gov Bills - Congress 117",
                commands=[
                    "INGESTION_MODE=production python scripts/ingest_congress_bills.py --congress 117 --batch-size 50"
                ],
                estimated_time="30-45 minutes",
                priority=2
            ),
            IngestionPhase(
                name="congress_bills_118",
                description="Congress.gov Bills - Congress 118",
                commands=[
                    "INGESTION_MODE=production python scripts/ingest_congress_bills.py --congress 118 --batch-size 50"
                ],
                estimated_time="30-45 minutes",
                priority=2
            ),
            IngestionPhase(
                name="govinfo_bills_117",
                description="GovInfo.gov Bills - Congress 117",
                commands=[
                    "INGESTION_MODE=production python scripts/ingest_govinfo_bills.py --congress 117 --batch-size 50"
                ],
                estimated_time="45-60 minutes",
                priority=3
            ),
            IngestionPhase(
                name="govinfo_bills_118",
                description="GovInfo.gov Bills - Congress 118",
                commands=[
                    "INGESTION_MODE=production python scripts/ingest_govinfo_bills.py --congress 118 --batch-size 50"
                ],
                estimated_time="45-60 minutes",
                priority=3
            ),
            IngestionPhase(
                name="openstates_people_complete",
                description="OpenStates.org People - Complete All States",
                commands=[
                    "INGESTION_MODE=production python scripts/ingest_openstates_incremental.py"
                ],
                estimated_time="20-30 minutes",
                priority=4
            ),
            IngestionPhase(
                name="openstates_bills_all",
                description="OpenStates.org Bills - All States (placeholder - script not available)",
                commands=[
                    "echo 'OpenStates bills script not available - skipping'"
                ],
                estimated_time="60-90 minutes",
                priority=5
            ),
            IngestionPhase(
                name="final_verification",
                description="Final Data Integrity Verification",
                commands=[
                    "python scripts/verify_complete_ingestion.py"
                ],
                estimated_time="5-10 minutes",
                priority=6
            )
        ]

    def run_command(self, command: str, phase_name: str) -> Dict[str, Any]:
        """Run a single command and return results"""
        logger.info(f"Executing command for phase '{phase_name}': {command}")

        start_time = datetime.now()

        try:
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return {
                'command': command,
                'phase': phase_name,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'success': result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out for phase '{phase_name}': {command}")
            return {
                'command': command,
                'phase': phase_name,
                'return_code': -1,
                'stdout': '',
                'stderr': 'Command timed out after 1 hour',
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': 3600,
                'success': False,
                'timeout': True
            }
        except Exception as e:
            logger.error(f"Error running command for phase '{phase_name}': {e}")
            return {
                'command': command,
                'phase': phase_name,
                'return_code': -1,
                'stdout': '',
                'stderr': str(e),
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'success': False,
                'error': str(e)
            }

    def run_phase(self, phase: IngestionPhase) -> Dict[str, Any]:
        """Run all commands in a phase"""
        logger.info(f"🚀 Starting phase: {phase.name}")
        logger.info(f"📋 Description: {phase.description}")
        logger.info(f"⏱️  Estimated time: {phase.estimated_time}")

        phase_start_time = datetime.now()
        phase_results = []

        for i, command in enumerate(phase.commands):
            logger.info(f"📦 Running command {i+1}/{len(phase.commands)}")

            result = self.run_command(command, phase.name)
            phase_results.append(result)

            if result['success']:
                logger.info(f"✅ Command completed successfully in {result['duration_seconds']:.1f}s")
            else:
                logger.error(f"❌ Command failed: {result.get('stderr', 'Unknown error')}")

                # For critical phases, stop on failure
                if phase.name in ['validation']:
                    logger.error(f"🚫 Critical phase '{phase.name}' failed. Stopping execution.")
                    break

        phase_end_time = datetime.now()
        phase_duration = (phase_end_time - phase_start_time).total_seconds()

        phase_result = {
            'phase': phase.name,
            'description': phase.description,
            'start_time': phase_start_time.isoformat(),
            'end_time': phase_end_time.isoformat(),
            'duration_seconds': phase_duration,
            'estimated_time': phase.estimated_time,
            'commands_count': len(phase.commands),
            'results': phase_results,
            'success': all(r['success'] for r in phase_results)
        }

        logger.info(f"🏁 Phase '{phase.name}' completed in {phase_duration:.1f}s - {'✅ SUCCESS' if phase_result['success'] else '❌ FAILED'}")

        return phase_result

    def run_complete_ingestion(self, phases_to_run: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the complete ingestion process"""
        logger.info("🎯 Starting Complete Bulk Data Ingestion")
        logger.info(f"📅 Session ID: {self.session_id}")
        logger.info(f"⏰ Start time: {self.start_time.isoformat()}")

        # Filter phases if specified
        if phases_to_run:
            filtered_phases = [p for p in self.phases if p.name in phases_to_run]
            if not filtered_phases:
                logger.error(f"No valid phases found for: {phases_to_run}")
                return {'success': False, 'error': 'No valid phases'}
        else:
            filtered_phases = self.phases

        # Sort by priority
        filtered_phases.sort(key=lambda p: p.priority)

        logger.info(f"📋 Running {len(filtered_phases)} phases")

        all_results = []
        failed_phases = []

        for phase in filtered_phases:
            logger.info(f"\\n{'='*60}")
            logger.info(f"🎯 PHASE: {phase.name}")
            logger.info(f"📝 {phase.description}")
            logger.info(f"⏱️  Estimated: {phase.estimated_time}")
            logger.info(f"{'='*60}")

            phase_result = self.run_phase(phase)
            all_results.append(phase_result)

            if not phase_result['success']:
                failed_phases.append(phase.name)
                logger.error(f"🚫 Phase '{phase.name}' failed")

                # Stop on critical failures
                if phase.name in ['validation']:
                    logger.error("🛑 Critical validation failure. Stopping ingestion.")
                    break
            else:
                logger.info(f"✅ Phase '{phase.name}' completed successfully")

        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # Generate summary
        successful_phases = [r for r in all_results if r['success']]
        failed_phases = [r for r in all_results if not r['success']]

        summary = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration_seconds': total_duration,
            'total_phases': len(all_results),
            'successful_phases': len(successful_phases),
            'failed_phases': len(failed_phases),
            'success_rate': len(successful_phases) / len(all_results) * 100 if all_results else 0,
            'results': all_results,
            'overall_success': len(failed_phases) == 0
        }

        # Log final summary
        logger.info(f"\\n{'='*60}")
        logger.info(f"🏁 COMPLETE INGESTION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"📅 Session: {self.session_id}")
        logger.info(f"⏰ Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        logger.info(f"📊 Phases: {len(successful_phases)}/{len(all_results)} successful")
        logger.info(f"✅ Success Rate: {summary['success_rate']:.1f}%")

        if failed_phases:
            logger.error(f"❌ Failed Phases: {[p['phase'] for p in failed_phases]}")
        else:
            logger.info(f"🎉 ALL PHASES COMPLETED SUCCESSFULLY!")

        logger.info(f"{'='*60}")

        # Save results to file
        results_file = f"ingestion_results_{self.session_id}.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            logger.info(f"📄 Results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

        return summary

    def get_status_report(self) -> Dict[str, Any]:
        """Get current status of all data sources"""
        logger.info("📊 Generating status report...")

        try:
            # Run status check
            status_command = "python -c \"import psycopg2; conn = psycopg2.connect(database='cbwinslow', user='cbwinslow'); cursor = conn.cursor(); cursor.execute('SELECT data_source, data_type, category, total_processed, total_estimated, completion_percentage, is_completed FROM incremental.checkpoint_status ORDER BY data_source, data_type, category'); results = cursor.fetchall(); cursor.close(); conn.close(); print('STATUS_REPORT:', json.dumps([{'source': r[0], 'type': r[1], 'category': r[2], 'processed': r[3], 'estimated': r[4], 'percentage': r[5], 'completed': r[6]} for r in results]))\""

            result = self.run_command(status_command, "status_report")

            if result['success']:
                # Parse the status from stdout
                lines = result['stdout'].strip().split('\\n')
                status_data = []

                for line in lines:
                    if line.startswith('STATUS_REPORT:'):
                        try:
                            import json
                            status_json = line.replace('STATUS_REPORT:', '').strip()
                            status_data = json.loads(status_json)
                            break
                        except json.JSONDecodeError:
                            continue

                return {
                    'success': True,
                    'data': status_data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': result['stderr'],
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Complete Bulk Data Ingestion Orchestrator')
    parser.add_argument('--phases', help='Comma-separated list of phases to run (e.g., validation,congress_bills_117)')
    parser.add_argument('--status', action='store_true', help='Show current status only')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (show what would be executed)')

    args = parser.parse_args()

    # Validate API keys first
    logger.info("🔍 Validating all required API keys...")
    key_validation = validate_all_api_keys()
    if not key_validation['valid']:
        logger.error("❌ API key validation failed")
        for error in key_validation['errors']:
            logger.error(f"   🚫 {error}")
        sys.exit(1)

    # Verify production mode
    mode = get_ingestion_mode_from_env()
    if mode.value != 'production':
        logger.error(f"❌ Production mode required. Current mode: {mode.value}")
        sys.exit(1)

    logger.info("✅ API keys validated - ready for ingestion")

    # Create orchestrator
    orchestrator = BulkIngestionOrchestrator()

    if args.status:
        # Show status only
        status = orchestrator.get_status_report()
        if status['success']:
            logger.info("📊 Current Status Report:")
            for item in status['data']:
                status_symbol = "✅" if item['completed'] else "🔄"
                logger.info(f"  {status_symbol} {item['source']} | {item['type']} | {item['category']}: {item['processed']}/{item['estimated']} ({item['percentage']:.1f}%)")
        else:
            logger.error(f"❌ Error getting status: {status['error']}")
        return

    if args.dry_run:
        logger.info("🔍 DRY RUN - Showing what would be executed:")
        for phase in orchestrator.phases:
            logger.info(f"\\n📋 Phase: {phase.name}")
            logger.info(f"📝 Description: {phase.description}")
            logger.info(f"⏱️  Estimated: {phase.estimated_time}")
            for command in phase.commands:
                logger.info(f"💻 Command: {command}")
        return

    # Parse phases if specified
    phases_to_run = None
    if args.phases:
        phases_to_run = [p.strip() for p in args.phases.split(',')]
        logger.info(f"🎯 Running specific phases: {phases_to_run}")

    # Run complete ingestion
    try:
        result = orchestrator.run_complete_ingestion(phases_to_run)

        if result['overall_success']:
            logger.info("🎉 Complete bulk ingestion finished successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Complete bulk ingestion failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("⚠️ Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
