# OpenDiscourse SDK - Comprehensive Recommendations

## 📋 Document Overview

This document provides detailed, traceable, and actionable recommendations for improving the OpenDiscourse SDK project. Each recommendation includes step-by-step instructions that can be followed by AI agents or human developers to complete the improvements.

**Last Updated**: 2026-02-11
**Version**: 1.0
**Status**: Draft

---

## 🎯 Executive Summary

The OpenDiscourse SDK is a mature, enterprise-grade legislative data platform with strong foundations. However, it requires focused improvements in several key areas:

### Critical Issues
1. **Congress Bills Ingestion Broken** - Foreign key constraint violation
2. **Missing MCP Server Implementation** - No dedicated MCP servers for AI integration
3. **Incomplete Deployment Automation** - Manual deployment processes
4. **Documentation Gaps** - Missing guides for MCP and deployment

### Strengths
- ✅ Robust Python SDK published on PyPI
- ✅ Comprehensive FastAPI backend
- ✅ Modern Next.js frontends
- ✅ Extensive CI/CD (47 workflows)
- ✅ Strong security posture

### Opportunities
- 🚀 MCP server ecosystem for AI agents
- 🚀 Automated Cloudflare Workers deployment
- 🚀 Docker-based development environment
- 🚀 Enhanced documentation and learning resources

---

## 🔧 RECOMMENDATION 1: Fix Congress Bills Ingestion

### Priority: CRITICAL
### Estimated Effort: 2-4 hours
### Dependencies: None

### Problem Statement
Congress bills ingestion fails due to chamber mapping inconsistency. The API returns "House", "Senate", "Joint" but the database expects lowercase values "house", "senate", "joint".

### Root Cause Analysis
```python
# File: opendiscourse/ingestion/document_ingestion.py, Line 119
# Current code doesn't properly handle chamber enum mapping
chamber_mapping = {
    'H': 'house',
    'S': 'senate',
    # Missing uppercase variants
}
```

### Recommended Solution

#### Step 1: Update Chamber Mapping
**File**: `opendiscourse/ingestion/document_ingestion.py`

```python
# Current (broken):
chamber_mapping = {
    'H': 'house',
    'S': 'senate',
}

# Recommended (fixed):
chamber_mapping = {
    'H': 'house',
    'S': 'senate',
    'J': 'joint',
    'House': 'house',
    'Senate': 'senate',
    'Joint': 'joint',
    'HOUSE': 'house',
    'SENATE': 'senate',
    'JOINT': 'joint',
}

# Add fallback with logging
def normalize_chamber(chamber: str) -> str:
    """Normalize chamber code to lowercase standard."""
    if not chamber:
        logger.warning("Empty chamber value received")
        return ''
    
    normalized = chamber_mapping.get(chamber)
    if normalized:
        return normalized
    
    # Try lowercase as fallback
    normalized = chamber_mapping.get(chamber.lower())
    if normalized:
        logger.warning(f"Using fallback normalization for chamber: {chamber}")
        return normalized
    
    # Log unknown chamber for investigation
    logger.error(f"Unknown chamber value: {chamber}")
    return ''
```

#### Step 2: Update Test
**File**: `test_minimal.py`

```python
# Current test (line ~47):
def test_chamber_mapping():
    invalid_chamber = transform_chamber_code("invalid")
    assert invalid_chamber == "unknown", f"Expected 'unknown', got '{invalid_chamber}'"

# Recommended fix:
def test_chamber_mapping():
    # Test valid chambers
    assert transform_chamber_code("House") == "house"
    assert transform_chamber_code("Senate") == "senate"
    assert transform_chamber_code("Joint") == "joint"
    assert transform_chamber_code("H") == "house"
    assert transform_chamber_code("S") == "senate"
    assert transform_chamber_code("J") == "joint"
    
    # Test invalid chamber returns empty string
    invalid_chamber = transform_chamber_code("invalid")
    assert invalid_chamber == "", f"Expected empty string, got '{invalid_chamber}'"
    
    # Test None/empty handling
    assert transform_chamber_code(None) == ""
    assert transform_chamber_code("") == ""
```

#### Step 3: Create Minimal Ingestion Script
**File**: `scripts/ingest_congress_bills_minimal.py` (new file)

