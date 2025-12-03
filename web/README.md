# OpenDiscourse Web Application

## Enterprise-Grade Political Document Analysis Platform

This is a Next.js 14 application that provides a comprehensive platform for government document analysis and retrieval with AI-powered semantic search, NLP processing, and comprehensive political data management.

## 🚀 Features

### Modern Next.js 14 Architecture
- **App Router**: Latest Next.js routing system with server components
- **TypeScript**: Full type safety across the application
- **Tailwind CSS**: Modern, responsive UI with dark mode support
- **Enterprise Security**: CSP headers, middleware protection, and rate limiting

### Political Document Analysis
- **Semantic Search**: AI-powered search across government documents
- **RAG Interface**: Query documents using retrieval-augmented generation
- **Document Management**: Upload, organize, and analyze political documents
- **Entity Recognition**: Extract and analyze political entities and relationships

### Authentication & Security
- **JWT Authentication**: Secure token-based authentication
- **Middleware Protection**: Route-level security and rate limiting
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Security Headers**: Enterprise-grade security headers

### API Integration
- **RESTful APIs**: Full REST API for document management
- **Authentication APIs**: Login, logout, and user management
- **RAG Endpoints**: AI-powered query processing
- **Document Search**: Advanced search with filtering capabilities

## 🛠️ Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Radix UI components
- **Authentication**: JWT with HTTP-only cookies
- **Database**: Supabase (PostgreSQL with pgvector)
- **Vector Search**: Multiple vector database support (Qdrant, Weaviate, ChromaDB)
- **State Management**: React Context + hooks
- **Testing**: Jest + Playwright for E2E testing
- **Package Manager**: pnpm

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- pnpm
- Docker (for local services)

### Installation

1. **Install dependencies**:
   ```bash
   pnpm install
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Start development server**:
   ```bash
   pnpm dev
   ```

4. **Build for production**:
   ```bash
   pnpm build
   pnpm start
   ```

### Development Scripts

```bash
# Development server
pnpm dev

# Build application
pnpm build

# Start production server
pnpm start

# Run linting
pnpm lint
pnpm lint:fix

# Type checking
pnpm type-check

# Run tests
pnpm test
pnpm test:watch
pnpm test:coverage

# End-to-end testing
pnpm test:e2e

# Bundle analysis
pnpm analyze
```

## 📁 Project Structure

```
web/
├── src/
│   ├── app/                 # Next.js 14 App Router
│   │   ├── api/            # API routes
│   │   ├── chat/           # RAG chat interface
│   │   ├── documents/      # Document management
│   │   ├── search/         # Search interface
│   │   ├── layout.tsx      # Root layout
│   │   └── page.tsx        # Homepage
│   ├── components/         # React components
│   │   ├── dashboard/      # Dashboard components
│   │   └── ui/            # Reusable UI components
│   ├── contexts/          # React contexts
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility libraries
│   ├── styles/            # Global styles
│   ├── types/             # TypeScript types
│   └── utils/             # Utility functions
├── public/                # Static assets
├── .env.example          # Environment variables template
├── .env.local            # Local environment variables
├── next.config.js        # Next.js configuration
├── tailwind.config.js    # Tailwind CSS configuration
├── tsconfig.json         # TypeScript configuration
└── package.json          # Dependencies and scripts
```

## 🔧 Configuration

### Environment Variables

Key environment variables for configuration:

```bash
# Application
NEXT_PUBLIC_APP_NAME=OpenDiscourse
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Authentication
JWT_SECRET=your-jwt-secret
AUTH_COOKIE_NAME=opendiscourse-token

# Database
DATABASE_URL=postgresql://...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Vector Databases
QDRANT_URL=http://localhost:6333
WEAVIATE_URL=http://localhost:8080
CHROMADB_URL=http://localhost:8000

# External APIs
GOVINFO_API_KEY=your-govinfo-api-key
CONGRESS_API_KEY=your-congress-api-key

# Security
RATE_LIMIT_MAX=100
CORS_ORIGINS=http://localhost:3000
```

### Tailwind CSS

The application uses a custom Tailwind configuration with:
- Custom color palette for government/political themes
- Dark mode support
- Custom animations and utilities
- Responsive design system

### TypeScript

Strict TypeScript configuration with:
- Path mapping for clean imports
- Comprehensive type definitions
- ESLint integration
- Build-time type checking

## 🔒 Security Features

### Authentication
- JWT-based authentication with HTTP-only cookies
- Protected routes with middleware
- Automatic token refresh
- Secure logout functionality

### Security Headers
- Content Security Policy (CSP)
- CORS configuration
- Rate limiting middleware
- XSS protection headers

### API Security
- Input validation and sanitization
- Error handling without information leakage
- Request size limits
- API rate limiting

## 🎨 UI Components

The application uses a comprehensive design system built on:

### Base Components
- Button variants (primary, secondary, outline, ghost)
- Card layouts with consistent spacing
- Form inputs with validation states
- Loading states and spinners

### Dashboard Components
- Header with navigation and user controls
- Statistics cards with trend indicators
- Feature grid with action buttons
- Recent activity feeds
- System status monitoring

### Data Components
- Document cards with metadata
- Search interfaces with filters
- Pagination controls
- Data tables with sorting

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/logout` - User logout
- `GET /api/auth/whoami` - Get current user

### Documents
- `GET /api/documents` - List documents with pagination
- `POST /api/documents/search` - Search documents
- `POST /api/documents/upload` - Upload documents

### RAG Interface
- `POST /api/rag` - Process RAG queries

### Analytics
- `POST /api/track` - Track user events
- `GET /api/analytics/stats` - Get analytics data

## 🧪 Testing

### Unit Testing
- Jest configuration for component testing
- React Testing Library for UI testing
- Mock implementations for external services

### End-to-End Testing
- Playwright configuration for E2E tests
- Automated testing workflows
- Visual regression testing

### Testing Commands
```bash
# Unit tests
pnpm test
pnpm test:watch
pnpm test:coverage

# E2E tests
pnpm test:e2e
```

## 🚀 Deployment

### Production Build
```bash
pnpm build
pnpm start
```

### Docker Deployment
The application can be containerized and deployed with Docker:
```bash
docker build -t opendiscourse-web .
docker run -p 3000:3000 opendiscourse-web
```

### Environment Setup
1. Set up production environment variables
2. Configure database connections
3. Set up vector database services
4. Configure external API access
5. Set up monitoring and logging

## 📊 Performance

### Optimization Features
- Static generation where possible
- Image optimization with Next.js
- Bundle splitting and code optimization
- Lazy loading for improved performance

### Monitoring
- Built-in analytics tracking
- Performance monitoring
- Error boundary implementation
- Real-time status monitoring

## 🤝 Contributing

1. Follow the established TypeScript and React patterns
2. Use the existing component library and design system
3. Write tests for new features
4. Follow the conventional commit format
5. Update documentation for new features

## 📄 License

This project is part of the OpenDiscourse platform for political document analysis.