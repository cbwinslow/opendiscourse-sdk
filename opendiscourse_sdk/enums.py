"""
Enumerations for the OpenDiscourse SDK.

This module defines all enumeration types used throughout the SDK,
providing type-safe constants for API parameters and responses.

All enums inherit from str and Enum to ensure JSON serialization compatibility
and provide string comparison capabilities.

Author: OpenDiscourse Team
License: MIT
"""

from enum import Enum


class BillType(str, Enum):
    """
    Types of bills in the US Congress.
    
    Used in Congress.gov API to specify the category of legislation.
    """
    HOUSE_BILL = "hr"  # House Bill
    SENATE_BILL = "s"  # Senate Bill
    HOUSE_JOINT_RESOLUTION = "hjres"  # House Joint Resolution
    SENATE_JOINT_RESOLUTION = "sjres"  # Senate Joint Resolution
    HOUSE_CONCURRENT_RESOLUTION = "hconres"  # House Concurrent Resolution
    SENATE_CONCURRENT_RESOLUTION = "sconres"  # Senate Concurrent Resolution
    HOUSE_RESOLUTION = "hres"  # House Simple Resolution
    SENATE_RESOLUTION = "sres"  # Senate Simple Resolution


class Chamber(str, Enum):
    """
    Legislative chambers in the US Congress.
    
    Used to specify which chamber of Congress a bill, member, or vote belongs to.
    """
    HOUSE = "house"  # House of Representatives
    SENATE = "senate"  # Senate
    BOTH = "both"  # Joint (both chambers)


class BillStatus(str, Enum):
    """
    Possible status values for bills.
    
    Represents the current stage of a bill in the legislative process.
    """
    INTRODUCED = "introduced"  # Bill has been introduced
    REFERRED = "referred"  # Referred to committee
    REPORTED = "reported"  # Reported by committee
    PASSED_HOUSE = "passed_house"  # Passed the House
    PASSED_SENATE = "passed_senate"  # Passed the Senate
    PASSED_BOTH = "passed_both"  # Passed both chambers
    RESOLVING_DIFFERENCES = "resolving_differences"  # Reconciling versions
    TO_PRESIDENT = "to_president"  # Sent to President
    BECAME_LAW = "became_law"  # Signed into law
    VETOED = "vetoed"  # Vetoed by President
    FAILED = "failed"  # Failed to pass


class VoteResult(str, Enum):
    """
    Possible outcomes of a legislative vote.
    
    Represents whether a vote passed, failed, or had another outcome.
    """
    PASSED = "passed"  # Vote passed
    FAILED = "failed"  # Vote failed
    AGREED_TO = "agreed_to"  # Motion agreed to
    NOT_AGREED_TO = "not_agreed_to"  # Motion not agreed to
    TIED = "tied"  # Tie vote


class VoteType(str, Enum):
    """
    Types of votes in Congress.
    
    Different voting procedures used in the legislative process.
    """
    YEA_NAY = "yea_nay"  # Yea/Nay vote
    VOICE = "voice"  # Voice vote
    ROLL_CALL = "roll_call"  # Roll call vote
    DIVISION = "division"  # Division vote
    UNANIMOUS_CONSENT = "unanimous_consent"  # Unanimous consent


class Party(str, Enum):
    """
    Political parties in the US Congress.
    
    Standard party affiliations for members of Congress.
    """
    DEMOCRAT = "D"  # Democratic Party
    REPUBLICAN = "R"  # Republican Party
    INDEPENDENT = "I"  # Independent
    LIBERTARIAN = "L"  # Libertarian Party
    GREEN = "G"  # Green Party
    OTHER = "O"  # Other party


class MemberTitle(str, Enum):
    """
    Titles for members of Congress.
    
    Official titles based on position and chamber.
    """
    SENATOR = "Senator"  # US Senator
    REPRESENTATIVE = "Representative"  # US Representative
    DELEGATE = "Delegate"  # Delegate (territories)
    RESIDENT_COMMISSIONER = "Resident Commissioner"  # PR Commissioner


class GovInfoCollection(str, Enum):
    """
    GovInfo.gov document collections.
    
    Available collections in the GovInfo API.
    Each collection represents a different type of government publication.
    """
    BILLS = "BILLS"  # Congressional Bills (text)
    BILLSTATUS = "BILLSTATUS"  # Congressional Bills (status/metadata)
    CONGRESSIONAL_RECORD = "CREC"  # Congressional Record
    FEDERAL_REGISTER = "FR"  # Federal Register
    CFR = "CFR"  # Code of Federal Regulations
    PUBLIC_LAWS = "PLAW"  # Public Laws
    STATUTES = "STATUTE"  # US Statutes at Large
    US_CODE = "USCODE"  # United States Code
    HEARINGS = "CHRG"  # Congressional Hearings
    HOUSE_DOCUMENTS = "HDOC"  # House Documents
    HOUSE_REPORTS = "HRPT"  # House Reports
    SENATE_DOCUMENTS = "SDOC"  # Senate Documents
    SENATE_REPORTS = "SRPT"  # Senate Reports
    CONGRESSIONAL_DOCUMENTS = "CDOC"  # Congressional Documents
    CONGRESSIONAL_REPORTS = "CRPT"  # Congressional Reports
    GOVERNMENT_PUBLICATIONS = "GOVPUB"  # Government Publications
    GAO_REPORTS = "GAOREPORTS"  # GAO Reports
    BUDGET = "BUDGET"  # Budget Documents
    ECONOMIC_INDICATORS = "ECONI"  # Economic Indicators


