#!/usr/bin/env python3
"""
Members Data Deduplication Analysis and Setup
Analyzes and sets up proper deduplication strategy across all data sources
"""

import os
import sys
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import argparse
from typing import Dict, List, Any

load_dotenv()

class MembersDeduplicationAnalyzer:
    """Analyzes and manages deduplication across member data sources"""

    def __init__(self):
        self.db_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.db_params)
        self.conn.cursor_factory = DictCursor

    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def analyze_current_data(self):
        """Analyze current member data across all schemas"""
        print("🔍 Analyzing current member data across all schemas...")

        with self.conn.cursor() as cursor:
            # Congress members
            cursor.execute("SELECT COUNT(*) as count FROM congress.members")
            congress_count = cursor.fetchone()['count']

            # GovInfo members
            cursor.execute("SELECT COUNT(*) as count FROM govinfo.members")
            govinfo_count = cursor.fetchone()['count']

            # OpenStates people
            cursor.execute("SELECT COUNT(*) as count FROM openstates.people")
            openstates_count = cursor.fetchone()['count']

            print(f"\n📊 Current Data Status:")
            print(f"   Congress members: {congress_count}")
            print(f"   GovInfo members: {govinfo_count}")
            print(f"   OpenStates people: {openstates_count}")

            # Analyze bioguide_id overlap
            cursor.execute("""
                SELECT
                    COUNT(*) as total_congress,
                    COUNT(bioguide_id) as with_bioguide_id,
                    COUNT(DISTINCT bioguide_id) as unique_bioguide_ids
                FROM congress.members
            """)
            congress_bioguide = cursor.fetchone()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_govinfo,
                    COUNT(bioguide_id) as with_bioguide_id,
                    COUNT(DISTINCT bioguide_id) as unique_bioguide_ids
                FROM govinfo.members
            """)
            govinfo_bioguide = cursor.fetchone()

            print(f"\n🔗 Bioguide ID Analysis:")
            print(f"   Congress: {congress_bioguide['with_bioguide_id']}/{congress_bioguide['total_congress']} have bioguide_id")
            print(f"   GovInfo: {govinfo_bioguide['with_bioguide_id']}/{govinfo_bioguide['total_govinfo']} have bioguide_id")

            # Check for potential overlaps
            if congress_bioguide['with_bioguide_id'] > 0 and govinfo_bioguide['with_bioguide_id'] > 0:
                cursor.execute("""
                    SELECT COUNT(*) as overlap_count
                    FROM congress.members cm
                    JOIN govinfo.members gm ON cm.bioguide_id = gm.bioguide_id
                    WHERE cm.bioguide_id IS NOT NULL AND gm.bioguide_id IS NOT NULL
                """)
                overlap = cursor.fetchone()['overlap_count']
                print(f"   Potential bioguide_id overlap: {overlap}")

    def analyze_deduplication_strategy(self):
        """Analyze the current deduplication strategy"""
        print(f"\n🎯 Deduplication Strategy Analysis:")

        with self.conn.cursor() as cursor:
            # Check primary keys and constraints
            schemas = ['congress', 'govinfo', 'openstates']
            tables = ['members', 'members', 'people']

            for schema, table in zip(schemas, tables):
                cursor.execute(f"""
                    SELECT
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = '{schema}'
                        AND tc.table_name = '{table}'
                        AND tc.constraint_type = 'PRIMARY KEY'
                """)
                pks = cursor.fetchall()

                cursor.execute(f"""
                    SELECT
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = '{schema}'
                        AND tc.table_name = '{table}'
                        AND tc.constraint_type = 'UNIQUE'
                """)
                uniques = cursor.fetchall()

                print(f"\n   {schema}.{table}:")
                print(f"     Primary Key: {[pk['column_name'] for pk in pks]}")
                print(f"     Unique Constraints: {[uk['column_name'] for uk in uniques]}")

        print(f"\n💡 Deduplication Strategy:")
        print(f"   • Congress: Uses bioguide_id as primary key (unique per person)")
        print(f"   • GovInfo: Uses member_id as primary key, bioguide_id unique constraint")
        print(f"   • OpenStates: Uses person_id as primary key (different identifier system)")
        print(f"   • These are SEPARATE data sources with different identifier systems")
        print(f"   • Deduplication should be maintained WITHIN each source")
        print(f"   • Cross-source matching would require additional mapping tables")

    def setup_reference_data(self):
        """Set up reference data for all schemas"""
        print(f"\n🔧 Setting up reference data...")

        with self.conn.cursor() as cursor:
            # Check GovInfo parties
            cursor.execute("SELECT COUNT(*) as count FROM govinfo.parties")
            govinfo_parties = cursor.fetchone()['count']

            if govinfo_parties == 0:
                print("   Setting up GovInfo parties...")
                cursor.execute("""
                    INSERT INTO govinfo.parties (party_code, party_name) VALUES
                    ('D', 'Democratic Party'),
                    ('R', 'Republican Party'),
                    ('I', 'Independent'),
                    ('L', 'Libertarian Party'),
                    ('G', 'Green Party'),
                    ('O', 'Other')
                """)
                print(f"   ✅ Created {cursor.rowcount} party records for GovInfo")
            else:
                print(f"   ✅ GovInfo parties already exist ({govinfo_parties} records)")

            # Check OpenStates jurisdictions
            cursor.execute("SELECT COUNT(*) as count FROM openstates.jurisdictions")
            jurisdictions = cursor.fetchone()['count']

            if jurisdictions == 0:
                print("   Setting up OpenStates jurisdictions (sample)...")
                cursor.execute("""
                    INSERT INTO openstates.jurisdictions (jurisdiction_id, name, classification, state_code) VALUES
                    ('ocd-jurisdiction/country:us/state:ca/government', 'California', 'state', 'ca'),
                    ('ocd-jurisdiction/country:us/state:ny/government', 'New York', 'state', 'ny'),
                    ('ocd-jurisdiction/country:us/state:tx/government', 'Texas', 'state', 'tx'),
                    ('ocd-jurisdiction/country:us/state:fl/government', 'Florida', 'state', 'fl'),
                    ('ocd-jurisdiction/country:us/government', 'United States', 'country', 'us')
                """)
                print(f"   ✅ Created {cursor.rowcount} jurisdiction records for OpenStates")
            else:
                print(f"   ✅ OpenStates jurisdictions already exist ({jurisdictions} records)")

        self.conn.commit()

    def create_cross_reference_view(self):
        """Create a view for cross-reference analysis"""
        print(f"\n🔗 Creating cross-reference analysis view...")

        with self.conn.cursor() as cursor:
            cursor.execute("""
                DROP VIEW IF EXISTS analysis.members_cross_reference;

                CREATE VIEW analysis.members_cross_reference AS
                SELECT
                    'congress' as source_schema,
                    cm.bioguide_id as source_id,
                    cm.first_name,
                    cm.last_name,
                    cm.official_full_name,
                    NULL as cross_reference_id,
                    NULL as cross_reference_schema
                FROM congress.members cm

                UNION ALL

                SELECT
                    'govinfo' as source_schema,
                    gm.member_id as source_id,
                    gm.first_name,
                    gm.last_name,
                    gm.full_name,
                    gm.bioguide_id as cross_reference_id,
                    CASE WHEN gm.bioguide_id IS NOT NULL THEN 'congress' ELSE NULL END as cross_reference_schema
                FROM govinfo.members gm

                UNION ALL

                SELECT
                    'openstates' as source_schema,
                    os.person_id as source_id,
                    os.given_name as first_name,
                    os.family_name as last_name,
                    os.name,
                    NULL as cross_reference_id,
                    NULL as cross_reference_schema
                FROM openstates.people os;
            """)

            print("   ✅ Created analysis.members_cross_reference view")

        self.conn.commit()

    def validate_deduplication(self):
        """Validate that deduplication is working correctly"""
        print(f"\n✅ Validating deduplication...")

        with self.conn.cursor() as cursor:
            # Check for duplicates in Congress
            cursor.execute("""
                SELECT bioguide_id, COUNT(*) as count
                FROM congress.members
                GROUP BY bioguide_id
                HAVING COUNT(*) > 1
            """)
            congress_duplicates = cursor.fetchall()

            # Check for duplicates in GovInfo
            cursor.execute("""
                SELECT member_id, COUNT(*) as count
                FROM govinfo.members
                GROUP BY member_id
                HAVING COUNT(*) > 1
            """)
            govinfo_duplicates = cursor.fetchall()

            # Check for bioguide_id duplicates in GovInfo
            cursor.execute("""
                SELECT bioguide_id, COUNT(*) as count
                FROM govinfo.members
                WHERE bioguide_id IS NOT NULL
                GROUP BY bioguide_id
                HAVING COUNT(*) > 1
            """)
            govinfo_bioguide_duplicates = cursor.fetchall()

            # Check for duplicates in OpenStates
            cursor.execute("""
                SELECT person_id, COUNT(*) as count
                FROM openstates.people
                GROUP BY person_id
                HAVING COUNT(*) > 1
            """)
            openstates_duplicates = cursor.fetchall()

            print(f"   Congress duplicate bioguide_ids: {len(congress_duplicates)}")
            print(f"   GovInfo duplicate member_ids: {len(govinfo_duplicates)}")
            print(f"   GovInfo duplicate bioguide_ids: {len(govinfo_bioguide_duplicates)}")
            print(f"   OpenStates duplicate person_ids: {len(openstates_duplicates)}")

            if len(congress_duplicates) == 0 and len(govinfo_duplicates) == 0 and len(govinfo_bioguide_duplicates) == 0 and len(openstates_duplicates) == 0:
                print("   ✅ No duplicates found - deduplication working correctly!")
                return True
            else:
                print("   ⚠️  Duplicates found - may need cleanup")
                return False

    def generate_report(self):
        """Generate a comprehensive deduplication report"""
        print(f"\n📋 Generating deduplication report...")

        with self.conn.cursor() as cursor:
            # Summary statistics
            cursor.execute("""
                SELECT
                    'congress' as schema_name,
                    COUNT(*) as total_records,
                    COUNT(bioguide_id) as with_identifier,
                    COUNT(DISTINCT bioguide_id) as unique_identifiers
                FROM congress.members

                UNION ALL

                SELECT
                    'govinfo' as schema_name,
                    COUNT(*) as total_records,
                    COUNT(bioguide_id) as with_identifier,
                    COUNT(DISTINCT bioguide_id) as unique_identifiers
                FROM govinfo.members

                UNION ALL

                SELECT
                    'openstates' as schema_name,
                    COUNT(*) as total_records,
                    COUNT(person_id) as with_identifier,
                    COUNT(DISTINCT person_id) as unique_identifiers
                FROM openstates.people
                ORDER BY schema_name
            """)

            results = cursor.fetchall()

            print(f"\n📊 Deduplication Summary Report:")
            print(f"{'Schema':<12} {'Total':<8} {'With ID':<10} {'Unique ID':<11}")
            print(f"{'-'*45}")

            for row in results:
                print(f"{row['schema_name']:<12} {row['total_records']:<8} {row['with_identifier']:<10} {row['unique_identifiers']:<11}")

            # Cross-reference analysis
            cursor.execute("""
                SELECT
                    source_schema,
                    COUNT(*) as total_records,
                    COUNT(cross_reference_id) as with_cross_ref
                FROM analysis.members_cross_reference
                GROUP BY source_schema
                ORDER BY source_schema
            """)

            cross_ref = cursor.fetchall()

            print(f"\n🔗 Cross-Reference Analysis:")
            for row in cross_ref:
                print(f"   {row['source_schema']}: {row['with_cross_ref']}/{row['total_records']} have cross-references")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze and setup members data deduplication")
    parser.add_argument('--setup', action='store_true', help='Set up reference data and views')
    parser.add_argument('--validate', action='store_true', help='Validate deduplication')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--all', action='store_true', help='Run all analysis steps')

    args = parser.parse_args()

    analyzer = MembersDeduplicationAnalyzer()

    try:
        analyzer.connect()

        if args.all or not any([args.setup, args.validate, args.report]):
            # Run full analysis
            analyzer.analyze_current_data()
            analyzer.analyze_deduplication_strategy()
            analyzer.setup_reference_data()
            analyzer.create_cross_reference_view()
            analyzer.validate_deduplication()
            analyzer.generate_report()
        else:
            if args.setup:
                analyzer.setup_reference_data()
                analyzer.create_cross_reference_view()

            if args.validate:
                analyzer.validate_deduplication()

            if args.report:
                analyzer.generate_report()

        print(f"\n🎉 Deduplication analysis completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
