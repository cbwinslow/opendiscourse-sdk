"""
OpenStates API client implementation.

This module provides a Python client for interacting with the OpenStates API (v3).
It handles state-level legislative data using GraphQL.

Example:
    >>> from opendiscourse_sdk import OpenStatesClient
    >>> client = OpenStatesClient(api_key="your_key")
    >>> 
    >>> # Get legislators from a state
    >>> legislators = client.legislators.list(jurisdiction="ny")
    >>> for leg in legislators.results:
    ...     print(f"{leg.name} ({leg.party})")

Author: OpenDiscourse Team
License: MIT
"""

import os
from typing import Optional

from opendiscourse_sdk.base import BaseClient
from opendiscourse_sdk.enums import StateCode
from opendiscourse_sdk.models.openstates import (
    BillListResponse,
    Legislator,
    LegislatorListResponse,
    StateBill,
)


class LegislatorsResource:
    """
    Resource handler for legislator operations.
    
    Provides methods to interact with state legislators.
    
    Attributes:
        client: Parent OpenStatesClient instance
    """
    
    def __init__(self, client: "OpenStatesClient") -> None:
        """
        Initialize the legislators resource.
        
        Args:
            client: Parent OpenStatesClient instance
        """
        self.client = client
    
    def list(
        self,
        jurisdiction: StateCode,
        session: Optional[str] = None,
        per_page: int = 50,
    ) -> LegislatorListResponse:
        """
        List legislators from a state.
        
        Args:
            jurisdiction: State code (e.g., "ny", "ca")
            session: Optional legislative session filter
            per_page: Results per page (max: 100)
        
        Returns:
            LegislatorListResponse with list of legislators
        
        Example:
            >>> legislators = client.legislators.list(
            ...     jurisdiction="ny",
            ...     session="2023-2024"
            ... )
        """
        params = {
            "jurisdiction": jurisdiction.value if isinstance(jurisdiction, StateCode) else jurisdiction,
            "per_page": min(per_page, 100),
        }
        
        if session:
            params["session"] = session
        
        endpoint = "/legislators"
        response_data = self.client.get(endpoint, params=params)
        return self.client.validate_response(response_data, LegislatorListResponse)


class BillsResource:
    """
    Resource handler for bill operations.
    
    Provides methods to interact with state bills.
    
    Attributes:
        client: Parent OpenStatesClient instance
    """
    
    def __init__(self, client: "OpenStatesClient") -> None:
        """
        Initialize the bills resource.
        
        Args:
            client: Parent OpenStatesClient instance
        """
        self.client = client
    
    def list(
        self,
        jurisdiction: StateCode,
        session: Optional[str] = None,
        per_page: int = 50,
    ) -> BillListResponse:
        """
        List bills from a state.
        
        Args:
            jurisdiction: State code (e.g., "ny", "ca")
            session: Optional legislative session filter
            per_page: Results per page (max: 100)
        
        Returns:
            BillListResponse with list of bills
        
        Example:
            >>> bills = client.bills.list(
            ...     jurisdiction="ny",
            ...     session="2023-2024"
            ... )
        """
        params = {
            "jurisdiction": jurisdiction.value if isinstance(jurisdiction, StateCode) else jurisdiction,
            "per_page": min(per_page, 100),
        }
        
        if session:
            params["session"] = session
        
        endpoint = "/bills"
        response_data = self.client.get(endpoint, params=params)
        return self.client.validate_response(response_data, BillListResponse)


class OpenStatesClient(BaseClient):
    """
    Main client for OpenStates API (v3).
    
    Provides access to state-level legislative data for all 50 states
    plus DC and US territories.
    
    The client uses resource-based organization:
    - client.legislators: Legislator operations
    - client.bills: Bill operations
    
    Attributes:
        legislators: LegislatorsResource for legislator operations
        bills: BillsResource for bill operations
    
    Example:
        >>> from opendiscourse_sdk import OpenStatesClient
        >>> 
        >>> # Initialize client
        >>> client = OpenStatesClient(api_key="your_key")
        >>> 
        >>> # Get legislators from New York
        >>> legislators = client.legislators.list(jurisdiction="ny")
        >>> 
        >>> # Get recent bills from California
        >>> bills = client.bills.list(jurisdiction="ca", session="2023-2024")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        rate_limit_delay: float = 0.6,  # OpenStates: 100 req/min = 0.6s delay
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the OpenStates API client.
        
        Args:
            api_key: OpenStates API key (or set OPENSTATES_API_KEY env var)
            timeout: Request timeout in seconds (default: 30)
            rate_limit_delay: Delay between requests (default: 0.6s for 100/min limit)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        # Get API key from parameter or environment
        api_key = api_key or os.getenv("OPENSTATES_API_KEY")
        
        # Initialize base client
        super().__init__(
            base_url="https://v3.openstates.org",
            api_key=api_key,
            timeout=timeout,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
        )
        
        # Initialize resources
        self.legislators = LegislatorsResource(self)
        self.bills = BillsResource(self)
    
    def _prepare_params(self, params: Optional[dict] = None) -> dict:
        """
        Prepare request parameters for OpenStates API.
        
        OpenStates uses 'apikey' parameter (not 'api_key').
        """
        prepared_params = params.copy() if params else {}
        
        # Add API key if configured
        if self.api_key:
            prepared_params["apikey"] = self.api_key
        
        # Remove None values
        prepared_params = {k: v for k, v in prepared_params.items() if v is not None}
        
        return prepared_params
