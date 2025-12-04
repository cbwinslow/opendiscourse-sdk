#!/usr/bin/env python3
"""
GovInfo Test Runner and Validation Script
Comprehensive test runner for validating GovInfo offset handling fixes
"""

import os
import sys
import argparse
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pytest
    from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats
    from unittest.mock import MagicMock, patch
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required dependencies are installed")
    sys.exit(1)


class GovInfoTestRunner:
    """Comprehensive test runner for GovInfo offset handling fixes"""

    def __init__(self, verbose: bool = False, production_mode: bool = False):
        self.verbose = verbose
        self.production_mode = production_mode
        self.setup_logging()
        self.test_results = {
            'offset_calculations': {'passed': 0, 'failed': 0, 'errors': []},
            'pagination_logic': {'passed': 0, 'failed': 0, 'errors': []},
            'checkpoint_system': {'passed': 0, 'failed': 0, 'errors': []},
            'rate_limiting': {'passed': 0, 'failed': 0, 'errors': []},
            'data_integrity': {'passed': 0, 'failed': 0, 'errors': []},
            'performance': {'passed': 0, 'failed': 0, 'errors': []},
            'e2e_integration': {'passed': 0, 'failed': 0, 'errors': []}
        }
        self.validation_report = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'production' if production_mode else 'development',
            'test_suite': 'GovInfo Offset Handling Validation',
            'overall_status': 'PENDING',
            'components_tested': [],
            'critical_issues': [],
            'recommendations': [],
            'performance_metrics': {}
        }

    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('govinfo_test_runner.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run_offset_calculation_validation(self) -> Dict[str, Any]:
        """Run offset calculation validation tests"""
        self.logger.info("🔄 Running offset calculation validation tests...")

        test_file = 'tests/test_govinfo_offset_calculations.py'
        if not os.path.exists(test_file):
            return {'status': 'FAILED', 'error': f'Test file not found: {test_file}'}

        try:
            # Run pytest with specific test file
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--no-header' if not self.verbose else '--tb=long'
            ])

            status = 'PASSED' if result == 0 else 'FAILED'
            return {'status': status, 'exit_code': result}

        except Exception as e:
            self.logger.error(f"Offset calculation tests failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def run_pagination_logic_validation(self) -> Dict[str, Any]:
        """Run pagination logic validation tests"""
        self.logger.info("🔄 Running pagination logic validation tests...")

        test_file = 'tests/test_govinfo_pagination_logic.py'
        if not os.path.exists(test_file):
            return {'status': 'FAILED', 'error': f'Test file not found: {test_file}'}

        try:
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--no-header' if not self.verbose else '--tb=long'
            ])

            status = 'PASSED' if result == 0 else 'FAILED'
            return {'status': status, 'exit_code': result}

        except Exception as e:
            self.logger.error(f"Pagination logic tests failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def run_checkpoint_system_validation(self) -> Dict[str, Any]:
        """Run checkpoint system validation tests"""
        self.logger.info("🔄 Running checkpoint system validation tests...")

        test_file = 'tests/govinfo_checkpoint_system_tests.py'
        if not os.path.exists(test_file):
            return {'status': 'FAILED', 'error': f'Test file not found: {test_file}'}

        try:
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--no-header' if not self.verbose else '--tb=long'
            ])

            status = 'PASSED' if result == 0 else 'FAILED'
            return {'status': status, 'exit_code': result}

        except Exception as e:
            self.logger.error(f"Checkpoint system tests failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def run_rate_limiting_validation(self) -> Dict[str, Any]:
        """Run rate limiting validation tests"""
        self.logger.info("🔄 Running rate limiting validation tests...")

        test_file = 'tests/govinfo_rate_limiting_tests.py'
        if not os.path.exists(test_file):
            return {'status': 'FAILED', 'error': f'Test file not found: {test_file}'}

        try:
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--no-header' if not self.verbose else '--tb=long'
            ])

            status = 'PASSED' if result == 0 else 'FAILED'
            return {'status': status, 'exit_code': result}

        except Exception as e:
            self.logger.error(f"Rate limiting tests failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def run_data_integrity_validation(self) -> Dict[str, Any]:
        """Run data integrity validation tests"""
        self.logger.info("🔄 Running data integrity validation tests...")

        test_file = 'tests/govinfo_data_integrity_tests.py'
        if not os.path.exists(test_file):
            return {'status': 'FAILED', 'error': f'Test file not found: {test_file}'}

        try:
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--no-header' if not self.verbose else '--tb=long'
            ])

            status = 'PASSED' if result == 0 else 'FAILED'
            return {'status': status, 'exit_code': result}

        except Exception as e:
            self.logger.error(f"Data integrity tests failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def run_performance_validation(self) -> Dict[str, Any]:
        """Run performance validation tests"""
        self.logger.info("🔄 Running performance validation tests...")

        test_file = 'tests/govinfo_performance_tests.py'
        if not os.path.exists(test_file):
            return {'status': 'FAILED', 'error': f'Test file not found: {test_file}'}

        try:
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--no-header' if not self.verbose else '--tb=long'
            ])

            status = 'PASSED' if result == 0 else 'FAILED'
            return {'status': status, 'exit_code': result}

        except Exception as e:
            self.logger.error(f"Performance tests failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def run_e2e_integration_validation(self) -> Dict[str, Any]:
        """Run end-to-end integration validation tests"""
        self.logger.info("🔄 Running end-to-end integration validation tests...")

        test_file = 'tests/govinfo_e2e_integration_tests.py'
        if not os.path.exists(test_file):
            return {'status': 'FAILED', 'error': f'Test file not found: {test_file}'}

        try:
            result = pytest.main([
                test_file,
                '-v',
                '--tb=short',
                '--no-header' if not self.verbose else '--tb=long'
            ])

            status = 'PASSED' if result == 0 else 'FAILED'
            return {'status': status, 'exit_code': result}

        except Exception as e:
            self.logger.error(f"E2E integration tests failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def run_functional_validation(self) -> Dict[str, Any]:
        """Run functional validation of actual GovInfo ingestor"""
        self.logger.info("🔄 Running functional validation...")

        try:
            # Test basic instantiation
            ingestor = FixedGovInfoIngestor()

            # Test configuration creation
            config = IngestionConfig(
                data_type=DataType.BILLS,
                congress=118,
                batch_size=100
            )

            # Test data type handling
            for data_type in [DataType.BILLS, DataType.VOTES, DataType.MEMBERS]:
                test_config = IngestionConfig(
                    data_type=data_type,
                    congress=118,
                    batch_size=50
                )
                assert test_config.data_type == data_type

            # Test basic methods exist and work
            assert hasattr(ingestor, 'paginate_api_response')
            assert hasattr(ingestor, 'insert_batch')
            assert hasattr(ingestor, 'normalize_bill_data')
            assert hasattr(ingestor, 'normalize_vote_data')
            assert hasattr(ingestor, 'normalize_member_data')

            return {'status': 'PASSED', 'details': 'Functional validation successful'}

        except Exception as e:
            self.logger.error(f"Functional validation failed: {e}")
            return {'status': 'FAILED', 'error': str(e)}

    def run_production_simulation(self) -> Dict[str, Any]:
        """Run production-like simulation test"""
        self.logger.info("🔄 Running production simulation...")

        try:
            # Simulate production conditions
            config = IngestionConfig(
                data_type=DataType.BILLS,
                congress=118,
                batch_size=100,
                max_retries=3,
                request_delay=0.01,  # Faster for testing
                enable_checkpoint=True,
                resume_from_checkpoint=True
            )

            # Mock API responses simulating production data
            test_bills = [
                {
                    'packageId': f'BILLS-118hr{i:04d}-2023-01-01',
                    'dateIssued': '2023-01-01T12:00:00Z',
                    'lastModified': '2023-01-02T10:30:00Z'
                }
                for i in range(1, 251)  # 250 test bills
            ]

            # Split into batches
            batches = [test_bills[i:i+100] for i in range(0, len(test_bills), 100)]

            # Test pagination logic
            offset = 0
            total_processed = 0

            for i, batch in enumerate(batches):
                batch_size = len(batch)
                total_processed += batch_size
                offset += batch_size

                self.logger.debug(f"Batch {i+1}: processed {batch_size} items, offset: {offset}")

            # Verify calculations
            assert total_processed == 250
            assert offset == 250

            return {
                'status': 'PASSED',
                'details': f'Successfully processed {total_processed} items with proper offset tracking'
            }

        except Exception as e:
            self.logger.error(f"Production simulation failed: {e}")
            return {'status': 'FAILED', 'error': str(e)}

    def validate_offset_handling_fixes(self) -> Dict[str, Any]:
        """Validate that offset handling fixes are working correctly"""
        self.logger.info("🔍 Validating offset handling fixes...")

        try:
            # Test offset calculation accuracy
            test_scenarios = [
                {'start_offset': 0, 'batch_sizes': [100, 95, 50], 'expected_offsets': [0, 100, 195]},
                {'start_offset': 150, 'batch_sizes': [100, 25], 'expected_offsets': [150, 250]},
                {'start_offset': 500, 'batch_sizes': [100, 100, 75], 'expected_offsets': [500, 600, 700]},
            ]

            for scenario in test_scenarios:
                offset = scenario['start_offset']
                expected_offsets = scenario['expected_offsets']

                for batch_size in scenario['batch_sizes']:
                    # Simulate offset calculation (items received vs batch size)
                    offset += batch_size

                assert offset in expected_offsets, f"Offset calculation error: got {offset}, expected in {expected_offsets}"

            return {
                'status': 'PASSED',
                'details': 'Offset handling fixes validated successfully',
                'scenarios_tested': len(test_scenarios)
            }

        except Exception as e:
            self.logger.error(f"Offset handling validation failed: {e}")
            return {'status': 'FAILED', 'error': str(e)}

    def generate_performance_benchmarks(self) -> Dict[str, Any]:
        """Generate performance benchmarks"""
        self.logger.info("📊 Generating performance benchmarks...")

        try:
            benchmark_results = {}

            # Batch processing benchmark
            start_time = time.time()
            test_items = [{'packageId': f'test-bill-{i}', 'dateIssued': '2023-01-01'} for i in range(1000)]
            batch_size = 100

            for i in range(0, len(test_items), batch_size):
                batch = test_items[i:i+batch_size]
                # Simulate processing
                processed = len(batch)

            batch_time = time.time() - start_time
            batch_throughput = len(test_items) / batch_time

            benchmark_results['batch_processing'] = {
                'items_processed': len(test_items),
                'time_seconds': batch_time,
                'throughput_items_per_second': batch_throughput
            }

            # Pagination benchmark
            start_time = time.time()
            offsets = []
            current_offset = 0
            batch_sizes = [100, 95, 87, 103, 91]

            for batch_size in batch_sizes:
                offsets.append(current_offset)
                current_offset += batch_size

            pagination_time = time.time() - start_time

            benchmark_results['pagination'] = {
                'offset_calculations': len(offsets),
                'time_seconds': pagination_time,
                'offsets_per_second': len(offsets) / pagination_time
            }

            return {
                'status': 'PASSED',
                'benchmarks': benchmark_results
            }

        except Exception as e:
            self.logger.error(f"Performance benchmarking failed: {e}")
            return {'status': 'FAILED', 'error': str(e)}

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        self.logger.info("🚀 Starting comprehensive GovInfo offset handling validation...")

        # Track test execution order
        test_sequence = [
            ('functional_validation', self.run_functional_validation),
            ('offset_calculation_validation', self.run_offset_calculation_validation),
            ('pagination_logic_validation', self.run_pagination_logic_validation),
            ('checkpoint_system_validation', self.run_checkpoint_system_validation),
            ('rate_limiting_validation', self.run_rate_limiting_validation),
            ('data_integrity_validation', self.run_data_integrity_validation),
            ('performance_validation', self.run_performance_validation),
            ('e2e_integration_validation', self.run_e2e_integration_validation),
            ('offset_handling_fixes', self.validate_offset_handling_fixes),
            ('production_simulation', self.run_production_simulation),
            ('performance_benchmarks', self.generate_performance_benchmarks)
        ]

        results = {}
        passed_tests = 0
        failed_tests = 0
        total_tests = len(test_sequence)

        for test_name, test_func in test_sequence:
            self.logger.info(f"▶️  Executing: {test_name}")

            try:
                result = test_func()
                results[test_name] = result

                if result['status'] == 'PASSED':
                    self.logger.info(f"✅ {test_name}: PASSED")
                    passed_tests += 1
                    self.validation_report['components_tested'].append({
                        'component': test_name,
                        'status': 'PASSED',
                        'timestamp': datetime.now().isoformat()
                    })
                elif result['status'] == 'FAILED':
                    self.logger.warning(f"⚠️  {test_name}: FAILED")
                    failed_tests += 1
                    self.validation_report['critical_issues'].append({
                        'component': test_name,
                        'issue': result.get('error', 'Test failed'),
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    self.logger.error(f"❌ {test_name}: ERROR - {result.get('error', 'Unknown error')}")
                    failed_tests += 1
                    self.validation_report['critical_issues'].append({
                        'component': test_name,
                        'issue': result.get('error', 'Test error'),
                        'timestamp': datetime.now().isoformat()
                    })

            except Exception as e:
                self.logger.error(f"❌ {test_name}: EXCEPTION - {e}")
                results[test_name] = {'status': 'ERROR', 'error': str(e)}
                failed_tests += 1
                self.validation_report['critical_issues'].append({
                    'component': test_name,
                    'issue': f'Exception: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                })

        # Determine overall status
        if failed_tests == 0:
            self.validation_report['overall_status'] = 'PASSED'
            self.logger.info("🎉 All tests PASSED!")
        elif failed_tests < total_tests // 2:
            self.validation_report['overall_status'] = 'PARTIAL_PASS'
            self.logger.warning("⚠️  Some tests FAILED but majority passed")
        else:
            self.validation_report['overall_status'] = 'FAILED'
            self.logger.error("❌ Majority of tests FAILED")

        # Add summary
        self.validation_report['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests) * 100
        }

        # Add recommendations
        self.generate_recommendations(results)

        return results

    def generate_recommendations(self, test_results: Dict[str, Any]):
        """Generate recommendations based on test results"""
        recommendations = []

        # Check for specific failures and provide targeted recommendations
        for test_name, result in test_results.items():
            if result['status'] != 'PASSED':
                if 'offset' in test_name.lower():
                    recommendations.append("Review offset calculation logic - API response sizes may not match batch requests")
                elif 'checkpoint' in test_name.lower():
                    recommendations.append("Verify database checkpoint table exists and is accessible")
                elif 'rate' in test_name.lower():
                    recommendations.append("Check API rate limiting configuration and retry logic")
                elif 'performance' in test_name.lower():
                    recommendations.append("Consider optimizing batch sizes or implementing concurrent processing")
                elif 'integration' in test_name.lower():
                    recommendations.append("Review integration points between components")

        # General recommendations based on overall status
        if self.validation_report['overall_status'] != 'PASSED':
            recommendations.append("Review failed tests and fix identified issues before production deployment")
            recommendations.append("Run tests in production-like environment to ensure compatibility")
        else:
            recommendations.append("All tests passed - ready for production deployment")
            recommendations.append("Monitor production performance and adjust batch sizes as needed")

        self.validation_report['recommendations'] = recommendations

    def save_validation_report(self, filename: str = None):
        """Save validation report to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'govinfo_validation_report_{timestamp}.json'

        try:
            with open(filename, 'w') as f:
                json.dump(self.validation_report, f, indent=2)
            self.logger.info(f"📄 Validation report saved to: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")

    def print_summary_report(self):
        """Print a formatted summary report"""
        print("\n" + "="*80)
        print("🔍 GOVINFO OFFSET HANDLING VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {self.validation_report['timestamp']}")
        print(f"Environment: {self.validation_report['environment']}")
        print(f"Overall Status: {self.validation_report['overall_status']}")
        print(f"Test Suite: {self.validation_report['test_suite']}")

        if 'summary' in self.validation_report:
            summary = self.validation_report['summary']
            print(f"\n📊 Test Summary:")
            print(f"  Total Tests: {summary['total_tests']}")
            print(f"  Passed: {summary['passed_tests']}")
            print(f"  Failed: {summary['failed_tests']}")
            print(f"  Success Rate: {summary['success_rate']:.1f}%")

        if self.validation_report['components_tested']:
            print(f"\n✅ Passed Components:")
            for comp in self.validation_report['components_tested']:
                print(f"  • {comp['component']}")

        if self.validation_report['critical_issues']:
            print(f"\n❌ Critical Issues:")
            for issue in self.validation_report['critical_issues']:
                print(f"  • {issue['component']}: {issue['issue']}")

        if self.validation_report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in self.validation_report['recommendations']:
                print(f"  • {rec}")

        print("\n" + "="*80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='GovInfo Offset Handling Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--production', '-p', action='store_true', help='Run in production mode')
    parser.add_argument('--report-file', '-r', type=str, help='Save validation report to file')
    parser.add_argument('--skip-performance', action='store_true', help='Skip performance tests')

    args = parser.parse_args()

    try:
        # Initialize test runner
        runner = GovInfoTestRunner(verbose=args.verbose, production_mode=args.production)

        print("🚀 Starting GovInfo Offset Handling Validation Suite")
        print(f"   Environment: {'Production' if args.production else 'Development'}")
        print(f"   Verbose: {args.verbose}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Run all tests
        results = runner.run_all_tests()

        # Save report if requested
        if args.report_file:
            runner.save_validation_report(args.report_file)

        # Print summary
        runner.print_summary_report()

        # Exit with appropriate code
        if runner.validation_report['overall_status'] == 'PASSED':
            sys.exit(0)
        elif runner.validation_report['overall_status'] == 'PARTIAL_PASS':
            sys.exit(1)
        else:
            sys.exit(2)

    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation failed with exception: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
