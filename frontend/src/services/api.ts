const API_BASE_URL = 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  username: string;
  password: string;
}

export interface Website {
  id: number;
  url: string;
  title: string;
  scraped_content: string;
  word_count: number;
  grammar_score?: number;
  improvement_suggestions?: string;
  analysis_result?: string;
  created_at: string;
  user_id: number;
}

class ApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }


  async login(loginData: LoginData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(loginData),
    });

    return this.handleResponse<AuthResponse>(response);
  }

  async signup(signupData: SignupData): Promise<User> {
    const response = await fetch(`${this.baseURL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(signupData),
    });

    return this.handleResponse<User>(response);
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${this.baseURL}/auth/me`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<User>(response);
  }

 
  async scrapeWebsite(url: string): Promise<Website> {
    const response = await fetch(`${this.baseURL}/scraper/scrape?url=${encodeURIComponent(url)}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<Website>(response);
  }

  async getUserWebsites(): Promise<Website[]> {
    const response = await fetch(`${this.baseURL}/scraper/websites`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<Website[]>(response);
  }

  async analyzeWebsite(websiteId: number): Promise<Website> {
    const response = await fetch(`${this.baseURL}/ai/analyze/${websiteId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<Website>(response);
  }


  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }


  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }


  storeAuthData(authResponse: AuthResponse): void {
    localStorage.setItem('access_token', authResponse.access_token);
    localStorage.setItem('user', JSON.stringify(authResponse.user));
  }

  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }
}

export const apiService = new ApiService();