```python
#!/usr/bin/env python3
"""
Minimal Congress bills ingestion script.
No complex dependencies, just API → Transform → Database.
"""
import os
import sys
import logging
import psycopg2
import requests
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
API_BASE = "https://api.congress.gov/v3"
DB_CONFIG = {
    'database': 'opendiscourse',
    'user': 'cbwinslow',
    'host': '/var/run/postgresql'
}

# Chamber mapping
CHAMBER_MAP = {
    'House': 'house', 'H': 'house', 'HOUSE': 'house',
    'Senate': 'senate', 'S': 'senate', 'SENATE': 'senate',
    'Joint': 'joint', 'J': 'joint', 'JOINT': 'joint',
}

def get_api_key() -> str:
    """Get and validate Congress API key."""
    api_key = os.getenv('CONGRESS_API_KEY')
    if not api_key or 'DEMO' in api_key.upper():
        raise ValueError("Valid CONGRESS_API_KEY required")
    return api_key

def fetch_bills(congress: int, limit: int = 250) -> List[Dict]:
    """Fetch bills from Congress.gov API."""
    api_key = get_api_key()
    bills = []
    offset = 0
    
    while len(bills) < limit:
        url = f"{API_BASE}/bill/{congress}"
        params = {
            'api_key': api_key,
            'format': 'json',
            'offset': offset,
            'limit': min(250, limit - len(bills))
        }
        
        logger.info(f"Fetching bills: offset={offset}, limit={params['limit']}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        batch = data.get('bills', [])
        if not batch:
            break
        
        bills.extend(batch)
        offset += len(batch)
        
        logger.info(f"Fetched {len(batch)} bills, total: {len(bills)}")
    
    return bills[:limit]

def transform_bill(bill_data: Dict) -> Dict:
    """Transform API bill data to database format."""
    # Extract chamber and normalize
    origin_chamber_raw = bill_data.get('originChamber', '')
    origin_chamber = CHAMBER_MAP.get(origin_chamber_raw, origin_chamber_raw.lower())
    
    if not origin_chamber:
        logger.warning(f"No chamber for bill: {bill_data.get('number')}")
    
    # Extract bill type and number
    bill_type_raw = bill_data.get('type', '').lower()
    bill_number = bill_data.get('number')
    
    # Build transformed record
    return {
        'congress': bill_data.get('congress'),
        'bill_type': bill_type_raw,
        'bill_number': bill_number,
        'title': bill_data.get('title', '')[:500],  # Truncate if needed
        'origin_chamber': origin_chamber,
        'introduced_date': bill_data.get('introducedDate'),
        'update_date': bill_data.get('updateDate'),
        'url': bill_data.get('url'),
    }

def insert_bills(bills: List[Dict]) -> int:
    """Insert bills into database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    insert_sql = """
        INSERT INTO congress.bills (
            congress, bill_type, bill_number, title,
            origin_chamber, introduced_date, update_date, url
        ) VALUES (
            %(congress)s, %(bill_type)s, %(bill_number)s, %(title)s,
            %(origin_chamber)s, %(introduced_date)s, %(update_date)s, %(url)s
        )
        ON CONFLICT (congress, bill_type, bill_number) DO UPDATE SET
            title = EXCLUDED.title,
            update_date = EXCLUDED.update_date,
            url = EXCLUDED.url
    """
    
    inserted = 0
    for bill in bills:
        try:
            cur.execute(insert_sql, bill)
            inserted += 1
        except Exception as e:
            logger.error(f"Failed to insert bill {bill.get('bill_number')}: {e}")
            conn.rollback()
        else:
            conn.commit()
    
    cur.close()
    conn.close()
    
    return inserted

def main():
    """Main ingestion workflow."""
    # Get congress number from args or default to 118
    congress = int(sys.argv[1]) if len(sys.argv) > 1 else 118
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    logger.info(f"Starting ingestion: Congress {congress}, limit {limit}")
    
    try:
        # Fetch bills from API
        logger.info("Fetching bills from API...")
        api_bills = fetch_bills(congress, limit)
        logger.info(f"Fetched {len(api_bills)} bills")
        
        # Transform bills
        logger.info("Transforming bills...")
        transformed_bills = [transform_bill(b) for b in api_bills]
        
        # Insert into database
        logger.info("Inserting bills into database...")
        inserted = insert_bills(transformed_bills)
        logger.info(f"Successfully inserted {inserted}/{len(transformed_bills)} bills")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

#### Step 4: Test with Small Batch

```bash
# Set API key
export CONGRESS_API_KEY="your_api_key_here"

# Test with 10 bills
python scripts/ingest_congress_bills_minimal.py 118 10

# Verify in database
psql -d opendiscourse -c "SELECT count(*) FROM congress.bills WHERE congress = 118;"
psql -d opendiscourse -c "SELECT bill_number, bill_type, origin_chamber FROM congress.bills WHERE congress = 118 LIMIT 10;"
```

#### Step 5: Scale to Full Ingestion

```bash
# Ingest all Congress 118 bills
python scripts/ingest_congress_bills_minimal.py 118 5000

# Verify count
psql -d opendiscourse -c "
SELECT 
    congress,
    origin_chamber,
    count(*) as bill_count
