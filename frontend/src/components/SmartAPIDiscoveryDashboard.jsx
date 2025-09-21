import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Brain,
  Search,
  Zap,
  Target,
  TrendingUp,
  Eye,
  Star,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Globe,
  Code,
  Database,
  Settings,
  RefreshCw,
  Filter,
  Download,
  Play,
  Bookmark,
  Share,
  BarChart3,
  PieChart,
  Activity,
  Network,
  Layers,
  Lightbulb,
  FileText,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Plus,
  Minus,
  ThumbsUp,
  ThumbsDown,
  MessageSquare
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, PieChart as RechartsPieChart, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const SmartAPIDiscoveryDashboard = () => {
  const { token } = useAuth();
  const [discoveredAPIs, setDiscoveredAPIs] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discoveryStats, setDiscoveryStats] = useState(null);
  const [selectedAPI, setSelectedAPI] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    category: 'all',
    confidence: 'all',
    status: 'all',
    tags: []
  });
  const [viewMode, setViewMode] = useState('grid'); // grid, list, patterns
  const [analysisResults, setAnalysisResults] = useState(null);
  const [behaviorAnalysis, setBehaviorAnalysis] = useState(null);
  const [expandedPatterns, setExpandedPatterns] = useState(new Set());

  useEffect(() => {
    fetchDiscoveredAPIs();
    fetchRecommendations();
    fetchPatterns();
    fetchDiscoveryStats();
    fetchBehaviorAnalysis();
  }, [filters, searchQuery]);

  const fetchDiscoveredAPIs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(getApiUrl('/api/smart-discovery/apis'), {
        headers: { Authorization: `Bearer ${token}` },
        params: { ...filters, search: searchQuery }
      });
      setDiscoveredAPIs(response.data.apis);
    } catch (error) {
      console.error('Failed to fetch discovered APIs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/smart-discovery/recommendations'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecommendations(response.data.recommendations);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  };

  const fetchPatterns = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/smart-discovery/patterns'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPatterns(response.data.patterns);
    } catch (error) {
      console.error('Failed to fetch patterns:', error);
    }
  };

  const fetchDiscoveryStats = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/smart-discovery/stats'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDiscoveryStats(response.data);
    } catch (error) {
      console.error('Failed to fetch discovery stats:', error);
    }
  };

  const fetchBehaviorAnalysis = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/smart-discovery/behavior-analysis'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBehaviorAnalysis(response.data);
    } catch (error) {
      console.error('Failed to fetch behavior analysis:', error);
    }
  };

  const runMLAnalysis = async (target = null) => {
    try {
      setLoading(true);
      const response = await axios.post(getApiUrl('/api/smart-discovery/analyze'), {
        target,
        deep_analysis: true,
        include_predictions: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalysisResults(response.data);
      fetchDiscoveredAPIs();
    } catch (error) {
      console.error('Failed to run ML analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveAPIEndpoint = async (api) => {
    try {
      await axios.post(getApiUrl('/api/smart-discovery/save'), {
        endpoint: api
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchDiscoveredAPIs();
    } catch (error) {
      console.error('Failed to save API endpoint:', error);
    }
  };

  const rateRecommendation = async (recommendationId, rating) => {
    try {
      await axios.post(getApiUrl(`/api/smart-discovery/recommendations/${recommendationId}/rate`), {
        rating
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchRecommendations();
    } catch (error) {
      console.error('Failed to rate recommendation:', error);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-400 bg-green-500/20';
    if (confidence >= 0.6) return 'text-yellow-400 bg-yellow-500/20';
    return 'text-red-400 bg-red-500/20';
  };

  const getCategoryColor = (category) => {
    const colors = {
      'rest': 'text-blue-400 bg-blue-500/20',
      'graphql': 'text-purple-400 bg-purple-500/20',
      'grpc': 'text-green-400 bg-green-500/20',
      'websocket': 'text-yellow-400 bg-yellow-500/20',
      'webhook': 'text-orange-400 bg-orange-500/20'
    };
    return colors[category.toLowerCase()] || 'text-gray-400 bg-gray-500/20';
  };

  const getMethodColor = (method) => {
    const colors = {
      'GET': 'text-green-400 bg-green-500/20',
      'POST': 'text-blue-400 bg-blue-500/20',
      'PUT': 'text-yellow-400 bg-yellow-500/20',
      'DELETE': 'text-red-400 bg-red-500/20',
      'PATCH': 'text-purple-400 bg-purple-500/20'
    };
    return colors[method] || 'text-gray-400 bg-gray-500/20';
  };

  const togglePatternExpansion = (patternId) => {
    const newExpanded = new Set(expandedPatterns);
    if (newExpanded.has(patternId)) {
      newExpanded.delete(patternId);
    } else {
      newExpanded.add(patternId);
    }
    setExpandedPatterns(newExpanded);
  };

  const renderAPICard = (api) => (
    <div key={api.id || api.url} className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700/50 transition">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className={`p-2 rounded-lg ${getCategoryColor(api.category)}`}>
            {api.category === 'rest' && <Globe className="w-4 h-4" />}
            {api.category === 'graphql' && <Code className="w-4 h-4" />}
            {api.category === 'grpc' && <Network className="w-4 h-4" />}
            {api.category === 'websocket' && <Activity className="w-4 h-4" />}
            {api.category === 'webhook' && <Zap className="w-4 h-4" />}
          </div>
          <div>
            <h3 className="font-semibold text-white">{api.name || api.endpoint}</h3>
            <p className="text-sm text-gray-400">{api.description || 'AI-discovered endpoint'}</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(api.confidence_score)}`}>
            {(api.confidence_score * 100).toFixed(0)}% confidence
          </span>
          <button
            onClick={() => setSelectedAPI(api)}
            className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">URL:</span>
          <span className="text-sm text-white font-mono truncate max-w-xs">{api.url}</span>
        </div>

        {api.methods && api.methods.length > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Methods:</span>
            <div className="flex space-x-1">
              {api.methods.slice(0, 3).map(method => (
                <span key={method} className={`px-2 py-1 rounded text-xs font-medium ${getMethodColor(method)}`}>
                  {method}
                </span>
              ))}
              {api.methods.length > 3 && (
                <span className="text-xs text-gray-400">+{api.methods.length - 3}</span>
              )}
            </div>
          </div>
        )}

        {api.tags && api.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {api.tags.slice(0, 4).map(tag => (
              <span key={tag} className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between pt-3 border-t border-gray-700">
          <div className="flex items-center space-x-3 text-xs text-gray-400">
            {api.response_time && (
              <span>⚡ {api.response_time}ms</span>
            )}
            {api.usage_frequency && (
              <span>📊 {api.usage_frequency} req/day</span>
            )}
            {api.last_seen && (
              <span>🕐 {new Date(api.last_seen).toLocaleDateString()}</span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => saveAPIEndpoint(api)}
              className="p-1 text-gray-400 hover:text-white transition"
              title="Save to collection"
            >
              <Bookmark className="w-4 h-4" />
            </button>
            <button
              onClick={() => window.open(api.url, '_blank')}
              className="p-1 text-gray-400 hover:text-white transition"
              title="Open in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPatterns = () => (
    <div className="space-y-4">
      {patterns.map(pattern => {
        const isExpanded = expandedPatterns.has(pattern.id);

        return (
          <div key={pattern.id} className="bg-gray-800 rounded-lg border border-gray-700">
            <div
              className="p-4 cursor-pointer hover:bg-gray-700/50 transition"
              onClick={() => togglePatternExpansion(pattern.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {isExpanded ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}
                  <Lightbulb className="w-5 h-5 text-yellow-400" />
                  <div>
                    <h3 className="font-semibold text-white">{pattern.name}</h3>
                    <p className="text-sm text-gray-400">{pattern.description}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-400">{pattern.instances} instances</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(pattern.confidence)}`}>
                    {(pattern.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            {isExpanded && (
              <div className="border-t border-gray-700 p-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-white mb-2">Pattern Characteristics</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">URL Structure:</span>
                        <span className="text-white font-mono">{pattern.url_pattern}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Common Methods:</span>
                        <div className="flex space-x-1">
                          {pattern.common_methods.map(method => (
                            <span key={method} className={`px-1 py-0.5 rounded text-xs ${getMethodColor(method)}`}>
                              {method}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Avg Response Time:</span>
                        <span className="text-white">{pattern.avg_response_time}ms</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-white mb-2">Example Endpoints</h4>
                    <div className="space-y-1">
                      {pattern.examples.slice(0, 3).map((example, index) => (
                        <div key={index} className="text-xs text-gray-400 font-mono">
                          {example}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {pattern.ml_insights && (
                  <div>
                    <h4 className="font-medium text-white mb-2">ML Insights</h4>
                    <div className="bg-gray-900 p-3 rounded-lg">
                      <p className="text-sm text-gray-300">{pattern.ml_insights}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00'];

  if (loading && !discoveredAPIs.length) {
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
            <Brain className="w-8 h-8 text-purple-400" />
            <div>
              <h1 className="text-2xl font-bold text-white">Smart API Discovery</h1>
              <p className="text-gray-400 mt-1">AI-powered endpoint discovery and pattern recognition</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => runMLAnalysis()}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center space-x-2"
            >
              <Brain className="w-4 h-4" />
              <span>Run Analysis</span>
            </button>

            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              className="px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
            >
              <option value="grid">Grid View</option>
              <option value="list">List View</option>
              <option value="patterns">Patterns</option>
            </select>

            <button
              onClick={fetchDiscoveredAPIs}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {discoveryStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">APIs Discovered</p>
                  <p className="text-2xl font-bold text-white">{discoveryStats.total_apis}</p>
                </div>
                <Target className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Patterns Found</p>
                  <p className="text-2xl font-bold text-white">{discoveryStats.patterns_found}</p>
                </div>
                <Lightbulb className="w-8 h-8 text-yellow-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Avg Confidence</p>
                  <p className="text-2xl font-bold text-white">{(discoveryStats.avg_confidence * 100).toFixed(0)}%</p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Active Domains</p>
                  <p className="text-2xl font-bold text-white">{discoveryStats.active_domains}</p>
                </div>
                <Globe className="w-8 h-8 text-purple-400" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Search and Filters */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Search APIs</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search endpoints..."
                className="w-full pl-10 pr-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Category</label>
            <select
              value={filters.category}
              onChange={(e) => setFilters({...filters, category: e.target.value})}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
            >
              <option value="all">All Categories</option>
              <option value="rest">REST</option>
              <option value="graphql">GraphQL</option>
              <option value="grpc">gRPC</option>
              <option value="websocket">WebSocket</option>
              <option value="webhook">Webhook</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Confidence</label>
            <select
              value={filters.confidence}
              onChange={(e) => setFilters({...filters, confidence: e.target.value})}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
            >
              <option value="all">All Confidence</option>
              <option value="high">High (80%+)</option>
              <option value="medium">Medium (60-80%)</option>
              <option value="low">Low (<60%)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="deprecated">Deprecated</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Actions</label>
            <button
              onClick={() => runMLAnalysis()}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center justify-center space-x-2"
            >
              <Brain className="w-4 h-4" />
              <span>Analyze</span>
            </button>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">AI Recommendations</h3>
          <div className="space-y-3">
            {recommendations.slice(0, 3).map(rec => (
              <div key={rec.id} className="bg-gray-900/50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <Star className="w-4 h-4 text-yellow-400" />
                      <span className="font-medium text-white">{rec.title}</span>
                      <span className={`px-2 py-1 rounded-full text-xs ${getConfidenceColor(rec.confidence)}`}>
                        {(rec.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-300 mb-2">{rec.description}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-400">
                      <span>Category: {rec.category}</span>
                      <span>Impact: {rec.impact}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => rateRecommendation(rec.id, 'positive')}
                      className="p-1 text-gray-400 hover:text-green-400 transition"
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => rateRecommendation(rec.id, 'negative')}
                      className="p-1 text-gray-400 hover:text-red-400 transition"
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Behavior Analysis */}
      {behaviorAnalysis && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">API Usage Patterns</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={behaviorAnalysis.usage_timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                <Legend />
                <Line type="monotone" dataKey="requests" stroke="#8B5CF6" strokeWidth={2} name="API Requests" />
                <Line type="monotone" dataKey="discoveries" stroke="#10B981" strokeWidth={2} name="New Discoveries" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Category Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={Object.entries(behaviorAnalysis.category_distribution || {}).map(([key, value]) => ({
                    name: key,
                    value
                  }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                >
                  {Object.entries(behaviorAnalysis.category_distribution || {}).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Main Content */}
      {viewMode === 'patterns' ? (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Discovered Patterns</h3>
          {renderPatterns()}
        </div>
      ) : (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Discovered APIs ({discoveredAPIs.length})</h3>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1 bg-gray-700 text-gray-300 rounded text-sm hover:bg-gray-600 transition">
                Export All
              </button>
            </div>
          </div>

          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {discoveredAPIs.map(renderAPICard)}
            </div>
          ) : (
            <div className="space-y-3">
              {discoveredAPIs.map(api => (
                <div key={api.id || api.url} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700/50 transition">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 rounded text-xs ${getCategoryColor(api.category)}`}>
                        {api.category}
                      </span>
                      <span className="font-mono text-sm text-white">{api.url}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${getConfidenceColor(api.confidence_score)}`}>
                        {(api.confidence_score * 100).toFixed(0)}%
                      </span>
                      <button
                        onClick={() => setSelectedAPI(api)}
                        className="p-1 text-gray-400 hover:text-white"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* API Detail Modal */}
      {selectedAPI && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">API Details</h3>
              <button
                onClick={() => setSelectedAPI(null)}
                className="text-gray-400 hover:text-white transition"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Endpoint URL</label>
                  <p className="text-white font-mono">{selectedAPI.url}</p>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">Category</label>
                  <span className={`px-2 py-1 rounded ${getCategoryColor(selectedAPI.category)}`}>
                    {selectedAPI.category}
                  </span>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">Confidence Score</label>
                  <span className={`px-2 py-1 rounded ${getConfidenceColor(selectedAPI.confidence_score)}`}>
                    {(selectedAPI.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>

                {selectedAPI.methods && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Supported Methods</label>
                    <div className="flex flex-wrap gap-1">
                      {selectedAPI.methods.map(method => (
                        <span key={method} className={`px-2 py-1 rounded text-xs ${getMethodColor(method)}`}>
                          {method}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                {selectedAPI.ml_features && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">ML Analysis</label>
                    <div className="bg-gray-900 p-3 rounded-lg">
                      <pre className="text-sm text-gray-300 overflow-x-auto">
                        {JSON.stringify(selectedAPI.ml_features, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {selectedAPI.behavioral_analysis && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Behavioral Analysis</label>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Usage Frequency:</span>
                        <span className="text-white">{selectedAPI.behavioral_analysis.usage_frequency}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Response Pattern:</span>
                        <span className="text-white">{selectedAPI.behavioral_analysis.response_pattern}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 mt-6">
              <button
                onClick={() => saveAPIEndpoint(selectedAPI)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                Save to Collection
              </button>
              <button
                onClick={() => window.open(selectedAPI.url, '_blank')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Test Endpoint
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartAPIDiscoveryDashboard;