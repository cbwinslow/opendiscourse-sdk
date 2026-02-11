#!/usr/bin/env python3
"""
Test script to verify the transform_* mapping functions for Congress, OpenStates, and GovInfo CLIs.
It creates sample API response data and prints the transformed tuples.
"""

# Import CLIs (adjust path if needed)
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))  # Add project root

from scripts.ingestion.congress_cli import CongressCLI
from scripts.ingestion.govinfo_cli import GovInfoCLI
from scripts.ingestion.openstates_cli import OpenStatesCLI


def test_congress_transform():
    cli = CongressCLI(api_key="dummy", db_config={})
    sample_bill = {
        "bill": {
            "type": "hr",
            "number": 123,
            "originChamber": "House",
            "introducedDate": "2023-01-01",
            "latestAction": {"actionDate": "2023-02-01", "text": "Passed"},
            "policyArea": {"name": "Health"},
            "title": "Sample Bill",
            "sponsor": {"bioguideId": "A000001"}
        }
    }
    transformed = cli.transform_bill(sample_bill, congress=118)
    print("Congress bill transformed:", transformed)

def test_openstates_transform():
    cli = OpenStatesCLI(api_key="dummy", db_config={})
    sample_person = {
        "id": "ocd-person/1",
        "name": "John Doe",
        "givenName": "John",
        "familyName": "Doe",
        "party": "Democratic",
        "current_role": {"jurisdiction_id": "ocd-jurisdiction/us/ca"},
        "sources": []
    }
    transformed = cli.transform_person(sample_person)
    print("OpenStates person transformed:", transformed)

    sample_bill = {
        "id": "ocd-bill/1",
        "identifier": "SB 1",
        "title": "Sample Bill",
        "classification": ["bill"],
        "jurisdiction": {"id": "ocd-jurisdiction/us/ca"},
        "session": "2023",
        "actions": []
    }
    transformed_bill = cli.transform_bill(sample_bill)
    print("OpenStates bill transformed:", transformed_bill)

def test_govinfo_transform():
    cli = GovInfoCLI(api_key="dummy", db_config={})
    sample_collection = {
        "collectionCode": "BILLS",
        "collectionName": "Bills Collection",
        "packageCount": 10,
        "granuleCount": 100
    }
    print("GovInfo collection transformed:", cli.transform_collection(sample_collection))

    sample_package = {
        "packageId": "PKG123",
        "collectionCode": "BILLS",
        "title": "Package Title",
        "congressNumber": 118,
        "chamberCode": "house",
        "billType": "hr",
        "billNumber": 123,
        "docClass": "pdf",
        "granuleCount": 5,
        "dateIssued": "2023-01-01",
        "lastModified": "2023-01-02"
    }
    print("GovInfo package transformed:", cli.transform_package(sample_package))

    sample_granule = {
        "granuleId": "GRAN123",
        "packageId": "PKG123",
        "granuleClass": "pdf",
        "title": "Granule Title",
        "sequenceNumber": 1,
        "granuleDate": "2023-01-01",
        "lastModified": "2023-01-02"
    }
    print("GovInfo granule transformed:", cli.transform_granule(sample_granule))

if __name__ == "__main__":
    test_congress_transform()
    test_openstates_transform()
    test_govinfo_transform()
