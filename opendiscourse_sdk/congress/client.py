"""
Congress.gov API client implementation.

This module provides a Python client for interacting with the Congress.gov API.
It handles bills, members, committees, votes, and other legislative data.

The client is organized into resource-specific subclients:
- bills: Bill and resolution operations
- members: Member of Congress operations  
- committees: Committee operations
- votes: Vote record operations

Example:
    >>> from opendiscourse_sdk import CongressClient
    >>> client = CongressClient(api_key="your_key")
    >>> 
    >>> # Get a specific bill
    >>> bill = client.bills.get(congress=118, bill_type="hr", number=1)
    >>> print(f"{bill.title}")
    >>> 
    >>> # List recent bills
    >>> bills = client.bills.list(congress=118, limit=10)
    >>> for bill in bills.bills:
    ...     print(f"{bill.type}{bill.number}: {bill.title}")

Author: OpenDiscourse Team
License: MIT
"""

import os
from typing import List, Optional

from opendiscourse_sdk.base import BaseClient
from opendiscourse_sdk.enums import BillType, Chamber, SortOrder
from opendiscourse_sdk.models.congress import (
    Bill,
    BillListResponse,
    Member,
    MemberListResponse,
    Vote,
    VoteListResponse,
)


class BillsResource:
    """
    Resource handler for bill operations.
    
    Provides methods to interact with bills and resolutions from Congress.
    
    Attributes:
        client: Parent CongressClient instance
    """
    
    def __init__(self, client: "CongressClient") -> None:
        """
        Initialize the bills resource.
        
        Args:
            client: Parent CongressClient instance
        """
        self.client = client
    
    def list(
        self,
        congress: int,
        bill_type: Optional[BillType] = None,
        limit: int = 20,
        offset: int = 0,
        sort: Optional[SortOrder] = None,
    ) -> BillListResponse:
        """
        List bills from a specific Congress.
        
        Args:
            congress: Congress number (e.g., 118 for 118th Congress)
            bill_type: Optional bill type filter (hr, s, hjres, etc.)
            limit: Maximum number of results (default: 20, max: 250)
            offset: Number of results to skip for pagination
            sort: Sort order (asc/desc)
        
        Returns:
            BillListResponse with list of bills and pagination info
        
        Raises:
            ValidationError: If parameters are invalid
            APIError: If request fails
            
        Example:
            >>> bills = client.bills.list(congress=118, bill_type="hr", limit=10)
            >>> for bill in bills.bills:
            ...     print(f"H.R. {bill.number}: {bill.title}")
        """
        # Build endpoint
        if bill_type:
            endpoint = f"/bill/{congress}/{bill_type}"
        else:
            endpoint = f"/bill/{congress}"
        
        # Build parameters
        params = {
            "limit": min(limit, 250),  # API max is 250
            "offset": offset,
        }
        
        if sort:
            params["sort"] = sort.value
        
        # Make request
        response_data = self.client.get(endpoint, params=params)
        
        # Parse and return
        return self.client.validate_response(response_data, BillListResponse)
    
    def get(
        self,
        congress: int,
        bill_type: BillType,
        number: int,
    ) -> Bill:
        """
        Get detailed information about a specific bill.
        
        Args:
            congress: Congress number (e.g., 118)
            bill_type: Type of bill (hr, s, hjres, etc.)
            number: Bill number
        
        Returns:
            Bill object with full details
        
        Raises:
            NotFoundError: If bill doesn't exist
            APIError: If request fails
            
        Example:
            >>> bill = client.bills.get(congress=118, bill_type="hr", number=1)
            >>> print(f"Introduced: {bill.introduced_date}")
            >>> print(f"Sponsors: {len(bill.sponsors)}")
        """
        endpoint = f"/bill/{congress}/{bill_type}/{number}"
        response_data = self.client.get(endpoint)
        
        # API returns {"bill": {...}} structure
        bill_data = response_data.get("bill", response_data)
        return self.client.validate_response(bill_data, Bill)
    
    def get_actions(
        self,
        congress: int,
        bill_type: BillType,
        number: int,
    ) -> List[dict]:
        """
        Get all actions taken on a bill.
        
        Args:
            congress: Congress number
            bill_type: Type of bill
            number: Bill number
        
        Returns:
            List of action dictionaries
        
        Example:
            >>> actions = client.bills.get_actions(118, "hr", 1)
            >>> for action in actions:
            ...     print(f"{action['date']}: {action['text']}")
        """
        endpoint = f"/bill/{congress}/{bill_type}/{number}/actions"
        response_data = self.client.get(endpoint)
        return response_data.get("actions", [])
    
    def get_cosponsors(
        self,
        congress: int,
        bill_type: BillType,
        number: int,
    ) -> List[dict]:
        """
        Get all cosponsors of a bill.
        
        Args:
            congress: Congress number
            bill_type: Type of bill
            number: Bill number
        
        Returns:
            List of cosponsor dictionaries
        
        Example:
            >>> cosponsors = client.bills.get_cosponsors(118, "hr", 1)
            >>> print(f"Total cosponsors: {len(cosponsors)}")
        """
        endpoint = f"/bill/{congress}/{bill_type}/{number}/cosponsors"
        response_data = self.client.get(endpoint)
        return response_data.get("cosponsors", [])


