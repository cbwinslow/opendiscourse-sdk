# ============================================================
# MCP Registry Pack v1.3 — Signed + Makefile + Charts
# ============================================================
# This version extends v1.2 with:
#   • Sigstore signing helper script and CI verification call
#   • Worker /api/verify endpoint that reports SHA256 + signature presence
#   • Latency history table + insertion for health sweeps
#   • Pages UI mini chart to visualize recent latency per server
#   • Seed script to import example registries
#   • Makefile with one-liners for all common tasks
#
# Files included below:
#   - Makefile
#   - scripts/sign_manifest.sh
#   - scripts/verify_via_worker.sh
#   - scripts/seed_examples.sh
#   - src/schema.sql (extended)
#   - src/worker.ts (extended with /api/verify and latency history)
#   - pages/index.html (extended with a simple canvas chart)
#   - .github/workflows/registry-ci.yml (updated to verify)
#
# Placeholders to set:
#   CF_ACCOUNT_ID, D1 database id in wrangler.toml, CI secrets, and Worker URLs.


# =============================================
# File: Makefile
# =============================================
# Makefile with convenient targets for common ops.
# Usage: set env vars as needed, e.g. CF_ACCOUNT_ID, CF_API_TOKEN, ADMIN_API_TOKEN

SHELL := /usr/bin/env bash

bootstrap:
	CF_ACCOUNT_ID=$${CF_ACCOUNT_ID} CF_API_TOKEN=$${CF_API_TOKEN} ADMIN_API_TOKEN=$${ADMIN_API_TOKEN} \
	bash scripts/cf_bootstrap.sh

publish:
	bash scripts/publish_r2.sh mcp_registry.yaml registry/manifest.json

sign:
	bash scripts/sign_manifest.sh

ingest:
	ADMIN_API_TOKEN=$${ADMIN_API_TOKEN} WORKER_ADMIN_INGEST_URL=$${WORKER_ADMIN_INGEST_URL} \
	bash scripts/admin_ingest.sh

cron:
	ADMIN_API_TOKEN=$${ADMIN_API_TOKEN} WORKER_ADMIN_CRON_URL=$${WORKER_ADMIN_CRON_URL} \
	bash scripts/admin_cron.sh

verify:
	WORKER_VERIFY_URL=$${WORKER_VERIFY_URL} bash scripts/verify_via_worker.sh

env:
	tools/env_from_bw.py --template .env.in --out .env --map .env.bwmap.yaml

seed:
	bash scripts/seed_examples.sh

deploy:
	npx wrangler deploy

pages-dev:
	python -m http.server -d pages 8080


# =============================================
# File: scripts/sign_manifest.sh
# =============================================
#!/usr/bin/env bash
# ------------------------------------------------------------
# Script: scripts/sign_manifest.sh
# Author: CBW + GPT-5 Thinking
# Date: 2025-11-04
# Summary: Signs registry/manifest.json with Sigstore (cosign keyless)
# Inputs: COSIGN_EXPERIMENTAL=1   (required for keyless)
#         COSIGN_IDENTITY         (optional OIDC identity selector)
#         COSIGN_FEDERATION       (optional, e.g., 'github-actions')
# Outputs: registry/manifest.sig
# ------------------------------------------------------------
set -euo pipefail

MANIFEST=${MANIFEST:-registry/manifest.json}
SIG=${SIG:-registry/manifest.sig}

command -v cosign >/dev/null 2>&1 || { echo "[ERR] cosign not installed" >&2; exit 1; }
[[ -f "$MANIFEST" ]] || { echo "[ERR] missing $MANIFEST" >&2; exit 1; }

export COSIGN_EXPERIMENTAL=${COSIGN_EXPERIMENTAL:-1}

# Optional: identity claims can be constrained via --identity if provided
IDENT_ARGS=()
if [[ -n "${COSIGN_IDENTITY:-}" ]]; then IDENT_ARGS+=("--identity" "$COSIGN_IDENTITY"); fi

cosign sign-blob --yes --output-signature "$SIG" "${IDENT_ARGS[@]}" "$MANIFEST"

echo "[OK] wrote $SIG"


