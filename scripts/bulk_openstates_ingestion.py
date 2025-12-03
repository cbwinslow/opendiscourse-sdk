#!/usr/bin/env python3
"""
Enhanced OpenStates Bulk Data Ingestion Script
Comprehensive ingestion for all jurisdictions with optimized pagination (200 per page)
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import validate_api_keys


class BulkOpenStatesIngestor:
    """Comprehensive bulk ingestion orchestrator for all OpenStates data"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.validate_environment()

        # Define all jurisdictions for comprehensive coverage
        self.all_states = [
            'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
            'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
            'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
            'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
            'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy',
            'dc', 'pr', 'vi', 'gu', 'as', 'mp'
        ]

        # Regional groupings for parallel processing
        self.regions = {
            'northeast': ['ct', 'me', 'ma', 'nh', 'ri', 'vt', 'ny', 'pa', 'nj', 'de', 'md', 'dc'],
            'southeast': ['wv', 'va', 'ky', 'tn', 'nc', 'sc', 'ga', 'al', 'ms', 'ar', 'la', 'fl'],
            'midwest': ['oh', 'mi', 'in', 'il', 'wi', 'mn', 'ia', 'mo', 'ks', 'ne', 'sd', 'nd'],
            'southwest': ['tx', 'ok', 'ar', 'la', 'nm'],
            'west': ['mt', 'wy', 'co', 'nm', 'az', 'ut', 'nv', 'ca', 'or', 'wa', 'ak', 'hi'],
            'territories': ['pr', 'vi', 'gu', 'as', 'mp']
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def validate_environment(self):
        """Validate API keys and environment"""
        self.logger.info("🔍 Validating environment...")

        api_keys = validate_api_keys()
        if not api_keys.get('openstates.org'):
            raise ValueError("OpenStates API key validation failed")

        # Check ingestion mode
        ingestion_mode = os.getenv('INGESTION_MODE', 'development')
        if ingestion_mode != 'production':
            self.logger.warning(f"⚠️  Ingestion mode: {ingestion_mode} (should be 'production')")
        else:
            self.logger.info("✅ Production mode confirmed")

        self.logger.info("✅ Environment validation passed")

    def run_command(self, command: List[str], description: str) -> Dict[str, Any]:
        """Execute a command and return results"""
        self.logger.info(f"🚀 {description}")

        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                self.logger.info(f"✅ {description} completed in {duration:.1f}s")
                return {
                    'success': True,
                    'duration': duration,
                    'output': result.stdout,
                    'description': description
                }
            else:
                self.logger.error(f"❌ {description} failed: {result.stderr}")
                return {
                    'success': False,
                    'duration': duration,
                    'error': result.stderr,
                    'description': description
                }

        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ {description} timed out")
            return {
                'success': False,
                'duration': 3600,
                'error': 'Command timed out after 1 hour',
                'description': description
            }
        except Exception as e:
            self.logger.error(f"💥 {description} crashed: {str(e)}")
            return {
                'success': False,
                'duration': 0,
                'error': str(e),
                'description': description
            }

    def ingest_single_state(self, state: str, data_types: str = "people,bills,committees,events") -> Dict[str, Any]:
        """Ingest single state with all data types"""
        command = [
            'python', 'enhanced_openstates_cli.py', 'ingest',
            '--jurisdiction', state,
            '--batch-size', '200',
            '--include-details',
            '--data-types', data_types
        ]

        description = f"State ingestion: {state.upper()}"
        return self.run_command(command, description)

    def ingest_region(self, region_name: str, states: List[str]) -> Dict[str, Any]:
        """Ingest entire region with parallel processing"""
        self.logger.info(f"🌎 Starting regional ingestion: {region_name.upper()}")

        # First ingest jurisdictions foundation
        foundation_result = self.run_command([
            'python', 'openstates_jurisdictions_ingestion.py'
        ], f"Jurisdictions foundation for {region_name}")

        if not foundation_result['success']:
            return foundation_result

        # Then ingest states in parallel (simulated sequential for now)
        region_results = []
        for state in states:
            result = self.ingest_single_state(state)
            region_results.append(result)

            if not result['success']:
                self.logger.warning(f"⚠️  State {state} failed, continuing with region")

        # Calculate regional statistics
        successful_states = sum(1 for r in region_results if r['success'])
        total_duration = sum(r['duration'] for r in region_results)

        return {
            'success': successful_states > 0,
            'duration': total_duration,
            'successful_states': successful_states,
            'total_states': len(states),
            'state_results': region_results,
            'description': f"Regional ingestion: {region_name}"
        }

    def ingest_all_states_sequential(self) -> Dict[str, Any]:
        """Ingest all states sequentially for maximum reliability"""
        self.logger.info("🇺🇸 Starting comprehensive national ingestion (sequential)")

        all_results = []
        start_time = time.time()

        # Ensure jurisdictions are loaded first
        self.logger.info("🏛️  Loading jurisdictions foundation...")
        foundation_result = self.run_command([
            'python', 'openstates_jurisdictions_ingestion.py'
        ], "National jurisdictions foundation")

        if not foundation_result['success']:
            return foundation_result

        # Ingest all states
        for i, state in enumerate(self.all_states, 1):
            self.logger.info(f"📊 Progress: {i}/{len(self.all_states)} - {state.upper()}")

            result = self.ingest_single_state(state)
            all_results.append(result)

            # Rate limiting between states
            if i < len(self.all_states):
                self.logger.info("⏱️  State-level rate limiting pause...")
                time.sleep(2)  # 2 second pause between states

        # Calculate final statistics
        successful_states = sum(1 for r in all_results if r['success'])
        total_duration = time.time() - start_time

        return {
            'success': successful_states > 0,
            'duration': total_duration,
            'successful_states': successful_states,
            'total_states': len(self.all_states),
            'state_results': all_results,
            'description': 'National comprehensive ingestion'
        }

    def ingest_all_states_parallel(self) -> Dict[str, Any]:
        """Ingest all states using regional parallel strategy"""
        self.logger.info("🇺🇸 Starting comprehensive national ingestion (parallel regions)")

        all_region_results = []
        start_time = time.time()

        # Load jurisdictions foundation
        foundation_result = self.run_command([
            'python', 'openstates_jurisdictions_ingestion.py'
        ], "National jurisdictions foundation")

        if not foundation_result['success']:
            return foundation_result

        # Process each region
        for region_name, states in self.regions.items():
            if region_name == 'territories':  # Skip territories for main run
                continue

            result = self.ingest_region(region_name, states)
            all_region_results.append(result)

            # Brief pause between regions
            if region_name != list(self.regions.keys())[-1]:
                self.logger.info("⏱️  Regional pause...")
                time.sleep(5)

        # Calculate comprehensive statistics
        successful_regions = sum(1 for r in all_region_results if r['success'])
        total_successful_states = sum(r.get('successful_states', 0) for r in all_region_results)
        total_duration = time.time() - start_time

        return {
            'success': successful_regions > 0,
            'duration': total_duration,
            'successful_regions': successful_regions,
            'total_regions': len([r for r in self.regions.keys() if r != 'territories']),
            'successful_states': total_successful_states,
            'total_states': sum(len(states) for region_name, states in self.regions.items() if region_name != 'territories'),
            'region_results': all_region_results,
            'description': 'National parallel regional ingestion'
        }

    def generate_ingestion_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive ingestion report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🎉 Enhanced OpenStates Bulk Ingestion Report
{'=' * 60}
Generated: {timestamp}
Description: {results['description']}

📊 Overall Results:
   Success: {'✅ YES' if results['success'] else '❌ NO'}
   Duration: {results['duration']:.1f} seconds ({results['duration']/3600:.1f} hours)

"""

        if 'successful_states' in results:
            report += f"""
📋 State Coverage:
   Successful States: {results.get('successful_states', 0)}/{results.get('total_states', 0)}
   Success Rate: {(results.get('successful_states', 0) / max(results.get('total_states', 1), 1) * 100):.1f}%

"""

        if 'successful_regions' in results:
            report += f"""
🌎 Regional Coverage:
   Successful Regions: {results.get('successful_regions', 0)}/{results.get('total_regions', 0)}
   Regional Success Rate: {(results.get('successful_regions', 0) / max(results.get('total_regions', 1), 1) * 100):.1f}%

"""

        # Add failed items if any
        if 'state_results' in results:
            failed_states = [r for r in results['state_results'] if not r['success']]
            if failed_states:
                report += "❌ Failed States:\n"
                for failed in failed_states[:10]:  # Limit to first 10
                    report += f"   - {failed['description']}: {failed.get('error', 'Unknown error')[:100]}...\n"
                if len(failed_states) > 10:
                    report += f"   ... and {len(failed_states) - 10} more failures\n"

        report += f"""
🚀 Performance Metrics:
   Average time per state: {results['duration'] / max(results.get('total_states', 1), 1):.1f} seconds
   Records per hour: {3600 / max(results['duration'] / max(results.get('successful_states', 1), 1), 1):.0f}

📋 Configuration:
   Batch Size: 200 records per page
   Rate Limiting: 1000 requests/hour
   Pagination: Optimized with offset tracking
   Data Types: people, bills, committees, events

🔧 Next Steps:
   1. Review any failed states and retry individually
   2. Run detailed enrichment for successful states
   3. Generate comprehensive data quality reports
   4. Set up automated monitoring for future ingestions

{'=' * 60}
"""

        return report

    def save_report(self, report: str, filename: str = None):
        """Save ingestion report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bulk_ingestion_report_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(report)

        self.logger.info(f"📄 Report saved to: {filename}")


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced OpenStates Bulk Ingestion')
    parser.add_argument('--mode', choices=['sequential', 'parallel', 'sample'],
                       default='sample', help='Ingestion mode')
    parser.add_argument('--states', nargs='+', help='Specific states to ingest')
    parser.add_argument('--regions', nargs='+', help='Specific regions to ingest')
    parser.add_argument('--report-file', help='Custom report filename')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without executing')

    args = parser.parse_args()

    ingestor = BulkOpenStatesIngestor()

    if args.dry_run:
        ingestor.logger.info("🔍 DRY RUN MODE - Showing execution plan:")
        if args.states:
            ingestor.logger.info(f"   States: {args.states}")
        if args.regions:
            ingestor.logger.info(f"   Regions: {args.regions}")
        if args.mode == 'sequential':
            ingestor.logger.info(f"   Mode: Sequential all states ({len(ingestor.all_states)} states)")
        elif args.mode == 'parallel':
            ingestor.logger.info(f"   Mode: Parallel regions ({len(ingestor.regions)} regions)")
        else:
            ingestor.logger.info(f"   Mode: Sample (CA, TX, NY, FL)")
        return

    results = None

    if args.states:
        # Ingest specific states
        all_results = []
        for state in args.states:
            result = ingestor.ingest_single_state(state)
            all_results.append(result)

        successful = sum(1 for r in all_results if r['success'])
        results = {
            'success': successful > 0,
            'duration': sum(r['duration'] for r in all_results),
            'successful_states': successful,
            'total_states': len(args.states),
            'state_results': all_results,
            'description': f'Specific states ingestion: {", ".join(args.states)}'
        }

    elif args.regions:
        # Ingest specific regions
        all_results = []
        for region in args.regions:
            if region in ingestor.regions:
                result = ingestor.ingest_region(region, ingestor.regions[region])
                all_results.append(result)

        results = {
            'success': any(r['success'] for r in all_results),
            'duration': sum(r['duration'] for r in all_results),
            'successful_regions': sum(1 for r in all_results if r['success']),
            'total_regions': len(args.regions),
            'region_results': all_results,
            'description': f'Specific regions ingestion: {", ".join(args.regions)}'
        }

    elif args.mode == 'sequential':
        # Sequential national ingestion
        results = ingestor.ingest_all_states_sequential()

    elif args.mode == 'parallel':
        # Parallel regional ingestion
        results = ingestor.ingest_all_states_parallel()

    else:
        # Sample mode - ingest a few representative states
        sample_states = ['ca', 'tx', 'ny', 'fl', 'pa']
        all_results = []
        for state in sample_states:
            result = ingestor.ingest_single_state(state)
            all_results.append(result)

        successful = sum(1 for r in all_results if r['success'])
        results = {
            'success': successful > 0,
            'duration': sum(r['duration'] for r in all_results),
            'successful_states': successful,
            'total_states': len(sample_states),
            'state_results': all_results,
            'description': f'Sample ingestion: {", ".join(sample_states)}'
        }

    # Generate and save report
    report = ingestor.generate_ingestion_report(results)
    ingestor.save_report(report, args.report_file)

    # Print summary
    print(report)

    return results


if __name__ == "__main__":
    main()
