#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced OpenStates System
Unit tests, integration tests, and performance tests
"""

import logging
import os
import sys
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_openstates_ingestion import (
    EnhancedOpenStatesIngestor,
    OpenStatesDataValidator,
    OpenStatesPaginationManager,
    OpenStatesProgressMonitor,
    OpenStatesRateLimitManager,
)
from openstates_orchestrator import OpenStatesOrchestrator, OrchestrationResult

# ============================================================================
# CONFIGURATION
# ============================================================================

# Configure test logging
logging.basicConfig(level=logging.WARNING)


# ============================================================================
# MOCK DATA
# ============================================================================

SAMPLE_PERSON_DATA = {
    "id": "ocd-person/12345678-1234-1234-1234-123456789abc",
    "name": "John Doe",
    "familyName": "Doe",
    "givenName": "John",
    "image": "https://example.com/image.jpg",
    "gender": "Male",
    "biography": "Test biography",
    "birthDate": "1970-01-01",
    "primaryParty": "Democratic",
    "jurisdiction": {
        "id": "ocd-jurisdiction/country:us/state:ca/government",
        "name": "California"
    },
    "currentRole": {
        "title": "Assembly Member",
        "orgClassification": "lower"
    }
}

SAMPLE_BILL_DATA = {
    "id": "ocd-bill/12345678-1234-1234-1234-123456789abc",
    "identifier": "AB 1234",
    "title": "Test Bill",
    "classification": "bill",
    "subject": "Education",
    "abstract": "Test abstract",
    "jurisdiction": {
        "id": "ocd-jurisdiction/country:us/state:ca/government",
        "name": "California"
    },
    "legislativeSession": {
        "id": "ocd-legal-session/2023",
        "name": "2023 Regular Session"
    },
    "sponsor": {
        "id": "ocd-person/12345678-1234-1234-1234-123456789abc",
        "name": "John Doe"
    }
}

SAMPLE_COMMITTEE_DATA = {
    "id": "ocd-committee/12345678-1234-1234-1234-123456789abc",
    "name": "Education Committee",
    "classification": "committee",
    "jurisdiction": {
        "id": "ocd-jurisdiction/country:us/state:ca/government",
        "name": "California"
    },
    "members": [
        {
            "id": "ocd-person/12345678-1234-1234-1234-123456789abc",
            "name": "John Doe",
            "role": "Chair"
        }
    ]
}

SAMPLE_EVENT_DATA = {
    "id": "ocd-event/12345678-1234-1234-1234-123456789abc",
    "name": "Committee Hearing",
    "classification": "event",
    "description": "Test event description",
    "jurisdiction": {
        "id": "ocd-jurisdiction/country:us/state:ca/government",
        "name": "California"
    },
    "start_date": "2023-01-01T10:00:00Z",
    "status": "confirmed"
}

SAMPLE_JURISDICTION_DATA = {
    "id": "ocd-jurisdiction/country:us/state:ca/government",
    "name": "California",
    "classification": "state",
    "url": "https://example.com/ca",
    "featureFlags": {
        "hasBills": True,
        "hasCommittees": True
    },
    "divisions": [
        {
            "id": "ocd-division/country:us/state:ca",
            "name": "California",
            "country": "us"
        }
    ],
    "links": [
        {
            "url": "https://example.com/ca/legislature",
            "note": "Official website"
        }
    ]
}


# ============================================================================
# UNIT TESTS
# ============================================================================

class TestRateLimitManager(unittest.TestCase):
    """Test cases for OpenStatesRateLimitManager"""

    def setUp(self):
        self.rate_manager = OpenStatesRateLimitManager(base_delay=0.01, max_delay=0.1)

    def test_initialization(self):
        """Test rate manager initialization"""
        self.assertEqual(self.rate_manager.base_delay, 0.01)
        self.assertEqual(self.rate_manager.max_delay, 0.1)
        self.assertEqual(self.rate_manager.hourly_limit, 1000)
        self.assertEqual(len(self.rate_manager.request_times), 0)
        self.assertEqual(self.rate_manager.adaptive_factor, 1.0)

    def test_wait_if_needed_basic(self):
        """Test basic rate limiting"""
        start_time = time.time()
        self.rate_manager.wait_if_needed()
        elapsed = time.time() - start_time

        # Should wait at least base_delay
        self.assertGreaterEqual(elapsed, 0.01)
        self.assertEqual(len(self.rate_manager.request_times), 1)

    def test_rate_limit_error_handling(self):
        """Test rate limit error handling"""
        initial_factor = self.rate_manager.adaptive_factor

        self.rate_manager.handle_rate_limit_error()

        # Adaptive factor should increase
        self.assertGreater(self.rate_manager.adaptive_factor, initial_factor)

    def test_success_handling(self):
        """Test success handling"""
        self.rate_manager.adaptive_factor = 2.0

        self.rate_manager.handle_success()

        # Adaptive factor should decrease
        self.assertLess(self.rate_manager.adaptive_factor, 2.0)
        self.assertGreaterEqual(self.rate_manager.adaptive_factor, 1.0)

    def test_hourly_limit_protection(self):
        """Test hourly limit protection"""
        # Fill up request times to near limit
        now = datetime.now()
        self.rate_manager.request_times = [now - timedelta(minutes=i) for i in range(950)]

        start_time = time.time()
        self.rate_manager.wait_if_needed()
        elapsed = time.time() - start_time

        # Should wait significantly due to approaching limit
        self.assertGreater(elapsed, 1.0)  # Should wait at least 1 minute


class TestPaginationManager(unittest.TestCase):
    """Test cases for OpenStatesPaginationManager"""

    def setUp(self):
        self.pagination_manager = OpenStatesPaginationManager(page_size=25)

    def test_initialization(self):
        """Test pagination manager initialization"""
        self.assertEqual(self.pagination_manager.page_size, 25)
        self.assertEqual(self.pagination_manager.max_consecutive_empty_pages, 3)
        self.assertEqual(len(self.pagination_manager.offset_cache), 0)

    def test_get_next_page_params(self):
        """Test getting next page parameters"""
        params = self.pagination_manager.get_next_page_params('people', 'ca')

        self.assertEqual(params['page'], 1)
        self.assertEqual(params['per_page'], 25)
        self.assertFalse(params['resume'])
        self.assertEqual(params['total_processed'], 0)

    def test_should_continue_pagination(self):
        """Test pagination continuation logic"""
        # Test with results
        response_data = {
            'results': [{'id': '1'}],
            'pagination': {'page': 1, 'max_page': 10}
        }

        self.assertTrue(self.pagination_manager.should_continue_pagination(response_data, 0))

        # Test without results
        response_data = {'results': [], 'pagination': {'page': 1, 'max_page': 10}}
        self.assertFalse(self.pagination_manager.should_continue_pagination(response_data, 3))

        # Test at max page
        response_data = {
            'results': [{'id': '1'}],
            'pagination': {'page': 10, 'max_page': 10}
        }
        self.assertFalse(self.pagination_manager.should_continue_pagination(response_data, 0))


class TestDataValidator(unittest.TestCase):
    """Test cases for OpenStatesDataValidator"""

    def setUp(self):
        self.validator = OpenStatesDataValidator()

    def test_validate_person_data_success(self):
        """Test successful person data validation"""
        result = self.validator.validate_person_data(SAMPLE_PERSON_DATA)

        self.assertIsNotNone(result)
        self.assertEqual(result.person_id, SAMPLE_PERSON_DATA['id'])
        self.assertEqual(result.name, SAMPLE_PERSON_DATA['name'])
        self.assertEqual(result.jurisdiction_id, SAMPLE_PERSON_DATA['jurisdiction']['id'])

    def test_validate_person_data_failure(self):
        """Test person data validation failure"""
        invalid_data = SAMPLE_PERSON_DATA.copy()
        invalid_data['id'] = None  # Missing required field

        result = self.validator.validate_person_data(invalid_data)

        self.assertIsNone(result)

    def test_validate_bill_data_success(self):
        """Test successful bill data validation"""
        result = self.validator.validate_bill_data(SAMPLE_BILL_DATA)

        self.assertIsNotNone(result)
        self.assertEqual(result.bill_id, SAMPLE_BILL_DATA['id'])
        self.assertEqual(result.identifier, SAMPLE_BILL_DATA['identifier'])
        self.assertEqual(result.title, SAMPLE_BILL_DATA['title'])

    def test_validate_bill_data_failure(self):
        """Test bill data validation failure"""
        invalid_data = SAMPLE_BILL_DATA.copy()
        invalid_data['id'] = None  # Missing required field

        result = self.validator.validate_bill_data(invalid_data)

        self.assertIsNone(result)

    def test_date_parsing(self):
        """Test date parsing functionality"""
        # Test valid date
        result = self.validator._parse_date("2023-01-01")
        self.assertEqual(result, "2023-01-01")

        # Test invalid date
        result = self.validator._parse_date("invalid-date")
        self.assertIsNone(result)

        # Test None
        result = self.validator._parse_date(None)
        self.assertIsNone(result)

    def test_datetime_parsing(self):
        """Test datetime parsing functionality"""
        # Test valid datetime
        result = self.validator._parse_datetime("2023-01-01T10:00:00Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)

        # Test invalid datetime
        result = self.validator._parse_datetime("invalid-datetime")
        self.assertIsNone(result)

        # Test None
        result = self.validator._parse_datetime(None)
        self.assertIsNone(result)


class TestProgressMonitor(unittest.TestCase):
    """Test cases for OpenStatesProgressMonitor"""

    def setUp(self):
        self.progress_monitor = OpenStatesProgressMonitor()

    def test_initialization(self):
        """Test progress monitor initialization"""
        self.assertIsNotNone(self.progress_monitor.start_time)
        self.assertEqual(len(self.progress_monitor.progress_history), 0)

    def test_update_progress(self):
        """Test progress update"""
        self.progress_monitor.update_progress('people', 'ca', 100, 1000)

        self.assertEqual(len(self.progress_monitor.progress_history), 1)

        progress = self.progress_monitor.progress_history[0]
        self.assertEqual(progress['data_type'], 'people')
        self.assertEqual(progress['category'], 'ca')
        self.assertEqual(progress['processed'], 100)
        self.assertEqual(progress['total'], 1000)
        self.assertEqual(progress['percentage'], 10.0)
        self.assertGreater(progress['rate'], 0)
        self.assertIsNotNone(progress['eta'])

    def test_get_summary(self):
        """Test progress summary"""
        # Add some progress
        self.progress_monitor.update_progress('people', 'ca', 100, 1000)
        self.progress_monitor.update_progress('bills', 'ca', 50, 500)

        summary = self.progress_monitor.get_summary()

        self.assertIsNotNone(summary)
        self.assertEqual(summary['total_data_types'], 2)
        self.assertGreater(summary['average_rate'], 0)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEnhancedIngestorIntegration(unittest.TestCase):
    """Integration tests for Enhanced OpenStates Ingestor"""

    def setUp(self):
        # Mock database connection
        self.mock_db_conn = Mock()
        self.mock_cursor = Mock()
        self.mock_db_conn.cursor.return_value = self.mock_cursor

        # Mock environment variables
        with patch.dict(os.environ, {'OPENSTATES_API_KEY': 'test-key'}):
            self.ingestor = EnhancedOpenStatesIngestor()
            self.ingestor.db_conn = self.mock_db_conn

    @patch('requests.get')
    def test_fetch_people_batch_success(self, mock_get):
        """Test successful people batch fetch"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [SAMPLE_PERSON_DATA],
            'pagination': {'page': 1, 'max_page': 10}
        }
        mock_get.return_value = mock_response

        result = self.ingestor.fetch_people_batch('ca', 1)

        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], SAMPLE_PERSON_DATA['id'])
        self.assertEqual(result['pagination']['page'], 1)

    @patch('requests.get')
    def test_fetch_people_batch_rate_limit(self, mock_get):
        """Test rate limit handling in people batch fetch"""
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        # Mock rate manager
        self.ingestor.rate_manager.handle_rate_limit_error = Mock()

        result = self.ingestor.fetch_people_batch('ca', 1)

        # Should handle rate limit and return empty results
        self.assertEqual(result['results'], [])
        self.ingestor.rate_manager.handle_rate_limit_error.assert_called()

    def test_is_record_processed(self):
        """Test record processing check"""
        # Mock database query
        self.mock_cursor.fetchone.return_value = [False]

        result = self.ingestor.is_record_processed('test-id', SAMPLE_PERSON_DATA)

        self.assertFalse(result)
        self.mock_cursor.execute.assert_called()

    def test_insert_people_batch(self):
        """Test people batch insertion"""
        people_data = [SAMPLE_PERSON_DATA]

        result = self.ingestor.insert_people_batch(people_data)

        self.assertEqual(result, 1)
        self.mock_cursor.execute.assert_called()
        self.mock_db_conn.commit.assert_called()


