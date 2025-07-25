import React, { useState } from 'react';
import { GraphView } from '../components/graph/GraphView';
import { Filter, Search, Settings } from 'lucide-react';
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
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Graph canvas */}
        <div className="flex-1 p-6">
          <div className="h-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
            <GraphView
              nodes={mockNodes}
              edges={mockEdges}
              width={800}
              height={600}
            />
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
                <span className="text-sm text-gray-700 dark:text-gray-300">Tag</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphExplorer; 