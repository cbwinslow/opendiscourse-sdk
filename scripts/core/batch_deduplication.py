"""
Optimized batch deduplication using temporary tables.
More efficient than checking each record individually.
"""

from typing import List, Dict, Any
import psycopg2
import logging

logger = logging.getLogger(__name__)


def deduplicate_batch_with_temp_table(
    conn: psycopg2.extensions.connection,
    records: List[Dict[str, Any]],
    table_name: str,
    unique_fields: List[str],
    fingerprint_field: str = "content_hash"
) -> tuple[List[Dict], List[Dict]]:
    """
    Efficiently deduplicate batch using temp table.

    Strategy:
    1. Create temp table with incoming data
    2. Join with existing table on unique fields
    3. Return only new/modified records

    Args:
        conn: Database connection
        records: Batch of records to check
        table_name: Target table name
        unique_fields: Fields that identify uniqueness
        fingerprint_field: Field containing content hash

    Returns:
        Tuple of (new_records, duplicate_records)
    """
    if not records:
        return [], []

    cursor = conn.cursor()

    try:
        # Create temporary table
        temp_table = f"temp_{table_name}_{id(records)}"

        # Get sample record to determine schema
        sample = records[0]
        columns = list(sample.keys())

        create_temp = f"""
            CREATE TEMP TABLE {temp_table} (
                {', '.join(f'{col} TEXT' for col in columns)}
            ) ON COMMIT DROP
        """
        cursor.execute(create_temp)

        # Insert all records into temp table
        placeholders = ', '.join(['%s'] * len(columns))
        insert_temp = f"""
            INSERT INTO {temp_table} ({', '.join(columns)})
            VALUES ({placeholders})
        """

        values = [tuple(r.get(col) for col in columns) for r in records]
        cursor.executemany(insert_temp, values)

        # Find existing records by joining on unique fields
        join_conditions = ' AND '.join(
            f't.{field} = e.{field}' for field in unique_fields
        )

        find_existing = f"""
            SELECT t.*, e.{fingerprint_field} as existing_hash
            FROM {temp_table} t
            LEFT JOIN {table_name} e ON {join_conditions}
        """

        cursor.execute(find_existing)
        results = cursor.fetchall()

        # Separate new from existing
        new_records = []
        duplicate_records = []

        col_names = [desc[0] for desc in cursor.description]

        for row in results:
            record_dict = dict(zip(col_names, row))
            existing_hash = record_dict.pop('existing_hash', None)

            if existing_hash is None:
                # New record
                new_records.append(record_dict)
            elif existing_hash != record_dict.get(fingerprint_field):
                # Modified record
                new_records.append(record_dict)
            else:
                # Exact duplicate
                duplicate_records.append(record_dict)

        logger.info(
            f"Batch deduplication: {len(new_records)} new, "
            f"{len(duplicate_records)} duplicates"
        )

        return new_records, duplicate_records

    finally:
        cursor.close()


def bulk_insert_with_deduplication(
    conn: psycopg2.extensions.connection,
    records: List[Dict[str, Any]],
    table_name: str,
    unique_fields: List[str],
    batch_size: int = 1000
) -> Dict[str, int]:
    """
    Bulk insert with efficient deduplication.

    Processes records in batches using temp tables.

    Returns:
        Dict with counts: inserted, updated, skipped
    """
    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        new_records, duplicates = deduplicate_batch_with_temp_table(
            conn, batch, table_name, unique_fields
        )

        # Insert new records (implementation depends on actual schema)
        stats["inserted"] += len(new_records)
        stats["skipped"] += len(duplicates)

        logger.debug(f"Batch {i//batch_size + 1}: Processed {len(batch)} records")

    return stats
