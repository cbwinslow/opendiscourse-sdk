#!/usr/bin/env python3
"""
Data Status Diagnostic Queries

This script provides comprehensive queries to paint a full picture of the data
ingestion status, what's been ingested, and what's left to process.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import DictCursor

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion_config import validate_all_api_keys, get_ingestion_mode_from_env

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class DataStatusDiagnostics:
    """Comprehensive data status diagnostics"""

    def __init__(self):
        self.conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)
        self.report_data = {}
        self.generated_at = datetime.now().isoformat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up database connections"""
        if hasattr(self, 'cursor'):
            self.cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        try:
            # Use a fresh connection for each query to avoid transaction issues
            fresh_conn = psycopg2.connect(database='cbwinslow', user='cbwinslow')
            fresh_cursor = fresh_conn.cursor(cursor_factory=DictCursor)

            # Set autocommit to avoid transaction issues
            fresh_conn.autocommit = True

            if params:
                fresh_cursor.execute(query, params)
            else:
                fresh_cursor.execute(query)

            columns = [desc[0] for desc in fresh_cursor.description]
            results = []

            for row in fresh_cursor.fetchall():
                result_dict = dict(zip(columns, row))
                # Convert datetime objects to strings for JSON serialization
                for key, value in result_dict.items():
                    if isinstance(value, datetime):
                        result_dict[key] = value.isoformat()
                    elif isinstance(value, timedelta):
                        result_dict[key] = str(value)
                results.append(result_dict)

            fresh_cursor.close()
            fresh_conn.close()
            return results

        except Exception as e:
            print(f"Error executing query: {e}")
            print(f"Query: {query}")
            return []

    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall ingestion status"""
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

        results = self.execute_query(query)

        # Calculate overall statistics
        total_records = sum(r['total_processed'] or 0 for r in results)
        total_estimated = sum(r['total_estimated'] or 0 for r in results if r['total_estimated'])
        completed_items = sum(1 for r in results if r['is_completed'])
        total_items = len(results)

        return {
            'summary': {
                'total_records_processed': total_records,
                'total_estimated_records': total_estimated,
                'overall_completion_percentage': (total_records / total_estimated * 100) if total_estimated > 0 else 0,
                'completed_items': completed_items,
                'total_items': total_items,
                'items_completion_percentage': (completed_items / total_items * 100) if total_items > 0 else 0
            },
            'details': results
        }

    def get_congress_data_status(self) -> Dict[str, Any]:
        """Get detailed Congress data status"""
        queries = {
            'members_by_congress': """
                SELECT
                    'congress' as source,
                    'members' as data_type,
                    mt.congress_number::text as category,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT m.bioguide_id) as unique_records,
                    MIN(m.created_at) as first_ingested,
                    MAX(m.created_at) as last_ingested,
                    COUNT(CASE WHEN m.updated_at > m.created_at THEN 1 END) as updated_records
                FROM congress.members m
                JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id
                WHERE mt.congress_number IN (116, 117, 118)
                GROUP BY mt.congress_number::text

                UNION ALL

                SELECT
                    'congress' as source,
                    'bills' as data_type,
                    congress_number::text as category,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT bill_id) as unique_records,
                    MIN(created_at) as first_ingested,
                    MAX(created_at) as last_ingested,
                    COUNT(CASE WHEN updated_at > created_at THEN 1 END) as updated_records
                FROM congress.bills
                WHERE congress_number IN (117, 118)
                GROUP BY congress_number::text

                ORDER BY source, data_type, category
            """,

            'summary_counts': """
                SELECT
                    'members' as table_name,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT bioguide_id) as unique_members,
                    MIN(created_at) as first_ingested,
                    MAX(created_at) as last_ingested
                FROM congress.members

                UNION ALL

                SELECT
                    'bills' as table_name,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT bill_id) as unique_bills,
                    MIN(created_at) as first_ingested,
                    MAX(created_at) as last_ingested
                FROM congress.bills
            """
        }

        results = {}
        for key, query in queries.items():
            results[key] = self.execute_query(query)

        return results

    def get_database_schema_status(self) -> Dict[str, Any]:
        """Get database schema and table status"""
        query = """
            SELECT
                table_schema,
                table_name,
                table_type,
                (SELECT COUNT(*) FROM information_schema.columns
                 WHERE table_schema = tables.table_schema AND table_name = tables.table_name) as column_count
            FROM information_schema.tables tables
            WHERE table_schema IN ('congress', 'incremental')
            ORDER BY table_schema, table_name
        """

        tables = self.execute_query(query)

        # Get record counts for each table
        table_counts = {}
        for table in tables:
            if table['table_type'] == 'BASE TABLE':
                count_query = f"SELECT COUNT(*) as record_count FROM {table['table_schema']}.{table['table_name']}"
                count_result = self.execute_query(count_query)
                table_counts[table['table_name']] = count_result[0]['record_count'] if count_result else 0

        return {
            'schema_info': tables,
            'table_counts': table_counts
        }

    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality and integrity metrics"""
        queries = {
            'duplicate_analysis': """
                SELECT
                    'members' as table_name,
                    'bioguide_id' as column_name,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT bioguide_id) as unique_fingerprints,
                    COUNT(*) - COUNT(DISTINCT bioguide_id) as duplicate_count,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            (COUNT(*) - COUNT(DISTINCT bioguide_id)) * 100.0 / COUNT(*)
                        ELSE 0
                    END as duplicate_percentage
                FROM congress.members
                WHERE bioguide_id IS NOT NULL

                UNION ALL

                SELECT
                    'bills' as table_name,
                    'bill_id' as column_name,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT bill_id) as unique_fingerprints,
                    COUNT(*) - COUNT(DISTINCT bill_id) as duplicate_count,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            (COUNT(*) - COUNT(DISTINCT bill_id)) * 100.0 / COUNT(*)
                        ELSE 0
                    END as duplicate_percentage
                FROM congress.bills
                WHERE bill_id IS NOT NULL
                ORDER BY duplicate_count DESC
            """,

            'data_completeness': """
                SELECT
                    'members' as table_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN bioguide_id IS NOT NULL THEN 1 END) as has_bioguide_id,
                    COUNT(CASE WHEN official_full_name IS NOT NULL THEN 1 END) as has_full_name,
                    COUNT(CASE WHEN birthday IS NOT NULL THEN 1 END) as has_birthday,
                    COUNT(CASE WHEN gender IS NOT NULL THEN 1 END) as has_gender
                FROM congress.members

                UNION ALL

                SELECT
                    'bills' as table_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN bill_id IS NOT NULL THEN 1 END) as has_bill_id,
                    COUNT(CASE WHEN official_title IS NOT NULL THEN 1 END) as has_title,
                    COUNT(CASE WHEN bill_type IS NOT NULL THEN 1 END) as has_bill_type,
                    COUNT(CASE WHEN congress_number IS NOT NULL THEN 1 END) as has_congress
                FROM congress.bills
                ORDER BY table_name
            """,

            'recent_activity': """
                SELECT
                    DATE_TRUNC('hour', created_at) as hour_bucket,
                    COUNT(*) as records_created,
                    COUNT(CASE WHEN updated_at > created_at THEN 1 END) as records_updated
                FROM (
                    SELECT created_at, updated_at FROM congress.members
                    UNION ALL
                    SELECT created_at, updated_at FROM congress.bills
                ) all_records
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY hour_bucket
                ORDER BY hour_bucket DESC
                LIMIT 24
            """
        }

        results = {}
        for key, query in queries.items():
            results[key] = self.execute_query(query)

        return results

    def get_api_usage_metrics(self) -> Dict[str, Any]:
        """Get API usage and performance metrics"""
        # This would typically come from monitoring logs
        # For now, we'll provide a placeholder structure
        return {
            'api_usage': {
                'congress_gov': {
                    'total_requests': 'N/A',
                    'rate_limit_hits': 'N/A',
                    'average_response_time': 'N/A',
                    'last_request': 'N/A'
                },
                'govinfo_gov': {
                    'total_requests': 'N/A',
                    'rate_limit_hits': 'N/A',
                    'average_response_time': 'N/A',
                    'last_request': 'N/A'
                },
                'openstates_org': {
                    'total_requests': 'N/A',
                    'rate_limit_hits': 'N/A',
                    'average_response_time': 'N/A',
                    'last_request': 'N/A'
                }
            }
        }

    def get_ingestion_progress_details(self) -> Dict[str, Any]:
        """Get detailed ingestion progress by data source"""
        queries = {
            'congress_progress': """
                SELECT
                    'congress.gov' as data_source,
                    'members' as data_type,
                    mt.congress_number::text as category,
                    COUNT(*) as total_processed,
                    CASE mt.congress_number
                        WHEN 116 THEN 440
                        WHEN 117 THEN 550
                        WHEN 118 THEN 550
                        ELSE 0
                    END as expected_total,
                    CASE
                        WHEN mt.congress_number IN (116, 117, 118) THEN
                            COUNT(*) * 100.0 / CASE mt.congress_number
                                WHEN 116 THEN 440
                                WHEN 117 THEN 550
                                WHEN 118 THEN 550
                                ELSE 1
                            END
                        ELSE 0
                    END as completion_percentage,
                    MAX(m.created_at) as last_ingestion
                FROM congress.members m
                JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id
                GROUP BY mt.congress_number

                UNION ALL

                SELECT
                    'congress.gov' as data_source,
                    'bills' as data_type,
                    congress_number::text as category,
                    COUNT(*) as total_processed,
                    NULL as expected_total,
                    NULL as completion_percentage,
                    MAX(created_at) as last_ingestion
                FROM congress.bills
                GROUP BY congress_number
                ORDER BY data_source, data_type, category
            """,

            'timeline_summary': """
                SELECT
                    DATE(created_at) as ingestion_date,
                    COUNT(*) as records_ingested,
                    COUNT(DISTINCT 'members') as data_types_count
                FROM (
                    SELECT created_at, 'members' as type FROM congress.members
                    UNION ALL
                    SELECT created_at, 'bills' as type FROM congress.bills
                ) combined
                GROUP BY DATE(created_at)
                ORDER BY ingestion_date DESC
                LIMIT 30
            """
        }

        results = {}
        for key, query in queries.items():
            results[key] = self.execute_query(query)

        return results

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive data status report"""
        print("🔍 Generating comprehensive data status report...")

        # Validate API keys first
        api_validation = validate_all_api_keys()

        # Get all diagnostic data
        report = {
            'generated_at': self.generated_at,
            'api_key_status': api_validation,
            'ingestion_mode': get_ingestion_mode_from_env().value,
            'overall_status': self.get_overall_status(),
            'congress_data_status': self.get_congress_data_status(),
            'database_schema_status': self.get_database_schema_status(),
            'data_quality_metrics': self.get_data_quality_metrics(),
            'api_usage_metrics': self.get_api_usage_metrics(),
            'ingestion_progress_details': self.get_ingestion_progress_details()
        }

        return report

    def save_report(self, filename: str = None) -> str:
        """Save report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data_status_report_{timestamp}.json"

        report = self.generate_comprehensive_report()

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"📄 Report saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return ""

    def print_summary(self):
        """Print a concise summary of the data status"""
        report = self.generate_comprehensive_report()

        print("\\n" + "="*60)
        print("📊 DATA STATUS SUMMARY")
        print("="*60)

        # API Status
        api_status = report['api_key_status']
        print(f"🔑 API Keys: {'✅ Valid' if api_status['valid'] else '❌ Invalid'}")
        print(f"🚀 Mode: {report['ingestion_mode']}")

        # Overall Status
        overall = report['overall_status']['summary']
        print(f"📈 Records Processed: {overall['total_records_processed']:,}")
        print(f"🎯 Estimated Total: {overall['total_estimated_records']:,}")
        print(f"📊 Overall Completion: {overall['overall_completion_percentage']:.1f}%")
        print(f"✅ Items Completed: {overall['completed_items']}/{overall['total_items']}")

        # Congress Data
        congress_data = report['congress_data_status']
        print("\\n🏛️  Congress Data:")

        # Show members by congress
        if 'members_by_congress' in congress_data:
            for item in congress_data['members_by_congress']:
                status_icon = "✅" if item['total_records'] > 0 else "❌"
                print(f"  {status_icon} {item['source'].title()} {item['data_type'].title()} {item['category']}: {item['total_records']:,} records")

        # Show summary counts
        if 'summary_counts' in congress_data:
            for item in congress_data['summary_counts']:
                status_icon = "✅" if item['total_records'] > 0 else "❌"
                print(f"  {status_icon} {item['table_name'].title()}: {item['total_records']:,} total records")

        # Data Quality
        quality = report['data_quality_metrics']
        if quality['duplicate_analysis']:
            print("\\n🔍 Data Quality:")
            for item in quality['duplicate_analysis']:
                if item['duplicate_count'] > 0:
                    print(f"  ⚠️  {item['table_name']}: {item['duplicate_count']} duplicates ({item['duplicate_percentage']:.1f}%)")
                else:
                    print(f"  ✅ {item['table_name']}: No duplicates")

        print("="*60)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate comprehensive data status report')
    parser.add_argument('--output', '-o', help='Output filename (default: auto-generated)')
    parser.add_argument('--summary', '-s', action='store_true', help='Print summary only')
    parser.add_argument('--save', action='store_true', help='Save report to file')

    args = parser.parse_args()

    try:
        with DataStatusDiagnostics() as diagnostics:
            if args.summary:
                diagnostics.print_summary()
            else:
                if args.save:
                    filename = diagnostics.save_report(args.output)
                    print(f"📄 Full report saved to: {filename}")
                else:
                    report = diagnostics.generate_comprehensive_report()
                    print(json.dumps(report, indent=2, default=str))

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
