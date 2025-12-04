# Scripts Documentation

## Overview
This document provides detailed documentation for all automation scripts in the opendiscourse project.

## Agent Scripts

### Ollama Integration Scripts

#### `server/scripts/delegateToOllama.ts`
```typescript
// Delegates tasks to Ollama agent
import { OllamaClient } from '../services/ollamaClient';

interface TaskOptions {
  model: string;
  prompt: string;
  temperature?: number;
  maxTokens?: number;
}

async function delegateTask(options: TaskOptions) {
  const client = new OllamaClient();
  return await client.submit(options);
}
```

Usage:
```bash
# Linux/macOS
npm run delegate:ollama -- --prompt="Write a function" --model="codellama"

# Windows (PowerShell)
npm run delegate:ollama -- '--prompt=Write a function' '--model=codellama'
```

#### `server/scripts/ollamaApiHealthCheck.ts`
```typescript
// Health check for Ollama API
async function checkHealth() {
  const endpoints = [
    '/api/health',
    '/api/models',
    '/api/generate'
  ];
  // Implementation details...
}
```

### Agent-Zero Integration Scripts

#### `server/scripts/agentZeroReview.ts`
```typescript
interface ReviewRequest {
  prId: string;
  files: string[];
  context: string;
}

async function requestReview(options: ReviewRequest) {
  // Implementation details...
}
```

### OpenAI Codex Scripts

#### `server/scripts/delegateToCodex.ts`
```typescript
interface CodexOptions {
  prompt: string;
  language: string;
  maxTokens: number;
}

async function generateCode(options: CodexOptions) {
  // Implementation details...
}
```

## Database Scripts

### Migration Scripts

#### `server/scripts/dbMigrate.ts`
```typescript
import { migrate } from 'drizzle-orm/postgres-js/migrator';

async function runMigrations() {
  // Implementation details...
}
```

Platform-specific usage:
```bash
# Linux/macOS
./scripts/db-migrate.sh

# Windows
.\scripts\db-migrate.bat
```

### Backup Scripts

#### `server/scripts/dbBackup.sh`
```bash
#!/bin/bash
# Database backup script
DB_NAME=${1:-ragchat}
BACKUP_DIR=${2:-./backups}
DATE=$(date +%Y%m%d_%H%M%S)

# Cross-platform implementation...
```

Windows equivalent (`dbBackup.bat`):
```batch
@echo off
set DB_NAME=%1
set BACKUP_DIR=%2
:: Windows-specific implementation...
```

## Monitoring Scripts

### `server/scripts/monitorAgent.ts`
```typescript
interface MetricsConfig {
  interval: number;
  targets: string[];
  alertThresholds: Record<string, number>;
}

class AgentMonitor {
  // Implementation details...
}
```

### `server/scripts/healthCheck.ts`
```typescript
const healthChecks = {
  database: async () => { /* ... */ },
  ollama: async () => { /* ... */ },
  codex: async () => { /* ... */ },
  agentZero: async () => { /* ... */ }
};
```

## Vector Store Scripts

### `server/scripts/vectorStoreManager.ts`
```typescript
interface VectorConfig {
  engine: 'elasticsearch' | 'weaviate';
  dimension: number;
  similarity: 'cosine' | 'l2' | 'ip';
}

class VectorStoreManager {
  // Implementation details...
}
```

## Cross-Platform Compatibility

### Environment Detection
```typescript
const isWindows = process.platform === 'win32';
const isMacOS = process.platform === 'darwin';
const isLinux = process.platform === 'linux';

export function getPathSeparator() {
  return isWindows ? '\\' : '/';
}
```

### Shell Command Execution
```typescript
import { exec } from 'child_process';

export function executeCommand(command: string): Promise<string> {
  const shellPrefix = isWindows ? 'cmd /c ' : '';
  return new Promise((resolve, reject) => {
    exec(shellPrefix + command, (error, stdout, stderr) => {
      if (error) reject(error);
      else resolve(stdout);
    });
  });
}
```

## Best Practices

1. **Error Handling**
```typescript
try {
  await runScript();
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}
```

2. **Logging**
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});
```

3. **Configuration Management**
```typescript
import dotenv from 'dotenv';
import path from 'path';

const envPath = path.resolve(process.cwd(), '.env');
dotenv.config({ path: envPath });
```

## Script Development Guidelines

1. Always include error handling
2. Add logging for important operations
3. Make scripts cross-platform compatible
4. Include usage examples
5. Document dependencies and requirements
6. Add type definitions for TypeScript
7. Include test cases

## Testing Scripts

```typescript
import { expect } from 'chai';
import { delegateToOllama } from './delegateToOllama';

describe('Ollama Delegation', () => {
  it('should successfully delegate task', async () => {
    const result = await delegateToOllama({
      prompt: 'test prompt',
      model: 'codellama'
    });
    expect(result).to.have.property('success', true);
  });
});
```

### Monitoring Scripts

#### `scripts/monitoring/job_monitor.py`
Monitors ingestion log files for errors and prints alerts. This can be extended to send notifications to external services.
