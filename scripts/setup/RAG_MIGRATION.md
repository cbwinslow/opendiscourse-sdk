# RAG DB Migration Script

A new migration script `migrate_rag_db.py` has been added to `scripts/setup/`.

## Usage

1. Install requirements (if not already):
   ```bash
   pip install psycopg2-binary
   ```

2. Run the migration script:
   ```bash
   python scripts/setup/migrate_rag_db.py --db-url postgresql://user:pass@host:port/dbname
   # Or set DATABASE_URL env var and run without --db-url
   ```

This will apply the schema in `rag_db_schema.sql` to your PostgreSQL database (with pgvector).
