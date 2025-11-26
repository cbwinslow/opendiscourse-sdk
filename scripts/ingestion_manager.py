#!/usr/bin/env python3
"""
Incremental Ingestion Manager
Orchestrates incremental ingestion across all data sources with checkpoint tracking
"""

import os
import sys
import json
import argparse
import psycopg2
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest_congress_incremental import IncrementalCongressIngestor
from ingest_openstates_incremental import IncrementalOpenStatesIngestor
from ingest_govinfo_incremental import IncrementalGovInfoIngestor
from ingest_congress_bills_incremental import IncrementalCongressBillsIngestor
from ingest_openstates_bills_incremental import IncrementalOpenStatesBillsIngestor
from ingest_govinfo_bills_incremental import IncrementalGovInfoBillsIngestor

class IncrementalIngestionManager:
    """Manages incremental ingestion across all data sources"""

    def __init__(self):
        self.db_conn = psycopg2.connect(
            database='cbwinslow',
            user='cbwinslow'
        )

        # Initialize ingestors
        self.congress_ingestor = IncrementalCongressIngestor()
        self.openstates_ingestor = IncrementalOpenStatesIngestor()
        self.govinfo_ingestor = IncrementalGovInfoIngestor()

        # Initialize bills ingestors
        self.congress_bills_ingestor = IncrementalCongressBillsIngestor()
        self.openstates_bills_ingestor = IncrementalOpenStatesBillsIngestor()
        self.govinfo_bills_ingestor = IncrementalGovInfoBillsIngestor()

    def get_all_checkpoint_status(self):
        """Get comprehensive checkpoint status across all sources"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM incremental.checkpoint_status
                ORDER BY data_source, data_type, category
            """)

            checkpoints = cursor.fetchall()

            print("\n🎯 COMPREHENSIVE INGESTION STATUS")
            print("=" * 100)
            print(f"{'Data Source':<15} {'Type':<10} {'Category':<15} {'Status':<12} {'Progress':<8} {'Processed':<10} {'Last Run':<20}")
            print("-" * 100)

            for cp in checkpoints:
                progress = f"{cp[8]:.1f}%" if cp[8] is not None else "N/A"
                processed = str(cp[7]) if cp[7] is not None else "0"
                last_run = str(cp[9]) if cp[9] is not None else "Never"
                print(f"{cp[0]:<15} {cp[1]:<10} {cp[2]:<15} {cp[11]:<12} {progress:<8} {processed:<10} {last_run:<20}")

            return checkpoints
        finally:
            cursor.close()

    def get_session_summary(self):
        """Get summary of recent ingestion sessions"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM incremental.session_summary
                ORDER BY started_at DESC
                LIMIT 10
            """)

            sessions = cursor.fetchall()

            print("\n📊 RECENT INGESTION SESSIONS")
            print("=" * 80)
            print(f"{'Session ID':<30} {'Source':<12} {'Status':<10} {'Duration':<10} {'Success Rate':<12}")
            print("-" * 80)

            for session in sessions:
                session_id = session[0][:27] + "..." if len(session[0]) > 30 else session[0]
                duration = session[3] if session[3] is not None else 0
                success_rate = session[8] if session[8] is not None else 0.0
                print(f"{session_id:<30} {session[1]:<12} {session[2]:<10} {duration:<10.1f}m {success_rate:<12.1f}%")

            return sessions
        finally:
            cursor.close()

    def reset_checkpoint(self, data_source: str, data_type: str, category: str):
        """Reset a specific checkpoint"""
        cursor = self.db_conn.cursor()

        try:
            cursor.execute("""
                CALL incremental.reset_checkpoint(%s, %s, %s)
            """, (data_source, data_type, category))

            self.db_conn.commit()
            print(f"✅ Reset checkpoint for {data_source}.{data_type}.{category}")
        except Exception as e:
            self.db_conn.rollback()
            print(f"❌ Failed to reset checkpoint: {e}")
        finally:
            cursor.close()

    def ingest_congress_data(self, congress_range: str = None):
        """Ingest Congress data incrementally"""
        if congress_range:
            start, end = map(int, congress_range.split('-'))
        else:
            start, end = 118, 118  # Default to current congress

        print(f"\n🏛️  INGESTING CONGRESS DATA (Congresses {start}-{end})")
        print("=" * 60)

        results = self.congress_ingestor.ingest_all_congresses(start, end)

        # Update overall progress
        self.update_overall_progress('congress.gov', 'members', results)

        return results

    def ingest_openstates_data(self, jurisdictions: List[str] = None):
        """Ingest OpenStates data incrementally"""
        if not jurisdictions:
            jurisdictions = ['ca', 'tx', 'ny', 'fl', 'pa', 'il', 'oh', 'ga', 'nc', 'mi']

        print(f"\n🏛️  INGESTING OPENSTATES DATA ({len(jurisdictions)} jurisdictions)")
        print("=" * 60)

        results = self.openstates_ingestor.ingest_all_jurisdictions(jurisdictions)

        # Update overall progress
        self.update_overall_progress('openstates.org', 'people', results)

        return results

    def ingest_govinfo_data(self, congress_range: str = None):
        """Ingest GovInfo data incrementally"""
        if congress_range:
            start, end = map(int, congress_range.split('-'))
        else:
            start, end = 118, 118  # Default to current congress

        print(f"\n📚 INGESTING GOVINFO DATA (Congresses {start}-{end})")
        print("=" * 60)

        results = self.govinfo_ingestor.ingest_all_congresses(start, end)

        # Update overall progress
        self.update_overall_progress('govinfo.gov', 'members', results)

        return results

    def ingest_congress_bills(self, congress_range: str = None):
        """Ingest Congress bills incrementally"""
        if congress_range:
            start, end = map(int, congress_range.split('-'))
        else:
            start, end = 118, 118  # Default to current congress

        print(f"\n🏛️ INGESTING CONGRESS BILLS (Congresses {start}-{end})")
        print("=" * 60)

        results = self.congress_bills_ingestor.ingest_all_congresses(start, end)

        # Update overall progress
        self.update_overall_progress('congress.gov', 'bills', results)

        return results

    def ingest_openstates_bills(self, jurisdictions: List[str] = None):
        """Ingest OpenStates bills incrementally"""
        if jurisdictions is None:
            jurisdictions = ['ca', 'tx', 'fl', 'ny', 'pa']  # Default to major states

        print(f"\n🏛️ INGESTING OPENSTATES BILLS ({len(jurisdictions)} jurisdictions)")
        print("=" * 60)

        results = self.openstates_bills_ingestor.ingest_all_jurisdictions(jurisdictions)

        # Update overall progress
        self.update_overall_progress('openstates.org', 'bills', results)

        return results

    def ingest_govinfo_bills(self, congress_range: str = None):
        """Ingest GovInfo bills incrementally"""
        if congress_range:
            start, end = map(int, congress_range.split('-'))
        else:
            start, end = 118, 118  # Default to current congress

        print(f"\n📚 INGESTING GOVINFO BILLS (Congresses {start}-{end})")
        print("=" * 60)

        results = self.govinfo_bills_ingestor.ingest_all_congresses(start, end)

        # Update overall progress
        self.update_overall_progress('govinfo.gov', 'bills', results)

        return results

    def update_overall_progress(self, data_source: str, data_type: str, results: List[Dict[str, Any]]):
        """Update overall progress tracking"""
        cursor = self.db_conn.cursor()

        try:
            total_processed = sum(r.get('records_processed', 0) for r in results)
            total_skipped = sum(r.get('records_skipped', 0) for r in results)
            total_failed = sum(1 for r in results if r.get('status') == 'failed')

            # Create summary record
            summary_data = {
                'data_source': data_source,
                'data_type': data_type,
                'total_processed': total_processed,
                'total_skipped': total_skipped,
                'total_failed': total_failed,
                'completed_at': datetime.now().isoformat(),
                'results': results
            }

            # Store in a summary table or log
            cursor.execute("""
                INSERT INTO ingestion.ingestion_jobs (
                    job_name, data_source, table_name, record_type,
                    processed_records, failed_records, status, metadata
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s::jsonb
                )
            """, (
                f"incremental_{data_source}_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                data_source, data_type, data_type,
                total_processed, total_failed, 'completed',
                json.dumps(summary_data)
            ))

            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            print(f"⚠️ Failed to update overall progress: {e}")
        finally:
            cursor.close()

    def run_full_incremental_ingestion(self, congress_range: str = None, jurisdictions: List[str] = None):
        """Run complete incremental ingestion across all sources"""
        print("\n🚀 STARTING FULL INCREMENTAL INGESTION")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Show current status
        self.get_all_checkpoint_status()

        all_results = {}

        try:
            # Ingest Congress data
            all_results['congress'] = self.ingest_congress_data(congress_range)

            # Ingest OpenStates data
            all_results['openstates'] = self.ingest_openstates_data(jurisdictions)

            # Ingest GovInfo data
            all_results['govinfo'] = self.ingest_govinfo_data(congress_range)

            # Final status
            print("\n🎉 FULL INGESTION COMPLETED")
            print("=" * 60)
            self.get_all_checkpoint_status()

            # Generate summary report
            self.generate_summary_report(all_results)

        except Exception as e:
            print(f"\n❌ INGESTION FAILED: {e}")
            raise

    def run_full_bills_ingestion(self, congress_range: str = None, jurisdictions: List[str] = None):
        """Run complete bills ingestion across all sources"""
        print("\n🚀 STARTING FULL BILLS INGESTION")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Show current status
        self.get_all_checkpoint_status()

        all_results = {}

        try:
            # Ingest Congress bills
            all_results['congress_bills'] = self.ingest_congress_bills(congress_range)

            # Ingest OpenStates bills
            all_results['openstates_bills'] = self.ingest_openstates_bills(jurisdictions)

            # Ingest GovInfo bills
            all_results['govinfo_bills'] = self.ingest_govinfo_bills(congress_range)

            # Final status
            print("\n🎉 FULL BILLS INGESTION COMPLETED")
            print("=" * 60)
            self.get_all_checkpoint_status()

            # Generate summary report
            self.generate_summary_report(all_results)

        except Exception as e:
            print(f"\n❌ BILLS INGESTION FAILED: {e}")
            raise

    def generate_summary_report(self, results: Dict[str, List[Dict[str, Any]]]):
        """Generate comprehensive summary report"""
        print("\n📊 INGESTION SUMMARY REPORT")
        print("=" * 60)

        total_processed = 0
        total_skipped = 0
        total_failed = 0

        for source, source_results in results.items():
            source_processed = sum(r.get('records_processed', 0) for r in source_results)
            source_skipped = sum(r.get('records_skipped', 0) for r in source_results)
            source_failed = sum(1 for r in source_results if r.get('status') == 'failed')

            print(f"\n{source.upper()}:")
            print(f"  ✅ Processed: {source_processed}")
            print(f"  ⏭️  Skipped: {source_skipped}")
            print(f"  ❌ Failed: {source_failed}")

            total_processed += source_processed
            total_skipped += source_skipped
            total_failed += source_failed

        print(f"\n🎯 OVERALL TOTALS:")
        print(f"  ✅ Total Processed: {total_processed}")
        print(f"  ⏭️  Total Skipped: {total_skipped}")
        print(f"  ❌ Total Failed: {total_failed}")

        if total_processed + total_skipped > 0:
            efficiency = (total_processed / (total_processed + total_skipped)) * 100
            print(f"  📈 Efficiency: {efficiency:.1f}% (new records vs duplicates)")

        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup_old_checkpoints(self, days: int = 30):
        """Clean up old checkpoints and sessions"""
        cursor = self.db_conn.cursor()

        try:
            # Clean up old sessions
            cursor.execute("""
                DELETE FROM incremental.ingestion_sessions
                WHERE started_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """, (days,))

            sessions_deleted = cursor.rowcount

            # Clean up old fingerprints (keep recent ones)
            cursor.execute("""
                DELETE FROM incremental.record_fingerprints
                WHERE last_updated_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """, (days,))

            fingerprints_deleted = cursor.rowcount

            self.db_conn.commit()

            print(f"🧹 Cleaned up {sessions_deleted} old sessions and {fingerprints_deleted} old fingerprints")

        except Exception as e:
            self.db_conn.rollback()
            print(f"❌ Cleanup failed: {e}")
        finally:
            cursor.close()

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description='Incremental Ingestion Manager')
    parser.add_argument('--action', choices=['status', 'ingest', 'reset', 'cleanup'],
                       default='status', help='Action to perform')
    parser.add_argument('--source', choices=['congress', 'openstates', 'govinfo', 'all'],
                       default='all', help='Data source to process')
    parser.add_argument('--data-type', choices=['members', 'bills', 'all'],
                       default='all', help='Data type to process (members or bills)')
    parser.add_argument('--congress-range', help='Congress range (e.g., "118-118")')
    parser.add_argument('--jurisdictions', nargs='+', help='OpenStates jurisdictions')
    parser.add_argument('--reset-category', help='Category to reset (format: source:type:category)')
    parser.add_argument('--cleanup-days', type=int, default=30, help='Days for cleanup')

    args = parser.parse_args()

    manager = IncrementalIngestionManager()

    if args.action == 'status':
        manager.get_all_checkpoint_status()
        manager.get_session_summary()

    elif args.action == 'ingest':
        if args.source == 'all':
            if args.data_type == 'all':
                # Ingest both members and bills for all sources
                manager.run_full_incremental_ingestion(args.congress_range, args.jurisdictions)
                manager.run_full_bills_ingestion(args.congress_range, args.jurisdictions)
            elif args.data_type == 'members':
                manager.run_full_incremental_ingestion(args.congress_range, args.jurisdictions)
            elif args.data_type == 'bills':
                manager.run_full_bills_ingestion(args.congress_range, args.jurisdictions)
        elif args.source == 'congress':
            if args.data_type == 'all' or args.data_type == 'members':
                manager.ingest_congress_data(args.congress_range)
            if args.data_type == 'all' or args.data_type == 'bills':
                manager.ingest_congress_bills(args.congress_range)
        elif args.source == 'openstates':
            if args.data_type == 'all' or args.data_type == 'members':
                manager.ingest_openstates_data(args.jurisdictions)
            if args.data_type == 'all' or args.data_type == 'bills':
                manager.ingest_openstates_bills(args.jurisdictions)
        elif args.source == 'govinfo':
            if args.data_type == 'all' or args.data_type == 'members':
                manager.ingest_govinfo_data(args.congress_range)
            if args.data_type == 'all' or args.data_type == 'bills':
                manager.ingest_govinfo_bills(args.congress_range)

    elif args.action == 'reset':
        if args.reset_category:
            source, data_type, category = args.reset_category.split(':')
            manager.reset_checkpoint(source, data_type, category)
        else:
            print("❌ Please specify --reset-category (format: source:type:category)")

    elif args.action == 'cleanup':
        manager.cleanup_old_checkpoints(args.cleanup_days)

if __name__ == "__main__":
    main()
