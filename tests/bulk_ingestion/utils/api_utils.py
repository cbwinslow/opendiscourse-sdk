"""
API utilities for testing
"""

import json
import time
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import requests

class MockResponse:
    """Mock response for testing API calls"""

    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] = None,
                 headers: Dict[str, str] = None, text: str = ""):
        self.status_code = status_code
        self.json_data = json_data or {}
        self.headers = headers or {}
        self.text = text
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

class APIResponseBuilder:
    """Builder for creating mock API responses"""

    @staticmethod
    def congress_bills_response(bills: List[Dict[str, Any]] = None,
                               limit: int = 50, offset: int = 0,
                               total_count: int = 1000) -> Dict[str, Any]:
        """Build Congress bills API response"""
        if bills is None:
            bills = APIResponseBuilder.generate_sample_bills(limit)

        return {
            'bills': bills,
            'pagination': {
                'count': total_count,
                'count_exact': True,
                'count_minimum': total_count,
                'limit': limit,
                'offset': offset
            }
        }

    @staticmethod
    def congress_members_response(members: List[Dict[str, Any]] = None,
                                limit: int = 50, offset: int = 0,
                                total_count: int = 500) -> Dict[str, Any]:
        """Build Congress members API response"""
        if members is None:
            members = APIResponseBuilder.generate_sample_members(limit)

        return {
            'members': members,
            'pagination': {
                'count': total_count,
                'count_exact': True,
                'limit': limit,
                'offset': offset
            }
        }

    @staticmethod
    def openstates_people_response(people: List[Dict[str, Any]] = None,
                                 limit: int = 50, offset: int = 0,
                                 total_count: int = 2000) -> Dict[str, Any]:
        """Build OpenStates people API response"""
        if people is None:
            people = APIResponseBuilder.generate_sample_people(limit)

        return {
            'results': people,
            'meta': {
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total_count': total_count
                }
            }
        }

    @staticmethod
    def generate_sample_bills(count: int) -> List[Dict[str, Any]]:
        """Generate sample bill data"""
        bills = []
        for i in range(count):
            bill = {
                'billId': f'hr{i+100}-{118}',
                'type': 'HR',
                'number': str(i + 100),
                'congress': 118,
                'originChamberCode': 'H',
                'originChamberName': 'House of Representatives',
                'title': f'Sample Bill {i+100} Title',
                'shortTitle': f'Sample Bill {i+100}',
                'latestAction': {
                    'actionDate': f'2024-{(i % 12) + 1:02d}-{((i % 28) + 1):02d}T00:00:00Z',
                    'text': f'Latest action for bill {i+100}'
                },
                'sponsor': {
                    'bioguideId': f'T{str(i+1).zfill(4)}',
                    'thomasId': f'{i+1:05d}',
                    'fullName': f'Test Sponsor {i+1}',
                    'firstName': f'Test',
                    'lastName': f'Sponsor {i+1}'
                },
                'introducedDate': f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T00:00:00Z',
                'subjects': [
                    {'name': f'Subject {i % 5}'},
                    {'name': f'Topic {i % 3}'}
                ],
                'policyArea': {'name': f'Policy Area {i % 2}'},
                'url': f'https://api.congress.gov/bill/hr{i+100}-118/',
                'citations': []
            }
            bills.append(bill)
        return bills

    @staticmethod
    def generate_sample_members(count: int) -> List[Dict[str, Any]]:
        """Generate sample member data"""
        members = []
        for i in range(count):
            member = {
                'bioguideId': f'T{str(i+1).zfill(4)}',
                'thomasId': f'{i+1:05d}',
                'fullName': f'Test Member {i+1}',
                'firstName': 'Test',
                'lastName': f'Member {i+1}',
                'state': 'CA' if i % 2 == 0 else 'NY',
                'district': (i % 50) + 1,
                'party': 'R' if i % 2 == 0 else 'D',
                'chamber': 'House',
                'terms': [
                    {
                        'startYear': 2023,
                        'endYear': 2025,
                        'memberType': 'Representative',
                        'stateCode': 'CA' if i % 2 == 0 else 'NY',
                        'districtNumber': (i % 50) + 1
                    }
                ]
            }
            members.append(member)
        return members

    @staticmethod
    def generate_sample_people(count: int) -> List[Dict[str, Any]]:
        """Generate sample OpenStates person data"""
        people = []
        for i in range(count):
            person = {
                'id': f'ocd-person/{i+1}',
                'name': f'Test Person {i+1}',
                'family_name': f'Person {i+1}',
                'given_name': 'Test',
                'image': f'https://example.com/images/person{i+1}.jpg',
                'party': [
                    {'name': 'Republican'} if i % 2 == 0 else {'name': 'Democrat'}
                ],
                'roles': [
                    {
                        'type': 'member',
                        'organization': {'name': 'California State Assembly'},
                        'district': f'District {(i % 80) + 1}',
                        'start_date': '2023-01-01',
                        'end_date': None
                    }
                ],
                'contact_details': [
                    {
                        'type': 'phone',
                        'value': f'555-{i+1000:04d}',
                        'note': 'Capitol Office'
                    }
                ],
                'ids': {
                    'openstates': f'{(i+1):04d}',
                    'legacy_openstates': str(i+1)
                }
            }
            people.append(person)
        return people

