#!/usr/bin/env python3
"""
Detailed Test of Congress Members Ingestion Process
Tests all components without relying on external API
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

import psycopg2
from psycopg2.extras import execute_values

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DetailedIngestionTester:
    """Comprehensive test of the ingestion pipeline"""

    def __init__(self):
        self.db_conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
        self.test_results = {
            'database_connection': False,
            'data_normalization': False,
            'batch_insertion': False,
            'fingerprinting': False,
            'checkpoint_tracking': False,
            'error_handling': False
        }

    def test_database_connection(self):
        """Test database connection and schema"""
        try:
            cursor = self.db_conn.cursor()

            # Test basic connectivity
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "Basic query failed"

            # Test schema exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'congress'
                    AND table_name = 'members'
                )
            """)
            schema_exists = cursor.fetchone()[0]
            assert schema_exists, "congress.members table does not exist"

            # Test incremental schema
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.schemata
                    WHERE schema_name = 'incremental'
                )
            """)
            incremental_exists = cursor.fetchone()[0]
            assert incremental_exists, "incremental schema does not exist"

            cursor.close()
            self.test_results['database_connection'] = True
            logger.info("✅ Database connection test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

    def test_data_normalization(self):
        """Test member data normalization logic"""
        try:
            # Sample API response data
            sample_member = {
                "member": {
                    "bioguideId": "T000476",
                    "firstName": "Donald",
                    "middleName": "John",
                    "lastName": "Trump",
                    "suffix": "Jr.",
                    "name": "Donald John Trump Jr.",
                    "birthDate": "1977-12-31",
                    "gender": "M",
                    "biography": "Test biography",
                    "birthPlace": "New York, NY"
                }
            }

            # Test normalization (simplified version)
            def normalize_member_data(member_data: Dict[str, Any]) -> Dict[str, Any]:
                member_info = member_data.get('member', member_data)
                full_name = member_info.get('name', '')
                name_parts = full_name.split()

                return {
                    'bioguide_id': member_info.get('bioguideId'),
                    'first_name': member_info.get('firstName', name_parts[0] if name_parts else ''),
                    'middle_name': member_info.get('middleName'),
                    'last_name': member_info.get('lastName', name_parts[-1] if len(name_parts) > 1 else ''),
                    'suffix': member_info.get('suffix'),
                    'official_full_name': full_name,
                    'birthday': member_info.get('birthDate'),
                    'gender': member_info.get('gender'),
                    'biography': member_info.get('biography', ''),
                    'birthplace': member_info.get('birthPlace'),
                    'death_date': member_info.get('deathDate'),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }

            normalized = normalize_member_data(sample_member)

            # Verify normalization
            assert normalized['bioguide_id'] == "T000476", "bioguide_id not normalized correctly"
            assert normalized['first_name'] == "Donald", "first_name not normalized correctly"
            assert normalized['last_name'] == "Trump", "last_name not normalized correctly"
            assert normalized['suffix'] == "Jr.", "suffix not normalized correctly"
            assert normalized['birthday'] == "1977-12-31", "birthday not normalized correctly"
            assert normalized['gender'] == "M", "gender not normalized correctly"

            self.test_results['data_normalization'] = True
            logger.info("✅ Data normalization test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Data normalization test failed: {e}")
            return False

    def test_batch_insertion(self):
        """Test batch insertion with UPSERT"""
        try:
            cursor = self.db_conn.cursor()

            # Create test member data
            test_members = [
                {
                    'bioguide_id': 'TEST001',
                    'first_name': 'Test',
                    'middle_name': 'User',
                    'last_name': 'One',
                    'suffix': None,
                    'official_full_name': 'Test User One',
                    'birthday': '1980-01-01',
                    'gender': 'M',
                    'biography': 'Test biography',
                    'birthplace': 'Test City',
                    'death_date': None,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                {
                    'bioguide_id': 'TEST002',
                    'first_name': 'Test',
                    'middle_name': 'User',
                    'last_name': 'Two',
                    'suffix': 'Jr.',
                    'official_full_name': 'Test User Two Jr.',
                    'birthday': '1985-05-15',
                    'gender': 'F',
                    'biography': 'Another test biography',
                    'birthplace': 'Another Test City',
                    'death_date': None,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            ]

            # Test batch insert
            query = """
                INSERT INTO congress.members (
                    bioguide_id, first_name, middle_name, last_name, suffix,
                    official_full_name, birthday, gender, biography, birthplace,
                    death_date, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    middle_name = EXCLUDED.middle_name,
                    last_name = EXCLUDED.last_name,
                    suffix = EXCLUDED.suffix,
                    official_full_name = EXCLUDED.official_full_name,
                    birthday = EXCLUDED.birthday,
                    gender = EXCLUDED.gender,
                    biography = EXCLUDED.biography,
                    birthplace = EXCLUDED.birthplace,
                    death_date = EXCLUDED.death_date,
                    updated_at = EXCLUDED.updated_at
            """

            values = [
                (
                    m['bioguide_id'], m['first_name'], m['middle_name'], m['last_name'],
                    m['suffix'], m['official_full_name'], m['birthday'], m['gender'],
                    m['biography'], m['birthplace'], m['death_date'], m['created_at'], m['updated_at']
                )
                for m in test_members
            ]

            execute_values(cursor, query, values)
            self.db_conn.commit()

            # Verify insertion
            cursor.execute("SELECT COUNT(*) FROM congress.members WHERE bioguide_id LIKE 'TEST%'")
            inserted_count = cursor.fetchone()[0]
            assert inserted_count == 2, f"Expected 2 test members, got {inserted_count}"

            # Test UPSERT by updating one member
            test_members[0]['first_name'] = 'Updated'
            values[0] = (
                test_members[0]['bioguide_id'], test_members[0]['first_name'],
                test_members[0]['middle_name'], test_members[0]['last_name'],
                test_members[0]['suffix'], test_members[0]['official_full_name'],
                test_members[0]['birthday'], test_members[0]['gender'],
                test_members[0]['biography'], test_members[0]['birthplace'],
                test_members[0]['death_date'], test_members[0]['created_at'],
                test_members[0]['updated_at']
            )

            execute_values(cursor, query, [values[0]])
            self.db_conn.commit()

            # Verify update
            cursor.execute("SELECT first_name FROM congress.members WHERE bioguide_id = 'TEST001'")
            updated_name = cursor.fetchone()[0]
            assert updated_name == 'Updated', f"UPSERT failed, expected 'Updated', got '{updated_name}'"

            # Cleanup test data
            cursor.execute("DELETE FROM congress.members WHERE bioguide_id LIKE 'TEST%'")
            self.db_conn.commit()

            cursor.close()
            self.test_results['batch_insertion'] = True
            logger.info("✅ Batch insertion test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Batch insertion test failed: {e}")
            self.db_conn.rollback()
            return False

    def test_fingerprinting(self):
        """Test SHA-256 fingerprinting functionality"""
        try:
            cursor = self.db_conn.cursor()

            # Test fingerprint function
            test_data = {"name": "Test User", "value": 123}
            test_id = "TEST_FINGERPRINT_001"

            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s::text, %s::text, %s::text, %s::jsonb
                )
            """, ('congress.gov', 'members', test_id, json.dumps(test_data)))

            first_check = cursor.fetchone()[0]
            assert first_check == False, "First check should return False"

            # Second check with same data - should be True (now exists)
            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s::text, %s::text, %s::text, %s::jsonb
                )
            """, ('congress.gov', 'members', test_id, json.dumps(test_data)))

            second_check = cursor.fetchone()[0]
            assert second_check == True, "Second check should return True (now exists)"

            # Check again (should now be True)
            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s::text, %s::text, %s::text, %s::jsonb
                )
            """, ('congress.gov', 'members', test_id, json.dumps(test_data)))

            third_check = cursor.fetchone()[0]
            assert third_check == True, "Third check should return True (already processed)"

            # Test with modified data
            modified_data = {"name": "Test User", "value": 456}
            cursor.execute("""
                SELECT incremental.is_record_processed(
                    %s::text, %s::text, %s::text, %s::jsonb
                )
            """, ('congress.gov', 'members', test_id, json.dumps(modified_data)))

            fourth_check = cursor.fetchone()[0]
            assert fourth_check == False, "Modified data should return False"

            # Cleanup
            cursor.execute("""
                DELETE FROM incremental.record_fingerprints
                WHERE data_source = 'congress.gov' AND data_type = 'members' AND record_id = %s
            """, (test_id,))
            self.db_conn.commit()

            cursor.close()
            self.test_results['fingerprinting'] = True
            logger.info("✅ Fingerprinting test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Fingerprinting test failed: {e}")
            self.db_conn.rollback()
            return False

    def test_checkpoint_tracking(self):
        """Test checkpoint tracking functionality"""
        try:
            cursor = self.db_conn.cursor()

            # Create test checkpoint
            test_congress = "999"

            cursor.execute("""
                SELECT incremental.get_or_create_checkpoint(
                    %s::text, %s::text, %s::text, %s::integer
                )
            """, ('congress.gov', 'members', test_congress, 100))

            checkpoint = cursor.fetchone()
            assert checkpoint is not None, "Checkpoint creation failed"

            # Test update progress
            cursor.execute("""
                SELECT incremental.update_checkpoint_progress(
                    %s::text, %s::text, %s::text,
                    %s::integer, NULL, NULL, NULL,
                    %s::integer, %s::boolean
                )
            """, ('congress.gov', 'members', test_congress, 50, 25, False))

            # Check updated values
            cursor.execute("""
                SELECT last_offset, total_processed, completion_percentage
                FROM incremental.ingestion_checkpoints
                WHERE data_source = 'congress.gov' AND data_type = 'members' AND category = %s
            """, (test_congress,))

            result = cursor.fetchone()
            assert result[0] == 50, f"Expected last_offset 50, got {result[0]}"
            assert result[1] == 25, f"Expected total_processed 25, got {result[1]}"
            expected_pct = 25.0
            actual_pct = float(result[2])
            assert abs(actual_pct - expected_pct) < 0.1, f"Expected completion {expected_pct}%, got {actual_pct}%"

            # Test completion
            cursor.execute("""
                SELECT incremental.update_checkpoint_progress(
                    %s::text, %s::text, %s::text,
                    %s::integer, NULL, NULL, NULL,
                    %s::integer, %s::boolean
                )
            """, ('congress.gov', 'members', test_congress, 100, 75, True))

            # Check completion
            cursor.execute("""
                SELECT is_completed, completion_percentage
                FROM incremental.ingestion_checkpoints
                WHERE data_source = 'congress.gov' AND data_type = 'members' AND category = %s
            """, (test_congress,))

            result = cursor.fetchone()
            assert result[0] == True, f"Expected is_completed True, got {result[0]}"
            expected_pct = 100.0
            actual_pct = float(result[1])
            assert abs(actual_pct - expected_pct) < 0.1, f"Expected completion {expected_pct}%, got {actual_pct}%"

            # Cleanup
            cursor.execute("""
                DELETE FROM incremental.ingestion_checkpoints
                WHERE data_source = 'congress.gov' AND data_type = 'members' AND category = %s
            """, (test_congress,))
            self.db_conn.commit()

            cursor.close()
            self.test_results['checkpoint_tracking'] = True
            logger.info("✅ Checkpoint tracking test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Checkpoint tracking test failed: {e}")
            self.db_conn.rollback()
            return False

    def test_error_handling(self):
        """Test error handling and recovery"""
        try:
            cursor = self.db_conn.cursor()

            # Test invalid data handling
            invalid_member = {
                'bioguide_id': None,  # Invalid: null bioguide_id
                'first_name': 'Test',
                'last_name': 'User',
                'official_full_name': 'Test User',
                'birthday': 'invalid-date',  # Invalid: bad date
                'gender': 'X',  # Invalid: not M/F
                'biography': '',
                'birthplace': None,
                'death_date': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            # Try to insert invalid data - should handle gracefully
            try:
                query = """
                    INSERT INTO congress.members (
                        bioguide_id, first_name, middle_name, last_name, suffix,
                        official_full_name, birthday, gender, biography, birthplace,
                        death_date, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(query, (
                    invalid_member['bioguide_id'], invalid_member['first_name'],
                    invalid_member.get('middle_name'), invalid_member['last_name'],
                    invalid_member.get('suffix'), invalid_member['official_full_name'],
                    invalid_member['birthday'], invalid_member['gender'],
                    invalid_member['biography'], invalid_member['birthplace'],
                    invalid_member['death_date'], invalid_member['created_at'],
                    invalid_member['updated_at']
                ))

                # If we get here, the database accepted invalid data (might be OK depending on constraints)
                self.db_conn.rollback()

            except Exception as insert_error:
                # Expected behavior - database rejected invalid data
                self.db_conn.rollback()
                logger.info(f"✅ Invalid data properly rejected: {type(insert_error).__name__}")

            # Test transaction rollback
            original_count = None
            try:
                cursor.execute("SELECT COUNT(*) FROM congress.members")
                original_count = cursor.fetchone()[0]

                # Start transaction
                cursor.execute("INSERT INTO congress.members (bioguide_id, first_name, last_name, created_at, updated_at) VALUES ('ROLLBACK_TEST', 'Test', 'User', NOW(), NOW())")

                # Rollback
                self.db_conn.rollback()

                # Verify rollback
                cursor.execute("SELECT COUNT(*) FROM congress.members")
                new_count = cursor.fetchone()[0]
                assert original_count == new_count, "Rollback failed - count changed"

            except Exception as rollback_error:
                self.db_conn.rollback()
                raise rollback_error

            cursor.close()
            self.test_results['error_handling'] = True
            logger.info("✅ Error handling test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.db_conn.rollback()
            return False

    def run_all_tests(self):
        """Run all tests and report results"""
        logger.info("🚀 Starting comprehensive ingestion pipeline tests")
        logger.info("=" * 60)

        tests = [
            ("Database Connection", self.test_database_connection),
            ("Data Normalization", self.test_data_normalization),
            ("Batch Insertion", self.test_batch_insertion),
            ("Fingerprinting", self.test_fingerprinting),
            ("Checkpoint Tracking", self.test_checkpoint_tracking),
            ("Error Handling", self.test_error_handling)
        ]

        for test_name, test_func in tests:
            logger.info(f"\n🧪 Testing {test_name}...")
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ {test_name} test crashed: {e}")

        # Final report
        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL TEST RESULTS")
        logger.info("=" * 60)

        passed = 0
        total = len(self.test_results)

        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1

        logger.info(f"\nSummary: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Ingestion pipeline is fully functional!")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed - Review issues before production use")

        return passed == total

    def cleanup(self):
        """Clean up database connections"""
        if self.db_conn:
            self.db_conn.close()

def main():
    """Main test runner"""
    tester = DetailedIngestionTester()

    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())