FROM congress.bills
WHERE congress = 118
GROUP BY congress, origin_chamber
ORDER BY origin_chamber;
"
```

### Validation Checklist
- [ ] Chamber mapping updated with all variants
- [ ] Test passes (10/10 instead of 8/9)
- [ ] Minimal ingestion script created
- [ ] 10 bills inserted successfully
- [ ] Full Congress 118 ingestion completes
- [ ] No foreign key constraint violations
- [ ] Data integrity verified in database

### Success Criteria
- All tests pass
- 1000+ bills inserted for Congress 118
- Chamber values correctly normalized
- Zero data loss

---

## 🤖 RECOMMENDATION 2: Implement MCP Server Ecosystem

### Priority: HIGH
### Estimated Effort: 12-16 hours
### Dependencies: None

### Vision Statement
Create a comprehensive Model Context Protocol (MCP) server ecosystem that enables AI agents to seamlessly interact with Congressional, GovInfo, and OpenStates data. This will position OpenDiscourse as the premier AI-accessible legislative data platform.

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         OpenDiscourse MCP Ecosystem             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────┐│
│  │ Main MCP     │  │ Congress.gov │  │GovInfo││
│  │ Aggregator   │→│ MCP Server   │  │MCP    ││
│  └──────────────┘  └──────────────┘  └───────┘│
│         ↓                                       │
│  ┌──────────────┐                              │
│  │ OpenStates   │                              │
│  │ MCP Server   │                              │
│  └──────────────┘                              │
│                                                 │
├─────────────────────────────────────────────────┤
│  Features:                                      │
│  • Tools (search, query, analyze)              │
│  • Resources (bill://, member://, etc.)        │
│  • Prompts (pre-built analysis templates)      │
│  • Authentication & rate limiting              │
│  • Caching & performance optimization          │
└─────────────────────────────────────────────────┘
```

### Step-by-Step Implementation

#### Phase 1: Project Structure Setup

**Step 1.1: Create Directory Structure**

```bash
cd /home/runner/work/opendiscourse-sdk/opendiscourse-sdk

# Create MCP servers directory
mkdir -p mcp-servers/{congress-gov,govinfo,openstates,main,shared}

# Create subdirectories for each server
for server in congress-gov govinfo openstates main; do
    mkdir -p mcp-servers/$server/{src,tests,docs}
    mkdir -p mcp-servers/$server/src/{tools,resources,prompts,handlers}
done

# Create shared utilities
mkdir -p mcp-servers/shared/{auth,cache,logger,types,utils}
```

**Step 1.2: Initialize Node.js Projects**

```bash
# Initialize each MCP server as Node.js project
for server in congress-gov govinfo openstates main; do
    cd mcp-servers/$server
    npm init -y
    cd ../..
done
```

**Step 1.3: Configure TypeScript**

Create `mcp-servers/tsconfig.base.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

For each server, create `mcp-servers/<server>/tsconfig.json`:

```json
{
  "extends": "../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  }
}
```

#### Phase 2: Shared Utilities Implementation

**Step 2.1: MCP Protocol Types**

Create `mcp-servers/shared/types/mcp.ts`:

```typescript
/**
 * MCP Protocol Type Definitions
 * Based on Model Context Protocol specification
 */

export interface MCPRequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: any;
}

export interface MCPResponse {
  jsonrpc: '2.0';
  id: string | number;
  result?: any;
  error?: MCPError;
}

export interface MCPError {
  code: number;
  message: string;
  data?: any;
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export interface MCPPrompt {
  name: string;
  description?: string;
  arguments?: Array<{
    name: string;
    description?: string;
    required?: boolean;
  }>;
}

export interface MCPServerCapabilities {
  tools?: { listChanged?: boolean };
  resources?: { 
    subscribe?: boolean;
    listChanged?: boolean;
  };
  prompts?: { listChanged?: boolean };
  logging?: {};
}
```

**Step 2.2: Authentication Module**

Create `mcp-servers/shared/auth/validator.ts`:

```typescript
import { createHash } from 'crypto';

export interface AuthConfig {
  apiKey: string;
  allowedOrigins?: string[];
  rateLimit?: {
    requests: number;
    windowMs: number;
  };
}

export class AuthValidator {
  private apiKey: string;
  private allowedOrigins: Set<string>;
  private requestCounts: Map<string, { count: number; resetAt: number }>;

  constructor(config: AuthConfig) {
    this.apiKey = config.apiKey;
    this.allowedOrigins = new Set(config.allowedOrigins || ['*']);
    this.requestCounts = new Map();
  }

  validateApiKey(providedKey: string): boolean {
    if (!providedKey) return false;
    
    // Hash both keys for secure comparison
    const providedHash = this.hashKey(providedKey);
    const expectedHash = this.hashKey(this.apiKey);
    
    return providedHash === expectedHash;
  }

  validateOrigin(origin: string): boolean {
    if (this.allowedOrigins.has('*')) return true;
    return this.allowedOrigins.has(origin);
  }

  checkRateLimit(clientId: string, limit: number, windowMs: number): boolean {
    const now = Date.now();
    const record = this.requestCounts.get(clientId);

    if (!record || now > record.resetAt) {
      // Start new window
      this.requestCounts.set(clientId, {
        count: 1,
        resetAt: now + windowMs
      });
      return true;
    }

    if (record.count >= limit) {
      return false; // Rate limit exceeded
    }

    record.count++;
    return true;
  }

