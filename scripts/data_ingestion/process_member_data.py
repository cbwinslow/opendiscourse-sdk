#!/usr/bin/env python3
"""
Member Data Processing Script

This script processes raw member data downloaded from Congress API and transforms
it into a structured format ready for database ingestion.

Usage:
    python process_member_data.py --input data/raw/members --output data/processed/members
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemberDataProcessor:
    """Process and transform member data."""

    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_all_files(self) -> Dict[str, Any]:
        """Process all member data files."""
        logger.info(f"Processing member data from {self.input_dir}")

        stats = {
            'files_processed': 0,
            'members_processed': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }

        json_files = list(self.input_dir.glob('**/*.json'))

        if not json_files:
            logger.warning(f"No JSON files found in {self.input_dir}")
            return stats

        for json_file in json_files:
            try:
                self.process_file(json_file)
                stats['files_processed'] += 1
            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")
                stats['errors'] += 1

        stats['end_time'] = datetime.now().isoformat()
        logger.info(f"Processing complete: {stats}")
        return stats

    def process_file(self, file_path: Path) -> None:
        """Process a single member data file."""
        logger.info(f"Processing file: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        # Handle different data structures
        if 'members' in data:
            members = data['members']
        elif isinstance(data, list):
            members = data
        else:
            members = [data]

        processed_members = []

        for member in members:
            try:
                processed = self.process_member(member)
                processed_members.append(processed)
            except Exception as e:
                logger.error(f"Error processing member: {e}")
                continue

        # Save processed data
        output_file = self.output_dir / file_path.name
        with open(output_file, 'w') as f:
            json.dump({
                'members': processed_members,
                'count': len(processed_members),
                'processed_at': datetime.now().isoformat()
            }, f, indent=2)

        logger.info(f"Saved processed data to {output_file}")

    def process_member(self, member: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single member record."""
        processed = {
            'bioguide_id': member.get('bioguideId', ''),
            'name': {
                'first': member.get('firstName', ''),
                'middle': member.get('middleName', ''),
                'last': member.get('lastName', ''),
                'suffix': member.get('suffix', ''),
                'official': member.get('officialName', ''),
                'direct_order': member.get('directOrderName', '')
            },
            'party': {
                'code': member.get('partyCode', ''),
                'name': member.get('partyName', ''),
                'history': member.get('partyHistory', [])
            },
            'state': member.get('state', ''),
            'district': member.get('district'),
            'terms': member.get('terms', []),
            'congressional_service': {
                'start': member.get('congressionalServiceStart'),
                'end': member.get('congressionalServiceEnd'),
                'years': member.get('congressionalServiceYears')
            },
            'chamber': member.get('chamber', ''),
            'current_member': member.get('currentMember', False),
            'leadership_roles': member.get('leadershipRoles', []),
            'contact': {
                'address': member.get('address', ''),
                'phone': member.get('phone', ''),
                'website': member.get('website', '')
            },
            'social_media': {
                'twitter': member.get('twitter', ''),
                'facebook': member.get('facebook', ''),
                'youtube': member.get('youtube', '')
            },
            'biographical': {
                'birth_year': member.get('birthYear'),
                'death_year': member.get('deathYear'),
                'image_url': member.get('imageUrl', ''),
                'biographical_text': member.get('biographicalText', '')
            },
            'metadata': {
                'update_date': member.get('updateDate'),
                'url': member.get('url', ''),
                'api_url': member.get('apiUrl', '')
            },
            'processed_at': datetime.now().isoformat()
        }

        return processed

    def generate_summary(self) -> None:
        """Generate a summary report of processed data."""
        summary_file = self.output_dir / 'processing_summary.json'

        processed_files = list(self.output_dir.glob('*.json'))

        total_members = 0
        parties = {}
        states = {}
        chambers = {}

        for file_path in processed_files:
            if file_path.name == 'processing_summary.json':
                continue

            with open(file_path) as f:
                data = json.load(f)

            members = data.get('members', [])
            total_members += len(members)

            for member in members:
                # Count by party
                party = member.get('party', {}).get('code', 'Unknown')
                parties[party] = parties.get(party, 0) + 1

                # Count by state
                state = member.get('state', 'Unknown')
                states[state] = states.get(state, 0) + 1

                # Count by chamber
                chamber = member.get('chamber', 'Unknown')
                chambers[chamber] = chambers.get(chamber, 0) + 1

        summary = {
            'total_members': total_members,
            'by_party': parties,
            'by_state': states,
            'by_chamber': chambers,
            'files_processed': len(processed_files) - 1,
            'generated_at': datetime.now().isoformat()
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary saved to {summary_file}")
        logger.info(f"Total members processed: {total_members}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Process member data from Congress API'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/raw/members'),
        help='Input directory containing raw member data'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/processed/members'),
        help='Output directory for processed data'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    processor = MemberDataProcessor(args.input, args.output)
    stats = processor.process_all_files()
    processor.generate_summary()

    logger.info(f"Processing complete: {stats}")


if __name__ == '__main__':
    main()
