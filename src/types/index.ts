export interface Node {
  id: string;
  type: string;
  properties: any;
}

export interface Edge {
  source: string;
  target: string;
  type: string;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

export interface Topic {
  id: number;
  name: string;
  size: number;
  top_words: string[];
  sample_titles: string[];
}

export interface Chat {
  id: string;
  title: string;
  create_time?: number;
}

export interface Message {
  id: string;
  content: string;
  role: string;
  timestamp?: number;
  cluster_id?: number;
}

export interface FilterState {
  selectedTags: string[];
  selectedCategory: string | null;
  searchQuery: string;
}

export interface SelectedNode {
  type: string;
  id?: string;
  label: string;
  properties?: any;
  query?: string;
} 