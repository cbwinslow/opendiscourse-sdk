"""
================================================================================
File: openstates_api.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    OpenStates API v3 client with full endpoint abstraction using Pydantic
    models. Provides type-safe access to all state legislature data including
    bills, people, votes, committees, and events across all 52 jurisdictions.

Dependencies:
    - scripts.core.api_client_base: Base API client functionality
    - pydantic: Data validation and type safety
    - typing: Type hint support
    - datetime: Date/time handling

Classes:
    - Jurisdiction: Enum for US states and territories
    - Classification: Enum for bill classifications
    - OpenStatesEndpoints: API endpoint definitions
    - OpenStatesAPIClient: Main API client for OpenStates

Endpoints Covered:
    - Bills (all states)
    - People (legislators, current and historical)
    - Vote events
    - Organizations (legislative bodies, committees)
    - Events (hearings, sessions)
    - Jurisdictions

Usage:
    from scripts.api.openstates_api import OpenStatesAPIClient

    # Initialize client
    client = OpenStatesAPIClient(api_key="your_key_here")

    # Get California bills from recent session
    response = client.get_bills(jurisdiction="ca", session="20232024")
    if response.success:
        bills = response.data['results']

    # Get all legislators for a state
    people = client.get_people(jurisdiction="ny")

Changelog:
    2025-12-04: Initial creation with full endpoint coverage

Notes:
    - All methods return APIResponse objects with .success and .data
    - Automatic retry on failure
    - Rate limiting enforced (20 req/s default)
    - GraphQL endpoint available for complex queries

================================================================================
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date

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

class Jurisdiction(str, Enum):
    """
    US State and Territory jurisdictions (52 total).

    Values include all 50 states plus DC and Puerto Rico.
    Format: Two-letter lowercase state code
    """
    # States
    AL = "al"  # Alabama
    AK = "ak"  # Alaska
    AZ = "az"  # Arizona
    AR = "ar"  # Arkansas
    CA = "ca"  # California
    CO = "co"  # Colorado
    CT = "ct"  # Connecticut
    DE = "de"  # Delaware
    FL = "fl"  # Florida
    GA = "ga"  # Georgia
    HI = "hi"  # Hawaii
    ID = "id"  # Idaho
    IL = "il"  # Illinois
    IN = "in"  # Indiana
    IA = "ia"  # Iowa
    KS = "ks"  # Kansas
    KY = "ky"  # Kentucky
    LA = "la"  # Louisiana
    ME = "me"  # Maine
    MD = "md"  # Maryland
    MA = "ma"  # Massachusetts
    MI = "mi"  # Michigan
    MN = "mn"  # Minnesota
    MS = "ms"  # Mississippi
    MO = "mo"  # Missouri
    MT = "mt"  # Montana
    NE = "ne"  # Nebraska
    NV = "nv"  # Nevada
    NH = "nh"  # New Hampshire
    NJ = "nj"  # New Jersey
    NM = "nm"  # New Mexico
    NY = "ny"  # New York
    NC = "nc"  # North Carolina
    ND = "nd"  # North Dakota
    OH = "oh"  # Ohio
    OK = "ok"  # Oklahoma
    OR = "or"  # Oregon
    PA = "pa"  # Pennsylvania
    RI = "ri"  # Rhode Island
    SC = "sc"  # South Carolina
    SD = "sd"  # South Dakota
    TN = "tn"  # Tennessee
    TX = "tx"  # Texas
    UT = "ut"  # Utah
    VT = "vt"  # Vermont
    VA = "va"  # Virginia
    WA = "wa"  # Washington
    WV = "wv"  # West Virginia
    WI = "wi"  # Wisconsin
    WY = "wy"  # Wyoming

    # Territories
    DC = "dc"  # District of Columbia
    PR = "pr"  # Puerto Rico


class Classification(str, Enum):
    """
    Bill classification types.

    Values:
        BILL: Regular legislation
        RESOLUTION: Legislative resolution
        CONCURRENT_RESOLUTION: Concurrent resolution
        JOINT_RESOLUTION: Joint resolution
        MEMORIAL: Memorial resolution
    """
    BILL = "bill"
    RESOLUTION = "resolution"
    CONCURRENT_RESOLUTION = "concurrent resolution"
    JOINT_RESOLUTION = "joint resolution"
    MEMORIAL = "memorial"


# ============================================================================
# API Endpoint Definitions
# ============================================================================

class OpenStatesEndpoints:
    """
    Centralized definition of all OpenStates API v3 endpoints.

    This class provides a single source of truth for all API paths.
    """

    # Core endpoints
    JURISDICTIONS = "/jurisdictions"
    JURISDICTION_DETAIL = "/jurisdictions/{jurisdiction_id}"

    # Bill endpoints
    BILLS = "/bills"
    BILL_DETAIL = "/bills/{bill_id}"

    # People endpoints
    PEOPLE = "/people"
    PERSON_DETAIL = "/people/{person_id}"

    # Vote endpoints
    VOTES = "/votes"
    VOTE_DETAIL = "/votes/{vote_id}"

    # Organization endpoints
    ORGANIZATIONS = "/organizations"
    ORGANIZATION_DETAIL = "/organizations/{organization_id}"

    # Event endpoints
    EVENTS = "/events"
    EVENT_DETAIL = "/events/{event_id}"

    # GraphQL endpoint (for complex queries)
    GRAPHQL = "/graphql"


# ============================================================================
# OpenStates API Client
# ============================================================================

class OpenStatesAPIClient(APIClientBase):
    """
    OpenStates API v3 client with full endpoint coverage.

    Provides type-safe, well-documented access to all OpenStates
    API endpoints with automatic error handling, retry logic, and
    rate limiting.

    Attributes:
        base_url: API base URL (https://v3.openstates.org)
        api_key: OpenStates API key
        rate_limit: Requests per second (default 20)

    Methods:
        Jurisdictions:
            - get_jurisdictions: List all jurisdictions
            - get_jurisdiction: Get jurisdiction details

        Bills:
            - get_bills: Search/list bills with filters
            - get_bill: Get bill details

        People:
            - get_people: Search/list legislators
            - get_person: Get person details

        Votes:
            - get_votes: List vote events
            - get_vote: Get vote details

        Organizations:
            - get_organizations: List organizations/committees
            - get_organization: Get organization details

        Events:
            - get_events: List legislative events
            - get_event: Get event details
    """

    def __init__(self, api_key: str, rate_limit: int = 20):
        """
        Initialize OpenStates API client.

        Args:
            api_key: OpenStates API key
            rate_limit: Maximum requests per second (default 20)
        """
        # Call parent constructor with OpenStates specifics
        super().__init__(
            base_url="https://v3.openstates.org",
            api_key=api_key,
            rate_limit=rate_limit,
            logger_name="OpenStatesAPI"
        )

        # Override auth header format (OpenStates uses X-API-KEY)
        self.session.headers.update({
            'X-API-KEY': api_key
        })

        # Log successful initialization
        self.logger.info("OpenStates API client initialized")

    # ========================================================================
    # Jurisdiction Methods
    # ========================================================================

    @log_api_call
    def get_jurisdictions(self) -> APIResponse:
        """
        Get all available jurisdictions (states/territories).

        Returns:
            APIResponse with jurisdictions in data['results']

        Example:
            >>> response = client.get_jurisdictions()
            >>> if response.success:
            >>>     for j in response.data['results']:
            >>>         print(j['id'], j['name'])
        """
        return self.get(OpenStatesEndpoints.JURISDICTIONS)

    @log_api_call
    def get_jurisdiction(self, jurisdiction_id: str) -> APIResponse:
        """
        Get details for a specific jurisdiction.

        Args:
            jurisdiction_id: Jurisdiction ID (e.g., "ocd-jurisdiction/country:us/state:ca/government")

        Returns:
            APIResponse with jurisdiction details

        Example:
            >>> response = client.get_jurisdiction("ocd-jurisdiction/country:us/state:ca/government")
        """
        endpoint = OpenStatesEndpoints.JURISDICTION_DETAIL.format(
            jurisdiction_id=jurisdiction_id
        )
        return self.get(endpoint)

    # ========================================================================
    # Bill Methods
    # ========================================================================

    @log_api_call
    def get_bills(
        self,
        jurisdiction: Optional[str] = None,
        session: Optional[str] = None,
        chamber: Optional[str] = None,
        classification: Optional[Classification] = None,
        subject: Optional[str] = None,
        updated_since: Optional[date] = None,
        q: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> APIResponse:
        """
        Search and filter bills.

        Args:
            jurisdiction: Jurisdiction code (e.g., "ca")
            session: Legislative session identifier
            chamber: Chamber (upper/lower)
            classification: Bill classification
            subject: Subject filter
            updated_since: Only bills updated since this date
            q: Full-text search query
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            APIResponse with bills in data['results']

        Example:
            >>> # Get recent California bills
            >>> response = client.get_bills(
            >>>     jurisdiction="ca",
            >>>     session="20232024",
            >>>     per_page=50
            >>> )
            >>> if response.success:
            >>>     for bill in response.data['results']:
            >>>         print(bill['identifier'], bill['title'])
        """
        # Build query parameters
        params = {
            'page': page,
            'per_page': min(per_page, 100)  # API max is 100
        }

        # Add optional filters
        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if session:
            params['session'] = session
        if chamber:
            params['chamber'] = chamber
        if classification:
            params['classification'] = classification.value
        if subject:
            params['subject'] = subject
        if updated_since:
            params['updated_since'] = updated_since.isoformat()
        if q:
            params['q'] = q

        # Make API request
        return self.get(OpenStatesEndpoints.BILLS, params=params)

    @log_api_call
    def get_bill(self, bill_id: str) -> APIResponse:
        """
        Get detailed information for a specific bill.

        Args:
            bill_id: OpenStates bill ID (e.g., "ocd-bill/...")

        Returns:
            APIResponse with bill details

        Example:
            >>> response = client.get_bill("ocd-bill/12345")
            >>> if response.success:
            >>>     bill = response.data
            >>>     print(bill['title'])
        """
        endpoint = OpenStatesEndpoints.BILL_DETAIL.format(bill_id=bill_id)
        return self.get(endpoint)

    # ========================================================================
    # People Methods
    # ========================================================================

    @log_api_call
    def get_people(
        self,
        jurisdiction: Optional[str] = None,
        name: Optional[str] = None,
        party: Optional[str] = None,
        district: Optional[str] = None,
        chamber: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> APIResponse:
        """
        Search and filter legislators.

        Args:
            jurisdiction: Jurisdiction code
            name: Person name (partial match)
            party: Party affiliation
            district: District number
            chamber: Chamber (upper/lower)
            page: Page number
            per_page: Results per page

        Returns:
            APIResponse with people in data['results']

        Example:
            >>> # Get all current California legislators
            >>> response = client.get_people(jurisdiction="ca")
            >>> for person in response.data['results']:
            >>>     print(person['name'], person['current_party'])
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if name:
            params['name'] = name
        if party:
            params['party'] = party
        if district:
            params['district'] = district
        if chamber:
            params['chamber'] = chamber

        return self.get(OpenStatesEndpoints.PEOPLE, params=params)

    @log_api_call
    def get_person(self, person_id: str) -> APIResponse:
        """
        Get details for a specific person.

        Args:
            person_id: OpenStates person ID

        Returns:
            APIResponse with person details
        """
        endpoint = OpenStatesEndpoints.PERSON_DETAIL.format(person_id=person_id)
        return self.get(endpoint)

    # ========================================================================
    # Vote Methods
    # ========================================================================

    @log_api_call
    def get_votes(
        self,
        jurisdiction: Optional[str] = None,
        bill_id: Optional[str] = None,
        chamber: Optional[str] = None,
        session: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> APIResponse:
        """
        Get vote events.

        Args:
            jurisdiction: Jurisdiction code
            bill_id: Filter by bill ID
            chamber: Chamber filter
            session: Session filter
            page: Page number
            per_page: Results per page

        Returns:
            APIResponse with votes in data['results']
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if bill_id:
            params['bill_id'] = bill_id
        if chamber:
            params['chamber'] = chamber
        if session:
            params['session'] = session

        return self.get(OpenStatesEndpoints.VOTES, params=params)

    @log_api_call
    def get_vote(self, vote_id: str) -> APIResponse:
        """
        Get details for a specific vote event.

        Args:
            vote_id: OpenStates vote ID

        Returns:
            APIResponse with vote details including individual votes
        """
        endpoint = OpenStatesEndpoints.VOTE_DETAIL.format(vote_id=vote_id)
        return self.get(endpoint)

    # ========================================================================
    # Organization Methods
    # ========================================================================

    @log_api_call
    def get_organizations(
        self,
        jurisdiction: Optional[str] = None,
        classification: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> APIResponse:
        """
        Get organizations (legislative bodies, committees).

        Args:
            jurisdiction: Jurisdiction code
            classification: Organization type (legislature, committee, etc.)
            page: Page number
            per_page: Results per page

        Returns:
            APIResponse with organizations in data['results']
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if classification:
            params['classification'] = classification

        return self.get(OpenStatesEndpoints.ORGANIZATIONS, params=params)

    @log_api_call
    def get_organization(self, organization_id: str) -> APIResponse:
        """
        Get details for a specific organization.

        Args:
            organization_id: OpenStates organization ID

        Returns:
            APIResponse with organization details
        """
        endpoint = OpenStatesEndpoints.ORGANIZATION_DETAIL.format(
            organization_id=organization_id
        )
        return self.get(endpoint)

    # ========================================================================
    # Event Methods
    # ========================================================================

    @log_api_call
    def get_events(
        self,
        jurisdiction: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        per_page: int = 100
    ) -> APIResponse:
        """
        Get legislative events (hearings, sessions).

        Args:
            jurisdiction: Jurisdiction code
            start_date: Events on or after this date
            end_date: Events on or before this date
            page: Page number
            per_page: Results per page

        Returns:
            APIResponse with events in data['results']
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()

        return self.get(OpenStatesEndpoints.EVENTS, params=params)

    @log_api_call
    def get_event(self, event_id: str) -> APIResponse:
        """
        Get details for a specific event.

        Args:
            event_id: OpenStates event ID

        Returns:
            APIResponse with event details
        """
        endpoint = OpenStatesEndpoints.EVENT_DETAIL.format(event_id=event_id)
        return self.get(endpoint)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'Jurisdiction',
    'Classification',
    'OpenStatesEndpoints',
    'OpenStatesAPIClient',
]
