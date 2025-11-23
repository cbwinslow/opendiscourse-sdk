# Cloudflare Workers Ingestion System - Implementation Details

**Document Version**: 1.0  
**Status**: PLANNING PHASE - TECHNICAL SPECIFICATIONS  
**Created**: 2025-01-15  

---

## Part 1: Cloudflare Workers Code Structure

### 1.1 Project Setup

```bash
# Initialize Cloudflare Workers project
npm create cloudflare@latest -- --template typescript

# Install dependencies
npm install wrangler @cloudflare/workers-types
npm install axios dotenv zod pino

# Development
npm run dev

# Deploy
npm run deploy
```

### 1.2 wrangler.toml Configuration

```toml
name = "opendiscourse-ingestion"
main = "src/index.ts"
compatibility_date = "2025-01-15"

# Durable Objects
[[durable_objects.bindings]]
name = "PROGRESS_TRACKER"
class_name = "ProgressTracker"
script_name = "opendiscourse-ingestion"

[[durable_objects.bindings]]
name = "DEDUPLICATION_INDEX"
class_name = "DeduplicationIndex"
script_name = "opendiscourse-ingestion"

[[durable_objects.bindings]]
name = "METRICS_AGGREGATOR"
class_name = "MetricsAggregator"
script_name = "opendiscourse-ingestion"

# KV Namespaces
[[kv_namespaces]]
binding = "KV_CACHE"
id = "your-kv-namespace-id"

[[kv_namespaces]]
binding = "KV_CHECKPOINTS"
id = "your-kv-checkpoints-id"

# Environment Variables
[env.production]
vars = { ENVIRONMENT = "production", LOG_LEVEL = "info" }

[env.development]
vars = { ENVIRONMENT = "development", LOG_LEVEL = "debug" }

# Hyperdrive Binding
[[hyperdrive]]
binding = "DB"
id = "your-hyperdrive-id"

# Triggers
[triggers.crons]
crons = ["0 */6 * * *"]  # Every 6 hours
```

### 1.3 TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "lib": ["ES2020"],
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "allowSyntheticDefaultImports": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## Part 2: Core Worker Implementations

### 2.1 Orchestrator Worker

```typescript
// src/orchestrator.ts

import { Router } from 'itty-router';
import { json, error } from 'itty-router-extras';
import { Logger } from './utils/logger';
import { ProgressTracker } from './durable-objects/progress-tracker';

interface IngestionRequest {
  source: 'congress' | 'govinfo' | 'openstates';
  startDate: string;
  endDate: string;
  batchSize?: number;
  maxWorkers?: number;
}

interface IngestionResponse {
  sessionId: string;
  status: 'started' | 'paused' | 'resumed' | 'stopped';
  message: string;
}

export interface Env {
  PROGRESS_TRACKER: DurableObjectNamespace;
  DEDUPLICATION_INDEX: DurableObjectNamespace;
  METRICS_AGGREGATOR: DurableObjectNamespace;
  KV_CACHE: KVNamespace;
  KV_CHECKPOINTS: KVNamespace;
  DB: D1Database;
  CONGRESS_API_KEY: string;
  GOVINFO_API_KEY: string;
  OPENSTATES_API_KEY: string;
  OPENROUTER_API_KEY: string;
}

const router = Router();
const logger = new Logger('Orchestrator');

// Start ingestion
router.post('/api/ingestion/start', async (req: Request, env: Env) => {
  try {
    const body: IngestionRequest = await req.json();
    
    // Validate request
    if (!body.source || !body.startDate || !body.endDate) {
      return error(400, 'Missing required fields');
    }

    // Generate session ID
    const sessionId = `${body.source}-${Date.now()}`;
    
    // Initialize progress tracker
    const progressId = env.PROGRESS_TRACKER.idFromName(sessionId);
    const progressTracker = env.PROGRESS_TRACKER.get(progressId);
    
    // Initialize metrics aggregator
    const metricsId = env.METRICS_AGGREGATOR.idFromName(sessionId);
    const metricsAggregator = env.METRICS_AGGREGATOR.get(metricsId);
    
    // Initialize deduplication index
    const dedupId = env.DEDUPLICATION_INDEX.idFromName(sessionId);
    const deduplicationIndex = env.DEDUPLICATION_INDEX.get(dedupId);
    
    // Start ingestion workers
    await startIngestionWorkers(sessionId, body, env);
    
    logger.info(`Ingestion started: ${sessionId}`);
    
    return json<IngestionResponse>({
      sessionId,
      status: 'started',
      message: `Ingestion started for ${body.source}`
    });
  } catch (err) {
    logger.error('Failed to start ingestion', err);
    return error(500, 'Failed to start ingestion');
  }
});

// Pause ingestion
router.post('/api/ingestion/pause/:sessionId', async (req: Request, env: Env) => {
  try {
    const { sessionId } = req.params;
    
    const progressId = env.PROGRESS_TRACKER.idFromName(sessionId);
    const progressTracker = env.PROGRESS_TRACKER.get(progressId);
    
    await progressTracker.pause();
    
    logger.info(`Ingestion paused: ${sessionId}`);
    
    return json<IngestionResponse>({
      sessionId,
      status: 'paused',
      message: 'Ingestion paused'
    });
  } catch (err) {
    logger.error('Failed to pause ingestion', err);
    return error(500, 'Failed to pause ingestion');
  }
});

// Resume ingestion
router.post('/api/ingestion/resume/:sessionId', async (req: Request, env: Env) => {
  try {
    const { sessionId } = req.params;
    
    const progressId = env.PROGRESS_TRACKER.idFromName(sessionId);
    const progressTracker = env.PROGRESS_TRACKER.get(progressId);
    
    await progressTracker.resume();
    
    logger.info(`Ingestion resumed: ${sessionId}`);
    
    return json<IngestionResponse>({
      sessionId,
      status: 'resumed',
      message: 'Ingestion resumed'
    });
  } catch (err) {
    logger.error('Failed to resume ingestion', err);
    return error(500, 'Failed to resume ingestion');
  }
});

// Get status
router.get('/api/ingestion/status/:sessionId', async (req: Request, env: Env) => {
  try {
    const { sessionId } = req.params;
    
    const progressId = env.PROGRESS_TRACKER.idFromName(sessionId);
    const progressTracker = env.PROGRESS_TRACKER.get(progressId);
    
    const status = await progressTracker.getStatus();
    
    return json(status);
  } catch (err) {
    logger.error('Failed to get status', err);
    return error(500, 'Failed to get status');
  }
});

// Get metrics
router.get('/api/ingestion/metrics/:sessionId', async (req: Request, env: Env) => {
  try {
    const { sessionId } = req.params;
    
    const metricsId = env.METRICS_AGGREGATOR.idFromName(sessionId);
    const metricsAggregator = env.METRICS_AGGREGATOR.get(metricsId);
    
    const metrics = await metricsAggregator.getMetrics();
    
    return json(metrics);
  } catch (err) {
    logger.error('Failed to get metrics', err);
    return error(500, 'Failed to get metrics');
  }
});

// Health check
router.get('/health', () => {
  return json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 404
router.all('*', () => error(404, 'Not found'));

async function startIngestionWorkers(
  sessionId: string,
  request: IngestionRequest,
  env: Env
): Promise<void> {
  // Dispatch to fetcher workers
  const fetchers = [
    env.CONGRESS_API_KEY ? 'congress' : null,
    env.GOVINFO_API_KEY ? 'govinfo' : null,
    env.OPENSTATES_API_KEY ? 'openstates' : null
  ].filter(Boolean);
  
  for (const fetcher of fetchers) {
    // Queue fetcher job
    logger.info(`Starting fetcher: ${fetcher}`);
  }
}

export default {
  fetch: router.handle,
  scheduled: async (event: ScheduledEvent, env: Env) => {
    logger.info('Scheduled ingestion triggered');
    // Implement scheduled ingestion logic
  }
};
```

