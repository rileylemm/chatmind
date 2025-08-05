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
// Health API Functions
// ============================================================================

export interface HealthStatus {
  status: string;
  neo4j: string;
}

export const getHealthStatus = async (): Promise<HealthStatus> => {
  return apiGet<HealthStatus>('/api/health');
};

// ============================================================================
// Search API Functions
// ============================================================================

export interface SearchResult {
  chunk_id?: string;
  content: string;
  message_id?: string;
  chat_id?: string;
  similarity_score?: number;
  source?: string;
  conversation_title?: string;
  timestamp?: number;
  role?: string;
  tags?: string[];
}

export interface SimpleSearchResult {
  content: string;
  message_id: string;
  conversation_title?: string;
  timestamp?: number;
  role?: string;
}

// Simple search (Neo4j only)
export const simpleSearch = async (params: {
  query: string;
  limit?: number;
}): Promise<SimpleSearchResult[]> => {
  const { query, limit = 10 } = params;
  return apiGet<SimpleSearchResult[]>(`/api/search?query=${encodeURIComponent(query)}&limit=${limit}`);
};

// Semantic search (Qdrant only)
export const semanticSearch = async (params: {
  query: string;
  limit?: number;
}): Promise<SearchResult[]> => {
  const { query, limit = 10 } = params;
  return apiGet<SearchResult[]>(`/api/search/semantic?query=${encodeURIComponent(query)}&limit=${limit}`);
};

// Hybrid search (Neo4j + Qdrant)
export const hybridSearch = async (params: {
  query: string;
  limit?: number;
}): Promise<SearchResult[]> => {
  const { query, limit = 10 } = params;
  return apiGet<SearchResult[]>(`/api/search/hybrid?query=${encodeURIComponent(query)}&limit=${limit}`);
};

// Search by tags
export const searchByTags = async (params: {
  tags: string[];
  limit?: number;
}): Promise<SearchResult[]> => {
  const { tags, limit = 10 } = params;
  const tagsParam = tags.join(',');
  return apiGet<SearchResult[]>(`/api/search/tags?tags=${encodeURIComponent(tagsParam)}&limit=${limit}`);
};

// Search by domain
export const searchByDomain = async (params: {
  domain: string;
  limit?: number;
}): Promise<SearchResult[]> => {
  const { domain, limit = 10 } = params;
  return apiGet<SearchResult[]>(`/api/search/domain/${encodeURIComponent(domain)}?limit=${limit}`);
};

// Find similar content
export const findSimilarContent = async (params: {
  chunk_id: string;
  limit?: number;
}): Promise<SearchResult[]> => {
  const { chunk_id, limit = 10 } = params;
  return apiGet<SearchResult[]>(`/api/search/similar/${chunk_id}?limit=${limit}`);
};

// Get available tags
export interface AvailableTag {
  name: string;
  count: number;
}

export const getAvailableTags = async (): Promise<AvailableTag[]> => {
  return apiGet<AvailableTag[]>('/api/search/tags/available');
};

// Search statistics
export interface SearchStats {
  neo4j_connected: boolean;
  qdrant_connected: boolean;
  embedding_model_loaded: boolean;
  total_conversations: number;
  total_messages: number;
  total_chunks: number;
}

export const getSearchStats = async (): Promise<SearchStats> => {
  return apiGet<SearchStats>('/api/search/stats');
};

// ============================================================================
// Graph API Functions
// ============================================================================

export interface GraphNode {
  id: string;
  type: string;
  properties: Record<string, unknown>;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties?: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Get graph data
export const getGraphData = async (params?: {
  limit?: number;
}): Promise<GraphData> => {
  const { limit = 100 } = params || {};
  return apiGet<GraphData>(`/api/graph?limit=${limit}`);
};

// Get graph visualization data
export const getGraphVisualization = async (params?: {
  node_types?: string[];
  limit?: number;
  include_edges?: boolean;
  filter_domain?: string;
}): Promise<GraphData> => {
  const searchParams = new URLSearchParams();
  if (params?.node_types) searchParams.append('node_types', params.node_types.join(','));
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.include_edges !== undefined) searchParams.append('include_edges', params.include_edges.toString());
  if (params?.filter_domain) searchParams.append('filter_domain', params.filter_domain);
  
  const queryString = searchParams.toString();
  return apiGet<GraphData>(`/api/graph/visualization${queryString ? `?${queryString}` : ''}`);
};

// ============================================================================
// Conversation API Functions
// ============================================================================

export interface Conversation {
  chat_id: string;
  title: string;
  create_time: number;
  message_count: number;
  position_x: number;
  position_y: number;
}

export interface Message {
  message_id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: number;
  chat_id: string;
}

export interface ChunkDetails {
  chunk_id: string;
  content: string;
  message_id: string;
  chat_id: string;
}

// Get conversations
export const getConversations = async (params?: {
  limit?: number;
}): Promise<Conversation[]> => {
  const { limit = 50 } = params || {};
  return apiGet<Conversation[]>(`/api/conversations?limit=${limit}`);
};

// Get messages for a conversation
export const getConversationMessages = async (params: {
  chat_id: string;
  limit?: number;
}): Promise<Message[]> => {
  const { chat_id, limit = 50 } = params;
  return apiGet<Message[]>(`/api/conversations/${chat_id}/messages?limit=${limit}`);
};

// Get chunk details
export const getChunkDetails = async (params: {
  chunk_id: string;
}): Promise<ChunkDetails> => {
  const { chunk_id } = params;
  return apiGet<ChunkDetails>(`/api/chunks/${chunk_id}`);
};

// ============================================================================
// Debug API Functions
// ============================================================================

export interface DatabaseSchema {
  neo4j_schema: {
    nodes: Array<{
      type: string;
      count: number;
      properties: string[];
    }>;
    relationships: Array<{
      type: string;
      count: number;
      properties: string[];
    }>;
  };
  qdrant_schema: {
    collection_name: string;
    vector_size: number;
    total_points: number;
  };
}

export const getDatabaseSchema = async (): Promise<DatabaseSchema> => {
  return apiGet<DatabaseSchema>('/api/debug/schema');
}; 