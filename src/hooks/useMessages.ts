import { useState } from 'react';
import axios from 'axios';
import { Message, SelectedNode, Topic, Chat } from '../types';

const API_BASE = 'http://localhost:8000';

export const useMessages = () => {
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const handleNodeClick = async (evt: any) => {
    const node = evt.target;
    const nodeData = node.data();
    
    try {
      let messagesResponse;
      if (nodeData.type === 'Chat') {
        messagesResponse = await axios.get(`${API_BASE}/chats/${nodeData.id}/messages`);
      } else if (nodeData.type === 'Topic') {
        messagesResponse = await axios.get(`${API_BASE}/topics/${nodeData.id}/messages`);
      } else {
        return;
      }
      
      setMessages(messagesResponse.data);
      setSelectedNode({
        type: nodeData.type,
        id: nodeData.id,
        label: nodeData.label,
        properties: nodeData
      });
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  };

  const handleSearch = async (query: string) => {
    try {
      const response = await axios.get(`${API_BASE}/search?query=${encodeURIComponent(query)}&limit=50`);
      setMessages(response.data);
      setSelectedNode({
        type: 'Search',
        label: `Search: ${query}`,
        query: query
      });
    } catch (err) {
      console.error('Error searching:', err);
    }
  };

  const handleTopicClick = (topic: Topic) => {
    handleSearch(topic.top_words.join(' '));
  };

  const handleChatClick = (chat: Chat) => {
    handleSearch(chat.title);
  };

  const clearSelection = () => {
    setSelectedNode(null);
    setMessages([]);
  };

  return {
    selectedNode,
    messages,
    handleNodeClick,
    handleSearch,
    handleTopicClick,
    handleChatClick,
    clearSelection
  };
}; 