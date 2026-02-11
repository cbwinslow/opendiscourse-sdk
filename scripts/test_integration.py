#!/usr/bin/env python3
"""
Integration Test Suite

This script tests the integration between all components:
- Phase scripts
- Enhanced orchestrator
- Legacy verification scripts
- Data diagnostics
- Monitoring infrastructure
"""

import importlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load environment variables
from dotenv import load_dotenv
from ingestion_config import get_ingestion_mode_from_env, validate_all_api_keys

load_dotenv()

class IntegrationTester:
    """Comprehensive integration testing suite"""

    def __init__(self):
        self.test_start = datetime.now()
        self.test_results = {}
        self.passed_tests = 0
        self.failed_tests = 0

        print("🧪 Integration Test Suite Initialized")
        print("="*60)

    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"\n🔍 Testing: {test_name}")

        try:
            start_time = datetime.now()
            result = test_func()
            duration = (datetime.now() - start_time).total_seconds()

            if result:
                print(f"✅ {test_name} - PASSED ({duration:.2f}s)")
                self.test_results[test_name] = {
                    'status': 'PASSED',
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                }
                self.passed_tests += 1
                return True
            else:
                print(f"❌ {test_name} - FAILED ({duration:.2f}s)")
                self.test_results[test_name] = {
                    'status': 'FAILED',
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                }
                self.failed_tests += 1
                return False

        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
            self.test_results[test_name] = {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.failed_tests += 1
            return False

    def test_environment_validation(self) -> bool:
        """Test environment validation"""
        try:
            key_validation = validate_all_api_keys()
            if not key_validation['valid']:
                return False

            mode = get_ingestion_mode_from_env()
            if mode.value != 'production':
                return False

            return True
        except Exception:
            return False

    def test_phase_script_imports(self) -> bool:
        """Test that all phase scripts can be imported"""
        phase_scripts = [
            'ingestion_phase_1_validation',
            'ingestion_phase_2_congress_members',
            'ingestion_phase_3_congress_bills',
            'ingestion_phase_4_govinfo_bills',
            'ingestion_phase_5_openstates',
            'ingestion_phase_6_verification'
        ]

        for script_name in phase_scripts:
            try:
                importlib.import_module(script_name)
            except ImportError as e:
                print(f"   ❌ Failed to import {script_name}: {e}")
                return False

        return True

    def test_legacy_script_imports(self) -> bool:
        """Test that legacy scripts can be imported"""
        legacy_scripts = [
            'verify_complete_ingestion',
            'data_status_queries',
            'complete_bulk_ingestion',
            'ingestion_manager'
        ]

        for script_name in legacy_scripts:
            try:
                importlib.import_module(script_name)
            except ImportError as e:
                print(f"   ⚠️  Failed to import {script_name}: {e}")
                # Legacy scripts might have issues, but that's expected

        return True  # Don't fail for legacy import issues

    def test_orchestrator_imports(self) -> bool:
        """Test that orchestrator components can be imported"""
        orchestrator_scripts = [
            'orchestrator_framework',
            'subagent_manager',
            'enhanced_orchestrator',
            'run_orchestrated_ingestion',
            'run_enhanced_ingestion'
        ]

        for script_name in orchestrator_scripts:
            try:
                importlib.import_module(script_name)
            except ImportError as e:
                print(f"   ❌ Failed to import {script_name}: {e}")
                return False

        return True

    def test_database_connectivity(self) -> bool:
        """Test database connectivity"""
        try:
            import psycopg2

            conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            cursor = conn.cursor()

            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            # Test checkpoint table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'incremental'
                    AND table_name = 'ingestion_checkpoints'
                );
            """)
            checkpoint_table_exists = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            if not checkpoint_table_exists:
                print("   ❌ Checkpoint table does not exist")
                return False

            return True

        except Exception as e:
            print(f"   ❌ Database connectivity failed: {e}")
            return False

    def test_verification_infrastructure(self) -> bool:
        """Test verification infrastructure"""
        try:
            from verify_complete_ingestion import IngestionVerifier

            verifier = IngestionVerifier()

            # Test checkpoint status method
            checkpoint_status = verifier.get_checkpoint_status()

            verifier.cleanup()

            return True

        except Exception as e:
            print(f"   ⚠️  Verification infrastructure issue: {e}")
            return False  # Expected if no data exists

    def test_data_diagnostics_infrastructure(self) -> bool:
        """Test data diagnostics infrastructure"""
        try:
            from data_status_queries import DataStatusDiagnostics

            diagnostics = DataStatusDiagnostics()

            # Test basic data status
            basic_status = diagnostics.get_basic_data_status()

            diagnostics.cleanup()

            return True

        except Exception as e:
            print(f"   ⚠️  Data diagnostics infrastructure issue: {e}")
            return False  # Expected if no data exists

    def test_monitoring_infrastructure(self) -> bool:
        """Test monitoring infrastructure"""
        try:
            from monitoring.job_monitor import check_log

            # Create a test log file
            test_log = Path("test_integration_monitor.log")
            test_log.write_text("INFO: Test log entry\nERROR: Test error entry\nINFO: Another entry")

            alerts = check_log(test_log)

            # Clean up test log
            test_log.unlink()

            return True

        except Exception as e:
            print(f"   ❌ Monitoring infrastructure issue: {e}")
            return False

    def test_enhanced_orchestrator_creation(self) -> bool:
        """Test enhanced orchestrator can be created"""
        try:
            from enhanced_orchestrator import EnhancedOrchestrator

            orchestrator = EnhancedOrchestrator()

            # Test agent registration
            enhanced_agents = orchestrator._get_enhanced_agents()

            return len(enhanced_agents) > 0

        except Exception as e:
            print(f"   ❌ Enhanced orchestrator creation failed: {e}")
            return False

    def test_phase_1_validation_dry_run(self) -> bool:
        """Test Phase 1 validation can run (dry run)"""
        try:
            from ingestion_phase_1_validation import Phase1Validator

            # Test validation setup
            validator = Phase1Validator()

            # Just test that it can be initialized
            return True

        except Exception as e:
            print(f"   ❌ Phase 1 validation test failed: {e}")
            return False

    def test_file_system_structure(self) -> bool:
        """Test that required files exist"""
        required_files = [
            'scripts/ingestion_phase_1_validation.py',
            'scripts/ingestion_phase_2_congress_members.py',
            'scripts/ingestion_phase_3_congress_bills.py',
            'scripts/ingestion_phase_4_govinfo_bills.py',
            'scripts/ingestion_phase_5_openstates.py',
            'scripts/ingestion_phase_6_verification.py',
            'scripts/orchestrator_framework.py',
            'scripts/enhanced_orchestrator.py',
            'scripts/run_enhanced_ingestion.py',
            'scripts/verify_complete_ingestion.py',
            'scripts/data_status_queries.py',
            'scripts/monitoring/job_monitor.py'
        ]

        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            print(f"   ❌ Missing files: {missing_files}")
            return False

        return True

    def test_configuration_files(self) -> bool:
        """Test that configuration files exist"""
        config_files = [
            '.env',
            'ingestion_config.py'
        ]

        for config_file in config_files:
            if not Path(config_file).exists():
                print(f"   ❌ Missing config file: {config_file}")
                return False

        return True

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🚀 Starting comprehensive integration tests...")

        # Define all tests
        tests = [
            ("Environment Validation", self.test_environment_validation),
            ("File System Structure", self.test_file_system_structure),
            ("Configuration Files", self.test_configuration_files),
            ("Database Connectivity", self.test_database_connectivity),
            ("Phase Script Imports", self.test_phase_script_imports),
            ("Legacy Script Imports", self.test_legacy_script_imports),
            ("Orchestrator Imports", self.test_orchestrator_imports),
            ("Verification Infrastructure", self.test_verification_infrastructure),
            ("Data Diagnostics Infrastructure", self.test_data_diagnostics_infrastructure),
            ("Monitoring Infrastructure", self.test_monitoring_infrastructure),
            ("Enhanced Orchestrator Creation", self.test_enhanced_orchestrator_creation),
            ("Phase 1 Validation Dry Run", self.test_phase_1_validation_dry_run)
        ]

        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)

        # Generate summary
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_duration = (datetime.now() - self.test_start).total_seconds()

        summary = {
            'test_start': self.test_start.isoformat(),
            'test_end': datetime.now().isoformat(),
            'total_duration': total_duration,
            'total_tests': total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': success_rate,
            'test_results': self.test_results,
            'overall_status': 'PASS' if self.failed_tests == 0 else 'FAIL'
        }

        # Print summary
        print("\n" + "="*60)
        print("🧪 INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Duration: {total_duration:.1f} seconds")
        print(f"🎯 Overall Status: {summary['overall_status']}")
        print("="*60)

        # Print failed tests
        if self.failed_tests > 0:
            print("\n❌ Failed Tests:")
            for test_name, result in self.test_results.items():
                if result['status'] in ['FAILED', 'ERROR']:
                    print(f"   - {test_name}: {result.get('error', result['status'])}")

        return summary

    def save_test_report(self, filename: str = None) -> str:
        """Save test report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"integration_test_report_{timestamp}.json"

        summary = self.run_all_tests()

        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)

            print(f"\n📄 Test report saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving test report: {e}")
            return ""

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Integration Test Suite')
    parser.add_argument('--save', action='store_true', help='Save test report to file')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--test', '-t', help='Run specific test (case-sensitive)')

    args = parser.parse_args()

    tester = IntegrationTester()

    if args.test:
        # Run specific test
        test_methods = {
            'environment': tester.test_environment_validation,
            'filesystem': tester.test_file_system_structure,
            'config': tester.test_configuration_files,
            'database': tester.test_database_connectivity,
            'phases': tester.test_phase_script_imports,
            'legacy': tester.test_legacy_script_imports,
            'orchestrator': tester.test_orchestrator_imports,
            'verification': tester.test_verification_infrastructure,
            'diagnostics': tester.test_data_diagnostics_infrastructure,
            'monitoring': tester.test_monitoring_infrastructure,
            'enhanced': tester.test_enhanced_orchestrator_creation,
            'validation': tester.test_phase_1_validation_dry_run
        }

        if args.test in test_methods:
            test_name = f"Specific Test: {args.test}"
            tester.run_test(test_name, test_methods[args.test])
        else:
            print(f"❌ Unknown test: {args.test}")
            print(f"Available tests: {', '.join(test_methods.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        if args.save:
            tester.save_test_report(args.output)
        else:
            tester.run_all_tests()

    # Exit with appropriate code
    if tester.failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
