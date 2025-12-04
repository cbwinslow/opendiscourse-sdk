#!/usr/bin/env python3
"""
Simple database connection test for ingestion system
"""

import subprocess
import json
import os


def test_database_connection():
    """Test database connection and return status"""
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
                "opendiscourse",
                "-c",
                "SELECT 'connection_successful' as status;",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Database connection successful!")

            # Check schemas
            schemas_result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "cbwinslow-penpot-postgres-1",
                    "psql",
                    "-U",
                    "penpot",
                    "-d",
                    "opendiscourse",
                    "-c",
                    """
                SELECT DISTINCT table_schema 
                FROM information_schema.tables 
                WHERE table_schema IN ('congress', 'govinfo', 'openstates', 'incremental', 'ingestion')
                ORDER BY table_schema;
                """,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            schemas = []
            if schemas_result.returncode == 0:
                for line in schemas_result.stdout.strip().split("\n")[2:]:  # Skip headers
                    schema = line.strip()
                    if schema and schema != "table_schema":
                        schemas.append(schema)

            # Check tables in each schema
            tables_info = []
            for schema in schemas:
                tables_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "cbwinslow-penpot-postgres-1",
                        "psql",
                        "-U",
                        "penpot",
                        "-d",
                        "opendiscourse",
                        "-c",
                        f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{schema}'
                    ORDER BY table_name;
                    """,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if tables_result.returncode == 0:
                    for line in tables_result.stdout.strip().split("\n")[2:]:  # Skip headers
                        table = line.strip()
                        if table and table != "table_name":
                            tables_info.append({"schema": schema, "table": table})

            return {
                "status": "success",
                "schemas": schemas,
                "tables": tables_info,
                "total_tables": len(tables_info),
                "connection_method": "docker_exec",
            }
        else:
            print(f"❌ Database connection failed: {result.stderr}")
            return {"status": "error", "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Connection timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def test_api_keys():
    """Test API key configuration"""
    from config.api_config import validate_api_configs

    print("Testing API configuration...")
    results = validate_api_configs()

    for provider, result in results.items():
        if result["status"] == "ok":
            print(f"✅ {provider}: Configuration valid")
            print(f"   URL: {result['base_url']}")
            print(f"   API Key: {'Set' if result['api_key_set'] else 'Not set'}")
        else:
            print(f"❌ {provider}: {result['error']}")
            print(f"   Environment variable: {result['api_key_env_var']}")
        print()

    return results


if __name__ == "__main__":
    print("=== OpenDiscourse Ingestion System Test ===")
    print()

    # Test database
    print("1. Testing Database Connection:")
    db_result = test_database_connection()
    print(json.dumps(db_result, indent=2))
    print()

    # Test API keys
    print("2. Testing API Configuration:")
    api_results = test_api_keys()
    print()

    # Summary
    print("3. Summary:")
    if db_result["status"] == "success":
        print(f"   ✅ Database: Connected ({db_result['total_tables']} tables)")
        print(f"   ✅ Schemas: {', '.join(db_result['schemas'])}")
    else:
        print(f"   ❌ Database: {db_result['error']}")

    api_valid_count = sum(1 for r in api_results.values() if r["status"] == "ok")
    if api_valid_count == len(api_results):
        print(f"   ✅ API Keys: All {api_valid_count} providers configured")
    else:
        print(f"   ⚠️  API Keys: {api_valid_count}/{len(api_results)} providers configured")

    print()
    if db_result["status"] == "success" and api_valid_count > 0:
        print("🎉 System is ready for ingestion!")
    else:
        print("⚠️  System needs configuration before ingestion can proceed.")