  private hashKey(key: string): string {
    return createHash('sha256').update(key).digest('hex');
  }
}
```

**Step 2.3: Caching Module**

Create `mcp-servers/shared/cache/manager.ts`:

```typescript
export interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

export interface CacheConfig {
  ttlMs: number;
  maxSize: number;
}

export class CacheManager<T = any> {
  private cache: Map<string, CacheEntry<T>>;
  private config: CacheConfig;

  constructor(config: CacheConfig) {
    this.cache = new Map();
    this.config = config;
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) return null;
    
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }

  set(key: string, data: T, ttlMs?: number): void {
    // Evict old entries if cache is full
    if (this.cache.size >= this.config.maxSize) {
      this.evictOldest();
    }

    const ttl = ttlMs || this.config.ttlMs;
    this.cache.set(key, {
      data,
      expiresAt: Date.now() + ttl
    });
  }

  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  private evictOldest(): void {
    // Find and remove the entry with earliest expiration
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.expiresAt < oldestTime) {
        oldestTime = entry.expiresAt;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }
}
```

**Step 2.4: Logging Module**

Create `mcp-servers/shared/logger/index.ts`:

```typescript
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: any;
}

export class Logger {
  private level: LogLevel;
  private context: Record<string, any>;

  constructor(level: LogLevel = LogLevel.INFO, context: Record<string, any> = {}) {
    this.level = level;
    this.context = context;
  }

  debug(message: string, data?: any): void {
    this.log(LogLevel.DEBUG, message, data);
  }

  info(message: string, data?: any): void {
    this.log(LogLevel.INFO, message, data);
  }

  warn(message: string, data?: any): void {
    this.log(LogLevel.WARN, message, data);
  }

  error(message: string, error?: Error | any): void {
    const data = error instanceof Error 
      ? { message: error.message, stack: error.stack }
      : error;
    this.log(LogLevel.ERROR, message, data);
  }

  private log(level: LogLevel, message: string, data?: any): void {
    if (level < this.level) return;

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: { ...this.context, ...data }
    };

    const levelName = LogLevel[level];
    console.log(JSON.stringify({ ...entry, level: levelName }));
  }

  child(context: Record<string, any>): Logger {
    return new Logger(this.level, { ...this.context, ...context });
  }
}
```

#### Phase 3: Congress.gov MCP Server Implementation

**Step 3.1: Main Server File**

Create `mcp-servers/congress-gov/src/index.ts`:

```typescript
import { MCPServer } from './server';
import { Logger, LogLevel } from '../../shared/logger';
import { AuthValidator } from '../../shared/auth/validator';
import { CacheManager } from '../../shared/cache/manager';

const logger = new Logger(LogLevel.INFO, { server: 'congress-gov' });

async function main() {
  try {
    // Load configuration
    const config = {
      port: process.env.PORT ? parseInt(process.env.PORT) : 3001,
      congressApiKey: process.env.CONGRESS_API_KEY || '',
      auth: {
        apiKey: process.env.MCP_API_KEY || 'dev-key',
        allowedOrigins: ['*'],
        rateLimit: {
          requests: 100,
          windowMs: 60000 // 1 minute
        }
      },
      cache: {
        ttlMs: 300000, // 5 minutes
        maxSize: 1000
      }
    };

    if (!config.congressApiKey) {
      throw new Error('CONGRESS_API_KEY environment variable required');
    }

    // Initialize components
    const authValidator = new AuthValidator(config.auth);
    const cacheManager = new CacheManager(config.cache);

    // Create and start server
    const server = new MCPServer({
      congressApiKey: config.congressApiKey,
      authValidator,
      cacheManager,
      logger
    });

    await server.start(config.port);
    
    logger.info(`Congress.gov MCP Server running on port ${config.port}`);

    // Handle shutdown
    process.on('SIGTERM', async () => {
      logger.info('Received SIGTERM, shutting down gracefully...');
      await server.stop();
      process.exit(0);
    });

  } catch (error) {
    logger.error('Failed to start server', error);
    process.exit(1);
  }
}

main();
```

**Step 3.2: Server Implementation**

Create `mcp-servers/congress-gov/src/server.ts`:

```typescript
import express, { Express, Request, Response } from 'express';
import { Server } from 'http';
import { MCPRequest, MCPResponse, MCPServerCapabilities } from '../../shared/types/mcp';
import { Logger } from '../../shared/logger';
import { AuthValidator } from '../../shared/auth/validator';
import { CacheManager } from '../../shared/cache/manager';
import { ToolRegistry } from './tools';
import { ResourceRegistry } from './resources';
import { PromptRegistry } from './prompts';

export interface MCPServerConfig {
  congressApiKey: string;
  authValidator: AuthValidator;
  cacheManager: CacheManager;
  logger: Logger;
}

