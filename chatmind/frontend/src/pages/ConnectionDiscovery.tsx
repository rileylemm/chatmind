import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  getConversations,
  explainConnection,
  searchCrossDomain,
  getDiscoverySuggestions,
  getConversationMessages,
  findSimilarContent
} from '../services/api';

interface ConnectionDiscoveryProps {}

const ConnectionDiscovery: React.FC<ConnectionDiscoveryProps> = () => {
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [crossDomainQuery, setCrossDomainQuery] = useState<string>('');
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Get available conversations for selection
  const { data: conversations, isLoading: conversationsLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => getConversations({ limit: 50 }),
  });

  // Get connection explanation
  const { data: connectionExplanation } = useQuery({
    queryKey: ['connection-explanation', selectedSource, selectedTarget],
    queryFn: () => explainConnection({ source_id: selectedSource, target_id: selectedTarget }),
    enabled: !!selectedSource && !!selectedTarget && selectedSource !== selectedTarget,
  });

  // Get cross-domain search results
  const { data: crossDomainResults, isLoading: crossDomainLoading } = useQuery({
    queryKey: ['cross-domain-search', crossDomainQuery],
    queryFn: () => searchCrossDomain({ query: crossDomainQuery, limit: 10 }),
    enabled: !!crossDomainQuery.trim(),
  });

  // Get discovery suggestions
  const { data: suggestions, isLoading: suggestionsLoading } = useQuery({
    queryKey: ['discovery-suggestions'],
    queryFn: () => getDiscoverySuggestions({ limit: 5 }),
  });

  // Get conversation messages for selected result
  const { data: conversationMessages } = useQuery({
    queryKey: ['conversation-messages', selectedResult?.chat_id],
    queryFn: () => getConversationMessages({ chat_id: selectedResult!.chat_id!, limit: 10 }),
    enabled: !!selectedResult?.chat_id,
  });

  // Get similar content for selected result
  const { data: similarContent } = useQuery({
    queryKey: ['similar-content', selectedResult?.message_id],
    queryFn: () => findSimilarContent({ chunk_id: selectedResult!.message_id!, limit: 5 }),
    enabled: !!selectedResult?.message_id,
  });

  const handleSourceSelect = (chatId: string) => {
    setSelectedSource(chatId);
    if (selectedTarget === chatId) {
      setSelectedTarget('');
    }
  };

  const handleTargetSelect = (chatId: string) => {
    setSelectedTarget(chatId);
  };

  const handleResultClick = (result: any) => {
    setSelectedResult(result);
    setShowDetails(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToResults = () => {
    setSelectedResult(null);
    setShowDetails(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCrossDomainSearch = () => {
    if (crossDomainQuery.trim()) {
      // Trigger the query
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Connection Discovery</h1>
        <p className="text-gray-600">Explore unexpected connections between conversations and topics</p>
      </div>

      {showDetails && selectedResult ? (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Result Details</h2>
            <button
              onClick={handleBackToResults}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              ← Back to Results
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Content</h3>
              <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{selectedResult.content}</p>
            </div>

            {selectedResult.domain && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Domain</h3>
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                  {selectedResult.domain}
                </span>
              </div>
            )}

            {selectedResult.tags && selectedResult.tags.length > 0 && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedResult.tags.map((tag: string) => (
                    <span key={tag} className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {similarContent && similarContent.length > 0 && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Similar Content</h3>
                <div className="space-y-2">
                  {similarContent.slice(0, 3).map((item: any, index: number) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-700">{item.content}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Similarity: {(item.similarity_score * 100).toFixed(1)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {conversationMessages && conversationMessages.length > 0 && (
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Conversation Context</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {conversationMessages.map((message: any) => (
                    <div key={message.message_id} className="bg-gray-50 p-3 rounded-lg">
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-medium text-gray-600">
                          {message.role === 'user' ? '👤 User' : '🤖 Assistant'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(message.timestamp * 1000).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{message.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Connection Explorer */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Connection Explorer</h2>
            <p className="text-gray-600 mb-4">Select two conversations to discover their connections</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Source Selection */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Source Conversation</h3>
                {conversationsLoading ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <div className="max-h-60 overflow-y-auto space-y-2">
                    {conversations?.map((chat) => (
                      <div
                        key={chat.chat_id}
                        onClick={() => handleSourceSelect(chat.chat_id)}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedSource === chat.chat_id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="font-medium text-gray-900">{chat.title}</div>
                        <div className="text-sm text-gray-500">
                          {chat.message_count} messages • {new Date(chat.create_time * 1000).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Target Selection */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Target Conversation</h3>
                {conversationsLoading ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <div className="max-h-60 overflow-y-auto space-y-2">
                    {conversations?.map((chat) => (
                      <div
                        key={chat.chat_id}
                        onClick={() => handleTargetSelect(chat.chat_id)}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedTarget === chat.chat_id
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="font-medium text-gray-900">{chat.title}</div>
                        <div className="text-sm text-gray-500">
                          {chat.message_count} messages • {new Date(chat.create_time * 1000).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Connection Explanation */}
            {connectionExplanation && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Connection Analysis</h3>
                <p className="text-blue-800 mb-3">{connectionExplanation.explanation}</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-blue-900">Strength:</span>
                    <span className="ml-2 text-blue-800">
                      {(connectionExplanation.connection_strength * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-blue-900">Type:</span>
                    <span className="ml-2 text-blue-800">{connectionExplanation.relationship_type}</span>
                  </div>
                  <div>
                    <span className="font-medium text-blue-900">Shared Topics:</span>
                    <span className="ml-2 text-blue-800">{connectionExplanation.shared_topics.length}</span>
                  </div>
                </div>
                {connectionExplanation.shared_topics.length > 0 && (
                  <div className="mt-3">
                    <span className="font-medium text-blue-900">Topics:</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {connectionExplanation.shared_topics.map((topic: string) => (
                        <span key={topic} className="px-2 py-1 bg-blue-200 text-blue-800 rounded-full text-xs">
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Cross-Domain Search */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Cross-Domain Search</h2>
            <p className="text-gray-600 mb-4">Find topics that appear across different domains</p>

            <div className="flex gap-4 mb-4">
              <input
                type="text"
                value={crossDomainQuery}
                onChange={(e) => setCrossDomainQuery(e.target.value)}
                placeholder="Enter a topic to search across domains..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && handleCrossDomainSearch()}
              />
              <button
                onClick={handleCrossDomainSearch}
                disabled={!crossDomainQuery.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Search
              </button>
            </div>

            {crossDomainLoading && (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Searching across domains...</p>
              </div>
            )}

            {crossDomainResults && crossDomainResults.length > 0 && (
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Results</h3>
                {crossDomainResults.map((result, index) => (
                  <div
                    key={index}
                    onClick={() => handleResultClick(result)}
                    className="p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-gray-300 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs">
                        {result.domain}
                      </span>
                      <span className="text-sm text-gray-500">
                        {(result.similarity_score * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <p className="text-gray-700">{result.content}</p>
                    {result.tags && result.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {result.tags.slice(0, 3).map((tag: string) => (
                          <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Discovery Suggestions */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Discovery Suggestions</h2>
            <p className="text-gray-600 mb-4">AI-powered suggestions for interesting connections</p>

            {suggestionsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading suggestions...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {suggestions?.map((suggestion, index) => (
                  <div key={index} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        suggestion.type === 'connection' ? 'bg-blue-100 text-blue-800' :
                        suggestion.type === 'topic' ? 'bg-green-100 text-green-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {suggestion.type}
                      </span>
                      <span className="text-sm text-gray-500">
                        {(suggestion.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <h3 className="font-medium text-gray-900 mb-1">{suggestion.title}</h3>
                    <p className="text-gray-600 text-sm">{suggestion.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionDiscovery; 