# =============================================
# File: scripts/verify_via_worker.sh
# =============================================
#!/usr/bin/env bash
# ------------------------------------------------------------
# Script: scripts/verify_via_worker.sh
# Author: CBW + GPT-5 Thinking
# Date: 2025-11-04
# Summary: Calls the Worker's /api/verify to fetch manifest SHA and signature presence.
# Inputs: WORKER_VERIFY_URL (e.g., https://<worker>.workers.dev/api/verify)
# ------------------------------------------------------------
set -euo pipefail

[[ -n "${WORKER_VERIFY_URL:-}" ]] || { echo "WORKER_VERIFY_URL required" >&2; exit 1; }

curl -fsSL "$WORKER_VERIFY_URL" | jq .

echo "[OK] verify call completed"


# =============================================
# File: scripts/seed_examples.sh
# =============================================
#!/usr/bin/env bash
# ------------------------------------------------------------
# Script: scripts/seed_examples.sh
# Author: CBW + GPT-5 Thinking
# Date: 2025-11-04
# Summary: Demonstrates merging one or more public MCP registries into mcp_registry.yaml
# Notes: Replace the example URLs with live registries you trust.
# ------------------------------------------------------------
set -euo pipefail

REG_FILE=${REG_FILE:-mcp_registry.yaml}
SOURCES=(
  # Add known registries here (YAML files):
  # "https://example.com/mcp/registry.yaml"
)

