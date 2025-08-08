import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  getTimelineWithInsights,
  getConversationMessages,
  findSimilarContent
} from '../services/api';

interface TimelineDiscoveryProps {}

const TimelineDiscovery: React.FC<TimelineDiscoveryProps> = () => {
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Get timeline with insights
  const { data: timelineItems, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline-insights', startDate, endDate],
    queryFn: () => getTimelineWithInsights({ 
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      limit: 20 
    }),
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

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Check if we have meaningful date ranges
  const hasMeaningfulDates = timelineItems && timelineItems.length > 0 && 
    timelineItems.some(item => (item.original_timestamp && item.original_timestamp > 0) || (item.timestamp && item.timestamp > 0));

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Timeline Discovery</h1>
        <p className="text-gray-600">Explore conversations over time with AI-generated insights</p>
      </div>

      {showDetails && selectedResult ? (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Result Details</h2>
            <button
              onClick={handleBackToResults}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              ← Back to Timeline
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Content</h3>
              <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{selectedResult.content}</p>
            </div>

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
          {/* Date Filters */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Timeline Filters</h2>
            {hasMeaningfulDates ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    onClick={() => {
                      setStartDate('');
                      setEndDate('');
                    }}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <span className="text-yellow-600">⚠️</span>
                  <div>
                    <h4 className="text-sm font-medium text-yellow-800 mb-1">Limited Date Information</h4>
                    <p className="text-sm text-yellow-700">
                      Your conversations don't have detailed timestamp information. The timeline will show conversations in discovery order.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Conversation Timeline</h2>
            
            {timelineLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading timeline...</p>
              </div>
            ) : (
              <div className="space-y-6">
                {timelineItems?.map((item, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-6 relative">
                    {/* Timeline dot */}
                    <div className="absolute -left-3 top-0 w-6 h-6 bg-blue-500 rounded-full border-4 border-white"></div>
                    
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="font-medium text-gray-900">{item.title}</h3>
                          <p className="text-sm text-gray-500">
                            {item.original_timestamp ? formatDate(item.original_timestamp) : formatDate(item.timestamp)}
                          </p>
                        </div>
                        <button
                          onClick={() => handleResultClick(item)}
                          className="px-3 py-1 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                        >
                          View Details
                        </button>
                      </div>

                      {/* Topics */}
                      {item.topics && item.topics.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-gray-700 mb-1">Topics</h4>
                          <div className="flex flex-wrap gap-1">
                            {item.topics.slice(0, 5).map((topic: string, topicIndex: number) => (
                              <span key={topicIndex} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                                {topic}
                              </span>
                            ))}
                            {item.topics.length > 5 && (
                              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                                +{item.topics.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Semantic Connections */}
                      {item.semantic_connections && item.semantic_connections.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-gray-700 mb-1">Semantic Connections</h4>
                          <div className="flex flex-wrap gap-1">
                            {item.semantic_connections.slice(0, 3).map((connection: string, connIndex: number) => (
                              <span key={connIndex} className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                                {connection}
                              </span>
                            ))}
                            {item.semantic_connections.length > 3 && (
                              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                                +{item.semantic_connections.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* AI Insight */}
                      {item.insight && (
                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <div className="flex items-start gap-2">
                            <span className="text-yellow-600">💡</span>
                            <div>
                              <h4 className="text-sm font-medium text-yellow-800 mb-1">AI Insight</h4>
                              <p className="text-sm text-yellow-700">{item.insight}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {timelineItems && timelineItems.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No timeline items found for the selected date range.</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Timeline Statistics */}
          {timelineItems && timelineItems.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Timeline Statistics</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{timelineItems.length}</div>
                  <div className="text-sm text-blue-700">Total Conversations</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {timelineItems.filter(item => item.topics && item.topics.length > 0).length}
                  </div>
                  <div className="text-sm text-green-700">With Topics</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {timelineItems.filter(item => item.semantic_connections && item.semantic_connections.length > 0).length}
                  </div>
                  <div className="text-sm text-purple-700">With Connections</div>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {timelineItems.filter(item => item.insight).length}
                  </div>
                  <div className="text-sm text-orange-700">With Insights</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TimelineDiscovery; 