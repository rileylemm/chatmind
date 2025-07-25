import React from 'react';
import { Link } from 'react-router-dom';
import { 
  MessageSquare, 
  Network, 
  Tag, 
  TrendingUp,
  Activity,
  ArrowUpRight,
  BarChart3,
  Search,
  Filter,
  Sparkles
} from 'lucide-react';

const Dashboard: React.FC = () => {
  // Mock data - will be replaced with real API calls
  const stats = [
    {
      name: 'Total Chats',
      value: '1,718',
      change: '+12%',
      changeType: 'positive',
      icon: MessageSquare,
      gradient: 'from-blue-500 to-blue-600',
      bgGradient: 'from-blue-50 to-blue-100',
      darkBgGradient: 'from-blue-900/20 to-blue-800/20',
    },
    {
      name: 'Total Messages',
      value: '34,106',
      change: '+8%',
      changeType: 'positive',
      icon: Network,
      gradient: 'from-emerald-500 to-emerald-600',
      bgGradient: 'from-emerald-50 to-emerald-100',
      darkBgGradient: 'from-emerald-900/20 to-emerald-800/20',
    },
    {
      name: 'Active Tags',
      value: '755',
      change: '+5%',
      changeType: 'positive',
      icon: Tag,
      gradient: 'from-slate-500 to-slate-600',
      bgGradient: 'from-slate-50 to-slate-100',
      darkBgGradient: 'from-slate-900/20 to-slate-800/20',
    },
    {
      name: 'Total Cost',
      value: '$24.50',
      change: '+15%',
      changeType: 'negative',
      icon: TrendingUp,
      gradient: 'from-amber-500 to-amber-600',
      bgGradient: 'from-amber-50 to-amber-100',
      darkBgGradient: 'from-amber-900/20 to-amber-800/20',
    },
  ];

  const recentActivity = [
    {
      id: 1,
      type: 'chat',
      title: 'Python Web Development Discussion',
      subtitle: '15 messages added',
      timestamp: '2 hours ago',
      icon: MessageSquare,
      gradient: 'from-blue-500 to-blue-600',
      bgGradient: 'from-blue-100 to-blue-200',
      darkBgGradient: 'from-blue-900/30 to-blue-800/30',
    },
    {
      id: 2,
      type: 'message',
      title: 'Added 15 new messages',
      subtitle: 'Auto-processed and tagged',
      timestamp: '4 hours ago',
      icon: Activity,
      gradient: 'from-emerald-500 to-emerald-600',
      bgGradient: 'from-emerald-100 to-emerald-200',
      darkBgGradient: 'from-emerald-900/30 to-emerald-800/30',
    },
    {
      id: 3,
      type: 'tag',
      title: 'Auto-tagged 23 messages',
      subtitle: 'New tags discovered',
      timestamp: '6 hours ago',
      icon: Tag,
      gradient: 'from-slate-500 to-slate-600',
      bgGradient: 'from-slate-100 to-slate-200',
      darkBgGradient: 'from-slate-900/30 to-slate-800/30',
    },
  ];

  const quickActions = [
    {
      name: 'Explore Graph',
      description: 'Visualize your knowledge network',
      icon: Network,
      href: '/graph',
      gradient: 'from-blue-500 to-blue-600',
    },
    {
      name: 'Browse Messages',
      description: 'Search and filter conversations',
      icon: MessageSquare,
      href: '/messages',
      gradient: 'from-emerald-500 to-emerald-600',
    },
    {
      name: 'View Analytics',
      description: 'Track usage and insights',
      icon: BarChart3,
      href: '/analytics',
      gradient: 'from-slate-500 to-slate-600',
    },
    {
      name: 'Manage Tags',
      description: 'Organize your knowledge',
      icon: Tag,
      href: '/tags',
      gradient: 'from-amber-500 to-amber-600',
    },
  ];

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Page header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-blue-500 to-blue-600 opacity-5"></div>
        <div className="relative flex items-center justify-between p-8">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  Dashboard
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400">
                  Welcome back! Here's what's happening with your knowledge graph.
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search anything..."
                className="pl-12 pr-4 py-3 border-0 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-gray-800 text-sm w-80 shadow-lg"
              />
            </div>
            <button className="px-4 py-3 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-0 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:-translate-y-0.5 text-sm font-medium text-gray-700 dark:text-gray-300">
              <Filter className="h-4 w-4 mr-2 inline" />
              Filters
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 p-8 space-y-8">
        {/* Stats grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <div
              key={stat.name}
              className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200/50 dark:border-gray-700/50 p-6 hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 backdrop-blur-sm"
            >
              <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300 from-transparent via-white/5 to-transparent"></div>
              <div className="relative flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                    {stat.name}
                  </p>
                  <p className="text-4xl font-bold text-gray-900 dark:text-white mb-3">
                    {stat.value}
                  </p>
                  <div className="flex items-center">
                    <span
                      className={`text-sm font-semibold ${
                        stat.changeType === 'positive'
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {stat.change}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                      from last month
                    </span>
                  </div>
                </div>
                <div className={`p-4 rounded-2xl bg-gradient-to-br ${stat.bgGradient} dark:${stat.darkBgGradient} shadow-lg`}>
                  <stat.icon className="h-8 w-8 text-gray-700 dark:text-gray-300" />
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent activity */}
          <div className="lg:col-span-2">
            <div className="rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 p-6 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  Recent Activity
                </h3>
                <button className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold hover:underline">
                  View all
                </button>
              </div>
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="group flex items-center space-x-4 p-4 rounded-xl hover:bg-gradient-to-r hover:from-gray-50 hover:to-gray-100 dark:hover:from-gray-700/50 dark:hover:to-gray-600/50 transition-all duration-200 hover:shadow-lg"
                  >
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${activity.bgGradient} dark:${activity.darkBgGradient} shadow-md`}>
                      <activity.icon className="h-6 w-6 text-gray-700 dark:text-gray-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {activity.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.subtitle}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.timestamp}
                      </span>
                      <ArrowUpRight className="h-4 w-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quick actions */}
          <div className="space-y-6">
            <div className="rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 p-6 shadow-xl">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                Quick Actions
              </h3>
              <div className="space-y-4">
                {quickActions.map((action) => (
                  <Link
                    key={action.name}
                    to={action.href}
                    className="w-full flex items-center space-x-4 p-4 rounded-xl bg-gradient-to-r from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200/50 dark:border-gray-700/50 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
                  >
                    <div className={`p-3 rounded-xl bg-gradient-to-r ${action.gradient} shadow-lg`}>
                      <action.icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {action.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {action.description}
                      </p>
                    </div>
                    <ArrowUpRight className="h-5 w-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
                  </Link>
                ))}
              </div>
            </div>
            
            {/* System status */}
            <div className="rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 p-6 shadow-xl">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                System Status
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Processing</span>
                  </div>
                  <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">Active</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Neo4j</span>
                  </div>
                  <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">Connected</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">API</span>
                  </div>
                  <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">Online</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 