class DocumentFormat(str, Enum):
    """
    Available document formats from GovInfo API.
    
    Different file formats that documents can be retrieved in.
    """
    XML = "xml"  # Extensible Markup Language
    HTML = "htm"  # Hypertext Markup Language
    PDF = "pdf"  # Portable Document Format
    TXT = "txt"  # Plain text
    ZIP = "zip"  # Compressed archive
    MODS = "mods"  # Metadata Object Description Schema
    PREMIS = "premis"  # Preservation Metadata


class StateCode(str, Enum):
    """
    US state and territory codes.
    
    Two-letter abbreviations used in OpenStates API and other systems.
    """
    ALABAMA = "al"
    ALASKA = "ak"
    ARIZONA = "az"
    ARKANSAS = "ar"
    CALIFORNIA = "ca"
    COLORADO = "co"
    CONNECTICUT = "ct"
    DELAWARE = "de"
    FLORIDA = "fl"
    GEORGIA = "ga"
    HAWAII = "hi"
    IDAHO = "id"
    ILLINOIS = "il"
    INDIANA = "in"
    IOWA = "ia"
    KANSAS = "ks"
    KENTUCKY = "ky"
    LOUISIANA = "la"
    MAINE = "me"
    MARYLAND = "md"
    MASSACHUSETTS = "ma"
    MICHIGAN = "mi"
    MINNESOTA = "mn"
    MISSISSIPPI = "ms"
    MISSOURI = "mo"
    MONTANA = "mt"
    NEBRASKA = "ne"
    NEVADA = "nv"
    NEW_HAMPSHIRE = "nh"
    NEW_JERSEY = "nj"
    NEW_MEXICO = "nm"
    NEW_YORK = "ny"
    NORTH_CAROLINA = "nc"
    NORTH_DAKOTA = "nd"
    OHIO = "oh"
    OKLAHOMA = "ok"
    OREGON = "or"
    PENNSYLVANIA = "pa"
    RHODE_ISLAND = "ri"
    SOUTH_CAROLINA = "sc"
    SOUTH_DAKOTA = "sd"
    TENNESSEE = "tn"
    TEXAS = "tx"
    UTAH = "ut"
    VERMONT = "vt"
    VIRGINIA = "va"
    WASHINGTON = "wa"
    WEST_VIRGINIA = "wv"
    WISCONSIN = "wi"
    WYOMING = "wy"
    # Territories
    DISTRICT_OF_COLUMBIA = "dc"
    PUERTO_RICO = "pr"
    US_VIRGIN_ISLANDS = "vi"
    GUAM = "gu"
    AMERICAN_SAMOA = "as"
    NORTHERN_MARIANA_ISLANDS = "mp"


class StateChamber(str, Enum):
    """
    State legislative chambers.
    
    Different types of chambers in state legislatures.
    """
    UPPER = "upper"  # State Senate (or equivalent)
    LOWER = "lower"  # State House/Assembly (or equivalent)
    LEGISLATURE = "legislature"  # Unicameral legislature (e.g., Nebraska)


class ActionType(str, Enum):
    """
    Types of legislative actions.
    
    Different actions that can occur during the legislative process.
    """
    INTRODUCED = "introduced"  # Bill introduced
    REFERRED = "referred"  # Referred to committee
    REPORTED = "reported"  # Reported by committee
    AMENDED = "amended"  # Amendment proposed or adopted
    PASSED = "passed"  # Passed chamber
    FAILED = "failed"  # Failed to pass
    VETOED = "vetoed"  # Vetoed by executive
    SIGNED = "signed"  # Signed into law
    READING_1 = "reading-1"  # First reading
    READING_2 = "reading-2"  # Second reading
    READING_3 = "reading-3"  # Third reading
    COMMITTEE_PASSAGE = "committee-passage"  # Passed committee
    COMMITTEE_FAILURE = "committee-failure"  # Failed in committee


class CommitteeType(str, Enum):
    """
    Types of congressional committees.
    
    Different categories of committees in Congress.
    """
    STANDING = "standing"  # Permanent committee
    SELECT = "select"  # Temporary, special purpose
    JOINT = "joint"  # Both chambers
    SPECIAL = "special"  # Special investigation
    SUBCOMMITTEE = "subcommittee"  # Subcommittee of another committee


class SortOrder(str, Enum):
    """
    Sort order for list queries.
    
    Standard ascending/descending sort options.
    """
    ASC = "asc"  # Ascending order
    DESC = "desc"  # Descending order


class SortField(str, Enum):
    """
    Fields that can be used for sorting results.
    
    Common fields used in sorting operations across APIs.
    """
    DATE = "date"  # Date field
    UPDATED = "updated"  # Last updated timestamp
    CREATED = "created"  # Creation timestamp
    TITLE = "title"  # Title/name
    NUMBER = "number"  # Bill/document number
    RELEVANCE = "relevance"  # Search relevance score
