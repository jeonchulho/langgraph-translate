/**
 * API client for translation service
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

export interface TranslateRequest {
  text: string;
}

export interface TranslateResponse {
  original: string;
  detected_language: string;
  translation: string;
  quality_score: number;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface StatsResponse {
  cache_stats: {
    hits: number;
    misses: number;
    total_requests: number;
    hit_rate_percent: number;
    connected: boolean;
  };
  total_translations: number;
}

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Error interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          // Server responded with error status
          const detail = (error.response.data as any)?.detail || 'An error occurred';
          throw new Error(detail);
        } else if (error.request) {
          // Request was made but no response
          throw new Error('No response from server. Please check your connection.');
        } else {
          // Error setting up request
          throw new Error(error.message);
        }
      }
    );
  }

  async translateText(text: string): Promise<TranslateResponse> {
    const response = await this.client.post<TranslateResponse>('/translate', { text });
    return response.data;
  }

  async translateDocument(file: File): Promise<Blob> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/translate/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    });

    return response.data;
  }

  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async getStats(): Promise<StatsResponse> {
    const response = await this.client.get<StatsResponse>('/stats');
    return response.data;
  }
}

export const apiClient = new APIClient();

/**
 * WebSocket helper for real-time translation
 */
export class TranslateWebSocket {
  private ws: WebSocket | null = null;
  private url: string;

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${protocol}//${window.location.host}/ws/translate`;
  }

  connect(
    onMessage: (data: TranslateResponse) => void,
    onError: (error: Event) => void
  ): void {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
  }

  send(text: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(text);
    } else {
      console.error('WebSocket is not connected');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
