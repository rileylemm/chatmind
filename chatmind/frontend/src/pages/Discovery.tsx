import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  TrendingDown, 
  Brain, 
  Globe, 
  Target, 
  Search,
  ArrowUpRight,
  Sparkles,
  Lightbulb
} from 'lucide-react';
import { 
  discoverTopics, 
  discoverDomains, 
  discoverClusters 
} from '../services/api';

const Discovery: React.FC = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
  const [selectedDomain] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch discovered topics
  const { data: topicsData, isLoading: topicsLoading } = useQuery({
    queryKey: ['discovered-topics', selectedTimeframe, selectedDomain],
    queryFn: () => discoverTopics({ 
      limit: 20, 
      min_count: 1,
      domain: selectedDomain === 'all' ? undefined : selectedDomain 
    }),
    refetchInterval: 60000,
  });

  // Fetch domain insights
  const { data: domainsData, isLoading: domainsLoading } = useQuery({
    queryKey: ['discovered-domains'],
    queryFn: discoverDomains,
    refetchInterval: 120000,
  });

  // Fetch clusters
  const { data: clustersData, isLoading: clustersLoading } = useQuery({
    queryKey: ['discovered-clusters', selectedTimeframe],
    queryFn: () => discoverClusters({ 
      limit: 15, 
      min_size: 2,
      include_positioning: true 
    }),
    refetchInterval: 120000,
  });

  // Filter topics based on search
  const filteredTopics = topicsData?.filter(topic => 
    topic.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
    topic.domain.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // Filter clusters based on search
  const filteredClusters = clustersData?.filter(cluster => 
    cluster.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    cluster.summary.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Lightbulb className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Discovery
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                Explore trending topics, domains, and knowledge clusters
              </p>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search topics, domains, or clusters..."
                className="block w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg leading-5 bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div className="flex space-x-2">
              {['daily', 'weekly', 'monthly'].map((timeframe) => (
                <button
                  key={timeframe}
                                     onClick={() => setSelectedTimeframe(timeframe as 'daily' | 'weekly' | 'monthly')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg border ${
                    selectedTimeframe === timeframe
                      ? 'bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-700'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'
                  }`}
                >
                  {timeframe.charAt(0).toUpperCase() + timeframe.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <Brain className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Topics</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {topicsLoading ? '...' : topicsData?.length || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center">
                  <Globe className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Domains</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {domainsLoading ? '...' : domainsData?.length || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Target className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Clusters</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {clustersLoading ? '...' : clustersData?.length || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Trending</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {topicsLoading ? '...' : topicsData?.filter(t => t.trend === 'rising').length || 0}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Trending Topics */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Trending Topics
                </h3>
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-4 w-4 text-purple-500" />
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {filteredTopics.length} topics
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6">
              {topicsLoading ? (
                <div className="space-y-4">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredTopics.slice(0, 8).map((topic, index) => (
                    <div key={topic.topic} className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                          <span className="text-white text-sm font-medium">
                            {index + 1}
                          </span>
                        </div>
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {topic.topic}
                          </h4>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {topic.count} conversations • {topic.domain}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          topic.trend === 'rising' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                        }`}>
                          {topic.trend === 'rising' ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                          {topic.trend}
                        </span>
                        <ArrowUpRight className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Knowledge Clusters */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Knowledge Clusters
                </h3>
                <div className="flex items-center space-x-2">
                  <Target className="h-4 w-4 text-purple-500" />
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {filteredClusters.length} clusters
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6">
              {clustersLoading ? (
                <div className="space-y-4">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredClusters.slice(0, 6).map((cluster) => (
                    <div key={cluster.cluster_id} className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                          {cluster.name}
                        </h4>
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                          {cluster.size} items
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">
                        {cluster.summary}
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {cluster.common_tags?.slice(0, 3).map((tag) => (
                          <span key={tag} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                            {tag}
                          </span>
                        ))}
                        {cluster.common_tags && cluster.common_tags.length > 3 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                            +{cluster.common_tags.length - 3}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Domain Insights */}
        <div className="mt-8">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Domain Insights
              </h3>
            </div>
            <div className="p-6">
              {domainsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {domainsData?.map((domain) => (
                    <div key={domain.domain} className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                          {domain.domain}
                        </h4>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">
                          {domain.percentage.toFixed(1)}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                        {domain.count} conversations
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500 dark:text-gray-400">Positive</span>
                          <span className="text-green-600 dark:text-green-400">
                            {domain.sentiment_distribution.positive}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500 dark:text-gray-400">Neutral</span>
                          <span className="text-yellow-600 dark:text-yellow-400">
                            {domain.sentiment_distribution.neutral}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500 dark:text-gray-400">Negative</span>
                          <span className="text-red-600 dark:text-red-400">
                            {domain.sentiment_distribution.negative}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Discovery; 