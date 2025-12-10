
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 12:26:21
- **End Time**: 2025-12-04 12:28:11
- **Total Duration**: 0:01:50.514863
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

- **Started**: 2025-12-04 12:26:21.370225
- **Completed**: 2025-12-04 12:26:23.380462

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:26:21.377467
- **Completed**: 2025-12-04 12:26:23.402632

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:26:43.432149
- **Completed**: 2025-12-04 12:26:45.433913

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:26:45.429944
- **Completed**: 2025-12-04 12:26:47.433370

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:27:05.519037
- **Completed**: 2025-12-04 12:27:07.525866

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:27:07.535860
- **Completed**: 2025-12-04 12:27:09.549143

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:27:29.763768
- **Completed**: 2025-12-04 12:27:31.770928

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:35.769916
- **Completed**: 2025-12-04 12:27:37.772262

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:35.794004
- **Completed**: 2025-12-04 12:27:37.797757

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:35.795084
- **Completed**: 2025-12-04 12:27:37.799355

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:37.772687
- **Completed**: 2025-12-04 12:27:39.776160

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:37.798562
- **Completed**: 2025-12-04 12:27:39.809070

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:37.798795
- **Completed**: 2025-12-04 12:27:39.809766

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:37.801511
- **Completed**: 2025-12-04 12:27:39.810473

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:39.776438
- **Completed**: 2025-12-04 12:27:41.779542

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:39.809549
- **Completed**: 2025-12-04 12:27:41.815385

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:39.810941
- **Completed**: 2025-12-04 12:27:41.815137

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:39.811865
- **Completed**: 2025-12-04 12:27:41.814768

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:41.780194
- **Completed**: 2025-12-04 12:27:43.783026

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:27:41.815675
- **Completed**: 2025-12-04 12:27:43.819928


## Performance Metrics
- **Average Records per Second**: 8615.02
- **Average Job Duration**: 0:00:00.843625
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
**Report Generated**: 2025-12-04 12:28:11
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
