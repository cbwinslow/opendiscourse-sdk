
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-04 08:39:49
- **End Time**: 2025-12-04 09:22:47
- **Total Duration**: 0:42:57.995995
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

- **Started**: 2025-12-04 08:39:49.717676
- **Completed**: 2025-12-04 08:39:51.722537

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 08:39:49.724129
- **Completed**: 2025-12-04 08:39:51.745304

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 08:40:13.811166
- **Completed**: 2025-12-04 08:40:15.813376

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 08:40:15.813666
- **Completed**: 2025-12-04 08:40:17.816082

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 08:40:40.123200
- **Completed**: 2025-12-04 08:40:42.125508

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 08:40:43.851844
- **Completed**: 2025-12-04 08:40:45.854666

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-04 08:41:05.919834
- **Completed**: 2025-12-04 08:41:07.922024

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:08.296884
- **Completed**: 2025-12-04 08:41:10.300036

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:10.299582
- **Completed**: 2025-12-04 08:41:12.302704

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:10.300276
- **Completed**: 2025-12-04 08:41:12.303241

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:10.307707
- **Completed**: 2025-12-04 08:41:12.310542

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:12.303030
- **Completed**: 2025-12-04 08:41:14.306121

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:12.303788
- **Completed**: 2025-12-04 08:41:14.305191

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:12.311145
- **Completed**: 2025-12-04 08:41:14.314910

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:14.305561
- **Completed**: 2025-12-04 08:41:16.308312

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:14.306661
- **Completed**: 2025-12-04 08:41:16.309082

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:14.315368
- **Completed**: 2025-12-04 08:41:16.317470

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:16.308615
- **Completed**: 2025-12-04 08:41:18.311331

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:16.309359
- **Completed**: 2025-12-04 08:41:18.310889

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status}
                         ...
openstates_cli.py: error: argument command: invalid choice: 'oh' (choose from 'ingest-people', 'ingest-jurisdictions', 'ingest-bills', 'ingest-committees', 'ingest-events', 'ingest-vote-events', 'ingest-organization
- **Started**: 2025-12-04 08:41:16.318232
- **Completed**: 2025-12-04 08:41:18.320411


## Performance Metrics
- **Average Records per Second**: 369.31
- **Average Job Duration**: 0:00:19.679359
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
**Report Generated**: 2025-12-04 09:22:47
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
