import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import ResponseViewer from './ResponseViewer';
import {
  Wifi,
  Server,
  Code2,
  Radio,
  Send,
  Loader,
  AlertCircle,
  CheckCircle,
  Copy,
  Save,
  Clock,
  Settings,
  Play,
  Pause,
  Plus,
  Minus,
  Globe
} from 'lucide-react';

const MultiProtocolTester = ({ projectId = null }) => {
  const { token } = useAuth();
  const [activeProtocol, setActiveProtocol] = useState('websocket');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  // WebSocket state
  const [wsConfig, setWsConfig] = useState({
    url: 'wss://echo.websocket.org',
    messages: [
      { message: 'Hello WebSocket', wait_for_response: true, timeout: 5 }
    ],
    headers: {},
    timeout: 30
  });

  // SOAP state
  const [soapConfig, setSoapConfig] = useState({
    url: '',
    soap_action: '',
    method_name: '',
    parameters: {},
    namespace: 'http://tempuri.org/',
    use_soap_12: false
  });

  // gRPC state
  const [grpcConfig, setGrpcConfig] = useState({
    url: '',
    service: '',
    method: '',
    request_data: {},
    metadata: {}
  });

  // SSE state
  const [sseConfig, setSseConfig] = useState({
    url: '',
    headers: {},
    max_events: 10,
    timeout: 30
  });

  const protocols = [
    { id: 'websocket', name: 'WebSocket', icon: Wifi, color: 'blue' },
    { id: 'grpc', name: 'gRPC', icon: Server, color: 'green' },
    { id: 'soap', name: 'SOAP/XML', icon: Code2, color: 'yellow' },
    { id: 'sse', name: 'SSE', icon: Radio, color: 'purple' }
  ];

  const testProtocol = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      let endpoint = '';
      let payload = {};

      switch (activeProtocol) {
        case 'websocket':
          endpoint = '/api/multi-protocol/websocket/test';
          payload = { ...wsConfig, project_id: projectId, save_result: !!projectId };
          break;
        case 'soap':
          endpoint = '/api/multi-protocol/soap/test';
          payload = { ...soapConfig, project_id: projectId, save_result: !!projectId };
          break;
        case 'grpc':
          endpoint = '/api/multi-protocol/grpc/test';
          payload = { ...grpcConfig, project_id: projectId, save_result: !!projectId };
          break;
        case 'sse':
          endpoint = '/api/multi-protocol/sse/test';
          payload = { ...sseConfig, project_id: projectId, save_result: !!projectId };
          break;
      }

      const result = await axios.post(getApiUrl(endpoint), payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setResponse(result.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const addWebSocketMessage = () => {
    setWsConfig(prev => ({
      ...prev,
      messages: [...prev.messages, { message: '', wait_for_response: true, timeout: 5 }]
    }));
  };

  const updateWebSocketMessage = (index, field, value) => {
    setWsConfig(prev => ({
      ...prev,
      messages: prev.messages.map((msg, i) => 
        i === index ? { ...msg, [field]: value } : msg
      )
    }));
  };

  const removeWebSocketMessage = (index) => {
    setWsConfig(prev => ({
      ...prev,
      messages: prev.messages.filter((_, i) => i !== index)
    }));
  };

  return (
    <div className="space-y-6">
      {/* Protocol Selector */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex space-x-2">
          {protocols.map(protocol => {
            const Icon = protocol.icon;
            return (
              <button
                key={protocol.id}
                onClick={() => setActiveProtocol(protocol.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                  activeProtocol === protocol.id
                    ? `bg-${protocol.color}-600/20 text-${protocol.color}-400 border border-${protocol.color}-500/50`
                    : 'bg-gray-700 text-gray-400 border border-gray-600 hover:bg-gray-600'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{protocol.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* WebSocket Configuration */}
      {activeProtocol === 'websocket' && (
        <div className="bg-gray-800 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Wifi className="w-5 h-5 mr-2 text-blue-400" />
            WebSocket Configuration
          </h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              WebSocket URL
            </label>
            <input
              type="text"
              value={wsConfig.url}
              onChange={(e) => setWsConfig(prev => ({ ...prev, url: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder="wss://example.com/socket"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-400">Messages</label>
              <button
                onClick={addWebSocketMessage}
                className="text-blue-400 hover:text-blue-300"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            
            {wsConfig.messages.map((msg, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={typeof msg.message === 'object' ? JSON.stringify(msg.message) : msg.message}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      updateWebSocketMessage(index, 'message', parsed);
                    } catch {
                      updateWebSocketMessage(index, 'message', e.target.value);
                    }
                  }}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="Message content (string or JSON)"
                />
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={msg.wait_for_response}
                    onChange={(e) => updateWebSocketMessage(index, 'wait_for_response', e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-400">Wait</span>
                </label>
                <button
                  onClick={() => removeWebSocketMessage(index)}
                  className="text-red-400 hover:text-red-300"
                >
                  <Minus className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* gRPC Configuration */}
      {activeProtocol === 'grpc' && (
        <div className="bg-gray-800 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Server className="w-5 h-5 mr-2 text-green-400" />
            gRPC Configuration
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Server URL
              </label>
              <input
                type="text"
                value={grpcConfig.url}
                onChange={(e) => setGrpcConfig(prev => ({ ...prev, url: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="https://grpc.example.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Service
              </label>
              <input
                type="text"
                value={grpcConfig.service}
                onChange={(e) => setGrpcConfig(prev => ({ ...prev, service: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="UserService"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Method
              </label>
              <input
                type="text"
                value={grpcConfig.method}
                onChange={(e) => setGrpcConfig(prev => ({ ...prev, method: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="GetUser"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Request Data (JSON)
              </label>
              <textarea
                value={JSON.stringify(grpcConfig.request_data, null, 2)}
                onChange={(e) => {
                  try {
                    setGrpcConfig(prev => ({ ...prev, request_data: JSON.parse(e.target.value) }));
                  } catch {}
                }}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="3"
              />
            </div>
          </div>
        </div>
      )}

      {/* SOAP Configuration */}
      {activeProtocol === 'soap' && (
        <div className="bg-gray-800 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Code2 className="w-5 h-5 mr-2 text-yellow-400" />
            SOAP/XML Configuration
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                WSDL URL
              </label>
              <input
                type="text"
                value={soapConfig.url}
                onChange={(e) => setSoapConfig(prev => ({ ...prev, url: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="https://example.com/soap/service"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                SOAP Action
              </label>
              <input
                type="text"
                value={soapConfig.soap_action}
                onChange={(e) => setSoapConfig(prev => ({ ...prev, soap_action: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="GetWeather"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Method Name
              </label>
              <input
                type="text"
                value={soapConfig.method_name}
                onChange={(e) => setSoapConfig(prev => ({ ...prev, method_name: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="GetWeatherByCity"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Parameters (JSON)
              </label>
              <textarea
                value={JSON.stringify(soapConfig.parameters, null, 2)}
                onChange={(e) => {
                  try {
                    setSoapConfig(prev => ({ ...prev, parameters: JSON.parse(e.target.value) }));
                  } catch {}
                }}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                rows="3"
                placeholder='{"city": "London", "country": "UK"}'
              />
            </div>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={soapConfig.use_soap_12}
              onChange={(e) => setSoapConfig(prev => ({ ...prev, use_soap_12: e.target.checked }))}
              className="mr-2"
            />
            <label className="text-sm text-gray-400">Use SOAP 1.2</label>
          </div>
        </div>
      )}

      {/* SSE Configuration */}
      {activeProtocol === 'sse' && (
        <div className="bg-gray-800 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Radio className="w-5 h-5 mr-2 text-purple-400" />
            Server-Sent Events Configuration
          </h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              SSE Endpoint URL
            </label>
            <input
              type="text"
              value={sseConfig.url}
              onChange={(e) => setSseConfig(prev => ({ ...prev, url: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder="https://example.com/events"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Max Events
              </label>
              <input
                type="number"
                value={sseConfig.max_events}
                onChange={(e) => setSseConfig(prev => ({ ...prev, max_events: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={sseConfig.timeout}
                onChange={(e) => setSseConfig(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
          </div>
        </div>
      )}

      {/* Test Button */}
      <div className="flex justify-between items-center">
        <button
          onClick={testProtocol}
          disabled={loading}
          className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50 flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              <span>Testing...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Test {protocols.find(p => p.id === activeProtocol)?.name}</span>
            </>
          )}
        </button>
        
        {projectId && (
          <button className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition flex items-center space-x-2">
            <Save className="w-4 h-4" />
            <span>Save Test</span>
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
            <div>
              <p className="text-red-400 font-medium">Test Failed</p>
              <p className="text-gray-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Response Display */}
      {response && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center">
              {response.success ? (
                <>
                  <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                  Test Successful
                </>
              ) : (
                <>
                  <AlertCircle className="w-5 h-5 mr-2 text-yellow-400" />
                  Test Completed with Issues
                </>
              )}
            </h3>
            
            {response.result?.duration_ms && (
              <span className="text-sm text-gray-400 flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {response.result.duration_ms}ms
              </span>
            )}
          </div>
          
          <ResponseViewer response={response.result} />
        </div>
      )}
    </div>
  );
};

export default MultiProtocolTester;