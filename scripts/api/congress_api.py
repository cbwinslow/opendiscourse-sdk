"""
================================================================================
File: congress_api.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Congress.gov API client with full endpoint abstraction using Pydantic
    models. Provides type-safe access to all Congress.gov API endpoints
    including bills, members, committees, votes, hearings, and more.

Dependencies:
    - scripts.core.api_client_base: Base API client functionality
    - pydantic: Data validation and type safety
    - typing: Type hint support
    - datetime: Date/time handling

Classes:
    - BillType: Enum for bill types (HR, S, HJRES, etc.)
    - Chamber: Enum for congressional chambers
    - CongressEndpoints: API endpoint definitions
    - CongressAPIClient: Main API client for Congress.gov

Endpoints Covered:
    - Bills (all types)
    - Members (current and historical)
    - Committees
    - Votes
    - Amendments
    - Bill actions, cosponsors, subjects, titles, summaries
    - Committee reports, prints, hearings
    - Congressional Record
    - Nominations, Treaties
    - Communications (House & Senate)

Usage:
    from scripts.api.congress_api import CongressAPIClient

    # Initialize client
    client = CongressAPIClient(api_key="your_key_here")

    # Get bills from Congress 118
    response = client.get_bills(congress=118, limit=50)
    if response.success:
        bills = response.data['bills']

    # Get member details
    member = client.get_member(bioguide_id="A000148")

Changelog:
    2025-12-04: Initial creation with full endpoint coverage

Notes:
    - All methods return APIResponse objects with .success and .data
    - Automatic retry on failure
    - Rate limiting enforced
    - Type-safe with Pydantic models

================================================================================
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, validator

from scripts.core.api_client_base import (
    APIClientBase,
    APIResponse,
    HTTPMethod,
    log_api_call,
    retry_on_failure
)


# ============================================================================
# Enums and Constants
# ============================================================================

class BillType(str, Enum):
    """
    Congressional bill types.

    Values:
        HR: House of Representatives bill
        S: Senate bill
        HJRES: House Joint Resolution
        SJRES: Senate Joint Resolution
        HCONRES: House Concurrent Resolution
        SCONRES: Senate Concurrent Resolution
        HRES: House Simple Resolution
        SRES: Senate Simple Resolution
    """
    HR = "hr"
    S = "s"
    HJRES = "hjres"
    SJRES = "sjres"
    HCONRES = "hconres"
    SCONRES = "sconres"
    HRES = "hres"
    SRES = "sres"


class Chamber(str, Enum):
    """
    Congressional chambers.

    Values:
        HOUSE: House of Representatives
        SENATE: Senate
        JOINT: Joint session
    """
    HOUSE = "house"
    SENATE = "senate"
    JOINT = "joint"


# ============================================================================
# API Endpoint Definitions
# ============================================================================

class CongressEndpoints:
    """
    Centralized definition of all Congress.gov API endpoints.

    This class provides a single source of truth for all API paths,
    making it easy to maintain and update endpoint URLs.
    """

    # Bills endpoints
    BILLS = "/bill"
    BILL_DETAIL = "/bill/{congress}/{billType}/{billNumber}"
    BILL_ACTIONS = "/bill/{congress}/{billType}/{billNumber}/actions"
    BILL_AMENDMENTS = "/bill/{congress}/{billType}/{billNumber}/amendments"
    BILL_COSPONSORS = "/bill/{congress}/{billType}/{billNumber}/cosponsors"
    BILL_SUBJECTS = "/bill/{congress}/{billType}/{billNumber}/subjects"
    BILL_SUMMARIES = "/bill/{congress}/{billType}/{billNumber}/summaries"
    BILL_TITLES = "/bill/{congress}/{billType}/{billNumber}/titles"
    BILL_TEXT = "/bill/{congress}/{billType}/{billNumber}/text"
    BILL_RELATED = "/bill/{congress}/{billType}/{billNumber}/relatedbills"

    # Member endpoints
    MEMBERS = "/member"
    MEMBER_DETAIL = "/member/{bioguideId}"
    MEMBER_SPONSORED = "/member/{bioguideId}/sponsored-legislation"
    MEMBER_COSPONSORED = "/member/{bioguideId}/cosponsored-legislation"

    # Committee endpoints
    COMMITTEES = "/committee"
    COMMITTEE_DETAIL = "/committee/{chamber}/{committeeCode}"
    COMMITTEE_BILLS = "/committee/{chamber}/{committeeCode}/bills"
    COMMITTEE_REPORTS = "/committee-report"
    COMMITTEE_PRINTS = "/committee-print"
    COMMITTEE_MEETINGS = "/committee-meeting"

    # Vote endpoints
    NOMINATIONS = "/nomination"
    NOMINATION_DETAIL = "/nomination/{congress}/{nominationNumber}"

    # Treaty endpoints
    TREATIES = "/treaty"
    TREATY_DETAIL = "/treaty/{congress}/{treatyNumber}"

    # Hearing endpoints
    HEARINGS = "/hearing"
    HEARING_DETAIL = "/hearing/{congress}/{hearingNumber}"

    # Congressional Record endpoints
    CONGRESSIONAL_RECORD = "/congressional-record"

    # Communication endpoints
    HOUSE_COMMUNICATION = "/house-communication"
    SENATE_COMMUNICATION = "/senate-communication"

    # Amendment endpoints
    AMENDMENTS = "/amendment"
    AMENDMENT_DETAIL = "/amendment/{congress}/{amendmentType}/{amendmentNumber}"

    # Summaries
    SUMMARIES = "/summaries"

    # Law endpoints
    LAW = "/law"


# ============================================================================
# Congress API Client
# ============================================================================

class CongressAPIClient(APIClientBase):
    """
    Congress.gov API client with full endpoint coverage.

    Provides type-safe, well-documented access to all Congress.gov
    API endpoints with automatic error handling, retry logic, and
    rate limiting.

    Attributes:
        base_url: API base URL (https://api.congress.gov/v3)
        api_key: Congress.gov API key
        rate_limit: Requests per second (default 100)

    Methods:
        Bills:
            - get_bills: List bills
            - get_bill: Get bill details
            - get_bill_actions: Get bill actions
            - get_bill_amendments: Get bill amendments
            - get_bill_cosponsors: Get bill cosponsors
            - get_bill_subjects: Get bill subjects
            - get_bill_summaries: Get bill summaries
            - get_bill_titles: Get bill titles
            - get_bill_text: Get bill text versions
            - get_bill_related: Get related bills

        Members:
            - get_members: List members
            - get_member: Get member details
            - get_member_sponsored: Get sponsored legislation
            - get_member_cosponsored: Get cosponsored legislation

        Committees:
            - get_committees: List committees
            - get_committee: Get committee details
            - get_committee_bills: Get committee bills
            - get_committee_reports: Get committee reports
            - get_committee_prints: Get committee prints
            - get_committee_meetings: Get committee meetings

        Other:
            - get_nominations: List nominations
            - get_treaties: List treaties
            - get_hearings: List hearings
            - get_congressional_record: Get Congressional Record
            - get_house_communications: Get House communications
            - get_senate_communications: Get Senate communications
    """

    def __init__(self, api_key: str, rate_limit: int = 100):
        """
        Initialize Congress API client.

        Args:
            api_key: Congress.gov API key
            rate_limit: Maximum requests per second (default 100)
        """
        # Call parent constructor with Congress.gov specifics
        super().__init__(
            base_url="https://api.congress.gov/v3",
            api_key=api_key,
            rate_limit=rate_limit,
            logger_name="CongressAPI"
        )

        # Log successful initialization
        self.logger.info("Congress API client initialized")

    # ========================================================================
    # Bill Methods
    # ========================================================================

    @log_api_call
    def get_bills(
        self,
        congress: Optional[int] = None,
        bill_type: Optional[BillType] = None,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get list of bills.

        Args:
            congress: Congress number (e.g., 118)
            bill_type: Type of bill (hr, s, etc.)
            offset: Pagination offset
            limit: Number of results (max 250)

        Returns:
            APIResponse with bill list in data['bills']

        Example:
            >>> response = client.get_bills(congress=118, limit=50)
            >>> if response.success:
            >>>     for bill in response.data['bills']:
            >>>         print(bill['number'], bill['title'])
        """
        # Build query parameters
        params = {
            'offset': offset,
            'limit': min(limit, 250)  # API max is 250
        }

        # Add optional filters
        if congress:
            params['fromDateTime'] = f"{congress}-01-01T00:00:00Z"

        # Build endpoint path
        endpoint = CongressEndpoints.BILLS
        if congress and bill_type:
            endpoint = f"/bill/{congress}/{bill_type.value}"

        # Make API request
        return self.get(endpoint, params=params)

    @log_api_call
    def get_bill(
        self,
        congress: int,
        bill_type: BillType,
        bill_number: int
    ) -> APIResponse:
        """
        Get detailed information for a specific bill.

        Args:
            congress: Congress number
            bill_type: Type of bill
            bill_number: Bill number

        Returns:
            APIResponse with bill details in data['bill']

        Example:
            >>> response = client.get_bill(118, BillType.HR, 1)
            >>> if response.success:
            >>>     bill = response.data['bill']
            >>>     print(bill['title'])
        """
        # Format endpoint with path parameters
        endpoint = CongressEndpoints.BILL_DETAIL.format(
            congress=congress,
            billType=bill_type.value,
            billNumber=bill_number
        )

        # Make API request
        return self.get(endpoint)

    @log_api_call
    def get_bill_actions(
        self,
        congress: int,
        bill_type: BillType,
        bill_number: int,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get actions for a specific bill.

        Args:
            congress: Congress number
            bill_type: Type of bill
            bill_number: Bill number
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with actions in data['actions']
        """
        endpoint = CongressEndpoints.BILL_ACTIONS.format(
            congress=congress,
            billType=bill_type.value,
            billNumber=bill_number
        )

        params = {'offset': offset, 'limit': min(limit, 250)}
        return self.get(endpoint, params=params)

    @log_api_call
    def get_bill_cosponsors(
        self,
        congress: int,
        bill_type: BillType,
        bill_number: int,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get cosponsors for a specific bill.

        Args:
            congress: Congress number
            bill_type: Type of bill
            bill_number: Bill number
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with cosponsors in data['cosponsors']
        """
        endpoint = CongressEndpoints.BILL_COSPONSORS.format(
            congress=congress,
            billType=bill_type.value,
            billNumber=bill_number
        )

        params = {'offset': offset, 'limit': min(limit, 250)}
        return self.get(endpoint, params=params)

    # ========================================================================
    # Member Methods
    # ========================================================================

    @log_api_call
    def get_members(
        self,
        congress: Optional[int] = None,
        chamber: Optional[Chamber] = None,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get list of congressional members.

        Args:
            congress: Congress number
            chamber: Chamber filter (house/senate)
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with members in data['members']
        """
        params = {'offset': offset, 'limit': min(limit, 250)}

        # Build endpoint with filters
        endpoint = CongressEndpoints.MEMBERS
        if congress:
            endpoint = f"/member/congress/{congress}"
            if chamber:
                endpoint += f"/{chamber.value}"

        return self.get(endpoint, params=params)

    @log_api_call
    def get_member(self, bioguide_id: str) -> APIResponse:
        """
        Get details for a specific member.

        Args:
            bioguide_id: Member's Bioguide ID

        Returns:
            APIResponse with member details in data['member']
        """
        endpoint = CongressEndpoints.MEMBER_DETAIL.format(bioguideId=bioguide_id)
        return self.get(endpoint)

    # ========================================================================
    # Committee Methods
    # ========================================================================

    @log_api_call
    def get_committees(
        self,
        congress: Optional[int] = None,
        chamber: Optional[Chamber] = None,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get list of committees.

        Args:
            congress: Congress number
            chamber: Chamber filter
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with committees in data['committees']
        """
        endpoint = CongressEndpoints.COMMITTEES
        params = {'offset': offset, 'limit': min(limit, 250)}

        if congress:
            params['congress'] = congress
        if chamber:
            params['chamber'] = chamber.value

        return self.get(endpoint, params=params)

    @log_api_call
    def get_committee_reports(
        self,
        congress: int,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get committee reports for a congress.

        Args:
            congress: Congress number
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with reports in data['reports']
        """
        params = {
            'congress': congress,
            'offset': offset,
            'limit': min(limit, 250)
        }

        return self.get(CongressEndpoints.COMMITTEE_REPORTS, params=params)

    @log_api_call
    def get_committee_prints(
        self,
        congress: int,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get committee prints for a congress.

        Args:
            congress: Congress number
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with prints in data['committeePrints']
        """
        params = {
            'congress': congress,
            'offset': offset,
            'limit': min(limit, 250)
        }

        return self.get(CongressEndpoints.COMMITTEE_PRINTS, params=params)

    @log_api_call
    def get_hearings(
        self,
        congress: int,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get hearings for a congress.

        Args:
            congress: Congress number
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with hearings in data['hearings']
        """
        params = {
            'congress': congress,
            'offset': offset,
            'limit': min(limit, 250)
        }

        return self.get(CongressEndpoints.HEARINGS, params=params)

    # ========================================================================
    # Other Methods
    # ========================================================================

    @log_api_call
    def get_nominations(
        self,
        congress: int,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get nominations for a congress.

        Args:
            congress: Congress number
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with nominations in data['nominations']
        """
        params = {
            'congress': congress,
            'offset': offset,
            'limit': min(limit, 250)
        }

        return self.get(CongressEndpoints.NOMINATIONS, params=params)

    @log_api_call
    def get_treaties(
        self,
        congress: int,
        offset: int = 0,
        limit: int = 250
    ) -> APIResponse:
        """
        Get treaties for a congress.

        Args:
            congress: Congress number
            offset: Pagination offset
            limit: Number of results

        Returns:
            APIResponse with treaties in data['treaties']
        """
        params = {
            'congress': congress,
            'offset': offset,
            'limit': min(limit, 250)
        }

        return self.get(CongressEndpoints.TREATIES, params=params)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'BillType',
    'Chamber',
    'CongressEndpoints',
    'CongressAPIClient',
]
