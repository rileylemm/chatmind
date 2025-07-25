import React, { useState } from 'react';
import { GraphView } from '../components/graph/GraphView';
import { Filter, Search, ZoomIn, ZoomOut, RotateCcw, Settings } from 'lucide-react';
import type { GraphNode, GraphEdge } from '../types';

const GraphExplorer: React.FC = () => {
  const [selectedNode] = useState<GraphNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Mock data for testing
  const mockNodes: GraphNode[] = [
    {
      id: 'chat-1',
      type: 'Chat',
      properties: {
        title: 'Python Web Development',
        size: 15,
        message_count: 45,
      },
    },
    {
      id: 'chat-2',
      type: 'Chat',
      properties: {
        title: 'React Best Practices',
        size: 12,
        message_count: 32,
      },
    },
    {
      id: 'topic-1',
      type: 'Topic',
      properties: {
        title: 'API Design',
        size: 8,
        top_words: ['api', 'design', 'rest'],
      },
    },
    {
      id: 'tag-1',
      type: 'Tag',
      properties: {
        title: '#python',
        size: 6,
      },
    },
    {
      id: 'tag-2',
      type: 'Tag',
      properties: {
        title: '#react',
        size: 4,
      },
    },
  ];

  const mockEdges: GraphEdge[] = [
    {
      source: 'chat-1',
      target: 'topic-1',
      type: 'HAS_TOPIC',
      properties: { weight: 0.8 },
    },
    {
      source: 'chat-1',
      target: 'tag-1',
      type: 'RELATED_TO',
      properties: { weight: 0.9 },
    },
    {
      source: 'chat-2',
      target: 'tag-2',
      type: 'RELATED_TO',
      properties: { weight: 0.7 },
    },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Page header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Graph Explorer
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Explore your knowledge graph interactively
          </p>
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
              className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm w-64"
            />
          </div>
          
          <button className="btn btn-secondary text-sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </button>
          
          <button className="btn btn-secondary text-sm">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Graph canvas */}
        <div className="flex-1 p-6">
          <div className="h-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <GraphView
              nodes={mockNodes}
              edges={mockEdges}
              width={800}
              height={600}
            />
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80 border-l border-gray-200 dark:border-gray-700 p-6 space-y-6">
          {/* Node details */}
          {selectedNode ? (
            <div className="card">
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
                    Title
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {selectedNode.properties.title}
                  </p>
                </div>
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
              </div>
            </div>
          ) : (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Node Details
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Select a node to view details
              </p>
            </div>
          )}

          {/* Graph stats */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Graph Stats
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Total Nodes</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockNodes.length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Total Edges</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockEdges.length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Chats</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockNodes.filter(n => n.type === 'Chat').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Topics</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockNodes.filter(n => n.type === 'Topic').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Tags</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockNodes.filter(n => n.type === 'Tag').length}
                </span>
              </div>
            </div>
          </div>

          {/* Quick actions */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <button className="w-full btn btn-secondary text-sm">
                <ZoomIn className="h-4 w-4 mr-2" />
                Zoom In
              </button>
              <button className="w-full btn btn-secondary text-sm">
                <ZoomOut className="h-4 w-4 mr-2" />
                Zoom Out
              </button>
              <button className="w-full btn btn-secondary text-sm">
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset View
              </button>
            </div>
          </div>

          {/* Legend */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Legend
            </h3>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Chats</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Messages</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Topics</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Tags</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphExplorer; 