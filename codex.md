# Codex Agent Briefing (OpenDiscourse Runtime Repo)

This repo primarily stores Codex CLI runtime metadata, session logs, and documentation—not application code. Keep configs canonical so the CLI boots cleanly and MCP servers reconnect without new errors.

## Quick Orientation
- Read: `DOCUMENTATION_INDEX.md` (structure and status), `docs/CLI_RUNTIME_METADATA.md` (runtime config care), `agents.md` (mandates, especially API key/database standards), `docs/journal/JOURNAL_2025_11_26.md` (latest session notes).
- Canonical configs: `config.toml`, `config.json`, `version.json`. Sessions live under `sessions/YYYY/MM/DD/*.jsonl`; logs in `log/codex-tui.log`; archives `history.jsonl` and `internal_storage.json` are append-only.
- Current priorities (from `DOCUMENTATION_INDEX.md`): fix bills ingestion (chamber mapping), validate configs, keep documentation consistent. One test still failing in `test_minimal.py`.

## Validation Commands (run after config edits)
```bash
# Validate JSON
python -m json.tool config.json

# Validate TOML (Python 3.11+)
python - <<'PY'
import pathlib, tomllib
tomllib.loads(pathlib.Path("config.toml").read_text())
PY

# Smoke test CLI + MCP
codex --config config.toml
tail -n 50 log/codex-tui.log
```
For larger edits, replay a prior session by copying an entry in `sessions/YYYY/MM/DD/*.jsonl` into a new file and ensure the CLI rehydrates without warnings.

## Security & Connectivity
- Never commit API tokens or secrets; use local secret stores. Scrub/redact before sharing logs from `sessions/**/*.jsonl` or `log/codex-tui.log`.
- DB connections must use the socket host: `database='opendiscourse'`, `user='cbwinslow'`, `host='/var/run/postgresql'` (not `localhost`, not `cbwinslow` DB).
- If adding trusted roots/sandbox changes in `config.toml`, note why elevated permissions are needed.

## Ingestion/Billing Context (what broke)
- Bills ingestion failed due to chamber code mismatch (`House` vs `house`). Map origin chamber to lowercase before inserts.
- Architecture was over-complex; aim for minimal path: API → transform → insert with validation and tests.
- API key enforcement is mandatory (see `agents.md`): all calls must load keys from env, reject demo/placeholder keys, and fail fast.

## Where to Look First (next agent checklist)
1) Open `DOCUMENTATION_INDEX.md` to see the current status/next steps.  
2) Read `docs/CLI_RUNTIME_METADATA.md` before touching configs.  
3) Review `agents.md` for security/database/API key mandates.  
4) Skim `docs/journal/JOURNAL_2025_11_26.md` for the latest Git/PAT and ingestion lessons.  
5) If working on ingestion/tests, inspect `test_minimal.py` and any scripts referenced in the documentation.

## How to Hand Off
- Record any config validation results and CLI log observations in the journal (`docs/journal/...`) if you change configs or runtimes.
- Keep JSON two-space indented; TOML single-quoted, one setting per line.
- Avoid rewriting unrelated files; do not revert user changes.
