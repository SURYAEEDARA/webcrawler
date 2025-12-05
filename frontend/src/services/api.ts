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

export interface AuditSummary {
  website_id: number;
  total_pages: number;
  broken_links_count: number;
  image_issues_count: number;
  average_grammar_score?: number;
  overall_health_score?: number;
  seo_score?: number;
  accessibility_score?: number;
}

export interface WebPage {
  id: number;
  url: string;
  title?: string;
  scraped_content?: string;
  word_count?: number;
  grammar_score?: number;
  improvement_suggestions?: string;
  analysis_result?: string;
  status_code?: number;
  load_time?: number;
  created_at: string;
  website_id?: number;
}

export interface Website {
  id: number;
  base_url: string;
  title?: string;
  created_at: string;
  user_id: number;
  page_count?: number;
  pages?: WebPage[];
  page?: WebPage;
}

export interface CrawledWebsite {
  id: number;
  base_url: string;
  title?: string;
  created_at: string;
  user_id: number;
  page_count: number;
  pages: WebPage[];
}

interface ExportWebsiteResponse {
  id?: number;
  base_url?: string;
  title?: string;
  created_at?: string;
  user_id?: number;
}

interface ExportPageResponse {
  id: number;
  url: string;
  title?: string;
  scraped_content?: string;
  content_preview?: string;
  word_count?: number;
  character_count?: number;
  status_code?: number;
  load_time?: number;
  created_at: string;
  grammar_score?: number;
  analysis_result?: string;
  improvement_suggestions?: string;
  has_analysis?: boolean;
  analysis_timestamp?: string;
  content_metrics?: {
    readability_score?: number;
    keyword_density?: Record<string, number>;
    content_categories?: string[];
  };
}

interface ExportAuditSummary {
  website_id?: number;
  total_pages?: number;
  broken_links_count?: number;
  image_issues_count?: number;
  average_grammar_score?: number;
  overall_health_score?: number;
  seo_score?: number;
  accessibility_score?: number;
}

interface ExportJSONResponse {
  export_date: string;
  export_type: string;
  website: ExportWebsiteResponse;
  audit_summary: ExportAuditSummary;
  analysis_metadata: {
    total_pages_exported: number;
    analyzed_pages_count: number;
    export_format_version: string;
    includes_full_content: boolean;
    includes_ai_analysis: boolean;
  };
  pages: ExportPageResponse[];
  export_settings: {
    include_full_content: boolean;
    include_ai_analysis: boolean;
    include_technical_metrics: boolean;
    timestamp: string;
  };
}

interface ExportReportResponse {
  report: string;
  website?: ExportWebsiteResponse;
}

interface UserLogsResponse {
  success: boolean;
  logs: Array<{
    id: number;
    action: string;
    message: string;
    timestamp: string;
    level: string;
    url?: string;
  }>;
  total: number;
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginData),
    });
    return this.handleResponse<AuthResponse>(response);
  }

  async signup(signupData: SignupData): Promise<User> {
    const response = await fetch(`${this.baseURL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

  async scrapeWebsite(url: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/scraper/scrape?url=${encodeURIComponent(url)}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async analyzeText(text: string): Promise<{
    text_preview: string;
    grammar_score: number;
    analysis: string;
    success: boolean;
  }> {
    const response = await fetch(`${this.baseURL}/ai/analyze/text`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ text }),
    });
    return this.handleResponse<any>(response);
  }

  async analyzeWebsiteByUrl(url: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/ai/analyze/url`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ url }),
    });
    return this.handleResponse<any>(response);
  }

  async getCrawledWebsites(): Promise<CrawledWebsite[]> {
    const response = await fetch(`${this.baseURL}/crawl/websites`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<CrawledWebsite[]>(response);
  }

  async getWebsiteWithPages(websiteId: number): Promise<any> {
    const response = await fetch(`${this.baseURL}/scraper/websites/${websiteId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getUserWebsites(): Promise<Website[]> {
    const response = await fetch(`${this.baseURL}/scraper/websites`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    const websites = await this.handleResponse<Website[]>(response);
    
    const websitesWithPages = await Promise.all(
      websites.map(async (website: Website) => {
        try {
          const pages = await this.getWebsitePages(website.id);
          if (pages.length > 0) {
            return {
              ...website,
              page: pages[0] 
            };
          }
        } catch (error) {
          console.log(`Could not get pages for website ${website.id}:`, error);
        }
        return website;
      })
    );
    
    return websitesWithPages;
  }

  async getWebsitePages(websiteId: number): Promise<WebPage[]> {
    const response = await fetch(`${this.baseURL}/crawl/websites/${websiteId}/pages`, {
      method: 'GET', 
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<WebPage[]>(response);
  }

  async crawlWebsiteRecursive(crawlData: { base_url: string; max_pages: number }): Promise<any> {
    const response = await fetch(`${this.baseURL}/crawl/website`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(crawlData),
    });
    return this.handleResponse<any>(response);
  }

  async analyzePage(pageId: number): Promise<{
    page_id: number;
    grammar_score: number;
    analysis_preview: string;
    success: boolean;
  }> {
    const response = await fetch(`${this.baseURL}/ai/analyze/page/${pageId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async analyzeWebsite(websiteId: number): Promise<{
    website_id: number;
    total_pages: number;
    successfully_analyzed: number;
    failed_analysis: number;
    results: any[];
  }> {
    const response = await fetch(`${this.baseURL}/ai/analyze/website/${websiteId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getFullAnalysis(pageId: number): Promise<{
    page_id: number;
    url: string;
    grammar_score: number;
    full_analysis: string;
    suggestions: string;
    analyzed_at: string;
  }> {
    const response = await fetch(`${this.baseURL}/ai/analysis/full/${pageId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  // FIXED: Add the missing getAuditReport method
  async getAuditReport(websiteId: number): Promise<AuditSummary> {
    const response = await fetch(`${this.baseURL}/analysis/audit/${websiteId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<AuditSummary>(response);
  }

  async exportWebsiteJSON(websiteId: number): Promise<ExportJSONResponse> {
    const response = await fetch(`${this.baseURL}/export/website/${websiteId}/json`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<ExportJSONResponse>(response);
  }

  async exportWebsiteReport(websiteId: number): Promise<ExportReportResponse> {
    const response = await fetch(`${this.baseURL}/export/website/${websiteId}/report`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<ExportReportResponse>(response);
  }

  async getDashboardData(): Promise<any> {
    const response = await fetch(`${this.baseURL}/dashboard/`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getUserLogs(limit: number = 50): Promise<UserLogsResponse> {
    const response = await fetch(`${this.baseURL}/logs/my-logs?limit=${limit}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<UserLogsResponse>(response);
  }

  async regenerateAuditReport(websiteId: number): Promise<AuditSummary> {
  const response = await fetch(`${this.baseURL}/analysis/audit/${websiteId}/regenerate`, {
    method: 'POST',
    headers: this.getAuthHeaders(),
  });
  return this.handleResponse<AuditSummary>(response);
}
}

export const apiService = new ApiService();