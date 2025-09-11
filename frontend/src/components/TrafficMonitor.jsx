import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, TrendingUp, AlertCircle, Zap, Globe, 
  Monitor, Clock, BarChart3, PieChart, Download,
  AlertTriangle, CheckCircle, XCircle, Wifi
} from 'lucide-react';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const TrafficMonitor = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState({
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    avg_response_time_ms: 0,
    requests_per_second: 0,
    error_rate: 0,
    p95_response_time: 0,
    total_bandwidth_mb: 0
  });
  const [endpoints, setEndpoints] = useState([]);
  const [statusCodes, setStatusCodes] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [timeSeriesData, setTimeSeriesData] = useState({
    rps: [],
    response_time: [],
    error_rate: []
  });
  const [selectedMetric, setSelectedMetric] = useState('rps');
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    fetchInitialData();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    const ws = new WebSocket(`ws://localhost:8000/api/traffic/ws`);
    
    ws.onopen = () => {
      console.log('Traffic monitor connected');
      setIsConnected(true);
      
      // Request initial data
      ws.send(JSON.stringify({ type: 'get_stats', window: 60 }));
      ws.send(JSON.stringify({ type: 'get_endpoints', top_n: 10 }));
      ws.send(JSON.stringify({ type: 'get_time_series', metric: 'rps', duration: 60 }));
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'initial':
          setStats(message.stats);
          setEndpoints(message.endpoints);
          setStatusCodes(message.status_codes);
          break;
          
        case 'stats_update':
          setStats(message.stats);
          break;
          
        case 'metric':
          // Update real-time metrics
          updateRealTimeMetrics(message.data);
          break;
          
        case 'alert':
          setAlerts(prev => [message.alert, ...prev].slice(0, 10));
          break;
          
        case 'time_series':
          setTimeSeriesData(prev => ({
            ...prev,
            [message.metric]: message.data
          }));
          break;
          
        case 'endpoints':
          setEndpoints(message.data);
          break;
          
        case 'heartbeat':
          // Keep connection alive
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
    
    wsRef.current = ws;
  };

  const fetchInitialData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch stats
      const statsRes = await fetch('http://localhost:8000/api/traffic/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
      
      // Fetch endpoints
      const endpointsRes = await fetch('http://localhost:8000/api/traffic/endpoints', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (endpointsRes.ok) {
        setEndpoints(await endpointsRes.json());
      }
      
      // Fetch alerts
      const alertsRes = await fetch('http://localhost:8000/api/traffic/alerts', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (alertsRes.ok) {
        setAlerts(await alertsRes.json());
      }
    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
  };

  const updateRealTimeMetrics = (metric) => {
    // Update stats based on new metric
    setStats(prev => ({
      ...prev,
      total_requests: prev.total_requests + 1,
      successful_requests: metric.status_code < 400 
        ? prev.successful_requests + 1 
        : prev.successful_requests,
      failed_requests: metric.status_code >= 400 
        ? prev.failed_requests + 1 
        : prev.failed_requests
    }));
  };

  const exportData = async (format) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:8000/api/traffic/export?format=${format}&window_seconds=3600`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      if (response.ok) {
        const data = await response.json();
        
        if (format === 'csv') {
          // Download CSV
          const blob = new Blob([data.data], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `traffic-data-${Date.now()}.csv`;
          a.click();
        } else {
          // Download JSON
          const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `traffic-data-${Date.now()}.json`;
          a.click();
        }
      }
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  // Chart configurations
  const lineChartData = {
    labels: timeSeriesData[selectedMetric]?.map(d => 
      new Date(d.timestamp).toLocaleTimeString()
    ) || [],
    datasets: [{
      label: selectedMetric === 'rps' ? 'Requests/sec' : 
             selectedMetric === 'response_time' ? 'Response Time (ms)' : 
             'Error Rate (%)',
      data: timeSeriesData[selectedMetric]?.map(d => d.value) || [],
      borderColor: selectedMetric === 'error_rate' ? 'rgb(239, 68, 68)' : 'rgb(59, 130, 246)',
      backgroundColor: selectedMetric === 'error_rate' 
        ? 'rgba(239, 68, 68, 0.1)' 
        : 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const statusCodeChartData = {
    labels: Object.keys(statusCodes),
    datasets: [{
      data: Object.values(statusCodes),
      backgroundColor: [
        'rgba(34, 197, 94, 0.8)',   // 2xx - green
        'rgba(59, 130, 246, 0.8)',  // 3xx - blue
        'rgba(251, 191, 36, 0.8)',  // 4xx - yellow
        'rgba(239, 68, 68, 0.8)',   // 5xx - red
        'rgba(156, 163, 175, 0.8)'  // 1xx - gray
      ]
    }]
  };

  const getStatusIcon = (code) => {
    if (code.startsWith('2')) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (code.startsWith('3')) return <AlertCircle className="w-4 h-4 text-blue-500" />;
    if (code.startsWith('4')) return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    if (code.startsWith('5')) return <XCircle className="w-4 h-4 text-red-500" />;
    return <Activity className="w-4 h-4 text-gray-500" />;
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Real-Time Traffic Monitor</h1>
            <p className="text-sm text-gray-500">Advanced observability beyond Postman</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
            isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            <Wifi className="w-4 h-4" />
            <span className="text-sm font-medium">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          <button
            onClick={() => exportData('json')}
            className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">Requests/sec</span>
            <Zap className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {stats.requests_per_second.toFixed(1)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Total: {stats.total_requests.toLocaleString()}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">Avg Response</span>
            <Clock className="w-4 h-4 text-green-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {stats.avg_response_time_ms.toFixed(0)}ms
          </div>
          <div className="text-xs text-gray-500 mt-1">
            P95: {stats.p95_response_time.toFixed(0)}ms
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">Error Rate</span>
            <AlertCircle className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {(stats.error_rate * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Errors: {stats.failed_requests.toLocaleString()}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">Bandwidth</span>
            <Globe className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {stats.total_bandwidth_mb.toFixed(1)} MB
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Last hour
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time Series Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Traffic Trends</h3>
            <div className="flex gap-2">
              {['rps', 'response_time', 'error_rate'].map(metric => (
                <button
                  key={metric}
                  onClick={() => setSelectedMetric(metric)}
                  className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                    selectedMetric === metric
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {metric === 'rps' ? 'RPS' : 
                   metric === 'response_time' ? 'Response' : 
                   'Errors'}
                </button>
              ))}
            </div>
          </div>
          <Line 
            data={lineChartData} 
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false }
              },
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }}
            height={250}
          />
        </div>

        {/* Status Codes Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Status Codes</h3>
          <Doughnut 
            data={statusCodeChartData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'bottom',
                  labels: {
                    generateLabels: (chart) => {
                      const data = chart.data;
                      return data.labels.map((label, i) => ({
                        text: `${label}: ${data.datasets[0].data[i]}`,
                        fillStyle: data.datasets[0].backgroundColor[i],
                        hidden: false,
                        index: i
                      }));
                    }
                  }
                }
              }
            }}
            height={250}
          />
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Endpoints */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Endpoints</h3>
          <div className="space-y-2">
            {endpoints.slice(0, 5).map((endpoint, index) => (
              <div key={index} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono text-gray-600">
                    {endpoint.endpoint}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500">
                    {endpoint.count} reqs
                  </span>
                  <span className="text-xs text-gray-500">
                    {endpoint.avg_response_time.toFixed(0)}ms
                  </span>
                  <span className={`text-xs ${
                    endpoint.error_rate > 0.05 ? 'text-red-500' : 'text-green-500'
                  }`}>
                    {(endpoint.error_rate * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Active Alerts */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Alerts</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {alerts.length > 0 ? (
              alerts.map((alert, index) => (
                <div key={index} className={`p-2 rounded-lg border ${
                  alert.severity === 'critical' ? 'border-red-200 bg-red-50' :
                  alert.severity === 'high' ? 'border-orange-200 bg-orange-50' :
                  alert.severity === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                  'border-blue-200 bg-blue-50'
                }`}>
                  <div className="flex items-start gap-2">
                    {getAlertIcon(alert.severity)}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {alert.message}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                <p className="text-sm">No active alerts</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrafficMonitor;