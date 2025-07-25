// Graph Types
export interface GraphNode {
  id: string;
  type: 'Chat' | 'Message' | 'Topic' | 'Tag';
  properties: {
    title?: string;
    content?: string;
    role?: string;
    timestamp?: number;
    size?: number;
    top_words?: string[];
    sample_titles?: string[];
    [key: string]: unknown;
  };
  position?: { x: number; y: number };
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'CONTAINS' | 'SUMMARIZES' | 'HAS_TOPIC' | 'RELATED_TO';
  properties?: {
    weight?: number;
    [key: string]: unknown;
  };
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Message Types
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp?: number;
  chat_id: string;
  cluster_id?: number;
  tags?: string[];
  parent_id?: string;
}

export interface Chat {
  id: string;
  title: string;
  create_time?: number;
  message_count?: number;
  tags?: string[];
}

// Tag Types
export interface Tag {
  name: string;
  count: number;
  category?: string;
}

export interface TagFilter {
  selectedTags: string[];
  selectedCategory: string | null;
  searchQuery: string;
}

// Cost Types
export interface CostStatistics {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  model_statistics: Record<string, unknown>;
  operation_statistics: Record<string, unknown>;
  date_range: {
    start_date: string | null;
    end_date: string | null;
  };
}

export interface RecentCall {
  id: number;
  timestamp: number;
  model: string;
  operation: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  success: boolean;
  error_message?: string;
}

// UI Types
export interface Theme {
  mode: 'light' | 'dark';
}

export interface UIState {
  sidebarOpen: boolean;
  theme: Theme;
  selectedNode: GraphNode | null;
  commandPaletteOpen: boolean;
}

// API Types
export interface ApiResponse<T> {
  data: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// Search Types
export interface SearchResult {
  id: string;
  type: 'chat' | 'message' | 'topic';
  title: string;
  content?: string;
  relevance: number;
  tags?: string[];
}

// Filter Types
export interface FilterState {
  tags: string[];
  dateRange: { start: Date | null; end: Date | null };
  role: 'all' | 'user' | 'assistant';
  searchQuery: string;
} 