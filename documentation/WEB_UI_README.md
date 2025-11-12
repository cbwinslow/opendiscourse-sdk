# OpenDiscourse Enterprise Web Interface

A modern, enterprise-grade web interface for government document analysis and retrieval using AI-powered RAG (Retrieval-Augmented Generation) technology.

## 🚀 Features

### Modern UI/UX Design
- **Enterprise-grade interface** with professional aesthetics
- **Responsive design** that works on all devices
- **Accessibility features** with proper ARIA labels and keyboard navigation
- **Consistent design system** with branded components

### Advanced RAG Interface
- **Chat-style conversation** interface with message bubbles
- **Real-time loading states** and progress indicators
- **Source document citations** with evidence display
- **Example queries** to guide users
- **Comprehensive error handling** with user-friendly messages

### Robust Architecture
- **TypeScript** for type safety and better developer experience
- **React 18** with functional components and hooks
- **Modular component structure** with proper separation of concerns
- **Context-based state management** for authentication
- **Reusable hooks** for common functionality

### Security & Authentication
- **Enterprise authentication** context with session management
- **Role-based access control** (admin, user, analyst)
- **AuthGuard** components for protected routes
- **Demo mode** for easy testing and onboarding

### Performance & Development
- **Vite build system** for fast development and optimized builds
- **Hot module replacement** for instant feedback
- **TypeScript support** with comprehensive type definitions
- **Tailwind CSS** for utility-first styling
- **Comprehensive linting** and code quality tools

## 🛠️ Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Build Tool**: Vite for fast development and builds
- **State Management**: React Context API
- **HTTP Client**: Custom API client with error handling
- **Development**: Hot reload, TypeScript checking, ESLint

## 📦 Installation & Setup

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```

## 🏗️ Architecture

### Component Structure
```
web/src/
├── components/           # Reusable UI components
│   ├── Auth.tsx         # Authentication components
│   ├── Layout.tsx       # Layout components (Layout, Card, PageHeader)
│   ├── LoadingComponents.tsx # Loading states and spinners
│   ├── RAGInterface.tsx # Advanced RAG chat interface
│   ├── DocumentViewer.tsx # Document browsing and search
│   └── Sidebar.tsx      # Navigation sidebar
├── contexts/            # React contexts
│   └── AuthContext.tsx  # Authentication state management
├── hooks/               # Custom React hooks
│   ├── useAnalytics.ts  # Analytics tracking
│   └── useLoadingState.ts # Loading state management
├── types/               # TypeScript type definitions
│   └── index.ts         # Core type definitions
├── utils/               # Utility functions
│   └── api.ts           # API client with error handling
└── main.css            # Global styles and Tailwind setup
```

### API Integration
The frontend integrates with the existing Python LangChain RAG service through a well-defined API layer:

- **RAG Queries**: Real-time question answering with source citations
- **Document Management**: Upload, search, and browse documents
- **Authentication**: Session-based authentication with role management
- **Analytics**: Event tracking and usage monitoring

## 🎨 Design System

### Color Palette
- **Primary**: Blue tones (#3b82f6, #2563eb, #1d4ed8)
- **Secondary**: Neutral grays (#64748b, #475569, #334155)
- **Success**: Green (#10b981)
- **Warning**: Orange (#f59e0b)
- **Error**: Red (#ef4444)

### Typography
- **Primary Font**: Inter (modern, readable sans-serif)
- **Monospace**: JetBrains Mono (for code and technical content)

### Components
All components follow enterprise design patterns:
- Consistent spacing and sizing
- Proper focus states and accessibility
- Loading states and error handling
- Responsive design principles

## 🔐 Security Features

### Authentication
- **Session-based authentication** with secure cookie handling
- **Role-based access control** (admin, user, analyst)
- **Demo mode** for testing and onboarding
- **Secure logout** with session cleanup

### Input Validation
- **Client-side validation** for forms and inputs
- **XSS protection** through proper escaping
- **CSRF protection** through secure headers
- **Input sanitization** for user-generated content

## 📊 Analytics & Monitoring

### Event Tracking
The interface includes comprehensive analytics tracking:
- Page views and navigation patterns
- RAG query performance and success rates
- Document interaction and search behavior
- User authentication and session management
- Error rates and performance metrics

### System Monitoring
- Real-time system status indicators
- Service health monitoring
- Performance metrics dashboard
- Usage statistics and trends

## 🌟 Enterprise Features

### User Experience
- **Dashboard** with key metrics and quick actions
- **Recent activity** feeds and notifications
- **System status** monitoring with uptime tracking
- **Quick actions** for common tasks

### Administration
- **User management** with role assignments
- **System configuration** and settings
- **Analytics dashboard** with detailed insights
- **Document management** with batch operations

### Integration
- **LangChain RAG service** integration with comprehensive error handling
- **Vector database** connectivity for semantic search
- **Document processing** pipeline integration
- **External API** compatibility and webhook support

## 📈 Performance Optimization

### Build Optimization
- **Code splitting** for optimal bundle sizes
- **Tree shaking** to eliminate unused code
- **Asset optimization** with compression
- **Caching strategies** for static assets

### Runtime Performance
- **Lazy loading** for heavy components
- **Memoization** for expensive computations
- **Virtual scrolling** for large lists
- **Debounced search** to reduce API calls

## 🧪 Testing & Quality

### Code Quality
- **TypeScript** for compile-time error detection
- **ESLint** with enterprise-grade rules
- **Prettier** for consistent code formatting
- **Git hooks** for pre-commit validation

### Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive design
- Progressive enhancement principles
- Graceful degradation for older browsers

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Environment Configuration
The application supports multiple environment configurations:
- **Development**: Hot reload, debug logging, mock data
- **Staging**: Production-like environment for testing
- **Production**: Optimized builds, error tracking, analytics

### Docker Support
```dockerfile
# Example Dockerfile for containerized deployment
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
EXPOSE 3000
CMD ["npm", "start"]
```

## 📚 API Documentation

### Core Endpoints
- `POST /api/rag` - RAG query with question and filters
- `GET /api/documents` - Paginated document listing
- `POST /api/documents/search` - Document search with filters
- `POST /api/documents/upload` - Document upload with metadata
- `GET /api/auth/whoami` - Current user information
- `POST /api/auth/login` - User authentication
- `GET /api/auth/logout` - Session termination

### Response Format
All API responses follow a consistent format:
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  requestId?: string;
}
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with proper TypeScript types
4. Add tests for new functionality
5. Run linting and type checking
6. Submit a pull request

### Code Standards
- Follow TypeScript best practices
- Use functional components with hooks
- Implement proper error boundaries
- Include comprehensive JSDoc comments
- Follow the established design system

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangChain** for RAG implementation patterns and documentation
- **React** and **TypeScript** communities for excellent tooling
- **Tailwind CSS** for the utility-first CSS framework
- **Vite** for the fast development environment

---

For more information about the OpenDiscourse project, see the main [README.md](../README.md) and [PROJECT_PLAN.md](../PROJECT_PLAN.md).