class MembersResource:
    """
    Resource handler for member operations.
    
    Provides methods to interact with Members of Congress.
    
    Attributes:
        client: Parent CongressClient instance
    """
    
    def __init__(self, client: "CongressClient") -> None:
        """
        Initialize the members resource.
        
        Args:
            client: Parent CongressClient instance
        """
        self.client = client
    
    def list(
        self,
        congress: Optional[int] = None,
        chamber: Optional[Chamber] = None,
        state: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MemberListResponse:
        """
        List members of Congress.
        
        Args:
            congress: Optional congress number filter
            chamber: Optional chamber filter (house/senate)
            state: Optional state abbreviation filter (e.g., 'CA', 'NY')
            limit: Maximum number of results (default: 20, max: 250)
            offset: Number of results to skip for pagination
        
        Returns:
            MemberListResponse with list of members
        
        Example:
            >>> # Get all current House members from California
            >>> members = client.members.list(
            ...     congress=118,
            ...     chamber="house",
            ...     state="CA"
            ... )
        """
        # Build endpoint
        if congress and chamber:
            endpoint = f"/member/congress/{congress}/{chamber}"
        elif congress:
            endpoint = f"/member/congress/{congress}"
        else:
            endpoint = "/member"
        
        # Build parameters
        params = {
            "limit": min(limit, 250),
            "offset": offset,
        }
        
        if state:
            params["state"] = state.upper()
        
        # Make request
        response_data = self.client.get(endpoint, params=params)
        return self.client.validate_response(response_data, MemberListResponse)
    
    def get(self, bioguide_id: str) -> Member:
        """
        Get detailed information about a specific member.
        
        Args:
            bioguide_id: Member's bioguide ID (e.g., 'P000197')
        
        Returns:
            Member object with full details
        
        Raises:
            NotFoundError: If member doesn't exist
        
        Example:
            >>> member = client.members.get("P000197")
            >>> print(f"{member.name} ({member.party}-{member.state})")
        """
        endpoint = f"/member/{bioguide_id}"
        response_data = self.client.get(endpoint)
        
        # API returns {"member": {...}} structure
        member_data = response_data.get("member", response_data)
        return self.client.validate_response(member_data, Member)


class VotesResource:
    """
    Resource handler for vote operations.
    
    Provides methods to interact with congressional votes.
    
    Attributes:
        client: Parent CongressClient instance
    """
    
    def __init__(self, client: "CongressClient") -> None:
        """
        Initialize the votes resource.
        
        Args:
            client: Parent CongressClient instance
        """
        self.client = client
    
    def list(
        self,
        congress: int,
        chamber: Chamber,
        limit: int = 20,
        offset: int = 0,
    ) -> VoteListResponse:
        """
        List votes from a specific Congress and chamber.
        
        Args:
            congress: Congress number
            chamber: Chamber (house/senate)
            limit: Maximum number of results (default: 20)
            offset: Number of results to skip for pagination
        
        Returns:
            VoteListResponse with list of votes
        
        Example:
            >>> votes = client.votes.list(congress=118, chamber="house")
            >>> for vote in votes.votes:
            ...     print(f"Vote {vote.vote_number}: {vote.question}")
        """
        endpoint = f"/vote/{congress}/{chamber}"
        
        params = {
            "limit": min(limit, 250),
            "offset": offset,
        }
        
        response_data = self.client.get(endpoint, params=params)
        return self.client.validate_response(response_data, VoteListResponse)
    
    def get(
        self,
        congress: int,
        chamber: Chamber,
        vote_number: int,
    ) -> Vote:
        """
        Get detailed information about a specific vote.
        
        Args:
            congress: Congress number
            chamber: Chamber (house/senate)
            vote_number: Roll call vote number
        
        Returns:
            Vote object with full details
        
        Raises:
            NotFoundError: If vote doesn't exist
        
        Example:
            >>> vote = client.votes.get(118, "house", 1)
            >>> print(f"Result: {vote.result}")
            >>> print(f"Yes: {vote.total_yes}, No: {vote.total_no}")
        """
        endpoint = f"/vote/{congress}/{chamber}/{vote_number}"
        response_data = self.client.get(endpoint)
        
        # API returns {"vote": {...}} structure
        vote_data = response_data.get("vote", response_data)
        return self.client.validate_response(vote_data, Vote)


class CongressClient(BaseClient):
    """
    Main client for Congress.gov API.
    
    Provides access to federal legislative data including bills,
    members, committees, and votes.
    
    The client uses resource-based organization:
    - client.bills: Bill operations
    - client.members: Member operations
    - client.votes: Vote operations
    
    Attributes:
        bills: BillsResource for bill operations
        members: MembersResource for member operations
        votes: VotesResource for vote operations
    
    Example:
        >>> from opendiscourse_sdk import CongressClient
        >>> 
        >>> # Initialize client
        >>> client = CongressClient(api_key="your_key")
        >>> 
        >>> # Or use environment variable
        >>> import os
        >>> os.environ['CONGRESS_API_KEY'] = 'your_key'
        >>> client = CongressClient()
        >>> 
        >>> # Use as context manager
        >>> with CongressClient(api_key="your_key") as client:
        ...     bills = client.bills.list(congress=118, limit=10)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        rate_limit_delay: float = 0.5,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the Congress.gov API client.
        
        Args:
            api_key: Congress.gov API key (or set CONGRESS_API_KEY env var)
            timeout: Request timeout in seconds (default: 30)
            rate_limit_delay: Delay between requests in seconds (default: 0.5)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Raises:
            AuthenticationError: If API key is not provided
        """
        # Get API key from parameter or environment
        api_key = api_key or os.getenv("CONGRESS_API_KEY")
        
        # Initialize base client
        super().__init__(
            base_url="https://api.congress.gov/v3",
            api_key=api_key,
            timeout=timeout,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
        )
        
        # Initialize resources
        self.bills = BillsResource(self)
        self.members = MembersResource(self)
        self.votes = VotesResource(self)
