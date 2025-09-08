import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Plus,
  Play,
  Pause,
  Edit2,
  Trash2,
  RefreshCw,
  Bell,
  BellOff,
  BarChart3,
  Zap,
  Shield,
  Loader2,
  Eye,
  Settings,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

const MonitoringDashboard = ({ onCreateFromRequest = null }) => {
  const { token } = useAuth();
  const [monitors, setMonitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonitor, setSelectedMonitor] = useState(null);
  const [monitorResults, setMonitorResults] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [expandedMonitors, setExpandedMonitors] = useState(new Set());
  const [runningMonitors, setRunningMonitors] = useState(new Set());
  
  // Form state for new monitor
  const [newMonitor, setNewMonitor] = useState({
    name: '',
    description: '',
    url: '',
    method: 'GET',
    headers: {},
    body: '',
    expected_status: 200,
    expected_response_time_ms: 1000,
    interval_minutes: 60,
    assertions: [],
    notify_on_failure: true
  });

  useEffect(() => {
    fetchMonitors();
  }, []);

  const fetchMonitors = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        getApiUrl('/api/monitors'),
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setMonitors(response.data.monitors);
    } catch (error) {
      console.error('Failed to fetch monitors:', error);
    } finally {
      setLoading(false);
    }
  };

  const createMonitor = async () => {
    try {
      const response = await axios.post(
        getApiUrl('/api/monitors'),
        newMonitor,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setMonitors([...monitors, response.data]);
      setShowCreateModal(false);
      resetNewMonitor();
    } catch (error) {
      console.error('Failed to create monitor:', error);
    }
  };

  const runMonitor = async (monitorId) => {
    setRunningMonitors(new Set([...runningMonitors, monitorId]));
    try {
      const response = await axios.post(
        getApiUrl(`/api/monitors/${monitorId}/run`),
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // Refresh monitors to show updated status
      fetchMonitors();
      
      // If this monitor is selected, refresh its results
      if (selectedMonitor?.id === monitorId) {
        fetchMonitorResults(monitorId);
      }
    } catch (error) {
      console.error('Failed to run monitor:', error);
    } finally {
      const newRunning = new Set(runningMonitors);
      newRunning.delete(monitorId);
      setRunningMonitors(newRunning);
    }
  };

  const toggleMonitor = async (monitor) => {
    try {
      const response = await axios.put(
        getApiUrl(`/api/monitors/${monitor.id}`),
        { is_active: !monitor.is_active },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // Update local state
      setMonitors(monitors.map(m => 
        m.id === monitor.id ? { ...m, is_active: !m.is_active } : m
      ));
    } catch (error) {
      console.error('Failed to toggle monitor:', error);
    }
  };

  const deleteMonitor = async (monitorId) => {
    if (!confirm('Are you sure you want to delete this monitor?')) return;
    
    try {
      await axios.delete(
        getApiUrl(`/api/monitors/${monitorId}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setMonitors(monitors.filter(m => m.id !== monitorId));
      if (selectedMonitor?.id === monitorId) {
        setSelectedMonitor(null);
        setMonitorResults([]);
      }
    } catch (error) {
      console.error('Failed to delete monitor:', error);
    }
  };

  const fetchMonitorResults = async (monitorId) => {
    try {
      const response = await axios.get(
        getApiUrl(`/api/monitors/${monitorId}/results`),
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setSelectedMonitor(response.data.monitor);
      setMonitorResults(response.data.results);
    } catch (error) {
      console.error('Failed to fetch monitor results:', error);
    }
  };

  const resetNewMonitor = () => {
    setNewMonitor({
      name: '',
      description: '',
      url: '',
      method: 'GET',
      headers: {},
      body: '',
      expected_status: 200,
      expected_response_time_ms: 1000,
      interval_minutes: 60,
      assertions: [],
      notify_on_failure: true
    });
  };

  const addAssertion = () => {
    setNewMonitor({
      ...newMonitor,
      assertions: [
        ...newMonitor.assertions,
        { type: 'status_code', value: '200' }
      ]
    });
  };

  const removeAssertion = (index) => {
    setNewMonitor({
      ...newMonitor,
      assertions: newMonitor.assertions.filter((_, i) => i !== index)
    });
  };

  const updateAssertion = (index, field, value) => {
    const newAssertions = [...newMonitor.assertions];
    newAssertions[index] = { ...newAssertions[index], [field]: value };
    setNewMonitor({ ...newMonitor, assertions: newAssertions });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'text-green-400';
      case 'failure': return 'text-red-400';
      case 'error': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'failure': return <XCircle className="w-5 h-5 text-red-400" />;
      case 'error': return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getUptimeColor = (percentage) => {
    if (percentage >= 99) return 'text-green-400';
    if (percentage >= 95) return 'text-yellow-400';
    return 'text-red-400';
  };

  const formatUptime = (percentage) => {
    return percentage ? `${percentage.toFixed(2)}%` : 'N/A';
  };

  const toggleExpanded = (monitorId) => {
    const newExpanded = new Set(expandedMonitors);
    if (newExpanded.has(monitorId)) {
      newExpanded.delete(monitorId);
    } else {
      newExpanded.add(monitorId);
      fetchMonitorResults(monitorId);
    }
    setExpandedMonitors(newExpanded);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  // Calculate overall stats
  const totalMonitors = monitors.length;
  const activeMonitors = monitors.filter(m => m.is_active).length;
  const failingMonitors = monitors.filter(m => m.last_status === 'failure').length;
  const avgUptime = monitors.length > 0 
    ? monitors.reduce((acc, m) => acc + (m.uptime_percentage || 0), 0) / monitors.length 
    : 0;

  return (
    <div className="h-full max-h-[calc(100vh-300px)] overflow-y-auto">
      <div className="space-y-6 p-2">
      {/* Header with Stats */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">API Monitoring</h2>
            <p className="text-gray-400 mt-1">Monitor your APIs health and performance</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Monitor
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-900/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-5 h-5 text-purple-400" />
              <span className="text-2xl font-bold text-white">{totalMonitors}</span>
            </div>
            <p className="text-sm text-gray-400">Total Monitors</p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <span className="text-2xl font-bold text-white">{activeMonitors}</span>
            </div>
            <p className="text-sm text-gray-400">Active</p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <XCircle className="w-5 h-5 text-red-400" />
              <span className="text-2xl font-bold text-white">{failingMonitors}</span>
            </div>
            <p className="text-sm text-gray-400">Failing</p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              <span className={`text-2xl font-bold ${getUptimeColor(avgUptime)}`}>
                {formatUptime(avgUptime)}
              </span>
            </div>
            <p className="text-sm text-gray-400">Avg Uptime</p>
          </div>
        </div>
      </div>

      {/* Monitors List */}
      {monitors.length === 0 ? (
        <div className="text-center py-20">
          <Activity className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400">No monitors configured</p>
          <p className="text-gray-500 text-sm mt-2">Create your first monitor to start tracking API health</p>
        </div>
      ) : (
        <div className="space-y-4">
          {monitors.map((monitor) => {
            const isExpanded = expandedMonitors.has(monitor.id);
            const isRunning = runningMonitors.has(monitor.id);
            
            return (
              <div
                key={monitor.id}
                className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 overflow-hidden"
              >
                {/* Monitor Header */}
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      <button
                        onClick={() => toggleExpanded(monitor.id)}
                        className="text-gray-400 hover:text-white transition"
                      >
                        {isExpanded ? (
                          <ChevronDown className="w-5 h-5" />
                        ) : (
                          <ChevronRight className="w-5 h-5" />
                        )}
                      </button>
                      
                      {getStatusIcon(monitor.last_status)}
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-medium text-white">{monitor.name}</h3>
                          <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                            {monitor.method}
                          </span>
                          {monitor.is_active ? (
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
                              Active
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-gray-500/20 text-gray-400 text-xs rounded">
                              Paused
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-400 mt-1">{monitor.url}</p>
                        {monitor.description && (
                          <p className="text-sm text-gray-500 mt-1">{monitor.description}</p>
                        )}
                      </div>
                      
                      {/* Monitor Stats */}
                      <div className="flex items-center gap-6 text-sm">
                        <div className="text-center">
                          <p className={`font-medium ${getUptimeColor(monitor.uptime_percentage)}`}>
                            {formatUptime(monitor.uptime_percentage)}
                          </p>
                          <p className="text-gray-500 text-xs">Uptime</p>
                        </div>
                        
                        <div className="text-center">
                          <p className="font-medium text-white">
                            {monitor.last_response_time_ms || 'N/A'}ms
                          </p>
                          <p className="text-gray-500 text-xs">Response</p>
                        </div>
                        
                        <div className="text-center">
                          <p className="font-medium text-white">
                            {monitor.interval_minutes}m
                          </p>
                          <p className="text-gray-500 text-xs">Interval</p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => runMonitor(monitor.id)}
                        disabled={isRunning}
                        className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed transition"
                        title="Run Now"
                      >
                        {isRunning ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                      
                      <button
                        onClick={() => toggleMonitor(monitor)}
                        className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
                        title={monitor.is_active ? "Pause Monitor" : "Resume Monitor"}
                      >
                        {monitor.is_active ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                      
                      <button
                        onClick={() => deleteMonitor(monitor.id)}
                        className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-red-500/20 hover:text-red-400 transition"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Last Check Info */}
                  {monitor.last_check_at && (
                    <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                      <span>Last checked: {new Date(monitor.last_check_at).toLocaleString()}</span>
                      {monitor.consecutive_failures > 0 && (
                        <span className="text-red-400">
                          {monitor.consecutive_failures} consecutive failures
                        </span>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Expanded Results */}
                {isExpanded && monitorResults.length > 0 && selectedMonitor?.id === monitor.id && (
                  <div className="border-t border-gray-700 p-4">
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">Recent Results</h4>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {monitorResults.map((result) => (
                        <div
                          key={result.id}
                          className="flex items-center justify-between p-2 bg-gray-900/50 rounded"
                        >
                          <div className="flex items-center gap-3">
                            {result.success ? (
                              <CheckCircle className="w-4 h-4 text-green-400" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-400" />
                            )}
                            <span className="text-sm text-gray-300">
                              {new Date(result.checked_at).toLocaleString()}
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-gray-400">
                              Status: {result.status_code || 'Error'}
                            </span>
                            <span className="text-gray-400">
                              {result.response_time_ms}ms
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {/* Assertions Summary */}
                    {monitorResults[0]?.assertions_passed && (
                      <div className="mt-4">
                        <h5 className="text-xs font-semibold text-gray-400 mb-2">Assertions</h5>
                        <div className="space-y-1">
                          {monitorResults[0].assertions_passed.map((assertion, index) => (
                            <div key={index} className="flex items-center gap-2 text-xs">
                              {assertion.passed ? (
                                <CheckCircle className="w-3 h-3 text-green-400" />
                              ) : (
                                <XCircle className="w-3 h-3 text-red-400" />
                              )}
                              <span className="text-gray-400">
                                {assertion.expected} {assertion.actual && `(got: ${assertion.actual})`}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create Monitor Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white mb-4">Create New Monitor</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
                <input
                  type="text"
                  value={newMonitor.name}
                  onChange={(e) => setNewMonitor({ ...newMonitor, name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  placeholder="Production API Health Check"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">URL</label>
                <input
                  type="text"
                  value={newMonitor.url}
                  onChange={(e) => setNewMonitor({ ...newMonitor, url: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  placeholder="https://api.example.com/health"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Method</label>
                  <select
                    value={newMonitor.method}
                    onChange={(e) => setNewMonitor({ ...newMonitor, method: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Check Interval</label>
                  <select
                    value={newMonitor.interval_minutes}
                    onChange={(e) => setNewMonitor({ ...newMonitor, interval_minutes: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  >
                    <option value="5">Every 5 minutes</option>
                    <option value="15">Every 15 minutes</option>
                    <option value="30">Every 30 minutes</option>
                    <option value="60">Every hour</option>
                    <option value="360">Every 6 hours</option>
                    <option value="1440">Daily</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Expected Status</label>
                  <input
                    type="number"
                    value={newMonitor.expected_status}
                    onChange={(e) => setNewMonitor({ ...newMonitor, expected_status: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                    placeholder="200"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Max Response Time (ms)</label>
                  <input
                    type="number"
                    value={newMonitor.expected_response_time_ms}
                    onChange={(e) => setNewMonitor({ ...newMonitor, expected_response_time_ms: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                    placeholder="1000"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Description (Optional)</label>
                <textarea
                  value={newMonitor.description}
                  onChange={(e) => setNewMonitor({ ...newMonitor, description: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  rows="2"
                  placeholder="Monitor description..."
                />
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="notify"
                  checked={newMonitor.notify_on_failure}
                  onChange={(e) => setNewMonitor({ ...newMonitor, notify_on_failure: e.target.checked })}
                  className="rounded text-purple-600 focus:ring-purple-500"
                />
                <label htmlFor="notify" className="text-sm text-gray-300">
                  Notify me on failure
                </label>
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  resetNewMonitor();
                }}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
              >
                Cancel
              </button>
              <button
                onClick={createMonitor}
                disabled={!newMonitor.name || !newMonitor.url}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition"
              >
                Create Monitor
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default MonitoringDashboard;