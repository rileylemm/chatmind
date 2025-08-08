import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  getAllClusters,
  getClusterDetails,
  getConversationMessages,
  findSimilarContent
} from '../services/api';

interface ClusterDiscoveryProps {}

const ClusterDiscovery: React.FC<ClusterDiscoveryProps> = () => {
  const [selectedCluster, setSelectedCluster] = useState<string>('');
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [minSize, setMinSize] = useState<number>(0);

  // Get all clusters
  const { data: clusters, isLoading: clustersLoading } = useQuery({
    queryKey: ['clusters', minSize],
    queryFn: () => getAllClusters({ 
      limit: 50, 
      min_size: minSize, 
      include_positioning: true 
    }),
  });

  // Get selected cluster details
  const { data: clusterDetails } = useQuery({
    queryKey: ['cluster-details', selectedCluster],
    queryFn: () => getClusterDetails({ cluster_id: selectedCluster }),
    enabled: !!selectedCluster,
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

  const handleClusterClick = (clusterId: string) => {
    setSelectedCluster(clusterId);
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

  const handleChunkClick = (chunkContent: string) => {
    // Create a mock result object for the chunk
    const mockResult = {
      content: chunkContent,
      message_id: `chunk_${Date.now()}`,
      chat_id: selectedCluster,
    };
    handleResultClick(mockResult);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Cluster Discovery</h1>
        <p className="text-gray-600">Explore semantic clusters and discover topic patterns</p>
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
          {/* Controls */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex flex-wrap gap-4 items-center justify-between">
              <div className="flex gap-4 items-center">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Minimum Cluster Size
                  </label>
                  <input
                    type="number"
                    value={minSize}
                    onChange={(e) => setMinSize(parseInt(e.target.value) || 0)}
                    min="0"
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    View Mode
                  </label>
                  <select
                    value={viewMode}
                    onChange={(e) => setViewMode(e.target.value as 'list' | 'grid')}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="list">List View</option>
                    <option value="grid">Grid View</option>
                  </select>
                </div>
              </div>
              <div className="text-sm text-gray-500">
                {clusters ? `${clusters.length} clusters found` : 'Loading...'}
              </div>
            </div>
          </div>

          {/* Clusters List */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Semantic Clusters</h2>
            
            {clustersLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading clusters...</p>
              </div>
            ) : (
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-4'}>
                {clusters?.map((cluster) => (
                  <div
                    key={cluster.cluster_id}
                    onClick={() => handleClusterClick(cluster.cluster_id)}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedCluster === cluster.cluster_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium text-gray-900">{cluster.name}</h3>
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs">
                        {cluster.size} chunks
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{cluster.summary}</p>
                    {cluster.x !== undefined && cluster.y !== undefined && (
                      <div className="text-xs text-gray-500">
                        Position: ({cluster.x.toFixed(2)}, {cluster.y.toFixed(2)})
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Selected Cluster Details */}
          {clusterDetails && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Cluster: {clusterDetails.name}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Summary</h3>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{clusterDetails.summary}</p>
                  
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{clusterDetails.size}</div>
                      <div className="text-sm text-blue-700">Chunks</div>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {clusterDetails.related_clusters.length}
                      </div>
                      <div className="text-sm text-green-700">Related Clusters</div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Sample Content</h3>
                  <div className="max-h-60 overflow-y-auto space-y-2">
                    {clusterDetails.chunk_contents.slice(0, 5).map((content: string, index: number) => (
                      <div
                        key={index}
                        onClick={() => handleChunkClick(content)}
                        className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                      >
                        <p className="text-sm text-gray-700 line-clamp-3">{content}</p>
                        <p className="text-xs text-gray-500 mt-1">Click to view details</p>
                      </div>
                    ))}
                    {clusterDetails.chunk_contents.length > 5 && (
                      <p className="text-xs text-gray-500 text-center">
                        +{clusterDetails.chunk_contents.length - 5} more chunks
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {clusterDetails.related_clusters.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-medium text-gray-900 mb-2">Related Clusters</h3>
                  <div className="flex flex-wrap gap-2">
                    {clusterDetails.related_clusters.map((clusterId: string) => (
                      <span
                        key={clusterId}
                        onClick={() => handleClusterClick(clusterId)}
                        className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm cursor-pointer hover:bg-purple-200 transition-colors"
                      >
                        {clusterId}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ClusterDiscovery; 