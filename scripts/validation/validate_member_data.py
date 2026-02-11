#!/usr/bin/env python3
"""
Member Data Validation Script

This script validates processed member data to ensure data quality and completeness.

Usage:
    python validate_member_data.py --input data/processed/members
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemberDataValidator:
    """Validate member data for quality and completeness."""

    REQUIRED_FIELDS = [
        'bioguide_id',
        'name',
        'party',
        'state',
        'chamber'
    ]

    VALID_CHAMBERS = ['House', 'Senate']
    VALID_PARTY_CODES = ['D', 'R', 'I', 'L', 'G', 'Unknown']

    def __init__(self, input_dir: Path):
        self.input_dir = input_dir
        self.validation_results = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'errors': [],
            'warnings': [],
            'validation_time': None
        }

    def validate_all_files(self) -> Dict[str, Any]:
        """Validate all processed member data files."""
        logger.info(f"Validating member data in {self.input_dir}")

        start_time = datetime.now()
        json_files = list(self.input_dir.glob('*.json'))

        if not json_files:
            logger.warning(f"No JSON files found in {self.input_dir}")
            return self.validation_results

        for json_file in json_files:
            if json_file.name == 'processing_summary.json':
                continue

            try:
                self.validate_file(json_file)
            except Exception as e:
                logger.error(f"Error validating {json_file}: {e}")
                self.validation_results['errors'].append({
                    'file': str(json_file),
                    'error': str(e)
                })

        end_time = datetime.now()
        self.validation_results['validation_time'] = (end_time - start_time).total_seconds()

        self.generate_validation_report()
        return self.validation_results

    def validate_file(self, file_path: Path) -> None:
        """Validate a single member data file."""
        logger.info(f"Validating file: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        members = data.get('members', [])

        for idx, member in enumerate(members):
            self.validation_results['total_records'] += 1

            is_valid, errors, warnings = self.validate_member(member)

            if is_valid:
                self.validation_results['valid_records'] += 1
            else:
                self.validation_results['invalid_records'] += 1

            if errors:
                self.validation_results['errors'].extend([
                    {
                        'file': str(file_path),
                        'record_index': idx,
                        'bioguide_id': member.get('bioguide_id', 'Unknown'),
                        'error': error
                    }
                    for error in errors
                ])

            if warnings:
                self.validation_results['warnings'].extend([
                    {
                        'file': str(file_path),
                        'record_index': idx,
                        'bioguide_id': member.get('bioguide_id', 'Unknown'),
                        'warning': warning
                    }
                    for warning in warnings
                ])

    def validate_member(self, member: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate a single member record."""
        errors = []
        warnings = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in member or not member[field]:
                errors.append(f"Missing required field: {field}")

        # Validate bioguide_id format
        bioguide_id = member.get('bioguide_id', '')
        if bioguide_id and not bioguide_id.isalnum():
            warnings.append(f"Bioguide ID has unexpected format: {bioguide_id}")

        # Validate name structure
        name = member.get('name', {})
        if isinstance(name, dict):
            if not name.get('first') and not name.get('last'):
                errors.append("Name must have at least first or last name")
        else:
            errors.append("Name field must be a dictionary")

        # Validate party
        party = member.get('party', {})
        if isinstance(party, dict):
            party_code = party.get('code', '')
            if party_code and party_code not in self.VALID_PARTY_CODES:
                warnings.append(f"Unexpected party code: {party_code}")
        else:
            errors.append("Party field must be a dictionary")

        # Validate chamber
        chamber = member.get('chamber', '')
        if chamber and chamber not in self.VALID_CHAMBERS:
            errors.append(f"Invalid chamber value: {chamber}")

        # Validate state
        state = member.get('state', '')
        if state and len(state) != 2:
            warnings.append(f"State code should be 2 characters: {state}")

        # Validate district for House members
        if chamber == 'House':
            district = member.get('district')
            if district is None:
                warnings.append("House member missing district number")

        # Validate congressional service dates
        service = member.get('congressional_service', {})
        if isinstance(service, dict):
            start = service.get('start')
            end = service.get('end')

            if start and end:
                try:
                    start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))

                    if end_date < start_date:
                        errors.append("Service end date before start date")
                except (ValueError, AttributeError):
                    warnings.append("Invalid date format in congressional service")

        # Validate terms
        terms = member.get('terms', [])
        if not isinstance(terms, list):
            warnings.append("Terms field should be a list")
        elif len(terms) == 0:
            warnings.append("Member has no terms listed")

        # Validate contact information
        contact = member.get('contact', {})
        if isinstance(contact, dict):
            phone = contact.get('phone', '')
            if phone and not self._is_valid_phone(phone):
                warnings.append(f"Invalid phone format: {phone}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Check if phone number has a valid format."""
        # Simple validation - at least 10 digits
        digits = ''.join(c for c in phone if c.isdigit())
        return len(digits) >= 10

    def generate_validation_report(self) -> None:
        """Generate a validation report."""
        report_file = self.input_dir / 'validation_report.json'

        report = {
            'summary': {
                'total_records': self.validation_results['total_records'],
                'valid_records': self.validation_results['valid_records'],
                'invalid_records': self.validation_results['invalid_records'],
                'validation_rate': (
                    self.validation_results['valid_records'] / 
                    self.validation_results['total_records'] * 100
                    if self.validation_results['total_records'] > 0 else 0
                ),
                'validation_time': self.validation_results['validation_time']
            },
            'errors': self.validation_results['errors'],
            'warnings': self.validation_results['warnings'],
            'generated_at': datetime.now().isoformat()
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Validation report saved to {report_file}")
        logger.info("Validation Summary:")
        logger.info(f"  Total Records: {report['summary']['total_records']}")
        logger.info(f"  Valid Records: {report['summary']['valid_records']}")
        logger.info(f"  Invalid Records: {report['summary']['invalid_records']}")
        logger.info(f"  Validation Rate: {report['summary']['validation_rate']:.2f}%")
        logger.info(f"  Errors: {len(self.validation_results['errors'])}")
        logger.info(f"  Warnings: {len(self.validation_results['warnings'])}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Validate processed member data'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/processed/members'),
        help='Input directory containing processed member data'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    validator = MemberDataValidator(args.input)
    results = validator.validate_all_files()

    # Exit with error code if validation failed
    if results['invalid_records'] > 0:
        logger.error(f"Validation failed: {results['invalid_records']} invalid records")
        exit(1)
    else:
        logger.info("All records validated successfully")
        exit(0)


if __name__ == '__main__':
    main()