class TestOrchestratorIntegration(unittest.TestCase):
    """Integration tests for OpenStates Orchestrator"""

    def setUp(self):
        # Mock environment variables
        with patch.dict(os.environ, {'OPENSTATES_API_KEY': 'test-key'}):
            self.orchestrator = OpenStatesOrchestrator()

    def test_initialization(self):
        """Test orchestrator initialization"""
        self.assertIsNotNone(self.orchestrator.rate_manager)
        self.assertIsNotNone(self.orchestrator.pagination_manager)
        self.assertIsNotNone(self.orchestrator.progress_monitor)
        self.assertIsNotNone(self.orchestrator.ingestion_plans)
        self.assertGreater(len(self.orchestrator.ingestion_plans), 0)

    def test_plan_definitions(self):
        """Test ingestion plan definitions"""
        plans = self.orchestrator.ingestion_plans

        # Check that required plans exist
        self.assertIn('jurisdictions', plans)
        self.assertIn('northeast_states', plans)
        self.assertIn('california', plans)

        # Check plan structure
        jurisdictions_plan = plans['jurisdictions']
        self.assertEqual(jurisdictions_plan.name, 'Load All Jurisdictions')
        self.assertEqual(jurisdictions_plan.data_types, ['jurisdictions'])
        self.assertEqual(jurisdictions_plan.dependencies, [])
        self.assertFalse(jurisdictions_plan.parallel_safe)
        self.assertEqual(jurisdictions_plan.priority, 1)

        # Check dependency relationships
        california_plan = plans['california']
        self.assertIn('jurisdictions', california_plan.dependencies)

    def test_dependency_checking(self):
        """Test dependency checking logic"""
        jurisdictions_plan = self.orchestrator.ingestion_plans['jurisdictions']
        california_plan = self.orchestrator.ingestion_plans['california']

        # Jurisdictions plan has no dependencies
        self.assertTrue(self.orchestrator._check_dependencies(jurisdictions_plan))

        # California plan depends on jurisdictions (not executed yet)
        self.assertFalse(self.orchestrator._check_dependencies(california_plan))

        # Add jurisdictions to executed plans
        mock_result = Mock()
        mock_result.plan_name = 'jurisdictions'
        self.orchestrator.orchestration_stats['plans_executed'].append(mock_result)

        # Now California plan should pass dependency check
        self.assertTrue(self.orchestrator._check_dependencies(california_plan))

    def test_get_available_plans(self):
        """Test getting available plans"""
        plans = self.orchestrator.get_available_plans()

        self.assertIsInstance(plans, dict)
        self.assertGreater(len(plans), 0)

        # Check that it's a copy (modifications shouldn't affect original)
        plans['test'] = 'test'
        self.assertNotIn('test', self.orchestrator.ingestion_plans)

    def test_plan_status(self):
        """Test plan status checking"""
        status = self.orchestrator.get_plan_status('jurisdictions')

        self.assertEqual(status['plan_name'], 'jurisdictions')
        self.assertIn('plan', status)
        self.assertIn('dependencies_satisfied', status)
        self.assertIn('executed_count', status)
        self.assertIn('failed_count', status)
        self.assertIn('status', status)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance(unittest.TestCase):
    """Performance tests for OpenStates system"""

    def test_rate_limiting_performance(self):
        """Test rate limiting performance"""
        rate_manager = OpenStatesRateLimitManager(base_delay=0.001)

        start_time = time.time()

        # Make 10 requests
        for i in range(10):
            rate_manager.wait_if_needed()

        elapsed = time.time() - start_time

        # Should take at least 10 * base_delay seconds
        expected_min_time = 10 * 0.001
        self.assertGreaterEqual(elapsed, expected_min_time)

    def test_data_validation_performance(self):
        """Test data validation performance"""
        validator = OpenStatesDataValidator()

        start_time = time.time()

        # Validate 1000 records
        for i in range(1000):
            person_data = SAMPLE_PERSON_DATA.copy()
            person_data['id'] = f"test-id-{i}"
            validator.validate_person_data(person_data)

        elapsed = time.time() - start_time

        # Should complete within reasonable time (less than 1 second)
        self.assertLess(elapsed, 1.0)

    def test_progress_monitoring_performance(self):
        """Test progress monitoring performance"""
        monitor = OpenStatesProgressMonitor()

        start_time = time.time()

        # Update progress 1000 times
        for i in range(1000):
            monitor.update_progress('people', 'ca', i, 1000)

        elapsed = time.time() - start_time

        # Should complete within reasonable time (less than 0.1 seconds)
        self.assertLess(elapsed, 0.1)
        self.assertEqual(len(monitor.progress_history), 1000)


