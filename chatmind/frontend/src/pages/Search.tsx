import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { 
  Search as SearchIcon, 
  Tag, 
  Brain, 
  MessageSquare, 
  Clock,
  ArrowUpRight,
  Sparkles,
  Target,
  Eye
} from 'lucide-react';
import { 
  searchSemantic, 
  searchContent, 
  searchByTags,
  advancedSearch 
} from '../services/api';

const Search: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [searchType, setSearchType] = useState<'semantic' | 'content' | 'tags' | 'advanced'>('semantic');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [filters, setFilters] = useState({
    role: 'all',
    min_similarity: 0.7,
    exact_match: false,
    limit: 20
  });

  // Update URL when search query changes
  useEffect(() => {
    if (searchQuery) {
      setSearchParams({ q: searchQuery });
    }
  }, [searchQuery, setSearchParams]);

  // Semantic search
  const { data: semanticResults, isLoading: semanticLoading } = useQuery({
    queryKey: ['semantic-search', searchQuery, filters.min_similarity],
    queryFn: () => searchSemantic({
      query: searchQuery,
      limit: filters.limit,
      min_similarity: filters.min_similarity
    }),
    enabled: searchType === 'semantic' && !!searchQuery,
  });

  // Content search
  const { data: contentResults, isLoading: contentLoading } = useQuery({
    queryKey: ['content-search', searchQuery, filters.role],
    queryFn: () => searchContent({
      query: searchQuery,
      limit: filters.limit,
      role: filters.role === 'all' ? undefined : filters.role
    }),
    enabled: searchType === 'content' && !!searchQuery,
  });

  // Tag search
  const { data: tagResults, isLoading: tagLoading } = useQuery({
    queryKey: ['tag-search', selectedTags, filters.exact_match],
    queryFn: () => searchByTags({
      tags: selectedTags,
      limit: filters.limit,
      exact_match: filters.exact_match
    }),
    enabled: searchType === 'tags' && selectedTags.length > 0,
  });

  // Advanced search
  const { data: advancedResults, isLoading: advancedLoading } = useQuery({
    queryKey: ['advanced-search', searchQuery, filters],
    queryFn: () => advancedSearch({
      query: searchQuery,
      filters: {
        limit: filters.limit,
        min_similarity: filters.min_similarity
      }
    }),
    enabled: searchType === 'advanced' && !!searchQuery,
  });

  const currentResults = searchType === 'semantic' ? semanticResults :
                        searchType === 'content' ? contentResults :
                        searchType === 'tags' ? tagResults :
                        advancedResults;

  const isLoading = semanticLoading || contentLoading || tagLoading || advancedLoading;

  const handleSearch = () => {
    if (!searchQuery.trim() && searchType !== 'tags') return;
    // Trigger search by changing search type briefly
    const currentType = searchType;
    setSearchType('semantic');
    setTimeout(() => setSearchType(currentType), 100);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                             <SearchIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Search
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                Find conversations, topics, and insights across your knowledge graph
              </p>
            </div>
          </div>
        </div>

        {/* Search Interface */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-8">
          <div className="space-y-6">
            {/* Search Type Selector */}
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'semantic', label: 'Semantic Search', icon: Brain, description: 'AI-powered semantic understanding' },
                { key: 'content', label: 'Content Search', icon: MessageSquare, description: 'Direct text matching' },
                { key: 'tags', label: 'Tag Search', icon: Tag, description: 'Search by tags and categories' },
                { key: 'advanced', label: 'Advanced Search', icon: Target, description: 'Complex queries with filters' }
              ].map((type) => (
                <button
                  key={type.key}
                                     onClick={() => setSearchType(type.key as 'semantic' | 'content' | 'tags' | 'advanced')}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                    searchType === type.key
                      ? 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'
                  }`}
                >
                  <type.icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{type.label}</span>
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative">
                             <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  searchType === 'semantic' ? "Search semantically (e.g., 'machine learning concepts')" :
                  searchType === 'content' ? "Search content directly (e.g., 'Python web development')" :
                  searchType === 'tags' ? "Search by tags (e.g., 'python, api, web')" :
                  "Advanced search with filters..."
                }
                className="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg leading-5 bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={handleSearch}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-1 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Search
              </button>
            </div>

            {/* Tag Selection (for tag search) */}
            {searchType === 'tags' && (
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Select Tags
                </label>
                <div className="flex flex-wrap gap-2">
                  {['python', 'api', 'web', 'ai', 'machine learning', 'database', 'frontend', 'backend'].map((tag) => (
                    <button
                      key={tag}
                      onClick={() => {
                        if (selectedTags.includes(tag)) {
                          setSelectedTags(selectedTags.filter(t => t !== tag));
                        } else {
                          setSelectedTags([...selectedTags, tag]);
                        }
                      }}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        selectedTags.includes(tag)
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Filters */}
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Role:</label>
                <select
                  value={filters.role}
                  onChange={(e) => setFilters({ ...filters, role: e.target.value })}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1 bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                >
                  <option value="all">All</option>
                  <option value="user">User</option>
                  <option value="assistant">Assistant</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Min Similarity:</label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={filters.min_similarity}
                  onChange={(e) => setFilters({ ...filters, min_similarity: parseFloat(e.target.value) })}
                  className="w-20"
                />
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {filters.min_similarity}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Limit:</label>
                <select
                  value={filters.limit}
                  onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) })}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1 bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>

              {searchType === 'tags' && (
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Exact Match:</label>
                  <input
                    type="checkbox"
                    checked={filters.exact_match}
                    onChange={(e) => setFilters({ ...filters, exact_match: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Search Results */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 animate-pulse">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-3"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : currentResults && currentResults.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Search Results ({currentResults.length})
              </h3>
              <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                <Sparkles className="h-4 w-4" />
                <span>Powered by AI</span>
              </div>
            </div>

                         {currentResults.map((result) => (
              <div key={result.id} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 hover:shadow-lg transition-shadow duration-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                        {result.role || 'Message'}
                      </span>
                      {result.similarity_score && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                          {(result.similarity_score * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                    
                    <p className="text-gray-900 dark:text-white mb-3 line-clamp-3">
                      {result.content}
                    </p>

                    <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex items-center space-x-4">
                        {result.timestamp && (
                          <div className="flex items-center space-x-1">
                            <Clock className="h-4 w-4" />
                            <span>{new Date(result.timestamp).toLocaleDateString()}</span>
                          </div>
                        )}
                        {result.chat_id && (
                          <div className="flex items-center space-x-1">
                            <MessageSquare className="h-4 w-4" />
                            <span>Chat {result.chat_id.slice(0, 8)}...</span>
                          </div>
                        )}
                      </div>

                      {result.tags && result.tags.length > 0 && (
                        <div className="flex items-center space-x-1">
                          <Tag className="h-4 w-4" />
                          <span>{result.tags.slice(0, 2).join(', ')}</span>
                          {result.tags.length > 2 && <span>+{result.tags.length - 2}</span>}
                        </div>
                      )}
                    </div>
                  </div>

                  <button className="ml-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                    <ArrowUpRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : searchQuery || selectedTags.length > 0 ? (
          <div className="text-center py-12">
            <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No results found
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Try adjusting your search terms or filters
            </p>
          </div>
        ) : (
          <div className="text-center py-12">
                         <SearchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Start searching
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Enter a query to search across your knowledge graph
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search; 