
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 11:53:14
- **End Time**: 2025-12-04 11:55:21
- **Total Duration**: 0:02:06.696991
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

- **Started**: 2025-12-04 11:53:14.584765
- **Completed**: 2025-12-04 11:53:16.591250

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 11:53:14.592790
- **Completed**: 2025-12-04 11:53:16.609343

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 11:53:40.670481
- **Completed**: 2025-12-04 11:53:42.672463

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 11:53:46.663358
- **Completed**: 2025-12-04 11:53:48.667739

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 11:54:10.947171
- **Completed**: 2025-12-04 11:54:12.970757

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 11:54:14.988713
- **Completed**: 2025-12-04 11:54:16.992853

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 11:54:39.016310
- **Completed**: 2025-12-04 11:54:41.018756

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:41.204463
- **Completed**: 2025-12-04 11:54:43.229158

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:42.812653
- **Completed**: 2025-12-04 11:54:44.814962

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:43.227168
- **Completed**: 2025-12-04 11:54:45.248305

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:43.229391
- **Completed**: 2025-12-04 11:54:45.247429

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:44.815461
- **Completed**: 2025-12-04 11:54:46.818725

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:45.247753
- **Completed**: 2025-12-04 11:54:47.258106

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:45.248879
- **Completed**: 2025-12-04 11:54:47.258660

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:46.819223
- **Completed**: 2025-12-04 11:54:48.822699

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:47.258265
- **Completed**: 2025-12-04 11:54:49.272841

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:47.258838
- **Completed**: 2025-12-04 11:54:49.273417

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:47.259199
- **Completed**: 2025-12-04 11:54:49.273624

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:48.823232
- **Completed**: 2025-12-04 11:54:50.826675

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 11:54:49.273838
- **Completed**: 2025-12-04 11:54:51.286217


## Performance Metrics
- **Average Records per Second**: 7514.69
- **Average Job Duration**: 0:00:00.967153
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
**Report Generated**: 2025-12-04 11:55:21
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
