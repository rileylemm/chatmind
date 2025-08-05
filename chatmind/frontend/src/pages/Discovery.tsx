import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  getAvailableTags, 
  searchByTags, 
  searchByDomain,
  findSimilarContent,
  getConversationMessages
} from '../services/api';

interface DiscoveryResultItem {
  content: string;
  message_id?: string;
  chat_id?: string;
  role?: string;
  timestamp?: number;
  tags?: string[];
  similarity_score?: number;
}

const Discovery: React.FC = () => {
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedResult, setSelectedResult] = useState<DiscoveryResultItem | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Get available tags
  const { data: availableTags, isLoading: tagsLoading } = useQuery({
    queryKey: ['available-tags'],
    queryFn: getAvailableTags,
  });

  // Search by tags
  const { data: tagResults, isLoading: tagSearchLoading } = useQuery({
    queryKey: ['tag-search', selectedTags],
    queryFn: () => searchByTags({ tags: selectedTags, limit: 20 }),
    enabled: selectedTags.length > 0,
  });

  // Search by domain
  const { data: domainResults, isLoading: domainSearchLoading } = useQuery({
    queryKey: ['domain-search', selectedDomain],
    queryFn: () => searchByDomain({ domain: selectedDomain, limit: 20 }),
    enabled: !!selectedDomain,
  });

  const handleTagClick = (tagName: string) => {
    if (selectedTags.includes(tagName)) {
      setSelectedTags(selectedTags.filter(tag => tag !== tagName));
    } else {
      setSelectedTags([...selectedTags, tagName]);
    }
  };

  const handleDomainClick = (domain: string) => {
    setSelectedDomain(domain);
  };

  const handleResultClick = (result: DiscoveryResultItem) => {
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

  // Get detailed information for selected result
  const { data: similarContent, isLoading: similarContentLoading } = useQuery({
    queryKey: ['similar-content', selectedResult?.message_id],
    queryFn: () => findSimilarContent({ chunk_id: selectedResult!.message_id!, limit: 5 }),
    enabled: !!selectedResult?.message_id,
  });

  const { data: conversationMessages, isLoading: conversationMessagesLoading } = useQuery({
    queryKey: ['conversation-messages', selectedResult?.chat_id],
    queryFn: () => getConversationMessages({ chat_id: selectedResult!.chat_id!, limit: 10 }),
    enabled: !!selectedResult?.chat_id,
  });

  const filteredTags = availableTags?.filter(tag => 
    tag.name.toLowerCase().includes(searchQuery.toLowerCase())
  ).sort((a, b) => b.count - a.count) || [];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Tag-Based Discovery</h1>
        <p className="text-gray-600">Explore your knowledge graph through tags and domains</p>
        
        {/* Statistics */}
        {availableTags && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600">{availableTags.length}</div>
              <div className="text-sm text-blue-700">Total Tags</div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600">{selectedTags.length}</div>
              <div className="text-sm text-green-700">Selected Tags</div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-600">
                {availableTags.reduce((sum, tag) => sum + tag.count, 0).toLocaleString()}
              </div>
              <div className="text-sm text-purple-700">Total Occurrences</div>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-600">
                {availableTags.slice(0, 10).reduce((sum, tag) => sum + tag.count, 0)}
              </div>
              <div className="text-sm text-orange-700">Top 10 Tags</div>
            </div>
          </div>
        )}
      </div>

      {/* Search Tags */}
      <div className="mb-6">
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tags..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setSelectedTags([])}
            disabled={selectedTags.length === 0}
            className="px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Clear Tags
          </button>
        </div>

        {/* Selected Tags */}
        {selectedTags.length > 0 && (
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Selected Tags</h3>
            <div className="flex flex-wrap gap-2">
              {selectedTags.map(tag => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tags Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Tags</h2>
          
          {tagsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading tags...</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-sm text-gray-500">
                Found {filteredTags.length} tags
              </div>
              
              <div className="max-h-96 overflow-y-auto space-y-2">
                {filteredTags.slice(0, 50).map((tag) => (
                  <div
                    key={tag.name}
                    onClick={() => handleTagClick(tag.name)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedTags.includes(tag.name)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{tag.name}</div>
                        <div className="text-sm text-gray-500">
                          {tag.count.toLocaleString()} occurrences
                          {tag.count > 100 && (
                            <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                              Popular
                            </span>
                          )}
                        </div>
                      </div>
                      {selectedTags.includes(tag.name) && (
                        <div className="text-blue-600 ml-2">✓</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Results</h2>
          
          {/* Tag Search Results */}
          {selectedTags.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Results for tags: {selectedTags.join(', ')}
              </h3>
              
              {tagSearchLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Searching...</p>
                </div>
              ) : tagResults && tagResults.length > 0 ? (
                <div className="space-y-3">
                  {tagResults.slice(0, 10).map((result, index) => (
                    <div 
                      key={index} 
                      onClick={() => handleResultClick(result)}
                      className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer"
                    >
                      <div className="text-gray-900 mb-1">{result.content}</div>
                      <div className="text-xs text-gray-500">
                        {result.role && `${result.role} • `}
                        {result.timestamp && `${new Date(result.timestamp * 1000).toLocaleString()} • `}
                        {result.tags && result.tags.length > 0 && `Tags: ${result.tags.join(', ')}`}
                      </div>
                      <div className="text-xs text-blue-600 mt-2">
                        Click to explore details and related content →
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No results found for selected tags</p>
              )}
            </div>
          )}

          {/* Domain Search Results */}
          {selectedDomain && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Results for domain: {selectedDomain}
              </h3>
              
              {domainSearchLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Searching...</p>
                </div>
              ) : domainResults && domainResults.length > 0 ? (
                <div className="space-y-3">
                  {domainResults.slice(0, 10).map((result, index) => (
                    <div key={index} className="p-3 border border-gray-200 rounded-lg">
                      <div className="text-gray-900 mb-1">{result.content}</div>
                      <div className="text-xs text-gray-500">
                        {result.chunk_id && `Chunk: ${result.chunk_id}`}
                        {result.message_id && ` • Message: ${result.message_id}`}
                        {result.chat_id && ` • Chat: ${result.chat_id}`}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No results found for selected domain</p>
              )}
            </div>
          )}

          {/* No Selection */}
          {selectedTags.length === 0 && !selectedDomain && (
            <div className="text-center py-8">
              <p className="text-gray-600">Select tags or a domain to see results</p>
            </div>
          )}
        </div>
      </div>

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
              
              {selectedResult.role && (
                <div>
                  <div className="text-sm font-medium text-gray-500">Role</div>
                  <div className="text-gray-900">{selectedResult.role}</div>
                </div>
              )}
              
              {selectedResult.timestamp && (
                <div>
                  <div className="text-sm font-medium text-gray-500">Timestamp</div>
                  <div className="text-gray-900">{new Date(selectedResult.timestamp * 1000).toLocaleString()}</div>
                </div>
              )}
              
              {selectedResult.tags && selectedResult.tags.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-gray-500">Tags</div>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {selectedResult.tags.map((tag, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
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

          {/* Similar Content */}
          {similarContent && similarContent.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Similar Content</h3>
              {similarContentLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading similar content...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {similarContent.map((item, index) => (
                    <div key={index} className="p-3 border border-gray-200 rounded-lg">
                      <div className="text-gray-900 mb-1">{item.content}</div>
                      <div className="text-xs text-gray-500">
                        {item.role && `${item.role} • `}
                        {item.timestamp && `${new Date(item.timestamp * 1000).toLocaleString()}`}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Conversation Context */}
          {conversationMessages && conversationMessages.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversation Context</h3>
              {conversationMessagesLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading conversation...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {conversationMessages.map((message, index) => (
                    <div key={index} className="p-3 border border-gray-200 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div className="text-sm font-medium text-gray-700">{message.role}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(message.timestamp * 1000).toLocaleString()}
                        </div>
                      </div>
                      <div className="text-gray-900">{message.content}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Popular Tags */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Popular Tags</h2>
        <div className="flex flex-wrap gap-2">
          {availableTags?.slice(0, 20).map(tag => (
            <button
              key={tag.name}
              onClick={() => handleTagClick(tag.name)}
              className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                selectedTags.includes(tag.name)
                  ? 'border-blue-500 bg-blue-50 text-blue-800'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              {tag.name} ({tag.count})
            </button>
          ))}
        </div>
      </div>

      {/* Quick Domain Access */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Domain Access</h2>
        <div className="flex flex-wrap gap-2">
          {['technology', 'health', 'science', 'business', 'education'].map(domain => (
            <button
              key={domain}
              onClick={() => handleDomainClick(domain)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                selectedDomain === domain
                  ? 'border-blue-500 bg-blue-50 text-blue-800'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              {domain}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Discovery; 