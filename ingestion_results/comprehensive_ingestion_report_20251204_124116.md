
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 12:39:18
- **End Time**: 2025-12-04 12:41:16
- **Total Duration**: 0:01:58.767685
- **Total Jobs**: 131
- **Completed Jobs**: 64
- **Failed Jobs**: 67
- **Success Rate**: 48.9%

## Records Processed
- **Total Records**: 952,088
- **Successful Records**: 888,216
- **Failed Records**: 63,872

## Source Breakdown

### Congress.gov
- **Jobs**: 63
- **Records**: 899,528
- **Success Rate**: 88.9%

### OpenStates
- **Jobs**: 60
- **Records**: 52,560
- **Success Rate**: 0.0%

### GovInfo
- **Jobs**: 8
- **Records**: 0
- **Success Rate**: 100.0%

## Failed Jobs Details

### congress_members_113
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:39:18.241425
- **Completed**: 2025-12-04 12:39:20.247096

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:39:18.251179
- **Completed**: 2025-12-04 12:39:20.274038

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:39:44.311914
- **Completed**: 2025-12-04 12:39:46.314347

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:39:46.484873
- **Completed**: 2025-12-04 12:39:48.494506

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:40:08.358933
- **Completed**: 2025-12-04 12:40:10.360938

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:40:14.555113
- **Completed**: 2025-12-04 12:40:16.557685

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:40:32.402432
- **Completed**: 2025-12-04 12:40:34.404043

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:38.612364
- **Completed**: 2025-12-04 12:40:40.614613

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:38.933496
- **Completed**: 2025-12-04 12:40:40.936607

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:40.615005
- **Completed**: 2025-12-04 12:40:42.616805

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:40.936908
- **Completed**: 2025-12-04 12:40:42.939310

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:42.610727
- **Completed**: 2025-12-04 12:40:44.612906

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:42.617025
- **Completed**: 2025-12-04 12:40:44.618582

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:42.939693
- **Completed**: 2025-12-04 12:40:44.942630

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:44.613711
- **Completed**: 2025-12-04 12:40:46.616330

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:44.614250
- **Completed**: 2025-12-04 12:40:46.617226

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:44.618854
- **Completed**: 2025-12-04 12:40:46.621539

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:44.943000
- **Completed**: 2025-12-04 12:40:46.945146

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:46.616859
- **Completed**: 2025-12-04 12:40:48.620452

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:40:46.618361
- **Completed**: 2025-12-04 12:40:48.621397


## Performance Metrics
- **Average Records per Second**: 8016.39
- **Average Job Duration**: 0:00:00.906624
- **Peak Parallel Jobs**: 15
- **Database Pool Size**: 20 connections

## Database Statistics

Error getting final database stats: column "tablename" does not exist
LINE 2:                     SELECT schemaname, tablename,
                                               ^


## Recommendations

1. **Review Failed Jobs**: Check error messages above for failed jobs
2. **Monitor Database Growth**: Track database size growth over time
3. **Optimize Parallel Processing**: Adjust worker count based on system performance
4. **Schedule Regular Ingestion**: Set up automated incremental updates

## Next Steps

1. **Verify Data Quality**: Run data validation queries
2. **Update Analytics**: Refresh any analytics dashboards
3. **Archive Logs**: Archive ingestion logs for future reference
4. **Plan Incremental Updates**: Set up daily/weekly incremental ingestion

---
**Report Generated**: 2025-12-04 12:41:16
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
