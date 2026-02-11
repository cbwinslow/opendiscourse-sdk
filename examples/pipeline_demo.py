#!/usr/bin/env python3
"""
Comprehensive Usage Examples for OpenDiscourse Pipelines

This script demonstrates the functionality of all three data pipelines:
- GovInfo Pipeline (government documents)
- Committee Pipeline (congressional committees)
- Member Pipeline (congressional members)

Usage:
    python examples/pipeline_demo.py --demo all
    python examples/pipeline_demo.py --demo govinfo
    python examples/pipeline_demo.py --demo committee
    python examples/pipeline_demo.py --demo member
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineDemo:
    """Demonstration of all OpenDiscourse data pipelines."""

    def __init__(self):
        self.results = {
            'demos_run': [],
            'successful': [],
            'failed': [],
            'start_time': datetime.now().isoformat()
        }

    def run_all_demos(self):
        """Run all pipeline demonstrations."""
        logger.info("=== OpenDiscourse Pipeline Demonstrations ===\n")

        self.demo_govinfo_pipeline()
        self.demo_committee_pipeline()
        self.demo_member_pipeline()

        self.results['end_time'] = datetime.now().isoformat()
        self.print_summary()

    def demo_govinfo_pipeline(self):
        """Demonstrate GovInfo pipeline functionality."""
        logger.info("=== GovInfo Data Pipeline Demo ===")
        demo_name = "GovInfo Pipeline"
        self.results['demos_run'].append(demo_name)

        try:
            logger.info("1. GovInfo Pipeline Overview")
            logger.info("   - Downloads government documents from GovInfo API")
            logger.info("   - Processes XML, HTML, and PDF documents")
            logger.info("   - Validates data quality")
            logger.info("   - Loads into PostgreSQL database")

            logger.info("\n2. Example: Download Bills")
            logger.info("   Command:")
            logger.info("   $ python download_data.py --collection BILLS --congress 118")
            logger.info("   ")
            logger.info("   Output:")
            logger.info("   - Raw data saved to: data/raw/govinfo/BILLS/118/")
            logger.info("   - Metadata extracted for each bill")
            logger.info("   - Full text content stored")

            logger.info("\n3. Example: Process Downloaded Data")
            logger.info("   Command:")
            logger.info("   $ python process_data.py --input data/raw/govinfo --output data/processed/govinfo")
            logger.info("   ")
            logger.info("   Processing steps:")
            logger.info("   - Parse XML/HTML content")
            logger.info("   - Extract metadata (sponsors, cosponsors, committees)")
            logger.info("   - Standardize data structure")
            logger.info("   - Generate processing summary")

            logger.info("\n4. Example: Validate Data Quality")
            logger.info("   Command:")
            logger.info("   $ python validate_data.py --input data/processed/govinfo")
            logger.info("   ")
            logger.info("   Validation checks:")
            logger.info("   ✓ Required fields present")
            logger.info("   ✓ Data format correctness")
            logger.info("   ✓ Cross-reference consistency")
            logger.info("   ✓ URL accessibility")

            logger.info("\n5. Data Structure Example")
            example_data = {
                "document_id": "BILLS-118hr1234",
                "collection": "BILLS",
                "congress": 118,
                "doc_type": "hr",
                "doc_number": "1234",
                "title": "Example Bill Title",
                "date_issued": "2024-01-15",
                "metadata": {
                    "sponsors": ["Rep. Example (D-NY)"],
                    "cosponsors": ["Rep. Sample (R-TX)"],
                    "committees": ["House Agriculture"]
                },
                "urls": {
                    "content": "https://www.govinfo.gov/content/...",
                    "pdf": "https://www.govinfo.gov/pdf/...",
                    "xml": "https://www.govinfo.gov/xml/..."
                }
            }
            logger.info(f"   {json.dumps(example_data, indent=2)}")

            logger.info("\n6. Database Schema")
            logger.info("   See: docs/erd/govinfo_schema.puml")
            logger.info("   Tables: documents, collections, congress_sessions,")
            logger.info("           document_content, document_metadata")

            logger.info("\n✓ GovInfo Pipeline Demo Complete\n")
            self.results['successful'].append(demo_name)

        except Exception as e:
            logger.error(f"Error in GovInfo demo: {e}")
            self.results['failed'].append(demo_name)

    def demo_committee_pipeline(self):
        """Demonstrate Committee pipeline functionality."""
        logger.info("=== Committee Data Pipeline Demo ===")
        demo_name = "Committee Pipeline"
        self.results['demos_run'].append(demo_name)

        try:
            logger.info("1. Committee Pipeline Overview")
            logger.info("   - Downloads committee information from Congress API")
            logger.info("   - Tracks committee membership and leadership")
            logger.info("   - Manages subcommittee relationships")
            logger.info("   - Links to hearings and reports")

            logger.info("\n2. Example: Download Committee Data")
            logger.info("   Command:")
            logger.info("   $ python download_committee_data.py --congress 118")
            logger.info("   ")
            logger.info("   Output:")
            logger.info("   - Raw data saved to: data/raw/committees/")
            logger.info("   - House and Senate committees")
            logger.info("   - Subcommittee information included")

            logger.info("\n3. Example: Process Committee Data")
            logger.info("   Command:")
            logger.info("   $ python process_committee_data.py \\")
            logger.info("       --input data/raw/committees \\")
            logger.info("       --output data/processed/committees")
            logger.info("   ")
            logger.info("   Processing steps:")
            logger.info("   - Parse committee JSON data")
            logger.info("   - Map parent-child relationships")
            logger.info("   - Structure member assignments")
            logger.info("   - Generate committee roster")

            logger.info("\n4. Example: Validate Committee Data")
            logger.info("   Command:")
            logger.info("   $ python validate_committee_data.py --input data/processed/committees")
            logger.info("   ")
            logger.info("   Validation checks:")
            logger.info("   ✓ Committee code format")
            logger.info("   ✓ Parent-child relationships")
            logger.info("   ✓ Member bioguide IDs")
            logger.info("   ✓ Date consistency")

            logger.info("\n5. Committee Structure Example")
            example_committee = {
                "committee_code": "HSAG",
                "committee_name": "House Committee on Agriculture",
                "committee_type": "standing",
                "chamber": "house",
                "is_subcommittee": False,
                "jurisdiction": "Agriculture and related matters...",
                "members": [
                    {
                        "bioguide_id": "T000478",
                        "name": "Rep. Example",
                        "party": "Republican",
                        "state": "NY",
                        "role": "Chairman",
                        "rank": 1
                    }
                ],
                "subcommittees": [
                    {
                        "committee_code": "HSAG03",
                        "name": "Livestock and Foreign Agriculture"
                    }
                ]
            }
            logger.info(f"   {json.dumps(example_committee, indent=2)}")

            logger.info("\n6. Database Schema")
            logger.info("   See: docs/erd/committee_schema.puml")
            logger.info("   Tables: committees, committee_members, committee_hearings,")
            logger.info("           committee_reports, committee_history")

            logger.info("\n7. Common Committees")
            committees = [
                ("HSAG", "House Agriculture"),
                ("HSAP", "House Appropriations"),
                ("SSAG", "Senate Agriculture"),
                ("SSAP", "Senate Appropriations")
            ]
            for code, name in committees:
                logger.info(f"   - {code}: {name}")

            logger.info("\n✓ Committee Pipeline Demo Complete\n")
            self.results['successful'].append(demo_name)

        except Exception as e:
            logger.error(f"Error in Committee demo: {e}")
            self.results['failed'].append(demo_name)

    def demo_member_pipeline(self):
        """Demonstrate Member pipeline functionality."""
        logger.info("=== Member Data Pipeline Demo ===")
        demo_name = "Member Pipeline"
        self.results['demos_run'].append(demo_name)

        try:
            logger.info("1. Member Pipeline Overview")
            logger.info("   - Downloads member information from Congress API")
            logger.info("   - Tracks congressional terms and service")
            logger.info("   - Manages party affiliation history")
            logger.info("   - Links to social media profiles")
            logger.info("   - Historical data back to 94th Congress (1975)")

            logger.info("\n2. Example: Download Current Members")
            logger.info("   Command:")
            logger.info("   $ python download_member_data.py --current-only")
            logger.info("   ")
            logger.info("   Output:")
            logger.info("   - Raw data saved to: data/raw/members/")
            logger.info("   - Biographical information")
            logger.info("   - Contact details")
            logger.info("   - Social media profiles")

            logger.info("\n3. Example: Download Historical Data")
            logger.info("   Command:")
            logger.info("   $ python download_member_data.py \\")
            logger.info("       --congress-start 94 --congress-end 118")
            logger.info("   ")
            logger.info("   Coverage:")
            logger.info("   - 94th Congress (1975) to 118th Congress (2024)")
            logger.info("   - ~50 years of congressional history")
            logger.info("   - Thousands of members across both chambers")

            logger.info("\n4. Example: Process Member Data")
            logger.info("   Command:")
            logger.info("   $ python process_member_data.py \\")
            logger.info("       --input data/raw/members \\")
            logger.info("       --output data/processed/members")
            logger.info("   ")
            logger.info("   Processing steps:")
            logger.info("   - Parse member JSON data")
            logger.info("   - Extract biographical information")
            logger.info("   - Structure term history")
            logger.info("   - Map party affiliations")
            logger.info("   - Aggregate service statistics")

            logger.info("\n5. Example: Validate Member Data")
            logger.info("   Command:")
            logger.info("   $ python validate_member_data.py --input data/processed/members")
            logger.info("   ")
            logger.info("   Validation checks:")
            logger.info("   ✓ Bioguide ID format")
            logger.info("   ✓ Name completeness")
            logger.info("   ✓ Party code validity")
            logger.info("   ✓ Chamber and state codes")
            logger.info("   ✓ Date consistency")

            logger.info("\n6. Member Data Structure Example")
            example_member = {
                "bioguide_id": "T000478",
                "name": {
                    "first": "Claudia",
                    "last": "Tenney",
                    "official": "Claudia Tenney"
                },
                "party": {
                    "code": "R",
                    "name": "Republican"
                },
                "state": "NY",
                "district": 24,
                "chamber": "House",
                "current_member": True,
                "congressional_service": {
                    "start": "2017-01-03",
                    "years": 6.8
                },
                "contact": {
                    "phone": "(202) 225-3665",
                    "website": "https://tenney.house.gov"
                },
                "social_media": {
                    "twitter": "@RepTenney",
                    "facebook": "RepClaudiaTenney"
                }
            }
            logger.info(f"   {json.dumps(example_member, indent=2)}")

            logger.info("\n7. Database Schema")
            logger.info("   See: docs/erd/member_schema.puml")
            logger.info("   Tables: members, member_terms, party_affiliations,")
            logger.info("           leadership_roles, member_contact, member_social_media")

            logger.info("\n8. Party Codes")
            parties = [
                ("D", "Democratic"),
                ("R", "Republican"),
                ("I", "Independent"),
                ("L", "Libertarian")
            ]
            for code, name in parties:
                logger.info(f"   - {code}: {name}")

            logger.info("\n✓ Member Pipeline Demo Complete\n")
            self.results['successful'].append(demo_name)

        except Exception as e:
            logger.error(f"Error in Member demo: {e}")
            self.results['failed'].append(demo_name)

    def print_summary(self):
        """Print summary of demonstrations."""
        logger.info("=" * 60)
        logger.info("DEMONSTRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total demos run: {len(self.results['demos_run'])}")
        logger.info(f"Successful: {len(self.results['successful'])}")
        logger.info(f"Failed: {len(self.results['failed'])}")

        if self.results['successful']:
            logger.info("\n✓ Successful Demos:")
            for demo in self.results['successful']:
                logger.info(f"  - {demo}")

        if self.results['failed']:
            logger.info("\n✗ Failed Demos:")
            for demo in self.results['failed']:
                logger.info(f"  - {demo}")

        logger.info("\nFor detailed documentation, see:")
        logger.info("  - docs/GOVINFO_PIPELINE.md")
        logger.info("  - docs/COMMITTEE_PIPELINE.md")
        logger.info("  - docs/MEMBER_PIPELINE.md")
        logger.info("  - docs/erd/ (for database schemas)")
        logger.info("\n" + "=" * 60)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='OpenDiscourse Pipeline Demonstrations'
    )
    parser.add_argument(
        '--demo',
        choices=['all', 'govinfo', 'committee', 'member'],
        default='all',
        help='Which demo to run (default: all)'
    )

    args = parser.parse_args()

    demo = PipelineDemo()

    if args.demo == 'all':
        demo.run_all_demos()
    elif args.demo == 'govinfo':
        demo.demo_govinfo_pipeline()
    elif args.demo == 'committee':
        demo.demo_committee_pipeline()
    elif args.demo == 'member':
        demo.demo_member_pipeline()


if __name__ == '__main__':
    main()