if [[ ${#SOURCES[@]} -eq 0 ]]; then
  echo "[WARN] No example sources configured. Edit scripts/seed_examples.sh and add URLs." >&2
  exit 0
fi

for url in "${SOURCES[@]}"; do
  echo "[merge] $url"
  ./mcpctl.py merge "$url"
done

echo "[OK] merged ${#SOURCES[@]} source(s) into $REG_FILE"


# =============================================
# File: src/schema.sql  (extended for latency history)
# =============================================
-- Existing servers table (as in v1.2) remains unchanged above this line
CREATE TABLE IF NOT EXISTS servers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT,
  tags TEXT,
  repo_url TEXT,
  home_url TEXT,
  docker_image TEXT,
  has_sse INTEGER DEFAULT 0,
  has_ws  INTEGER DEFAULT 0,
  has_http INTEGER DEFAULT 0,
  description TEXT,
  license TEXT,
  maintainers TEXT,
  quality INTEGER DEFAULT 0,
  version TEXT,
  updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_servers_category ON servers(category);
CREATE INDEX IF NOT EXISTS idx_servers_quality ON servers(quality);

-- New: latency history (simple timeseries)
CREATE TABLE IF NOT EXISTS latency (
  server_id TEXT NOT NULL,
  ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ms INTEGER NOT NULL,
  ok INTEGER NOT NULL,
  PRIMARY KEY (server_id, ts)
);
CREATE INDEX IF NOT EXISTS idx_latency_server ON latency(server_id);
CREATE INDEX IF NOT EXISTS idx_latency_ts ON latency(ts);


# =============================================
# File: src/worker.ts (extended)
# =============================================
export interface Env {
  R2: R2Bucket;
  DB: D1Database;
  REGISTRY_PREFIX: string;
  PUBLIC_BASE_URL: string;
  ADMIN_API_TOKEN: string;
}

const json = (data: unknown, init: ResponseInit = {}) =>
  new Response(JSON.stringify(data, null, 2), { headers: { "content-type": "application/json" }, ...init });

function requireAdmin(req: Request, env: Env) {
  const tok = req.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!tok || tok !== env.ADMIN_API_TOKEN) return new Response("Unauthorized", { status: 401 });
  return null;
}

async function handleRegistry(req: Request, env: Env) {
  const url = new URL(req.url);
  const key = env.REGISTRY_PREFIX + url.pathname.replace(/^\/registry\//, "");
  const obj = await env.R2.get(key);
  if (!obj) return new Response("Not found", { status: 404 });
  const hdrs = new Headers();
  if (obj.httpMetadata?.contentType) hdrs.set("content-type", obj.httpMetadata.contentType);
  return new Response(obj.body, { headers: hdrs });
}

async function handleListServers(req: Request, env: Env) {
  const { searchParams } = new URL(req.url);
  const category = searchParams.get("category");
  const tag = searchParams.get("tag");
  const minQ = parseInt(searchParams.get("minQuality") || "0", 10);
  const q = searchParams.get("q");

  let sql = `SELECT * FROM servers WHERE quality >= ?`;
  const args: unknown[] = [minQ];
  if (category) { sql += ` AND category = ?`; args.push(category); }
  if (tag) { sql += ` AND (tags LIKE ?)`; args.push(`%${tag}%`); }
  if (q) { sql += ` AND (id LIKE ? OR name LIKE ? OR description LIKE ?)`; args.push(`%${q}%`, `%${q}%`, `%${q}%`); }
  sql += ` ORDER BY quality DESC, name ASC LIMIT 500`;

  const out = await env.DB.prepare(sql).bind(...args).all();
  return json({ count: out.results?.length || 0, results: out.results || [] });
}

async function handleApiVerify(_req: Request, env: Env) {
  // Returns manifest sha256 and whether a signature object exists in R2.
  const man = await env.R2.get(`${env.REGISTRY_PREFIX}manifest.json`);
  if (!man) return json({ error: "manifest not found" }, { status: 404 });
  const buf = await man.arrayBuffer();
  const sha = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", buf)))
    .map(b => b.toString(16).padStart(2, "0")).join("");
  const sig = await env.R2.get(`${env.REGISTRY_PREFIX}manifest.sig`);
  return json({ sha256: sha, signature_present: !!sig });
}

async function handleAdminIngest(req: Request, env: Env) {
  const unauthorized = requireAdmin(req, env); if (unauthorized) return unauthorized;
  const body = await req.json<any>();
  const servers = body?.servers || [];
  const tx = env.DB.prepare("BEGIN TRANSACTION");
  await tx.run();
  try {
    for (const s of servers) {
      const tags = (s.tags || []).join(",");
      const has_sse = s.endpoints?.sse ? 1 : 0;
      const has_ws  = s.endpoints?.ws ? 1 : 0;
      const has_http= s.endpoints?.http ? 1 : 0;
      const quality = Number(s.metadata?.quality || 0);
      await env.DB.prepare(`
        INSERT INTO servers (id, name, category, tags, repo_url, home_url, docker_image,
                              has_sse, has_ws, has_http, description, license, maintainers, quality, version, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,
          category=excluded.category,
          tags=excluded.tags,
          repo_url=excluded.repo_url,
          home_url=excluded.home_url,
          docker_image=excluded.docker_image,
          has_sse=excluded.has_sse,
          has_ws=excluded.has_ws,
          has_http=excluded.has_http,
          description=excluded.description,
          license=excluded.license,
          maintainers=excluded.maintainers,
          quality=excluded.quality,
          version=excluded.version,
          updated_at=datetime('now');
      `).bind(
        s.id, s.name, s.category || null, tags, s.repo_url || null, s.home_url || null, s.docker_image || null,
        has_sse, has_ws, has_http, s.metadata?.description || null, s.metadata?.license || null,
        (s.metadata?.maintainers || []).join(","), quality, s.metadata?.version || null
      ).run();
    }
    await env.DB.prepare("COMMIT").run();
    return json({ ingested: servers.length });
  } catch (e) {
    await env.DB.prepare("ROLLBACK").run();
    return json({ error: String(e) }, { status: 500 });
  }
}

async function doHealthSweep(env: Env) {
  const list = await env.DB.prepare("SELECT id FROM servers").all();
  if (!list.results) return;
  for (const row of list.results as any[]) {
    let eps: {sse?: string|null, ws?: string|null, http?: string|null} = {};
    try {
      const obj = await env.R2.get(`${env.REGISTRY_PREFIX}servers/${row.id}.json`);
      if (obj) {
        const parsed = JSON.parse(await obj.text());
        eps = parsed.endpoints || {};
      }
    } catch {}

    const targets = [eps.sse, eps.http, eps.ws].filter(Boolean) as string[];
    let score = 0; let hits = 0; let fastest = Infinity;
    for (const url of targets) {
      try {
        const ctl = new AbortController();
        const t = setTimeout(() => ctl.abort(), 5000);
        const t0 = Date.now();
        const res = await fetch(url as string, { method: "HEAD", signal: ctl.signal });
        clearTimeout(t);
        const dt = Date.now() - t0;
        if (res.ok) { hits++; fastest = Math.min(fastest, dt); }
        // record sample (cap by sampling every run; for prod you might rate-limit)
        await env.DB.prepare("INSERT OR REPLACE INTO latency(server_id, ts, ms, ok) VALUES(?, datetime('now'), ?, ?)")
          .bind(row.id, Math.min(60000, Math.max(0, dt)), res.ok ? 1 : 0).run();
      } catch {
        await env.DB.prepare("INSERT OR REPLACE INTO latency(server_id, ts, ms, ok) VALUES(?, datetime('now'), ?, 0)")
          .bind(row.id, 60000).run();
      }
    }
    if (hits > 0) {
      score = 60 + Math.min(20, targets.length * 10) + (fastest === Infinity ? 0 : Math.max(0, 20 - Math.floor(fastest/100)));
    } else {
      score = 0;
    }
    await env.DB.prepare("UPDATE servers SET quality=?, updated_at=datetime('now') WHERE id=?").bind(score, row.id).run();
  }
}

async function handleLatency(req: Request, env: Env) {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  if (!id) return json({ error: "missing id" }, { status: 400 });
  const out = await env.DB.prepare("SELECT ts, ms, ok FROM latency WHERE server_id=? ORDER BY ts DESC LIMIT 100")
    .bind(id).all();
  return json({ id, points: (out.results || []).reverse() });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/registry/")) return handleRegistry(req, env);
    if (url.pathname === "/api/servers") return handleListServers(req, env);
    if (url.pathname === "/api/verify") return handleApiVerify(req, env);
    if (url.pathname === "/api/latency") return handleLatency(req, env);
    if (url.pathname === "/admin/ingest" && req.method === "POST") return handleAdminIngest(req, env);
    if (url.pathname === "/admin/cron"   && req.method === "POST") { const una = requireAdmin(req, env); if (una) return una; await doHealthSweep(env); return json({ok:true}); }
    return json({ ok: true, routes: ["/registry/*", "/api/servers", "/api/verify", "/api/latency", "/admin/ingest", "/admin/cron"] });
  },
  async scheduled(_event: ScheduledEvent, env: Env): Promise<void> {
    await doHealthSweep(env);
  }
} satisfies ExportedHandler<Env>;


# =============================================
# File: pages/index.html (chart-enhanced)
# =============================================
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CloudCurio MCP Registry</title>
  <style>
    body { font-family: ui-sans-serif, system-ui; background:#0b0b0b; color:#d7ffcf; }
    input, select { background:#111; color:#d7ffcf; border:1px solid #1f1f1f; padding:.5rem; border-radius:.5rem; }
    table { width:100%; border-collapse: collapse; margin-top:1rem; }
    th, td { border-bottom:1px solid #222; padding:.5rem; text-align:left; }
    .muted{ color:#7ae0a6; }
    #chart { display:none; margin-top: 1rem; background:#111; border:1px solid #1f1f1f; border-radius:.5rem; }
  </style>
</head>
<body>
  <h1>CloudCurio MCP Registry</h1>
  <div>
    <input id="q" placeholder="search..."/> 
    <select id="category"><option value="">(all categories)</option></select>
    <select id="minQ">
      <option value="0">min quality 0</option>
      <option value="40">40</option>
      <option value="60">60</option>
      <option value="80">80</option>
    </select>
    <button id="go">Search</button>
  </div>
  <canvas id="chart" width="900" height="220"></canvas>
  <table id="tbl"><thead><tr><th>ID</th><th>Name</th><th>Category</th><th>Quality</th><th>Links</th></tr></thead><tbody></tbody></table>

  <script>
    async function fetchServers(params={}){
      const url = new URL('/api/servers', location.origin);
      for (const [k,v] of Object.entries(params)) if (v) url.searchParams.set(k, v);
      const r = await fetch(url); return await r.json();
    }
    async function fetchLatency(id){
      const url = new URL('/api/latency', location.origin); url.searchParams.set('id', id);
      const r = await fetch(url); return await r.json();
    }
    function drawChart(points){
      const c = document.getElementById('chart');
      const ctx = c.getContext('2d');
      ctx.clearRect(0,0,c.width,c.height);
      if (!points || points.length===0){ c.style.display='none'; return; }
      c.style.display='block';
      const pad=20, w=c.width-2*pad, h=c.height-2*pad; ctx.strokeStyle='#7ae0a6'; ctx.lineWidth=2;
      const ms = points.map(p=>p.ms);
      const min=Math.min(...ms), max=Math.max(...ms);
      const norm = v=> h - (h*((v-min)/(Math.max(1,max-min))));
      ctx.beginPath();
      points.forEach((p, i)=>{
        const x = pad + (w*(i/(points.length-1||1)));
        const y = pad + norm(p.ms);
        if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
      });
      ctx.stroke();
      ctx.fillStyle='#7ae0a6'; ctx.fillText(`${points.length} samples  (lower is faster)`, pad, 14);
    }
    async function render(){
      const q = document.getElementById('q').value;
      const category = (document.getElementById('category')).value;
      const minQuality = (document.getElementById('minQ')).value;
      const data = await fetchServers({ q, category, minQuality });
      const tbody = document.querySelector('#tbl tbody');
      tbody.innerHTML = '';
      for (const s of data.results){
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><a href="#" data-id="${s.id}"><code>${s.id}</code></a></td><td>${s.name||''}</td><td>${s.category||''}</td><td>${s.quality||0}</td>
                        <td class="muted"><a href="${s.repo_url||'#'}" target="_blank">repo</a> · <a href="${s.home_url||'#'}" target="_blank">home</a></td>`;
        tbody.appendChild(tr);
      }
      tbody.querySelectorAll('a[data-id]').forEach(a=>{
        a.addEventListener('click', async (e)=>{
          e.preventDefault();
          const id = e.target.closest('a').dataset.id;
          const res = await fetchLatency(id);
          drawChart(res.points||[]);
        });
      })
    }
    document.getElementById('go').onclick = render;
    (async()=>{ await render(); })();
  </script>
</body>
</html>


# =============================================
# File: .github/workflows/registry-ci.yml (updated verify)
# =============================================
name: Registry CI
on:
  push:
    branches: [ main ]
    paths:
      - 'mcp_registry.yaml'
      - 'registry/**'
      - 'src/**'
      - '.github/workflows/registry-ci.yml'
  schedule:
    - cron: '17 3 * * *'

jobs:
  validate-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install deps
        run: |
          python -m pip install --upgrade pip pyyaml

      - name: Validate YAML schema (light)
        run: |
          python - <<'PY'
          import yaml, sys
          doc = yaml.safe_load(open('mcp_registry.yaml'))
          assert isinstance(doc, dict) and 'servers' in doc and isinstance(doc['servers'], list)
          for s in doc['servers']:
              assert 'id' in s and 'name' in s and 'endpoints' in s and 'metadata' in s
          print('OK: registry basic validation passed.')
          PY

      - name: Create manifest.json with SHA256
        run: |
          mkdir -p registry
          python - <<'PY'
          import yaml, json, hashlib
          data = yaml.safe_load(open('mcp_registry.yaml'))
          blob = json.dumps(data, sort_keys=True).encode()
          sha = hashlib.sha256(blob).hexdigest()
          open('registry/manifest.json','w').write(json.dumps({'files':[{'path':'mcp_registry.yaml','sha256':sha}]}, indent=2))
          print('Wrote registry/manifest.json')
          PY

      - name: Upload to R2 (wrangler)
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          command: r2 object put cloudcurio-mcp/registry/mcp_registry.yaml --file=./mcp_registry.yaml

      - name: Upload manifest.json
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          command: r2 object put cloudcurio-mcp/registry/manifest.json --file=./registry/manifest.json

      - name: Run DB migrations (D1)
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          command: d1 execute mcp-registry --file=src/schema.sql

      - name: Ingest into D1 via Worker
        env:
          ADMIN_API_TOKEN: ${{ secrets.ADMIN_API_TOKEN }}
          WORKER_ADMIN_INGEST_URL: ${{ secrets.WORKER_ADMIN_INGEST_URL }}
        run: |
          echo '{"servers": '$(python -c "import yaml, json; print(json.dumps(yaml.safe_load(open('mcp_registry.yaml'))['servers']))")'}' > payload.json
          curl -fsSL -X POST "$WORKER_ADMIN_INGEST_URL" \
               -H "authorization: Bearer $ADMIN_API_TOKEN" \
               -H 'content-type: application/json' \
               --data-binary @payload.json

      - name: Install Cosign (Sigstore)
        uses: sigstore/cosign-installer@v3

      - name: Sign manifest with Sigstore keyless
        env:
          COSIGN_EXPERIMENTAL: "1"
        run: |
          cosign sign-blob --yes --output-signature registry/manifest.sig registry/manifest.json

      - name: Upload signature to R2
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          command: r2 object put cloudcurio-mcp/registry/manifest.sig --file=./registry/manifest.sig

      - name: Verify presence via Worker
        env:
          WORKER_VERIFY_URL: ${{ secrets.WORKER_VERIFY_URL }}
        run: |
          curl -fsSL "$WORKER_VERIFY_URL" | jq .

  nightly-health:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Worker cron via admin endpoint
        env:
          ADMIN_API_TOKEN: ${{ secrets.ADMIN_API_TOKEN }}
          WORKER_ADMIN_CRON_URL: ${{ secrets.WORKER_ADMIN_CRON_URL }}
        run: |
          curl -fsSL -X POST "$WORKER_ADMIN_CRON_URL" -H "authorization: Bearer $ADMIN_API_TOKEN" || true


# =============================================
# File: Dockerfile.registry-tools
# =============================================
# Purpose: Portable toolchain image for running registry ops locally or in CI
# Includes: Python + PyYAML, Node + Wrangler, Cosign, jq, curl, git
# Usage:
#   REGISTRY_IMAGE=ghcr.io/cbwinslow/mcp-registry-tools:latest \
#   docker build -t $REGISTRY_IMAGE -f Dockerfile.registry-tools .
#   docker run --rm -it -v "$(pwd)":/work -w /work $REGISTRY_IMAGE bash
FROM debian:stable-slim
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    ca-certificates curl jq git python3 python3-pip nodejs npm \
    && rm -rf /var/lib/apt/lists/*
RUN npm -g install wrangler@3
RUN pip3 install --no-cache-dir pyyaml
# Cosign
RUN curl -fsSL https://artifacts.sigstore.dev/cosign/cosign-linux-amd64 -o /usr/local/bin/cosign \
    && chmod +x /usr/local/bin/cosign
WORKDIR /work
CMD ["bash"]


# =============================================
# Makefile — added Docker + GHCR targets
# =============================================
# (append to existing Makefile; duplicate targets are fine in GNU make if identical)
REGISTRY_IMAGE ?= ghcr.io/cbwinslow/mcp-registry-tools:latest

.PHONY: docker-build docker-push ghcr-login verify-signature-local

docker-build:
	docker build -t $(REGISTRY_IMAGE) -f Dockerfile.registry-tools .

docker-push: docker-build
	docker push $(REGISTRY_IMAGE)

# Logs in to GHCR using a PAT from env GITHUB_TOKEN (or docker’s native prompt)
# For non-interactive secret retrieval, see scripts/ghcr_login_with_bw.sh
ghcr-login:
	@if [ -z "$$GITHUB_TOKEN" ]; then \
	  echo "Set GITHUB_TOKEN (with package:write) or use scripts/ghcr_login_with_bw.sh"; exit 1; fi
	echo "$$GITHUB_TOKEN" | docker login ghcr.io -u cbwinslow --password-stdin

# Quick local signature check (SHA only) against the manifest
verify-signature-local:
	@python - <<'PY'
import json,hashlib
b=open('registry/manifest.json','rb').read()
print('SHA256:', hashlib.sha256(b).hexdigest())
print('Signature present:', __import__('os').path.exists('registry/manifest.sig'))
PY


# =============================================
# File: scripts/ghcr_login_with_bw.sh
# =============================================
#!/usr/bin/env bash
# ------------------------------------------------------------
# Script: scripts/ghcr_login_with_bw.sh
# Author: CBW + GPT-5 Thinking
# Date: 2025-11-04
# Summary: Log in to GHCR using a PAT stored in Bitwarden.
# Inputs (env):
#   BW_SESSION           - from `bw unlock --raw`
#   BW_ITEM              - Bitwarden item name or id that holds the GHCR PAT
#   BW_FIELD             - field name (default: password)
#   GHCR_USER            - default: cbwinslow
# ------------------------------------------------------------
set -euo pipefail
: "${BW_FIELD:=password}"; : "${GHCR_USER:=cbwinslow}"

if ! command -v bw >/dev/null 2>&1; then echo "[ERR] missing bw CLI" >&2; exit 1; fi
if ! command -v docker >/dev/null 2>&1; then echo "[ERR] missing docker" >&2; exit 1; fi

[[ -n "${BW_SESSION:-}" ]] || { echo "[ERR] BW_SESSION required" >&2; exit 1; }
[[ -n "${BW_ITEM:-}" ]]    || { echo "[ERR] BW_ITEM required (item name or id)" >&2; exit 1; }

json=$(bw get item --session "$BW_SESSION" "$BW_ITEM" 2>/dev/null || true)
if [[ -z "$json" ]]; then
  id=$(bw list items --search "$BW_ITEM" --session "$BW_SESSION" | jq -r '.[0].id // empty')
  [[ -n "$id" ]] || { echo "[ERR] No Bitwarden item $BW_ITEM" >&2; exit 1; }
  json=$(bw get item --session "$BW_SESSION" "$id")
fi
pat=$(jq -r --arg f "$BW_FIELD" 'if $f=="password" then .login.password else (.fields//[])|map(select(.name==$f))|.[0].value end' <<<"$json")
[[ -n "$pat" ]] || { echo "[ERR] field $BW_FIELD empty" >&2; exit 1; }

echo "$pat" | docker login ghcr.io -u "$GHCR_USER" --password-stdin

echo "[OK] Logged in to ghcr.io as $GHCR_USER"


# =============================================
# File: .gitignore (recommended)
# =============================================
# Local environment and generated artifacts
.env
.env.*
registry/manifest.sig
registry/manifest.json
.ingest.payload.json
__pycache__/
*.log


# =============================================
# File: examples/.env.in  (template for tools/env_from_bw.py)
# =============================================
# Values equal to "populate from bw" will be auto-filled from mapping or heuristic
CF_ACCOUNT_ID="populate from bw"
CF_API_TOKEN="bw:item=Cloudflare API;field=token"
ADMIN_API_TOKEN="populate from bw"
GITHUB_TOKEN="bw:item=GitHub;field=token"


# =============================================
# File: examples/.env.bwmap.yaml
# =============================================
CF_ACCOUNT_ID:
  item: "Cloudflare Account"
  field: "account_id"
ADMIN_API_TOKEN:
  item: "MCP Registry Admin"
  field: "token"


# =============================================
# Notes — Operational Hardening & Next Steps
# =============================================
# 1) Dockerized ops: Use Dockerfile.registry-tools to pin a working toolchain for CI or local use.
# 2) Supply chain: Consider generating SLSA provenance for manifest.json and storing it next to the sig.
# 3) RBAC: Move ADMIN_API_TOKEN to Cloudflare Dashboard secrets; rotate quarterly.
# 4) R2 object ACLs: keep manifest + sig world-readable; keep per-server dumps in /registry/servers/ read-only.
# 5) Observability: add traceparent passthrough and emit basic logs on Worker for /admin routes.
# 6) Rate limits: shield /admin/* with WAF rule matching a service token or IP allowlist in addition to bearer.
# 7) Automatic server docs: extend CI to emit a /registry/servers/<id>.json for each server with endpoints and metadata.
