import React from 'react';
import { 
  MessageSquare, 
  Network, 
  Tag, 
  TrendingUp,
  Activity
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
    },
    {
      name: 'Total Messages',
      value: '34,106',
      change: '+8%',
      changeType: 'positive',
      icon: Network,
    },
    {
      name: 'Active Tags',
      value: '755',
      change: '+5%',
      changeType: 'positive',
      icon: Tag,
    },
    {
      name: 'Total Cost',
      value: '$24.50',
      change: '+15%',
      changeType: 'negative',
      icon: TrendingUp,
    },
  ];

  const recentActivity = [
    {
      id: 1,
      type: 'chat',
      title: 'Python Web Development Discussion',
      timestamp: '2 hours ago',
      icon: MessageSquare,
    },
    {
      id: 2,
      type: 'message',
      title: 'Added 15 new messages',
      timestamp: '4 hours ago',
      icon: Activity,
    },
    {
      id: 3,
      type: 'tag',
      title: 'Auto-tagged 23 messages',
      timestamp: '6 hours ago',
      icon: Tag,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Overview of your ChatMind knowledge graph
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="card hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.name}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stat.value}
                </p>
              </div>
              <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-lg">
                <stat.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              </div>
            </div>
            <div className="mt-4 flex items-center">
              <span
                className={`text-sm font-medium ${
                  stat.changeType === 'positive'
                    ? 'text-success'
                    : 'text-error'
                }`}
              >
                {stat.change}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                from last month
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Activity
          </h3>
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div
                key={activity.id}
                className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <activity.icon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {activity.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {activity.timestamp}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h3>
          <div className="space-y-3">
            <button className="w-full btn btn-primary">
              Explore Graph
            </button>
            <button className="w-full btn btn-secondary">
              Browse Messages
            </button>
            <button className="w-full btn btn-secondary">
              View Analytics
            </button>
            <button className="w-full btn btn-secondary">
              Manage Tags
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 