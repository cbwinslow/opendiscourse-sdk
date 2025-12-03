"""Generate OpenAPI specification for the OpenDiscourse API."""

import json
from pathlib import Path

from opendiscourse.main import app


def main() -> None:
    """Write the FastAPI OpenAPI schema to docs/api/openapi.json."""
    schema = app.openapi()
    out_path = Path(__file__).resolve().parents[1] / "docs" / "api" / "openapi.json"
    out_path.write_text(json.dumps(schema, indent=2))
    print(f"OpenAPI spec written to {out_path}")


if __name__ == "__main__":
    main()
