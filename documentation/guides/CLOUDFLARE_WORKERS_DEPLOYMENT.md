# Cloudflare Workers Ingestion System Deployment Guide

This document provides comprehensive instructions for deploying the multi-source data ingestion system powered by Cloudflare Workers. It covers Cloudflare Tunnel setup for PostgreSQL connectivity and the deployment of all individual Workers.

## 1. Prerequisites

-   **Cloudflare Account**: With a domain managed by Cloudflare.
-   **`wrangler` CLI**: Installed and authenticated (`npm i -g wrangler` then `wrangler login`).
-   **Node.js**: (LTS version) and npm installed.
-   **PostgreSQL Database**: Running and accessible (as configured in previous debugging steps).
-   **`cloudflared` CLI**: Installed on a machine with network access to your PostgreSQL database to run the Cloudflare Tunnel.

## 2. Cloudflare Tunnel Setup (for PostgreSQL Connectivity)

This establishes a secure, free-tier connection from Cloudflare Workers to your self-hosted PostgreSQL database.

1.  **Install `cloudflared` CLI**:
    On the machine that will host the tunnel, install `cloudflared`. Refer to [https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/).

2.  **Authenticate `cloudflared`**:
    ```bash
    cloudflared login
    ```
    This opens a browser for Cloudflare account login and domain selection.

3.  **Create a Tunnel**:
    ```bash
    cloudflared tunnel create opendiscourse-postgres
    ```
    **Note down the `Tunnel ID`** (e.g., `a5c09e3e-4d6d-4f7f-8e1d-c3b2f5a6b7d8`).

4.  **Create `config.yml`**:
    Create a `config.yml` file (e.g., in `~/.cloudflared/` or project root) and replace placeholders:
    ```yaml
    # config.yml
    tunnel: <YOUR_TUNNEL_ID>
    credentials-file: ~/.cloudflared/<YOUR_TUNNEL_ID>.json # Adjust path if different
    
    ingress:
      - hostname: postgres.<YOUR_DOMAIN>.com # e.g., postgres.example.com
        service: tcp://<YOUR_LOCAL_DB_IP>:5432 # IP of your PostgreSQL instance (e.g., 127.0.0.1 or internal LAN IP)
      - service: http_status:404 # Fallback
    ```

5.  **Create DNS Record**:
    ```bash
    cloudflared tunnel route dns opendiscourse-postgres postgres.<YOUR_DOMAIN>.com
    ```
    Or manually in Cloudflare Dashboard: `CNAME` record, `Name: postgres`, `Target: <YOUR_TUNNEL_ID>.cfargotunnel.com`.

6.  **Run the Tunnel**:
    ```bash
    cloudflared tunnel run opendiscourse-postgres
    ```
    For production, configure `cloudflared` as a system service.

7.  **Configure PostgreSQL Database**:
    *   **`postgresql.conf`**: Set `listen_addresses = '<YOUR_LOCAL_DB_IP>'` (e.g., `'0.0.0.0'`).
    *   **`pg_hba.conf`**: Add `host all all <IP_OF_CLOUDFLARED_MACHINE>/32 scram-sha-256`.
    *   **Restart PostgreSQL**: `sudo systemctl restart postgresql@16-main.service` (or your relevant service name).

## 3. Workers Deployment

Each Worker project must be deployed separately. Ensure you navigate into each project's directory (`cloudflare-workers`, `cloudflare-workers-fetcher-congress`, etc.) for deployment.

### 3.1 Orchestrator Worker (`cloudflare-workers`)

1.  **Project Setup**: If not already done, create the project:
    ```bash
    npm create cloudflare@latest cloudflare-workers -- --ts
    cd cloudflare-workers
    npm install openai postgres
    ```

2.  **`wrangler.toml`**: Ensure the following bindings are correctly configured:
    ```toml
    # Durable Object binding
    [[durable_objects.bindings]]
    name = "PROGRESS_TRACKER"
    class_name = "ProgressTracker"
    migrations = [ { tag = "v1", new_classes = ["ProgressTracker"] } ]

    # Fetcher Worker Bindings (replace service names with your deployed worker names)
    [[services]]
    binding = "CONGRESS_FETCHER"
    service = "cloudflare-workers-fetcher-congress"

    [[services]]
    binding = "GOVINFO_FETCHER"
    service = "cloudflare-workers-fetcher-govinfo"

    [[services]]
    binding = "OPENSTATES_FETCHER"
    service = "cloudflare-workers-fetcher-openstates"

    # Transformer Worker Bindings (replace service names with your deployed worker names)
    [[services]]
    binding = "CONGRESS_TRANSFORMER"
    service = "cloudflare-workers-transformer-congress"

    [[services]]
    binding = "GOVINFO_TRANSFORMER"
    service = "cloudflare-workers-transformer-govinfo"

    [[services]]
    binding = "OPENSTATES_TRANSFORMER"
    service = "cloudflare-workers-transformer-openstates"
    ```

3.  **Durable Object Code (`src/durable-objects/progress-tracker.ts`)**:
    Create this file:
    ```typescript
    // cloudflare-workers/src/durable-objects/progress-tracker.ts
    // ... (code provided in previous conversation turn)
    ```

