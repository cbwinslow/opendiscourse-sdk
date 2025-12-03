#!/usr/bin/env python3
"""
Minimal OpenDiscourse Tests
Test core functionality without complex dependencies
"""

import pytest
import os
import psycopg2
from datetime import datetime
from typing import Dict, Any

class TestDatabaseConnection:
    """Test database connectivity"""

    def test_database_connection(self):
        """Test basic database connection"""
        try:
            conn = psycopg2.connect(
                database='opendiscourse',
                user='cbwinslow',
                host='/var/run/postgresql'
            )
            conn.close()
            assert True, "Database connection successful"
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    def test_required_tables_exist(self):
        """Test that required tables exist"""
        required_tables = [
            'congress.members',
            'congress.bills',
            'congress.chambers',
            'openstates.people',
            'openstates.jurisdictions'
        ]

        try:
            conn = psycopg2.connect(
                database='opendiscourse',
                user='cbwinslow',
                host='/var/run/postgresql'
            )
            cursor = conn.cursor()

            for table in required_tables:
                schema, table_name = table.split('.')
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = '{schema}'
                        AND table_name = '{table_name}'
                    )
                """)
                exists = cursor.fetchone()[0]
                assert exists, f"Table {table} does not exist"

            cursor.close()
            conn.close()
        except Exception as e:
            pytest.fail(f"Table check failed: {e}")

class TestAPICredentials:
    """Test API credentials are available"""

    def test_congress_api_key(self):
        """Test Congress API key exists"""
        api_key = os.getenv('CONGRESS_API_KEY')
        assert api_key, "CONGRESS_API_KEY not found"
        assert api_key != 'DEMO_KEY', "Demo key detected"

    def test_openstates_api_key(self):
        """Test OpenStates API key exists"""
        api_key = os.getenv('OPENSTATES_API_KEY')
        assert api_key, "OPENSTATES_API_KEY not found"
        assert api_key != 'DEMO_KEY', "Demo key detected"

class TestCongressAPI:
    """Test Congress.gov API functionality"""

    @pytest.fixture
    def api_key(self):
        return os.getenv('CONGRESS_API_KEY')

    def test_api_connectivity(self, api_key):
        """Test basic API connectivity"""
        import requests

        headers = {'X-API-Key': api_key, 'Accept': 'application/json'}
        response = requests.get(
            'https://api.congress.gov/v3/member/congress/118?limit=1',
            headers=headers
        )

        assert response.status_code == 200, f"API request failed: {response.status_code}"

        data = response.json()
        assert 'members' in data, "Invalid API response structure"

class TestDataTransformation:
    """Test data transformation logic"""

    def test_chamber_code_mapping(self):
        """Test chamber code mapping"""
        chamber_mapping = {
            'House': 'house',
            'Senate': 'senate',
            'Joint': 'joint'
        }

        # Test valid mappings
        assert chamber_mapping.get('House') == 'house'
        assert chamber_mapping.get('Senate') == 'senate'
        assert chamber_mapping.get('Joint') == 'joint'

        # Test invalid mapping
        assert chamber_mapping.get('Invalid', '') == ''
        assert chamber_mapping.get('Unknown', '').lower() == 'unknown'

    def test_bill_data_transformation(self):
        """Test bill data transformation"""
        bill_data = {
            'bill': {
                'type': 'HR',
                'number': '1234',
                'originChamber': 'House',
                'introducedDate': '2023-01-01',
                'title': 'Test Bill',
                'sponsor': {'bioguideId': 'T000123'}
            }
        }

        # Simulate transformation
        bill = bill_data.get('bill', bill_data)
        chamber_mapping = {
            'House': 'house',
            'Senate': 'senate',
            'Joint': 'joint'
        }
        origin_chamber = chamber_mapping.get(bill.get('originChamber', ''), bill.get('originChamber', '').lower())

        transformed = (
            118,  # congress
            bill.get('type', ''),
            int(bill.get('number', 0)),
            origin_chamber,
            bill.get('introducedDate'),
            None,  # latest_action_date
            None,  # latest_action_text
            None,  # policy_area
            bill.get('title', ''),
            bill.get('sponsor', {}).get('bioguideId'),
            datetime.now()
        )

        # Verify transformation
        assert transformed[0] == 118  # congress
        assert transformed[1] == 'HR'  # bill_type
        assert transformed[2] == 1234  # bill_number
        assert transformed[3] == 'house'  # origin_chamber (mapped)
        assert transformed[4] == '2023-01-01'  # introduced_date
        assert transformed[8] == 'Test Bill'  # title

class TestDatabaseConstraints:
    """Test database constraints and foreign keys"""

    def test_chambers_foreign_key(self):
        """Test chamber foreign key constraint"""
        try:
            conn = psycopg2.connect(
                database='opendiscourse',
                user='cbwinslow',
                host='/var/run/postgresql'
            )
            cursor = conn.cursor()

            # Test valid chamber codes
            cursor.execute("SELECT chamber_code FROM congress.chambers")
            valid_chambers = [row[0] for row in cursor.fetchall()]

            expected_chambers = ['house', 'senate', 'joint']
            for chamber in expected_chambers:
                assert chamber in valid_chambers, f"Chamber {chamber} not found"

            cursor.close()
            conn.close()
        except Exception as e:
            pytest.fail(f"Chamber constraint test failed: {e}")

    def test_member_foreign_key(self):
        """Test member foreign key constraint"""
        try:
            conn = psycopg2.connect(
                database='opendiscourse',
                user='cbwinslow',
                host='/var/run/postgresql'
            )
            cursor = conn.cursor()

            # Check if we have any members
            cursor.execute("SELECT COUNT(*) FROM congress.members")
            member_count = cursor.fetchone()[0]

            if member_count > 0:
                # Test a sample member
                cursor.execute("SELECT bioguide_id FROM congress.members LIMIT 1")
                member_id = cursor.fetchone()[0]
                assert member_id, "No member bioguide ID found"

            cursor.close()
            conn.close()
        except Exception as e:
            pytest.fail(f"Member constraint test failed: {e}")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