class RateLimiterTester:
    """Test rate limiting functionality"""

    def __init__(self):
        self.call_times = []
        self.api_calls = []

    def record_api_call(self, api_name: str, tokens_used: int = 1):
        """Record an API call"""
        self.call_times.append((time.time(), api_name, tokens_used))
        self.api_calls.append({
            'timestamp': time.time(),
            'api': api_name,
            'tokens': tokens_used
        })

    def get_calls_per_second(self, api_name: str, time_window: int = 60) -> float:
        """Get calls per second for an API"""
        now = time.time()
        cutoff = now - time_window

        recent_calls = [
            call for call in self.call_times
            if call[0] > cutoff and call[1] == api_name
        ]

        if time_window == 0:
            return 0

        return len(recent_calls) / time_window

    def verify_rate_limit(self, api_name: str, expected_rate: float, tolerance: float = 0.1) -> bool:
        """Verify rate limiting is working correctly"""
        calls_per_sec = self.get_calls_per_second(api_name, 60)
        difference = abs(calls_per_sec - expected_rate)
        return difference <= tolerance

    def get_api_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all APIs"""
        stats = {}

        for api_name in set(call[1] for call in self.call_times):
            api_calls = [call for call in self.call_times if call[1] == api_name]

            if len(api_calls) >= 2:
                time_span = api_calls[-1][0] - api_calls[0][0]
                avg_rate = len(api_calls) / time_span if time_span > 0 else 0
                recent_rate = self.get_calls_per_second(api_name, 30)
            else:
                time_span = 0
                avg_rate = 0
                recent_rate = 0

            stats[api_name] = {
                'total_calls': len(api_calls),
                'time_span_seconds': time_span,
                'average_rate': avg_rate,
                'recent_rate_30s': recent_rate,
                'first_call': datetime.fromtimestamp(api_calls[0][0]) if api_calls else None,
                'last_call': datetime.fromtimestamp(api_calls[-1][0]) if api_calls else None
            }

        return stats

class APITestHelper:
    """Helper class for API testing"""

    def __init__(self):
        self.mock_responses = {}
        self.rate_limiter_tester = RateLimiterTester()

    def setup_mock_response(self, url: str, response_data: Dict[str, Any],
                           status_code: int = 200, headers: Dict[str, str] = None):
        """Setup mock response for a URL"""
        self.mock_responses[url] = {
            'data': response_data,
            'status_code': status_code,
            'headers': headers or {'X-RateLimit-Remaining': '100', 'X-RateLimit-Reset': '3600'}
        }

    def get_mock_response(self, url: str) -> Optional[MockResponse]:
        """Get mock response for URL"""
        if url in self.mock_responses:
            config = self.mock_responses[url]
            return MockResponse(
                status_code=config['status_code'],
                json_data=config['data'],
                headers=config['headers']
            )
        return None

    def create_congress_api_mock(self, bills_data: List[Dict[str, Any]] = None,
                               limit: int = 50, offset: int = 0) -> str:
        """Create mock Congress API response"""
        response_data = APIResponseBuilder.congress_bills_response(bills_data, limit, offset)
        url = f"https://api.congress.gov/v3/bill?limit={limit}&offset={offset}"
        self.setup_mock_response(url, response_data)
        return url

    def create_openstates_api_mock(self, people_data: List[Dict[str, Any]] = None,
                                 limit: int = 50, offset: int = 0) -> str:
        """Create mock OpenStates API response"""
        response_data = APIResponseBuilder.openstates_people_response(people_data, limit, offset)
        url = f"https://v3.openstates.org/people?limit={limit}&offset={offset}"
        self.setup_mock_response(url, response_data)
        return url

    def simulate_rate_limit_error(self, api_name: str):
        """Simulate rate limit error"""
        headers = {
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(time.time()) + 60),
            'Retry-After': '60'
        }

        # This would be used with mock to simulate 429 response
        return MockResponse(status_code=429, json_data={'error': 'Rate limit exceeded'}, headers=headers)

    def simulate_network_error(self):
        """Simulate network error"""
        return MockResponse(status_code=500, json_data={'error': 'Internal server error'})

    def simulate_auth_error(self):
        """Simulate authentication error"""
        return MockResponse(status_code=401, json_data={'error': 'Unauthorized'})

    def create_error_scenarios(self) -> Dict[str, MockResponse]:
        """Create various error scenarios for testing"""
        return {
            'rate_limit': self.simulate_rate_limit_error('congress.gov'),
            'network_error': self.simulate_network_error(),
            'auth_error': self.simulate_auth_error(),
            'timeout': MockResponse(status_code=408, json_data={'error': 'Request timeout'}),
            'not_found': MockResponse(status_code=404, json_data={'error': 'Not found'}),
            'server_error': MockResponse(status_code=503, json_data={'error': 'Service unavailable'})
        }

def create_test_api_config() -> Dict[str, str]:
    """Create test API configuration"""
    return {
        'congress_api_key': 'test_congress_key_12345',
        'openstates_api_key': 'test_openstates_key_67890',
        'govinfo_api_key': 'test_govinfo_key_abcdef'
    }

def get_api_helper() -> APITestHelper:
    """Get API test helper instance"""
    return APITestHelper()
