import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Globe,
  Shield,
  Server,
  Key,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader,
  Settings,
  Wifi,
  WifiOff,
  Lock,
  Unlock,
  List,
  Plus,
  Trash2,
  TestTube,
  Save,
  RefreshCw,
  Monitor,
  Cloud,
  Building2
} from 'lucide-react';

const ProxySettings = ({ workspaceId = null, environmentId = null }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [activeTab, setActiveTab] = useState('global');
  const [presets, setPresets] = useState([]);
  const [systemProxy, setSystemProxy] = useState(null);
  
  // Proxy configuration state
  const [proxyConfig, setProxyConfig] = useState({
    enabled: false,
    type: 'http',
    host: '',
    port: 8080,
    username: '',
    password: '',
    bypass_list: [],
    use_system_proxy: false,
    tunnel_https: true,
    verify_ssl: true,
    timeout: 30
  });
  
  const [bypassInput, setBypassInput] = useState('');

  useEffect(() => {
    loadProxySettings();
    loadPresets();
    detectSystemProxy();
  }, [activeTab]);

  const loadProxySettings = async () => {
    try {
      const response = await axios.get(
        getApiUrl('/api/proxy/settings'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        const settings = response.data.settings;
        
        // Load appropriate settings based on active tab
        if (activeTab === 'global' && settings.global_proxy) {
          setProxyConfig(settings.global_proxy);
        } else if (activeTab === 'workspace' && workspaceId) {
          const key = `workspace_${workspaceId}`;
          if (settings.workspace_proxies[key]) {
            setProxyConfig(settings.workspace_proxies[key]);
          }
        } else if (activeTab === 'environment' && environmentId) {
          const key = `env_${environmentId}`;
          if (settings.environment_proxies[key]) {
            setProxyConfig(settings.environment_proxies[key]);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load proxy settings:', error);
    }
  };

  const loadPresets = async () => {
    try {
      const response = await axios.get(
        getApiUrl('/api/proxy/presets'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        setPresets(response.data.presets);
      }
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const detectSystemProxy = async () => {
    try {
      const response = await axios.get(
        getApiUrl('/api/proxy/detect-system'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success && response.data.detected) {
        setSystemProxy(response.data.proxy);
      }
    } catch (error) {
      console.error('Failed to detect system proxy:', error);
    }
  };

  const saveProxyConfig = async () => {
    setLoading(true);
    try {
      let endpoint = '/api/proxy/global';
      if (activeTab === 'workspace' && workspaceId) {
        endpoint = `/api/proxy/workspace/${workspaceId}`;
      } else if (activeTab === 'environment' && environmentId) {
        endpoint = `/api/proxy/environment/${environmentId}`;
      }

      const response = await axios.post(
        getApiUrl(endpoint),
        proxyConfig,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        setTestResult({
          success: true,
          message: 'Proxy configuration saved successfully'
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || 'Failed to save proxy configuration'
      });
    } finally {
      setLoading(false);
    }
  };

  const testProxy = async () => {
    setTestLoading(true);
    setTestResult(null);
    
    try {
      const response = await axios.post(
        getApiUrl('/api/proxy/test'),
        {
          config: proxyConfig,
          test_url: 'http://httpbin.org/ip'
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setTestResult(response.data.result);
    } catch (error) {
      setTestResult({
        success: false,
        error: error.response?.data?.detail || 'Connection test failed'
      });
    } finally {
      setTestLoading(false);
    }
  };

  const applyPreset = (preset) => {
    setProxyConfig({
      ...proxyConfig,
      ...preset.config,
      bypass_list: preset.config.bypass_list || []
    });
  };

  const addBypassRule = () => {
    if (bypassInput.trim()) {
      setProxyConfig({
        ...proxyConfig,
        bypass_list: [...proxyConfig.bypass_list, bypassInput.trim()]
      });
      setBypassInput('');
    }
  };

  const removeBypassRule = (index) => {
    const newList = proxyConfig.bypass_list.filter((_, i) => i !== index);
    setProxyConfig({
      ...proxyConfig,
      bypass_list: newList
    });
  };

  const proxyTypes = [
    { value: 'http', label: 'HTTP', icon: Globe },
    { value: 'https', label: 'HTTPS', icon: Lock },
    { value: 'socks4', label: 'SOCKS4', icon: Server },
    { value: 'socks5', label: 'SOCKS5', icon: Shield },
    { value: 'system', label: 'System', icon: Monitor }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Globe className="w-8 h-8 text-blue-400" />
            <div>
              <h2 className="text-2xl font-bold text-white">Proxy Configuration</h2>
              <p className="text-gray-400">Configure HTTP, HTTPS, and SOCKS proxy settings</p>
            </div>
          </div>
          <button
            onClick={detectSystemProxy}
            className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Detect System</span>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 border-b border-gray-700">
          <button
            onClick={() => setActiveTab('global')}
            className={`pb-2 px-1 transition ${
              activeTab === 'global'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4" />
              <span>Global</span>
            </div>
          </button>
          {workspaceId && (
            <button
              onClick={() => setActiveTab('workspace')}
              className={`pb-2 px-1 transition ${
                activeTab === 'workspace'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Building2 className="w-4 h-4" />
                <span>Workspace</span>
              </div>
            </button>
          )}
          {environmentId && (
            <button
              onClick={() => setActiveTab('environment')}
              className={`pb-2 px-1 transition ${
                activeTab === 'environment'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Cloud className="w-4 h-4" />
                <span>Environment</span>
              </div>
            </button>
          )}
        </div>
      </div>

      {/* System Proxy Detection */}
      {systemProxy && (
        <div className="bg-blue-900/20 border border-blue-500/50 rounded-lg p-4">
          <div className="flex items-center space-x-2 text-blue-400">
            <Monitor className="w-5 h-5" />
            <span className="font-medium">System Proxy Detected</span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            {systemProxy.type.toUpperCase()} proxy at {systemProxy.host}:{systemProxy.port}
          </p>
          <button
            onClick={() => setProxyConfig(systemProxy)}
            className="mt-2 text-sm text-blue-400 hover:text-blue-300"
          >
            Use System Proxy →
          </button>
        </div>
      )}

      {/* Presets */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Quick Presets</h3>
        <div className="grid grid-cols-3 gap-3">
          {presets.slice(0, 6).map((preset, index) => (
            <button
              key={index}
              onClick={() => applyPreset(preset)}
              className="p-3 bg-gray-700 rounded-lg hover:bg-gray-600 transition text-left"
            >
              <p className="text-white font-medium">{preset.name}</p>
              <p className="text-gray-400 text-xs mt-1">{preset.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Configuration */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="space-y-4">
          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between">
            <label className="text-white font-medium">Enable Proxy</label>
            <button
              onClick={() => setProxyConfig(prev => ({ ...prev, enabled: !prev.enabled }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                proxyConfig.enabled ? 'bg-blue-500' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                  proxyConfig.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {proxyConfig.enabled && (
            <>
              {/* Proxy Type */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Proxy Type
                </label>
                <div className="flex space-x-2">
                  {proxyTypes.map(type => (
                    <button
                      key={type.value}
                      onClick={() => setProxyConfig(prev => ({ ...prev, type: type.value }))}
                      className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition ${
                        proxyConfig.type === type.value
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      <type.icon className="w-4 h-4" />
                      <span>{type.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Host and Port */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Proxy Host
                  </label>
                  <input
                    type="text"
                    value={proxyConfig.host}
                    onChange={(e) => setProxyConfig(prev => ({ ...prev, host: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    placeholder="e.g., proxy.company.com"
                    disabled={proxyConfig.use_system_proxy}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Port
                  </label>
                  <input
                    type="number"
                    value={proxyConfig.port}
                    onChange={(e) => setProxyConfig(prev => ({ ...prev, port: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    placeholder="8080"
                    disabled={proxyConfig.use_system_proxy}
                  />
                </div>
              </div>

              {/* Authentication */}
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Key className="w-4 h-4 text-gray-400" />
                  <label className="text-sm font-medium text-gray-400">
                    Proxy Authentication (Optional)
                  </label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="text"
                    value={proxyConfig.username}
                    onChange={(e) => setProxyConfig(prev => ({ ...prev, username: e.target.value }))}
                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    placeholder="Username"
                  />
                  <input
                    type="password"
                    value={proxyConfig.password}
                    onChange={(e) => setProxyConfig(prev => ({ ...prev, password: e.target.value }))}
                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    placeholder="Password"
                  />
                </div>
              </div>

              {/* Bypass List */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-400">
                    Bypass List (No proxy for these hosts)
                  </label>
                </div>
                <div className="space-y-2">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={bypassInput}
                      onChange={(e) => setBypassInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addBypassRule()}
                      className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                      placeholder="e.g., localhost, *.local, 192.168.*"
                    />
                    <button
                      onClick={addBypassRule}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                  {proxyConfig.bypass_list.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {proxyConfig.bypass_list.map((rule, index) => (
                        <div
                          key={index}
                          className="px-3 py-1 bg-gray-700 rounded-full flex items-center space-x-2"
                        >
                          <span className="text-sm text-gray-300">{rule}</span>
                          <button
                            onClick={() => removeBypassRule(index)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <XCircle className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Advanced Settings */}
              <div className="space-y-3 pt-4 border-t border-gray-700">
                <h4 className="text-sm font-medium text-gray-400">Advanced Settings</h4>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">HTTPS Tunneling</label>
                  <input
                    type="checkbox"
                    checked={proxyConfig.tunnel_https}
                    onChange={(e) => setProxyConfig(prev => ({ ...prev, tunnel_https: e.target.checked }))}
                    className="rounded"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Verify SSL Certificates</label>
                  <input
                    type="checkbox"
                    checked={proxyConfig.verify_ssl}
                    onChange={(e) => setProxyConfig(prev => ({ ...prev, verify_ssl: e.target.checked }))}
                    className="rounded"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Timeout (seconds)</label>
                  <input
                    type="number"
                    value={proxyConfig.timeout}
                    onChange={(e) => setProxyConfig(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                    className="w-20 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`rounded-lg p-4 ${
          testResult.success 
            ? 'bg-green-900/20 border border-green-500/50' 
            : 'bg-red-900/20 border border-red-500/50'
        }`}>
          <div className="flex items-center space-x-2">
            {testResult.success ? (
              <CheckCircle className="w-5 h-5 text-green-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
            <span className={testResult.success ? 'text-green-400' : 'text-red-400'}>
              {testResult.success ? 'Proxy connection successful' : 'Proxy connection failed'}
            </span>
          </div>
          {testResult.latency_ms && (
            <p className="text-sm text-gray-400 mt-1">
              Latency: {testResult.latency_ms.toFixed(0)}ms
            </p>
          )}
          {testResult.error && (
            <p className="text-sm text-red-400 mt-1">{testResult.error}</p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-4">
        <button
          onClick={testProxy}
          disabled={testLoading || !proxyConfig.enabled}
          className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition disabled:opacity-50 flex items-center space-x-2"
        >
          {testLoading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              <span>Testing...</span>
            </>
          ) : (
            <>
              <TestTube className="w-4 h-4" />
              <span>Test Connection</span>
            </>
          )}
        </button>
        
        <button
          onClick={saveProxyConfig}
          disabled={loading}
          className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition disabled:opacity-50 flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              <span>Saving...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save Configuration</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ProxySettings;