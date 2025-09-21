import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  GitBranch,
  Clock,
  Search,
  Filter,
  RefreshCw,
  Eye,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Activity,
  Server,
  Globe,
  Zap,
  BarChart3,
  TrendingUp,
  Map,
  Layers,
  Settings,
  Download,
  Info,
  Calendar,
  Timer,
  Target,
  Link,
  ArrowRight,
  ArrowDown,
  ChevronRight,
  ChevronDown,
  Gauge,
  Network,
  Code,
  Database,
  CloudLightning
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const DistributedTracingDashboard = () => {
  const { token } = useAuth();
  const [traces, setTraces] = useState([]);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [traceTimeline, setTraceTimeline] = useState([]);
  const [serviceMap, setServiceMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchFilters, setSearchFilters] = useState({
    traceId: '',
    serviceName: '',
    operationName: '',
    minDuration: '',
    maxDuration: '',
    errorOnly: false,
    timeRange: '1h'
  });
  const [showFilters, setShowFilters] = useState(false);
  const [tracingStats, setTracingStats] = useState(null);
  const [expandedSpans, setExpandedSpans] = useState(new Set());
  const [viewMode, setViewMode] = useState('list'); // list, timeline, service-map

  useEffect(() => {
    fetchTraces();
    fetchServiceMap();
    fetchTracingStats();
  }, [searchFilters]);

  const fetchTraces = async () => {
    setLoading(true);
    try {
      const response = await axios.get(getApiUrl('/api/observability/traces'), {
        headers: { Authorization: `Bearer ${token}` },
        params: searchFilters
      });
      setTraces(response.data.traces);
    } catch (error) {
      console.error('Failed to fetch traces:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTraceDetails = async (traceId) => {
    try {
      const response = await axios.get(getApiUrl(`/api/observability/traces/${traceId}`), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedTrace(response.data);
    } catch (error) {
      console.error('Failed to fetch trace details:', error);
    }
  };

  const fetchTraceTimeline = async (traceId) => {
    try {
      const response = await axios.get(getApiUrl(`/api/observability/traces/${traceId}/timeline`), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTraceTimeline(response.data.timeline);
    } catch (error) {
      console.error('Failed to fetch trace timeline:', error);
    }
  };

  const fetchServiceMap = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/observability/service-map'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setServiceMap(response.data);
    } catch (error) {
      console.error('Failed to fetch service map:', error);
    }
  };

  const fetchTracingStats = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/observability/dashboard'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTracingStats(response.data);
    } catch (error) {
      console.error('Failed to fetch tracing stats:', error);
    }
  };

  const exportTrace = async (traceId) => {
    try {
      const response = await axios.get(getApiUrl(`/api/observability/traces/${traceId}/export`), {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `trace-${traceId}-${Date.now()}.json`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export trace:', error);
    }
  };

  const getSpanStatusColor = (status) => {
    switch (status) {
      case 'ok': return 'text-green-400 bg-green-500/20';
      case 'error': return 'text-red-400 bg-red-500/20';
      case 'timeout': return 'text-yellow-400 bg-yellow-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getSpanTypeIcon = (spanType) => {
    switch (spanType) {
      case 'http': return <Globe className="w-4 h-4" />;
      case 'database': return <Database className="w-4 h-4" />;
      case 'cache': return <Zap className="w-4 h-4" />;
      case 'service': return <Server className="w-4 h-4" />;
      case 'function': return <Code className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const formatDuration = (ms) => {
    if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const toggleSpanExpansion = (spanId) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  const calculateSpanWidth = (span, totalDuration) => {
    return Math.max(2, (span.duration_ms / totalDuration) * 100);
  };

  const calculateSpanOffset = (span, traceStart) => {
    const startTime = new Date(span.start_time).getTime();
    const traceStartTime = new Date(traceStart).getTime();
    return ((startTime - traceStartTime) / totalDuration) * 100;
  };

  const renderSpanHierarchy = (spans, parentId = null, depth = 0) => {
    const childSpans = spans.filter(span => span.parent_span_id === parentId);

    return childSpans.map(span => {
      const hasChildren = spans.some(s => s.parent_span_id === span.span_id);
      const isExpanded = expandedSpans.has(span.span_id);

      return (
        <div key={span.span_id} className="border-l border-gray-600" style={{ marginLeft: `${depth * 20}px` }}>
          <div className="flex items-center p-3 hover:bg-gray-700/50 transition">
            <div className="flex items-center space-x-2 flex-1">
              {hasChildren && (
                <button
                  onClick={() => toggleSpanExpansion(span.span_id)}
                  className="text-gray-400 hover:text-white"
                >
                  {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </button>
              )}
              {!hasChildren && <div className="w-4" />}

              {getSpanTypeIcon(span.span_type)}

              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-white">{span.operation_name}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSpanStatusColor(span.status)}`}>
                    {span.status}
                  </span>
                </div>
                <div className="text-sm text-gray-400">
                  {span.service_name} • {formatDuration(span.duration_ms)}
                </div>
              </div>

              <div className="text-right text-sm text-gray-400">
                <div>{formatTimestamp(span.start_time)}</div>
                {span.tags && Object.keys(span.tags).length > 0 && (
                  <div className="text-xs">{Object.keys(span.tags).length} tags</div>
                )}
              </div>
            </div>
          </div>

          {isExpanded && span.tags && (
            <div className="ml-8 p-3 bg-gray-900/50 border-l border-gray-600">
              <h5 className="text-sm font-medium text-gray-300 mb-2">Tags</h5>
              <div className="space-y-1">
                {Object.entries(span.tags).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-gray-400">{key}:</span>
                    <span className="text-gray-300">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {isExpanded && hasChildren && renderSpanHierarchy(spans, span.span_id, depth + 1)}
        </div>
      );
    });
  };

  const renderTimelineView = () => {
    if (!selectedTrace || !traceTimeline.length) return null;

    const totalDuration = selectedTrace.total_duration_ms;

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold text-white">Timeline View</h4>
          <div className="text-sm text-gray-400">
            Total Duration: {formatDuration(totalDuration)}
          </div>
        </div>

        <div className="bg-gray-900 p-4 rounded-lg">
          {traceTimeline.map(span => {
            const width = calculateSpanWidth(span, totalDuration);
            const offset = calculateSpanOffset(span, selectedTrace.start_time);

            return (
              <div key={span.span_id} className="mb-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-300">
                    {span.service_name} - {span.operation_name}
                  </span>
                  <span className="text-xs text-gray-400">
                    {formatDuration(span.duration_ms)}
                  </span>
                </div>
                <div className="relative h-6 bg-gray-800 rounded">
                  <div
                    className={`absolute h-full rounded ${
                      span.status === 'error' ? 'bg-red-500' :
                      span.status === 'ok' ? 'bg-green-500' : 'bg-blue-500'
                    }`}
                    style={{
                      left: `${offset}%`,
                      width: `${width}%`
                    }}
                    title={`${span.operation_name} - ${formatDuration(span.duration_ms)}`}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderServiceMap = () => {
    if (!serviceMap) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h4 className="text-lg font-semibold text-white">Service Dependency Map</h4>
          <span className="text-sm text-gray-400">
            {serviceMap.services.length} services • Generated at {formatTimestamp(serviceMap.generated_at)}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {serviceMap.services.map(service => (
            <div key={service.name} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Server className="w-5 h-5 text-blue-400" />
                  <h5 className="font-medium text-white">{service.name}</h5>
                </div>
                <div className={`w-3 h-3 rounded-full ${
                  service.error_rate < 0.01 ? 'bg-green-400' :
                  service.error_rate < 0.05 ? 'bg-yellow-400' : 'bg-red-400'
                }`} />
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Requests:</span>
                  <span className="text-white">{service.request_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Error Rate:</span>
                  <span className={`${service.error_rate < 0.01 ? 'text-green-400' :
                    service.error_rate < 0.05 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {(service.error_rate * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Duration:</span>
                  <span className="text-white">{formatDuration(service.avg_duration_ms)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Operations:</span>
                  <span className="text-white">{service.operations.length}</span>
                </div>
              </div>

              {service.operations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <h6 className="text-xs font-medium text-gray-400 mb-2">Top Operations</h6>
                  <div className="space-y-1">
                    {service.operations.slice(0, 3).map(op => (
                      <div key={op} className="text-xs text-gray-500 truncate">
                        {op}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading && !traces.length) {
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
            <GitBranch className="w-8 h-8 text-purple-400" />
            <div>
              <h1 className="text-2xl font-bold text-white">Distributed Tracing</h1>
              <p className="text-gray-400 mt-1">Monitor request flows across your microservices architecture</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              className="px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
            >
              <option value="list">Trace List</option>
              <option value="timeline">Timeline View</option>
              <option value="service-map">Service Map</option>
            </select>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition flex items-center space-x-2"
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
            </button>

            <button
              onClick={fetchTraces}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {tracingStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Active Traces</p>
                  <p className="text-2xl font-bold text-white">{tracingStats.active_traces?.toLocaleString()}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Services</p>
                  <p className="text-2xl font-bold text-white">{tracingStats.service_count}</p>
                </div>
                <Server className="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Avg Latency</p>
                  <p className="text-2xl font-bold text-white">{formatDuration(tracingStats.avg_latency_ms)}</p>
                </div>
                <Gauge className="w-8 h-8 text-yellow-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Error Rate</p>
                  <p className="text-2xl font-bold text-white">{(tracingStats.error_rate * 100).toFixed(2)}%</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Search and Filters */}
      {showFilters && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Search & Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Trace ID</label>
              <input
                type="text"
                value={searchFilters.traceId}
                onChange={(e) => setSearchFilters({...searchFilters, traceId: e.target.value})}
                placeholder="Enter trace ID"
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Service Name</label>
              <input
                type="text"
                value={searchFilters.serviceName}
                onChange={(e) => setSearchFilters({...searchFilters, serviceName: e.target.value})}
                placeholder="Filter by service"
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Operation</label>
              <input
                type="text"
                value={searchFilters.operationName}
                onChange={(e) => setSearchFilters({...searchFilters, operationName: e.target.value})}
                placeholder="Filter by operation"
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Time Range</label>
              <select
                value={searchFilters.timeRange}
                onChange={(e) => setSearchFilters({...searchFilters, timeRange: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              >
                <option value="15m">Last 15 minutes</option>
                <option value="1h">Last hour</option>
                <option value="6h">Last 6 hours</option>
                <option value="24h">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Min Duration (ms)</label>
              <input
                type="number"
                value={searchFilters.minDuration}
                onChange={(e) => setSearchFilters({...searchFilters, minDuration: e.target.value})}
                placeholder="Minimum"
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Max Duration (ms)</label>
              <input
                type="number"
                value={searchFilters.maxDuration}
                onChange={(e) => setSearchFilters({...searchFilters, maxDuration: e.target.value})}
                placeholder="Maximum"
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              />
            </div>

            <div className="flex items-end">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={searchFilters.errorOnly}
                  onChange={(e) => setSearchFilters({...searchFilters, errorOnly: e.target.checked})}
                  className="rounded text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-300">Errors only</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Content based on view mode */}
      {viewMode === 'service-map' && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          {renderServiceMap()}
        </div>
      )}

      {viewMode === 'timeline' && selectedTrace && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          {renderTimelineView()}
        </div>
      )}

      {viewMode === 'list' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Traces List */}
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700">
            <div className="p-6 border-b border-gray-700">
              <h3 className="text-lg font-semibold text-white">Traces</h3>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {traces.map((trace) => (
                <div
                  key={trace.trace_id}
                  className="p-4 border-b border-gray-700 hover:bg-gray-700/50 transition cursor-pointer"
                  onClick={() => {
                    fetchTraceDetails(trace.trace_id);
                    fetchTraceTimeline(trace.trace_id);
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="font-mono text-sm text-purple-400">{trace.trace_id.substring(0, 8)}...</span>
                        {trace.error_count > 0 ? (
                          <XCircle className="w-4 h-4 text-red-400" />
                        ) : (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        )}
                      </div>

                      <div className="space-y-1 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Duration:</span>
                          <span className="text-white">{formatDuration(trace.total_duration_ms)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Spans:</span>
                          <span className="text-white">{trace.span_count}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-400">Services:</span>
                          <span className="text-white">{trace.services.length}</span>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1 mt-2">
                        {trace.services.slice(0, 3).map(service => (
                          <span key={service} className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                            {service}
                          </span>
                        ))}
                        {trace.services.length > 3 && (
                          <span className="text-xs text-gray-400">+{trace.services.length - 3} more</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          exportTrace(trace.trace_id);
                        }}
                        className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
                        title="Export Trace"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <Eye className="w-4 h-4 text-gray-400" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trace Details */}
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700">
            <div className="p-6 border-b border-gray-700">
              <h3 className="text-lg font-semibold text-white">
                {selectedTrace ? `Trace Details - ${selectedTrace.trace_id.substring(0, 16)}...` : 'Select a Trace'}
              </h3>
            </div>

            {selectedTrace ? (
              <div className="max-h-96 overflow-y-auto">
                {selectedTrace.spans && renderSpanHierarchy(selectedTrace.spans)}
              </div>
            ) : (
              <div className="p-6 text-center text-gray-400">
                <GitBranch className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Select a trace from the list to view its details</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Performance Charts */}
      {tracingStats?.latency_distribution && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Performance Analysis</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-3">Latency Distribution</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={tracingStats.latency_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="bucket" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                  <Bar dataKey="count" fill="#8B5CF6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-3">Error Rate Trend</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={tracingStats.error_rate_timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                  <Line type="monotone" dataKey="error_rate" stroke="#EF4444" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DistributedTracingDashboard;