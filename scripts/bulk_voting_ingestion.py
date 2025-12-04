#!/usr/bin/env python3
"""
Bulk All Voting Data System
Ingests ALL voting data from ALL sources across ALL years
"""

import sys
import os
import json
import time
import requests
import psycopg2
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import logging

sys.path.append('/home/cbwinslow/Videos/opendiscourse')
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BulkVotingIngestion:
    def __init__(self):
        self.db_pool = None
        self.ingestion_results = {'start_time': datetime.now().isoformat(), 'total_records': 0, 'errors': []}
        self._setup_database()
        self._setup_config()

    def _setup_database(self):
        try:
            self.db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5, maxconn=20, database="opendiscourse", user="cbwinslow", host="/var/run/postgresql"
            )
            logger.info("✅ Database connection pool established")
        except Exception as e:
            logger.error(f"❌ Database pool setup failed: {e}")
            self.db_pool = None

    def _setup_config(self):
        self.config = {
            'congress_years': {110: list(range(2007, 2009)), 111: list(range(2009, 2011)), 112: list(range(2011, 2013)),
                              113: list(range(2013, 2015)), 114: list(range(2015, 2017)), 115: list(range(2017, 2019)),
                              116: list(range(2019, 2021)), 117: list(range(2021, 2023)), 118: list(range(2023, 2025))},
            'openstates_jurisdictions': ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy'],
            'govinfo_collections': ['BILLS', 'CREC', 'FR', 'GPO', 'USCODE', 'USCOURTS']
        }

    def run_comprehensive_ingestion(self, mode="full", parallel=True, workers=4):
        logger.info(f"🚀 Starting comprehensive voting ingestion: mode={mode}")

        try:
            if mode == "full":
                self._ingest_all_sources_all_years(parallel, workers)
            elif mode == "votes-only":
                self._ingest_votes_only(parallel, workers)
            elif mode.startswith("congress"):
                congress_range = mode.split()[1] if len(mode.split()) > 1 else "118"
                self._ingest_congress_range(congress_range, parallel, workers)
            else:
                logger.error(f"❌ Unknown mode: {mode}")
                return False

            self._generate_report()
            return True

        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            return False

    def _ingest_all_sources_all_years(self, parallel, workers):
        logger.info("📊 Ingesting ALL data from ALL sources across ALL years")

        tasks = []

        # Congress.gov data (all congresses, all years)
        for congress, years in self.config['congress_years'].items():
            for year in years:
                if parallel:
                    tasks.append(('congress_votes', congress, year))
                else:
                    self._ingest_congress_votes(congress, year)

        # OpenStates data (all jurisdictions, recent years)
        for jurisdiction in self.config['openstates_jurisdictions']:
            for year in range(2020, 2025):
                if parallel:
                    tasks.append(('openstates_votes', jurisdiction, year))
                else:
                    self._ingest_openstates_votes(jurisdiction, year)

        # GovInfo data (all collections, all years)
        for collection in self.config['govinfo_collections']:
            for year in range(2000, 2025):
                if parallel:
                    tasks.append(('govinfo_votes', collection, year))
                else:
                    self._ingest_govinfo_votes(collection, year)

        if parallel and tasks:
            logger.info(f"🔄 Running {len(tasks)} tasks with {workers} workers")
            self._execute_tasks_parallel(tasks, workers)

    def _ingest_votes_only(self, parallel, workers):
        logger.info("📊 Ingesting voting data only from all sources")

        vote_tasks = []

        # Congress.gov votes (recent congresses)
        for congress in [116, 117, 118]:
            for year in self.config['congress_years'].get(congress, []):
                vote_tasks.append(('congress_votes', congress, year))

        # OpenStates votes (all jurisdictions, recent years)
        for jurisdiction in self.config['openstates_jurisdictions']:
            for year in range(2022, 2025):
                vote_tasks.append(('openstates_votes', jurisdiction, year))

        # GovInfo votes (main collections)
        for collection in ['BILLS', 'CREC']:
            for year in range(2020, 2025):
                vote_tasks.append(('govinfo_votes', collection, year))

        if parallel:
            self._execute_tasks_parallel(vote_tasks, workers)
        else:
            for task in vote_tasks:
                source, identifier, year = task
                if source == 'congress_votes':
                    self._ingest_congress_votes(identifier, year)
                elif source == 'openstates_votes':
                    self._ingest_openstates_votes(identifier, year)
                elif source == 'govinfo_votes':
                    self._ingest_govinfo_votes(identifier, year)

    def _ingest_congress_range(self, congress_range, parallel, workers):
        logger.info(f"📊 Ingesting Congress votes for range: {congress_range}")

        if '-' in congress_range:
            start_congress, end_congress = map(int, congress_range.split('-'))
            congresses = list(range(start_congress, end_congress + 1))
        else:
            congresses = [int(congress_range)]

        congress_tasks = []
        for congress in congresses:
            years = self.config['congress_years'].get(congress, [])
            for year in years:
                if parallel:
                    congress_tasks.append(('congress_votes', congress, year))
                else:
                    self._ingest_congress_votes(congress, year)

        if parallel and congress_tasks:
            self._execute_tasks_parallel(congress_tasks, workers)

    def _execute_tasks_parallel(self, tasks, workers):
        def run_single_task(task):
            source, identifier, year = task
            try:
                if source == 'congress_votes':
                    return self._ingest_congress_votes(identifier, year)
                elif source == 'openstates_votes':
                    return self._ingest_openstates_votes(identifier, year)
                elif source == 'govinfo_votes':
                    return self._ingest_govinfo_votes(identifier, year)
                else:
                    logger.warning(f"Unknown source: {source}")
                    return 0
            except Exception as e:
                logger.error(f"Task failed ({source} {identifier} {year}): {e}")
                return 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_task = {executor.submit(run_single_task, task): task for task in tasks}

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    logger.info(f"✅ Completed {task}: {result} records")
                except Exception as e:
                    logger.error(f"❌ Task failed {task}: {e}")

    def _ingest_congress_votes(self, congress, year):
        logger.info(f"🏛️ Ingesting Congress votes: {congress} ({year})")

        try:
            from bulk_ingest_votes import VoteIngestionAPI
            ingestion = VoteIngestionAPI()
            return ingestion.ingest_congress_votes(congress, year, limit=1000)
        except Exception as e:
            logger.error(f"Congress votes ingestion failed ({congress} {year}): {e}")
            return self._ingest_congress_votes_direct(congress, year)

    def _ingest_openstates_votes(self, jurisdiction, year):
        logger.info(f"🏛️ Ingesting OpenStates votes: {jurisdiction.upper()} ({year})")

        try:
            from bulk_ingest_votes import VoteIngestionAPI
            ingestion = VoteIngestionAPI()
            return ingestion.ingest_openstates_votes(jurisdiction, year, limit=500)
        except Exception as e:
            logger.error(f"OpenStates votes ingestion failed ({jurisdiction} {year}): {e}")
            return self._ingest_openstates_votes_direct(jurisdiction, year)

    def _ingest_govinfo_votes(self, collection, year):
        logger.info(f"🏛️ Ingesting GovInfo votes: {collection} ({year})")

        try:
            from bulk_ingest_votes import VoteIngestionAPI
            ingestion = VoteIngestionAPI()
            return ingestion.ingest_govinfo_votes(collection, year, limit=500)
        except Exception as e:
            logger.error(f"GovInfo votes ingestion failed ({collection} {year}): {e}")
            return self._ingest_govinfo_votes_direct(collection, year)

    def _ingest_congress_votes_direct(self, congress, year):
        logger.info(f"🏛️ Direct Congress API: {congress} ({year})")

        try:
            headers = {"X-API-Key": os.getenv('CONGRESS_API_KEY'), "Content-Type": "application/json"}
            params = {"congress": congress, "year": year, "limit": 1000, "offset": 0, "format": "json"}

            response = requests.get("https://api.congress.gov/v3/house-vote", params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            votes = data.get('houseRollCallVotes', [])

            if not votes:
                logger.info(f"No votes found for Congress {congress} year {year}")
                return 0

            processed_votes = []
            for vote in votes:
                processed_vote = {
                    'vote_id': f"{congress}-{year}-{vote.get('rollCallNumber', '')}",
                    'congress': congress, 'year': year, 'vote_date': vote.get('date'),
                    'vote_type': vote.get('voteType'), 'result': vote.get('result'),
                    'total_yes': vote.get('total', {}).get('yes', 0),
                    'total_no': vote.get('total', {}).get('no', 0),
                    'total_present': vote.get('total', {}).get('present', 0),
                    'raw_data': json.dumps(vote)
                }
                processed_votes.append(processed_vote)

            saved = self._save_votes_to_database("congress_votes", processed_votes)
            logger.info(f"✅ Saved {saved} Congress votes ({congress} {year})")
            return saved

        except Exception as e:
            logger.error(f"Direct Congress API failed ({congress} {year}): {e}")
            return 0

    def _ingest_openstates_votes_direct(self, jurisdiction, year):
        logger.info(f"🏛️ Direct OpenStates API: {jurisdiction} ({year})")

        try:
            headers = {"X-API-Key": os.getenv('OPENSTATES_API_KEY'), "Content-Type": "application/json"}
            params = {"jurisdiction": jurisdiction, "year": year, "per_page": 500, "page": 1}

            response = requests.get("https://v3.openstates.org/votes", params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            votes = data.get('results', [])

            if not votes:
                logger.info(f"No votes found for {jurisdiction} year {year}")
                return 0

            processed_votes = []
            for vote in votes:
                processed_vote = {
                    'vote_id': vote.get('id'), 'jurisdiction': jurisdiction, 'year': year,
                    'vote_date': vote.get('date'), 'result': vote.get('result'),
                    'yes_count': vote.get('yes_count', 0), 'no_count': vote.get('no_count', 0),
                    'other_count': vote.get('other_count', 0), 'raw_data': json.dumps(vote)
                }
                processed_votes.append(processed_vote)

            saved = self._save_votes_to_database("openstates_votes", processed_votes)
            logger.info(f"✅ Saved {saved} OpenStates votes ({jurisdiction} {year})")
            return saved

        except Exception as e:
            logger.error(f"Direct OpenStates API failed ({jurisdiction} {year}): {e}")
            return 0

    def _ingest_govinfo_votes_direct(self, collection, year):
        logger.info(f"🏛️ Direct GovInfo API: {collection} ({year})")

        try:
            headers = {"X-API-Key": os.getenv('GOVINFO_API_KEY'), "Content-Type": "application/json"}
            params = {"year": year, "pageSize": 500, "offset": 0}

            response = requests.get(f"https://api.govinfo.gov/collections/{collection}/votes",
                                  params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            votes = data.get('votes', [])

            if not votes:
                logger.info(f"No votes found for {collection} year {year}")
                return 0

            processed_votes = []
            for vote in votes:
                processed_vote = {
                    'vote_id': vote.get('vote_id'), 'collection': collection, 'year': year,
                    'vote_date': vote.get('vote_date'), 'vote_type': vote.get('vote_type'),
                    'result': vote.get('result'), 'yea_count': vote.get('yea_count', 0),
                    'nay_count': vote.get('nay_count', 0), 'present_count': vote.get('present_count', 0),
                    'raw_data': json.dumps(vote)
                }
                processed_votes.append(processed_vote)

            saved = self._save_votes_to_database("govinfo_votes", processed_votes)
            logger.info(f"✅ Saved {saved} GovInfo votes ({collection} {year})")
            return saved

        except Exception as e:
            logger.error(f"Direct GovInfo API failed ({collection} {year}): {e}")
            return 0

    def _save_votes_to_database(self, table, votes):
        if not self.db_pool or not votes:
            return 0

        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            self._create_table_if_not_exists(cursor, table)

            inserted_count = 0
            for vote in votes:
                try:
                    if table == "congress_votes":
                        cursor.execute("""
                            INSERT INTO congress_votes (vote_id, congress, year, vote_date, vote_type, result,
                            total_yes, total_no, total_present, raw_data) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (vote_id) DO NOTHING
                        """, (vote.get('vote_id'), vote.get('congress'), vote.get('year'), vote.get('vote_date'),
                              vote.get('vote_type'), vote.get('result'), vote.get('total_yes', 0), vote.get('total_no', 0),
                              vote.get('total_present', 0), vote.get('raw_data')))

                    elif table == "openstates_votes":
                        cursor.execute("""
                            INSERT INTO openstates_votes (vote_id, jurisdiction, year, vote_date, result,
                            yes_count, no_count, other_count, raw_data) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (vote_id) DO NOTHING
                        """, (vote.get('vote_id'), vote.get('jurisdiction'), vote.get('year'), vote.get('vote_date'),
                              vote.get('result'), vote.get('yes_count', 0), vote.get('no_count', 0),
                              vote.get('other_count', 0), vote.get('raw_data')))

                    elif table == "govinfo_votes":
                        cursor.execute("""
                            INSERT INTO govinfo_votes (vote_id, collection, year, vote_date, vote_type, result,
                            yea_count, nay_count, present_count, raw_data) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (vote_id) DO NOTHING
                        """, (vote.get('vote_id'), vote.get('collection'), vote.get('year'), vote.get('vote_date'),
                              vote.get('vote_type'), vote.get('result'), vote.get('yea_count', 0), vote.get('nay_count', 0),
                              vote.get('present_count', 0), vote.get('raw_data')))

                    inserted_count += 1

                except Exception as e:
                    logger.error(f"Failed to insert vote {vote.get('vote_id')}: {e}")
                    continue

            conn.commit()
            cursor.close()
            self.db_pool.putconn(conn)

            return inserted_count

        except Exception as e:
            logger.error(f"Database save error for {table}: {e}")
            if 'conn' in locals():
                conn.rollback()
                self.db_pool.putconn(conn)
            return 0

    def _create_table_if_not_exists(self, cursor, table):
        if table == "congress_votes":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS congress_votes (
                    vote_id VARCHAR(100) PRIMARY KEY, congress INT, year INT, vote_date TIMESTAMP,
                    vote_type VARCHAR(50), result VARCHAR(50), total_yes INT, total_no INT, total_present INT,
                    raw_data JSONB, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        elif table == "openstates_votes":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS openstates_votes (
                    vote_id VARCHAR(100) PRIMARY KEY, jurisdiction VARCHAR(10), year INT, vote_date TIMESTAMP,
                    result VARCHAR(50), yes_count INT, no_count INT, other_count INT, raw_data JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        elif table == "govinfo_votes":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS govinfo_votes (
                    vote_id VARCHAR(100) PRIMARY KEY, collection VARCHAR(50), year INT, vote_date TIMESTAMP,
                    vote_type VARCHAR(50), result VARCHAR(50), yea_count INT, nay_count INT, present_count INT,
                    raw_data JSONB, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def run_all_data_types(self):
        logger.info("🚀 Running ALL DATA TYPES comprehensive ingestion")

        scripts = [
            ('Congress Bills', 'python', 'scripts/ingest_congress_bills_incremental.py', '--congress 118'),
            ('Congress Members', 'python', 'scripts/ingest_congress_incremental.py', '--congress 118'),
            ('OpenStates People', 'python', 'scripts/ingest_openstates_incremental.py', '--jurisdictions all'),
            ('OpenStates Bills', 'python', 'scripts/ingest_openstates_bills_incremental.py', '--jurisdictions all'),
            ('GovInfo Bills', 'python', 'scripts/ingest_govinfo_bills_incremental.py', '--congress 118'),
            ('GovInfo Members', 'python', 'scripts/ingest_govinfo_incremental.py', '--congress 118'),
            ('Congress Votes', 'python', 'scripts/bulk_voting_ingestion.py', '--mode congress 118'),
            ('All Votes', 'python', 'scripts/bulk_voting_ingestion.py', '--mode votes-only --parallel --workers 4')
        ]

        results = {}

        for name, cmd, script, args in scripts:
            logger.info(f"📊 Running {name} ingestion...")
            try:
                full_cmd = f"{cmd} {script} {args}"
                result = subprocess.run(full_cmd.split(), capture_output=True, text=True, timeout=3600)

                if result.returncode == 0:
                    logger.info(f"✅ {name} completed successfully")
                    results[name] = {'status': 'success', 'output': result.stdout}
                else:
                    logger.error(f"❌ {name} failed: {result.stderr}")
                    results[name] = {'status': 'failed', 'error': result.stderr}

            except Exception as e:
                logger.error(f"❌ {name} failed with exception: {e}")
                results[name] = {'status': 'error', 'error': str(e)}

        return results

    def _generate_report(self):
        self.ingestion_results['end_time'] = datetime.now().isoformat()

        start_time = datetime.fromisoformat(self.ingestion_results['start_time'])
        end_time = datetime.fromisoformat(self.ingestion_results['end_time'])
        duration = end_time - start_time

        report = f"""
COMPREHENSIVE VOTING DATA INGESTION REPORT
==========================================
Start Time: {self.ingestion_results['start_time']}
End Time: {self.ingestion_results['end_time']}
Duration: {str(duration)}

SUMMARY:
--------
Total Records Ingested: {self.ingestion_results.get('total_records', 0):,}
Total Errors: {len(self.ingestion_results.get('errors', []))}
"""

        report_file = f"bulk_voting_ingestion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"📋 Report saved: {report_file}")
        print(report)

        return report_file

def main():
    parser = argparse.ArgumentParser(description="Bulk Voting Data Ingestion System")
    parser.add_argument('--mode', choices=['full', 'votes-only', 'congress'], default='full')
    parser.add_argument('--parallel', action='store_true', help='Run ingestion in parallel')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--all-data-types', action='store_true', help='Run all data types')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without running')

    args = parser.parse_args()

    logger.info("🚀 Bulk Voting Data Ingestion System")
    logger.info("=" * 50)

    try:
        ingestion = BulkVotingIngestion()

        if args.all_data_types:
            logger.info("📊 Running ALL DATA TYPES ingestion")
            results = ingestion.run_all_data_types()

        elif args.dry_run:
            logger.info("🔍 Dry run mode - showing ingestion plan")
            print_plan(ingestion.config)

        else:
            success = ingestion.run_comprehensive_ingestion(
                mode=args.mode, parallel=args.parallel, workers=args.workers
            )

            if not success:
                sys.exit(1)

        logger.info("✅ Bulk voting ingestion completed!")

    except Exception as e:
        logger.error(f"❌ Bulk voting ingestion failed: {e}")
        sys.exit(1)

def print_plan(config):
    print("\n📋 BULK VOTING INGESTION PLAN")
    print("=" * 40)

    print(f"\n🏛️ CONGRESS.GOV DATA:")
    for congress, years in config['congress_years'].items():
        print(f"  Congress {congress}: {len(years)} years")

    print(f"\n🏛️ OPENSTATES DATA:")
    print(f"  {len(config['openstates_jurisdictions'])} jurisdictions")

    print(f"\n🏛️ GOVINFO DATA:")
    print(f"  {len(config['govinfo_collections'])} collections")

    congress_tasks = sum(len(years) for years in config['congress_years'].values())
    openstates_tasks = len(config['openstates_jurisdictions']) * 5
    govinfo_tasks = len(config['govinfo_collections']) * 25

    total_tasks = congress_tasks + openstates_tasks + govinfo_tasks

    print(f"\n📊 ESTIMATED TASKS: {total_tasks}")
    print(f"⏱️ ESTIMATED TIME: ~{total_tasks * 0.5:.0f} minutes")

if __name__ == "__main__":
    main()