# ============================================================================
# END-TO-END TESTS
# ============================================================================

class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for OpenStates system"""

    def setUp(self):
        # Mock all external dependencies
        self.mock_db_conn = Mock()
        self.mock_cursor = Mock()
        self.mock_db_conn.cursor.return_value = self.mock_cursor

        with patch.dict(os.environ, {'OPENSTATES_API_KEY': 'test-key'}):
            self.orchestrator = OpenStatesOrchestrator()
            self.orchestrator.db_conn = self.mock_db_conn

    @patch('requests.get')
    def test_end_to_end_jurisdictions_ingestion(self, mock_get):
        """Test end-to-end jurisdictions ingestion"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [SAMPLE_JURISDICTION_DATA],
            'pagination': {'page': 1, 'max_page': 1}
        }
        mock_get.return_value = mock_response

        # Mock database operations
        self.mock_cursor.fetchone.return_value = [False]  # Not processed

        result = self.orchestrator.execute_plan('jurisdictions')

        self.assertTrue(result.success)
        self.assertEqual(result.records_processed, 1)
        self.assertEqual(result.plan_name, 'jurisdictions')

    def test_end_to_end_plan_dependencies(self):
        """Test end-to-end plan dependency resolution"""
        # Mock jurisdictions plan execution
        with patch.object(self.orchestrator, 'execute_plan') as mock_execute:
            mock_execute.return_value = OrchestrationResult(
                plan_name='jurisdictions',
                success=True,
                records_processed=1
            )

            # Execute california plan (depends on jurisdictions)
            result = self.orchestrator.execute_plan('california')

            # Should have executed jurisdictions first
            self.assertEqual(mock_execute.call_count, 2)
            self.assertEqual(mock_execute.call_args_list[0][0][0], 'jurisdictions')
            self.assertEqual(mock_execute.call_args_list[1][0][0], 'california')


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running Unit Tests...")

    test_classes = [
        TestRateLimitManager,
        TestPaginationManager,
        TestDataValidator,
        TestProgressMonitor
    ]

    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running Integration Tests...")

    test_classes = [
        TestEnhancedIngestorIntegration,
        TestOrchestratorIntegration
    ]

    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_performance_tests():
    """Run performance tests"""
    print("⚡ Running Performance Tests...")

    test_classes = [
        TestPerformance
    ]

    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_end_to_end_tests():
    """Run end-to-end tests"""
    print("🎯 Running End-to-End Tests...")

    test_classes = [
        TestEndToEnd
    ]

    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_all_tests():
    """Run all test suites"""
    print("🚀 Enhanced OpenStates Test Suite")
    print("=" * 50)

    results = {}

    # Run test suites
    results['unit'] = run_unit_tests()
    results['integration'] = run_integration_tests()
    results['performance'] = run_performance_tests()
    results['end_to_end'] = run_end_to_end_tests()

    # Generate summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)

    for test_type, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_type.title():<15}: {status}")

    overall_success = all(results.values())
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")

    return overall_success


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced OpenStates Test Suite')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.performance:
        success = run_performance_tests()
    elif args.e2e:
        success = run_end_to_end_tests()
    else:
        success = run_all_tests()

    sys.exit(0 if success else 1)
