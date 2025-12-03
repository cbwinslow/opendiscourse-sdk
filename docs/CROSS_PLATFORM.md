# Cross-Platform Compatibility Guide

## Overview
This document outlines the cross-platform compatibility considerations and implementations for the opendiscourse project.

## Platform-Specific Configurations

### Environment Detection
```typescript
// platform.ts
export const Platform = {
  isWindows: process.platform === 'win32',
  isMacOS: process.platform === 'darwin',
  isLinux: process.platform === 'linux',
  isUnix: process.platform !== 'win32'
};
```

### Path Handling
```typescript
// paths.ts
import * as path from 'path';
import { Platform } from './platform';

export const Paths = {
  normalize: (filePath: string): string => {
    return Platform.isWindows ? filePath.replace(/\//g, '\\') : filePath;
  },
  
  join: (...paths: string[]): string => {
    return path.join(...paths);
  },
  
  getHomeDir: (): string => {
    return Platform.isWindows ? process.env.USERPROFILE! : process.env.HOME!;
  }
};
```

## Script Compatibility

### Shell Scripts
```bash
#!/bin/bash
# Cross-platform shell script template

# Detect OS
case "$(uname -s)" in
  Darwin*)  OS='macOS';;
  Linux*)   OS='Linux';;
  CYGWIN*)  OS='Windows';;
  MINGW*)   OS='Windows';;
  *)        OS='Unknown';;
esac

# OS-specific commands
if [ "$OS" = "Windows" ]; then
  # Windows commands
  PYTHON_CMD="python"
  PATH_SEP=";"
else
  # Unix commands
  PYTHON_CMD="python3"
  PATH_SEP=":"
fi
```

### Batch Scripts (Windows)
```batch
@echo off
REM Windows batch script template

set PYTHON_CMD=python
set PATH_SEP=;

REM Check Python version
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
  echo Python not found
  exit /b 1
)
```

## Database Compatibility

### Connection Strings
```typescript
// db-config.ts
export const getDbConfig = () => {
  const config = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'ragchat',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD
  };

  if (Platform.isWindows) {
    // Windows-specific settings
    config.host = config.host.replace('localhost', '127.0.0.1');
  }

  return config;
};
```

### File System Operations
```typescript
// file-ops.ts
import * as fs from 'fs/promises';
import { Platform } from './platform';

export class FileOps {
  static async readFile(filePath: string): Promise<string> {
    const normalizedPath = Platform.isWindows ? 
      filePath.replace(/\//g, '\\') : 
      filePath;
    return await fs.readFile(normalizedPath, 'utf8');
  }

  static async writeFile(filePath: string, content: string): Promise<void> {
    const normalizedPath = Platform.isWindows ? 
      filePath.replace(/\//g, '\\') : 
      filePath;
    await fs.writeFile(normalizedPath, content, 'utf8');
  }
}
```

## Process Management

### Service Management
```typescript
// service-manager.ts
import { exec } from 'child_process';
import { Platform } from './platform';

export class ServiceManager {
  static async startService(serviceName: string): Promise<void> {
    const command = Platform.isWindows ?
      `net start ${serviceName}` :
      `sudo systemctl start ${serviceName}`;
    
    return new Promise((resolve, reject) => {
      exec(command, (error) => {
        if (error) reject(error);
        else resolve();
      });
    });
  }

  static async stopService(serviceName: string): Promise<void> {
    const command = Platform.isWindows ?
      `net stop ${serviceName}` :
      `sudo systemctl stop ${serviceName}`;
    
    return new Promise((resolve, reject) => {
      exec(command, (error) => {
        if (error) reject(error);
        else resolve();
      });
    });
  }
}
```

## Docker Compatibility

### Docker Commands
```typescript
// docker-manager.ts
export class DockerManager {
  static getDockerCommand(): string {
    return Platform.isWindows ? 'docker.exe' : 'docker';
  }

  static getComposeCommand(): string {
    return Platform.isWindows ? 
      'docker-compose.exe' : 
      'docker compose';
  }

  static async runContainer(image: string, options: string[]): Promise<void> {
    const command = `${this.getDockerCommand()} run ${options.join(' ')} ${image}`;
    // Implementation...
  }
}
```

## Environment Variables

### Loading Environment Variables
```typescript
// env-loader.ts
import dotenv from 'dotenv';
import { Platform } from './platform';

export class EnvLoader {
  static load(): void {
    const envFile = Platform.isWindows ? '.env.windows' : '.env';
    dotenv.config({ path: envFile });
    
    // Set platform-specific defaults
    if (Platform.isWindows) {
      process.env.TEMP_DIR = process.env.TEMP_DIR || 'C:\\temp';
    } else {
      process.env.TEMP_DIR = process.env.TEMP_DIR || '/tmp';
    }
  }
}
```

## Testing Cross-Platform Compatibility

### Test Configuration
```typescript
// test-config.ts
import { Platform } from './platform';

export const TestConfig = {
  tempDir: Platform.isWindows ? 'C:\\temp\\test' : '/tmp/test',
  dbConfig: {
    host: Platform.isWindows ? '127.0.0.1' : 'localhost',
    // Other config...
  }
};
```

### Platform-Specific Tests
```typescript
// platform.test.ts
describe('Platform Tests', () => {
  it('should handle paths correctly', () => {
    const testPath = '/test/path';
    const normalized = Paths.normalize(testPath);
    
    if (Platform.isWindows) {
      expect(normalized).to.equal('\\test\\path');
    } else {
      expect(normalized).to.equal('/test/path');
    }
  });
});
```

## Best Practices

1. **Path Handling**
   - Always use path.join() for path concatenation
   - Use platform-agnostic path separators
   - Handle absolute vs relative paths correctly

2. **File System Operations**
   - Use fs.promises for async operations
   - Handle line endings (CRLF vs LF)
   - Use proper file permissions

3. **Process Management**
   - Use cross-platform commands when possible
   - Handle platform-specific services appropriately
   - Manage process signals correctly

4. **Environment Variables**
   - Use platform-specific defaults
   - Handle path-like variables correctly
   - Support multiple .env files

5. **Testing**
   - Test on all supported platforms
   - Use platform-specific test configurations
   - Mock platform-specific behaviors

## Troubleshooting

### Common Issues

1. **Path Separators**
   - Windows: Use `\\` or `/`
   - Unix: Use `/`
   - Solution: Use `path.join()`

2. **Line Endings**
   - Windows: CRLF (`\r\n`)
   - Unix: LF (`\n`)
   - Solution: Use `.gitattributes`

3. **File Permissions**
   - Windows: Less restrictive
   - Unix: More granular
   - Solution: Use appropriate chmod/ACL

4. **Process Management**
   - Windows: Different service management
   - Unix: Different process signals
   - Solution: Use platform detection

## Platform-Specific Configuration Files

### Windows (.env.windows)
```ini
TEMP_DIR=C:\temp
PATH_SEP=;
PYTHON_CMD=python
```

### Unix (.env.unix)
```ini
TEMP_DIR=/tmp
PATH_SEP=:
PYTHON_CMD=python3
```