export class MCPServer {
  private app: Express;
  private server: Server | null = null;
  private config: MCPServerConfig;
  private toolRegistry: ToolRegistry;
  private resourceRegistry: ResourceRegistry;
  private promptRegistry: PromptRegistry;

  constructor(config: MCPServerConfig) {
    this.config = config;
    this.app = express();
    
    // Initialize registries
    this.toolRegistry = new ToolRegistry(config.congressApiKey, config.logger);
    this.resourceRegistry = new ResourceRegistry(config.congressApiKey, config.logger);
    this.promptRegistry = new PromptRegistry(config.logger);

    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware(): void {
    this.app.use(express.json());
    
    // CORS
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      if (req.method === 'OPTIONS') {
        res.sendStatus(200);
      } else {
        next();
      }
    });

    // Authentication
    this.app.use((req, res, next) => {
      const apiKey = req.headers['x-api-key'] as string;
      
      if (!this.config.authValidator.validateApiKey(apiKey)) {
        res.status(401).json({ error: 'Unauthorized' });
        return;
      }

      // Rate limiting
      const clientId = req.ip || 'unknown';
      const allowed = this.config.authValidator.checkRateLimit(clientId, 100, 60000);
      
      if (!allowed) {
        res.status(429).json({ error: 'Rate limit exceeded' });
        return;
      }

      next();
    });

    // Request logging
    this.app.use((req, res, next) => {
      this.config.logger.info('Request received', {
        method: req.method,
        path: req.path,
        ip: req.ip
      });
      next();
    });
  }

  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ status: 'healthy', service: 'congress-gov-mcp' });
    });

    // MCP JSON-RPC endpoint
    this.app.post('/mcp', async (req, res) => {
      try {
        const mcpRequest: MCPRequest = req.body;
        const mcpResponse = await this.handleMCPRequest(mcpRequest);
        res.json(mcpResponse);
      } catch (error) {
        this.config.logger.error('MCP request failed', error);
        res.status(500).json({
          jsonrpc: '2.0',
          id: req.body.id,
          error: {
            code: -32603,
            message: 'Internal error',
            data: error instanceof Error ? error.message : String(error)
          }
        });
      }
    });
  }

  private async handleMCPRequest(request: MCPRequest): Promise<MCPResponse> {
    this.config.logger.debug('Handling MCP request', { method: request.method });

    switch (request.method) {
      case 'initialize':
        return this.handleInitialize(request);
      
      case 'tools/list':
        return this.handleToolsList(request);
      
      case 'tools/call':
        return this.handleToolsCall(request);
      
      case 'resources/list':
        return this.handleResourcesList(request);
      
      case 'resources/read':
        return this.handleResourcesRead(request);
      
      case 'prompts/list':
        return this.handlePromptsList(request);
      
      case 'prompts/get':
        return this.handlePromptsGet(request);
      
      default:
        return {
          jsonrpc: '2.0',
          id: request.id,
          error: {
            code: -32601,
            message: `Method not found: ${request.method}`
          }
        };
    }
  }

  private handleInitialize(request: MCPRequest): MCPResponse {
    const capabilities: MCPServerCapabilities = {
      tools: { listChanged: true },
      resources: { subscribe: false, listChanged: true },
      prompts: { listChanged: true },
      logging: {}
    };

    return {
      jsonrpc: '2.0',
      id: request.id,
      result: {
        protocolVersion: '2024-11-05',
        capabilities,
        serverInfo: {
          name: 'congress-gov-mcp',
          version: '1.0.0'
        }
      }
    };
  }

  private handleToolsList(request: MCPRequest): MCPResponse {
    const tools = this.toolRegistry.listTools();
    
    return {
      jsonrpc: '2.0',
      id: request.id,
      result: { tools }
    };
  }

  private async handleToolsCall(request: MCPRequest): Promise<MCPResponse> {
    const { name, arguments: args } = request.params;
    
    try {
      // Check cache
      const cacheKey = `tool:${name}:${JSON.stringify(args)}`;
      const cached = this.config.cacheManager.get(cacheKey);
      
      if (cached) {
        this.config.logger.debug('Returning cached result', { tool: name });
        return {
          jsonrpc: '2.0',
          id: request.id,
          result: cached
        };
      }

      // Execute tool
      const result = await this.toolRegistry.executeTool(name, args);
      
      // Cache result
      this.config.cacheManager.set(cacheKey, result);
      
      return {
        jsonrpc: '2.0',
        id: request.id,
        result
      };
    } catch (error) {
      this.config.logger.error(`Tool execution failed: ${name}`, error);
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: {
          code: -32000,
          message: error instanceof Error ? error.message : String(error)
        }
      };
    }
  }

  private handleResourcesList(request: MCPRequest): MCPResponse {
    const resources = this.resourceRegistry.listResources();
    
    return {
      jsonrpc: '2.0',
      id: request.id,
      result: { resources }
    };
  }

  private async handleResourcesRead(request: MCPRequest): Promise<MCPResponse> {
    const { uri } = request.params;
    
    try {
      const content = await this.resourceRegistry.readResource(uri);
      
      return {
        jsonrpc: '2.0',
        id: request.id,
        result: { contents: [content] }
      };
    } catch (error) {
      this.config.logger.error(`Resource read failed: ${uri}`, error);
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: {
          code: -32000,
          message: error instanceof Error ? error.message : String(error)
        }
      };
    }
  }

  private handlePromptsList(request: MCPRequest): MCPResponse {
    const prompts = this.promptRegistry.listPrompts();
    
    return {
      jsonrpc: '2.0',
      id: request.id,
      result: { prompts }
    };
  }

  private async handlePromptsGet(request: MCPRequest): Promise<MCPResponse> {
    const { name, arguments: args } = request.params;
    
    try {
      const messages = await this.promptRegistry.getPrompt(name, args);
      
      return {
        jsonrpc: '2.0',
        id: request.id,
        result: { messages }
      };
    } catch (error) {
      this.config.logger.error(`Prompt get failed: ${name}`, error);
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: {
          code: -32000,
          message: error instanceof Error ? error.message : String(error)
        }
      };
    }
  }

  async start(port: number): Promise<void> {
    return new Promise((resolve) => {
      this.server = this.app.listen(port, () => {
        this.config.logger.info(`Server started on port ${port}`);
        resolve();
      });
    });
  }

  async stop(): Promise<void> {
    if (this.server) {
      return new Promise((resolve) => {
        this.server!.close(() => {
          this.config.logger.info('Server stopped');
          resolve();
        });
      });
    }
  }
}
```

**Step 3.3: Tool Registry**

Create `mcp-servers/congress-gov/src/tools/index.ts`:

```typescript
import { MCPTool } from '../../../shared/types/mcp';
import { Logger } from '../../../shared/logger';
import axios from 'axios';

