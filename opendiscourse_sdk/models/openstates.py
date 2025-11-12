"""
Pydantic models for OpenStates API.

This module defines all data models for the OpenStates API including:
- State legislators
- State bills
- State committees
- State votes

Author: OpenDiscourse Team
License: MIT
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from opendiscourse_sdk.enums import StateCode, StateChamber, Party, ActionType
from opendiscourse_sdk.models.common import BaseResponse, ContactInfo


class Legislator(BaseResponse):
    """
    State legislator information.
    
    Attributes:
        id: OpenStates unique ID
        name: Full name
        party: Political party
        jurisdiction: State/jurisdiction code
        current_role: Current role information
        email: Email address
        capitol_office: Capitol office information
        district_office: District office information
    """
    
    id: str = Field(..., description="OpenStates ID")
    name: str = Field(..., description="Full name")
    party: Optional[Party] = Field(None, description="Party affiliation")
    jurisdiction: StateCode = Field(..., description="State code")
    current_role: Optional[dict] = Field(None, description="Current role", alias="currentRole")
    email: Optional[str] = Field(None, description="Email address")
    capitol_office: Optional[dict] = Field(None, description="Capitol office", alias="capitolOffice")
    district_office: Optional[dict] = Field(None, description="District office", alias="districtOffice")
    
    model_config = ConfigDict(populate_by_name=True)


class StateBill(BaseResponse):
    """
    State bill information.
    
    Attributes:
        id: OpenStates unique ID
        identifier: Bill identifier (e.g., "SB 123")
        title: Bill title
        classification: Bill classification
        jurisdiction: State code
        session: Legislative session
        created_at: Creation timestamp
        updated_at: Last update timestamp
        first_action_date: First action date
        latest_action_date: Latest action date
        latest_action_description: Latest action text
        sponsorships: List of sponsors
        subjects: Policy subjects
    """
    
    id: str = Field(..., description="OpenStates ID")
    identifier: str = Field(..., description="Bill identifier")
    title: str = Field(..., description="Bill title")
    classification: List[str] = Field(default_factory=list, description="Classifications")
    jurisdiction: StateCode = Field(..., description="State code")
    session: str = Field(..., description="Legislative session")
    created_at: datetime = Field(..., description="Created at", alias="createdAt")
    updated_at: datetime = Field(..., description="Updated at", alias="updatedAt")
    first_action_date: Optional[date] = Field(None, description="First action", alias="firstActionDate")
    latest_action_date: Optional[date] = Field(None, description="Latest action", alias="latestActionDate")
    latest_action_description: Optional[str] = Field(None, description="Latest action text", alias="latestActionDescription")
    sponsorships: List[dict] = Field(default_factory=list, description="Sponsors")
    subjects: List[str] = Field(default_factory=list, description="Subjects")
    
    model_config = ConfigDict(populate_by_name=True)


class LegislatorListResponse(BaseResponse):
    """Response from legislators list endpoint."""
    
    results: List[Legislator] = Field(default_factory=list, description="Legislators")
    pagination: Optional[dict] = Field(None, description="Pagination info")


class BillListResponse(BaseResponse):
    """Response from bills list endpoint."""
    
    results: List[StateBill] = Field(default_factory=list, description="Bills")
    pagination: Optional[dict] = Field(None, description="Pagination info")
