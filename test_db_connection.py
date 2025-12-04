#!/usr/bin/env python3
"""
Test database connection using docker exec
"""

import subprocess
import json


def test_docker_database():
    """Test database connection using docker exec"""
    try:
        # Test basic connection
        result = subprocess.run(
            [
                "docker",
                "exec",
                "cbwinslow-penpot-postgres-1",
                "psql",
                "-U",
                "penpot",
                "-d",
                "penpot",
                "-c",
                "SELECT 'connection_successful' as status;",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Database connection successful!")

            # Check tables
            tables_result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "cbwinslow-penpot-postgres-1",
                    "psql",
                    "-U",
                    "penpot",
                    "-d",
                    "penpot",
                    "-c",
                    """
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema IN ('congress', 'govinfo', 'openstates', 'incremental', 'ingestion')
                ORDER BY table_schema, table_name;
                """,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if tables_result.returncode == 0:
                lines = tables_result.stdout.strip().split("\n")
                headers = lines[0].split("|")
                table_count = len(lines) - 2  # Subtract header and separator

                print(f"📊 Found {table_count} tables")

                # Show schemas
                schemas = set()
                for line in lines[2:]:
                    if line.strip():
                        schema = line.split("|")[0].strip()
                        if schema:
                            schemas.add(schema)

                print(f"📁 Schemas found: {', '.join(sorted(schemas))}")

                return {
                    "status": "success",
                    "tables_count": table_count,
                    "schemas": list(schemas),
                    "connection_method": "docker_exec",
                }
            else:
                print(f"❌ Error querying tables: {tables_result.stderr}")
                return {"status": "error", "error": tables_result.stderr}
        else:
            print(f"❌ Database connection failed: {result.stderr}")
            return {"status": "error", "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Connection timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    result = test_docker_database()
    print(json.dumps(result, indent=2))
