#!/usr/bin/env python3
"""
Bulk Bill Text Extraction Manager

This script processes all bills in the database and extracts missing text content
using the hybrid approach (GovInfo -> Congress.gov -> OCR).

Author: OpenDiscourse AI Agent
Date: December 3, 2025
"""

import os
import sys
import psycopg2
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.data_ingestion.bill_text_extractor import BillTextExtractor, BillTextResult

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BulkTextExtractor:
    """Manages bulk extraction of bill text for all bills in database"""

    def __init__(self, max_workers: int = 5):
        self.extractor = BillTextExtractor()
        self.max_workers = max_workers
        self.processed_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.start_time = datetime.now()

    def get_bills_missing_text(self, limit: Optional[int] = None) -> List[Tuple[int, str, int]]:
        """Get bills that are missing text content"""
        try:
            conn = psycopg2.connect(
                database='opendiscourse',
                user='cbwinslow',
                host='/var/run/postgresql'
            )
            cursor = conn.cursor()

            # Find bills with no or minimal summary_text
            query = """
            SELECT congress_number, bill_type, bill_number
            FROM congress.bills
            WHERE (summary_text IS NULL OR LENGTH(summary_text) < 100)
            ORDER BY congress_number DESC, bill_type, bill_number
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            bills = cursor.fetchall()

            cursor.close()
            conn.close()

            logger.info(f"Found {len(bills)} bills missing text content")
            return bills

        except Exception as e:
            logger.error(f"Error fetching bills missing text: {e}")
            return []

    def extract_text_for_bill(self, bill_info: Tuple[int, str, int]) -> bool:
        """Extract text for a single bill"""
        congress, bill_type, bill_number = bill_info
        bill_id = f"{congress}-{bill_type}-{bill_number}"

        try:
            # Extract text using hybrid approach
            result = self.extractor.extract_bill_text(congress, bill_type, bill_number)

            if result:
                # Save to database
                success = self.extractor.save_bill_text_to_database(result)

                if success:
                    self.success_count += 1
                    logger.info(f"✅ Successfully extracted and saved text for {bill_id}")
                    return True
                else:
                    self.failure_count += 1
                    logger.error(f"❌ Failed to save text for {bill_id}")
                    return False
            else:
                self.failure_count += 1
                logger.warning(f"⚠️ Could not extract text for {bill_id}")
                return False

        except Exception as e:
            self.failure_count += 1
            logger.error(f"❌ Error processing {bill_id}: {e}")
            return False
        finally:
            self.processed_count += 1

    def process_bills_bulk(self, limit: Optional[int] = None, parallel: bool = True) -> Dict[str, int]:
        """Process bills in bulk to extract missing text"""
        logger.info("Starting bulk bill text extraction")

        # Get bills missing text
        bills = self.get_bills_missing_text(limit)

        if not bills:
            logger.info("No bills missing text content")
            return {
                'total': 0,
                'processed': 0,
                'success': 0,
                'failed': 0
            }

        logger.info(f"Processing {len(bills)} bills for text extraction")

        if parallel and len(bills) > 1:
            # Process in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_bill = {
                    executor.submit(self.extract_text_for_bill, bill): bill
                    for bill in bills
                }

                # Process results as they complete
                for future in as_completed(future_to_bill):
                    bill = future_to_bill[future]
                    try:
                        success = future.result()
                        if self.processed_count % 10 == 0:
                            elapsed = datetime.now() - self.start_time
                            rate = self.processed_count / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                            logger.info(f"Progress: {self.processed_count}/{len(bills)} ({rate:.2f} bills/sec)")
                    except Exception as e:
                        logger.error(f"Future failed for bill {bill}: {e}")
                        self.failure_count += 1
                        self.processed_count += 1
        else:
            # Process sequentially
            for i, bill in enumerate(bills):
                self.extract_text_for_bill(bill)

                if (i + 1) % 10 == 0:
                    elapsed = datetime.now() - self.start_time
                    rate = (i + 1) / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                    logger.info(f"Progress: {i + 1}/{len(bills)} ({rate:.2f} bills/sec)")

        # Print final statistics
        self.print_final_statistics(len(bills))

        return {
            'total': len(bills),
            'processed': self.processed_count,
            'success': self.success_count,
            'failed': self.failure_count
        }

    def print_final_statistics(self, total_bills: int):
        """Print final processing statistics"""
        elapsed = datetime.now() - self.start_time

        print("\n" + "="*80)
        print("BULK BILL TEXT EXTRACTION RESULTS")
        print("="*80)
        print(f"Total bills to process: {total_bills}")
        print(f"Bills processed:        {self.processed_count}")
        print(f"Successfully extracted:  {self.success_count}")
        print(f"Failed to extract:     {self.failure_count}")

        if total_bills > 0:
            success_rate = (self.success_count / total_bills) * 100
            print(f"Success rate:          {success_rate:.1f}%")

        print(f"Processing time:        {elapsed}")

        if elapsed.total_seconds() > 0:
            rate = self.processed_count / elapsed.total_seconds()
            print(f"Processing rate:        {rate:.2f} bills/second")

        # Print extractor statistics
        self.extractor.print_statistics()

        print("="*80)

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract bill text for bills missing content')
    parser.add_argument('--limit', type=int, help='Limit number of bills to process')
    parser.add_argument('--sequential', action='store_true', help='Process sequentially instead of parallel')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    parser.add_argument('--congress', type=int, help='Process specific congress only')
    parser.add_argument('--bill-type', type=str, help='Process specific bill type only')

    args = parser.parse_args()

    # Create bulk extractor
    extractor = BulkTextExtractor(max_workers=args.workers)

    # Process bills
    results = extractor.process_bills_bulk(
        limit=args.limit,
        parallel=not args.sequential
    )

    # Print summary
    logger.info(f"Bulk extraction completed: {results}")

if __name__ == "__main__":
    main()
