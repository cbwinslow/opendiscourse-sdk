
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 05:51:15
- **End Time**: 2025-12-04 05:53:06
- **Total Duration**: 0:01:50.440406
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

- **Started**: 2025-12-04 05:51:15.621273
- **Completed**: 2025-12-04 05:51:17.626164

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:51:15.627728
- **Completed**: 2025-12-04 05:51:17.650104

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:51:39.675453
- **Completed**: 2025-12-04 05:51:41.678127

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:51:39.868176
- **Completed**: 2025-12-04 05:51:41.878617

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:52:03.774117
- **Completed**: 2025-12-04 05:52:05.776775

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:52:03.943412
- **Completed**: 2025-12-04 05:52:05.946880

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 05:52:27.820334
- **Completed**: 2025-12-04 05:52:29.822436

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:29.822849
- **Completed**: 2025-12-04 05:52:31.826529

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:29.825232
- **Completed**: 2025-12-04 05:52:31.827540

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:29.983165
- **Completed**: 2025-12-04 05:52:31.986070

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:29.990997
- **Completed**: 2025-12-04 05:52:31.993042

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:31.826766
- **Completed**: 2025-12-04 05:52:33.830705

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:31.827906
- **Completed**: 2025-12-04 05:52:33.830504

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:31.986454
- **Completed**: 2025-12-04 05:52:33.988348

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:31.993258
- **Completed**: 2025-12-04 05:52:33.994878

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:33.830891
- **Completed**: 2025-12-04 05:52:35.834263

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:33.830978
- **Completed**: 2025-12-04 05:52:35.833817

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:33.988657
- **Completed**: 2025-12-04 05:52:35.991045

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:33.995156
- **Completed**: 2025-12-04 05:52:35.997921

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'oh' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 05:52:35.834135
- **Completed**: 2025-12-04 05:52:37.837245


## Performance Metrics
- **Average Records per Second**: 8607.65
- **Average Job Duration**: 0:00:00.843057
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
**Report Generated**: 2025-12-04 05:53:06
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
