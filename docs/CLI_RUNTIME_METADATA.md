# Codex CLI Runtime Metadata Guide

This repository currently stores Codex CLI runtime metadata (configuration, sessions, and logs) rather than application code. Keep the files in their canonical locations so the CLI can boot and reconnect to MCP servers without errors.

## Canonical Files and Layout
- Root configs: `config.toml`, `config.json`, `version.json` (loaded by the CLI at startup).
- Session transcripts: `sessions/YYYY/MM/DD/*.jsonl`.
- Operational logs: `log/codex-tui.log`.
- Archives: `history.jsonl` and `internal_storage.json` are append-only; rotate only after taking a backup.
- Keep trusted project roots and sandbox settings documented in `config.toml` so later runs preserve permissions.

## Validation and Smoke Tests
Run quick validation after any config change:

```bash
# Validate JSON formatting
python -m json.tool config.json

# Validate TOML (Python 3.11+)
python - <<'PY'
import pathlib, tomllib
tomllib.loads(pathlib.Path("config.toml").read_text())
PY

# Smoke test the CLI and MCP connections
codex --config config.toml
tail -n 50 log/codex-tui.log
```

For larger edits, replay a recent session by copying a prior entry in `sessions/YYYY/MM/DD/*.jsonl` into a new file and confirming the CLI rehydrates it without warnings.

## Formatting and Style
- JSON uses two-space indentation.
- TOML uses one setting per line with single-quoted string literals to match the current style.
- Document paths as repo-relative (for example, `sessions/2025/11/26/run.jsonl`) so other agents can copy them directly.

## Security and Secrets
- Do not place API tokens or credentials in `auth.json` or any tracked file; use local secret stores and placeholders when documenting keys.
- Scrub or redact user-identifying data before sharing log excerpts from `sessions/**/*.jsonl` or `log/codex-tui.log`.
- Note when newly trusted roots in `config.toml` require elevated sandbox permissions and why.

## Maintenance Notes
- Treat `history.jsonl` and `internal_storage.json` as append-only archives; back up before rotating or truncating.
- Keep `config.toml` and `config.json` authoritative; update both if a setting needs to stay in sync.
- After edits, record validation commands and any observed log output in the relevant journal so follow-on agents have a paper trail.