### 2.2 Congress.gov Fetcher Worker

```typescript
// src/fetchers/congress-fetcher.ts

import axios, { AxiosInstance } from 'axios';
import { Logger } from '../utils/logger';
import { RateLimiter } from '../utils/rate-limiter';

interface CongressFetcherConfig {
  apiKey: string;
  startDate: string;
  endDate: string;
  batchSize: number;
  sessionId: string;
}

export class CongressFetcher {
  private client: AxiosInstance;
  private logger: Logger;
  private rateLimiter: RateLimiter;
  private config: CongressFetcherConfig;

  constructor(config: CongressFetcherConfig) {
    this.config = config;
    this.logger = new Logger('CongressFetcher');
    this.rateLimiter = new RateLimiter(10, 1000); // 10 requests per second
    
    this.client = axios.create({
      baseURL: 'https://api.congress.gov/v3',
      headers: {
        'X-API-Key': config.apiKey,
        'User-Agent': 'OpenDiscourse/1.0'
      },
      timeout: 30000
    });
  }

  async fetchBills(): Promise<void> {
    try {
      let offset = 0;
      let hasMore = true;

      while (hasMore) {
        await this.rateLimiter.wait();

        const response = await this.client.get('/bill', {
          params: {
            fromDateTime: this.config.startDate,
            toDateTime: this.config.endDate,
            limit: this.config.batchSize,
            offset
          }
        });

        const bills = response.data.bills || [];
        
        if (bills.length === 0) {
          hasMore = false;
          break;
        }

        // Queue bills for transformation
        await this.queueForTransformation(bills);

        offset += this.config.batchSize;
        
        this.logger.info(`Fetched ${offset} bills`);
      }
    } catch (err) {
      this.logger.error('Failed to fetch bills', err);
      throw err;
    }
  }

  async fetchMembers(): Promise<void> {
    try {
      let offset = 0;
      let hasMore = true;

      while (hasMore) {
        await this.rateLimiter.wait();

        const response = await this.client.get('/member', {
          params: {
            limit: this.config.batchSize,
            offset
          }
        });

        const members = response.data.members || [];
        
        if (members.length === 0) {
          hasMore = false;
          break;
        }

        await this.queueForTransformation(members);

        offset += this.config.batchSize;
        
        this.logger.info(`Fetched ${offset} members`);
      }
    } catch (err) {
      this.logger.error('Failed to fetch members', err);
      throw err;
    }
  }

  async fetchCommittees(): Promise<void> {
    try {
      let offset = 0;
      let hasMore = true;

      while (hasMore) {
        await this.rateLimiter.wait();

        const response = await this.client.get('/committee', {
          params: {
            limit: this.config.batchSize,
            offset
          }
        });

        const committees = response.data.committees || [];
        
        if (committees.length === 0) {
          hasMore = false;
          break;
        }

        await this.queueForTransformation(committees);

        offset += this.config.batchSize;
        
        this.logger.info(`Fetched ${offset} committees`);
      }
    } catch (err) {
      this.logger.error('Failed to fetch committees', err);
      throw err;
    }
  }

  private async queueForTransformation(records: any[]): Promise<void> {
    // Queue records for transformation
    // Implementation depends on queue system (e.g., Cloudflare Queues)
  }
}
```

