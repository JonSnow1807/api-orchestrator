import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Database,
  Zap,
  Trash2,
  RefreshCw,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  HardDrive,
  Server,
  Activity,
  Settings,
  Search,
  Filter,
  Download,
  Upload,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Layers,
  Globe,
  Lock,
  Unlock,
  Timer,
  Target,
  Gauge,
  FileText,
  Eye,
  MoreVertical
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const AdvancedCachingDashboard = () => {
  const { token } = useAuth();
  const [cacheStats, setCacheStats] = useState(null);
  const [cacheEntries, setCacheEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNamespace, setSelectedNamespace] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [cacheConfig, setCacheConfig] = useState(null);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [bulkAction, setBulkAction] = useState('');
  const [selectedEntries, setSelectedEntries] = useState(new Set());

  useEffect(() => {
    fetchCacheData();
    fetchPerformanceMetrics();
    fetchCacheConfig();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchCacheData();
      fetchPerformanceMetrics();
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedNamespace, searchTerm]);

  const fetchCacheData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(getApiUrl('/api/cache/stats'), {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          namespace: selectedNamespace !== 'all' ? selectedNamespace : undefined,
          search: searchTerm || undefined
        }
      });
      setCacheStats(response.data.stats);
      setCacheEntries(response.data.entries);
    } catch (error) {
      console.error('Failed to fetch cache data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/cache/performance'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPerformanceMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch performance metrics:', error);
    }
  };

  const fetchCacheConfig = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/cache/config'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCacheConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch cache config:', error);
    }
  };

  const clearCache = async (namespace = null) => {
    try {
      await axios.delete(getApiUrl('/api/cache/clear'), {
        headers: { Authorization: `Bearer ${token}` },
        data: { namespace }
      });
      fetchCacheData();
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  const evictEntry = async (key, namespace) => {
    try {
      await axios.delete(getApiUrl(`/api/cache/evict`), {
        headers: { Authorization: `Bearer ${token}` },
        data: { key, namespace }
      });
      fetchCacheData();
    } catch (error) {
      console.error('Failed to evict cache entry:', error);
    }
  };

  const warmupCache = async (namespace = null) => {
    try {
      await axios.post(getApiUrl('/api/cache/warmup'), {
        namespace
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCacheData();
    } catch (error) {
      console.error('Failed to warm up cache:', error);
    }
  };

  const updateCacheConfig = async (config) => {
    try {
      await axios.put(getApiUrl('/api/cache/config'), config, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCacheConfig();
    } catch (error) {
      console.error('Failed to update cache config:', error);
    }
  };

  const exportCacheData = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/cache/export'), {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cache-data-${Date.now()}.json`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export cache data:', error);
    }
  };

  const executeBulkAction = async () => {
    if (!bulkAction || selectedEntries.size === 0) return;

    try {
      const entries = Array.from(selectedEntries);
      await axios.post(getApiUrl('/api/cache/bulk-action'), {
        action: bulkAction,
        entries
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setSelectedEntries(new Set());
      setBulkAction('');
      fetchCacheData();
    } catch (error) {
      console.error('Failed to execute bulk action:', error);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const getCacheTypeColor = (type) => {
    switch (type) {
      case 'redis': return 'text-red-400 bg-red-500/20';
      case 'memory': return 'text-blue-400 bg-blue-500/20';
      case 'database': return 'text-green-400 bg-green-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getCacheStatusIcon = (status) => {
    switch (status) {
      case 'hit': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'miss': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'expired': return <Clock className="w-4 h-4 text-yellow-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00'];

  if (loading && !cacheStats) {
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
            <Database className="w-8 h-8 text-purple-400" />
            <div>
              <h1 className="text-2xl font-bold text-white">Advanced Caching Dashboard</h1>
              <p className="text-gray-400 mt-1">Multi-tier cache management and performance optimization</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={selectedNamespace}
              onChange={(e) => setSelectedNamespace(e.target.value)}
              className="px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
            >
              <option value="all">All Namespaces</option>
              {cacheStats?.namespaces?.map(ns => (
                <option key={ns} value={ns}>{ns}</option>
              ))}
            </select>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition flex items-center space-x-2"
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
            </button>

            <button
              onClick={exportCacheData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>

            <button
              onClick={() => clearCache(selectedNamespace !== 'all' ? selectedNamespace : null)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center space-x-2"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear Cache</span>
            </button>

            <button
              onClick={fetchCacheData}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {cacheStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Hit Ratio</p>
                  <p className="text-2xl font-bold text-green-400">{cacheStats.hit_ratio.toFixed(1)}%</p>
                </div>
                <Target className="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Entries</p>
                  <p className="text-2xl font-bold text-white">{cacheStats.total_entries.toLocaleString()}</p>
                </div>
                <Layers className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Memory Usage</p>
                  <p className="text-2xl font-bold text-white">{formatBytes(cacheStats.memory_usage)}</p>
                </div>
                <HardDrive className="w-8 h-8 text-purple-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Avg Response Time</p>
                  <p className="text-2xl font-bold text-white">{cacheStats.avg_response_time.toFixed(1)}ms</p>
                </div>
                <Gauge className="w-8 h-8 text-yellow-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Operations/sec</p>
                  <p className="text-2xl font-bold text-white">{cacheStats.operations_per_second.toFixed(0)}</p>
                </div>
                <Activity className="w-8 h-8 text-red-400" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Search and Filters */}
      {showFilters && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Search & Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Search Keys</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search cache keys..."
                  className="w-full pl-10 pr-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Cache Type</label>
              <select className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600">
                <option value="all">All Types</option>
                <option value="redis">Redis</option>
                <option value="memory">Memory</option>
                <option value="database">Database</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Status</label>
              <select className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600">
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="expired">Expired</option>
                <option value="evicted">Evicted</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hit Ratio Timeline */}
        {performanceMetrics?.hit_ratio_timeline && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Cache Hit Ratio</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceMetrics.hit_ratio_timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                <Legend />
                <Line type="monotone" dataKey="hit_ratio" stroke="#10B981" strokeWidth={2} name="Hit Ratio %" />
                <Line type="monotone" dataKey="miss_ratio" stroke="#EF4444" strokeWidth={2} name="Miss Ratio %" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Cache Distribution */}
        {cacheStats?.cache_distribution && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Cache Distribution by Type</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(cacheStats.cache_distribution).map(([key, value]) => ({
                    name: key,
                    value
                  }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                >
                  {Object.entries(cacheStats.cache_distribution).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Cache Configuration */}
      {cacheConfig && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Cache Configuration</h3>
            <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center space-x-2">
              <Settings className="w-4 h-4" />
              <span>Configure</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <h4 className="font-semibold text-white">Redis Configuration</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Max Memory:</span>
                  <span className="text-white">{formatBytes(cacheConfig.redis.max_memory)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Eviction Policy:</span>
                  <span className="text-white">{cacheConfig.redis.eviction_policy}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TTL:</span>
                  <span className="text-white">{formatDuration(cacheConfig.redis.default_ttl)}</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-white">Memory Cache</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Max Size:</span>
                  <span className="text-white">{cacheConfig.memory.max_size} entries</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Algorithm:</span>
                  <span className="text-white">{cacheConfig.memory.algorithm}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TTL:</span>
                  <span className="text-white">{formatDuration(cacheConfig.memory.default_ttl)}</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-white">Performance Settings</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Compression:</span>
                  <span className="text-white">{cacheConfig.compression_enabled ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Serialization:</span>
                  <span className="text-white">{cacheConfig.serialization_format}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Background Cleanup:</span>
                  <span className="text-white">{cacheConfig.background_cleanup ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      {selectedEntries.size > 0 && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <span className="text-white">{selectedEntries.size} entries selected</span>
            <div className="flex items-center space-x-3">
              <select
                value={bulkAction}
                onChange={(e) => setBulkAction(e.target.value)}
                className="px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              >
                <option value="">Select Action</option>
                <option value="evict">Evict</option>
                <option value="refresh">Refresh</option>
                <option value="extend_ttl">Extend TTL</option>
              </select>
              <button
                onClick={executeBulkAction}
                disabled={!bulkAction}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600 transition"
              >
                Execute
              </button>
              <button
                onClick={() => setSelectedEntries(new Set())}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
              >
                Clear Selection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cache Entries */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700">
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Cache Entries</h3>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => warmupCache(selectedNamespace !== 'all' ? selectedNamespace : null)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center space-x-2"
              >
                <Zap className="w-4 h-4" />
                <span>Warm Up</span>
              </button>
            </div>
          </div>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {cacheEntries.map((entry) => (
            <div
              key={`${entry.namespace}-${entry.key}`}
              className="p-4 border-b border-gray-700 hover:bg-gray-700/50 transition"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    checked={selectedEntries.has(`${entry.namespace}-${entry.key}`)}
                    onChange={(e) => {
                      const newSelected = new Set(selectedEntries);
                      if (e.target.checked) {
                        newSelected.add(`${entry.namespace}-${entry.key}`);
                      } else {
                        newSelected.delete(`${entry.namespace}-${entry.key}`);
                      }
                      setSelectedEntries(newSelected);
                    }}
                    className="mt-1"
                  />

                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-medium text-white font-mono">{entry.key}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCacheTypeColor(entry.cache_type)}`}>
                        {entry.cache_type}
                      </span>
                      {getCacheStatusIcon(entry.status)}
                    </div>

                    <div className="flex items-center space-x-4 text-xs text-gray-400 mb-2">
                      <span>Namespace: {entry.namespace}</span>
                      <span>Size: {formatBytes(entry.size)}</span>
                      <span>Hits: {entry.hit_count}</span>
                      <span>TTL: {entry.ttl ? formatDuration(entry.ttl) : 'No expiry'}</span>
                    </div>

                    <div className="text-xs text-gray-500">
                      Created: {new Date(entry.created_at).toLocaleString()}
                      {entry.last_accessed && (
                        <span className="ml-4">Last accessed: {new Date(entry.last_accessed).toLocaleString()}</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedEntry(entry)}
                    className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
                    title="View Details"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => evictEntry(entry.key, entry.namespace)}
                    className="p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                    title="Evict"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Entry Detail Modal */}
      {selectedEntry && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Cache Entry Details</h3>
              <button
                onClick={() => setSelectedEntry(null)}
                className="text-gray-400 hover:text-white transition"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Key</label>
                  <p className="text-white font-mono">{selectedEntry.key}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Namespace</label>
                  <p className="text-white">{selectedEntry.namespace}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Cache Type</label>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCacheTypeColor(selectedEntry.cache_type)}`}>
                    {selectedEntry.cache_type}
                  </span>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Size</label>
                  <p className="text-white">{formatBytes(selectedEntry.size)}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Hit Count</label>
                  <p className="text-white">{selectedEntry.hit_count}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Value Preview</label>
                <pre className="text-sm text-gray-300 bg-gray-900 p-3 rounded-lg overflow-x-auto max-h-48">
                  {selectedEntry.value_preview || 'No preview available'}
                </pre>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Created At</label>
                  <p className="text-white">{new Date(selectedEntry.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Expires At</label>
                  <p className="text-white">
                    {selectedEntry.expires_at ? new Date(selectedEntry.expires_at).toLocaleString() : 'Never'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedCachingDashboard;