import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Shield,
  AlertTriangle,
  Eye,
  Search,
  Filter,
  Download,
  RefreshCw,
  Clock,
  User,
  Globe,
  Activity,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  AlertCircle,
  Info,
  Calendar,
  MapPin,
  Lock,
  Settings,
  BarChart3,
  PieChart,
  FileText,
  ExternalLink
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart as RechartsPieChart, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const EnterpriseAuditDashboard = () => {
  const { token } = useAuth();
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [filters, setFilters] = useState({
    severity: 'all',
    eventType: 'all',
    status: 'all',
    userId: '',
    searchTerm: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [complianceReport, setComplianceReport] = useState(null);
  const [riskMetrics, setRiskMetrics] = useState(null);

  useEffect(() => {
    fetchAuditData();
    fetchComplianceReport();
    fetchRiskMetrics();
  }, [timeRange, filters]);

  const fetchAuditData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(getApiUrl('/api/audit/events'), {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          time_range: timeRange,
          ...filters,
          limit: 100
        }
      });
      setAuditEvents(response.data.events);
      setStats(response.data.stats);
    } catch (error) {
      console.error('Failed to fetch audit data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchComplianceReport = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/audit/compliance-report'), {
        headers: { Authorization: `Bearer ${token}` },
        params: { time_range: timeRange }
      });
      setComplianceReport(response.data);
    } catch (error) {
      console.error('Failed to fetch compliance report:', error);
    }
  };

  const fetchRiskMetrics = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/audit/risk-metrics'), {
        headers: { Authorization: `Bearer ${token}` },
        params: { time_range: timeRange }
      });
      setRiskMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch risk metrics:', error);
    }
  };

  const exportAuditLog = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/audit/export'), {
        headers: { Authorization: `Bearer ${token}` },
        params: { ...filters, time_range: timeRange },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-log-${timeRange}-${Date.now()}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export audit log:', error);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-400 bg-red-500/20';
      case 'HIGH': return 'text-orange-400 bg-orange-500/20';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-500/20';
      case 'LOW': return 'text-blue-400 bg-blue-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'CRITICAL': return <AlertTriangle className="w-4 h-4" />;
      case 'HIGH': return <AlertCircle className="w-4 h-4" />;
      case 'MEDIUM': return <Info className="w-4 h-4" />;
      case 'LOW': return <CheckCircle className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'SUCCESS': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'FAILURE': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'BLOCKED': return <Lock className="w-4 h-4 text-yellow-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getRiskLevel = (score) => {
    if (score >= 80) return { level: 'High', color: 'text-red-400', bgColor: 'bg-red-500/20' };
    if (score >= 60) return { level: 'Medium', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' };
    if (score >= 40) return { level: 'Low', color: 'text-blue-400', bgColor: 'bg-blue-500/20' };
    return { level: 'Minimal', color: 'text-green-400', bgColor: 'bg-green-500/20' };
  };

  const eventTypeOptions = [
    'USER_LOGIN', 'USER_LOGOUT', 'API_ACCESS', 'DATA_ACCESS', 'CONFIG_CHANGE',
    'PERMISSION_CHANGE', 'SECURITY_EVENT', 'COMPLIANCE_CHECK', 'SYSTEM_EVENT'
  ];

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00'];

  if (loading && !auditEvents.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-purple-400" />
            <div>
              <h1 className="text-2xl font-bold text-white">Enterprise Audit Dashboard</h1>
              <p className="text-gray-400 mt-1">Security audit logs and compliance monitoring</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition flex items-center space-x-2"
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
            </button>

            <button
              onClick={exportAuditLog}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>

            <button
              onClick={fetchAuditData}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Events</p>
                  <p className="text-2xl font-bold text-white">{stats.total_events.toLocaleString()}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Security Events</p>
                  <p className="text-2xl font-bold text-white">{stats.security_events}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">High Risk Events</p>
                  <p className="text-2xl font-bold text-white">{stats.high_risk_events}</p>
                </div>
                <Shield className="w-8 h-8 text-yellow-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Compliance Score</p>
                  <p className="text-2xl font-bold text-white">{stats.compliance_score}%</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Severity</label>
              <select
                value={filters.severity}
                onChange={(e) => setFilters({...filters, severity: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              >
                <option value="all">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Event Type</label>
              <select
                value={filters.eventType}
                onChange={(e) => setFilters({...filters, eventType: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              >
                <option value="all">All Types</option>
                {eventTypeOptions.map(type => (
                  <option key={type} value={type}>{type.replace('_', ' ')}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              >
                <option value="all">All Statuses</option>
                <option value="SUCCESS">Success</option>
                <option value="FAILURE">Failure</option>
                <option value="BLOCKED">Blocked</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">User ID</label>
              <input
                type="text"
                value={filters.userId}
                onChange={(e) => setFilters({...filters, userId: e.target.value})}
                placeholder="Enter user ID"
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={filters.searchTerm}
                  onChange={(e) => setFilters({...filters, searchTerm: e.target.value})}
                  placeholder="Search events..."
                  className="w-full pl-10 pr-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Event Timeline */}
        {stats?.timeline && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Event Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats.timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                <Legend />
                <Line type="monotone" dataKey="events" stroke="#8B5CF6" strokeWidth={2} name="Events" />
                <Line type="monotone" dataKey="security_events" stroke="#EF4444" strokeWidth={2} name="Security Events" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Event Types Distribution */}
        {stats?.event_types && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Event Types</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={Object.entries(stats.event_types).map(([key, value]) => ({
                    name: key.replace('_', ' '),
                    value
                  }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                >
                  {Object.entries(stats.event_types).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Risk Metrics */}
      {riskMetrics && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Assessment</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-32 h-32 mx-auto mb-4 relative">
                <div className="w-full h-full rounded-full bg-gray-700">
                  <div
                    className="w-full h-full rounded-full bg-gradient-to-r from-red-500 to-yellow-500"
                    style={{
                      background: `conic-gradient(from 0deg, #ef4444 0%, #f59e0b ${riskMetrics.overall_risk_score}%, #374151 ${riskMetrics.overall_risk_score}%)`
                    }}
                  />
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">{riskMetrics.overall_risk_score}</div>
                    <div className="text-xs text-gray-400">Risk Score</div>
                  </div>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskLevel(riskMetrics.overall_risk_score).bgColor} ${getRiskLevel(riskMetrics.overall_risk_score).color}`}>
                {getRiskLevel(riskMetrics.overall_risk_score).level} Risk
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-white">Risk Factors</h4>
              {riskMetrics.risk_factors.map((factor, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-gray-300">{factor.name}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-700 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-red-500"
                        style={{ width: `${factor.score}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-400">{factor.score}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-white">Recommendations</h4>
              <div className="space-y-2">
                {riskMetrics.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-400 mt-1" />
                    <span className="text-sm text-gray-300">{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Events List */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700">
        <div className="p-6 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">Recent Audit Events</h3>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {auditEvents.map((event) => (
            <div
              key={event.id}
              className="p-4 border-b border-gray-700 hover:bg-gray-700/50 transition cursor-pointer"
              onClick={() => setSelectedEvent(event)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getSeverityIcon(event.severity)}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-medium text-white">{event.event_type.replace('_', ' ')}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(event.severity)}`}>
                        {event.severity}
                      </span>
                      {getStatusIcon(event.status)}
                    </div>
                    <p className="text-gray-300 text-sm mb-2">{event.message}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-400">
                      <div className="flex items-center space-x-1">
                        <User className="w-3 h-3" />
                        <span>{event.user_id || 'System'}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Globe className="w-3 h-3" />
                        <span>{event.ip_address}</span>
                      </div>
                      {event.location && (
                        <div className="flex items-center space-x-1">
                          <MapPin className="w-3 h-3" />
                          <span>{event.location}</span>
                        </div>
                      )}
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{formatTimestamp(event.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {event.risk_score && (
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskLevel(event.risk_score).bgColor} ${getRiskLevel(event.risk_score).color}`}>
                      Risk: {event.risk_score}
                    </span>
                  )}
                  <Eye className="w-4 h-4 text-gray-400 hover:text-white transition" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Event Details</h3>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-gray-400 hover:text-white transition"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Event Type</label>
                  <p className="text-white">{selectedEvent.event_type.replace('_', ' ')}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Severity</label>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(selectedEvent.severity)}`}>
                    {selectedEvent.severity}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Message</label>
                <p className="text-white">{selectedEvent.message}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">User</label>
                  <p className="text-white">{selectedEvent.user_id || 'System'}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">IP Address</label>
                  <p className="text-white">{selectedEvent.ip_address}</p>
                </div>
              </div>

              {selectedEvent.details && (
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Additional Details</label>
                  <pre className="text-sm text-gray-300 bg-gray-900 p-3 rounded-lg overflow-x-auto">
                    {JSON.stringify(selectedEvent.details, null, 2)}
                  </pre>
                </div>
              )}

              <div>
                <label className="block text-sm text-gray-400 mb-1">Timestamp</label>
                <p className="text-white">{formatTimestamp(selectedEvent.timestamp)}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnterpriseAuditDashboard;