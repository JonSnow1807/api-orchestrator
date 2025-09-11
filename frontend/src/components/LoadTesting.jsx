import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Zap,
  Play,
  Pause,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Clock,
  Users,
  Activity,
  CheckCircle,
  XCircle,
  Loader,
  Download,
  Settings
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const LoadTesting = ({ projectId = null }) => {
  const { token } = useAuth();
  const [activeTest, setActiveTest] = useState(null);
  const [testResults, setTestResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [presets, setPresets] = useState([]);
  
  // Test configuration
  const [config, setConfig] = useState({
    url: '',
    method: 'GET',
    headers: {},
    body: null,
    test_type: 'load',
    duration_seconds: 60,
    target_rps: 10,
    concurrent_users: 10,
    ramp_up_seconds: 10
  });

  useEffect(() => {
    fetchPresets();
  }, []);

  useEffect(() => {
    if (activeTest && polling) {
      const interval = setInterval(() => {
        checkTestStatus();
      }, 2000); // Poll every 2 seconds
      
      return () => clearInterval(interval);
    }
  }, [activeTest, polling]);

  const fetchPresets = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/load-testing/presets'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPresets(response.data.presets);
    } catch (error) {
      console.error('Failed to fetch presets:', error);
    }
  };

  const startLoadTest = async () => {
    setLoading(true);
    setTestResults(null);
    
    try {
      const response = await axios.post(
        getApiUrl('/api/load-testing/start'),
        { ...config, project_id: projectId, save_results: !!projectId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setActiveTest(response.data.test_id);
      setPolling(true);
    } catch (error) {
      console.error('Failed to start load test:', error);
    } finally {
      setLoading(false);
    }
  };

  const stopLoadTest = async () => {
    if (!activeTest) return;
    
    try {
      await axios.post(
        getApiUrl(`/api/load-testing/stop/${activeTest}`),
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setPolling(false);
      await fetchResults();
    } catch (error) {
      console.error('Failed to stop load test:', error);
    }
  };

  const checkTestStatus = async () => {
    if (!activeTest) return;
    
    try {
      const response = await axios.get(
        getApiUrl(`/api/load-testing/status/${activeTest}`),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.status === 'completed') {
        setPolling(false);
        await fetchResults();
      }
    } catch (error) {
      console.error('Failed to check test status:', error);
    }
  };

  const fetchResults = async () => {
    if (!activeTest) return;
    
    try {
      const response = await axios.get(
        getApiUrl(`/api/load-testing/results/${activeTest}`),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setTestResults(response.data.summary);
      setActiveTest(null);
    } catch (error) {
      console.error('Failed to fetch results:', error);
    }
  };

  const applyPreset = (preset) => {
    setSelectedPreset(preset.name);
    setConfig(prev => ({
      ...prev,
      ...preset.config
    }));
  };

  const testTypes = [
    { id: 'load', name: 'Load Test', icon: TrendingUp, description: 'Gradual increase to target load' },
    { id: 'stress', name: 'Stress Test', icon: AlertTriangle, description: 'Push beyond normal capacity' },
    { id: 'spike', name: 'Spike Test', icon: Zap, description: 'Sudden traffic increase' },
    { id: 'soak', name: 'Soak Test', icon: Clock, description: 'Extended duration testing' },
    { id: 'performance', name: 'Performance Test', icon: BarChart3, description: 'Measure response times and throughput' },
    { id: 'endurance', name: 'Endurance Test', icon: Activity, description: 'Long-running stability test' },
    { id: 'scalability', name: 'Scalability Test', icon: Users, description: 'Test system scaling capabilities' },
    { id: 'volume', name: 'Volume Test', icon: Settings, description: 'Test with large data volumes' }
  ];

  return (
    <div className="space-y-6">
      {/* Test Type Selector */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Select Test Type</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {testTypes.map(type => {
            const Icon = type.icon;
            return (
              <button
                key={type.id}
                onClick={() => setConfig(prev => ({ ...prev, test_type: type.id }))}
                className={`p-4 rounded-lg border transition ${
                  config.test_type === type.id
                    ? 'bg-purple-600/20 border-purple-500 text-purple-400'
                    : 'bg-gray-700 border-gray-600 text-gray-400 hover:bg-gray-600'
                }`}
              >
                <Icon className="w-8 h-8 mx-auto mb-2" />
                <p className="font-medium">{type.name}</p>
                <p className="text-xs mt-1 opacity-75">{type.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">Configuration</h3>
          
          {/* Preset Selector */}
          <select
            value={selectedPreset || ''}
            onChange={(e) => {
              const preset = presets.find(p => p.name === e.target.value);
              if (preset) applyPreset(preset);
            }}
            className="px-3 py-1 bg-gray-700 text-white rounded-lg border border-gray-600"
          >
            <option value="">Select Preset</option>
            {presets.map(preset => (
              <option key={preset.name} value={preset.name}>
                {preset.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Target URL
            </label>
            <input
              type="text"
              value={config.url}
              onChange={(e) => setConfig(prev => ({ ...prev, url: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder="https://api.example.com/endpoint"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              HTTP Method
            </label>
            <select
              value={config.method}
              onChange={(e) => setConfig(prev => ({ ...prev, method: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Duration (seconds)
            </label>
            <input
              type="number"
              value={config.duration_seconds}
              onChange={(e) => setConfig(prev => ({ ...prev, duration_seconds: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              min="10"
              max="600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Target RPS
            </label>
            <input
              type="number"
              value={config.target_rps}
              onChange={(e) => setConfig(prev => ({ ...prev, target_rps: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              min="1"
              max="1000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Concurrent Users
            </label>
            <input
              type="number"
              value={config.concurrent_users}
              onChange={(e) => setConfig(prev => ({ ...prev, concurrent_users: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              min="1"
              max="500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Ramp-up Time (seconds)
            </label>
            <input
              type="number"
              value={config.ramp_up_seconds}
              onChange={(e) => setConfig(prev => ({ ...prev, ramp_up_seconds: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              min="0"
              max="60"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center mt-6">
          {!activeTest ? (
            <button
              onClick={startLoadTest}
              disabled={loading || !config.url}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50 flex items-center space-x-2"
            >
              <Play className="w-4 h-4" />
              <span>Start Load Test</span>
            </button>
          ) : (
            <button
              onClick={stopLoadTest}
              className="px-6 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition flex items-center space-x-2"
            >
              <Pause className="w-4 h-4" />
              <span>Stop Test</span>
            </button>
          )}
        </div>
      </div>

      {/* Live Status */}
      {activeTest && polling && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-center">
            <Loader className="w-8 h-8 text-purple-400 animate-spin mr-3" />
            <span className="text-white">Load test in progress...</span>
          </div>
        </div>
      )}

      {/* Results */}
      {testResults && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Requests</p>
                  <p className="text-2xl font-bold text-white">{testResults.total_requests}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Success Rate</p>
                  <p className="text-2xl font-bold text-green-400">
                    {((testResults.successful_requests / testResults.total_requests) * 100).toFixed(1)}%
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Avg Response Time</p>
                  <p className="text-2xl font-bold text-white">
                    {testResults.response_times.mean.toFixed(0)}ms
                  </p>
                </div>
                <Clock className="w-8 h-8 text-yellow-400" />
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Requests/sec</p>
                  <p className="text-2xl font-bold text-white">
                    {testResults.requests_per_second.toFixed(1)}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-400" />
              </div>
            </div>
          </div>

          {/* Response Time Distribution */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Response Time Distribution</h3>
            <div className="grid grid-cols-6 gap-4 text-center">
              <div>
                <p className="text-gray-400 text-sm">Min</p>
                <p className="text-white font-medium">{testResults.response_times.min.toFixed(0)}ms</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Median</p>
                <p className="text-white font-medium">{testResults.response_times.median.toFixed(0)}ms</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Mean</p>
                <p className="text-white font-medium">{testResults.response_times.mean.toFixed(0)}ms</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">P95</p>
                <p className="text-white font-medium">{testResults.response_times.p95.toFixed(0)}ms</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">P99</p>
                <p className="text-white font-medium">{testResults.response_times.p99.toFixed(0)}ms</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Max</p>
                <p className="text-white font-medium">{testResults.response_times.max.toFixed(0)}ms</p>
              </div>
            </div>
          </div>

          {/* Charts */}
          {testResults.time_series?.response_times?.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Response Times Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={testResults.time_series.response_times}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                  <Line type="monotone" dataKey="avg_response_time" stroke="#8B5CF6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Status Code Distribution */}
          {testResults.status_codes && Object.keys(testResults.status_codes).length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Status Code Distribution</h3>
              <div className="space-y-2">
                {Object.entries(testResults.status_codes).map(([code, count]) => (
                  <div key={code} className="flex items-center justify-between">
                    <span className={`text-sm ${code.startsWith('2') ? 'text-green-400' : code.startsWith('4') ? 'text-yellow-400' : 'text-red-400'}`}>
                      Status {code}
                    </span>
                    <div className="flex items-center">
                      <div className="w-32 bg-gray-700 rounded-full h-2 mr-3">
                        <div
                          className={`h-2 rounded-full ${code.startsWith('2') ? 'bg-green-400' : code.startsWith('4') ? 'bg-yellow-400' : 'bg-red-400'}`}
                          style={{ width: `${(count / testResults.total_requests) * 100}%` }}
                        />
                      </div>
                      <span className="text-gray-400 text-sm">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LoadTesting;