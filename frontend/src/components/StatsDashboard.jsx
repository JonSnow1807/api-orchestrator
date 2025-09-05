import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import {
  TrendingUp,
  Package,
  CheckCircle,
  XCircle,
  Clock,
  FileCode,
  Users,
  Activity,
  Zap,
  BarChart3,
  PieChart,
  RefreshCw
} from 'lucide-react';

const StatsDashboard = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('week');

  useEffect(() => {
    fetchStats();
  }, [timeRange]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `http://localhost:8000/api/projects/stats/overview?range=${timeRange}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
      // Set default stats if API fails
      setStats({
        total_projects: 0,
        total_tasks: 0,
        successful_tasks: 0,
        failed_tasks: 0,
        pending_tasks: 0,
        total_apis_discovered: 0,
        total_tests_generated: 0,
        total_mock_servers: 0,
        average_task_duration: 0,
        recent_activity: []
      });
    } finally {
      setLoading(false);
    }
  };

  const calculateSuccessRate = () => {
    if (!stats || stats.total_tasks === 0) return 0;
    return Math.round((stats.successful_tasks / stats.total_tasks) * 100);
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  const StatCard = ({ icon: Icon, label, value, color, trend }) => (
    <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <div className={`flex items-center text-sm ${
            trend > 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
      <h3 className="text-2xl font-bold text-gray-800">{value}</h3>
      <p className="text-sm text-gray-600 mt-1">{label}</p>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Activity className="w-12 h-12 text-blue-500 animate-pulse mx-auto mb-3" />
          <p className="text-gray-600">Loading statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Statistics Overview</h2>
            <p className="text-gray-600 mt-1">Track your API orchestration metrics</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Time Range Selector */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="day">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="year">This Year</option>
              <option value="all">All Time</option>
            </select>
            <button
              onClick={fetchStats}
              className="p-2 text-gray-500 hover:text-blue-600 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Package}
          label="Total Projects"
          value={stats?.total_projects || 0}
          color="bg-blue-500"
          trend={stats?.projects_trend}
        />
        <StatCard
          icon={Zap}
          label="Total Tasks"
          value={stats?.total_tasks || 0}
          color="bg-purple-500"
          trend={stats?.tasks_trend}
        />
        <StatCard
          icon={CheckCircle}
          label="Success Rate"
          value={`${calculateSuccessRate()}%`}
          color="bg-green-500"
        />
        <StatCard
          icon={Clock}
          label="Avg. Duration"
          value={formatDuration(stats?.average_task_duration || 0)}
          color="bg-yellow-500"
        />
      </div>

      {/* Detailed Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Status Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Task Status Distribution</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-gray-700">Successful</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold">{stats?.successful_tasks || 0}</span>
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{
                      width: `${stats?.total_tasks > 0 
                        ? (stats.successful_tasks / stats.total_tasks) * 100 
                        : 0}%`
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-500" />
                <span className="text-gray-700">Failed</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold">{stats?.failed_tasks || 0}</span>
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-500 h-2 rounded-full"
                    style={{
                      width: `${stats?.total_tasks > 0 
                        ? (stats.failed_tasks / stats.total_tasks) * 100 
                        : 0}%`
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-yellow-500" />
                <span className="text-gray-700">Pending</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold">{stats?.pending_tasks || 0}</span>
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-yellow-500 h-2 rounded-full"
                    style={{
                      width: `${stats?.total_tasks > 0 
                        ? (stats.pending_tasks / stats.total_tasks) * 100 
                        : 0}%`
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Generation Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Generation Metrics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <FileCode className="w-5 h-5 text-blue-500" />
                <span className="text-gray-700">APIs Discovered</span>
              </div>
              <span className="font-semibold text-lg">{stats?.total_apis_discovered || 0}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-green-500" />
                <span className="text-gray-700">Tests Generated</span>
              </div>
              <span className="font-semibold text-lg">{stats?.total_tests_generated || 0}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Package className="w-5 h-5 text-purple-500" />
                <span className="text-gray-700">Mock Servers</span>
              </div>
              <span className="font-semibold text-lg">{stats?.total_mock_servers || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      {stats?.recent_activity && stats.recent_activity.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {stats.recent_activity.map((activity, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <Activity className="w-4 h-4 text-blue-500" />
                <div className="flex-1">
                  <p className="text-sm text-gray-700">{activity.description}</p>
                  <p className="text-xs text-gray-500">{activity.timestamp}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatsDashboard;