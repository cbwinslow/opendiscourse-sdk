# SQL Schema Consolidation - Migration Guide

## Overview

This document outlines the consolidation of redundant SQL migration files across the OpenDiscourse project. We have successfully eliminated duplicate schemas and established a single source of truth for each data source.

## Changes Made

### 1. Congress.gov Schema Consolidation

**Before:**
- `/congress.gov/migrations/` - Normalized relational schema (3 files)
- `/opendiscourse-mcp/mcp_server/sql/congress_schema.sql` - Denormalized JSONB schema
- `/opendiscourse-mcp/mcp_server/sql/congress_schema_fixed.sql` - Duplicate of above

**After:**
- `/migrations/001_congress_schema.sql` - **Single consolidated schema**

**Key Features:**
- Normalized relational design with proper foreign keys
- UUID primary keys for entities
- Comprehensive indexing for performance
- Full-text search capabilities
- Proper schema organization under `congress.` namespace

### 2. GovInfo Schema Consolidation

**Before:**
- `/govinfo/sql/001_create_tables.sql` - Comprehensive relational schema
- `/opendiscourse-mcp/mcp_server/sql/govinfo_schema.sql` - Simplified JSONB schema

**After:**
- `/migrations/002_govinfo_schema.sql` - **Single consolidated schema**

**Key Features:**
- Complete relational model with proper normalization
- Bulk data management tables
- Comprehensive voting and attendance tracking
- Processing and audit logging
- Full API snapshot capabilities

### 3. Removed Redundant Files

The following duplicate schema files have been removed:
- `opendiscourse-mcp/mcp_server/sql/congress_schema.sql`
- `opendiscourse-mcp/mcp_server/sql/congress_schema_fixed.sql`
- `opendiscourse-mcp/mcp_server/sql/govinfo_schema.sql`

## Migration Path

### For New Deployments

Use the consolidated schemas in `/migrations/`:
```sql
-- Apply in order
\i migrations/001_congress_schema.sql
\i migrations/002_govinfo_schema.sql
```

### For Existing Deployments

If you have existing data using the old schemas:

1. **Backup existing data:**
```sql
pg_dump -h localhost -U username -d database > backup_before_migration.sql
```

2. **Create migration scripts** to transform data from old to new schema structure:
   - Map UUID primary keys from old integer/text keys
   - Migrate JSONB columns to normalized tables where appropriate
   - Update foreign key references

3. **Test migration** in development environment before production deployment

### Schema Differences

#### Congress.gov Changes

| Old Schema | New Schema | Notes |
|------------|------------|-------|
| `congress_bills` (TEXT PK) | `congress.bills` (UUID PK) | Primary key type changed |
| JSONB columns for relationships | Normalized tables | Better data integrity |
| Separate schema files | Single consolidated file | Easier management |

#### GovInfo Changes

| Old Schema | New Schema | Notes |
|------------|------------|-------|
| Simplified structure | Full relational model | Complete data model |
| Missing audit tables | Comprehensive audit/logging | Better tracking |
| Limited voting data | Full voting/attendance | Complete coverage |

## Benefits Achieved

1. **Single Source of Truth**: Each data source now has one definitive schema
2. **Better Data Integrity**: Proper foreign keys and normalization
3. **Improved Performance**: Comprehensive indexing strategy
4. **Easier Maintenance**: Single file per data source
5. **Full Feature Coverage**: Combined best features from all versions

## Updated .gitignore

The `.gitignore` file has been updated to allow access to the new consolidated schemas while still blocking other SQL files:

```
# Database
*.sqlite3
*.db
*.sql
*.dump

# Exceptions: Allow migration SQL files
!congress.gov/migrations/*.sql
!govinfo/sql/*.sql
!opendiscourse-mcp/mcp_server/sql/*.sql
!opendiscourse-mcp/congress_ingest_bundle/*.sql
!opendiscourse-mcp/*.sql
!migrations/*.sql
```

## Next Steps

1. Update any deployment scripts to use the new consolidated schemas
2. Update documentation references to old schema files
3. Consider creating migration scripts for existing deployments
4. Update ERD diagrams to reflect the consolidated schemas

## Rollback Plan

If issues arise with the consolidated schemas:

1. Restore the original schema files from git history
2. Update `.gitignore` to remove the new exceptions
3. Use backup databases created before migration

## Support

For questions about the schema consolidation:
- Review the consolidated schema files in `/migrations/`
- Check existing ingestion scripts for compatibility
- Test in development environment before production deployment