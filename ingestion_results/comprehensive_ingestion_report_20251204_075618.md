
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 07:54:24
- **End Time**: 2025-12-04 07:56:18
- **Total Duration**: 0:01:53.409732
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

- **Started**: 2025-12-04 07:54:24.774767
- **Completed**: 2025-12-04 07:54:26.781521

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:54:24.780846
- **Completed**: 2025-12-04 07:54:26.808362

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:54:50.836524
- **Completed**: 2025-12-04 07:54:52.839016

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:54:53.154240
- **Completed**: 2025-12-04 07:54:55.160214

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:55:16.899913
- **Completed**: 2025-12-04 07:55:18.902209

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:55:17.324860
- **Completed**: 2025-12-04 07:55:19.327944

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 07:55:40.993740
- **Completed**: 2025-12-04 07:55:42.996539

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:42.996844
- **Completed**: 2025-12-04 07:55:45.000574

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:43.449791
- **Completed**: 2025-12-04 07:55:45.452533

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:43.450531
- **Completed**: 2025-12-04 07:55:45.454440

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:43.451071
- **Completed**: 2025-12-04 07:55:45.453426

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:45.000930
- **Completed**: 2025-12-04 07:55:47.003954

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:45.452774
- **Completed**: 2025-12-04 07:55:47.456122

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:45.453784
- **Completed**: 2025-12-04 07:55:47.457409

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:45.454875
- **Completed**: 2025-12-04 07:55:47.457265

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:47.004329
- **Completed**: 2025-12-04 07:55:49.006443

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:47.456674
- **Completed**: 2025-12-04 07:55:49.461376

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:47.458317
- **Completed**: 2025-12-04 07:55:49.465634

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:47.459115
- **Completed**: 2025-12-04 07:55:49.467577

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'oh' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 07:55:49.007172
- **Completed**: 2025-12-04 07:55:51.010845


## Performance Metrics
- **Average Records per Second**: 8395.12
- **Average Job Duration**: 0:00:00.865723
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
**Report Generated**: 2025-12-04 07:56:18
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
