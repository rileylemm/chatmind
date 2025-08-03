import axios from 'axios';
import type { ApiResponse, PaginatedResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    if (error.response?.status === 500) {
      console.error('Server error:', error.response.data);
    }
    
    return Promise.reject(error);
  }
);

// Generic API functions
export const apiGet = async <T>(url: string): Promise<T> => {
  const response = await api.get<ApiResponse<T>>(url);
  return response.data.data;
};

export const apiPost = async <T>(url: string, data?: unknown): Promise<T> => {
  const response = await api.post<ApiResponse<T>>(url, data);
  return response.data.data;
};

export const apiPut = async <T>(url: string, data?: unknown): Promise<T> => {
  const response = await api.put<ApiResponse<T>>(url, data);
  return response.data.data;
};

export const apiDelete = async <T>(url: string): Promise<T> => {
  const response = await api.delete<ApiResponse<T>>(url);
  return response.data.data;
};

// Paginated response helper
export const apiGetPaginated = async <T>(
  url: string,
  params?: Record<string, string | number>
): Promise<PaginatedResponse<T>> => {
  const response = await api.get<PaginatedResponse<T>>(url, { params });
  return response.data;
};

// Error handling helper
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message || error.message || 'An error occurred';
  }
  return error instanceof Error ? error.message : 'An unknown error occurred';
};

// ============================================================================
// Discovery API Functions
// ============================================================================

export interface DiscoveredTopic {
  topic: string;
  count: number;
  domain: string;
  trend: string;
  related_topics: string[];
}

export interface DiscoveredDomain {
  domain: string;
  count: number;
  percentage: number;
  top_topics: string[];
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export interface DiscoveredCluster {
  cluster_id: number;
  name: string;
  size: number;
  umap_x?: number;
  umap_y?: number;
  summary: string;
  key_points: string[];
  common_tags: string[];
}

export const discoverTopics = async (params?: {
  limit?: number;
  min_count?: number;
  domain?: string;
}): Promise<DiscoveredTopic[]> => {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.min_count) searchParams.append('min_count', params.min_count.toString());
  if (params?.domain) searchParams.append('domain', params.domain);
  
  return apiGet<DiscoveredTopic[]>(`/api/discover/topics?${searchParams.toString()}`);
};

export const discoverDomains = async (): Promise<DiscoveredDomain[]> => {
  return apiGet<DiscoveredDomain[]>('/api/discover/domains');
};

export const discoverClusters = async (params?: {
  limit?: number;
  min_size?: number;
  include_positioning?: boolean;
}): Promise<DiscoveredCluster[]> => {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.min_size) searchParams.append('min_size', params.min_size.toString());
  if (params?.include_positioning !== undefined) {
    searchParams.append('include_positioning', params.include_positioning.toString());
  }
  
  return apiGet<DiscoveredCluster[]>(`/api/discover/clusters?${searchParams.toString()}`);
};

// ============================================================================
// Search API Functions
// ============================================================================

export interface SearchResult {
  id: string;
  content: string;
  role?: string;
  timestamp?: number;
  chat_id?: string;
  tags?: string[];
  similarity_score?: number;
}

export const searchSemantic = async (params: {
  query: string;
  limit?: number;
  min_similarity?: number;
}): Promise<SearchResult[]> => {
  const searchParams = new URLSearchParams();
  searchParams.append('query', params.query);
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.min_similarity) searchParams.append('min_similarity', params.min_similarity.toString());
  
  return apiGet<SearchResult[]>(`/api/search/semantic?${searchParams.toString()}`);
};

export const searchContent = async (params: {
  query: string;
  limit?: number;
  role?: string;
}): Promise<SearchResult[]> => {
  const searchParams = new URLSearchParams();
  searchParams.append('query', params.query);
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.role) searchParams.append('role', params.role);
  
  return apiGet<SearchResult[]>(`/api/search/content?${searchParams.toString()}`);
};

export const searchByTags = async (params: {
  tags: string[];
  limit?: number;
  exact_match?: boolean;
}): Promise<SearchResult[]> => {
  const searchParams = new URLSearchParams();
  searchParams.append('tags', params.tags.join(','));
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.exact_match !== undefined) {
    searchParams.append('exact_match', params.exact_match.toString());
  }
  
  return apiGet<SearchResult[]>(`/api/search/tags?${searchParams.toString()}`);
};

export const advancedSearch = async (params: {
  query: string;
  filters: {
    start_date?: string;
    end_date?: string;
    domain?: string;
    sentiment?: string;
    complexity?: string;
    tags?: string[];
    min_similarity?: number;
    limit?: number;
  };
}): Promise<SearchResult[]> => {
  return apiPost<SearchResult[]>('/api/search/advanced', {
    query: params.query,
    filters: params.filters,
  });
};

// ============================================================================
// Graph Exploration API Functions
// ============================================================================

export interface GraphVisualizationData {
  nodes: Array<{
    id: string;
    type: string;
    properties: Record<string, unknown>;
    position?: { x: number; y: number };
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
    properties?: Record<string, unknown>;
  }>;
}

export const getGraphVisualization = async (params?: {
  node_types?: string[];
  limit?: number;
  include_edges?: boolean;
  filter_domain?: string;
}): Promise<GraphVisualizationData> => {
  const searchParams = new URLSearchParams();
  if (params?.node_types) searchParams.append('node_types', params.node_types.join(','));
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.include_edges !== undefined) {
    searchParams.append('include_edges', params.include_edges.toString());
  }
  if (params?.filter_domain) searchParams.append('filter_domain', params.filter_domain);
  
  return apiGet<GraphVisualizationData>(`/api/graph/visualization?${searchParams.toString()}`);
};

