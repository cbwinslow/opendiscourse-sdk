
# Parallel Bulk Ingestion Report - Votes & Bill Details
# Generated: 2025-12-04 00:04:39

## Execution Summary
- **Start Time**: 2025-12-04 00:04:13
- **End Time**: 2025-12-04 00:04:39
- **Total Duration**: 0:00:26.083321
- **Total Jobs**: 123
- **Completed Jobs**: 0
- **Failed Jobs**: 123
- **Success Rate**: 0.0%

## Records Processed
- **Total Records**: 1,064
- **Successful Records**: 0
- **Failed Records**: 1,064

## Source Breakdown

### Congress Votes
- **Jobs**: 56
- **Records**: 1,064
- **Success Rate**: 0.0%

### Congress Bill Details
- **Jobs**: 7
- **Records**: 0
- **Success Rate**: 0.0%

### OpenStates Votes
- **Jobs**: 30
- **Records**: 0
- **Success Rate**: 0.0%

### OpenStates Bill Details
- **Jobs**: 30
- **Records**: 0
- **Success Rate**: 0.0%

## Performance Metrics
- **Average Records per Second**: 40.79
- **Average Job Duration**: 0:00:00.212060
- **Peak Parallel Jobs**: 10
- **Database Pool Size**: 20 connections

## Database Statistics

Error getting final database stats: column "tablename" does not exist
LINE 2:                     SELECT schemaname, tablename,
                                               ^



## Recommendations

1. **Review Vote Data**: Verify vote records are properly linked to bills
2. **Check Bill Details**: Ensure bill details contain amendments, summaries, and texts
3. **Monitor Database Growth**: Track new tables growth over time
4. **Optimize Parallel Processing**: Adjust worker count based on system performance

## Next Steps

1. **Verify Data Quality**: Run data validation queries on new data
2. **Update Analytics**: Refresh any analytics dashboards with new data
3. **Archive Logs**: Archive parallel ingestion logs for future reference
4. **Plan Incremental Updates**: Set up daily/weekly incremental ingestion for votes

---
**Report Generated**: 2025-12-04 00:04:39
**Script Location**: /home/cbwinslow/Videos/opendiscourse/scripts/parallel_bulk_ingestion.py
