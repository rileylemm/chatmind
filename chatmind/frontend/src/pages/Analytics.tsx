import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  DollarSign, 
  Activity, 
  Tag,
  Download,
  BarChart3,
  LineChart
} from 'lucide-react';
import { 
  LineChart as RechartsLineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell
} from 'recharts';
import { api } from '../services/api';
import type { CostStatistics, Tag as TagType } from '../types';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Analytics: React.FC = () => {
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [selectedOperation, setSelectedOperation] = useState<string>('all');

  // Fetch cost statistics
  const { data: costStats, isLoading: costLoading } = useQuery({
    queryKey: ['cost-statistics', dateRange, selectedOperation],
    queryFn: async (): Promise<CostStatistics> => {
      const params = new URLSearchParams();
      
      // Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      if (dateRange === '7d') {
        startDate.setDate(endDate.getDate() - 7);
      } else if (dateRange === '30d') {
        startDate.setDate(endDate.getDate() - 30);
      } else if (dateRange === '90d') {
        startDate.setDate(endDate.getDate() - 90);
      }
      
      params.append('start_date', startDate.toISOString().split('T')[0]);
      params.append('end_date', endDate.toISOString().split('T')[0]);
      
      if (selectedOperation !== 'all') {
        params.append('operation', selectedOperation);
      }
      
      const response = await api.get(`/api/costs/statistics?${params.toString()}`);
      return response.data.data;
    },
  });

  // Fetch tags for tag analysis
  const { data: tags, isLoading: tagsLoading } = useQuery({
    queryKey: ['tags'],
    queryFn: async (): Promise<TagType[]> => {
      const response = await api.get('/api/tags');
      return response.data.data || [];
    },
  });

  // Prepare data for charts
  const costByDateData = (costStats as any)?.cost_by_date?.map((item: { date: string; cost: string; calls: number }) => ({
    date: new Date(item.date).toLocaleDateString(),
    cost: parseFloat(item.cost.replace('$', '')),
    calls: item.calls
  })) || [];

  const topTagsData = tags?.slice(0, 10).map((tag, index) => ({
    name: tag.name,
    count: tag.count,
    color: COLORS[index % COLORS.length]
  })) || [];

  const costByOperationData = (costStats as any)?.cost_by_operation ? 
    Object.entries((costStats as any).cost_by_operation).map(([operation, cost]) => ({
      operation,
      cost: parseFloat((cost as string).replace('$', ''))
    })) : [];

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Analytics
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Track usage, costs, and insights from your ChatMind data
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value as '7d' | '30d' | '90d')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
            
            <select
              value={selectedOperation}
              onChange={(e) => setSelectedOperation(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Operations</option>
              <option value="tagging">Tagging</option>
              <option value="embedding">Embedding</option>
              <option value="clustering">Clustering</option>
            </select>
            
            <button className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 p-6 space-y-6">
        {/* Overview cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Cost</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {costLoading ? '...' : `$${(costStats?.total_cost_usd || 0).toFixed(2)}`}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {costLoading ? '...' : costStats?.total_calls?.toLocaleString() || '0'}
                </p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Success Rate</p>
                <p className={`text-2xl font-bold ${getSuccessRateColor(costStats?.success_rate || 0)}`}>
                  {costLoading ? '...' : `${(costStats?.success_rate || 0).toFixed(1)}%`}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-500" />
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Tags</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {tagsLoading ? '...' : tags?.length || '0'}
                </p>
              </div>
              <Tag className="h-8 w-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Charts grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost over time */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Cost Over Time</h3>
              <LineChart className="h-5 w-5 text-gray-400" />
            </div>
            {costLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <RechartsLineChart data={costByDateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`$${value}`, 'Cost']} />
                  <Line type="monotone" dataKey="cost" stroke="#3B82F6" strokeWidth={2} />
                </RechartsLineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Top tags */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Tags</h3>
              <Tag className="h-5 w-5 text-gray-400" />
            </div>
            {tagsLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <RechartsPieChart>
                  <Pie
                    data={topTagsData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {topTagsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </RechartsPieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Cost by operation */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Cost by Operation</h3>
              <BarChart3 className="h-5 w-5 text-gray-400" />
            </div>
            {costLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={costByOperationData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="operation" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`$${value}`, 'Cost']} />
                  <Bar dataKey="cost" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* API calls over time */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">API Calls Over Time</h3>
              <Activity className="h-5 w-5 text-gray-400" />
            </div>
            {costLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <RechartsLineChart data={costByDateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="calls" stroke="#8B5CF6" strokeWidth={2} />
                </RechartsLineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Detailed statistics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Token usage */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Token Usage</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Input Tokens</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {costStats?.total_input_tokens?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Output Tokens</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {costStats?.total_output_tokens?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Total Tokens</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {((costStats?.total_input_tokens || 0) + (costStats?.total_output_tokens || 0)).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Model statistics */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Model Usage</h3>
            <div className="space-y-3">
              {costStats?.model_statistics ? (
                Object.entries(costStats.model_statistics).map(([model, stats]: [string, any]) => (
                  <div key={model} className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">{model}</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {stats.calls || 0} calls
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500 dark:text-gray-400">No model data available</p>
              )}
            </div>
          </div>

          {/* Recent activity */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Processing new data</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Tagging messages</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Updating clusters</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 