# GitHub Issues Seed Status

Status: 0 issues created; 9 failed during REST seed (401 Bad credentials).

Context:
- Payloads: 10 issues defined in `github_issues_payload.json`.
- Seed method: REST-based creation via `scripts/create_github_issues_rest.py` using `GITHUB_TOKEN`.
- Result: All attempts failed due to invalid/insufficient credentials.

What happened:
- 9 REST calls returned 401 Bad credentials; no issues created.
- An attempt was made using the token you provided earlier (token hidden in logs).

Current blockers:
- A valid GitHub token with repo access is required to seed issues.
- If your org uses SSO, a dedicated token with proper scopes must be issued.

Next steps once credentials are available:
- Re-run: `python3 scripts/create_github_issues_rest.py` to seed the 10 issues.
- Output: `github_issues_created.json` containing created issues.
- Optional: initialize a GitHub Project V2 board and attach issues as cards.

Notes:
- We’ll keep the prepared payloads and issue descriptions ready to seed immediately after credentials arrive.
