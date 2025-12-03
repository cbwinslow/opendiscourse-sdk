
# Comprehensive Bulk Ingestion Report

## Execution Summary
- **Start Time**: 2025-12-03 11:10:15
- **End Time**: 2025-12-03 11:12:09
- **Total Duration**: 0:01:54.408487
- **Total Jobs**: 131
- **Completed Jobs**: 64
- **Failed Jobs**: 67
- **Success Rate**: 48.9%

## Records Processed
- **Total Records**: 782,947
- **Successful Records**: 725,312
- **Failed Records**: 57,635

## Source Breakdown

### Congress.gov
- **Jobs**: 63
- **Records**: 730,387
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

- **Started**: 2025-12-03 11:10:15.447369
- **Completed**: 2025-12-03 11:10:19.454389

### congress_members_114
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-03 11:10:15.457395
- **Completed**: 2025-12-03 11:10:19.469062

### congress_members_115
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-03 11:10:41.488137
- **Completed**: 2025-12-03 11:10:43.493223

### congress_members_116
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-03 11:10:41.505096
- **Completed**: 2025-12-03 11:10:43.506615

### congress_members_117
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-03 11:11:05.527486
- **Completed**: 2025-12-03 11:11:07.530377

### congress_members_118
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-03 11:11:07.530271
- **Completed**: 2025-12-03 11:11:09.533198

### congress_members_119
- **Source**: congress
- **Error**: Process exited with code 2: usage: congress_api_ingest.py [-h] --source {govinfo,congress}
                              [--collection COLLECTION] [--congress CONGRESS]
                              [--bill-type BILL_TYPE]
                              [--start-date START_DATE] [--end-date END_DATE]
                              [--limit LIMIT] [--data-dir DATA_DIR]
congress_api_ingest.py: error: unrecognized arguments: --data-type members

- **Started**: 2025-12-03 11:11:29.662975
- **Completed**: 2025-12-03 11:11:31.668273

### openstates_people_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:31.580490
- **Completed**: 2025-12-03 11:11:33.583681

### openstates_bills_ca
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'ca' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:31.583409
- **Completed**: 2025-12-03 11:11:33.586038

### openstates_people_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:31.668740
- **Completed**: 2025-12-03 11:11:33.671498

### openstates_bills_ny
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'ny' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:33.565950
- **Completed**: 2025-12-03 11:11:35.568464

### openstates_people_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:33.584062
- **Completed**: 2025-12-03 11:11:35.587042

### openstates_bills_tx
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'tx' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:33.586298
- **Completed**: 2025-12-03 11:11:35.588193

### openstates_people_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:33.671893
- **Completed**: 2025-12-03 11:11:35.674403

### openstates_bills_fl
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'fl' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:35.568735
- **Completed**: 2025-12-03 11:11:37.570563

### openstates_people_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:35.587510
- **Completed**: 2025-12-03 11:11:37.591075

### openstates_bills_il
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'il' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:35.588882
- **Completed**: 2025-12-03 11:11:37.591726

### openstates_people_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:35.769455
- **Completed**: 2025-12-03 11:11:37.773416

### openstates_bills_pa
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'pa' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:37.570839
- **Completed**: 2025-12-03 11:11:39.573072

### openstates_people_oh
- **Source**: openstates
- **Error**: Process exited with code 2: usage: openstates_cli.py [-h] [--dry-run] [--batch-size BATCH_SIZE]
                         {ingest-people,ingest-jurisdictions,ingest-bills,ingest-committees,ingest-events,ingest-vote-events,ingest-organizations,ingest-sessions,ingest-all-states,status} ...
openstates_cli.py: error: argument command: invalid choice: 'oh' (choose from ingest-people, ingest-jurisdictions, ingest-bills, ingest-committees, ingest-events, ingest-vote-events, ingest-organizations, ingest-sessions, ingest-all-states,
- **Started**: 2025-12-03 11:11:37.591543
- **Completed**: 2025-12-03 11:11:39.596257


## Performance Metrics
- **Average Records per Second**: 6843.43
- **Average Job Duration**: 0:00:00.873347
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
**Report Generated**: 2025-12-03 11:12:09
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/comprehensive_bulk_ingestion.py
