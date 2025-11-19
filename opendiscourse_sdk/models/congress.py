"""
Pydantic models for Congress.gov API.

This module defines all data models for the Congress.gov API including:
- Bills and resolutions
- Members of Congress
- Committees
- Votes and amendments

Author: OpenDiscourse Team
License: MIT
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from opendiscourse_sdk.enums import BillType, Chamber, BillStatus, Party, VoteResult
from opendiscourse_sdk.models.common import BaseResponse, ContactInfo, DateRange


class BillSummary(BaseResponse):
    """
    Summary information for a bill.
    
    This is the abbreviated version returned in list endpoints.
    
    Attributes:
        number: Bill number
        type: Type of bill (hr, s, hjres, etc.)
        congress: Congress number
        title: Bill title
        introduced_date: Date bill was introduced
        latest_action: Latest action taken on the bill
        url: URL to full bill details
    """
    
    number: int = Field(..., description="Bill number")
    type: BillType = Field(..., description="Type of bill")
    congress: int = Field(..., description="Congress number (e.g., 118)")
    title: str = Field(..., description="Bill title")
    introduced_date: Optional[date] = Field(None, description="Introduction date", alias="introducedDate")
    latest_action: Optional[str] = Field(None, description="Latest action text", alias="latestAction")
    url: Optional[HttpUrl] = Field(None, description="URL to full bill details")
    
    model_config = ConfigDict(populate_by_name=True)


class Sponsor(BaseModel):
    """
    Bill sponsor information.
    
    Attributes:
        bioguide_id: Unique bioguide identifier
        name: Full name
        party: Political party
        state: State represented
        district: Congressional district (for Representatives)
        is_original_cosponsor: Whether they were an original cosponsor
    """
    
    bioguide_id: str = Field(..., description="Bioguide ID", alias="bioguideId")
    name: str = Field(..., description="Full name")
    party: Optional[Party] = Field(None, description="Political party")
    state: Optional[str] = Field(None, description="State")
    district: Optional[str] = Field(None, description="District number")
    is_original_cosponsor: bool = Field(False, description="Original cosponsor", alias="isOriginalCosponsor")
    
    model_config = ConfigDict(populate_by_name=True)


class BillAction(BaseModel):
    """
    Action taken on a bill.
    
    Attributes:
        date: Action date
        text: Action description
        action_code: Action code
        chamber: Chamber where action occurred
    """
    
    date: date = Field(..., description="Action date")
    text: str = Field(..., description="Action description")
    action_code: Optional[str] = Field(None, description="Action code", alias="actionCode")
    chamber: Optional[Chamber] = Field(None, description="Chamber")
    
    model_config = ConfigDict(populate_by_name=True)


class Committee(BaseModel):
    """
    Congressional committee information.
    
    Attributes:
        name: Committee name
        system_code: Unique committee code
        chamber: Chamber (house/senate/joint)
        url: URL to committee details
    """
    
    name: str = Field(..., description="Committee name")
    system_code: str = Field(..., description="Committee code", alias="systemCode")
    chamber: Optional[Chamber] = Field(None, description="Chamber")
    url: Optional[HttpUrl] = Field(None, description="Committee URL")
    
    model_config = ConfigDict(populate_by_name=True)


class Bill(BaseResponse):
    """
    Complete bill information.
    
    This is the full version with all details.
    
    Attributes:
        number: Bill number
        type: Type of bill
        congress: Congress number
        title: Bill title
        origin_chamber: Chamber where bill originated
        introduced_date: Introduction date
        latest_action_date: Date of most recent action
        latest_action_text: Text of most recent action
        status: Current bill status
        sponsors: List of sponsors
        cosponsors: List of cosponsors
        committees: Committees bill was referred to
        actions: List of all actions
        subjects: Policy areas and subjects
        related_bills: Related legislation
        text_versions: Available text versions
        summary: Bill summary
        url: URL to bill on Congress.gov
    """
    
    number: int = Field(..., description="Bill number")
    type: BillType = Field(..., description="Type of bill")
    congress: int = Field(..., description="Congress number")
    title: str = Field(..., description="Bill title")
    origin_chamber: Chamber = Field(..., description="Origin chamber", alias="originChamber")
    introduced_date: date = Field(..., description="Introduction date", alias="introducedDate")
    latest_action_date: Optional[date] = Field(None, description="Latest action date", alias="latestActionDate")
    latest_action_text: Optional[str] = Field(None, description="Latest action text", alias="latestActionText")
    status: Optional[BillStatus] = Field(None, description="Bill status")
    sponsors: List[Sponsor] = Field(default_factory=list, description="Sponsors")
    cosponsors: List[Sponsor] = Field(default_factory=list, description="Cosponsors")
    committees: List[Committee] = Field(default_factory=list, description="Committees")
    actions: List[BillAction] = Field(default_factory=list, description="Actions")
    subjects: List[str] = Field(default_factory=list, description="Policy subjects")
    related_bills: List[str] = Field(default_factory=list, description="Related bills", alias="relatedBills")
    text_versions: List[dict] = Field(default_factory=list, description="Text versions", alias="textVersions")
    summary: Optional[str] = Field(None, description="Bill summary")
    url: Optional[HttpUrl] = Field(None, description="Congress.gov URL")
    
    model_config = ConfigDict(populate_by_name=True)


class Member(BaseResponse):
    """
    Member of Congress information.
    
    Attributes:
        bioguide_id: Unique bioguide identifier
        name: Full name
        first_name: First name
        last_name: Last name
        party: Political party
        state: State represented
        district: District number (for Representatives)
        chamber: Chamber (house/senate)
        terms: Service terms
        contact: Contact information
        url: Member's official URL
    """
    
    bioguide_id: str = Field(..., description="Bioguide ID", alias="bioguideId")
    name: str = Field(..., description="Full name")
    first_name: Optional[str] = Field(None, description="First name", alias="firstName")
    last_name: Optional[str] = Field(None, description="Last name", alias="lastName")
    party: Optional[Party] = Field(None, description="Party affiliation")
    state: str = Field(..., description="State")
    district: Optional[str] = Field(None, description="District number")
    chamber: Chamber = Field(..., description="Chamber")
    terms: List[DateRange] = Field(default_factory=list, description="Terms of service")
    contact: Optional[ContactInfo] = Field(None, description="Contact information")
    url: Optional[HttpUrl] = Field(None, description="Official URL")
    
    model_config = ConfigDict(populate_by_name=True)


class Vote(BaseResponse):
    """
    Congressional vote information.
    
    Attributes:
        vote_id: Unique vote identifier
        chamber: Chamber where vote occurred
        congress: Congress number
        session: Session number
        vote_number: Roll call number
        date: Vote date
        question: Question being voted on
        result: Vote result
        vote_type: Type of vote
        total_yes: Total yes votes
        total_no: Total no votes
        total_present: Total present/abstain
        total_not_voting: Total not voting
        url: URL to vote details
    """
    
    vote_id: str = Field(..., description="Vote ID", alias="voteId")
    chamber: Chamber = Field(..., description="Chamber")
    congress: int = Field(..., description="Congress number")
    session: int = Field(..., description="Session number")
    vote_number: int = Field(..., description="Roll call number", alias="voteNumber")
    date: date = Field(..., description="Vote date")
    question: str = Field(..., description="Question voted on")
    result: VoteResult = Field(..., description="Vote result")
    vote_type: Optional[str] = Field(None, description="Vote type", alias="voteType")
    total_yes: int = Field(0, description="Yes votes", alias="totalYes")
    total_no: int = Field(0, description="No votes", alias="totalNo")
    total_present: int = Field(0, description="Present votes", alias="totalPresent")
    total_not_voting: int = Field(0, description="Not voting", alias="totalNotVoting")
    url: Optional[HttpUrl] = Field(None, description="Vote URL")
    
    model_config = ConfigDict(populate_by_name=True)


# Response models for list endpoints
class BillListResponse(BaseResponse):
    """Response from bills list endpoint."""
    
    bills: List[BillSummary] = Field(default_factory=list, description="List of bills")
    count: int = Field(0, description="Total count")
    next_page: Optional[str] = Field(None, description="Next page URL", alias="nextPage")
    
    model_config = ConfigDict(populate_by_name=True)


class MemberListResponse(BaseResponse):
    """Response from members list endpoint."""
    
    members: List[Member] = Field(default_factory=list, description="List of members")
    count: int = Field(0, description="Total count")
    next_page: Optional[str] = Field(None, description="Next page URL", alias="nextPage")
    
    model_config = ConfigDict(populate_by_name=True)


class VoteListResponse(BaseResponse):
    """Response from votes list endpoint."""
    
    votes: List[Vote] = Field(default_factory=list, description="List of votes")
    count: int = Field(0, description="Total count")
    next_page: Optional[str] = Field(None, description="Next page URL", alias="nextPage")
    
    model_config = ConfigDict(populate_by_name=True)
