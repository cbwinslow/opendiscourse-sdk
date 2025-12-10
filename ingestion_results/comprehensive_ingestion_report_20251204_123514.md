
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 12:32:13
- **End Time**: 2025-12-04 12:35:14
- **Total Duration**: 0:03:01.410950
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

- **Started**: 2025-12-04 12:32:13.160657
- **Completed**: 2025-12-04 12:32:15.168474

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:32:13.167414
- **Completed**: 2025-12-04 12:32:15.195841

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:33:25.776534
- **Completed**: 2025-12-04 12:33:27.779309

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:33:29.342045
- **Completed**: 2025-12-04 12:33:31.344045

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:33:54.260053
- **Completed**: 2025-12-04 12:33:56.262644

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:34:02.256262
- **Completed**: 2025-12-04 12:34:04.258219

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:34:24.462552
- **Completed**: 2025-12-04 12:34:26.464520

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:36.380528
- **Completed**: 2025-12-04 12:34:38.384341

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:37.874030
- **Completed**: 2025-12-04 12:34:39.876481

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:38.385071
- **Completed**: 2025-12-04 12:34:40.390220

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:38.391277
- **Completed**: 2025-12-04 12:34:40.394564

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:39.876806
- **Completed**: 2025-12-04 12:34:41.879470

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:40.390540
- **Completed**: 2025-12-04 12:34:42.392431

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:40.394879
- **Completed**: 2025-12-04 12:34:42.396602

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:40.399609
- **Completed**: 2025-12-04 12:34:42.400872

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:41.879840
- **Completed**: 2025-12-04 12:34:43.882092

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:42.647931
- **Completed**: 2025-12-04 12:34:44.651294

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:42.648334
- **Completed**: 2025-12-04 12:34:44.652454

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:42.648818
- **Completed**: 2025-12-04 12:34:44.652325

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:34:43.882435
- **Completed**: 2025-12-04 12:34:45.885206


## Performance Metrics
- **Average Records per Second**: 5248.24
- **Average Job Duration**: 0:00:01.384816
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
**Report Generated**: 2025-12-04 12:35:14
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
