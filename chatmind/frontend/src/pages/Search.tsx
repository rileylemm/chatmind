import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  simpleSearch, 
  semanticSearch, 
  hybridSearch, 
  getSearchStats,
  getChunkDetails,
  findSimilarContent,
  getConversationMessages
} from '../services/api';

interface SearchResultItem {
  content: string;
  chunk_id?: string;
  message_id?: string;
  chat_id?: string;
  similarity_score?: number;
  source?: string;
  conversation_title?: string;
  timestamp?: number;
  role?: string;
}

const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'simple' | 'semantic' | 'hybrid'>('semantic');
  const [limit, setLimit] = useState(10);
  const [selectedResult, setSelectedResult] = useState<SearchResultItem | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Get search stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['search-stats'],
    queryFn: getSearchStats,
  });

  // Search query
  const { data: searchResults, isLoading: searchLoading, refetch } = useQuery({
    queryKey: ['search', query, searchType, limit],
    queryFn: async () => {
      if (!query.trim()) return [];
      
      switch (searchType) {
        case 'simple':
          return await simpleSearch({ query, limit });
        case 'semantic':
          return await semanticSearch({ query, limit });
        case 'hybrid':
          return await hybridSearch({ query, limit });
        default:
          return [];
      }
    },
    enabled: !!query.trim(),
  });

  // Scroll to results when search completes
  React.useEffect(() => {
    if (searchResults && searchResults.length > 0 && query.trim()) {
      setTimeout(() => {
        const resultsElement = document.querySelector('[data-search-results]');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }, [searchResults, query]);

  // Get chunk details when a result is selected
  const { data: chunkDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['chunk-details', selectedResult?.chunk_id],
    queryFn: () => getChunkDetails({ chunk_id: selectedResult!.chunk_id! }),
    enabled: !!selectedResult?.chunk_id,
  });

  // Get similar content
  const { data: similarContent, isLoading: similarLoading } = useQuery({
    queryKey: ['similar-content', selectedResult?.chunk_id],
    queryFn: () => findSimilarContent({ chunk_id: selectedResult!.chunk_id!, limit: 5 }),
    enabled: !!selectedResult?.chunk_id,
  });

  // Get conversation messages
  const { data: conversationMessages, isLoading: messagesLoading } = useQuery({
    queryKey: ['conversation-messages', selectedResult?.chat_id],
    queryFn: () => getConversationMessages({ chat_id: selectedResult!.chat_id!, limit: 10 }),
    enabled: !!selectedResult?.chat_id,
  });

  const handleSearch = () => {
    if (query.trim()) {
      refetch();
      setSelectedResult(null);
      setShowDetails(false);
      // Scroll to top when performing new search
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleResultClick = (result: SearchResultItem) => {
    setSelectedResult(result);
    setShowDetails(true);
    // Scroll to top when showing details
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToResults = () => {
    setSelectedResult(null);
    setShowDetails(false);
    // Scroll to top when going back to results
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Search & Discovery</h1>
        <p className="text-gray-600">Explore your ChatGPT knowledge graph with semantic search</p>
      </div>

      {/* Search Stats */}
      {statsLoading ? (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="animate-pulse">Loading stats...</div>
        </div>
      ) : stats && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{stats.total_conversations}</div>
            <div className="text-sm text-blue-600">Conversations</div>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.total_messages}</div>
            <div className="text-sm text-green-600">Messages</div>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{stats.total_chunks}</div>
            <div className="text-sm text-purple-600">Chunks</div>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {stats.neo4j_connected && stats.qdrant_connected ? '✅' : '❌'}
            </div>
            <div className="text-sm text-orange-600">Connected</div>
          </div>
        </div>
      )}

      {/* Search Interface */}
      <div className="mb-8">
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search for topics, concepts, or questions..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as 'simple' | 'semantic' | 'hybrid')}
              className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="simple">Simple (Neo4j)</option>
              <option value="semantic">Semantic (Qdrant)</option>
              <option value="hybrid">Hybrid (Both)</option>
            </select>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={5}>5 results</option>
              <option value={10}>10 results</option>
              <option value={20}>20 results</option>
              <option value={50}>50 results</option>
            </select>
            <button
              onClick={handleSearch}
              disabled={!query.trim() || searchLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {searchLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </div>

      {/* Search Results */}
      {searchLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Searching...</p>
        </div>
      )}

      {searchResults && searchResults.length > 0 && !showDetails && (
        <div className="space-y-4" data-search-results>
          <h2 className="text-xl font-semibold text-gray-900">
            Found {searchResults.length} results for "{query}"
          </h2>
          
          <div className="grid gap-4">
            {searchResults.map((result, index) => (
              <div 
                key={index} 
                onClick={() => handleResultClick(result)}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="text-sm text-gray-500">
                    {searchType === 'simple' ? 'Simple Search' : 
                     searchType === 'semantic' ? 'Semantic Search' : 'Hybrid Search'}
                  </div>
                  {('similarity_score' in result && result.similarity_score) && (
                    <div className="text-sm text-green-600 font-medium">
                      {(result.similarity_score * 100).toFixed(1)}% match
                    </div>
                  )}
                </div>
                
                <div className="text-gray-900 mb-2">
                  {result.content}
                </div>
                
                <div className="text-xs text-gray-500 space-y-1">
                  {result.conversation_title && (
                    <div className="font-medium text-blue-600">
                      📝 {result.conversation_title}
                    </div>
                  )}
                  {result.role && (
                    <div className="text-gray-600">
                      👤 {result.role.charAt(0).toUpperCase() + result.role.slice(1)}
                    </div>
                  )}
                  {result.timestamp && (
                    <div className="text-gray-500">
                      🕒 {new Date(result.timestamp * 1000).toLocaleString()}
                    </div>
                  )}
                </div>
                
                <div className="mt-2 text-xs text-blue-600">
                  Click to explore details and related content →
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed View */}
      {showDetails && selectedResult && (
        <div className="space-y-6">
          {/* Back Button */}
          <button
            onClick={handleBackToResults}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
          >
            ← Back to search results
          </button>

          {/* Selected Result Details */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Selected Content</h2>
            
            <div className="space-y-4">
              <div>
                <div className="text-sm font-medium text-gray-500">Content</div>
                <div className="text-gray-900 mt-1">{selectedResult.content}</div>
              </div>
              
              {('similarity_score' in selectedResult && selectedResult.similarity_score) && (
                <div>
                  <div className="text-sm font-medium text-gray-500">Similarity Score</div>
                  <div className="text-green-600 font-medium">
                    {(selectedResult.similarity_score * 100).toFixed(1)}% match
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                {selectedResult.chunk_id && (
                  <div>
                    <div className="font-medium text-gray-500">Chunk ID</div>
                    <div className="text-gray-900 break-all">{selectedResult.chunk_id}</div>
                  </div>
                )}
                {selectedResult.message_id && (
                  <div>
                    <div className="font-medium text-gray-500">Message ID</div>
                    <div className="text-gray-900 break-all">{selectedResult.message_id}</div>
                  </div>
                )}
                {selectedResult.chat_id && (
                  <div>
                    <div className="font-medium text-gray-500">Chat ID</div>
                    <div className="text-gray-900 break-all">{selectedResult.chat_id}</div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Chunk Details */}
          {chunkDetails && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Chunk Details</h3>
              <div className="space-y-2">
                <div>
                  <div className="text-sm font-medium text-gray-500">Chunk ID</div>
                  <div className="text-gray-900 break-all">{chunkDetails.chunk_id}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-500">Content</div>
                  <div className="text-gray-900">{chunkDetails.content}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-500">Message ID</div>
                  <div className="text-gray-900">{chunkDetails.message_id}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-500">Chat ID</div>
                  <div className="text-gray-900">{chunkDetails.chat_id}</div>
                </div>
              </div>
            </div>
          )}

          {/* Similar Content */}
          {similarContent && similarContent.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Similar Content</h3>
              <div className="space-y-3">
                {similarContent.map((item, index) => (
                  <div key={index} className="p-3 border border-gray-200 rounded-lg">
                    <div className="text-gray-900 mb-1">{item.content}</div>
                    <div className="text-xs text-gray-500">
                      {item.chunk_id && `Chunk: ${item.chunk_id}`}
                      {item.message_id && ` • Message: ${item.message_id}`}
                      {item.chat_id && ` • Chat: ${item.chat_id}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Conversation Context */}
          {conversationMessages && conversationMessages.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversation Context</h3>
              <div className="space-y-3">
                {conversationMessages.map((message, index) => (
                  <div key={index} className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex justify-between items-start mb-1">
                      <div className="text-sm font-medium text-gray-500">{message.role}</div>
                      <div className="text-xs text-gray-400">
                        {new Date(message.timestamp * 1000).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-gray-900">{message.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Loading States */}
          {detailsLoading && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="animate-pulse">Loading chunk details...</div>
            </div>
          )}
          
          {similarLoading && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="animate-pulse">Loading similar content...</div>
            </div>
          )}
          
          {messagesLoading && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="animate-pulse">Loading conversation context...</div>
            </div>
          )}
        </div>
      )}

      {searchResults && searchResults.length === 0 && query && !searchLoading && !showDetails && (
        <div className="text-center py-8">
          <p className="text-gray-600">No results found for "{query}"</p>
          <p className="text-sm text-gray-500 mt-2">Try a different search term or search type</p>
        </div>
      )}
    </div>
  );
};

export default Search; 