#!/usr/bin/env python3
"""
Congress Members Data Verification Utility
Provides easy access to all verification queries, views, and procedures
"""

import argparse
import os
import sys
from typing import Any, Dict, List

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

load_dotenv()

class CongressDataVerifier:
    """Utility for verifying Congress members data"""

    def __init__(self):
        self.conn_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }
        self.conn = None

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.conn_params)
        self.conn.cursor_factory = DictCursor

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def run_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        with self.conn.cursor() as cursor:
            cursor.execute(query, params or ())
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def call_procedure(self, procedure_name: str, params: tuple = None):
        """Call a stored procedure"""
        with self.conn.cursor() as cursor:
            if params:
                param_str = ', '.join(['%s'] * len(params))
                cursor.execute(f"CALL {procedure_name}({param_str})", params)
            else:
                cursor.execute(f"CALL {procedure_name}()")

    # View-based queries
    def get_member_counts_by_congress(self) -> List[Dict[str, Any]]:
        """Get member counts by congress"""
        return self.run_query("SELECT * FROM congress.member_counts_by_congress ORDER BY congress_number")

    def get_longest_serving_members(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get longest serving members"""
        return self.run_query(f"SELECT * FROM congress.longest_serving_members LIMIT {limit}")

    def get_party_distribution_by_congress(self, congress: int = None) -> List[Dict[str, Any]]:
        """Get party distribution by congress"""
        if congress:
            return self.run_query(
                "SELECT * FROM congress.party_distribution_by_congress WHERE congress_number = %s ORDER BY member_count DESC",
                (congress,)
            )
        return self.run_query("SELECT * FROM congress.party_distribution_by_congress ORDER BY congress_number, member_count DESC")

    def get_chamber_distribution_by_congress(self, congress: int = None) -> List[Dict[str, Any]]:
        """Get chamber distribution by congress"""
        if congress:
            return self.run_query(
                "SELECT * FROM congress.chamber_distribution_by_congress WHERE congress_number = %s",
                (congress,)
            )
        return self.run_query("SELECT * FROM congress.chamber_distribution_by_congress ORDER BY congress_number")

    def get_state_representation_by_congress(self, congress: int = None) -> List[Dict[str, Any]]:
        """Get state representation by congress"""
        if congress:
            return self.run_query(
                "SELECT * FROM congress.state_representation_by_congress WHERE congress_number = %s ORDER BY member_count DESC",
                (congress,)
            )
        return self.run_query("SELECT * FROM congress.state_representation_by_congress ORDER BY congress_number, member_count DESC")

    def get_members_with_incomplete_data(self) -> List[Dict[str, Any]]:
        """Get members with incomplete data"""
        return self.run_query("SELECT * FROM congress.members_with_incomplete_data ORDER BY missing_field, last_name")

    def get_duplicate_member_terms(self) -> List[Dict[str, Any]]:
        """Get duplicate member terms"""
        return self.run_query("SELECT * FROM congress.duplicate_member_terms ORDER BY duplicate_count DESC")

    # Function calls
    def get_unique_member_count(self) -> int:
        """Get total unique member count"""
        result = self.run_query("SELECT congress.get_unique_member_count()")
        return result[0]['get_unique_member_count']

    def get_total_member_terms_count(self) -> int:
        """Get total member terms count"""
        result = self.run_query("SELECT congress.get_total_member_terms_count()")
        return result[0]['get_total_member_terms_count']

    def get_longest_serving_members_function(self, limit: int = 10):
        """Get longest serving members using function"""
        return self.run_query(f"SELECT * FROM congress.get_longest_serving_members({limit})")

    def get_party_distribution_function(self, congress: int):
        """Get party distribution using function"""
        return self.run_query(f"SELECT * FROM congress.get_party_distribution({congress})")

    def get_chamber_distribution_function(self, congress: int):
        """Get chamber distribution using function"""
        return self.run_query(f"SELECT * FROM congress.get_chamber_distribution({congress})")

    def get_state_representation_function(self, congress: int, chamber: str = None):
        """Get state representation using function"""
        if chamber:
            return self.run_query(f"SELECT * FROM congress.get_state_representation({congress}, '{chamber}')")
        return self.run_query(f"SELECT * FROM congress.get_state_representation({congress})")

    def check_member_data_completeness(self):
        """Check member data completeness"""
        return self.run_query("SELECT * FROM congress.check_member_data_completeness()")

    def get_member_career_path(self, bioguide_id: str):
        """Get member career path"""
        return self.run_query(f"SELECT * FROM congress.get_member_career_path('{bioguide_id}')")

    def get_congress_summary(self, congress: int):
        """Get congress summary statistics"""
        return self.run_query(f"SELECT * FROM congress.get_congress_summary({congress})")

    # Procedure calls
    def get_member_statistics(self, congress: int = None):
        """Get member statistics using procedure"""
        try:
            if congress:
                self.call_procedure('congress.get_member_statistics', (congress,))
            else:
                self.call_procedure('congress.get_member_statistics')
            print("✅ Member statistics retrieved (check notices)")
        except Exception as e:
            print(f"❌ Error getting member statistics: {e}")

    def check_data_quality(self):
        """Check data quality using procedure"""
        try:
            self.call_procedure('congress.check_data_quality')
            print("✅ Data quality check completed (check notices)")
        except Exception as e:
            print(f"❌ Error checking data quality: {e}")

    def clean_duplicate_terms(self):
        """Clean duplicate terms using procedure"""
        try:
            self.call_procedure('congress.clean_duplicate_terms')
            print("✅ Duplicate terms cleaned (check notices)")
        except Exception as e:
            print(f"❌ Error cleaning duplicate terms: {e}")

    def get_member_career_summary(self, bioguide_id: str):
        """Get member career summary using procedure"""
        try:
            self.call_procedure('congress.get_member_career_summary', (bioguide_id,))
            print(f"✅ Career summary for {bioguide_id} (check notices)")
        except Exception as e:
            print(f"❌ Error getting career summary: {e}")

    def print_report(self, title: str, data: List[Dict[str, Any]], max_rows: int = 20):
        """Print a formatted report"""
        if not data:
            print(f"No data found for {title}")
            return

        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")

        # Print headers
        headers = list(data[0].keys())
        header_row = " | ".join(f"{h:15}" for h in headers)
        print(header_row)
        print("-" * len(header_row))

        # Print data
        for i, row in enumerate(data[:max_rows]):
            data_row = " | ".join(f"{str(row[h]):15}" for h in headers)
            print(data_row)

        if len(data) > max_rows:
            print(f"... and {len(data) - max_rows} more rows")

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="Congress Members Data Verification Utility")
    parser.add_argument('--congress', type=int, help='Filter by specific congress number')
    parser.add_argument('--bioguide', type=str, help='Get career path for specific bioguide ID')
    parser.add_argument('--check-quality', action='store_true', help='Run data quality check')
    parser.add_argument('--clean-duplicates', action='store_true', help='Clean duplicate terms')
    parser.add_argument('--stats', action='store_true', help='Show member statistics')
    parser.add_argument('--summary', type=int, help='Show congress summary for specific congress')

    args = parser.parse_args()

    verifier = CongressDataVerifier()

    try:
        verifier.connect()

        if args.check_quality:
            verifier.check_data_quality()

        if args.clean_duplicates:
            verifier.clean_duplicate_terms()

        if args.stats:
            verifier.get_member_statistics(args.congress)

        if args.summary:
            data = verifier.get_congress_summary(args.summary)
            verifier.print_report(f"Congress {args.summary} Summary", data)

        if args.bioguide:
            data = verifier.get_member_career_path(args.bioguide)
            verifier.print_report(f"Career Path: {args.bioguide}", data)
            verifier.get_member_career_summary(args.bioguide)

        # Default reports
        if not any([args.check_quality, args.clean_duplicates, args.stats, args.summary, args.bioguide]):
            # Member counts by congress
            data = verifier.get_member_counts_by_congress()
            verifier.print_report("Member Counts by Congress", data)

            # Longest serving members
            data = verifier.get_longest_serving_members()
            verifier.print_report("Longest Serving Members", data)

            # Data completeness
            data = verifier.check_member_data_completeness()
            verifier.print_report("Data Completeness Check", data)

            # Overall statistics
            unique_count = verifier.get_unique_member_count()
            terms_count = verifier.get_total_member_terms_count()
            print(f"\n{'='*60}")
            print(" Overall Statistics")
            print(f"{'='*60}")
            print(f"Total Unique Members: {unique_count}")
            print(f"Total Member Terms: {terms_count}")
            print(f"Average Terms per Member: {terms_count/unique_count:.2f}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        verifier.close()

if __name__ == "__main__":
    main()
