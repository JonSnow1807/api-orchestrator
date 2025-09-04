import React, { useState, useEffect } from 'react';
import { Server, Play, Pause, RefreshCw, Copy, ExternalLink, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const MockServerManager = ({ taskId }) => {
  const [mockConfig, setMockConfig] = useState(null);
  const [serverStatus, setServerStatus] = useState('stopped'); // stopped, starting, running, error
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (taskId) {
      fetchMockServerConfig();
    }
  }, [taskId]);

  const fetchMockServerConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/mock-server/${taskId}`);
      setMockConfig(response.data);
      setError(null);
      // Check if server is already running
      if (response.data?.status === 'running') {
        setServerStatus('running');
      }
    } catch (err) {
      console.error('Failed to fetch mock server config:', err);
      setError('Failed to load mock server configuration');
    } finally {
      setLoading(false);
    }
  };

  const toggleServer = async () => {
    if (serverStatus === 'running') {
      await stopServer();
    } else {
      await startServer();
    }
  };

  const startServer = async () => {
    try {
      setServerStatus('starting');
      const response = await axios.post(`/api/mock-server/${taskId}/start`);
      if (response.data.success) {
        setServerStatus('running');
        setMockConfig(prev => ({ ...prev, ...response.data.config }));
      }
    } catch (err) {
      console.error('Failed to start mock server:', err);
      setServerStatus('error');
      setError('Failed to start mock server');
    }
  };

  const stopServer = async () => {
    try {
      const response = await axios.post(`/api/mock-server/${taskId}/stop`);
      if (response.data.success) {
        setServerStatus('stopped');
      }
    } catch (err) {
      console.error('Failed to stop mock server:', err);
      setError('Failed to stop mock server');
    }
  };

  const copyUrl = (url) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (error && !mockConfig) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
        {error}
      </div>
    );
  }

  if (!mockConfig) {
    return (
      <div className="text-center p-8 text-gray-500">
        No mock server configuration available. Run orchestration to generate mock servers.
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (serverStatus) {
      case 'running':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'stopped':
        return <XCircle className="w-5 h-5 text-gray-400" />;
      case 'starting':
        return <RefreshCw className="w-5 h-5 text-yellow-400 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (serverStatus) {
      case 'running':
        return 'Running';
      case 'stopped':
        return 'Stopped';
      case 'starting':
        return 'Starting...';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="space-y-6">
      {/* Server Status Card */}
      <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg p-6 border border-purple-500/20">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <Server className="w-6 h-6 text-purple-400 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Mock Server Status</h3>
              <div className="flex items-center gap-2 mb-4">
                {getStatusIcon()}
                <span className={`font-medium ${
                  serverStatus === 'running' ? 'text-green-400' : 
                  serverStatus === 'error' ? 'text-red-400' : 
                  'text-gray-400'
                }`}>
                  {getStatusText()}
                </span>
              </div>
              
              {mockConfig.base_url && serverStatus === 'running' && (
                <div className="bg-gray-900/50 rounded-lg p-3 mb-4">
                  <p className="text-xs text-gray-400 mb-1">Base URL:</p>
                  <div className="flex items-center gap-2">
                    <code className="text-green-400 text-sm font-mono">{mockConfig.base_url}</code>
                    <button
                      onClick={() => copyUrl(mockConfig.base_url)}
                      className="p-1 hover:bg-gray-800 rounded transition-colors"
                    >
                      <Copy className="w-4 h-4 text-gray-400" />
                    </button>
                    {copied && (
                      <span className="text-xs text-green-400">Copied!</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <button
            onClick={toggleServer}
            disabled={serverStatus === 'starting'}
            className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
              serverStatus === 'running' 
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30 border border-green-500/30'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {serverStatus === 'running' ? (
              <>
                <Pause className="w-4 h-4" />
                Stop Server
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Start Server
              </>
            )}
          </button>
        </div>
      </div>

      {/* Endpoints */}
      {mockConfig.endpoints && mockConfig.endpoints.length > 0 && (
        <div className="bg-gray-800/50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <ExternalLink className="w-5 h-5 text-blue-400" />
            Available Endpoints
          </h3>
          <div className="space-y-3">
            {mockConfig.endpoints.map((endpoint, index) => (
              <div key={index} className="bg-gray-900/50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        endpoint.method === 'GET' ? 'bg-blue-500/30 text-blue-300' :
                        endpoint.method === 'POST' ? 'bg-green-500/30 text-green-300' :
                        endpoint.method === 'PUT' ? 'bg-yellow-500/30 text-yellow-300' :
                        endpoint.method === 'DELETE' ? 'bg-red-500/30 text-red-300' :
                        'bg-gray-500/30 text-gray-300'
                      }`}>
                        {endpoint.method || 'GET'}
                      </span>
                      <code className="text-white font-mono text-sm">{endpoint.path || '/'}</code>
                    </div>
                    {endpoint.description && (
                      <p className="text-gray-400 text-sm mb-2">{endpoint.description}</p>
                    )}
                    {endpoint.response_example && (
                      <details className="mt-2">
                        <summary className="text-xs text-purple-400 cursor-pointer hover:text-purple-300">
                          View Response Example
                        </summary>
                        <pre className="mt-2 p-2 bg-gray-950 rounded text-xs text-gray-300 overflow-x-auto">
                          {JSON.stringify(endpoint.response_example, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                  {serverStatus === 'running' && mockConfig.base_url && (
                    <button
                      onClick={() => window.open(`${mockConfig.base_url}${endpoint.path}`, '_blank')}
                      className="p-2 hover:bg-gray-800 rounded transition-colors"
                      title="Open in browser"
                    >
                      <ExternalLink className="w-4 h-4 text-gray-400" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Configuration Details */}
      {mockConfig.config && (
        <div className="bg-gray-800/50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Server Configuration</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {mockConfig.config.port && (
              <div className="bg-gray-900/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Port</p>
                <p className="text-white font-medium">{mockConfig.config.port}</p>
              </div>
            )}
            {mockConfig.config.host && (
              <div className="bg-gray-900/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Host</p>
                <p className="text-white font-medium">{mockConfig.config.host}</p>
              </div>
            )}
            {mockConfig.config?.delay !== undefined && (
              <div className="bg-gray-900/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Response Delay</p>
                <p className="text-white font-medium">{mockConfig.config.delay}ms</p>
              </div>
            )}
            {mockConfig.config.cors && (
              <div className="bg-gray-900/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">CORS</p>
                <p className="text-white font-medium">
                  {mockConfig.config.cors ? 'Enabled' : 'Disabled'}
                </p>
              </div>
            )}
            {mockConfig.config.auth && (
              <div className="bg-gray-900/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Authentication</p>
                <p className="text-white font-medium">
                  {mockConfig.config.auth ? 'Required' : 'None'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MockServerManager;