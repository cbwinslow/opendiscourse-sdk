import { ApiResponse } from '@/types';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        success: true,
        data,
        requestId: response.headers.get('x-request-id') || undefined,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'REQUEST_FAILED',
          message: error instanceof Error ? error.message : 'Unknown error',
          details: error,
        },
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // Specialized methods for OpenDiscourse API
  async ragQuery(query: string, filters?: Record<string, unknown>) {
    return this.post('/rag', { question: query, filters });
  }

  async searchDocuments(query: string, options?: {
    maxResults?: number;
    threshold?: number;
    filters?: Record<string, unknown>;
  }) {
    return this.post('/documents/search', { query, ...options });
  }

  async uploadDocument(file: File, metadata?: Record<string, unknown>) {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    return this.request('/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  async getDocuments(page = 1, limit = 20) {
    return this.get(`/documents?page=${page}&limit=${limit}`);
  }

  async getDocument(id: string) {
    return this.get(`/documents/${id}`);
  }

  auth() {
    return {
      login: (username: string, password: string) =>
        this.post('/auth/login', { username, password }),
      
      logout: () => this.get('/auth/logout'),
      
      whoami: () => this.get('/auth/whoami'),
    };
  }

  analytics() {
    return {
      track: (event: string, metadata?: Record<string, unknown>) =>
        this.post('/track', { event, path: window.location.pathname, ...metadata }),
      
      getStats: () => this.get('/analytics/stats'),
    };
  }
}

export const apiClient = new ApiClient();
export default ApiClient;