import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, DollarSign, Clock, Shield, Users,
  Activity, BarChart3, PieChart, LineChart, ArrowUp, ArrowDown,
  Zap, AlertTriangle, CheckCircle, Info, Download, Filter,
  Calendar, Target, Cpu, Database, Globe, Award, Sparkles
} from 'lucide-react';
import {
  LineChart as RechartsLine, Line, AreaChart, Area, BarChart, Bar,
  PieChart as RechartsPie, Pie, Cell, ResponsiveContainer,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ComposedChart, Scatter, RadialBarChart, RadialBar
} from 'recharts';
import axios from 'axios';

const AdvancedAnalytics = ({ workspaceId }) => {
  const [timeRange, setTimeRange] = useState('7d');
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Color palette for charts
  const colors = {
    primary: '#8b5cf6',
    secondary: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    gradient: ['#8b5cf6', '#3b82f6'],
  };

  useEffect(() => {
    fetchAnalytics();
  }, [workspaceId, timeRange]);

  const fetchAnalytics = async () => {
    if (!workspaceId) {
      setLoading(false);
      setMetrics(null);
      return;
    }

    setLoading(true);
    try {
      // Fetch real data from backend
      const [overview, performance, costs, security] = await Promise.all([
        axios.get(`/api/analytics/overview?workspace_id=${workspaceId}&range=${timeRange}`),
        axios.get(`/api/analytics/performance?workspace_id=${workspaceId}&range=${timeRange}`),
        axios.get(`/api/analytics/costs?workspace_id=${workspaceId}`),
        axios.get(`/api/analytics/security?workspace_id=${workspaceId}`)
      ]);

      setMetrics({
        overview: overview.data,
        performance: performance.data,
        costs: costs.data,
        security: security.data,
        insights: overview.data.insights || []
      });
    } catch (error) {
      console.error('Error fetching analytics:', error);
      // Set empty state instead of mock data
      setMetrics({
        overview: {
          totalAPIs: 0,
          activeUsers: 0,
          apiCalls: 0,
          errorRate: 0,
          avgResponseTime: 0,
          securityScore: 0,
          costSaved: 0,
          timesSaved: 0,
          roi: 0
        },
        trends: [],
        performance: {
          responseTimeDistribution: [],
          endpointPerformance: [],
          hourlyTraffic: []
        },
        costs: {
          breakdown: [],
          monthly: [],
          comparison: []
        },
        security: {
          scores: [],
          vulnerabilities: {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0
          },
          compliance: {
            gdpr: false,
            hipaa: false,
            soc2: false,
            pci: false
          }
        },
        predictions: {
          traffic: { next7Days: 0, confidence: 0 },
          costs: { next30Days: 0, confidence: 0 },
          errors: { next24Hours: 0, confidence: 0 },
          growth: { nextQuarter: 0, confidence: 0 }
        },
        insights: []
      });
    } finally {
      setLoading(false);
    }
  };

  const MetricCard = ({ icon: Icon, title, value, change, color, subtitle }) => (
    <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700 hover:border-purple-500/50 transition-all duration-300">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg bg-gradient-to-br ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {change && change !== 0 && (
          <div className={`flex items-center gap-1 text-sm ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {change > 0 ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-gray-400 text-sm">{title}</div>
      {subtitle && <div className="text-gray-500 text-xs mt-1">{subtitle}</div>}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (!workspaceId) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center">
        <BarChart3 className="w-16 h-16 text-gray-600 mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">No Workspace Selected</h3>
        <p className="text-gray-400">Please select a workspace to view analytics</p>
      </div>
    );
  }

  if (!metrics || !metrics.overview) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center">
        <BarChart3 className="w-16 h-16 text-gray-600 mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">No Analytics Data</h3>
        <p className="text-gray-400">Start using the platform to see analytics</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h2>
          <p className="text-gray-400">Real-time insights and metrics</p>
        </div>
        <div className="flex gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          <button className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white hover:bg-gray-700 transition flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      {metrics.overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Zap}
            title="API Calls"
            value={metrics.overview.apiCalls?.toLocaleString() || '0'}
            change={metrics.overview.apiCallsChange}
            color="from-purple-500 to-pink-600"
          />
          <MetricCard
            icon={Clock}
            title="Avg Response Time"
            value={`${metrics.overview.avgResponseTime || 0}ms`}
            change={metrics.overview.responseTimeChange}
            color="from-blue-500 to-cyan-600"
          />
          <MetricCard
            icon={Shield}
            title="Security Score"
            value={`${metrics.overview.securityScore || 0}/100`}
            change={metrics.overview.securityChange}
            color="from-green-500 to-emerald-600"
          />
          <MetricCard
            icon={AlertTriangle}
            title="Error Rate"
            value={`${(metrics.overview.errorRate || 0).toFixed(2)}%`}
            change={metrics.overview.errorRateChange}
            color="from-amber-500 to-orange-600"
          />
        </div>
      )}

      {/* Tabs for Different Views */}
      <div className="flex gap-2 p-1 bg-gray-800/50 rounded-lg">
        {['overview', 'performance', 'costs', 'security'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 rounded-lg transition capitalize ${
              activeTab === tab
                ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
        {activeTab === 'overview' && (
          <div>
            {metrics.trends && metrics.trends.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">API Traffic Trends</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={metrics.trends}>
                    <defs>
                      <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                    <Area type="monotone" dataKey="requests" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorRequests)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <Activity className="w-12 h-12 mx-auto mb-3 text-gray-600" />
                <p>No traffic data available yet</p>
                <p className="text-sm mt-2">Start making API calls to see trends</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'performance' && (
          <div>
            {metrics.performance?.endpointPerformance?.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Endpoint Performance</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-700">
                        <th className="text-left py-3 px-4 text-gray-400">Endpoint</th>
                        <th className="text-right py-3 px-4 text-gray-400">Calls</th>
                        <th className="text-right py-3 px-4 text-gray-400">Avg Time</th>
                        <th className="text-right py-3 px-4 text-gray-400">Success Rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {metrics.performance.endpointPerformance.map((endpoint, idx) => (
                        <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-900/50">
                          <td className="py-3 px-4 text-white">{endpoint.endpoint}</td>
                          <td className="text-right py-3 px-4 text-gray-300">{endpoint.calls.toLocaleString()}</td>
                          <td className="text-right py-3 px-4 text-gray-300">{endpoint.avgTime}ms</td>
                          <td className="text-right py-3 px-4">
                            <span className={`${endpoint.successRate > 95 ? 'text-green-400' : 'text-yellow-400'}`}>
                              {endpoint.successRate}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <Cpu className="w-12 h-12 mx-auto mb-3 text-gray-600" />
                <p>No performance data available</p>
                <p className="text-sm mt-2">API endpoints will appear here once they're used</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'costs' && (
          <div className="text-center py-12 text-gray-400">
            <DollarSign className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <p>Cost tracking coming soon</p>
            <p className="text-sm mt-2">We'll calculate your savings compared to traditional development</p>
          </div>
        )}

        {activeTab === 'security' && (
          <div>
            {metrics.security?.scores?.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Security Assessment</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={metrics.security.scores}>
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis dataKey="aspect" stroke="#9ca3af" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9ca3af" />
                    <Radar name="Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <Shield className="w-12 h-12 mx-auto mb-3 text-gray-600" />
                <p>No security scans performed yet</p>
                <p className="text-sm mt-2">Security analysis will appear after API discovery</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* AI Insights */}
      {metrics.insights && metrics.insights.length > 0 && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">AI Insights</h3>
          </div>
          <div className="space-y-3">
            {metrics.insights.map((insight, idx) => (
              <div key={idx} className="flex items-start gap-3 p-4 bg-gray-900/50 rounded-lg">
                {insight.type === 'success' && <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />}
                {insight.type === 'warning' && <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />}
                {insight.type === 'info' && <Info className="w-5 h-5 text-blue-400 mt-0.5" />}
                <p className="text-gray-300 text-sm">{insight.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedAnalytics;