"""
Example usage scripts for the OpenDiscourse SDK.

This module provides complete, working examples for all three API clients.
Run this file directly to see the SDK in action (requires valid API keys).

Author: OpenDiscourse Team
License: MIT
"""

import os
from datetime import datetime


def example_congress_api():
    """
    Example usage of the Congress.gov API client.
    
    Demonstrates:
    - Listing bills
    - Getting bill details
    - Listing members
    - Getting vote information
    """
    from opendiscourse_sdk import CongressClient
    from opendiscourse_sdk.exceptions import APIError, NotFoundError

    print("\n" + "="*60)
    print("Congress.gov API Examples")
    print("="*60)

    # Initialize client (reads CONGRESS_API_KEY from environment)
    client = CongressClient()

    try:
        # Example 1: List recent House bills
        print("\n1. Listing recent House bills:")
        bills = client.bills.list(congress=118, bill_type="hr", limit=5)
        for bill in bills.bills:
            print(f"  - H.R. {bill.number}: {bill.title[:60]}...")

        # Example 2: Get a specific bill
        print("\n2. Getting details for H.R. 1:")
        try:
            bill = client.bills.get(congress=118, bill_type="hr", number=1)
            print(f"  Title: {bill.title}")
            print(f"  Introduced: {bill.introduced_date}")
            print(f"  Sponsors: {len(bill.sponsors)}")
            print(f"  Status: {bill.status}")
        except NotFoundError:
            print("  Bill not found")

        # Example 3: List members from California
        print("\n3. Listing House members from California:")
        members = client.members.list(
            congress=118,
            chamber="house",
            state="CA",
            limit=5
        )
        for member in members.members:
            print(f"  - {member.name} ({member.party}-{member.district})")

        # Example 4: Get recent House votes
        print("\n4. Listing recent House votes:")
        votes = client.votes.list(congress=118, chamber="house", limit=3)
        for vote in votes.votes:
            print(f"  - Vote #{vote.vote_number}: {vote.question}")
            print(f"    Result: {vote.result} (Yes: {vote.total_yes}, No: {vote.total_no})")

    except APIError as e:
        print(f"\nAPI Error: {e}")
    except Exception as e:
        print(f"\nError: {e}")


def example_govinfo_api():
    """
    Example usage of the GovInfo.gov API client.
    
    Demonstrates:
    - Listing collections
    - Getting packages from a collection
    - Retrieving package content
    """
    from opendiscourse_sdk import GovInfoClient
    from opendiscourse_sdk.exceptions import APIError

    print("\n" + "="*60)
    print("GovInfo.gov API Examples")
    print("="*60)

    # Initialize client (reads GOVINFO_API_KEY from environment)
    client = GovInfoClient()

    try:
        # Example 1: List available collections
        print("\n1. Listing available collections:")
        collections = client.collections.list()
        for collection in collections.collections[:5]:
            print(f"  - {collection.collection_code}: {collection.collection_name}")

        # Example 2: Get packages from BILLS collection
        print("\n2. Getting recent bills from GovInfo:")
        packages = client.packages.list(
            collection="BILLS",
            start_date="2024-01-01",
            page_size=5
        )
        for package in packages.packages:
            print(f"  - {package.package_id}: {package.title[:60]}...")

        # Example 3: Get package details
        if packages.packages:
            package_id = packages.packages[0].package_id
            print(f"\n3. Getting details for package {package_id}:")
            package = client.packages.get(package_id)
            print(f"  Title: {package.title}")
            print(f"  Collection: {package.collection_code}")
            print(f"  Issued: {package.date_issued}")

            # Example 4: Get package content (uncomment to download)
            # print(f"\n4. Getting content for {package_id}:")
            # content = client.packages.get_content(package_id, content_type="xml")
            # print(f"  Content length: {len(content)} characters")

    except APIError as e:
        print(f"\nAPI Error: {e}")
    except Exception as e:
        print(f"\nError: {e}")


def example_openstates_api():
    """
    Example usage of the OpenStates API client.
    
    Demonstrates:
    - Listing state legislators
    - Listing state bills
    """
    from opendiscourse_sdk import OpenStatesClient
    from opendiscourse_sdk.exceptions import APIError

    print("\n" + "="*60)
    print("OpenStates API Examples")
    print("="*60)

    # Initialize client (reads OPENSTATES_API_KEY from environment)
    client = OpenStatesClient()

    try:
        # Example 1: List legislators from New York
        print("\n1. Listing legislators from New York:")
        legislators = client.legislators.list(jurisdiction="ny", per_page=5)
        for leg in legislators.results:
            print(f"  - {leg.name} ({leg.party})")

        # Example 2: List recent bills from California
        print("\n2. Listing recent bills from California:")
        bills = client.bills.list(
            jurisdiction="ca",
            session="2023-2024",
            per_page=5
        )
        for bill in bills.results:
            print(f"  - {bill.identifier}: {bill.title[:60]}...")

    except APIError as e:
        print(f"\nAPI Error: {e}")
    except Exception as e:
        print(f"\nError: {e}")


def example_error_handling():
    """
    Example of error handling with the SDK.
    
    Demonstrates:
    - Handling authentication errors
    - Handling not found errors
    - Handling rate limit errors
    - Using context managers
    """
    from opendiscourse_sdk import CongressClient
    from opendiscourse_sdk.exceptions import (
        APIError,
        AuthenticationError,
        NotFoundError,
        RateLimitError,
    )

    print("\n" + "="*60)
    print("Error Handling Examples")
    print("="*60)

    # Example 1: Using context manager
    print("\n1. Using context manager:")
    try:
        with CongressClient() as client:
            bills = client.bills.list(congress=118, limit=3)
            print(f"  Retrieved {len(bills.bills)} bills")
            # Session is automatically closed when exiting
    except AuthenticationError:
        print("  Authentication failed - check your API key")

    # Example 2: Handling not found
    print("\n2. Handling NotFoundError:")
    client = CongressClient()
    try:
        # Try to get a bill that doesn't exist
        bill = client.bills.get(congress=118, bill_type="hr", number=999999)
    except NotFoundError:
        print("  Bill not found (expected)")

    # Example 3: Handling rate limits
    print("\n3. Handling RateLimitError:")
    try:
        # Make many requests quickly (may trigger rate limit)
        for i in range(3):
            bills = client.bills.list(congress=118, limit=1)
        print("  Requests completed successfully")
    except RateLimitError as e:
        print(f"  Rate limit exceeded. Retry after {e.retry_after} seconds")

    # Example 4: Catch-all error handling
    print("\n4. General error handling:")
    try:
        bill = client.bills.get(congress=118, bill_type="hr", number=1)
        print(f"  Successfully retrieved: {bill.title[:50]}...")
    except APIError as e:
        print(f"  API error occurred: {e}")
    finally:
        client.close()


def main():
    """
    Run all example functions.
    
    Note: Requires valid API keys to be set in environment variables:
    - CONGRESS_API_KEY
    - GOVINFO_API_KEY
    - OPENSTATES_API_KEY
    """
    print("\n" + "="*60)
    print("OpenDiscourse SDK - Examples")
    print("="*60)
    print(f"Timestamp: {datetime.now()}")

    # Check for API keys
    if not os.getenv("CONGRESS_API_KEY"):
        print("\nWarning: CONGRESS_API_KEY not set")
    if not os.getenv("GOVINFO_API_KEY"):
        print("Warning: GOVINFO_API_KEY not set")
    if not os.getenv("OPENSTATES_API_KEY"):
        print("Warning: OPENSTATES_API_KEY not set")

    # Run examples
    try:
        if os.getenv("CONGRESS_API_KEY"):
            example_congress_api()

        if os.getenv("GOVINFO_API_KEY"):
            example_govinfo_api()

        if os.getenv("OPENSTATES_API_KEY"):
            example_openstates_api()

        # Always run error handling examples
        if os.getenv("CONGRESS_API_KEY"):
            example_error_handling()

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