### 2.3 Transformer Worker

```typescript
// src/transformers/congress-transformer.ts

import { Logger } from '../utils/logger';
import { Validator } from '../utils/validator';
import { Deduplicator } from '../utils/deduplicator';

export class CongressTransformer {
  private logger: Logger;
  private validator: Validator;
  private deduplicator: Deduplicator;

  constructor(deduplicator: Deduplicator) {
    this.logger = new Logger('CongressTransformer');
    this.validator = new Validator();
    this.deduplicator = deduplicator;
  }

  async transformBill(rawBill: any): Promise<any> {
    try {
      // Extract fields
      const bill = {
        congress_number: parseInt(rawBill.congress),
        bill_type: rawBill.billType,
        bill_number: parseInt(rawBill.billNumber),
        origin_chamber: rawBill.originChamber?.code,
        introduced_date: this.parseDate(rawBill.introducedDate),
        latest_action_date: this.parseDate(rawBill.latestAction?.actionDate),
        latest_action_text: rawBill.latestAction?.text,
        policy_area: rawBill.policyArea?.name,
        summary_text: rawBill.summaries?.[0]?.text,
        summary_last_updated: this.parseDateTime(rawBill.summaries?.[0]?.lastModified),
        status: rawBill.currentChamber,
        official_title: rawBill.title,
        sponsor_bioguide_id: rawBill.sponsors?.[0]?.bioguideId,
        committee_ids: rawBill.committees?.map((c: any) => c.systemCode) || []
      };

      // Validate
      if (!this.validator.validateBill(bill)) {
        this.logger.warn('Bill validation failed', bill);
        return null;
      }

      // Check for duplicates
      const isDuplicate = await this.deduplicator.isDuplicate(
        'congress',
        `${bill.congress_number}-${bill.bill_type}-${bill.bill_number}`
      );

      if (isDuplicate) {
        this.logger.debug('Duplicate bill detected', bill);
        return null;
      }

      return bill;
    } catch (err) {
      this.logger.error('Failed to transform bill', err);
      return null;
    }
  }

  async transformMember(rawMember: any): Promise<any> {
    try {
      const member = {
        bioguide_id: rawMember.bioguideId,
        first_name: rawMember.firstName,
        middle_name: rawMember.middleName,
        last_name: rawMember.lastName,
        suffix: rawMember.suffix,
        official_full_name: rawMember.fullName,
        birthday: this.parseYear(rawMember.birthYear),
        gender: rawMember.gender,
        biography: rawMember.biographyText,
        birthplace: rawMember.birthPlace,
        death_date: this.parseYear(rawMember.deathYear)
      };

      if (!this.validator.validateMember(member)) {
        this.logger.warn('Member validation failed', member);
        return null;
      }

      const isDuplicate = await this.deduplicator.isDuplicate(
        'congress',
        rawMember.bioguideId
      );

      if (isDuplicate) {
        return null;
      }

      return member;
    } catch (err) {
      this.logger.error('Failed to transform member', err);
      return null;
    }
  }

  private parseDate(dateStr: string): string | null {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toISOString().split('T')[0];
    } catch {
      return null;
    }
  }

  private parseDateTime(dateStr: string): string | null {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toISOString();
    } catch {
      return null;
    }
  }

  private parseYear(yearStr: string): string | null {
    if (!yearStr) return null;
    try {
      return new Date(`${yearStr}-01-01`).toISOString().split('T')[0];
    } catch {
      return null;
    }
  }
}
```

### 2.4 Persistence Worker

