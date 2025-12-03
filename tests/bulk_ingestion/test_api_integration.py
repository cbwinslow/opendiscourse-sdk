"""
API integration and rate limiting tests
"""

import pytest
import requests
import time
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from rate_limiter import TokenBucket, RateLimiter, AdaptiveRateLimiter
from env_config import validate_api_keys, get_optional_env_var

from .utils.api_utils import get_api_helper, APIResponseBuilder, RateLimiterTester
from .conftest import generate_test_bills

class TestAPIConnectivity:
    """Test API connectivity and basic operations"""

    @pytest.mark.network
    @pytest.mark.integration
    def test_congress_api_connectivity(self, mock_env_vars):
        """Test Congress API connectivity with actual API call"""
        if get_optional_env_var('CONGRESS_API_KEY', '').startswith('DEMO'):
            pytest.skip("Skipping API test with demo key")

        url = "https://api.congress.gov/v3/member/congress/118"
        headers = {
            'X-API-Key': get_optional_env_var('CONGRESS_API_KEY')
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            assert response.status_code == 200

            data = response.json()
            assert 'members' in data

        except requests.exceptions.RequestException as e:
            pytest.skip(f"API connectivity test skipped due to network issue: {e}")

    @pytest.mark.network
    @pytest.mark.integration
    def test_openstates_api_connectivity(self, mock_env_vars):
        """Test OpenStates API connectivity"""
        if get_optional_env_var('OPENSTATES_API_KEY', '').startswith('DEMO'):
            pytest.skip("Skipping API test with demo key")

        url = "https://v3.openstates.org/people"
        headers = {
            'X-API-KEY': get_optional_env_var('OPENSTATES_API_KEY')
        }
        params = {'limit': 1, 'jurisdiction': 'ca'}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            assert response.status_code == 200

            data = response.json()
            assert 'results' in data

        except requests.exceptions.RequestException as e:
            pytest.skip(f"API connectivity test skipped due to network issue: {e}")

    def test_api_connectivity_mocked(self, mock_requests):
        """Test API connectivity with mocked responses"""
        mock_response = mock_requests['response']
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'bills': [{'billId': 'hr123-118', 'type': 'HR', 'number': '123'}]
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_response

            response = requests.get("https://api.congress.gov/v3/bill")
            assert response.status_code == 200

            data = response.json()
            assert 'bills' in data
            assert len(data['bills']) == 1

class TestAPIAuthentication:
    """Test API authentication and validation"""

    @pytest.mark.unit
    def test_api_key_validation(self, mock_env_vars):
        """Test API key validation"""
        api_keys = validate_api_keys()

        assert 'congress.gov' in api_keys
        assert 'openstates.org' in api_keys
        assert 'govinfo.gov' in api_keys

        assert api_keys['congress.gov'] == True
        assert api_keys['openstates.org'] == True
        assert api_keys['govinfo.gov'] == True

    @pytest.mark.unit
    def test_api_key_invalid_format(self):
        """Test API key validation with invalid format"""
        with patch.dict('os.environ', {
            'CONGRESS_API_KEY': 'DEMO_KEY',
            'OPENSTATES_API_KEY': 'TEST_KEY',
            'GOVINFO_API_KEY': 'DEMO'
        }):
            api_keys = validate_api_keys()

            assert api_keys['congress.gov'] == True
            assert api_keys['openstates.org'] == True
            assert api_keys['govinfo.gov'] == True

    @pytest.mark.unit
    def test_missing_api_keys(self):
        """Test behavior with missing API keys"""
        with patch.dict('os.environ', {}, clear=True):
            api_keys = validate_api_keys()

            assert api_keys['congress.gov'] == False
            assert api_keys['openstates.org'] == False
            assert api_keys['govinfo.gov'] == False

class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.unit
    def test_token_bucket_basic(self):
        """Test basic token bucket functionality"""
        bucket = TokenBucket(rate=1.0, capacity=5)

        assert bucket.consume(1) == True
        assert bucket.consume(4) == True
        assert bucket.consume(1) == False

        time.sleep(1.1)
        assert bucket.consume(1) == True

    @pytest.mark.unit
    def test_token_bucket_rate_limit(self):
        """Test token bucket rate limiting"""
        bucket = TokenBucket(rate=2.0, capacity=2)

        start_time = time.time()

        assert bucket.consume(2) == True
        assert bucket.consume(1) == False

        time.sleep(1)
        assert bucket.consume(1) == True

        elapsed = time.time() - start_time
        assert elapsed >= 1.0

    @pytest.mark.unit
    def test_rate_limiter_configuration(self, rate_limiter):
        """Test rate limiter configuration"""
        assert 'congress.gov' in rate_limiter.limiters
        assert 'openstates.org' in rate_limiter.limiters
        assert 'govinfo.gov' in rate_limiter.limiters

        congress_limiter = rate_limiter.get_limiter('congress.gov')
        assert isinstance(congress_limiter, TokenBucket)

        default_limiter = rate_limiter.get_limiter('unknown-api')
        assert isinstance(default_limiter, TokenBucket)

    @pytest.mark.unit
    def test_rate_limiter_wait_functionality(self):
        """Test rate limiter wait functionality"""
        rate_limiter = RateLimiter()

        start_time = time.time()
        rate_limiter.wait('congress.gov', 1)
        elapsed = time.time() - start_time

        assert elapsed >= 0.1

    @pytest.mark.unit
    def test_can_proceed_functionality(self):
        """Test can_proceed functionality"""
        rate_limiter = RateLimiter()

        assert rate_limiter.can_proceed('congress.gov', 1) == True

        for _ in range(20):
            if not rate_limiter.can_proceed('congress.gov', 1):
                break

        for _ in range(5):
            rate_limiter.can_proceed('congress.gov', 1)

class TestAdaptiveRateLimiting:
    """Test adaptive rate limiting functionality"""

    @pytest.mark.unit
    def test_adaptive_rate_limiter_initialization(self, adaptive_limiter):
        """Test adaptive rate limiter initialization"""
        assert adaptive_limiter.api_name == 'test_api'
        assert adaptive_limiter.base_rate == 1.0
        assert adaptive_limiter.capacity == 5
        assert adaptive_limiter.current_rate == 1.0
        assert adaptive_limiter.consecutive_errors == 0
        assert adaptive_limiter.max_errors == 3

    @pytest.mark.unit
    def test_update_from_response_headers(self, adaptive_limiter):
        """Test rate limit update from response headers"""
        headers = {
            'X-RateLimit-Remaining': '50',
            'X-RateLimit-Reset': str(int(time.time()) + 60)
        }

        initial_rate = adaptive_limiter.current_rate
        adaptive_limiter.update_from_response(headers)

        assert adaptive_limiter.current_rate != initial_rate

    @pytest.mark.unit
    def test_handle_error_responses(self, adaptive_limiter):
        """Test handling of error responses"""
        initial_rate = adaptive_limiter.current_rate
        adaptive_limiter.handle_error(429)

        assert adaptive_limiter.consecutive_errors == 1
        assert adaptive_limiter.current_rate == initial_rate

        for _ in range(3):
            adaptive_limiter.handle_error(429)

        assert adaptive_limiter.current_rate < initial_rate

    @pytest.mark.unit
    def test_handle_success_responses(self, adaptive_limiter):
        """Test handling of success responses"""
        adaptive_limiter.consecutive_errors = 2
        initial_rate = adaptive_limiter.current_rate

        adaptive_limiter.handle_error(200)

        assert adaptive_limiter.consecutive_errors == 0
        assert adaptive_limiter.current_rate == initial_rate

class TestAPIResponseHandling:
    """Test API response handling and parsing"""

    @pytest.mark.unit
    def test_response_builder_bills(self):
        """Test Congress bills response building"""
        bills = APIResponseBuilder.generate_sample_bills(5)
        assert len(bills) == 5

        response = APIResponseBuilder.congress_bills_response(bills)

        assert 'bills' in response
        assert 'pagination' in response
        assert len(response['bills']) == 5
        assert response['pagination']['limit'] == 50
        assert response['pagination']['offset'] == 0

    @pytest.mark.unit
    def test_response_builder_members(self):
        """Test Congress members response building"""
        members = APIResponseBuilder.generate_sample_members(3)
        assert len(members) == 3

        response = APIResponseBuilder.congress_members_response(members)

        assert 'members' in response
        assert 'pagination' in response
        assert len(response['members']) == 3

    @pytest.mark.unit
    def test_response_builder_openstates(self):
        """Test OpenStates response building"""
        people = APIResponseBuilder.generate_sample_people(4)
        assert len(people) == 4

        response = APIResponseBuilder.openstates_people_response(people)

        assert 'results' in response
        assert 'meta' in response
        assert 'pagination' in response['meta']
        assert len(response['results']) == 4

    @pytest.mark.unit
    def test_sample_data_structure(self):
        """Test structure of generated sample data"""
        bills = APIResponseBuilder.generate_sample_bills(1)
        bill = bills[0]

        assert 'billId' in bill
        assert 'type' in bill
        assert 'number' in bill
        assert 'sponsor' in bill
        assert 'introducedDate' in bill

        assert 'bioguideId' in bill['sponsor']

        members = APIResponseBuilder.generate_sample_members(1)
        member = members[0]

        assert 'bioguideId' in member
        assert 'fullName' in member
        assert 'state' in member
        assert 'party' in member

    @pytest.mark.unit
    def test_api_helper_mock_setup(self):
        """Test API helper mock setup"""
        helper = get_api_helper()

        mock_data = {'test': 'data'}
        helper.setup_mock_response('https://test.com/api', mock_data)

        response = helper.get_mock_response('https://test.com/api')

        assert response is not None
        assert response.json_data == mock_data
        assert response.status_code == 200

class TestAPIErrorHandling:
    """Test API error handling and recovery"""

    @pytest.mark.unit
    def test_http_error_responses(self):
        """Test handling of HTTP error responses"""
        error_responses = {
            401: {'error': 'Unauthorized'},
            403: {'error': 'Forbidden'},
            404: {'error': 'Not Found'},
            429: {'error': 'Rate Limit Exceeded'},
            500: {'error': 'Internal Server Error'},
            503: {'error': 'Service Unavailable'}
        }

        for status_code, error_data in error_responses.items():
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.json.return_value = error_data

            with patch('requests.get') as mock_get:
                mock_get.return_value = mock_response

                response = requests.get('https://api.congress.gov/v3/test')

                assert response.status_code == status_code

                if status_code >= 400:
                    with pytest.raises(requests.exceptions.HTTPError):
                        response.raise_for_status()

    @pytest.mark.unit
    def test_network_timeout_handling(self):
        """Test network timeout handling"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

            with pytest.raises(requests.exceptions.Timeout):
                requests.get('https://api.congress.gov/v3/test', timeout=5)

    @pytest.mark.unit
    def test_connection_error_handling(self):
        """Test connection error handling"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            with pytest.raises(requests.exceptions.ConnectionError):
                requests.get('https://api.congress.gov/v3/test')

    @pytest.mark.unit
    def test_adaptive_rate_limiter_error_handling(self, adaptive_limiter):
        """Test adaptive rate limiter error handling"""
        for i in range(5):
            adaptive_limiter.handle_error(429)

        assert adaptive_limiter.consecutive_errors == 2

        assert adaptive_limiter.current_rate < 1.0

        adaptive_limiter.handle_error(200)
        assert adaptive_limiter.consecutive_errors == 0
