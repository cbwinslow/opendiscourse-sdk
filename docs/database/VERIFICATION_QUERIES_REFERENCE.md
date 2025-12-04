# Congress Members Data Verification Queries

This document contains all the verification queries, views, procedures, and functions created for monitoring and analyzing the Congress members data.

## Database Objects Created

### Views (in `migrations/004_member_verification_views.sql`)

#### 1. `congress.member_counts_by_congress`
Shows member counts by congress number.
```sql
SELECT * FROM congress.member_counts_by_congress ORDER BY congress_number;
```

#### 2. `congress.longest_serving_members`
Shows members with most terms served.
```sql
SELECT * FROM congress.longest_serving_members LIMIT 10;
```

#### 3. `congress.member_term_details`
Detailed view of all member terms with full information.
```sql
SELECT * FROM congress.member_term_details 
WHERE bioguide_id = 'S001207' 
ORDER BY congress_number;
```

#### 4. `congress.party_distribution_by_congress`
Party distribution by congress with percentages.
```sql
SELECT * FROM congress.party_distribution_by_congress 
WHERE congress_number = 118;
```

#### 5. `congress.state_representation_by_congress`
State representation by congress and chamber.
```sql
SELECT * FROM congress.state_representation_by_congress 
WHERE congress_number = 118;
```

#### 6. `congress.chamber_distribution_by_congress`
Chamber distribution by congress.
```sql
SELECT * FROM congress.chamber_distribution_by_congress 
WHERE congress_number = 118;
```

#### 7. `congress.members_with_incomplete_data`
Members missing required data fields.
```sql
SELECT * FROM congress.members_with_incomplete_data;
```

#### 8. `congress.duplicate_member_terms`
Detects duplicate member terms for data quality.
```sql
SELECT * FROM congress.duplicate_member_terms;
```

### Procedures (in `migrations/005_member_verification_procedures.sql`)

#### 1. `congress.get_member_statistics(congress_number)`
Gets comprehensive member statistics.
```sql
CALL congress.get_member_statistics(118);
CALL congress.get_member_statistics(); -- Overall stats
```

#### 2. `congress.check_data_quality()`
Checks for data quality issues.
```sql
CALL congress.check_data_quality();
```

#### 3. `congress.clean_duplicate_terms()`
Removes duplicate member terms.
```sql
CALL congress.clean_duplicate_terms();
```

#### 4. `congress.get_member_career_summary(bioguide_id)`
Shows career summary for a specific member.
```sql
CALL congress.get_member_career_summary('S001207');
```

### Functions (in `migrations/006_member_verification_functions.sql`)

#### 1. `congress.get_member_count_by_congress(congress_number)`
Returns member count for specific congress.
```sql
SELECT congress.get_member_count_by_congress(118);
```

#### 2. `congress.get_unique_member_count()`
Returns total unique member count.
```sql
SELECT congress.get_unique_member_count();
```

#### 3. `congress.get_total_member_terms_count()`
Returns total member terms count.
```sql
SELECT congress.get_total_member_terms_count();
```

#### 4. `congress.get_longest_serving_members(limit)`
Returns longest serving members.
```sql
SELECT * FROM congress.get_longest_serving_members(10);
```

#### 5. `congress.get_party_distribution(congress_number)`
Returns party distribution for specific congress.
```sql
SELECT * FROM congress.get_party_distribution(118);
```

#### 6. `congress.get_chamber_distribution(congress_number)`
Returns chamber distribution for specific congress.
```sql
SELECT * FROM congress.get_chamber_distribution(118);
```

#### 7. `congress.get_state_representation(congress_number, chamber_code)`
Returns state representation by congress and chamber.
```sql
SELECT * FROM congress.get_state_representation(118, 'house');
SELECT * FROM congress.get_state_representation(118); -- All chambers
```

#### 8. `congress.check_member_data_completeness()`
Returns data completeness report.
```sql
SELECT * FROM congress.check_member_data_completeness();
```

#### 9. `congress.get_member_career_path(bioguide_id)`
Returns complete career path for a member.
```sql
SELECT * FROM congress.get_member_career_path('S001207');
```

#### 10. `congress.get_congress_summary(congress_number)`
Returns summary statistics for a congress.
```sql
SELECT * FROM congress.get_congress_summary(118);
```

## Python Verification Utility

The `scripts/verify_congress_data.py` provides easy access to all verification queries:

### Command Line Usage

```bash
# Show member statistics
python scripts/verify_congress_data.py --stats

# Show statistics for specific congress
python scripts/verify_congress_data.py --stats --congress 118

# Check data quality
python scripts/verify_congress_data.py --check-quality

# Clean duplicate terms
python scripts/verify_congress_data.py --clean-duplicates

# Get career path for specific member
python scripts/verify_congress_data.py --bioguide S001207

# Show congress summary
python scripts/verify_congress_data.py --summary 118

# Run all default reports
python scripts/verify_congress_data.py
```

### Programmatic Usage

```python
from scripts.verify_congress_data import CongressDataVerifier

verifier = CongressDataVerifier()
verifier.connect()

# Get member counts by congress
counts = verifier.get_member_counts_by_congress()

# Get longest serving members
longest = verifier.get_longest_serving_members(limit=10)

# Check data quality
verifier.check_data_quality()

# Get specific member career path
career = verifier.get_member_career_path('S001207')

verifier.close()
```

## Common Verification Queries

### Quick Data Overview
```sql
-- Total counts
SELECT 
    (SELECT COUNT(*) FROM congress.members) as unique_members,
    (SELECT COUNT(*) FROM congress.member_terms) as total_terms,
    (SELECT COUNT(DISTINCT congress_number) FROM congress.member_terms) as congresses_covered;

-- Member counts by congress
SELECT * FROM congress.member_counts_by_congress ORDER BY congress_number;

-- Longest serving members
SELECT * FROM congress.longest_serving_members LIMIT 10;
```

### Data Quality Checks
```sql
-- Check for missing data
SELECT * FROM congress.check_member_data_completeness();

-- Check for duplicates
SELECT * FROM congress.duplicate_member_terms;

-- Run comprehensive data quality check
CALL congress.check_data_quality();
```

### Congress-Specific Analysis
```sql
-- Congress 118 summary
SELECT * FROM congress.get_congress_summary(118);

-- Party distribution for Congress 118
SELECT * FROM congress.get_party_distribution(118);

-- Chamber distribution for Congress 118
SELECT * FROM congress.get_chamber_distribution(118);

-- State representation for Congress 118
SELECT * FROM congress.get_state_representation(118);
```

### Member-Specific Analysis
```sql
-- Career path for Mikie Sherrill
SELECT * FROM congress.get_member_career_path('S001207');

-- Career summary for Mikie Sherrill
CALL congress.get_member_career_summary('S001207');

-- Find members who served in both House and Senate
SELECT bioguide_id, first_name, last_name, 
       COUNT(DISTINCT chamber_code) as chambers_served
FROM congress.member_details
GROUP BY bioguide_id, first_name, last_name
HAVING COUNT(DISTINCT chamber_code) > 1
ORDER BY chambers_served DESC;
```

## Performance Considerations

- Views are pre-defined queries that can be used directly
- Functions are optimized for specific use cases
- Procedures are used for operations that don't return data (cleaning, reporting)
- All database objects are created with appropriate permissions in the congress schema

## Maintenance

- Views automatically reflect current data
- Functions and procedures can be modified as needed
- New verification queries can be added to the migration files
- The Python utility can be extended with additional methods

These verification tools provide comprehensive monitoring and analysis capabilities for the Congress members data, ensuring data quality and enabling detailed historical analysis.