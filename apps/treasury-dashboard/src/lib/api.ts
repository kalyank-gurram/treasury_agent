import axios, { AxiosInstance, AxiosResponse } from 'axios';
import Cookies from 'js-cookie';
import { 
  User, 
  LoginRequest, 
  LoginResponse, 
  AnalyticsData, 
  PaymentTransaction, 
  ChatMessage, 
  ForecastData,
  ApiError 
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(this.handleApiError(error));
      }
    );
  }

  private handleApiError(error: any): ApiError {
    if (error.response?.data) {
      return {
        error: error.response.data.error || 'API Error',
        message: error.response.data.message || 'An unexpected error occurred',
        details: error.response.data.details,
      };
    }
    return {
      error: 'Network Error',
      message: 'Unable to connect to the server',
    };
  }

  // Token management
  setToken(token: string): void {
    Cookies.set('treasury_token', token, { 
      expires: 1, // 1 day
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });
  }

  getToken(): string | null {
    return Cookies.get('treasury_token') || null;
  }

  clearToken(): void {
    Cookies.remove('treasury_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response: AxiosResponse<LoginResponse> = await this.client.post('/auth/login', credentials);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<User> = await this.client.get('/auth/me');
    return response.data;
  }

  // Analytics endpoints
  async getAnalytics(): Promise<AnalyticsData> {
    const response: AxiosResponse<AnalyticsData> = await this.client.get('/analytics/summary');
    return response.data;
  }

  async getForecast(days: number = 30): Promise<ForecastData[]> {
    const response: AxiosResponse<ForecastData[]> = await this.client.get(`/analytics/forecast?days=${days}`);
    return response.data;
  }

  // Payment endpoints
  async getPayments(): Promise<PaymentTransaction[]> {
    const response: AxiosResponse<PaymentTransaction[]> = await this.client.get('/payments');
    return response.data;
  }

  async approvePayment(paymentId: string): Promise<void> {
    await this.client.post(`/payments/${paymentId}/approve`);
  }

  async rejectPayment(paymentId: string, reason: string): Promise<void> {
    await this.client.post(`/payments/${paymentId}/reject`, { reason });
  }

  // Chat endpoints
  async sendMessage(message: string): Promise<ChatMessage> {
    const response: AxiosResponse<ChatMessage> = await this.client.post('/chat/message', {
      message,
      conversation_id: 'default'
    });
    return response.data;
  }

  async getChatHistory(): Promise<ChatMessage[]> {
    const response: AxiosResponse<any> = await this.client.get('/chat/history');
    // Backend returns { messages: [...] }
    const raw = response.data?.messages ?? response.data ?? [];
    return Array.isArray(raw) ? raw : [];
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;