export interface GraphConnection {
  path: string[];
  length: number;
  relationships: string[];
  total_score: number;
}

export interface GraphConnectionsData {
  paths: GraphConnection[];
  summary: {
    total_paths: number;
    average_score: number;
    strongest_connection: number;
  };
}

export const findGraphConnections = async (params: {
  source_id: string;
  target_id?: string;
  max_hops?: number;
  relationship_types?: string[];
}): Promise<GraphConnectionsData> => {
  const searchParams = new URLSearchParams();
  searchParams.append('source_id', params.source_id);
  if (params.target_id) searchParams.append('target_id', params.target_id);
  if (params.max_hops) searchParams.append('max_hops', params.max_hops.toString());
  if (params.relationship_types) {
    searchParams.append('relationship_types', params.relationship_types.join(','));
  }
  
  return apiGet<GraphConnectionsData>(`/api/graph/connections?${searchParams.toString()}`);
};

export interface GraphNeighbor {
  id: string;
  type: string;
  title?: string;
  similarity_score: number;
  relationship_type: string;
}

export interface GraphNeighborsData {
  node: {
    id: string;
    type: string;
    title?: string;
  };
  neighbors: GraphNeighbor[];
  summary: {
    total_neighbors: number;
    average_similarity: number;
    strongest_connection: number;
  };
}

export const getGraphNeighbors = async (params: {
  node_id: string;
  limit?: number;
  min_similarity?: number;
  relationship_type?: string;
}): Promise<GraphNeighborsData> => {
  const searchParams = new URLSearchParams();
  searchParams.append('node_id', params.node_id);
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.min_similarity) searchParams.append('min_similarity', params.min_similarity.toString());
  if (params.relationship_type) searchParams.append('relationship_type', params.relationship_type);
  
  return apiGet<GraphNeighborsData>(`/api/graph/neighbors?${searchParams.toString()}`);
};

// ============================================================================
// Analytics API Functions
// ============================================================================

export interface AnalyticsPatterns {
  conversation_frequency: Array<{
    date: string;
    count: number;
    avg_messages: number;
  }>;
  topic_evolution: Array<{
    topic: string;
    trend: string;
    growth_rate: number;
  }>;
  sentiment_trends: {
    positive: number;
    neutral: number;
    negative: number;
  };
  complexity_distribution: {
    beginner: number;
    intermediate: number;
    advanced: number;
  };
}

export const analyzePatterns = async (params?: {
  timeframe?: string;
  domain?: string;
  include_sentiment?: boolean;
}): Promise<AnalyticsPatterns> => {
  const searchParams = new URLSearchParams();
  if (params?.timeframe) searchParams.append('timeframe', params.timeframe);
  if (params?.domain) searchParams.append('domain', params.domain);
  if (params?.include_sentiment !== undefined) {
    searchParams.append('include_sentiment', params.include_sentiment.toString());
  }
  
  return apiGet<AnalyticsPatterns>(`/api/analytics/patterns?${searchParams.toString()}`);
};

export interface SentimentAnalysis {
  overall_sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
  sentiment_by_domain: Array<{
    domain: string;
    positive: number;
    neutral: number;
    negative: number;
  }>;
  sentiment_timeline: Array<{
    date: string;
    positive: number;
    neutral: number;
    negative: number;
  }>;
}

export const analyzeSentiment = async (params?: {
  start_date?: string;
  end_date?: string;
  group_by?: string;
}): Promise<SentimentAnalysis> => {
  const searchParams = new URLSearchParams();
  if (params?.start_date) searchParams.append('start_date', params.start_date);
  if (params?.end_date) searchParams.append('end_date', params.end_date);
  if (params?.group_by) searchParams.append('group_by', params.group_by);
  
  return apiGet<SentimentAnalysis>(`/api/analytics/sentiment?${searchParams.toString()}`);
};

// ============================================================================
// Legacy API Functions (for backward compatibility)
// ============================================================================

export const getDashboardStats = async () => {
  return apiGet('/api/stats/dashboard');
};

export const getGraphData = async (params?: {
  limit?: number;
  node_types?: string;
  parent_id?: string;
  use_semantic_positioning?: boolean;
  layer?: string;
}) => {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.node_types) searchParams.append('node_types', params.node_types);
  if (params?.parent_id) searchParams.append('parent_id', params.parent_id);
  if (params?.use_semantic_positioning !== undefined) {
    searchParams.append('use_semantic_positioning', params.use_semantic_positioning.toString());
  }
  if (params?.layer) searchParams.append('layer', params.layer);
  
  return apiGet(`/api/graph?${searchParams.toString()}`);
};

export const getChats = async (params?: { limit?: number }) => {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  
  return apiGet(`/api/chats?${searchParams.toString()}`);
};

export const getChatMessages = async (chatId: string, params?: { limit?: number }) => {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  
  return apiGet(`/api/chats/${chatId}/messages?${searchParams.toString()}`);
};

export const getTags = async () => {
  return apiGet('/api/tags');
};

export const getCostStatistics = async (params?: {
  start_date?: string;
  end_date?: string;
  operation?: string;
}) => {
  const searchParams = new URLSearchParams();
  if (params?.start_date) searchParams.append('start_date', params.start_date);
  if (params?.end_date) searchParams.append('end_date', params.end_date);
  if (params?.operation) searchParams.append('operation', params.operation);
  
  return apiGet(`/api/costs/statistics?${searchParams.toString()}`);
}; 