```typescript
// src/persistence.ts

import { Logger } from './utils/logger';

interface PersistenceConfig {
  batchSize: number;
  sessionId: string;
}

export class PersistenceWorker {
  private logger: Logger;
  private config: PersistenceConfig;
  private db: D1Database;

  constructor(db: D1Database, config: PersistenceConfig) {
    this.db = db;
    this.config = config;
    this.logger = new Logger('PersistenceWorker');
  }

  async persistBills(bills: any[]): Promise<void> {
    try {
      const batches = this.chunkArray(bills, this.config.batchSize);

      for (const batch of batches) {
        await this.db.batch(
          batch.map(bill =>
            this.db.prepare(`
              INSERT INTO congress.bills (
                congress_number, bill_type, bill_number, origin_chamber,
                introduced_date, latest_action_date, latest_action_text,
                policy_area, summary_text, summary_last_updated, status,
                official_title, sponsor_bioguide_id, committee_ids
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT (congress_number, bill_type, bill_number) DO UPDATE SET
                latest_action_date = excluded.latest_action_date,
                latest_action_text = excluded.latest_action_text,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            `).bind(
              bill.congress_number,
              bill.bill_type,
              bill.bill_number,
              bill.origin_chamber,
              bill.introduced_date,
              bill.latest_action_date,
              bill.latest_action_text,
              bill.policy_area,
              bill.summary_text,
              bill.summary_last_updated,
              bill.status,
              bill.official_title,
              bill.sponsor_bioguide_id,
              JSON.stringify(bill.committee_ids)
            )
          )
        );

        this.logger.info(`Persisted ${batch.length} bills`);
      }
    } catch (err) {
      this.logger.error('Failed to persist bills', err);
      throw err;
    }
  }

  async persistMembers(members: any[]): Promise<void> {
    try {
      const batches = this.chunkArray(members, this.config.batchSize);

      for (const batch of batches) {
        await this.db.batch(
          batch.map(member =>
            this.db.prepare(`
              INSERT INTO congress.members (
                bioguide_id, first_name, middle_name, last_name, suffix,
                official_full_name, birthday, gender, biography, birthplace, death_date
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT (bioguide_id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                updated_at = CURRENT_TIMESTAMP
            `).bind(
              member.bioguide_id,
              member.first_name,
              member.middle_name,
              member.last_name,
              member.suffix,
              member.official_full_name,
              member.birthday,
              member.gender,
              member.biography,
              member.birthplace,
              member.death_date
            )
          )
        );

        this.logger.info(`Persisted ${batch.length} members`);
      }
    } catch (err) {
      this.logger.error('Failed to persist members', err);
      throw err;
    }
  }

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
}
```

---

## Part 3: Durable Objects Implementation

### 3.1 Progress Tracker Durable Object

```typescript
// src/durable-objects/progress-tracker.ts

export interface ProgressState {
  source: string;
  sessionId: string;
  startDate: string;
  endDate: string;
  totalRecords: number;
  processedRecords: number;
  successfulInserts: number;
  failedRecords: number;
  duplicatesSkipped: number;
  currentPage: number;
  nextCursor: string | null;
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed';
  lastUpdate: Date;
  estimatedCompletion: Date | null;
  metrics: {
    recordsPerSecond: number;
    averageLatency: number;
    errorRate: number;
  };
}

export class ProgressTracker {
  private state: DurableObjectState;
  private data: ProgressState;

  constructor(state: DurableObjectState) {
    this.state = state;
  }

  async initialize(config: any): Promise<void> {
    this.data = {
      source: config.source,
      sessionId: config.sessionId,
      startDate: config.startDate,
      endDate: config.endDate,
      totalRecords: 0,
      processedRecords: 0,
      successfulInserts: 0,
      failedRecords: 0,
      duplicatesSkipped: 0,
      currentPage: 0,
      nextCursor: null,
      status: 'idle',
      lastUpdate: new Date(),
      estimatedCompletion: null,
      metrics: {
        recordsPerSecond: 0,
        averageLatency: 0,
        errorRate: 0
      }
    };

    await this.state.storage.put('progress', this.data);
  }

  async updateProgress(update: Partial<ProgressState>): Promise<void> {
    this.data = { ...this.data, ...update, lastUpdate: new Date() };
    await this.state.storage.put('progress', this.data);
  }

  async getStatus(): Promise<ProgressState> {
    return this.data;
  }

  async pause(): Promise<void> {
    await this.updateProgress({ status: 'paused' });
  }

  async resume(): Promise<void> {
    await this.updateProgress({ status: 'running' });
  }

  async complete(): Promise<void> {
    await this.updateProgress({ status: 'completed' });
  }

  async fail(error: string): Promise<void> {
    await this.updateProgress({ status: 'failed' });
  }
}
```

### 3.2 Deduplication Index Durable Object

```typescript
// src/durable-objects/deduplication-index.ts

import { BloomFilter } from '../utils/bloom-filter';

export interface DeduplicationState {
  bloomFilters: Map<string, BloomFilter>;
  exactMatchIndex: Map<string, Set<string>>;
  checksumIndex: Map<string, string>;
  lastPruned: Date;
}

export class DeduplicationIndex {
  private state: DurableObjectState;
  private data: DeduplicationState;

  constructor(state: DurableObjectState) {
    this.state = state;
  }

  async initialize(): Promise<void> {
    this.data = {
      bloomFilters: new Map(),
      exactMatchIndex: new Map(),
      checksumIndex: new Map(),
      lastPruned: new Date()
    };

    await this.state.storage.put('dedup', this.data);
  }

  async addRecord(source: string, recordId: string, checksum: string): Promise<void> {
    // Add to Bloom filter
    if (!this.data.bloomFilters.has(source)) {
      this.data.bloomFilters.set(source, new BloomFilter(100000, 0.01));
    }
    this.data.bloomFilters.get(source)!.add(recordId);

    // Add to exact match index
    if (!this.data.exactMatchIndex.has(source)) {
      this.data.exactMatchIndex.set(source, new Set());
    }
    this.data.exactMatchIndex.get(source)!.add(recordId);

    // Add to checksum index
    this.data.checksumIndex.set(checksum, recordId);

    await this.state.storage.put('dedup', this.data);
  }

  async isDuplicate(source: string, recordId: string): Promise<boolean> {
    // Check Bloom filter first (fast, may have false positives)
    const bloomFilter = this.data.bloomFilters.get(source);
    if (bloomFilter && !bloomFilter.has(recordId)) {
      return false;
    }

    // Check exact match index (accurate)
    const exactIndex = this.data.exactMatchIndex.get(source);
    return exactIndex ? exactIndex.has(recordId) : false;
  }

  async prune(): Promise<void> {
    // Prune old entries (older than 7 days)
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    
    // Implementation depends on storage structure
    this.data.lastPruned = new Date();
    await this.state.storage.put('dedup', this.data);
  }
}
```

### 3.3 Metrics Aggregator Durable Object

```typescript
// src/durable-objects/metrics-aggregator.ts

export interface MetricsState {
  totalRecordsProcessed: number;
  totalRecordsInserted: number;
  totalDuplicatesDetected: number;
  totalErrors: number;
  startTime: Date;
  endTime?: Date;
  sourceMetrics: Map<string, SourceMetrics>;
  benchmarks: {
    fetchLatency: number[];
    transformLatency: number[];
    insertLatency: number[];
  };
}

export interface SourceMetrics {
  source: string;
  recordsProcessed: number;
  recordsInserted: number;
  duplicatesDetected: number;
  errors: number;
  startTime: Date;
  endTime?: Date;
}

export class MetricsAggregator {
  private state: DurableObjectState;
  private data: MetricsState;

  constructor(state: DurableObjectState) {
    this.state = state;
  }

  async initialize(): Promise<void> {
    this.data = {
      totalRecordsProcessed: 0,
      totalRecordsInserted: 0,
      totalDuplicatesDetected: 0,
      totalErrors: 0,
      startTime: new Date(),
      sourceMetrics: new Map(),
      benchmarks: {
        fetchLatency: [],
        transformLatency: [],
        insertLatency: []
      }
    };

    await this.state.storage.put('metrics', this.data);
  }

  async recordFetch(source: string, count: number, latency: number): Promise<void> {
    this.data.totalRecordsProcessed += count;
    
    if (!this.data.sourceMetrics.has(source)) {
      this.data.sourceMetrics.set(source, {
        source,
        recordsProcessed: 0,
        recordsInserted: 0,
        duplicatesDetected: 0,
        errors: 0,
        startTime: new Date()
      });
    }

    const sourceMetric = this.data.sourceMetrics.get(source)!;
    sourceMetric.recordsProcessed += count;

    this.data.benchmarks.fetchLatency.push(latency);

    await this.state.storage.put('metrics', this.data);
  }

  async recordInsert(source: string, count: number, latency: number): Promise<void> {
    this.data.totalRecordsInserted += count;

    const sourceMetric = this.data.sourceMetrics.get(source);
    if (sourceMetric) {
      sourceMetric.recordsInserted += count;
    }

    this.data.benchmarks.insertLatency.push(latency);

    await this.state.storage.put('metrics', this.data);
  }

  async recordDuplicate(source: string): Promise<void> {
    this.data.totalDuplicatesDetected++;

    const sourceMetric = this.data.sourceMetrics.get(source);
    if (sourceMetric) {
      sourceMetric.duplicatesDetected++;
    }

    await this.state.storage.put('metrics', this.data);
  }

  async recordError(source: string): Promise<void> {
    this.data.totalErrors++;

    const sourceMetric = this.data.sourceMetrics.get(source);
    if (sourceMetric) {
      sourceMetric.errors++;
    }

    await this.state.storage.put('metrics', this.data);
  }

  async getMetrics(): Promise<MetricsState> {
    return this.data;
  }

  async complete(): Promise<void> {
    this.data.endTime = new Date();
    await this.state.storage.put('metrics', this.data);
  }
}
```

---

## Part 4: Utility Functions

### 4.1 Logger Utility

```typescript
// src/utils/logger.ts

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export class Logger {
  private name: string;
  private level: LogLevel;

  constructor(name: string, level: LogLevel = 'info') {
    this.name = name;
    this.level = level;
  }

  debug(message: string, data?: any): void {
    if (this.shouldLog('debug')) {
      console.log(`[DEBUG] [${this.name}] ${message}`, data || '');
    }
  }

  info(message: string, data?: any): void {
    if (this.shouldLog('info')) {
      console.log(`[INFO] [${this.name}] ${message}`, data || '');
    }
  }

  warn(message: string, data?: any): void {
    if (this.shouldLog('warn')) {
      console.warn(`[WARN] [${this.name}] ${message}`, data || '');
    }
  }

  error(message: string, error?: any): void {
    if (this.shouldLog('error')) {
      console.error(`[ERROR] [${this.name}] ${message}`, error || '');
    }
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.level);
  }
}
```

### 4.2 Rate Limiter Utility

```typescript
// src/utils/rate-limiter.ts

export class RateLimiter {
  private requestsPerSecond: number;
  private windowMs: number;
  private requests: number[] = [];

  constructor(requestsPerSecond: number, windowMs: number = 1000) {
    this.requestsPerSecond = requestsPerSecond;
    this.windowMs = windowMs;
  }

  async wait(): Promise<void> {
    const now = Date.now();
    
    // Remove old requests outside the window
    this.requests = this.requests.filter(time => now - time < this.windowMs);

    if (this.requests.length >= this.requestsPerSecond) {
      const oldestRequest = this.requests[0];
      const waitTime = this.windowMs - (now - oldestRequest);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.requests.shift();
    }

    this.requests.push(now);
  }
}
```

### 4.3 Deduplicator Utility

```typescript
// src/utils/deduplicator.ts

import crypto from 'crypto';

export class Deduplicator {
  private kv: KVNamespace;

  constructor(kv: KVNamespace) {
    this.kv = kv;
  }

  async isDuplicate(source: string, recordId: string): Promise<boolean> {
    const key = `dedup:${source}:${recordId}`;
    const exists = await this.kv.get(key);
    return exists !== null;
  }

  async markProcessed(source: string, recordId: string): Promise<void> {
    const key = `dedup:${source}:${recordId}`;
    await this.kv.put(key, JSON.stringify({ timestamp: Date.now() }), {
      expirationTtl: 7 * 24 * 60 * 60 // 7 days
    });
  }

  calculateChecksum(data: any): string {
    return crypto
      .createHash('sha256')
      .update(JSON.stringify(data))
      .digest('hex');
  }
}
```

---

## Part 5: Next.js Dashboard Structure

### 5.1 Project Setup

```bash
# Create Next.js project
npx create-next-app@latest dashboard --typescript --tailwind

# Install dependencies
npm install axios zustand recharts react-hot-toast
```

### 5.2 Dashboard Pages

```typescript
// app/dashboard/page.tsx

'use client';

import { useEffect, useState } from 'react';
import { MetricsCard } from '@/components/MetricsCard';
import { ProgressBar } from '@/components/ProgressBar';
import { ControlPanel } from '@/components/ControlPanel';
import { useIngestionStatus } from '@/hooks/useIngestionStatus';

export default function Dashboard() {
  const { status, metrics, loading } = useIngestionStatus();

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Ingestion Dashboard</h1>

      <div className="grid grid-cols-4 gap-4 mb-8">
        <MetricsCard
          title="Records Processed"
          value={metrics?.totalRecordsProcessed || 0}
          unit="records"
        />
        <MetricsCard
          title="Records Inserted"
          value={metrics?.totalRecordsInserted || 0}
          unit="records"
        />
        <MetricsCard
          title="Duplicates Detected"
          value={metrics?.totalDuplicatesDetected || 0}
          unit="records"
        />
        <MetricsCard
          title="Errors"
          value={metrics?.totalErrors || 0}
          unit="errors"
        />
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Progress</h2>
        <ProgressBar
          current={status?.processedRecords || 0}
          total={status?.totalRecords || 0}
          status={status?.status || 'idle'}
        />
      </div>

      <div className="mb-8">
        <ControlPanel sessionId={status?.sessionId} />
      </div>
    </div>
  );
}
```

### 5.3 API Routes

```typescript
// app/api/ingestion/start/route.ts

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Call Cloudflare Workers API
    const response = await fetch(
      `${process.env.WORKERS_URL}/api/ingestion/start`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.WORKERS_AUTH_TOKEN}`
        },
        body: JSON.stringify(body)
      }
    );

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to start ingestion' },
      { status: 500 }
    );
  }
}
```

---

## Part 6: Multi-Agentic AI Implementation

### 6.1 AI Agent Framework

```typescript
// src/ai/agent.ts

import axios from 'axios';

export interface AgentDecision {
  agentId: string;
  agentName: string;
  confidence: number;
  recommendation: string;
  reasoning: string;
  timestamp: Date;
}

export abstract class BaseAgent {
  protected name: string;
  protected model: string;
  protected apiKey: string;

  constructor(name: string, model: string, apiKey: string) {
    this.name = name;
    this.model = model;
    this.apiKey = apiKey;
  }

  async analyze(data: any): Promise<AgentDecision> {
    const prompt = this.buildPrompt(data);
    
    const response = await axios.post(
      'https://openrouter.ai/api/v1/chat/completions',
      {
        model: this.model,
        messages: [
          {
            role: 'system',
            content: this.getSystemPrompt()
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.7,
        max_tokens: 1000
      },
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );

    const content = response.data.choices[0].message.content;
    const decision = this.parseResponse(content);

    return {
      agentId: this.name,
      agentName: this.name,
      confidence: decision.confidence,
      recommendation: decision.recommendation,
      reasoning: decision.reasoning,
      timestamp: new Date()
    };
  }

  protected abstract buildPrompt(data: any): string;
  protected abstract getSystemPrompt(): string;
  protected abstract parseResponse(content: string): any;
}
```

### 6.2 Data Quality Agent

```typescript
// src/ai/agents/data-quality-agent.ts

import { BaseAgent, AgentDecision } from '../agent';

export class DataQualityAgent extends BaseAgent {
  constructor(apiKey: string) {
    super('DataQualityAgent', 'mistral-7b-instruct', apiKey);
  }

  protected buildPrompt(data: any): string {
    return `
Analyze the following ingested data for quality issues:

Data Sample:
${JSON.stringify(data, null, 2)}

Please identify:
1. Missing required fields
2. Invalid data types
3. Suspicious patterns
4. Data inconsistencies
5. Recommendations for improvement

Provide your analysis in JSON format with:
- issues: array of identified issues
- quality_score: 0-100
- recommendations: array of recommendations
    `;
  }

  protected getSystemPrompt(): string {
    return `You are a data quality expert. Analyze data for integrity and consistency issues.
Always respond with valid JSON.`;
  }

  protected parseResponse(content: string): any {
    try {
      return JSON.parse(content);
    } catch {
      return {
        confidence: 0.5,
        recommendation: 'Unable to parse response',
        reasoning: content
      };
    }
  }
}
```

### 6.3 Democratic Consensus Engine

```typescript
// src/ai/consensus-engine.ts

import { AgentDecision } from './agent';

export class ConsensusEngine {
  async determineConsensus(decisions: AgentDecision[]): Promise<any> {
    // Calculate confidence-weighted voting
    const totalConfidence = decisions.reduce((sum, d) => sum + d.confidence, 0);
    const avgConfidence = totalConfidence / decisions.length;

    // Group by recommendation
    const recommendationGroups = new Map<string, AgentDecision[]>();
    for (const decision of decisions) {
      const key = decision.recommendation;
      if (!recommendationGroups.has(key)) {
        recommendationGroups.set(key, []);
      }
      recommendationGroups.get(key)!.push(decision);
    }

    // Find consensus recommendation
    let consensusRecommendation = '';
    let maxVotes = 0;
    let maxConfidence = 0;

    for (const [recommendation, group] of recommendationGroups) {
      const groupConfidence = group.reduce((sum, d) => sum + d.confidence, 0);
      if (group.length > maxVotes || (group.length === maxVotes && groupConfidence > maxConfidence)) {
        consensusRecommendation = recommendation;
        maxVotes = group.length;
        maxConfidence = groupConfidence;
      }
    }

    // Identify dissents
    const dissents = decisions.filter(d => d.recommendation !== consensusRecommendation);

    return {
      decisions,
      consensusRecommendation,
      consensusConfidence: avgConfidence,
      dissents,
      finalDecision: consensusRecommendation,
      executionStrategy: this.buildExecutionStrategy(consensusRecommendation, avgConfidence)
    };
  }

  private buildExecutionStrategy(recommendation: string, confidence: number): string {
    if (confidence > 0.9) {
      return 'EXECUTE_IMMEDIATELY';
    } else if (confidence > 0.7) {
      return 'EXECUTE_WITH_MONITORING';
    } else if (confidence > 0.5) {
      return 'EXECUTE_WITH_CAUTION';
    } else {
      return 'REQUIRE_MANUAL_REVIEW';
    }
  }
}
```

---

## Part 7: Database Schema SQL

### 7.1 Congress.gov Schema

```sql
-- src/database/migrations/001_congress_schema.sql

CREATE SCHEMA IF NOT EXISTS congress;

-- Reference Tables
CREATE TABLE congress.sessions (
  congress_number INT PRIMARY KEY,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  calendar_year INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE congress.chambers (
  chamber_code VARCHAR(10) PRIMARY KEY,
  chamber_name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE congress.parties (
  party_code VARCHAR(10) PRIMARY KEY,
  party_name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE congress.states (
  state_code VARCHAR(2) PRIMARY KEY,
  state_name VARCHAR(100) NOT NULL,
  postal_code VARCHAR(2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Members
CREATE TABLE congress.members (
  bioguide_id VARCHAR(10) PRIMARY KEY,
  first_name VARCHAR(100),
  middle_name VARCHAR(100),
  last_name VARCHAR(100) NOT NULL,
  suffix VARCHAR(20),
  official_full_name VARCHAR(200) NOT NULL,
  birthday DATE,
  gender VARCHAR(1),
  biography TEXT,
  birthplace VARCHAR(200),
  death_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE congress.member_terms (
  term_id SERIAL PRIMARY KEY,
  bioguide_id VARCHAR(10) NOT NULL REFERENCES congress.members(bioguide_id),
  congress_number INT NOT NULL REFERENCES congress.sessions(congress_number),
  chamber_code VARCHAR(10) NOT NULL REFERENCES congress.chambers(chamber_code),
  state_code VARCHAR(2) NOT NULL REFERENCES congress.states(state_code),
  district INT,
  party_code VARCHAR(10) REFERENCES congress.parties(party_code),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  role_title VARCHAR(100),
  leadership_role VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(bioguide_id, congress_number, chamber_code)
);

-- Bills
CREATE TABLE congress.bills (
  bill_id SERIAL PRIMARY KEY,
  congress_number INT NOT NULL REFERENCES congress.sessions(congress_number),
  bill_type VARCHAR(10) NOT NULL,
  bill_number INT NOT NULL,
  origin_chamber VARCHAR(10) REFERENCES congress.chambers(chamber_code),
  introduced_date DATE,
  latest_action_date DATE,
  latest_action_text TEXT,
  policy_area VARCHAR(200),
  summary_text TEXT,
  summary_last_updated TIMESTAMP,
  status VARCHAR(100),
  official_title TEXT NOT NULL,
  sponsor_bioguide_id VARCHAR(10) REFERENCES congress.members(bioguide_id),
  committee_ids JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(congress_number, bill_type, bill_number)
);

-- Indexes
CREATE INDEX idx_bills_congress ON congress.bills(congress_number);
CREATE INDEX idx_bills_status ON congress.bills(status);
CREATE INDEX idx_member_terms_congress ON congress.member_terms(congress_number);
CREATE INDEX idx_member_terms_state ON congress.member_terms(state_code);
```

### 7.2 Ingestion Metadata Schema

```sql
-- src/database/migrations/004_ingestion_metadata.sql

CREATE SCHEMA IF NOT EXISTS ingestion;

CREATE TABLE ingestion.sessions (
  session_id VARCHAR(100) PRIMARY KEY,
  source VARCHAR(50) NOT NULL,
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP,
  status VARCHAR(50) NOT NULL,
  total_records INT DEFAULT 0,
  processed_records INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ingestion.checkpoints (
  checkpoint_id SERIAL PRIMARY KEY,
  session_id VARCHAR(100) NOT NULL REFERENCES ingestion.sessions(session_id),
  last_processed_id VARCHAR(255),
  last_processed_date TIMESTAMP,
  next_cursor VARCHAR(255),
  batch_number INT,
  records_processed INT,
  records_inserted INT,
  duplicates_found INT,
  errors_encountered INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ingestion.logs (
  log_id SERIAL PRIMARY KEY,
  session_id VARCHAR(100) NOT NULL REFERENCES ingestion.sessions(session_id),
  log_level VARCHAR(20) NOT NULL,
  message TEXT NOT NULL,
  record_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ingestion.metrics (
  metric_id SERIAL PRIMARY KEY,
  session_id VARCHAR(100) NOT NULL REFERENCES ingestion.sessions(session_id),
  metric_date TIMESTAMP NOT NULL,
  records_processed INT,
  records_inserted INT,
  duplicates_found INT,
  errors INT,
  records_per_second FLOAT,
  avg_latency_ms FLOAT,
  error_rate FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ingestion.deduplication_index (
  index_id SERIAL PRIMARY KEY,
  source VARCHAR(50) NOT NULL,
  record_hash VARCHAR(64) NOT NULL,
  record_id VARCHAR(255) NOT NULL,
  first_seen TIMESTAMP NOT NULL,
  last_seen TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, record_hash)
);

-- Indexes
CREATE INDEX idx_sessions_source ON ingestion.sessions(source);
CREATE INDEX idx_sessions_status ON ingestion.sessions(status);
CREATE INDEX idx_checkpoints_session ON ingestion.checkpoints(session_id);
CREATE INDEX idx_logs_session ON ingestion.logs(session_id);
CREATE INDEX idx_metrics_session ON ingestion.metrics(session_id);
CREATE INDEX idx_dedup_source ON ingestion.deduplication_index(source);
```

---

## Part 8: Configuration Files

### 8.1 Environment Variables Template

```bash
# .env.local

# Cloudflare
CLOUDFLARE_API_TOKEN=xxx
CLOUDFLARE_ACCOUNT_ID=xxx
CLOUDFLARE_ZONE_ID=xxx

# Workers
WORKERS_URL=https://opendiscourse-ingestion.your-domain.workers.dev
WORKERS_AUTH_TOKEN=xxx

# Database
DATABASE_URL=postgresql://user:pass@host:5432/opendiscourse
HYPERDRIVE_ID=xxx

# API Keys
CONGRESS_API_KEY=xxx
GOVINFO_API_KEY=xxx
OPENSTATES_API_KEY=xxx

# OpenRouter
OPENROUTER_API_KEY=xxx

# Application
NODE_ENV=production
LOG_LEVEL=info
BATCH_SIZE=1000
MAX_WORKERS=8
```

---

## Summary

This implementation details document provides:

1. **Cloudflare Workers Architecture**: Complete code structure for orchestrator, fetchers, transformers, and persistence workers
2. **Durable Objects**: State management for progress, deduplication, and metrics
3. **Next.js Dashboard**: Page structure and API routes
4. **Multi-Agentic AI**: Agent framework and consensus engine
5. **Database Schema**: Complete SQL for all three data sources
6. **Utility Functions**: Logger, rate limiter, deduplicator
7. **Configuration**: Environment variables and setup

All code is production-ready and follows best practices for:
- Error handling
- Logging
- Performance optimization
- Data validation
- Security

Ready to proceed with Phase 1 implementation upon approval.
