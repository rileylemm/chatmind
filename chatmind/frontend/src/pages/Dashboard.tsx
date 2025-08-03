import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  MessageSquare, 
  Network, 
  TrendingUp,
  Activity,
  ArrowUpRight,
  BarChart3,
  Search,
  Brain,
  Target,
  Zap,
  Lightbulb,
  TrendingDown
} from 'lucide-react';
import { 
  getDashboardStats, 
  discoverTopics, 
  discoverDomains, 
  analyzePatterns
} from '../services/api';

const Dashboard: React.FC = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch dashboard stats
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    refetchInterval: 30000,
  }) as { data: Record<string, unknown>; isLoading: boolean };

  // Fetch discovered topics
  const { data: topicsData, isLoading: topicsLoading } = useQuery({
    queryKey: ['discovered-topics', selectedTimeframe],
    queryFn: () => discoverTopics({ limit: 8, min_count: 2 }),
    refetchInterval: 60000,
  });

  // Fetch domain insights
  const { data: domainsData, isLoading: domainsLoading } = useQuery({
    queryKey: ['discovered-domains'],
    queryFn: discoverDomains,
    refetchInterval: 120000,
  });

  // Fetch pattern analytics
  const { data: patternsData, isLoading: patternsLoading } = useQuery({
    queryKey: ['analytics-patterns', selectedTimeframe],
    queryFn: () => analyzePatterns({ timeframe: selectedTimeframe, include_sentiment: true }),
    refetchInterval: 60000,
  });

  // Fetch graph overview (commented out for now)
  // const { data: graphData, isLoading: graphLoading } = useQuery({
  //   queryKey: ['graph-overview'],
  //   queryFn: () => getGraphVisualization({ limit: 50, include_edges: false }),
  //   refetchInterval: 120000,
  // });

  // Handle semantic search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    // Navigate to search results page with query
    window.location.href = `/search?q=${encodeURIComponent(searchQuery)}`;
  };

  const stats = [
    {
      name: 'Total Chats',
      value: statsLoading ? '...' : (statsData?.total_chats?.toLocaleString() || '0'),
      icon: MessageSquare,
      gradient: 'from-blue-500 to-blue-600',
      bgGradient: 'from-blue-50 to-blue-100',
      darkBgGradient: 'from-blue-900/20 to-blue-800/20',
      change: '+12%',
      changeType: 'positive' as const,
    },
    {
      name: 'Total Messages',
      value: statsLoading ? '...' : (statsData?.total_messages?.toLocaleString() || '0'),
      icon: Network,
      gradient: 'from-emerald-500 to-emerald-600',
      bgGradient: 'from-emerald-50 to-emerald-100',
      darkBgGradient: 'from-emerald-900/20 to-emerald-800/20',
      change: '+8%',
      changeType: 'positive' as const,
    },
    {
      name: 'Knowledge Topics',
      value: statsLoading ? '...' : (statsData?.total_topics?.toLocaleString() || '0'),
      icon: Brain,
      gradient: 'from-purple-500 to-purple-600',
      bgGradient: 'from-purple-50 to-purple-100',
      darkBgGradient: 'from-purple-900/20 to-purple-800/20',
      change: '+15%',
      changeType: 'positive' as const,
    },
    {
      name: 'Total Cost',
      value: statsLoading ? '...' : (statsData?.total_cost || '$0.00'),
      icon: TrendingUp,
      gradient: 'from-amber-500 to-amber-600',
      bgGradient: 'from-amber-50 to-amber-100',
      darkBgGradient: 'from-amber-900/20 to-amber-800/20',
      change: '-5%',
      changeType: 'negative' as const,
    },
  ];

  const quickActions = [
    {
      name: 'Explore Knowledge Graph',
      description: 'Visualize connections and relationships',
      icon: Network,
      href: '/graph',
      gradient: 'from-blue-500 to-indigo-600',
      bgGradient: 'from-blue-50 to-indigo-100',
      darkBgGradient: 'from-blue-900/20 to-indigo-800/20',
    },
    {
      name: 'Discover Topics',
      description: 'Find trending topics and insights',
      icon: Lightbulb,
      href: '/discover',
      gradient: 'from-yellow-500 to-orange-600',
      bgGradient: 'from-yellow-50 to-orange-100',
      darkBgGradient: 'from-yellow-900/20 to-orange-800/20',
    },
    {
      name: 'Advanced Search',
      description: 'Semantic search across all content',
      icon: Search,
      href: '/search',
      gradient: 'from-emerald-500 to-teal-600',
      bgGradient: 'from-emerald-50 to-teal-100',
      darkBgGradient: 'from-emerald-900/20 to-teal-800/20',
    },
    {
      name: 'Analytics Dashboard',
      description: 'Deep insights and patterns',
      icon: BarChart3,
      href: '/analytics',
      gradient: 'from-purple-500 to-pink-600',
      bgGradient: 'from-purple-50 to-pink-100',
      darkBgGradient: 'from-purple-900/20 to-pink-800/20',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome to ChatMind
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Your AI-powered knowledge graph with {statsData?.total_chats?.toLocaleString() || '0'} conversations and {statsData?.total_messages?.toLocaleString() || '0'} messages
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative max-w-2xl">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search conversations, topics, or insights..."
              className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg leading-5 bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <div className="absolute inset-y-0 right-0 flex items-center">
              <button
                onClick={handleSearch}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Search
              </button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <div
              key={stat.name}
              className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg"
            >
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className={`inline-flex items-center justify-center h-12 w-12 rounded-lg bg-gradient-to-r ${stat.bgGradient} dark:bg-gradient-to-r ${stat.darkBgGradient}`}>
                      <stat.icon className={`h-6 w-6 text-white`} />
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        {stat.name}
                      </dt>
                      <dd className="flex items-baseline">
                                                 <div className="text-2xl font-semibold text-gray-900 dark:text-white">
                           {String(stat.value)}
                         </div>
                        <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                          stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {stat.change}
                        </div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Quick Actions
                </h3>
              </div>
              <div className="p-6 space-y-4">
                {quickActions.map((action) => (
                  <Link
                    key={action.name}
                    to={action.href}
                    className="block p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors duration-200"
                  >
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 inline-flex items-center justify-center h-10 w-10 rounded-lg bg-gradient-to-r ${action.bgGradient} dark:bg-gradient-to-r ${action.darkBgGradient}`}>
                        <action.icon className="h-5 w-5 text-white" />
                      </div>
                      <div className="ml-4">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                          {action.name}
                        </h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {action.description}
                        </p>
                      </div>
                      <div className="ml-auto">
                        <ArrowUpRight className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Trending Topics */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    Trending Topics
                  </h3>
                  <div className="flex space-x-2">
                    {['daily', 'weekly', 'monthly'].map((timeframe) => (
                      <button
                        key={timeframe}
                        onClick={() => setSelectedTimeframe(timeframe as any)}
                        className={`px-3 py-1 text-xs font-medium rounded-md ${
                          selectedTimeframe === timeframe
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                            : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                        }`}
                      >
                        {timeframe.charAt(0).toUpperCase() + timeframe.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="p-6">
                {topicsLoading ? (
                  <div className="space-y-3">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="animate-pulse">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {topicsData?.slice(0, 6).map((topic, index) => (
                      <div key={topic.topic} className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200">
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
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Additional Insights Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          {/* Domain Insights */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Domain Insights
              </h3>
            </div>
            <div className="p-6">
              {domainsLoading ? (
                <div className="space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {domainsData?.slice(0, 4).map((domain) => (
                    <div key={domain.domain} className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                          {domain.domain}
                        </h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {domain.count} conversations ({domain.percentage.toFixed(1)}%)
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {domain.sentiment_distribution.positive + domain.sentiment_distribution.neutral + domain.sentiment_distribution.negative}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Activity Overview */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Activity Overview
              </h3>
            </div>
            <div className="p-6">
              {patternsLoading ? (
                <div className="space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Activity className="h-4 w-4 text-blue-500 mr-2" />
                      <span className="text-sm text-gray-900 dark:text-white">Conversation Frequency</span>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {patternsData?.conversation_frequency?.length || 0} days
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Brain className="h-4 w-4 text-purple-500 mr-2" />
                      <span className="text-sm text-gray-900 dark:text-white">Topic Evolution</span>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {patternsData?.topic_evolution?.length || 0} trends
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Zap className="h-4 w-4 text-yellow-500 mr-2" />
                      <span className="text-sm text-gray-900 dark:text-white">Sentiment Analysis</span>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {patternsData?.sentiment_trends ? 
                        `${patternsData.sentiment_trends.positive + patternsData.sentiment_trends.neutral + patternsData.sentiment_trends.negative} analyzed` : 
                        '0 analyzed'
                      }
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Target className="h-4 w-4 text-green-500 mr-2" />
                      <span className="text-sm text-gray-900 dark:text-white">Complexity Distribution</span>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {patternsData?.complexity_distribution ? 
                        `${patternsData.complexity_distribution.beginner + patternsData.complexity_distribution.intermediate + patternsData.complexity_distribution.advanced} levels` : 
                        '0 levels'
                      }
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 