# OpenDiscourse Caddy Development Server

This directory contains a comprehensive Caddy-based development environment for OpenDiscourse with custom plugins and advanced configuration.

## 🚀 Quick Start

### Option 1: Quick Development (Fastest)
```bash
# Download and run immediately
./scripts/caddy-quick.sh start
```

### Option 2: Full Custom Build
```bash
# Build custom Caddy with plugins
./scripts/build-caddy.sh

# Start development environment
./scripts/dev-start.sh
```

### Option 3: Docker Environment
```bash
# Start with Docker Compose
./scripts/dev-docker.sh start
```

## 📋 What's Included

### Custom Caddy Build
- **Core Modules**: All standard Caddy modules
- **Security**: Advanced authentication and rate limiting
- **Development**: Hot reloading and debugging tools
- **Observability**: Metrics, logging, and monitoring
- **Performance**: Caching and compression

### Development Features
- 🔄 **Hot Reloading**: Automatic restart on file changes
- 📊 **Monitoring Dashboard**: Real-time metrics at http://localhost:9090
- 📁 **File Browser**: Development file access at http://localhost:8081
- 🔧 **API Proxy**: Seamless backend integration
- 🌐 **CORS Support**: Frontend/backend communication
- 📝 **Request Logging**: Detailed access logs

### Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Main App | http://localhost:8080 | Primary web interface |
| API Backend | http://localhost:8000 | FastAPI REST API |
| Monitoring | http://localhost:9090 | Development dashboard |
| File Browser | http://localhost:8081 | Static file serving |
| Health Check | http://localhost:8080/health | Service status |

## 🔧 Configuration

### Caddyfile Structure
```
Caddyfile                 # Main development configuration
Caddyfile.dev            # Minimal quick-start config
sites/*.caddy            # Additional site configurations
```

### Key Features in Caddyfile
- **Reverse Proxy**: API requests to FastAPI backend
- **Static Files**: Web interface and documentation
- **Security Headers**: CORS, XSS protection, content type
- **Compression**: Gzip and Zstd for better performance
- **Health Checks**: Automatic backend health monitoring
- **Error Handling**: Custom 404 pages and error responses

## 📦 Plugin Ecosystem

### Included Plugins
```go
// Core functionality
_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/reverseproxy"
_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/fileserver"
_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/templates"

// Security and authentication
_ "github.com/greenpau/caddy-security"
_ "github.com/mholt/caddy-ratelimit"
_ "github.com/hslatman/caddy-crowdsec-bouncer"

// Development and debugging
_ "github.com/abiosoft/caddy-exec"
_ "github.com/caddyserver/transform-encoder"

// Performance and caching
_ "github.com/sillygod/cdp-cache"
```

## 🛠️ Development Scripts

### Build Scripts
```bash
./scripts/build-caddy.sh     # Build custom Caddy binary
./scripts/dev-start.sh       # Start local development
./scripts/dev-docker.sh      # Docker-based development
./scripts/caddy-quick.sh     # Quick minimal setup
```

### Script Options
```bash
# Local development
./scripts/build-caddy.sh
./scripts/dev-start.sh

# Docker development
./scripts/dev-docker.sh start
./scripts/dev-docker.sh logs caddy-dev
./scripts/dev-docker.sh exec api-backend bash

# Quick setup
./scripts/caddy-quick.sh start
./scripts/caddy-quick.sh status
./scripts/caddy-quick.sh stop
```

## 🐳 Docker Configuration

### Services
- **caddy-dev**: Custom Caddy server with plugins
- **api-backend**: FastAPI application server
- **postgres-dev**: PostgreSQL database
- **redis-dev**: Redis cache
- **dev-tools**: Development utilities

### Docker Commands
```bash
# Start all services
docker-compose -f docker-compose.caddy.yml up -d

# View logs
docker-compose -f docker-compose.caddy.yml logs -f caddy-dev

# Restart service
docker-compose -f docker-compose.caddy.yml restart api-backend

# Get shell access
docker-compose -f docker-compose.caddy.yml exec dev-tools sh
```

## 📊 Monitoring & Debugging

### Access Logs
```bash
# Real-time logs
tail -f logs/access.log

# API logs
tail -f logs/api.log

# Metrics logs
tail -f logs/metrics.log
```

### Development Dashboard
Visit http://localhost:9090 for:
- Service status monitoring
- Real-time metrics
- Quick navigation links
- System health overview
- Log aggregation

### Debug Mode
The development configuration includes:
- Detailed error messages
- Request/response logging
- Performance metrics
- Health check endpoints

## 🔐 Security Features

### Development Security
- Basic authentication for admin endpoints
- CORS configuration for local development
- Rate limiting for API endpoints
- Security headers (XSS, CSRF protection)

### Authentication
Default credentials for development:
- Username: `admin`
- Password: `admin123`

## ⚡ Performance Optimization

### Caching Strategy
- Static assets cached with appropriate headers
- API responses with no-cache during development
- Compression for text-based content
- Browser caching for static resources

### Compression
- Gzip compression for all text content
- Zstd compression for modern browsers
- Asset optimization for faster loading

## 🚦 Health Checks

### Automated Monitoring
- Backend API health checks every 30 seconds
- Database connection monitoring
- Redis connectivity checks
- Custom health endpoints

### Manual Health Check
```bash
# Test all endpoints
curl http://localhost:8080/health
curl http://localhost:8000/health
curl http://localhost:9090/status
```

## 🔄 Hot Reloading

### File Watching
- Frontend files: Automatic browser refresh
- Backend files: Uvicorn auto-reload
- Caddy config: Manual restart required

### Development Workflow
1. Edit files in `web/` or `api/`
2. Changes automatically detected
3. Services restart as needed
4. Browser refreshes automatically

## 📚 Advanced Configuration

### Custom Sites
Add additional sites in `sites/` directory:
```caddy
# sites/additional.caddy
subdomain.localhost:8080 {
    reverse_proxy localhost:8001
}
```

### Environment Variables
```bash
# Set in your shell or .env file
export CADDY_ADMIN=off
export ENV=development
export DEBUG=true
```

### SSL/TLS Development
For HTTPS development:
```caddy
https://localhost:8443 {
    tls internal
    # ... rest of configuration
}
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
lsof -i :8080
kill -9 <PID>
```

**Caddy Won't Start**
```bash
# Check configuration syntax
./caddy validate --config Caddyfile

# Run with verbose logging
./caddy run --config Caddyfile --adapter caddyfile --debug
```

**Backend Connection Failed**
```bash
# Check if FastAPI is running
curl http://localhost:8000/health

# Check Python dependencies
python3 -c "import fastapi, uvicorn"
```

### Debug Commands
```bash
# Test Caddy configuration
./caddy validate --config Caddyfile

# Check plugin list
./caddy list-modules

# Show version info
./caddy version

# Test HTTP endpoints
curl -v http://localhost:8080/health
```

## 📖 Additional Resources

- [Caddy Documentation](https://caddyserver.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [OpenDiscourse Project Documentation](./docs/)

## 🤝 Contributing

When adding new features:
1. Update the Caddyfile configuration
2. Add appropriate health checks
3. Update documentation
4. Test with both local and Docker setups
5. Add logging for debugging

---

**Happy Development!** 🎉

For questions or issues, check the logs or open an issue in the project repository.
