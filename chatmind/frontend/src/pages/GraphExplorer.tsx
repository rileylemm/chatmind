import React, { useState } from 'react';
import { GraphView } from '../components/graph/GraphView';
import { Filter, Search, Settings } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import type { GraphNode, GraphEdge } from '../types';

const GraphExplorer: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentView, setCurrentView] = useState<'topics' | 'chats' | 'messages'>('topics');
  const [parentId, setParentId] = useState<string | null>(null);
  const [currentZoom, setCurrentZoom] = useState(1);

  // Fetch real graph data from API
  const { data: graphData, isLoading, error } = useQuery({
    queryKey: ['graph-data', currentView, parentId],
    queryFn: async () => {
      let url = '/graph?limit=500';
      
      if (currentView === 'topics') {
        url += '&node_types=Topic&use_semantic_positioning=true';
      } else if (currentView === 'chats') {
        url += '&node_types=Topic,Chat';
        if (parentId) {
          url += `&parent_id=${parentId}`;
        }
      } else if (currentView === 'messages') {
        url += '&node_types=Topic,Chat,Message';
        if (parentId) {
          url += `&parent_id=${parentId}`;
        }
      }
      
      const response = await api.get(url);
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const allNodes: GraphNode[] = graphData?.nodes || [];
  const allEdges: GraphEdge[] = graphData?.edges || [];
  
  // Filter nodes based on search query
  const nodes = searchQuery 
    ? allNodes.filter(node => 
        (node.properties.title as string)?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (node.properties.name as string)?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (node.properties.sample_titles as string[])?.some((title: string) => 
          title.toLowerCase().includes(searchQuery.toLowerCase())
        )
      )
    : allNodes;
  
  // Filter edges to only include connections between visible nodes
  const nodeIds = new Set(nodes.map(n => n.id));
  const edges = allEdges.filter(edge => 
    nodeIds.has(edge.source) && nodeIds.has(edge.target)
  );

  const handleNodeClick = (node: GraphNode) => {
    console.log('GraphExplorer: Node clicked:', node);
    setSelectedNode(node);
    
    // Handle hierarchical navigation
    if (node.type === 'Topic' && currentView === 'topics') {
      console.log('Navigating to chats for topic:', node.id);
      // Clicking a topic when viewing topics -> show chats for this topic
      setCurrentView('chats');
      setParentId(node.id);
    } else if (node.type === 'Chat' && currentView === 'chats') {
      console.log('Navigating to messages for chat:', node.id);
      // Clicking a chat when viewing chats -> show messages for this chat
      setCurrentView('messages');
      setParentId(node.id);
    }
  };

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Go back to topics
        setCurrentView('topics');
        setParentId(null);
        setSelectedNode(null);
      } else if (event.key === 'Backspace') {
        // Go back one level
        if (currentView === 'messages') {
          setCurrentView('chats');
        } else if (currentView === 'chats') {
          setCurrentView('topics');
          setParentId(null);
        }
        setSelectedNode(null);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentView]);

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Page header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Graph Explorer
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Explore your knowledge graph interactively
          </p>
          {graphData && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Showing {nodes.length} nodes and {edges.length} edges
            </p>
          )}
          
          {/* Breadcrumb navigation */}
          <div className="flex items-center space-x-2 mt-2">
            <button
              onClick={() => {
                setCurrentView('topics');
                setParentId(null);
                setSelectedNode(null);
              }}
              className={`text-xs px-2 py-1 rounded ${
                currentView === 'topics' 
                  ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' 
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              Topics
            </button>
            {currentView !== 'topics' && (
              <>
                <span className="text-gray-400">→</span>
                <button
                  onClick={() => {
                    setCurrentView('chats');
                    setParentId(null);
                    setSelectedNode(null);
                  }}
                  className={`text-xs px-2 py-1 rounded ${
                    currentView === 'chats' 
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' 
                      : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                  }`}
                >
                  Chats
                </button>
              </>
            )}
            {currentView === 'messages' && (
              <>
                <span className="text-gray-400">→</span>
                <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  Messages
                </span>
              </>
            )}
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm w-64"
            />
          </div>
          
          <button className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </button>
          
          <button className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </button>
          
          {/* Navigation Controls */}
          {currentView !== 'topics' && (
            <button
              onClick={() => {
                setCurrentView('topics');
                setParentId(null);
                setSelectedNode(null);
              }}
              className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              ← Back to Topics
            </button>
          )}
          
          {/* Semantic positioning info */}
          {currentView === 'topics' && (
            <div className="text-xs text-gray-500 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded">
              🧠 Semantic positioning enabled
            </div>
          )}
          
          {/* Zoom info */}
          <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded">
            Zoom: {Math.round(currentZoom * 100)}%
          </div>
          
          {/* Help tooltip */}
          <div className="text-xs text-gray-500 dark:text-gray-400 bg-yellow-50 dark:bg-yellow-900/20 px-2 py-1 rounded">
            ⌨️ Esc: Topics | ←: Back
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex">
                            {/* Graph canvas */}
                    <div className="flex-1 p-6 relative">
                      <div className="h-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
                        
                        {/* Tooltip */}
                        {hoveredNode && (
                          <div 
                            className="absolute z-10 bg-gray-900 text-white p-3 rounded-lg shadow-lg text-sm max-w-xs"
                            style={{
                              left: '50%',
                              top: '20px',
                              transform: 'translateX(-50%)'
                            }}
                          >
                            <div className="font-semibold mb-1">{hoveredNode.properties.title || hoveredNode.id}</div>
                            {hoveredNode.type === 'Topic' && (
                              <div className="space-y-1 text-xs">
                                <div>Chats: {(hoveredNode.properties.chat_count as number) || 0}</div>
                                <div>Messages: {(hoveredNode.properties.message_count as number) || 0}</div>
                                {(hoveredNode.properties.last_active as number) && (
                                  <div>Last active: {new Date((hoveredNode.properties.last_active as number) * 1000).toLocaleDateString()}</div>
                                )}
                              </div>
                            )}
                            {hoveredNode.type === 'Chat' && (
                              <div className="text-xs">
                                Messages: {(hoveredNode.properties.message_count as number) || 0}
                              </div>
                            )}
                          </div>
                        )}
            {isLoading ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                  <p className="text-gray-600 dark:text-gray-400">Loading graph data...</p>
                </div>
              </div>
            ) : error ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <p className="text-red-600 dark:text-red-400 mb-2">Error loading graph data</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Please check your API connection</p>
                </div>
              </div>
            ) : (
              <GraphView
                nodes={nodes}
                edges={edges}
                width={800}
                height={600}
                onNodeClick={handleNodeClick}
                onNodeHover={setHoveredNode}
                onZoomChange={setCurrentZoom}
              />
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 space-y-6">
          {/* Node details */}
          {selectedNode ? (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Node Details
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Type
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {selectedNode.type}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    ID
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white font-mono">
                    {selectedNode.id}
                  </p>
                </div>
                {selectedNode.properties.title && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Title
                    </label>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {selectedNode.properties.title}
                    </p>
                  </div>
                )}
                {selectedNode.properties.size && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Size
                    </label>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {selectedNode.properties.size}
                    </p>
                  </div>
                )}
                {typeof selectedNode.properties.message_count === 'number' && selectedNode.properties.message_count > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Messages
                    </label>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {selectedNode.properties.message_count}
                    </p>
                  </div>
                )}
                {selectedNode.properties.top_words && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Top Words
                    </label>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {Array.isArray(selectedNode.properties.top_words) 
                        ? selectedNode.properties.top_words.join(', ')
                        : selectedNode.properties.top_words}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Node Details
              </h3>
              <div className="text-center py-8">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
                  <Search className="h-8 w-8 text-gray-400" />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Select a node to view details
                </p>
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Legend
            </h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-700 dark:text-gray-300">Chat</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-700 dark:text-gray-300">Topic</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-4 h-4 bg-purple-500 rounded-full"></div>
                <span className="text-sm text-gray-700 dark:text-gray-300">Message</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphExplorer; 