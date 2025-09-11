import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import EnvironmentManager from './EnvironmentManager';
import CollectionsManager from './CollectionsManager';
import GraphQLBuilder from './GraphQLBuilder';
import MultiProtocolTester from './MultiProtocolTester';
import {
  Send,
  Plus,
  Minus,
  Copy,
  Check,
  AlertCircle,
  Clock,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Save,
  History,
  Code2,
  FileText,
  Key,
  Globe,
  Server,
  Zap,
  Folder,
  Settings,
  Wifi
} from 'lucide-react';

const APIRequestBuilder = () => {
  const { token } = useAuth();
  
  // Request state
  const [method, setMethod] = useState('GET');
  const [url, setUrl] = useState('');
  const [isGraphQL, setIsGraphQL] = useState(false);
  const [protocol, setProtocol] = useState('http'); // http, websocket, grpc, soap, sse
  const [headers, setHeaders] = useState([
    { key: 'Content-Type', value: 'application/json', enabled: true }
  ]);
  const [queryParams, setQueryParams] = useState([
    { key: '', value: '', enabled: true }
  ]);
  const [bodyType, setBodyType] = useState('json');
  const [bodyContent, setBodyContent] = useState('');
  const [authorization, setAuthorization] = useState({ type: 'none', value: '' });
  
  // Response state
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [responseTime, setResponseTime] = useState(null);
  const [activeTab, setActiveTab] = useState('params');
  const [responseTab, setResponseTab] = useState('body');
  const [error, setError] = useState(null);
  
  // History
  const [requestHistory, setRequestHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  // Saved requests
  const [savedRequests, setSavedRequests] = useState([]);
  const [requestName, setRequestName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  
  // Environment and Collections
  const [currentEnvironment, setCurrentEnvironment] = useState(null);
  const [showCollections, setShowCollections] = useState(false);
  const [currentRequestData, setCurrentRequestData] = useState(null);

  const methods = [
    { value: 'GET', color: 'text-green-500' },
    { value: 'POST', color: 'text-yellow-500' },
    { value: 'PUT', color: 'text-blue-500' },
    { value: 'PATCH', color: 'text-purple-500' },
    { value: 'DELETE', color: 'text-red-500' },
    { value: 'HEAD', color: 'text-gray-500' },
    { value: 'OPTIONS', color: 'text-pink-500' },
    { value: 'GRAPHQL', color: 'text-indigo-500', label: 'GraphQL' },
    { value: 'MULTI', color: 'text-cyan-500', label: 'Multi-Protocol' }
  ];

  const authTypes = [
    { value: 'none', label: 'No Auth' },
    { value: 'bearer', label: 'Bearer Token' },
    { value: 'basic', label: 'Basic Auth' },
    { value: 'api-key', label: 'API Key' }
  ];

  useEffect(() => {
    // Load saved requests from localStorage
    const saved = localStorage.getItem('savedApiRequests');
    if (saved) {
      setSavedRequests(JSON.parse(saved));
    }
    
    // Load history
    const history = localStorage.getItem('requestHistory');
    if (history) {
      setRequestHistory(JSON.parse(history));
    }
  }, []);

  // Replace variables in a string with environment values
  const replaceVariables = (str) => {
    if (!str || !currentEnvironment) return str;
    
    let result = str;
    Object.entries(currentEnvironment.variables).forEach(([key, value]) => {
      const regex = new RegExp(`{{${key}}}`, 'g');
      result = result.replace(regex, value);
    });
    return result;
  };

  const handleSendRequest = async () => {
    // Replace variables in URL
    const processedUrl = replaceVariables(url);
    
    if (!processedUrl) {
      setError('Please enter a URL');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);
    const startTime = Date.now();

    try {
      // Build headers object with variable substitution
      const headersObj = {};
      headers.forEach(h => {
        if (h.enabled && h.key) {
          headersObj[replaceVariables(h.key)] = replaceVariables(h.value);
        }
      });

      // Add authorization header with variable substitution
      if (authorization.type === 'bearer' && authorization.value) {
        headersObj['Authorization'] = `Bearer ${replaceVariables(authorization.value)}`;
      } else if (authorization.type === 'api-key' && authorization.value) {
        headersObj['X-API-Key'] = replaceVariables(authorization.value);
      }

      // Build query params with variable substitution
      const params = {};
      queryParams.forEach(p => {
        if (p.enabled && p.key) {
          params[replaceVariables(p.key)] = replaceVariables(p.value);
        }
      });

      // Parse body if needed with variable substitution
      let data = null;
      if (['POST', 'PUT', 'PATCH'].includes(method)) {
        const processedBody = replaceVariables(bodyContent);
        if (bodyType === 'json' && processedBody) {
          try {
            data = JSON.parse(processedBody);
          } catch (e) {
            setError('Invalid JSON in request body');
            setLoading(false);
            return;
          }
        } else if (bodyType === 'raw') {
          data = processedBody;
        }
      }

      // Make request through backend proxy to avoid CORS
      const requestData = {
        method,
        url: processedUrl,
        headers: headersObj,
        params,
        data,
        environment_id: currentEnvironment?.id || null,
        collection_id: currentRequestData?.collectionId || null,
        project_id: null  // Can be added if we have project context
      };

      const proxyResponse = await axios.post(
        getApiUrl('/api/proxy-request'),
        requestData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      const endTime = Date.now();
      setResponseTime(endTime - startTime);
      setResponse(proxyResponse.data);

      // Add to history
      const historyEntry = {
        id: Date.now(),
        method,
        url,
        timestamp: new Date().toISOString(),
        status: proxyResponse.data.status,
        responseTime: endTime - startTime
      };
      
      const newHistory = [historyEntry, ...requestHistory.slice(0, 49)];
      setRequestHistory(newHistory);
      localStorage.setItem('requestHistory', JSON.stringify(newHistory));

    } catch (err) {
      const endTime = Date.now();
      setResponseTime(endTime - startTime);
      
      if (err.response) {
        setResponse({
          status: err.response.status,
          statusText: err.response.statusText,
          headers: err.response.headers,
          data: err.response.data
        });
      } else {
        setError(err.message || 'Request failed');
      }
    }

    setLoading(false);
  };

  const handleSaveRequest = () => {
    if (!requestName) {
      alert('Please enter a name for the request');
      return;
    }

    const requestData = {
      id: Date.now(),
      name: requestName,
      method,
      url,
      headers,
      queryParams,
      bodyType,
      bodyContent,
      authorization,
      createdAt: new Date().toISOString()
    };

    const newSaved = [...savedRequests, requestData];
    setSavedRequests(newSaved);
    localStorage.setItem('savedApiRequests', JSON.stringify(newSaved));
    
    setShowSaveDialog(false);
    setRequestName('');
  };

  const loadSavedRequest = (request) => {
    setMethod(request.method);
    setUrl(request.url);
    setHeaders(request.headers);
    setQueryParams(request.queryParams);
    setBodyType(request.bodyType);
    setBodyContent(request.bodyContent);
    setAuthorization(request.authorization);
  };

  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '', enabled: true }]);
  };

  const removeHeader = (index) => {
    setHeaders(headers.filter((_, i) => i !== index));
  };

  const updateHeader = (index, field, value) => {
    const newHeaders = [...headers];
    newHeaders[index][field] = value;
    setHeaders(newHeaders);
  };

  const addQueryParam = () => {
    setQueryParams([...queryParams, { key: '', value: '', enabled: true }]);
  };

  const removeQueryParam = (index) => {
    setQueryParams(queryParams.filter((_, i) => i !== index));
  };

  const updateQueryParam = (index, field, value) => {
    const newParams = [...queryParams];
    newParams[index][field] = value;
    setQueryParams(newParams);
  };

  const formatJson = () => {
    try {
      const formatted = JSON.stringify(JSON.parse(bodyContent), null, 2);
      setBodyContent(formatted);
    } catch (e) {
      // Invalid JSON, ignore
    }
  };

  const getStatusColor = (status) => {
    if (status >= 200 && status < 300) return 'text-green-500';
    if (status >= 300 && status < 400) return 'text-yellow-500';
    if (status >= 400 && status < 500) return 'text-orange-500';
    if (status >= 500) return 'text-red-500';
    return 'text-gray-500';
  };

  // Handle loading request from collections
  const loadRequestFromCollection = (request) => {
    setMethod(request.method || 'GET');
    setUrl(request.url || '');
    setHeaders(request.headers || [{ key: 'Content-Type', value: 'application/json', enabled: true }]);
    setQueryParams(request.queryParams || [{ key: '', value: '', enabled: true }]);
    setBodyType(request.bodyType || 'json');
    setBodyContent(request.bodyContent || '');
    setAuthorization(request.authorization || { type: 'none', value: '' });
    setCurrentRequestData(request);
  };

  // Prepare current request for saving
  const getCurrentRequestForSaving = () => {
    return {
      name: requestName || `${method} Request`,
      method,
      url,
      headers,
      queryParams,
      bodyType,
      bodyContent,
      authorization
    };
  };

  return (
    <div className="flex gap-6">
      {/* Left Sidebar - Collections */}
      {showCollections && (
        <div className="w-80 bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 h-[calc(100vh-200px)]">
          <CollectionsManager
            onRequestSelect={loadRequestFromCollection}
            onRequestSave={(saved) => {
              setCurrentRequestData(saved);
              setShowSaveDialog(false);
            }}
            currentRequest={getCurrentRequestForSaving()}
          />
        </div>
      )}
      
      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Environment Manager */}
        <EnvironmentManager 
          onEnvironmentChange={setCurrentEnvironment}
          currentEnvironment={currentEnvironment}
        />
        
        {/* Request Builder */}
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white flex items-center gap-2">
              <Zap className="w-6 h-6 text-purple-500" />
              API Request Builder
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowCollections(!showCollections)}
                className={`px-3 py-1 rounded-lg transition flex items-center gap-2 ${
                  showCollections 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <Folder className="w-4 h-4" />
                Collections
              </button>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="px-3 py-1 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition flex items-center gap-2"
              >
                <History className="w-4 h-4" />
                History
              </button>
              <button
                onClick={() => setShowSaveDialog(true)}
                className="px-3 py-1 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save
              </button>
            </div>
          </div>

        {/* URL Bar */}
        <div className="flex gap-2 mb-4">
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
          >
            {methods.map(m => (
              <option key={m.value} value={m.value}>{m.label || m.value}</option>
            ))}
          </select>
          
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter request URL (e.g., https://api.example.com/users)"
            className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
          />
          
          <button
            onClick={handleSendRequest}
            disabled={loading || !url || method === 'GRAPHQL' || method === 'MULTI'}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition flex items-center gap-2"
            title={method === 'GRAPHQL' ? 'Use the GraphQL Execute button below' : method === 'MULTI' ? 'Use the Multi-Protocol interface below' : ''}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Sending...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Send</span>
              </>
            )}
          </button>
        </div>

        {/* Show GraphQL Builder if GraphQL is selected */}
        {method === 'GRAPHQL' ? (
          <GraphQLBuilder
            endpoint={url}
            headers={headers}
            onResponse={setResponse}
            currentEnvironment={currentEnvironment}
            replaceVariables={replaceVariables}
          />
        ) : method === 'MULTI' ? (
          <MultiProtocolTester 
            projectId={currentRequestData?.project_id}
          />
        ) : (
          <>
            {/* Request Configuration Tabs */}
            <div className="border-b border-gray-700 mb-4">
              <div className="flex gap-4">
                {['params', 'authorization', 'headers', 'body'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 capitalize transition ${
                  activeTab === tab
                    ? 'text-purple-400 border-b-2 border-purple-400'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="min-h-[200px]">
          {/* Query Params Tab */}
          {activeTab === 'params' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Query Parameters</span>
                <button
                  onClick={addQueryParam}
                  className="text-purple-400 hover:text-purple-300 flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" />
                  Add Param
                </button>
              </div>
              {queryParams.map((param, index) => (
                <div key={index} className="flex gap-2 items-center">
                  <input
                    type="checkbox"
                    checked={param.enabled}
                    onChange={(e) => updateQueryParam(index, 'enabled', e.target.checked)}
                    className="text-purple-600"
                  />
                  <input
                    type="text"
                    value={param.key}
                    onChange={(e) => updateQueryParam(index, 'key', e.target.value)}
                    placeholder="Key"
                    className="flex-1 px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                  <input
                    type="text"
                    value={param.value}
                    onChange={(e) => updateQueryParam(index, 'value', e.target.value)}
                    placeholder="Value"
                    className="flex-1 px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                  <button
                    onClick={() => removeQueryParam(index)}
                    className="text-red-400 hover:text-red-300"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Authorization Tab */}
          {activeTab === 'authorization' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Type</label>
                <select
                  value={authorization.type}
                  onChange={(e) => setAuthorization({ ...authorization, type: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                >
                  {authTypes.map(auth => (
                    <option key={auth.value} value={auth.value}>{auth.label}</option>
                  ))}
                </select>
              </div>
              
              {authorization.type === 'bearer' && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Token</label>
                  <input
                    type="text"
                    value={authorization.value}
                    onChange={(e) => setAuthorization({ ...authorization, value: e.target.value })}
                    placeholder="Enter bearer token"
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                </div>
              )}
              
              {authorization.type === 'api-key' && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">API Key</label>
                  <input
                    type="text"
                    value={authorization.value}
                    onChange={(e) => setAuthorization({ ...authorization, value: e.target.value })}
                    placeholder="Enter API key"
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                </div>
              )}
            </div>
          )}

          {/* Headers Tab */}
          {activeTab === 'headers' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Headers</span>
                <button
                  onClick={addHeader}
                  className="text-purple-400 hover:text-purple-300 flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" />
                  Add Header
                </button>
              </div>
              {headers.map((header, index) => (
                <div key={index} className="flex gap-2 items-center">
                  <input
                    type="checkbox"
                    checked={header.enabled}
                    onChange={(e) => updateHeader(index, 'enabled', e.target.checked)}
                    className="text-purple-600"
                  />
                  <input
                    type="text"
                    value={header.key}
                    onChange={(e) => updateHeader(index, 'key', e.target.value)}
                    placeholder="Header name"
                    className="flex-1 px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                  <input
                    type="text"
                    value={header.value}
                    onChange={(e) => updateHeader(index, 'value', e.target.value)}
                    placeholder="Value"
                    className="flex-1 px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                  <button
                    onClick={() => removeHeader(index)}
                    className="text-red-400 hover:text-red-300"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

            {/* Body Tab */}
            {activeTab === 'body' && ['POST', 'PUT', 'PATCH'].includes(method) && (
            <div className="space-y-4">
              <div className="flex gap-4 mb-2">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    value="json"
                    checked={bodyType === 'json'}
                    onChange={(e) => setBodyType(e.target.value)}
                    className="text-purple-600"
                  />
                  <span className="text-gray-300">JSON</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    value="raw"
                    checked={bodyType === 'raw'}
                    onChange={(e) => setBodyType(e.target.value)}
                    className="text-purple-600"
                  />
                  <span className="text-gray-300">Raw</span>
                </label>
                <button
                  onClick={formatJson}
                  className="ml-auto text-purple-400 hover:text-purple-300 text-sm"
                >
                  Format JSON
                </button>
              </div>
              <textarea
                value={bodyContent}
                onChange={(e) => setBodyContent(e.target.value)}
                placeholder={bodyType === 'json' ? '{\n  "key": "value"\n}' : 'Enter raw body content'}
                className="w-full h-40 px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none font-mono text-sm"
              />
              </div>
            )}
          </div>
          </>
        )}
      </div>

      {/* Response - Show for standard HTTP methods */}
      {method !== 'GRAPHQL' && method !== 'MULTI' && (response || error) && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold text-white">Response</h3>
            {response && (
              <div className="flex items-center gap-4 text-sm">
                <span className={`flex items-center gap-1 ${getStatusColor(response.status)}`}>
                  {response.status >= 200 && response.status < 300 ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    <XCircle className="w-4 h-4" />
                  )}
                  {response.status} {response.statusText}
                </span>
                {responseTime && (
                  <span className="text-gray-400 flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {responseTime}ms
                  </span>
                )}
              </div>
            )}
          </div>

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
                <div>
                  <p className="text-red-400 font-medium">Request Failed</p>
                  <p className="text-gray-400 text-sm mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {response && (
            <>
              <div className="border-b border-gray-700 mb-4">
                <div className="flex gap-4">
                  {['body', 'headers', 'cookies'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setResponseTab(tab)}
                      className={`px-4 py-2 capitalize transition ${
                        responseTab === tab
                          ? 'text-purple-400 border-b-2 border-purple-400'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              <div className="min-h-[200px] max-h-[400px] overflow-auto">
                {responseTab === 'body' && (
                  <pre className="text-gray-300 text-sm font-mono whitespace-pre-wrap">
                    {typeof response.data === 'object' 
                      ? JSON.stringify(response.data, null, 2)
                      : response.data}
                  </pre>
                )}
                
                {responseTab === 'headers' && (
                  <div className="space-y-1">
                    {response.headers && Object.entries(response.headers).map(([key, value]) => (
                      <div key={key} className="flex gap-2 text-sm">
                        <span className="text-purple-400 font-medium">{key}:</span>
                        <span className="text-gray-300">{value}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                {responseTab === 'cookies' && (
                  <div className="text-gray-400 text-sm">
                    {response.cookies ? (
                      <pre className="font-mono">{JSON.stringify(response.cookies, null, 2)}</pre>
                    ) : (
                      'No cookies in response'
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-xl font-semibold text-white mb-4">Save Request</h3>
            <input
              type="text"
              value={requestName}
              onChange={(e) => setRequestName(e.target.value)}
              placeholder="Enter request name"
              className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none mb-4"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSaveRequest}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                Save
              </button>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* History Panel */}
      {showHistory && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Request History</h3>
          <div className="space-y-2">
            {requestHistory.length === 0 ? (
              <p className="text-gray-400 text-sm">No requests yet</p>
            ) : (
              requestHistory.map(item => (
                <div
                  key={item.id}
                  onClick={() => setUrl(item.url)}
                  className="flex items-center justify-between p-2 bg-gray-700/50 rounded-lg hover:bg-gray-700 cursor-pointer transition"
                >
                  <div className="flex items-center gap-3">
                    <span className={`font-medium ${methods.find(m => m.value === item.method)?.color}`}>
                      {item.method}
                    </span>
                    <span className="text-gray-300 text-sm truncate max-w-md">{item.url}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm ${getStatusColor(item.status)}`}>
                      {item.status}
                    </span>
                    <span className="text-gray-500 text-xs">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Saved Requests */}
      {savedRequests.length > 0 && (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Saved Requests</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {savedRequests.map(request => (
              <button
                key={request.id}
                onClick={() => loadSavedRequest(request)}
                className="p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition text-left"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-medium ${methods.find(m => m.value === request.method)?.color}`}>
                    {request.method}
                  </span>
                  <span className="text-white text-sm font-medium truncate">{request.name}</span>
                </div>
                <p className="text-gray-400 text-xs truncate">{request.url}</p>
              </button>
            ))}
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default APIRequestBuilder;