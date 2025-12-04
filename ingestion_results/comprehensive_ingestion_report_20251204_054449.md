
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 05:43:10
- **End Time**: 2025-12-04 05:44:49
- **Total Duration**: 0:01:38.569954
- **Total Jobs**: 131
- **Completed Jobs**: 64
- **Failed Jobs**: 67
- **Success Rate**: 48.9%

## Records Processed
- **Total Records**: 950,632
- **Successful Records**: 886,760
- **Failed Records**: 63,872

## Source Breakdown

### Congress.gov
- **Jobs**: 63
- **Records**: 898,072
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

- **Started**: 2025-12-04 05:43:10.537181
- **Completed**: 2025-12-04 05:43:12.541362

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:43:10.542760
- **Completed**: 2025-12-04 05:43:12.564041

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:43:30.824675
- **Completed**: 2025-12-04 05:43:32.828549

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:43:30.831528
- **Completed**: 2025-12-04 05:43:32.849501

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:43:50.962078
- **Completed**: 2025-12-04 05:43:52.964062

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:43:52.870912
- **Completed**: 2025-12-04 05:43:54.873298

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:44:11.040260
- **Completed**: 2025-12-04 05:44:13.044460

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:13.044383
- **Completed**: 2025-12-04 05:44:15.048031

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:13.045368
- **Completed**: 2025-12-04 05:44:15.047501

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:14.918528
- **Completed**: 2025-12-04 05:44:16.921206

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:15.047726
- **Completed**: 2025-12-04 05:44:17.050055

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:15.048449
- **Completed**: 2025-12-04 05:44:17.050867

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:16.921666
- **Completed**: 2025-12-04 05:44:18.924697

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:16.923271
- **Completed**: 2025-12-04 05:44:18.926961

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:17.050277
- **Completed**: 2025-12-04 05:44:19.052870

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:17.051061
- **Completed**: 2025-12-04 05:44:19.053081

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:18.925190
- **Completed**: 2025-12-04 05:44:20.928012

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:18.927372
- **Completed**: 2025-12-04 05:44:20.930013

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:19.053226
- **Completed**: 2025-12-04 05:44:21.055811

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'oh' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:44:19.053407
- **Completed**: 2025-12-04 05:44:21.055641


## Performance Metrics
- **Average Records per Second**: 9644.24
- **Average Job Duration**: 0:00:00.752442
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
**Report Generated**: 2025-12-04 05:44:49
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
