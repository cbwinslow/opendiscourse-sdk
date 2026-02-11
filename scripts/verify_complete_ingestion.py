#!/usr/bin/env python3
"""
Complete Ingestion Verification Script

This script provides comprehensive verification of the bulk data ingestion process
with working queries that show what's been ingested and what's left.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import DictCursor

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load environment variables
from dotenv import load_dotenv
from ingestion_config import get_ingestion_mode_from_env, validate_all_api_keys

load_dotenv()

class IngestionVerifier:
    """Comprehensive ingestion verification"""

    def __init__(self):
        self.conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)
        self.verification_time = datetime.now()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up database connections"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results safely"""
        try:
            # Use a fresh connection for each query to avoid transaction issues
            fresh_conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            fresh_cursor = fresh_conn.cursor(cursor_factory=DictCursor)

            fresh_cursor.execute(query)
            columns = [desc[0] for desc in fresh_cursor.description]
            results = []

            for row in fresh_cursor.fetchall():
                result_dict = dict(zip(columns, row))
                # Convert datetime objects to strings
                for key, value in result_dict.items():
                    if isinstance(value, datetime):
                        result_dict[key] = value.isoformat()
                results.append(result_dict)

            fresh_cursor.close()
            fresh_conn.close()
            return results

        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def get_checkpoint_status(self) -> List[Dict[str, Any]]:
        """Get checkpoint status from incremental schema"""
        query = """
            SELECT
                data_source,
                data_type,
                category,
                total_processed,
                total_estimated,
                completion_percentage,
                is_completed,
                last_ingestion_at,
                CASE
                    WHEN is_completed THEN 'COMPLETED'
                    WHEN total_processed > 0 THEN 'IN_PROGRESS'
                    ELSE 'NOT_STARTED'
                END as status
            FROM incremental.checkpoint_status
            ORDER BY data_source, data_type, category
        """
        return self.execute_query(query)

    def get_members_status(self) -> List[Dict[str, Any]]:
        """Get members ingestion status by congress"""
        query = """
            SELECT
                mt.congress,
                COUNT(DISTINCT m.bioguide_id) as total_members,
                MIN(m.created_at) as first_ingested,
                MAX(m.created_at) as last_ingested,
                CASE
                    WHEN COUNT(DISTINCT m.bioguide_id) >= 550 THEN 'COMPLETE'
                    WHEN COUNT(DISTINCT m.bioguide_id) >= 440 THEN 'MOSTLY_COMPLETE'
                    WHEN COUNT(DISTINCT m.bioguide_id) > 0 THEN 'IN_PROGRESS'
                    ELSE 'NOT_STARTED'
                END as status
            FROM congress.member_terms mt
            LEFT JOIN congress.members m ON mt.bioguide_id = m.bioguide_id
            WHERE mt.congress IN (116, 117, 118)
            GROUP BY mt.congress
            ORDER BY mt.congress
        """
        return self.execute_query(query)

    def get_bills_status(self) -> List[Dict[str, Any]]:
        """Get bills ingestion status by congress"""
        query = """
            SELECT
                congress_number,
                COUNT(*) as total_bills,
                MIN(created_at) as first_ingested,
                MAX(created_at) as last_ingested,
                CASE
                    WHEN COUNT(*) > 0 THEN 'IN_PROGRESS'
                    ELSE 'NOT_STARTED'
                END as status
            FROM congress.bills
            WHERE congress_number IN (117, 118)
            GROUP BY congress_number
            ORDER BY congress_number
        """
        return self.execute_query(query)

    def get_data_completeness(self) -> Dict[str, Any]:
        """Get data completeness metrics"""
        queries = {
            'members_completeness': """
                SELECT
                    COUNT(*) as total_members,
                    COUNT(CASE WHEN bioguide_id IS NOT NULL THEN 1 END) as has_bioguide_id,
                    COUNT(CASE WHEN official_full_name IS NOT NULL THEN 1 END) as has_full_name,
                    COUNT(CASE WHEN birthday IS NOT NULL THEN 1 END) as has_birthday,
                    COUNT(CASE WHEN gender IS NOT NULL THEN 1 END) as has_gender
                FROM congress.members
            """,

            'bills_completeness': """
                SELECT
                    COUNT(*) as total_bills,
                    COUNT(CASE WHEN bill_id IS NOT NULL THEN 1 END) as has_bill_id,
                    COUNT(CASE WHEN official_title IS NOT NULL THEN 1 END) as has_title,
                    COUNT(CASE WHEN bill_type IS NOT NULL THEN 1 END) as has_bill_type,
                    COUNT(CASE WHEN congress_number IS NOT NULL THEN 1 END) as has_congress
                FROM congress.bills
            """,

            'table_counts': """
                SELECT
                    'members' as table_name,
                    COUNT(*) as record_count
                FROM congress.members

                UNION ALL

                SELECT
                    'bills' as table_name,
                    COUNT(*) as record_count
                FROM congress.bills
            """
        }

        results = {}
        for key, query in queries.items():
            results[key] = self.execute_query(query)

        return results

    def get_ingestion_timeline(self) -> List[Dict[str, Any]]:
        """Get ingestion timeline by date"""
        query = """
            SELECT
                DATE(created_at) as ingestion_date,
                COUNT(*) as records_ingested,
                'members' as data_type
            FROM congress.members
            GROUP BY DATE(created_at)

            UNION ALL

            SELECT
                DATE(created_at) as ingestion_date,
                COUNT(*) as records_ingested,
                'bills' as data_type
            FROM congress.bills
            GROUP BY DATE(created_at)
            ORDER BY ingestion_date DESC
            LIMIT 20
        """
        return self.execute_query(query)

    def verify_api_key_compliance(self) -> Dict[str, Any]:
        """Verify API key compliance"""
        api_validation = validate_all_api_keys()
        mode = get_ingestion_mode_from_env()

        return {
            'api_validation': api_validation,
            'ingestion_mode': mode.value,
            'compliance_status': 'COMPLIANT' if api_validation['valid'] and mode.value == 'production' else 'NON_COMPLIANT'
        }

    def generate_verification_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        print("🔍 Generating comprehensive verification report...")

        report = {
            'verification_time': self.verification_time.isoformat(),
            'api_key_compliance': self.verify_api_key_compliance(),
            'checkpoint_status': self.get_checkpoint_status(),
            'members_status': self.get_members_status(),
            'bills_status': self.get_bills_status(),
            'data_completeness': self.get_data_completeness(),
            'ingestion_timeline': self.get_ingestion_timeline()
        }

        # Calculate summary statistics
        total_checkpoints = len(report['checkpoint_status'])
        completed_checkpoints = sum(1 for cp in report['checkpoint_status'] if cp['is_completed'])

        total_members = sum(m['total_members'] or 0 for m in report['members_status'])
        total_bills = sum(b['total_bills'] or 0 for b in report['bills_status'])

        report['summary'] = {
            'total_checkpoints': total_checkpoints,
            'completed_checkpoints': completed_checkpoints,
            'checkpoint_completion_rate': (completed_checkpoints / total_checkpoints * 100) if total_checkpoints > 0 else 0,
            'total_members_ingested': total_members,
            'total_bills_ingested': total_bills,
            'total_records_ingested': total_members + total_bills,
            'overall_status': 'COMPLETE' if completed_checkpoints == total_checkpoints else 'IN_PROGRESS'
        }

        return report

    def print_verification_summary(self):
        """Print a concise verification summary"""
        report = self.generate_verification_report()

        print("\\n" + "="*70)
        print("🔍 BULK INGESTION VERIFICATION REPORT")
        print("="*70)

        # API Compliance
        compliance = report['api_key_compliance']
        print(f"🔑 API Compliance: {'✅ ' + compliance['compliance_status']}")
        print(f"🚀 Ingestion Mode: {compliance['ingestion_mode']}")

        # Summary
        summary = report['summary']
        print("\\n📊 SUMMARY:")
        print(f"  Total Records: {summary['total_records_ingested']:,}")
        print(f"  Members: {summary['total_members_ingested']:,}")
        print(f"  Bills: {summary['total_bills_ingested']:,}")
        print(f"  Checkpoints: {summary['completed_checkpoints']}/{summary['total_checkpoints']} ({summary['checkpoint_completion_rate']:.1f}%)")
        print(f"  Overall Status: {summary['overall_status']}")

        # Checkpoint Details
        print("\\n📋 CHECKPOINT STATUS:")
        for cp in report['checkpoint_status']:
            status_icon = "✅" if cp['is_completed'] else "🔄" if cp['total_processed'] > 0 else "❌"
            processed = cp['total_processed'] or 0
            estimated = cp['total_estimated'] or "Unknown"
            percentage = cp['completion_percentage'] or 0
            print(f"  {status_icon} {cp['data_source']} | {cp['data_type']} | {cp['category']}: {processed:,}/{estimated} ({percentage:.1f}%)")

        # Members Status
        print("\\n👥 MEMBERS STATUS:")
        for member in report['members_status']:
            status_icon = "✅" if member['status'] == 'COMPLETE' else "🔄" if member['status'] == 'IN_PROGRESS' else "❌"
            expected = 550 if member['congress'] in [117, 118] else 440
            completion = (member['total_members'] / expected * 100) if expected > 0 else 0
            print(f"  {status_icon} Congress {member['congress']}: {member['total_members']:,}/{expected} ({completion:.1f}%) - {member['status']}")

        # Bills Status
        print("\\n📜 BILLS STATUS:")
        for bill in report['bills_status']:
            status_icon = "🔄" if bill['total_bills'] > 0 else "❌"
            print(f"  {status_icon} Congress {bill['congress_number']}: {bill['total_bills']:,} bills - {bill['status']}")

        # Data Quality
        completeness = report['data_completeness']
        if completeness.get('members_completeness'):
            members = completeness['members_completeness'][0]
            total = members['total_members']
            complete_pct = (members['has_bioguide_id'] / total * 100) if total > 0 else 0
            print("\\n🔍 DATA QUALITY:")
            print(f"  Members: {complete_pct:.1f}% have bioguide_id")

        if completeness.get('bills_completeness'):
            bills = completeness['bills_completeness'][0]
            total = bills['total_bills']
            complete_pct = (bills['has_bill_id'] / total * 100) if total > 0 else 0
            print(f"  Bills: {complete_pct:.1f}% have bill_id")

        print("="*70)

        return report

    def save_verification_report(self, filename: str = None) -> str:
        """Save verification report to file"""
        if not filename:
            timestamp = self.verification_time.strftime('%Y%m%d_%H%M%S')
            filename = f"ingestion_verification_{timestamp}.json"

        report = self.generate_verification_report()

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"📄 Verification report saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return ""

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Verify complete bulk data ingestion')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--save', action='store_true', help='Save report to file')
    parser.add_argument('--json', action='store_true', help='Output JSON format')

    args = parser.parse_args()

    try:
        with IngestionVerifier() as verifier:
            if args.json:
                report = verifier.generate_verification_report()
                print(json.dumps(report, indent=2, default=str))
            else:
                verifier.print_verification_summary()

            if args.save:
                verifier.save_verification_report(args.output)

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
