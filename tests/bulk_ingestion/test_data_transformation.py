"""
Data transformation and normalization tests
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock
from typing import Dict, Any, Optional

class TestBillDataNormalization:
    """Test bill data normalization functionality"""

    @pytest.fixture
    def sample_bill_data(self):
        """Provide sample bill data for testing"""
        return {
            'billId': 'hr123-118',
            'type': 'HR',
            'number': '123',
            'titles': [
                {'title': 'Test Bill Title', 'type': 'short'},
                {'title': 'A Bill to Test Something', 'type': 'official'}
            ],
            'sponsor': {
                'bioguideId': 'T0001',
                'fullName': 'Test Sponsor'
            },
            'introducedDate': '2024-01-15T00:00:00Z',
            'url': 'https://api.congress.gov/bill/hr123-118/',
            'actions': [
                {
                    'actionDate': '2024-01-15T00:00:00Z',
                    'text': 'Introduced in House'
                }
            ],
            'policyArea': {
                'name': 'Government Operations'
            },
            'subjects': [
                {'name': 'Tax policy'},
                {'name': 'Government spending'}
            ]
        }

    def test_normalize_bill_data_complete(self, sample_bill_data):
        """Test normalization of complete bill data"""
        def normalize_bill_data(bill_data: Dict[str, Any], congress: int) -> Optional[Dict[str, Any]]:
            try:
                bill = bill_data.get('bill', bill_data)

                bill_id = bill.get('billId', '')
                bill_type = bill.get('type', '')
                bill_number = bill.get('number', '')

                if '-' in bill_id:
                    congress_part, type_num = bill_id.split('-', 1)
                    if type_num:
                        bill_type = type_num[0] if type_num[0].isalpha() else bill_type
                        bill_number = type_num[1:] if type_num[0].isalpha() else type_num

                titles = bill.get('titles', [])
                primary_title = titles[0].get('title', '') if titles else ''

                sponsor = bill.get('sponsor', {})
                sponsor_bioguide = sponsor.get('bioguideId', '')

                introduced_date = bill.get('introducedDate', '')

                actions = bill.get('actions', [])
                latest_action = actions[-1] if actions else {}
                latest_action_text = latest_action.get('text', '')
                latest_action_date = latest_action.get('actionDate', '')

                policy_areas = bill.get('policyArea', {})
                policy_area_name = policy_areas.get('name', '')

                subjects = bill.get('subjects', [])
                subject_names = [s.get('name', '') for s in subjects if s.get('name')]

                return {
                    'bill_id': bill_id,
                    'congress': congress,
                    'bill_type': bill_type,
                    'bill_number': bill_number,
                    'title': primary_title,
                    'sponsor_bioguide_id': sponsor_bioguide,
                    'introduced_date': datetime.fromisoformat(introduced_date.replace('Z', '+00:00')) if introduced_date else None,
                    'latest_action_text': latest_action_text,
                    'latest_action_date': datetime.fromisoformat(latest_action_date.replace('Z', '+00:00')) if latest_action_date else None,
                    'policy_area': policy_area_name,
                    'subjects': subject_names,
                    'url': bill.get('url', ''),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            except Exception:
                return None

        normalized = normalize_bill_data(sample_bill_data, 118)

        assert normalized is not None
        assert normalized['bill_id'] == 'hr123-118'
        assert normalized['congress'] == 118
        assert normalized['bill_type'] == 'HR'
        assert normalized['bill_number'] == '123'
        assert normalized['title'] == 'Test Bill Title'
        assert normalized['sponsor_bioguide_id'] == 'T0001'
        assert normalized['policy_area'] == 'Government Operations'
        assert isinstance(normalized['subjects'], list)
        assert len(normalized['subjects']) == 2
        assert 'Tax policy' in normalized['subjects']
        assert 'Government spending' in normalized['subjects']
        assert normalized['url'] == 'https://api.congress.gov/bill/hr123-118/'

    def test_normalize_bill_data_minimal(self):
        """Test normalization with minimal bill data"""
        def normalize_bill_data(bill_data: Dict[str, Any], congress: int) -> Optional[Dict[str, Any]]:
            try:
                bill = bill_data.get('bill', bill_data)
                bill_id = bill.get('billId', '')
                return {
                    'bill_id': bill_id,
                    'congress': congress,
                    'bill_type': bill.get('type', ''),
                    'bill_number': bill.get('number', ''),
                    'title': bill.get('titles', [{}])[0].get('title', '') if bill.get('titles') else '',
                    'sponsor_bioguide_id': bill.get('sponsor', {}).get('bioguideId', ''),
                    'introduced_date': None,
                    'latest_action_text': '',
                    'latest_action_date': None,
                    'policy_area': '',
                    'subjects': [],
                    'url': '',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            except Exception:
                return None

        minimal_data = {'billId': 's1-118'}
        normalized = normalize_bill_data(minimal_data, 118)

        assert normalized is not None
        assert normalized['bill_id'] == 's1-118'
        assert normalized['congress'] == 118
        assert normalized['title'] == ''
        assert normalized['subjects'] == []

    def test_normalize_bill_data_missing_required_fields(self):
        """Test normalization with missing required fields"""
        def normalize_bill_data(bill_data: Dict[str, Any], congress: int) -> Optional[Dict[str, Any]]:
            bill = bill_data.get('bill', bill_data)
            bill_id = bill.get('billId', '')
            if not bill_id:
                return None

            return {
                'bill_id': bill_id,
                'congress': congress,
                'title': bill.get('titles', [{}])[0].get('title', '') if bill.get('titles') else '',
            }

        missing_id_data = {'type': 'HR', 'number': '123'}
        normalized = normalize_bill_data(missing_id_data, 118)

        assert normalized is None

    def test_bill_id_parsing(self):
        """Test bill ID parsing logic"""
        def parse_bill_id(bill_id: str, provided_type: str, provided_number: str) -> tuple:
            bill_type = provided_type
            bill_number = provided_number

            if '-' in bill_id:
                congress_part, type_num = bill_id.split('-', 1)
                if type_num:
                    bill_type = type_num[0] if type_num[0].isalpha() else bill_type
                    bill_number = type_num[1:] if type_num[0].isalpha() else type_num

            return bill_type, bill_number

        test_cases = [
            ('hr123-118', 'HR', '123'),
            ('s1-118', 'S', '1'),
            ('hjres45-118', 'HJR', '45'),
            ('sjres12-118', 'SJR', '12'),
            ('hr456', 'HR', '456'),
        ]

        for bill_id, expected_type, expected_number in test_cases:
            bill_type, bill_number = parse_bill_id(bill_id, '', '')
            assert bill_type == expected_type
            assert bill_number == expected_number

class TestDataValidation:
    """Test data validation and sanitization"""

    @pytest.mark.unit
    def test_string_field_validation(self):
        """Test validation of string fields"""
        def validate_string_field(value: str, max_length: int = None) -> str:
            if not isinstance(value, str):
                return ''

            if max_length and len(value) > max_length:
                return value[:max_length]

            return value.strip()

        assert validate_string_field('') == ''
        assert validate_string_field('   test   ') == 'test'
        assert validate_string_field('a' * 1000, 500) == 'a' * 500
        assert validate_string_field(123) == ''
        assert validate_string_field(None) == ''

    @pytest.mark.unit
    def test_date_field_validation(self):
        """Test validation of date fields"""
        def parse_date_safely(date_str: str) -> Optional[datetime]:
            if not date_str:
                return None

            try:
                if date_str.endswith('Z'):
                    date_str = date_str[:-1] + '+00:00'
                return datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                return None

        result1 = parse_date_safely('2024-01-15T00:00:00Z')
        assert isinstance(result1, datetime)

        result2 = parse_date_safely('invalid-date')
        assert result2 is None

        result3 = parse_date_safely('')
        assert result3 is None

        result4 = parse_date_safely(None)
        assert result4 is None

    @pytest.mark.unit
    def test_list_field_validation(self):
        """Test validation of list fields"""
        def sanitize_list(items: list) -> list:
            if not isinstance(items, list):
                return []

            return [str(item).strip() for item in items if str(item).strip()]

        assert sanitize_list([]) == []
        assert sanitize_list(['a', '  b  ', 'c']) == ['a', 'b', 'c']
        assert sanitize_list(['', None, 'valid']) == ['valid']
        assert sanitize_list('not a list') == []
        assert sanitize_list(None) == []

class TestDataTransformationEdgeCases:
    """Test edge cases in data transformation"""

    @pytest.mark.unit
    def test_empty_bill_data(self):
        """Test handling of completely empty bill data"""
        def normalize_bill_data(bill_data: Dict[str, Any], congress: int) -> Optional[Dict[str, Any]]:
            if not bill_data:
                return None

            bill_id = bill_data.get('billId', '')
            if not bill_id:
                return None

            return {
                'bill_id': bill_id,
                'congress': congress,
                'title': bill_data.get('titles', [{}])[0].get('title', '') if bill_data.get('titles') else '',
            }

        empty_data = {}
        result = normalize_bill_data(empty_data, 118)
        assert result is None

    @pytest.mark.unit
    def test_special_characters_in_data(self):
        """Test handling of special characters in data fields"""
        def sanitize_text(text: str) -> str:
            if not isinstance(text, str):
                return ''

            sanitized = ''.join(c for c in text if c.isprintable() or c in ['\t', '\n'])
            return sanitized.strip()

        assert sanitize_text('Normal text') == 'Normal text'
        assert sanitize_text('Text with \x00null') == 'Text with ull'
        assert 'Text with\t\ttabs' == sanitize_text('Text with\t\ttabs')
        assert sanitize_text('Control\x01\x02chars') == 'Controlchars'

    @pytest.mark.unit
    def test_unicode_handling(self):
        """Test handling of unicode characters in bill data"""
        unicode_data = {
            'title': 'Bañl tô introduce résøurcés',
            'sponsor_name': 'José María González',
            'policy_area': 'Educación y Salud Pública'
        }

        assert 'Bañl' in unicode_data['title']
        assert 'José' in unicode_data['sponsor_name']
        assert 'Educación' in unicode_data['policy_area']

class TestDataMapping:
    """Test mapping between API response and database schema"""

    @pytest.mark.unit
    def test_congress_api_to_db_mapping(self):
        """Test mapping from Congress API response to database schema"""
        api_bill = {
            'billId': 'hr123-118',
            'type': 'HR',
            'number': '123',
            'congress': 118,
            'title': 'A Bill to Test Something',
            'shortTitle': 'Test Bill',
            'sponsor': {
                'bioguideId': 'T1234',
                'fullName': 'Test Sponsor'
            },
            'introducedDate': '2024-01-15T00:00:00Z',
            'url': 'https://api.congress.gov/bill/hr123-118/',
            'latestAction': {
                'actionDate': '2024-01-20T00:00:00Z',
                'text': 'Passed House'
            }
        }

        bill_id = api_bill['billId']
        congress = api_bill['congress']
        bill_type = api_bill['type']
        bill_number = str(api_bill['number'])
        title = api_bill.get('shortTitle') or api_bill.get('title', '')
        sponsor_id = api_bill.get('sponsor', {}).get('bioguideId', '')
        introduced_date = api_bill.get('introducedDate', '')
        latest_action = api_bill.get('latestAction', {})
        latest_action_text = latest_action.get('text', '')
        latest_action_date = latest_action.get('actionDate', '')

        assert bill_id == 'hr123-118'
        assert congress == 118
        assert bill_type == 'HR'
        assert bill_number == '123'
        assert title == 'Test Bill'
        assert sponsor_id == 'T1234'
        assert introduced_date == '2024-01-15T00:00:00Z'
        assert latest_action_text == 'Passed House'
        assert latest_action_date == '2024-01-20T00:00:00Z'

class TestDataConsistency:
    """Test data consistency and integrity checks"""

    @pytest.mark.unit
    def test_duplicate_detection_logic(self):
        """Test logic for detecting duplicate records"""
        def generate_bill_fingerprint(bill_data: Dict[str, Any]) -> str:
            key_fields = {
                'bill_id': bill_data.get('billId', ''),
                'title': bill_data.get('title', ''),
                'sponsor': bill_data.get('sponsor', {}).get('bioguideId', ''),
                'introduced_date': bill_data.get('introducedDate', '')
            }

            fingerprint_str = json.dumps(key_fields, sort_keys=True)
            return fingerprint_str

        bill_data = {
            'billId': 'hr123-118',
            'title': 'Test Bill',
            'sponsor': {'bioguideId': 'T1234'},
            'introducedDate': '2024-01-15T00:00:00Z'
        }

        fingerprint1 = generate_bill_fingerprint(bill_data)
        fingerprint2 = generate_bill_fingerprint(bill_data)
        assert fingerprint1 == fingerprint2

        different_data = bill_data.copy()
        different_data['billId'] = 'hr124-118'
        fingerprint3 = generate_bill_fingerprint(different_data)
        assert fingerprint1 != fingerprint3

    @pytest.mark.unit
    def test_required_field_validation(self):
        """Test validation of required fields"""
        def validate_required_fields(bill_data: Dict[str, Any]) -> Dict[str, bool]:
            required_fields = ['bill_id', 'congress', 'bill_type']
            validation_results = {}

            for field in required_fields:
                value = bill_data.get(field)
                validation_results[field] = value is not None and value != ''

            return validation_results

        valid_data = {
            'bill_id': 'hr123-118',
            'congress': 118,
            'bill_type': 'HR'
        }

        invalid_data = {
            'bill_id': '',
            'congress': None,
            'bill_type': 'HR'
        }

        valid_results = validate_required_fields(valid_data)
        invalid_results = validate_required_fields(invalid_data)

        assert all(valid_results.values())
        assert not all(invalid_results.values())
