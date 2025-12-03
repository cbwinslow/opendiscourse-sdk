# Congress CLI Ingestion Bugs

## Identified Issues

### 1. ✅ FIXED: Schema Mismatch in Committees Table
**Status:** Fixed
**Severity:** High
**Component:** `congress_cli.py::ingest_committees`

**Problem:**
- The `congress.committees` table in the database schema does not have a `jurisdiction` column
- The `ingest_committees` function and `transform_congress_committee` were trying to insert this column
- Error: `column "jurisdiction" of relation "committees" does not exist`

**Fix Applied:**
- Removed `jurisdiction` from the INSERT query in `ingest_committees()` (line 902)
- Removed `jurisdiction` from `transform_congress_committee()` return tuple (line 160)

**Verification:**
- Successfully ingested 816 committees for Congress 118

---

### 2. ⚠️ IN PROGRESS: Votes Ingestion Endpoint Errors
**Status:** Needs Fix
**Severity:** High
**Component:** `congress_cli.py::ingest_votes`

**Problem:**
- Originally used `/roll-call-vote/{congress}/{chamber}/{session}` endpoint which returns 404
- Congress.gov API only supports `/house-vote` for listing votes
- Senate votes not available via list endpoint

**Current State:**
- Code updated to use `/house-vote` endpoint
- Needs verification with real run

**Remaining Work:**
- Test `/house-vote` ingestion
- Document Senate vote limitation
- Consider using GovInfo API for Senate votes

---

### 3. ⚠️ DEPENDENCY: Committee Members Requires Parent Data
**Status:** Fixed (via fixing committees)
**Severity:** Medium
**Component:** `congress_cli.py::ingest_committee_members`

**Problem:**
- `ingest_committee_members` queries `congress.committees` table
- If committees table is empty (from dry-runs), ingestion silently fails with 0 records

**Fix:**
- Ensured `ingest-committees` runs before `ingest-committee-members`
- Added logging to show number of committees found

**Verification Needed:**
- Run `ingest-committee-members` now that committees are populated

---

### 4. ⚠️ TODO: Transform Function Data Mapping
**Status:** Needs Review
**Severity:** Medium
**Components:** Multiple transform functions

**Problem:**
- Transform functions may not correctly map API response fields to database schema
- Need to verify:
  - `transform_vote()` - positions JSONB structure
  - `transform_committee_member()` - field mappings
  - `transform_bill_*()` functions - natural key to UUID lookups

**Required:**
- Test each transform function with actual API responses
- Update mapping_test.py with real API data

---

### 5. ⚠️ TODO: Bill Details Ingestion Requires Bills Table
**Status:** Known Issue
**Severity:** Medium
**Component:** `congress_cli.py::ingest_bill_details`

**Problem:**
- All bill detail ingestion functions (actions, cosponsors, subjects, titles, related bills) query `congress.bills` table
- Uses subquery to lookup `bill_id` UUID from natural keys
- Will fail if bills table is empty or bill not found

**Recommendation:**
- Always run `ingest-bills` before any bill detail ingestion
- Add error handling/logging when bill not found in database

---

## Summary
- ✅ 1 Fixed: Committee schema mismatch
- ⚠️ 4 Identified issues requiring attention
- 🎯 Next: Test votes ingestion, verify committee members, create GitHub issues
