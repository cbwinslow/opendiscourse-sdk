
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 12:11:45
- **End Time**: 2025-12-04 12:13:37
- **Total Duration**: 0:01:52.377999
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

- **Started**: 2025-12-04 12:11:45.275136
- **Completed**: 2025-12-04 12:11:47.280835

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:11:45.281916
- **Completed**: 2025-12-04 12:11:47.309491

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:12:09.444734
- **Completed**: 2025-12-04 12:12:11.466033

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:12:09.447192
- **Completed**: 2025-12-04 12:12:11.473836

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:12:33.725633
- **Completed**: 2025-12-04 12:12:35.731197

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:12:37.746809
- **Completed**: 2025-12-04 12:12:39.767641

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 12:12:57.920773
- **Completed**: 2025-12-04 12:12:59.923713

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:03.930965
- **Completed**: 2025-12-04 12:13:05.934149

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:03.935573
- **Completed**: 2025-12-04 12:13:05.938184

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:03.942971
- **Completed**: 2025-12-04 12:13:05.945873

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:05.934702
- **Completed**: 2025-12-04 12:13:07.937752

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:05.938381
- **Completed**: 2025-12-04 12:13:07.940039

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:05.939778
- **Completed**: 2025-12-04 12:13:07.942032

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:05.946317
- **Completed**: 2025-12-04 12:13:07.948548

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:07.938088
- **Completed**: 2025-12-04 12:13:09.939801

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:07.940379
- **Completed**: 2025-12-04 12:13:09.942854

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:07.942274
- **Completed**: 2025-12-04 12:13:09.944461

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:07.948791
- **Completed**: 2025-12-04 12:13:09.951715

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:09.940326
- **Completed**: 2025-12-04 12:13:11.942701

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 1:   File "/home/cbwinslow/Videos/opendiscourse/scripts/ingestion/openstates_cli.py", line 210
    def ingest_people(self, jurisdiction: str):
    ^^^
SyntaxError: invalid syntax

- **Started**: 2025-12-04 12:13:09.943223
- **Completed**: 2025-12-04 12:13:11.946881


## Performance Metrics
- **Average Records per Second**: 8472.19
- **Average Job Duration**: 0:00:00.857847
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
**Report Generated**: 2025-12-04 12:13:37
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
