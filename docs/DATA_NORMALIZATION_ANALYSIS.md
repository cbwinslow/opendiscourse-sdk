# Congress Data Normalization Analysis

## Current Situation

### ❌ Problem: Incomplete Normalization
```sql
-- Current: Members table only (deduplicated)
congress.members: 1,901 unique members
congress.member_terms: 0 records ← MISSING!
```

### ❌ What This Breaks
1. **Time-based analysis**: Can't query "How many Democrats served in 2018?"
2. **Service tracking**: Don't know when members served
3. **Career progression**: Can't track party switches or chamber changes
4. **Accurate counts**: Any time-specific report will be wrong

## Proper Normalization Structure

### ✅ What We Should Have
```sql
-- Members table: Static information (name, bioguide_id, etc.)
congress.members: 1,901 unique records

-- Member terms table: Historical service records
congress.member_terms: ~10,000+ records expected
  - Each row = one member's service in one congress
  - Tracks: congress_number, chamber, party, dates, etc.
```

## Example: Proper Data Structure

### Member (Static Info)
| bioguide_id | first_name | last_name | official_full_name |
|-------------|------------|-----------|-------------------|
| W000817     | Warren     | Elizabeth | Warren, Elizabeth |

### Member Terms (Historical Service)
| bioguide_id | congress_number | chamber_code | party_code | start_date | end_date |
|-------------|-----------------|--------------|-----------|------------|----------|
| W000817     | 113             | senate       | D         | 2013-01-01 | 2014-12-31 |
| W000817     | 114             | senate       | D         | 2015-01-01 | 2016-12-31 |
| W000817     | 115             | senate       | D         | 2017-01-01 | 2018-12-31 |
| W000817     | 116             | senate       | D         | 2019-01-01 | 2020-12-31 |
| W000817     | 117             | senate       | D         | 2021-01-01 | 2022-12-31 |
| W000817     | 118             | senate       | D         | 2023-01-01 | 2024-12-31 |

## Impact on Analysis

### ❌ With Current Structure
```sql
-- This query gives WRONG results
SELECT COUNT(*) as democrat_count 
FROM congress.members 
WHERE party = 'Democratic';
-- Result: 0 (because party isn't in members table!)
```

### ✅ With Proper Normalization
```sql
-- This query gives CORRECT results for 2023
SELECT COUNT(DISTINCT mt.bioguide_id) as democrat_count
FROM congress.member_terms mt
JOIN congress.parties p ON mt.party_code = p.party_code
WHERE mt.congress_number = 118 
  AND p.party_name = 'Democratic';
-- Result: Accurate count of Democrats in 118th Congress
```

## Reporting Examples That Currently Fail

### 1. Party Composition Over Time
```sql
-- ❌ Can't do this now
SELECT 
  congress_number,
  COUNT(DISTINCT bioguide_id) as total_members,
  SUM(CASE WHEN party_name = 'Democratic' THEN 1 ELSE 0 END) as democrats
FROM congress.member_terms
GROUP BY congress_number;
```

### 2. Member Tenure Analysis
```sql
-- ❌ Can't analyze career length
SELECT 
  m.official_full_name,
  COUNT(mt.congress_number) as congresses_served,
  MIN(mt.start_date) as first_service,
  MAX(mt.end_date) as last_service
FROM congress.members m
JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id
GROUP BY m.bioguide_id, m.official_full_name;
```

### 3. Chamber Switching
```sql
-- ❌ Can't track House ↔ Senate moves
SELECT 
  m.official_full_name,
  STRING_AGG(DISTINCT chamber_code, ' → ') as career_path
FROM congress.members m
JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id
GROUP BY m.bioguide_id, m.official_full_name
HAVING COUNT(DISTINCT chamber_code) > 1;
```

## Solution: Complete the Normalization

### Step 1: Ingest Member Terms Data
We need to modify our ingestion script to populate the `member_terms` table with the historical service data from the API.

### Step 2: Update Schema References
Ensure all foreign keys and relationships are properly maintained.

### Step 3: Validate Data Integrity
Check for completeness and accuracy of the historical records.

## Recommendation

**We need to complete the ingestion process** by populating the `member_terms` table. The current approach of deduplicating members is correct, but we must preserve the historical service context in the `member_terms` table.

This will give us:
- ✅ Accurate time-based analysis
- ✅ Complete service history tracking  
- ✅ Proper reporting capabilities
- ✅ Career progression analysis
- ✅ Data integrity across time periods