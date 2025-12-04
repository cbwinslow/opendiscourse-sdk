
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 07:33:14
- **End Time**: 2025-12-04 07:35:02
- **Total Duration**: 0:01:48.351700
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

- **Started**: 2025-12-04 07:33:14.557940
- **Completed**: 2025-12-04 07:33:16.562825

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:33:14.563284
- **Completed**: 2025-12-04 07:33:16.583919

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:33:36.628015
- **Completed**: 2025-12-04 07:33:38.630691

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:33:36.715222
- **Completed**: 2025-12-04 07:33:38.724452

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:33:58.674046
- **Completed**: 2025-12-04 07:34:00.676062

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:34:00.668937
- **Completed**: 2025-12-04 07:34:02.671133

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:34:22.842495
- **Completed**: 2025-12-04 07:34:24.844312

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:24.844696
- **Completed**: 2025-12-04 07:34:26.847600

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:24.847549
- **Completed**: 2025-12-04 07:34:26.850003

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:24.849327
- **Completed**: 2025-12-04 07:34:26.851910

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:26.847937
- **Completed**: 2025-12-04 07:34:28.849886

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:26.850274
- **Completed**: 2025-12-04 07:34:28.852848

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:26.852249
- **Completed**: 2025-12-04 07:34:28.854421

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:28.728911
- **Completed**: 2025-12-04 07:34:30.730861

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:28.850313
- **Completed**: 2025-12-04 07:34:30.852794

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:28.853358
- **Completed**: 2025-12-04 07:34:30.856428

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:28.854971
- **Completed**: 2025-12-04 07:34:30.857213

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:30.731228
- **Completed**: 2025-12-04 07:34:32.733895

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:30.853214
- **Completed**: 2025-12-04 07:34:32.855560

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'oh' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:34:30.856621
- **Completed**: 2025-12-04 07:34:32.858914


## Performance Metrics
- **Average Records per Second**: 8787.01
- **Average Job Duration**: 0:00:00.827112
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
**Report Generated**: 2025-12-04 07:35:02
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