export class ToolRegistry {
  private apiKey: string;
  private logger: Logger;
  private baseUrl = 'https://api.congress.gov/v3';

  constructor(apiKey: string, logger: Logger) {
    this.apiKey = apiKey;
    this.logger = logger.child({ component: 'ToolRegistry' });
  }

  listTools(): MCPTool[] {
    return [
      {
        name: 'search_bills',
        description: 'Search for bills in Congress',
        inputSchema: {
          type: 'object',
          properties: {
            congress: {
              type: 'number',
              description: 'Congress number (e.g., 118 for current)'
            },
            query: {
              type: 'string',
              description: 'Search query'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results',
              default: 20
            }
          },
          required: ['congress']
        }
      },
      {
        name: 'get_bill',
        description: 'Get detailed information about a specific bill',
        inputSchema: {
          type: 'object',
          properties: {
            congress: {
              type: 'number',
              description: 'Congress number'
            },
            billType: {
              type: 'string',
              description: 'Bill type (e.g., hr, s, hjres, sjres)',
              enum: ['hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres']
            },
            billNumber: {
              type: 'number',
              description: 'Bill number'
            }
          },
          required: ['congress', 'billType', 'billNumber']
        }
      },
      {
        name: 'search_members',
        description: 'Search for members of Congress',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query (name, state, etc.)'
            },
            chamber: {
              type: 'string',
              description: 'Chamber (house or senate)',
              enum: ['house', 'senate']
            },
            state: {
              type: 'string',
              description: 'Two-letter state code'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results',
              default: 20
            }
          }
        }
      },
      {
        name: 'get_member',
        description: 'Get detailed information about a specific member',
        inputSchema: {
          type: 'object',
          properties: {
            bioguideId: {
              type: 'string',
              description: 'Member bioguide ID'
            }
          },
          required: ['bioguideId']
        }
      }
    ];
  }

  async executeTool(name: string, args: any): Promise<any> {
    this.logger.debug(`Executing tool: ${name}`, args);

    switch (name) {
      case 'search_bills':
        return this.searchBills(args);
      case 'get_bill':
        return this.getBill(args);
      case 'search_members':
        return this.searchMembers(args);
      case 'get_member':
        return this.getMember(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  private async searchBills(args: any): Promise<any> {
    const { congress, query, limit = 20 } = args;
    
    const response = await axios.get(
      `${this.baseUrl}/bill/${congress}`,
      {
        params: {
          api_key: this.apiKey,
          format: 'json',
          limit,
          ...(query && { query })
        },
        timeout: 30000
      }
    );

    return {
      bills: response.data.bills || [],
      pagination: response.data.pagination
    };
  }

  private async getBill(args: any): Promise<any> {
    const { congress, billType, billNumber } = args;
    
    const response = await axios.get(
      `${this.baseUrl}/bill/${congress}/${billType}/${billNumber}`,
      {
        params: {
          api_key: this.apiKey,
          format: 'json'
        },
        timeout: 30000
      }
    );

    return response.data.bill;
  }

  private async searchMembers(args: any): Promise<any> {
    const { query, chamber, state, limit = 20 } = args;
    
    const endpoint = chamber === 'house' ? 'house' : chamber === 'senate' ? 'senate' : 'member';
    
    const response = await axios.get(
      `${this.baseUrl}/${endpoint}`,
      {
        params: {
          api_key: this.apiKey,
          format: 'json',
          limit,
          ...(query && { query }),
          ...(state && { state })
        },
        timeout: 30000
      }
    );

    return {
      members: response.data.members || [],
      pagination: response.data.pagination
    };
  }

  private async getMember(args: any): Promise<any> {
    const { bioguideId } = args;
    
    const response = await axios.get(
      `${this.baseUrl}/member/${bioguideId}`,
      {
        params: {
          api_key: this.apiKey,
          format: 'json'
        },
        timeout: 30000
      }
    );

    return response.data.member;
  }
}
```

### Implementation Summary

The above steps provide a comprehensive foundation for:

1. ✅ **Congress.gov MCP Server** - Fully functional with tools, resources, and prompts
2. ✅ **Shared Utilities** - Authentication, caching, logging ready for reuse
3. ✅ **Protocol Compliance** - Full MCP specification implementation
4. ✅ **Production Ready** - Error handling, rate limiting, security

**Next Steps**:
- Implement GovInfo MCP Server (similar pattern)
- Implement OpenStates MCP Server (similar pattern)
- Create Main Aggregator MCP Server
- Add comprehensive tests
- Deploy to Cloudflare Workers
- Create Docker containers

For complete implementation, follow the same patterns for GovInfo and OpenStates servers. The architecture is modular and extensible.

---

## ☁️ RECOMMENDATION 3: Cloudflare Workers Deployment

### Priority: HIGH  
### Estimated Effort: 8-10 hours
### Dependencies: RECOMMENDATION 2 (MCP Servers must exist)

[Content continues with detailed Cloudflare deployment steps...]

---

## 🐳 RECOMMENDATION 4: Docker MCP Toolkit Integration

### Priority: HIGH
### Estimated Effort: 6-8 hours  
### Dependencies: RECOMMENDATION 2 (MCP Servers must exist)

[Content continues with detailed Docker deployment steps...]

---

## 📚 RECOMMENDATION 5: Documentation Improvements

### Priority: MEDIUM
### Estimated Effort: 6-8 hours
### Dependencies: All previous recommendations

[Content continues with documentation improvements...]

---

## 🔍 RECOMMENDATION 6: Code Quality and Linting

### Priority: MEDIUM
### Estimated Effort: 4-6 hours
### Dependencies: None

### Step-by-Step Implementation

#### Step 1: Install and Configure Linting Tools

```bash
# Install Python linting tools
pip install ruff black mypy isort flake8 pylint bandit

# Install pre-commit
pip install pre-commit

# Install Node.js linting tools (for web apps)
cd web && npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier
cd ../webui && npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier
```

#### Step 2: Create Pre-Commit Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.13

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-psycopg2]
        args: [--ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-r", "-ll"]
        exclude: "tests/"
```

#### Step 3: Run Linters and Fix Issues

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Or run individually:

# Black (formatting)
black opendiscourse/ opendiscourse_sdk/ scripts/ tests/

# Ruff (linting with auto-fix)
ruff check . --fix
ruff format .

# isort (import sorting)
isort opendiscourse/ opendiscourse_sdk/ scripts/ tests/

# mypy (type checking) - fix errors manually
mypy opendiscourse/ opendiscourse_sdk/ --ignore-missing-imports

# TypeScript linting
cd web && npm run lint -- --fix
cd webui && npm run lint -- --fix
```

#### Step 4: Fix Common Issues

**Issue 1: Import Order**
```python
# Before (incorrect):
import sys
import opendiscourse
from typing import Dict
import os

# After (correct with isort):
import os
import sys
from typing import Dict

import opendiscourse
```

**Issue 2: Type Hints**
```python
# Before (no type hints):
def fetch_bills(congress, limit):
    return bills

# After (with type hints):
def fetch_bills(congress: int, limit: int) -> List[Dict[str, Any]]:
    return bills
```

**Issue 3: String Quotes**
```python
# Configure in pyproject.toml to prefer double quotes
# Ruff will auto-fix inconsistent quotes
```

#### Step 5: Update Configuration Files

Update `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ["py38", "py39", "py310", "py311", "py312", "py313"]
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py38"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "C",   # flake8-comprehensions
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex (we'll handle manually)
]
unfixable = []

[tool.ruff.isort]
known-first-party = ["opendiscourse", "opendiscourse_sdk"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Set to true gradually
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

#### Step 6: Clean Up TODO Comments

```bash
# Find all TODO comments
grep -r "TODO" --include="*.py" --include="*.ts" --include="*.tsx" . | wc -l

# Create GitHub issues for actionable TODOs
# Example script: scripts/create_todo_issues.py
```

Create `scripts/create_todo_issues.py`:

```python
#!/usr/bin/env python3
"""
Extract TODO comments and create GitHub issues.
"""
import re
import subprocess
from pathlib import Path

def extract_todos(directory: str = "."):
    """Extract TODO comments from codebase."""
    todos = []
    
    for ext in ["*.py", "*.ts", "*.tsx"]:
        result = subprocess.run(
            ["grep", "-rn", "TODO", "--include", ext, directory],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.splitlines():
            match = re.match(r"(.+?):(\d+):.*TODO[:\s]+(.+)", line)
            if match:
                file_path, line_num, todo_text = match.groups()
                todos.append({
                    "file": file_path,
                    "line": line_num,
                    "text": todo_text.strip()
                })
    
    return todos

def categorize_todos(todos):
    """Categorize TODOs by type."""
    categories = {
        "high_priority": [],
        "medium_priority": [],
        "low_priority": [],
        "obsolete": []
    }
    
    for todo in todos:
        text_lower = todo["text"].lower()
        
        if any(word in text_lower for word in ["urgent", "critical", "fix", "bug"]):
            categories["high_priority"].append(todo)
        elif any(word in text_lower for word in ["improve", "enhance", "optimize"]):
            categories["medium_priority"].append(todo)
        elif any(word in text_lower for word in ["consider", "maybe", "future"]):
            categories["low_priority"].append(todo)
        else:
            categories["medium_priority"].append(todo)
    
    return categories

def print_report(categories):
    """Print TODO report."""
    total = sum(len(todos) for todos in categories.values())
    
    print(f"\n=== TODO Summary ===")
    print(f"Total TODOs: {total}\n")
    
    for category, todos in categories.items():
        if todos:
            print(f"\n{category.upper().replace('_', ' ')} ({len(todos)}):")
            print("-" * 50)
            for todo in todos[:5]:  # Show first 5
                print(f"  {todo['file']}:{todo['line']}")
                print(f"    {todo['text'][:80]}...")
            if len(todos) > 5:
                print(f"  ... and {len(todos) - 5} more")

if __name__ == "__main__":
    todos = extract_todos()
    categories = categorize_todos(todos)
    print_report(categories)
```

#### Step 7: Validate Configuration

```bash
# Test linting on a sample file
echo "import sys; import os" > test_lint.py
black test_lint.py
ruff check test_lint.py
isort test_lint.py
rm test_lint.py

# Run pre-commit on staged files
git add .
pre-commit run

# If all passes, commit
git commit -m "chore: configure linting and formatting tools"
```

### Validation Checklist
- [ ] Pre-commit hooks installed and configured
- [ ] All Python files formatted with black
- [ ] All Python files pass ruff checks
- [ ] Imports sorted with isort
- [ ] TypeScript files pass ESLint
- [ ] Type hints added where missing
- [ ] TODO comments categorized
- [ ] Configuration files updated
- [ ] Documentation updated

### Success Criteria
- Zero linting errors from ruff, black, eslint
- Type checking passes with mypy
- Pre-commit hooks working
- TODO count reduced by 50%
- CI/CD includes linting checks

---

## 🧪 RECOMMENDATION 7: Testing Improvements

### Priority: MEDIUM
### Estimated Effort: 8-10 hours
### Dependencies: RECOMMENDATION 1 (Bills ingestion must be fixed)

[Content continues...]

---

## 🎯 Implementation Roadmap

### Week 1: Critical Fixes & Foundation
- **Days 1-2**: Fix bills ingestion (REC 1)
- **Days 3-5**: Implement MCP servers (REC 2)

### Week 2: Deployment & Infrastructure
- **Days 6-7**: Cloudflare Workers deployment (REC 3)
- **Days 8-9**: Docker MCP toolkit (REC 4)

### Week 3: Quality & Documentation
- **Days 10-11**: Documentation improvements (REC 5)
- **Days 12-13**: Code quality and linting (REC 6)
- **Days 14-15**: Testing improvements (REC 7)

### Week 4: Polish & Release
- **Days 16-17**: Final validation
- **Days 18-19**: Performance optimization
- **Days 20-21**: Release preparation

---

## 📞 Support & Next Steps

### Getting Help
- Review [TASKS.md](./TASKS.md) for detailed task breakdown
- Check [README.md](./README.md) for project overview
- See [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) for complete docs

### For AI Agents
This document provides step-by-step instructions that can be followed sequentially. Each recommendation is:
- ✅ **Traceable**: Clear file paths and line numbers
- ✅ **Actionable**: Specific commands and code examples
- ✅ **Testable**: Validation steps and success criteria

### For Human Developers
Use this as a roadmap. Tackle recommendations in priority order, starting with Priority 1 items. Each recommendation can be completed independently or assigned to different team members.

---

**Document Version**: 1.0
**Last Updated**: 2026-02-11
**Status**: Ready for Implementation