4.  **AI Agents Code (`src/ai-agents/openrouter-client.ts` and `src/ai-agents/data-quality-agent.ts`, `src/ai-agents/optimization-agent.ts`, `src/ai-agents/conflict-resolution-agent.ts`)**:
    Create these files:
    ```typescript
    // cloudflare-workers/src/ai-agents/openrouter-client.ts
    // ... (code provided in previous conversation turn)
    // cloudflare-workers/src/ai-agents/data-quality-agent.ts
    // ... (code provided in previous conversation turn)
    // cloudflare-workers/src/ai-agents/optimization-agent.ts
    // ... (code provided in previous conversation turn)
    // cloudflare-workers/src/ai-agents/conflict-resolution-agent.ts
    // ... (code provided in previous conversation turn)
    ```

5.  **Main Worker Code (`src/index.ts`)**:
    Replace with the Orchestrator code:
    ```typescript
    // cloudflare-workers/src/index.ts
    // ... (full Orchestrator code provided in previous conversation turn)
    ```

6.  **Worker Secrets**: Set all necessary environment variables as Worker secrets:
    ```bash
    npx wrangler secret put DB_HOST
    npx wrangler secret put DB_USER
    npx wrangler secret put DB_PASSWORD
    npx wrangler secret put DB_NAME
    npx wrangler secret put CONGRESS_API_KEY
    npx wrangler secret put GOVINFO_API_KEY
    npx wrangler secret put OPENSTATES_API_KEY
    npx wrangler secret put OPENROUTER_API_KEY
    ```

7.  **Deploy Orchestrator**:
    ```bash
    npx wrangler deploy
    ```
    **Note down the deployed URL of your Orchestrator Worker.**

### 3.2 Fetcher Workers (e.g., `cloudflare-workers-fetcher-congress`)

1.  **Project Setup**: For each source (Congress, GovInfo, OpenStates), create a separate project:
    ```bash
    npm create cloudflare@latest cloudflare-workers-fetcher-<source> -- --ts
    cd cloudflare-workers-fetcher-<source>
    # (Example for Congress.gov)
    ```

2.  **`wrangler.toml`**: Ensure `name = "cloudflare-workers-fetcher-<source>"` (e.g., `"cloudflare-workers-fetcher-congress"`) matches the `service` binding in the Orchestrator's `wrangler.toml`.

3.  **Main Worker Code (`src/index.ts`)**:
    Update with the Fetcher logic (including retry and rate limiting):
    ```typescript
    // cloudflare-workers-fetcher-congress/src/index.ts
    // ... (code provided in previous conversation turn)
    ```

4.  **Worker Secrets**: Set the relevant API key:
    ```bash
    npx wrangler secret put CONGRESS_API_KEY
    # Repeat for GOVINFO_API_KEY and OPENSTATES_API_KEY in their respective fetcher projects
    ```

5.  **Deploy Fetcher**:
    ```bash
    npx wrangler deploy
    ```

### 3.3 Transformer Workers (e.g., `cloudflare-workers-transformer-congress`)

1.  **Project Setup**: For each source (Congress, GovInfo, OpenStates), create a separate project:
    ```bash
    npm create cloudflare@latest cloudflare-workers-transformer-<source> -- --ts
    cd cloudflare-workers-transformer-<source>
    # (Example for Congress.gov)
    ```

2.  **`wrangler.toml`**: Ensure `name = "cloudflare-workers-transformer-<source>"` matches the `service` binding in the Orchestrator's `wrangler.toml`.

3.  **Main Worker Code (`src/index.ts`)**:
    Update with the Transformer logic:
    ```typescript
    // cloudflare-workers-transformer-congress/src/index.ts
    // ... (code provided in previous conversation turn)
    ```

4.  **Deploy Transformer**:
    ```bash
    npx wrangler deploy
    ```

## 4. Testing the Ingestion Pipeline

Once all Workers are deployed, you can test the full pipeline using your Orchestrator Worker's URL:

1.  **Initialize Job State**:
    ```
    <YOUR_ORCHESTRATOR_URL>/start-ingestion
    ```
2.  **Run Ingestion for a Source**:
    *   Congress.gov: `<YOUR_ORCHESTRATOR_URL>/run-congress-ingestion?apiEndpoint=member`
    *   GovInfo: `<YOUR_ORCHESTRATOR_URL>/run-govinfo-ingestion?apiEndpoint=collections`
    *   OpenStates: `<YOUR_ORCHESTRATOR_URL>/run-openstates-ingestion?apiEndpoint=legislators`
3.  **Check Status**:
    ```
    <YOUR_ORCHESTRATOR_URL>/get-status
    ```
    Monitor the status changes, including data quality and optimization recommendations in the response (which are currently logged to your Worker's console via `wrangler tail`).
4.  **Control Ingestion**:
    *   Pause: `<YOUR_ORCHESTRATOR_URL>/pause-ingestion`
    *   Resume: `<YOUR_ORCHESTRATOR_URL>/resume-ingestion`
    *   Reset: `<YOUR_ORCHESTRATOR_URL>/reset-job`
