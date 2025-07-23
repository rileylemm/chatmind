import { useState, useEffect } from 'react';
import axios from 'axios';
import { GraphData, Topic, Chat, FilterState } from '../types';

const API_BASE = 'http://localhost:8000';

export const useGraphData = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load graph data
        const graphResponse = await axios.get(`${API_BASE}/graph?limit=50`);
        setGraphData(graphResponse.data);

        // Load topics
        const topicsResponse = await axios.get(`${API_BASE}/topics`);
        setTopics(topicsResponse.data);

        // Load chats
        const chatsResponse = await axios.get(`${API_BASE}/chats?limit=50`);
        setChats(chatsResponse.data);

      } catch (err: any) {
        console.error('Error loading data:', err);
        setError(err.response?.data?.detail || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Load filtered data when filters change
  const loadFilteredData = async (filters: FilterState) => {
    if (filters.selectedTags.length > 0 || filters.selectedCategory || filters.searchQuery) {
      try {
        setGraphLoading(true);
        const params = new URLSearchParams();
        if (filters.selectedTags.length > 0) {
          params.append('tags', filters.selectedTags.join(','));
        }
        if (filters.selectedCategory) {
          params.append('category', filters.selectedCategory);
        }
        if (filters.searchQuery) {
          params.append('query', filters.searchQuery);
        }

        const response = await axios.get(`${API_BASE}/graph/filtered?${params.toString()}`);
        setGraphData(response.data);
      } catch (err: any) {
        console.error('Error loading filtered data:', err);
      } finally {
        setGraphLoading(false);
      }
    }
  };

  // Refresh data
  const refreshData = async () => {
    try {
      setLoading(true);
      setError(null);

      const graphResponse = await axios.get(`${API_BASE}/graph?limit=50`);
      setGraphData(graphResponse.data);

      const topicsResponse = await axios.get(`${API_BASE}/topics`);
      setTopics(topicsResponse.data);

      const chatsResponse = await axios.get(`${API_BASE}/chats?limit=50`);
      setChats(chatsResponse.data);

    } catch (err: any) {
      console.error('Error refreshing data:', err);
      setError(err.response?.data?.detail || 'Failed to refresh data');
    } finally {
      setLoading(false);
    }
  };

  return {
    graphData,
    topics,
    chats,
    loading,
    error,
    graphLoading,
    loadFilteredData,
    refreshData,
    setGraphData
  };
}; 