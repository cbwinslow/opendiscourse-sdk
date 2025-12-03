#!/usr/bin/env python3
"""DB health diagnostic for OpenDiscourse
Reads common connection patterns and environment-provided credentials."""

import os
import sys
import json
import urllib.parse as up
import psycopg2


def try_connect(params):
    host = params.get("host")
    dbname = params.get("dbname")
    user = params.get("user")
    password = params.get("password")
    port = params.get("port")
    try:
        conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return {"ok": True, "dbname": dbname, "host": host, "user": user, "port": port}
    except Exception as e:
        return {
            "ok": False,
            "dbname": dbname,
            "host": host,
            "user": user,
            "port": port,
            "error": str(e),
        }


def main():
    results = []

    # Known ingestion patterns (hard-coded in code)
    results.append(
        try_connect({"dbname": "cbwinslow", "user": "cbwinslow", "host": "localhost"})
    )

    # OpenDiscourse OpenStates pattern (may rely on password env)
    results.append(
        try_connect(
            {
                "dbname": "opendiscourse",
                "user": "cbwinslow",
                "host": "localhost",
                "password": os.getenv("DB_PASSWORD"),
            }
        )
    )

    # DATABASE_URL env (optional)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            u = up.urlparse(database_url)
            results.append(
                {
                    "ok": True,
                    "dbname": u.path.lstrip("/"),
                    "host": u.hostname,
                    "port": u.port,
                    "user": u.username,
                    "password_present": bool(u.password),
                }
            )
        except Exception as e:
            results.append({"ok": False, "error": f"DATABASE_URL parse error: {e}"})

    print(json.dumps(results, indent=2))
    if any(r.get("ok") for r in results):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
