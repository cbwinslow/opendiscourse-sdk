"""
Basic tests for the OpenDiscourse SDK.

These tests verify that the SDK can be imported and basic functionality works.
They don't require API keys and test the structure and validation.

Author: OpenDiscourse Team
License: MIT
"""

from datetime import date

import pytest


# Test imports
def test_imports():
    """Test that all main components can be imported."""
    from opendiscourse_sdk import (
        CongressClient,
        GovInfoClient,
        OpenStatesClient,
    )

    # All imports successful
    assert CongressClient is not None
    assert GovInfoClient is not None
    assert OpenStatesClient is not None


def test_exception_hierarchy():
    """Test that exception hierarchy is correct."""
    from opendiscourse_sdk.exceptions import (
        APIError,
        AuthenticationError,
        NotFoundError,
        OpenDiscourseSDKError,
        RateLimitError,
        ValidationError,
    )

    # Test inheritance
    assert issubclass(APIError, OpenDiscourseSDKError)
    assert issubclass(AuthenticationError, APIError)
    assert issubclass(RateLimitError, APIError)
    assert issubclass(NotFoundError, APIError)
    assert issubclass(ValidationError, OpenDiscourseSDKError)

    # Test exception creation
    error = OpenDiscourseSDKError("Test error", details={"key": "value"})
    assert str(error) == "Test error - Details: {'key': 'value'}"

    api_error = APIError("API failed", status_code=500)
    assert "HTTP 500" in str(api_error)

    rate_error = RateLimitError(retry_after=60)
    assert "60 seconds" in str(rate_error)


def test_enums():
    """Test that enumerations work correctly."""
    from opendiscourse_sdk.enums import (
        BillType,
        Chamber,
        GovInfoCollection,
        StateCode,
    )

    # Test bill types
    assert BillType.HOUSE_BILL.value == "hr"
    assert BillType.SENATE_BILL.value == "s"

    # Test chambers
    assert Chamber.HOUSE.value == "house"
    assert Chamber.SENATE.value == "senate"

    # Test collections
    assert GovInfoCollection.BILLS.value == "BILLS"
    assert GovInfoCollection.FEDERAL_REGISTER.value == "FR"

    # Test state codes
    assert StateCode.CALIFORNIA.value == "ca"
    assert StateCode.NEW_YORK.value == "ny"


def test_pydantic_models():
    """Test that Pydantic models validate correctly."""
    from opendiscourse_sdk.enums import BillType, Chamber
    from opendiscourse_sdk.models.congress import Bill, BillSummary

    # Test BillSummary creation
    bill_summary = BillSummary(
        number=1,
        type=BillType.HOUSE_BILL,
        congress=118,
        title="Test Bill",
    )
    assert bill_summary.number == 1
    assert bill_summary.type == BillType.HOUSE_BILL
    assert bill_summary.congress == 118

    # Test Bill creation
    bill = Bill(
        number=1,
        type=BillType.HOUSE_BILL,
        congress=118,
        title="Test Bill",
        origin_chamber=Chamber.HOUSE,
        introduced_date=date(2024, 1, 1),
    )
    assert bill.number == 1
    assert bill.origin_chamber == Chamber.HOUSE


def test_client_initialization():
    """Test that clients can be initialized without API keys."""
    import os

    from opendiscourse_sdk import CongressClient, GovInfoClient, OpenStatesClient

    # Temporarily clear environment variables
    old_congress_key = os.environ.get("CONGRESS_API_KEY")
    old_govinfo_key = os.environ.get("GOVINFO_API_KEY")
    old_openstates_key = os.environ.get("OPENSTATES_API_KEY")

    try:
        if "CONGRESS_API_KEY" in os.environ:
            del os.environ["CONGRESS_API_KEY"]
        if "GOVINFO_API_KEY" in os.environ:
            del os.environ["GOVINFO_API_KEY"]
        if "OPENSTATES_API_KEY" in os.environ:
            del os.environ["OPENSTATES_API_KEY"]

        # Test initialization without API keys
        congress = CongressClient(api_key="test_key")
        assert congress.api_key == "test_key"
        congress.close()

        govinfo = GovInfoClient(api_key="test_key")
        assert govinfo.api_key == "test_key"
        govinfo.close()

        openstates = OpenStatesClient(api_key="test_key")
        assert openstates.api_key == "test_key"
        openstates.close()

    finally:
        # Restore environment variables
        if old_congress_key:
            os.environ["CONGRESS_API_KEY"] = old_congress_key
        if old_govinfo_key:
            os.environ["GOVINFO_API_KEY"] = old_govinfo_key
        if old_openstates_key:
            os.environ["OPENSTATES_API_KEY"] = old_openstates_key


def test_context_manager():
    """Test that clients work as context managers."""
    from opendiscourse_sdk import CongressClient

    with CongressClient(api_key="test_key") as client:
        assert client is not None
        assert client.session is not None
    # Session should be closed after exiting context


def test_rate_limiting():
    """Test that rate limiting configuration works."""
    import time

    from opendiscourse_sdk import CongressClient

    client = CongressClient(api_key="test_key", rate_limit_delay=0.1)
    assert client.rate_limit_delay == 0.1

    # Test that rate limiting delay is enforced
    start = time.time()
    client._enforce_rate_limit()
    client._last_request_time = time.time()
    client._enforce_rate_limit()
    elapsed = time.time() - start

    # Should have added delay
    assert elapsed >= 0.1

    client.close()


def test_url_building():
    """Test that URLs are built correctly."""
    from opendiscourse_sdk import CongressClient

    client = CongressClient(api_key="test_key")

    # Test URL building
    url = client._build_url("/bill/118/hr/1")
    assert url == "https://api.congress.gov/v3/bill/118/hr/1"

    # Test with leading slash
    url = client._build_url("bill/118/hr/1")
    assert url == "https://api.congress.gov/v3/bill/118/hr/1"

    client.close()


def test_parameter_preparation():
    """Test that request parameters are prepared correctly."""
    from opendiscourse_sdk import CongressClient

    client = CongressClient(api_key="test_key")

    # Test parameter preparation
    params = client._prepare_params({"limit": 10, "offset": 0, "none_value": None})
    assert params["api_key"] == "test_key"
    assert params["limit"] == 10
    assert params["offset"] == 0
    assert "none_value" not in params  # None values should be removed

    client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
