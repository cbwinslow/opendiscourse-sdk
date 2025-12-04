/**
 * ================================================================================
 * File: jest.setup.js
 * Author: OpenDiscourse Contributors
 * Created: 2025-12-04
 * Last Modified: 2025-12-04
 * Version: 1.0.0
 *
 * Description:
 *     Jest setup configuration for OpenDiscourse Next.js application.
 *     Sets up test environment, mocks, and global test utilities.
 *
 * ================================================================================
 */

import '@testing-library/jest-dom';
import 'jest-environment-jsdom';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: '',
      asPath: '',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    };
  },
}));

// Mock Next.js auth context
jest.mock('next-auth/react', () => ({
  useSession: () => ({
    data: {
      user: {
        name: 'Test User',
        email: 'test@example.com',
        image: null,
      },
    },
    status: 'authenticated',
  }),
  signIn: jest.fn(),
  signOut: jest.fn(),
}));

// Mock fetch globally
global.fetch = jest.fn();

// Mock console methods to reduce noise in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    // Suppress React warnings and errors in tests
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning:') ||
       args[0].includes('Error:') ||
       args[0].includes('ReactDOM.render is no longer supported'))
    ) {
      return;
    }
    originalConsoleError(...args);
  };

  console.warn = (...args) => {
    // Suppress development warnings in tests
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning:') ||
       args[0].includes('Warning: useLayoutEffect does nothing on the server'))
    ) {
      return;
    }
    originalConsoleWarn(...args);
  };
});

afterAll(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

// Clean up all mocks after each test
afterEach(() => {
  jest.clearAllMocks();
});

// Mock environment variables for testing
process.env.NODE_ENV = 'test';
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:3000/api';
process.env.NEXTAUTH_SECRET = 'test-secret';
process.env.NEXTAUTH_URL = 'http://localhost:3000';

// Mock ResizeObserver (not available in test environment)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver (not available in test environment)
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock window.matchMedia (not available in test environment)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window.HTMLMediaElement methods
HTMLMediaElement.prototype.play = jest.fn();
HTMLMediaElement.prototype.pause = jest.fn();
HTMLMediaElement.prototype.load = jest.fn();

// Mock crypto.randomUUID if not available
if (!global.crypto.randomUUID) {
  global.crypto.randomUUID = jest.fn(() => '12345678-1234-5678-9abc-123456789abc');
}

// Mock Date.now for consistent test results
const mockNow = new Date('2024-01-15T12:00:00Z');
jest.spyOn(Date, 'now').mockImplementation(() => mockNow.getTime());

// Global test utilities
global.testUtils = {
  // Create mock file for testing
  createMockFile: (name, size, type) => {
    const file = new File(['mock content'], name, { type });
    Object.defineProperty(file, 'size', { value: size });
    return file;
  },

  // Create mock API response
  createMockApiResponse: (data, status = 200) => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  }),

  // Create mock session data
  createMockSession: (overrides = {}) => ({
    user: {
      name: 'Test User',
      email: 'test@example.com',
      image: null,
      ...overrides.user,
    },
    expires: '2024-12-31T23:59:59Z',
    ...overrides,
  }),

  // Create mock document data
  createMockDocument: (overrides = {}) => ({
    id: '123e4567-e89b-12d3-a456-426614174000',
    title: 'Test Document',
    content: 'This is test document content.',
    type: 'bill',
    source: 'congress.gov',
    createdAt: '2024-01-15T12:00:00Z',
    updatedAt: '2024-01-15T12:00:00Z',
    metadata: {
      congress: 118,
      billType: 'HR',
      billNumber: '123',
    },
    ...overrides,
  }),

  // Create mock search results
  createMockSearchResults: (count = 10) => ({
    results: Array.from({ length: count }, (_, i) => ({
      id: `result-${i + 1}`,
      title: `Search Result ${i + 1}`,
      snippet: `This is a snippet for result ${i + 1}...`,
      relevanceScore: 0.9 - (i * 0.05),
      source: ['congress.gov', 'openstates.org', 'govinfo.gov'][i % 3],
      type: ['bill', 'member', 'document'][i % 3],
      url: `https://example.com/result/${i + 1}`,
      metadata: {
        congress: 118 - (i % 5),
        state: ['CA', 'TX', 'NY', 'FL'][i % 4],
        party: ['D', 'R', 'I'][i % 3],
      },
    })),
    totalResults: count,
    searchTime: 0.25,
    query: 'test query',
    facets: {
      type: { bill: 5, member: 3, document: 2 },
      source: { 'congress.gov': 4, 'openstates.org': 3, 'govinfo.gov': 3 },
      congress: { 118: 3, 117: 3, 116: 2, 115: 2 },
    },
  }),

  // Wait for async operations in tests
  waitFor: (callback, options = {}) => {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Timeout waiting for condition'));
      }, options.timeout || 5000);

      const check = () => {
        try {
          callback();
          clearTimeout(timeout);
          resolve();
        } catch (error) {
          // Continue checking
        }
      };

      // Check immediately
      check();

      // Check periodically
      const interval = setInterval(check, 100);

      // Clean up
      setTimeout(() => {
        clearInterval(interval);
        clearTimeout(timeout);
        try {
          callback();
          resolve();
        } catch (error) {
          reject(error);
        }
      }, options.timeout || 5000);
    });
  },

  // Mock geolocation API
  mockGeolocation: () => {
    global.navigator.geolocation = {
      getCurrentPosition: jest.fn((success) => {
        success({
          coords: {
            latitude: 40.7128,
            longitude: -74.0060,
          },
        });
      }),
      watchPosition: jest.fn(),
      clearWatch: jest.fn(),
    };
  },

  // Mock clipboard API
  mockClipboard: () => {
    global.navigator.clipboard = {
      writeText: jest.fn(() => Promise.resolve()),
      readText: jest.fn(() => Promise.resolve('mock clipboard text')),
    };
  },
};

// Custom matchers for Jest
expect.extend({
  toBeValidEmail(received) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const pass = emailRegex.test(received);

    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid email`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid email`,
        pass: false,
      };
    }
  },

  toBeValidDate(received) {
    const pass = !isNaN(Date.parse(received));

    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid date`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid date`,
        pass: false,
      };
    }
  },

  toHaveFileSize(received, expected) {
    const pass = received.size === expected;

    if (pass) {
      return {
        message: () => `expected file size ${received.size} not to equal ${expected}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected file size ${received.size} to equal ${expected}`,
        pass: false,
      };
    }
  },

  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;

    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },
});

export default function setupTests() {
  // Additional setup can be added here
  console.log('🧪 Jest test environment initialized');
}
