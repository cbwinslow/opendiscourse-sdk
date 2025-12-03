/**
 * LocalAI Client for OpenDiscourse
 * Provides integration with LocalAI for embeddings and chat completion
 */

interface LocalAIConfig {
  baseURL: string;
  apiKey?: string;
  timeout?: number;
}

interface EmbeddingRequest {
  input: string | string[];
  model?: string;
}

interface EmbeddingResponse {
  data: Array<{
    embedding: number[];
    index: number;
    object: string;
  }>;
  model: string;
  object: string;
  usage: {
    prompt_tokens: number;
    total_tokens: number;
  };
}

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  max_tokens?: number;
  temperature?: number;
  stream?: boolean;
}

interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export class LocalAIClient {
  private config: LocalAIConfig;

  constructor(config?: Partial<LocalAIConfig>) {
    this.config = {
      baseURL: process.env.LOCALAI_URL || 'http://localhost:8080',
      apiKey: process.env.LOCALAI_API_KEY,
      timeout: 30000,
      ...config,
    };
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add custom headers if provided
    if (options.headers) {
      const customHeaders = options.headers as Record<string, string>;
      Object.assign(headers, customHeaders);
    }

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`LocalAI API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('LocalAI request timeout');
      }
      throw error;
    }
  }

  /**
   * Generate embeddings for the given text
   */
  async generateEmbeddings(
    input: string | string[],
    model = 'text-embedding-ada-002'
  ): Promise<EmbeddingResponse> {
    const request: EmbeddingRequest = {
      input,
      model,
    };

    return this.makeRequest<EmbeddingResponse>('/v1/embeddings', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Chat completion with LocalAI
   */
  async chatCompletion(
    messages: ChatMessage[],
    options: Partial<ChatCompletionRequest> = {}
  ): Promise<ChatCompletionResponse> {
    const request: ChatCompletionRequest = {
      model: 'gpt-3.5-turbo', // Default model, can be overridden
      messages,
      max_tokens: 1000,
      temperature: 0.7,
      ...options,
    };

    return this.makeRequest<ChatCompletionResponse>('/v1/chat/completions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Stream chat completion (returns an async generator)
   */
  async *streamChatCompletion(
    messages: ChatMessage[],
    options: Partial<ChatCompletionRequest> = {}
  ): AsyncGenerator<ChatCompletionResponse, void, unknown> {
    const request: ChatCompletionRequest = {
      model: 'gpt-3.5-turbo',
      messages,
      max_tokens: 1000,
      temperature: 0.7,
      stream: true,
      ...options,
    };

    const url = `${this.config.baseURL}/v1/chat/completions`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`LocalAI API error: ${response.status} ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body reader available');
    }

    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim() !== '');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;

            try {
              const parsed = JSON.parse(data) as ChatCompletionResponse;
              yield parsed;
            } catch (error) {
              console.error('Error parsing streaming response:', error);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Check if LocalAI is available
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.makeRequest('/health');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get available models
   */
  async getModels(): Promise<{ data: Array<{ id: string; object: string }> }> {
    return this.makeRequest<{ data: Array<{ id: string; object: string }> }>('/v1/models');
  }
}

// Default client instance
export const localAI = new LocalAIClient();

// RAG-specific functions
export class RAGService {
  private client: LocalAIClient;

  constructor(client: LocalAIClient = localAI) {
    this.client = client;
  }

  /**
   * Generate embeddings for document chunks
   */
  async generateDocumentEmbeddings(text: string): Promise<number[]> {
    const response = await this.client.generateEmbeddings(text);
    return response.data[0]?.embedding || [];
  }

  /**
   * Generate answer based on context and question
   */
  async answerQuestion(
    question: string,
    context: string[],
    systemPrompt?: string
  ): Promise<string> {
    const contextText = context.join('\n\n');
    const defaultSystemPrompt = `You are a helpful assistant that answers questions based on the provided context. 
If the answer cannot be found in the context, say "I don't have enough information to answer that question."

Context:
${contextText}`;

    const messages: ChatMessage[] = [
      { role: 'system', content: systemPrompt || defaultSystemPrompt },
      { role: 'user', content: question },
    ];

    const response = await this.client.chatCompletion(messages);
    return response.choices[0]?.message.content || 'No response generated';
  }

  /**
   * Stream answer generation for real-time responses
   */
  async *streamAnswer(
    question: string,
    context: string[],
    systemPrompt?: string
  ): AsyncGenerator<string, void, unknown> {
    const contextText = context.join('\n\n');
    const defaultSystemPrompt = `You are a helpful assistant that answers questions based on the provided context. 
If the answer cannot be found in the context, say "I don't have enough information to answer that question."

Context:
${contextText}`;

    const messages: ChatMessage[] = [
      { role: 'system', content: systemPrompt || defaultSystemPrompt },
      { role: 'user', content: question },
    ];

    for await (const chunk of this.client.streamChatCompletion(messages)) {
      const content = chunk.choices[0]?.message?.content;
      if (content) {
        yield content;
      }
    }
  }
}

export const ragService = new RAGService();