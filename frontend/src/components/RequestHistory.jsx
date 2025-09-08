import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Clock,
  Search,
  Filter,
  Play,
  Trash2,
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  Calendar,
  TrendingUp,
  Zap,
  MoreVertical,
  Eye,
  RefreshCw,
  Download,
  Tag
} from 'lucide-react';

const RequestHistory = ({ onReplay = null }) => {
  const { token } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [expandedItems, setExpandedItems] = useState(new Set());
  const [copiedId, setCopiedId] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [page, setPage] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  const [replayingId, setReplayingId] = useState(null);
  const itemsPerPage = 20;

  useEffect(() => {
    fetchHistory();
  }, [page, searchTerm, selectedMethod, selectedStatus]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        skip: page * itemsPerPage,
        limit: itemsPerPage
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (selectedMethod) params.append('method', selectedMethod);
      if (selectedStatus) params.append('status_code', selectedStatus);

      const response = await axios.get(
        getApiUrl(`/api/request-history?${params}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setHistory(response.data.history);
      setTotalItems(response.data.total);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReplay = async (historyItem) => {
    setReplayingId(historyItem.id);
    try {
      const response = await axios.post(
        getApiUrl(`/api/request-history/${historyItem.id}/replay`),
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // If there's a callback, send the request data back to the parent
      if (onReplay) {
        onReplay({
          method: historyItem.method,
          url: historyItem.url,
          headers: historyItem.headers,
          body: historyItem.body,
          response: response.data
        });
      }
      
      // Refresh history to show new entry
      fetchHistory();
    } catch (error) {
      console.error('Failed to replay request:', error);
    } finally {
      setReplayingId(null);
    }
  };

  const handleDelete = async (historyId) => {
    if (!confirm('Are you sure you want to delete this request from history?')) return;
    
    try {
      await axios.delete(
        getApiUrl(`/api/request-history/${historyId}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // Refresh history
      fetchHistory();
    } catch (error) {
      console.error('Failed to delete history item:', error);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear all request history? This cannot be undone.')) return;
    
    try {
      await axios.delete(
        getApiUrl('/api/request-history'),
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // Reset and refresh
      setHistory([]);
      setTotalItems(0);
      setPage(0);
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleExpanded = (id) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const getMethodColor = (method) => {
    const colors = {
      GET: 'text-green-400 bg-green-500/20',
      POST: 'text-yellow-400 bg-yellow-500/20',
      PUT: 'text-blue-400 bg-blue-500/20',
      PATCH: 'text-purple-400 bg-purple-500/20',
      DELETE: 'text-red-400 bg-red-500/20'
    };
    return colors[method] || 'text-gray-400 bg-gray-500/20';
  };

  const getStatusIcon = (statusCode) => {
    if (!statusCode) return <AlertCircle className="w-4 h-4 text-gray-400" />;
    if (statusCode >= 200 && statusCode < 300) {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    } else if (statusCode >= 400) {
      return <XCircle className="w-4 h-4 text-red-400" />;
    }
    return <AlertCircle className="w-4 h-4 text-yellow-400" />;
  };

  const formatResponseTime = (ms) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatSize = (bytes) => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)}MB`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) return 'Just now';
    // Less than 1 hour
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    // Less than 1 day
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    // Less than 1 week
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} days ago`;
    
    return date.toLocaleDateString();
  };

  if (loading && history.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="h-full max-h-[calc(100vh-300px)] overflow-y-auto">
      <div className="space-y-6 p-2">
      {/* Header */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">Request History</h2>
            <p className="text-gray-400 mt-1">View and replay your previous API requests</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchHistory}
              className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            {history.length > 0 && (
              <button
                onClick={handleClearAll}
                className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Clear All
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[300px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(0);
                }}
                placeholder="Search by URL or name..."
                className="w-full pl-10 pr-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Method Filter */}
          <select
            value={selectedMethod}
            onChange={(e) => {
              setSelectedMethod(e.target.value);
              setPage(0);
            }}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
          >
            <option value="">All Methods</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="PATCH">PATCH</option>
            <option value="DELETE">DELETE</option>
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setPage(0);
            }}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
          >
            <option value="">All Status</option>
            <option value="200">Success (2xx)</option>
            <option value="400">Client Error (4xx)</option>
            <option value="500">Server Error (5xx)</option>
          </select>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 mt-4 text-sm text-gray-400">
          <span className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            {totalItems} total requests
          </span>
          <span className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            {history.filter(h => h.success).length} successful
          </span>
          <span className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            {history.length > 0 
              ? `${Math.round(history.reduce((acc, h) => acc + (h.response_time_ms || 0), 0) / history.length)}ms avg`
              : 'N/A'
            }
          </span>
        </div>
      </div>

      {/* History List */}
      {history.length === 0 ? (
        <div className="text-center py-20">
          <Clock className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400">No request history yet</p>
          <p className="text-gray-500 text-sm mt-2">Your API requests will appear here</p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((item) => {
            const isExpanded = expandedItems.has(item.id);
            
            return (
              <div
                key={item.id}
                className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 overflow-hidden"
              >
                {/* Header */}
                <div
                  className="p-4 cursor-pointer hover:bg-gray-700/30 transition"
                  onClick={() => toggleExpanded(item.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      {/* Expand Icon */}
                      {isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                      )}
                      
                      {/* Method */}
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getMethodColor(item.method)}`}>
                        {item.method}
                      </span>
                      
                      {/* Status */}
                      <div className="flex items-center gap-2">
                        {getStatusIcon(item.status_code)}
                        <span className="text-sm text-gray-300">
                          {item.status_code || 'Failed'}
                        </span>
                      </div>
                      
                      {/* URL */}
                      <div className="flex-1 min-w-0">
                        <p className="text-white truncate">{item.url}</p>
                        {item.name && (
                          <p className="text-gray-400 text-sm">{item.name}</p>
                        )}
                      </div>
                      
                      {/* Response Time */}
                      <span className="text-sm text-gray-400">
                        {formatResponseTime(item.response_time_ms)}
                      </span>
                      
                      {/* Size */}
                      <span className="text-sm text-gray-400">
                        {formatSize(item.response_size_bytes)}
                      </span>
                      
                      {/* Time */}
                      <span className="text-sm text-gray-500">
                        {formatDate(item.created_at)}
                      </span>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center gap-2 ml-4" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleReplay(item)}
                        disabled={replayingId === item.id}
                        className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition"
                        title="Replay Request"
                      >
                        {replayingId === item.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => copyToClipboard(item.url, item.id)}
                        className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
                        title="Copy URL"
                      >
                        {copiedId === item.id ? (
                          <Check className="w-4 h-4 text-green-400" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-red-500/20 hover:text-red-400 transition"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t border-gray-700 p-4 space-y-4">
                    {/* Headers */}
                    {item.headers && Object.keys(item.headers).length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">Request Headers</h4>
                        <div className="bg-gray-900/50 rounded-lg p-3">
                          <pre className="text-xs text-gray-400 font-mono overflow-x-auto">
                            {JSON.stringify(item.headers, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                    
                    {/* Request Body */}
                    {item.body && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">Request Body</h4>
                        <div className="bg-gray-900/50 rounded-lg p-3">
                          <pre className="text-xs text-gray-400 font-mono overflow-x-auto">
                            {typeof item.body === 'string' 
                              ? item.body 
                              : JSON.stringify(JSON.parse(item.body), null, 2)
                            }
                          </pre>
                        </div>
                      </div>
                    )}
                    
                    {/* Response */}
                    {item.response_body && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">Response</h4>
                        <div className="bg-gray-900/50 rounded-lg p-3">
                          <pre className="text-xs text-gray-400 font-mono overflow-x-auto max-h-64 overflow-y-auto">
                            {typeof item.response_body === 'string' 
                              ? (item.response_body.startsWith('{') || item.response_body.startsWith('[')
                                ? JSON.stringify(JSON.parse(item.response_body), null, 2)
                                : item.response_body)
                              : JSON.stringify(item.response_body, null, 2)
                            }
                          </pre>
                        </div>
                      </div>
                    )}
                    
                    {/* Error Message */}
                    {item.error_message && (
                      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                        <p className="text-red-400 text-sm">{item.error_message}</p>
                      </div>
                    )}
                    
                    {/* Tags */}
                    {item.tags && item.tags.length > 0 && (
                      <div className="flex items-center gap-2">
                        <Tag className="w-4 h-4 text-gray-400" />
                        {item.tags.map((tag, index) => (
                          <span key={index} className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalItems > itemsPerPage && (
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed transition"
          >
            Previous
          </button>
          <span className="text-gray-400">
            Page {page + 1} of {Math.ceil(totalItems / itemsPerPage)}
          </span>
          <button
            onClick={() => setPage(Math.min(Math.ceil(totalItems / itemsPerPage) - 1, page + 1))}
            disabled={page >= Math.ceil(totalItems / itemsPerPage) - 1}
            className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      )}
      </div>
    </div>
  );
};

export default RequestHistory;