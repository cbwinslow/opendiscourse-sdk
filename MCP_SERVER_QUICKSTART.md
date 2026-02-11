# MCP Server Quick Start Guide

## 🎯 Overview
This guide provides a quick reference for implementing Model Context Protocol (MCP) servers for the OpenDiscourse SDK. For detailed implementation, see [RECOMMENDATIONS.md](./RECOMMENDATIONS.md).

## 📋 Prerequisites

### Required Tools
```bash
# Node.js 18+ and pnpm
node --version  # Should be 18+
pnpm --version  # Should be 8+

# TypeScript
pnpm add -g typescript

# Development dependencies
pnpm install
```

### Environment Variables
```bash
# .env file
CONGRESS_API_KEY=your_congress_api_key
GOVINFO_API_KEY=your_govinfo_api_key
OPENSTATES_API_KEY=your_openstates_api_key
MCP_API_KEY=your_mcp_server_api_key
```

## 🚀 Quick Start

### 1. Create Project Structure
```bash
# From repository root
mkdir -p mcp-servers/{congress-gov,govinfo,openstates,main,shared}

# Create subdirectories
for server in congress-gov govinfo openstates main; do
    mkdir -p mcp-servers/$server/{src,tests,docs}
    mkdir -p mcp-servers/$server/src/{tools,resources,prompts,handlers}
done

# Create shared utilities
mkdir -p mcp-servers/shared/{auth,cache,logger,types,utils}
```

### 2. Initialize Projects
```bash
cd mcp-servers

# Initialize each server
for server in congress-gov govinfo openstates main; do
    cd $server
    pnpm init
    cd ..
done

# Install dependencies
pnpm add express axios
pnpm add -D typescript @types/node @types/express ts-node
```

### 3. Create Base Configuration

**tsconfig.base.json**:
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
    "forceConsistentCasingInFileNames": true
  }
}
```

### 4. Implement Shared Utilities

Copy implementations from RECOMMENDATIONS.md:
- `shared/types/mcp.ts` - MCP protocol types
- `shared/auth/validator.ts` - Authentication
- `shared/cache/manager.ts` - Caching
- `shared/logger/index.ts` - Logging

### 5. Implement Congress.gov MCP Server

**Key Files**:
```
congress-gov/
├── src/
│   ├── index.ts          # Main entry point
│   ├── server.ts         # Server implementation
│   ├── tools/
│   │   └── index.ts      # Tool registry
│   ├── resources/
│   │   └── index.ts      # Resource registry
│   └── prompts/
│       └── index.ts      # Prompt registry
├── tests/
│   └── server.test.ts    # Tests
└── package.json
```

See RECOMMENDATIONS.md for complete implementations.

### 6. Run and Test

```bash
# Start server
cd mcp-servers/congress-gov
pnpm start

# Test in another terminal
curl -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

## 📚 MCP Protocol Reference

### Protocol Methods

#### initialize
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "client", "version": "1.0.0"}
  }
}
```

#### tools/list
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

#### tools/call
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_bills",
    "arguments": {
      "congress": 118,
      "query": "climate",
      "limit": 10
    }
  }
}
```

#### resources/list
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/list",
  "params": {}
}
```

#### resources/read
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "bill://118/hr/1234"
  }
}
```

## 🔧 Development Commands

### Build
```bash
pnpm run build
```

### Test
```bash
pnpm run test
```

### Lint
```bash
pnpm run lint
```

### Dev Mode (with auto-reload)
```bash
pnpm run dev
```

## 📦 Package.json Scripts

```json
{
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node-dev --respawn --transpile-only src/index.ts",
    "test": "jest",
    "lint": "eslint src --ext .ts",
    "clean": "rm -rf dist"
  }
}
```

## 🌐 Deployment

### Local Development
```bash
pnpm run dev
```

### Docker
```bash
docker build -t mcp-congress-gov .
docker run -p 3001:3001 --env-file .env mcp-congress-gov
```

### Cloudflare Workers
```bash
cd cloudflare-mcp/workers/congress-gov
wrangler publish
```

See [RECOMMENDATIONS.md](./RECOMMENDATIONS.md) for detailed deployment instructions.

## 🧪 Testing

### Unit Tests
```typescript
import { MCPServer } from '../src/server';

describe('MCPServer', () => {
  it('should initialize correctly', async () => {
    const server = new MCPServer(config);
    const response = await server.handleMCPRequest({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: { protocolVersion: '2024-11-05' }
    });
    
    expect(response.result).toBeDefined();
    expect(response.result.serverInfo.name).toBe('congress-gov-mcp');
  });
});
```

### Integration Tests
```bash
# Start server
pnpm start &

# Run tests
pnpm run test:integration

# Stop server
pkill -f "node dist/index.js"
```

## 📖 Resources

### Documentation
- **MCP Specification**: https://modelcontextprotocol.io/
- **TASKS.md**: Complete task list
- **RECOMMENDATIONS.md**: Detailed implementation guide
- **SESSION_SUMMARY_2026_02_11.md**: Session report

### Example Tools

#### Congress.gov Tools
- `search_bills` - Search bills by keyword, congress, status
- `get_bill` - Get bill details
- `search_members` - Search members
- `get_member` - Get member details
- `get_votes` - Get voting records

#### GovInfo Tools
- `search_documents` - Search documents
- `get_document` - Get document details
- `list_collections` - List collections

#### OpenStates Tools
- `search_legislation` - Search state bills
- `get_bill` - Get state bill
- `search_legislators` - Search legislators
- `get_legislator` - Get legislator details

### Resource URIs

```
# Congress.gov
bill://118/hr/1234
member://B000001
vote://118/house/1/123

# GovInfo
document://BILLS-118hr1234

# OpenStates
state_bill://ca/2023-2024/AB-123
legislator://ocd-person/abc123
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check port availability
lsof -i :3001

# Check environment variables
env | grep API_KEY

# Check logs
tail -f server.log
```

### Tool execution fails
```bash
# Test API directly
curl "https://api.congress.gov/v3/bill/118?api_key=$CONGRESS_API_KEY"

# Check authentication
curl -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
```

### Build errors
```bash
# Clean and rebuild
pnpm run clean
pnpm run build

# Check TypeScript errors
tsc --noEmit
```

## 🚀 Next Steps

1. **Implement Servers**: Follow RECOMMENDATIONS.md for detailed implementation
2. **Test Locally**: Run servers and test with cURL or Postman
3. **Deploy to Cloudflare**: Use wrangler for deployment
4. **Create Docker Images**: For self-hosting
5. **Add to Registry**: Update `.kilocode/mcp.json`

## 📞 Support

- **Issues**: Check TASKS.md for current status
- **Implementation**: See RECOMMENDATIONS.md for step-by-step guide
- **Documentation**: Review DOCUMENTATION_INDEX.md

---

**Quick Start Time**: ~2 hours to first working server
**Full Implementation**: 12-16 hours for all servers
**Status**: Ready to implement

For complete implementation details, see [RECOMMENDATIONS.md](./RECOMMENDATIONS.md).
