import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Search, 
  Filter, 
  MessageSquare, 
  Calendar,
  User,
  Bot,
  ChevronRight,
  ChevronDown,
  Copy
} from 'lucide-react';
import { api } from '../services/api';
import type { Chat, Message } from '../types';

const Messages: React.FC = () => {
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<'all' | 'user' | 'assistant'>('all');
  const [expandedChats, setExpandedChats] = useState<Set<string>>(new Set());

  // Fetch all chats
  const { data: chats, isLoading: chatsLoading } = useQuery({
    queryKey: ['chats'],
    queryFn: async (): Promise<Chat[]> => {
      const response = await api.get('/api/chats');
      return response.data.data || [];
    },
  });

  // Fetch messages for selected chat
  const { data: messages, isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', selectedChatId],
    queryFn: async (): Promise<Message[]> => {
      if (!selectedChatId) return [];
      const response = await api.get(`/api/chats/${selectedChatId}/messages`);
      return response.data.data || [];
    },
    enabled: !!selectedChatId,
  });

  // Filter chats based on search query
  const filteredChats = chats?.filter(chat => 
    chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    chat.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  ) || [];

  // Filter messages based on role
  const filteredMessages = messages?.filter(message => 
    roleFilter === 'all' || message.role === roleFilter
  ) || [];

  const toggleChatExpansion = (chatId: string) => {
    const newExpanded = new Set(expandedChats);
    if (newExpanded.has(chatId)) {
      newExpanded.delete(chatId);
    } else {
      newExpanded.add(chatId);
    }
    setExpandedChats(newExpanded);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Messages
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Browse and search your ChatGPT conversations
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search chats and messages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm w-64"
              />
            </div>
            
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as 'all' | 'user' | 'assistant')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Roles</option>
              <option value="user">User Only</option>
              <option value="assistant">Assistant Only</option>
            </select>
            
            <button className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chats list */}
        <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-y-auto">
          <div className="p-4">
            {chatsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading chats...</span>
              </div>
            ) : filteredChats.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">No chats found</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredChats.map((chat) => {
                  const isExpanded = expandedChats.has(chat.id);
                  const isSelected = selectedChatId === chat.id;
                  
                  return (
                    <div
                      key={chat.id}
                      className={`rounded-lg border transition-all duration-200 ${
                        isSelected 
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      {/* Chat header */}
                      <div
                        className={`p-4 cursor-pointer ${
                          isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                        }`}
                        onClick={() => {
                          setSelectedChatId(chat.id);
                          if (!isExpanded) {
                            setExpandedChats(new Set([...expandedChats, chat.id]));
                          }
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                              {chat.title}
                            </h3>
                            <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
                              <span className="flex items-center">
                                <MessageSquare className="h-3 w-3 mr-1" />
                                {chat.message_count || 0} messages
                              </span>
                              {chat.create_time && (
                                <span className="flex items-center">
                                  <Calendar className="h-3 w-3 mr-1" />
                                  {new Date(chat.create_time * 1000).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {chat.tags && chat.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {chat.tags.slice(0, 2).map((tag, idx) => (
                                  <span
                                    key={idx}
                                    className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded-full text-gray-600 dark:text-gray-400"
                                  >
                                    {tag}
                                  </span>
                                ))}
                                {chat.tags.length > 2 && (
                                  <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded-full text-gray-600 dark:text-gray-400">
                                    +{chat.tags.length - 2}
                                  </span>
                                )}
                              </div>
                            )}
                            
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleChatExpansion(chat.id);
                              }}
                              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                            >
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4 text-gray-500" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-gray-500" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Expanded messages preview */}
                      {isExpanded && (
                        <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <div className="p-4 space-y-2">
                            {messagesLoading ? (
                              <div className="text-center py-4">
                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
                                <span className="text-sm text-gray-600 dark:text-gray-400 ml-2">Loading messages...</span>
                              </div>
                            ) : filteredMessages.length === 0 ? (
                              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                                No messages found
                              </p>
                            ) : (
                              filteredMessages.slice(0, 3).map((message) => (
                                <div
                                  key={message.id}
                                  className="p-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700"
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex items-center space-x-2 mb-2">
                                      {message.role === 'user' ? (
                                        <User className="h-4 w-4 text-blue-500" />
                                      ) : (
                                        <Bot className="h-4 w-4 text-green-500" />
                                      )}
                                      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                                        {message.role}
                                      </span>
                                      {message.timestamp && (
                                        <span className="text-xs text-gray-500 dark:text-gray-400">
                                          {formatTimestamp(message.timestamp)}
                                        </span>
                                      )}
                                    </div>
                                    <button
                                      onClick={() => copyToClipboard(message.content)}
                                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                                    >
                                      <Copy className="h-3 w-3 text-gray-400" />
                                    </button>
                                  </div>
                                  <p className="text-sm text-gray-900 dark:text-white line-clamp-3">
                                    {message.content}
                                  </p>
                                </div>
                              ))
                            )}
                            {filteredMessages.length > 3 && (
                              <button className="w-full text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 py-2">
                                View all {filteredMessages.length} messages
                              </button>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Messages detail */}
        <div className="w-1/2 bg-white dark:bg-gray-800 overflow-y-auto">
          {selectedChatId ? (
            <div className="p-6">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  {chats?.find(c => c.id === selectedChatId)?.title}
                </h2>
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <span className="flex items-center">
                    <MessageSquare className="h-4 w-4 mr-1" />
                    {filteredMessages.length} messages
                  </span>
                  {roleFilter !== 'all' && (
                    <span className="flex items-center">
                      <Filter className="h-4 w-4 mr-1" />
                      {roleFilter} only
                    </span>
                  )}
                </div>
              </div>

              {messagesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  <span className="ml-2 text-gray-600 dark:text-gray-400">Loading messages...</span>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredMessages.map((message) => (
                    <div
                      key={message.id}
                      className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          {message.role === 'user' ? (
                            <div className="flex items-center space-x-2">
                              <User className="h-5 w-5 text-blue-500" />
                              <span className="text-sm font-medium text-blue-600 dark:text-blue-400">You</span>
                            </div>
                          ) : (
                            <div className="flex items-center space-x-2">
                              <Bot className="h-5 w-5 text-green-500" />
                              <span className="text-sm font-medium text-green-600 dark:text-green-400">Assistant</span>
                            </div>
                          )}
                          {message.timestamp && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {formatTimestamp(message.timestamp)}
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {message.tags && message.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {message.tags.map((tag, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded-full text-gray-600 dark:text-gray-400"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                          <button
                            onClick={() => copyToClipboard(message.content)}
                            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                            title="Copy message"
                          >
                            <Copy className="h-4 w-4 text-gray-400" />
                          </button>
                        </div>
                      </div>
                      
                      <div className="prose prose-sm max-w-none text-gray-900 dark:text-white">
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">Select a chat to view messages</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Messages; 