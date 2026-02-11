"""
Integration tests for Congress members ingestion process
"""

import os
import subprocess
import time
import unittest

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

load_dotenv()

class TestIngestionIntegration(unittest.TestCase):
    """Integration tests for the ingestion process"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.conn_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }
        cls.conn = psycopg2.connect(**cls.conn_params)
        cls.conn.cursor_factory = DictCursor
        cls.test_bioguide = 'T000001'  # Test bioguide ID

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.conn:
            cls.conn.close()

    def setUp(self):
        """Set up test cursor"""
        self.cursor = self.conn.cursor()

    def tearDown(self):
        """Clean up test cursor"""
        self.cursor.close()

    def query(self, sql, params=None):
        """Execute query and return results"""
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def query_one(self, sql, params=None):
        """Execute query and return single result"""
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone()

    def test_ingestion_script_exists(self):
        """Test that ingestion scripts exist and are executable"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'scripts', 'ingest_members_official.py')

        self.assertTrue(os.path.exists(script_path), "Ingestion script should exist")
        self.assertTrue(os.access(script_path, os.X_OK), "Ingestion script should be executable")

        print("✅ Ingestion script exists and is executable")

    def test_environment_variables(self):
        """Test that required environment variables are set"""
        required_vars = ['CONGRESS_API_KEY', 'DB_NAME', 'DB_USER']

        for var in required_vars:
            self.assertIsNotNone(os.getenv(var), f"Environment variable {var} should be set")

        print("✅ All required environment variables are set")

    def test_database_connection(self):
        """Test database connection"""
        try:
            result = self.query_one("SELECT 1 as test")
            self.assertEqual(result['test'], 1, "Database connection should work")
            print("✅ Database connection successful")
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_reference_data_exists(self):
        """Test that reference data is populated"""
        # Check sessions
        sessions = self.query_one("SELECT COUNT(*) as count FROM congress.sessions")
        self.assertGreater(sessions['count'], 0, "Sessions table should be populated")

        # Check chambers
        chambers = self.query_one("SELECT COUNT(*) as count FROM congress.chambers")
        self.assertGreater(chambers['count'], 0, "Chambers table should be populated")

        # Check parties
        parties = self.query_one("SELECT COUNT(*) as count FROM congress.parties")
        self.assertGreater(parties['count'], 0, "Parties table should be populated")

        # Check states
        states = self.query_one("SELECT COUNT(*) as count FROM congress.states")
        self.assertGreater(states['count'], 0, "States table should be populated")

        print("✅ All reference data is populated")

    def test_api_connectivity(self):
        """Test Congress.gov API connectivity"""
        try:
            import requests

            api_key = os.getenv('CONGRESS_API_KEY')
            if not api_key:
                self.skipTest("CONGRESS_API_KEY not set")

            # Test API with a simple request
            url = "https://api.congress.gov/v3/member/congress/118"
            headers = {'X-API-Key': api_key, 'Accept': 'application/json'}
            params = {'limit': 1}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            self.assertEqual(response.status_code, 200, "API should respond successfully")

            data = response.json()
            self.assertIn('members', data, "API response should contain members")

            print("✅ Congress.gov API connectivity successful")

        except ImportError:
            self.skipTest("requests library not available")
        except Exception as e:
            self.fail(f"API connectivity test failed: {e}")

    def test_dry_run_ingestion(self):
        """Test ingestion script in dry-run mode"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'scripts', 'ingest_members_official.py')

        try:
            # Run ingestion script with --dry-run flag
            result = subprocess.run([
                'python', script_path, 
                '--congress-start', '118',
                '--congress-end', '118',
                '--dry-run'
            ], capture_output=True, text=True, timeout=30)

            self.assertEqual(result.returncode, 0, f"Dry-run should succeed: {result.stderr}")
            self.assertIn("DRY RUN", result.stdout, "Should indicate dry run mode")

            print("✅ Dry-run ingestion successful")

        except subprocess.TimeoutExpired:
            self.fail("Dry-run ingestion timed out")
        except Exception as e:
            self.fail(f"Dry-run ingestion failed: {e}")

    def test_verification_utility(self):
        """Test verification utility functionality"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'scripts', 'verify_congress_data.py')

        try:
            # Run verification utility
            result = subprocess.run([
                'python', script_path
            ], capture_output=True, text=True, timeout=30)

            self.assertEqual(result.returncode, 0, f"Verification utility should succeed: {result.stderr}")
            self.assertIn("Member Counts by Congress", result.stdout, "Should show member counts")

            print("✅ Verification utility successful")

        except subprocess.TimeoutExpired:
            self.fail("Verification utility timed out")
        except Exception as e:
            self.fail(f"Verification utility failed: {e}")

    def test_small_scale_ingestion(self):
        """Test small-scale ingestion (single congress)"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'scripts', 'ingest_members_official.py')

        # Get current counts
        before_members = self.query_one("SELECT COUNT(*) as count FROM congress.members")['count']
        before_terms = self.query_one("SELECT COUNT(*) as count FROM congress.member_terms")['count']

        try:
            # Run ingestion for a single congress
            result = subprocess.run([
                'python', script_path, 
                '--congress-start', '117',
                '--congress-end', '117',
                '--batch-size', '10'
            ], capture_output=True, text=True, timeout=120)

            self.assertEqual(result.returncode, 0, f"Small-scale ingestion should succeed: {result.stderr}")

            # Check that data was added
            after_members = self.query_one("SELECT COUNT(*) as count FROM congress.members")['count']
            after_terms = self.query_one("SELECT COUNT(*) as count FROM congress.member_terms")['count']

            # Should have added some data (or at least not lost data)
            self.assertGreaterEqual(after_members, before_members, "Should not lose member data")
            self.assertGreaterEqual(after_terms, before_terms, "Should not lose term data")

            print("✅ Small-scale ingestion successful")

        except subprocess.TimeoutExpired:
            self.fail("Small-scale ingestion timed out")
        except Exception as e:
            self.fail(f"Small-scale ingestion failed: {e}")

    def test_data_after_ingestion(self):
        """Test data integrity after ingestion"""
        # Test that we have data
        member_count = self.query_one("SELECT COUNT(*) as count FROM congress.members")['count']
        term_count = self.query_one("SELECT COUNT(*) as count FROM congress.member_terms")['count']

        self.assertGreater(member_count, 0, "Should have members after ingestion")
        self.assertGreater(term_count, 0, "Should have terms after ingestion")

        # Test data quality views
        try:
            views = [
                'congress.member_counts_by_congress',
                'congress.longest_serving_members',
                'congress.party_distribution_by_congress'
            ]

            for view in views:
                result = self.query(f"SELECT COUNT(*) as count FROM {view}")
                self.assertGreater(result[0]['count'], 0, f"View {view} should return data")

            print("✅ Data integrity checks passed")

        except Exception as e:
            self.fail(f"Data integrity check failed: {e}")


class TestIngestionPerformance(unittest.TestCase):
    """Performance tests for ingestion process"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.conn_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }
        cls.conn = psycopg2.connect(**cls.conn_params)
        cls.conn.cursor_factory = DictCursor

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.conn:
            cls.conn.close()

    def setUp(self):
        """Set up test cursor"""
        self.cursor = self.conn.cursor()

    def tearDown(self):
        """Clean up test cursor"""
        self.cursor.close()

    def query_one(self, sql, params=None):
        """Execute query and return single result"""
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone()

    def test_query_performance(self):
        """Test performance of key queries"""
        queries = [
            ("Member count", "SELECT COUNT(*) FROM congress.members"),
            ("Term count", "SELECT COUNT(*) FROM congress.member_terms"),
            ("Congress summary", "SELECT congress_number, COUNT(*) FROM congress.member_terms GROUP BY congress_number"),
            ("Longest serving", "SELECT * FROM congress.longest_serving_members LIMIT 10"),
            ("Party distribution", "SELECT * FROM congress.party_distribution_by_congress WHERE congress_number = 118")
        ]

        for name, query in queries:
            start_time = time.time()
            result = self.query_one(query)
            end_time = time.time()

            duration = end_time - start_time
            self.assertLess(duration, 2.0, f"Query '{name}' should complete in <2 seconds")

            print(f"✅ Query '{name}' completed in {duration:.2f}s")

    def test_view_performance(self):
        """Test performance of materialized views"""
        views = [
            'congress.member_counts_by_congress',
            'congress.longest_serving_members',
            'congress.party_distribution_by_congress'
        ]

        for view in views:
            start_time = time.time()
            result = self.query_one(f"SELECT COUNT(*) as count FROM {view}")
            end_time = time.time()

            duration = end_time - start_time
            self.assertLess(duration, 1.0, f"View '{view}' should complete in <1 second")

            print(f"✅ View '{view}' completed in {duration:.2f}s")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)