import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('api_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API Functions
export const documentApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  list: (params?: any) => api.get('/documents', { params }),
  
  get: (id: string) => api.get(`/documents/${id}`),
  
  delete: (id: string) => api.delete(`/documents/${id}`),
  
  analyze: (id: string) => api.post(`/documents/${id}/analyze`),
};

export const searchApi = {
  semantic: (query: string, limit = 10) => 
    api.post('/search/semantic', { query, limit }),
    
  vector: (embedding: number[], limit = 10) =>
    api.post('/search/vector', { embedding, limit }),
};

export const ragApi = {
  query: (question: string, context?: string[]) =>
    api.post('/rag/query', { question, context }),
    
  history: () => api.get('/rag/history'),
};

export const govDataApi = {
  ingest: (source: string, filters?: any) =>
    api.post('/govdata/ingest', { source, filters }),
    
  sources: () => api.get('/govdata/sources'),
  
  scrape: (url: string) => api.post('/govdata/scrape', { url }),
};