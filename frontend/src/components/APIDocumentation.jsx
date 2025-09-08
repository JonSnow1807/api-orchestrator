import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Book,
  Code,
  Send,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  ExternalLink,
  Shield,
  Clock,
  Server,
  Key,
  Hash,
  Type,
  ToggleLeft,
  FileJson,
  Play,
  X,
  Loader2
} from 'lucide-react';

const APIDocumentation = ({ projects = [], currentTaskId = null }) => {
  const { token } = useAuth();
  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedEndpoints, setExpandedEndpoints] = useState(new Set());
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [tryItOut, setTryItOut] = useState(false);
  const [testResponse, setTestResponse] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [copiedCode, setCopiedCode] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  
  // Try It Out form state
  const [testParams, setTestParams] = useState({});
  const [testHeaders, setTestHeaders] = useState({});
  const [testBody, setTestBody] = useState('');
  const [baseUrl, setBaseUrl] = useState('');

  useEffect(() => {
    // Try to load OpenAPI spec from the most recent project with a completed orchestration
    if (projects && projects.length > 0) {
      const projectWithTask = projects.find(p => p.last_task_id) || projects[0];
      if (projectWithTask && projectWithTask.last_task_id) {
        setSelectedProject(projectWithTask);
        setSelectedTaskId(projectWithTask.last_task_id);
        fetchOpenApiSpec(projectWithTask.last_task_id);
      } else {
        setLoading(false);
      }
    } else if (currentTaskId) {
      setSelectedTaskId(currentTaskId);
      fetchOpenApiSpec(currentTaskId);
    } else {
      setLoading(false);
    }
  }, [projects, currentTaskId]);

  const fetchOpenApiSpec = async (taskId) => {
    if (!taskId) {
      setLoading(false);
      return;
    }
    
    try {
      // First try to get the task status which includes the OpenAPI spec
      const response = await axios.get(
        getApiUrl(`/api/tasks/${taskId}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      if (response.data.openapi_spec) {
        setSpec(response.data.openapi_spec);
        setBaseUrl(response.data.openapi_spec.servers?.[0]?.url || 'http://localhost:8000');
      } else {
        // Fallback to export endpoint if spec not in task status
        const exportResponse = await axios.get(
          getApiUrl(`/api/export/${taskId}?format=json`),
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        setSpec(exportResponse.data);
        setBaseUrl(exportResponse.data.servers?.[0]?.url || 'http://localhost:8000');
      }
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch OpenAPI spec:', error);
      setLoading(false);
    }
  };

  const getMethodColor = (method) => {
    const colors = {
      get: 'bg-green-500',
      post: 'bg-yellow-500',
      put: 'bg-blue-500',
      patch: 'bg-purple-500',
      delete: 'bg-red-500',
      head: 'bg-gray-500',
      options: 'bg-pink-500'
    };
    return colors[method] || 'bg-gray-500';
  };

  const getMethodTextColor = (method) => {
    const colors = {
      get: 'text-green-500',
      post: 'text-yellow-500',
      put: 'text-blue-500',
      patch: 'text-purple-500',
      delete: 'text-red-500',
      head: 'text-gray-500',
      options: 'text-pink-500'
    };
    return colors[method] || 'text-gray-500';
  };

  const toggleEndpoint = (endpointId) => {
    const newExpanded = new Set(expandedEndpoints);
    if (newExpanded.has(endpointId)) {
      newExpanded.delete(endpointId);
    } else {
      newExpanded.add(endpointId);
    }
    setExpandedEndpoints(newExpanded);
  };

  const generateCodeExample = (endpoint, method, path) => {
    const examples = {
      curl: `curl -X ${method.toUpperCase()} "${baseUrl}${path}" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN"${
    ['post', 'put', 'patch'].includes(method) ? ` \\
  -d '{"key": "value"}'` : ''
  }`,
      
      python: `import requests

response = requests.${method}(
    "${baseUrl}${path}",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN"
    }${['post', 'put', 'patch'].includes(method) ? `,
    json={"key": "value"}` : ''}
)
print(response.json())`,
      
      javascript: `fetch("${baseUrl}${path}", {
  method: "${method.toUpperCase()}",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
  }${['post', 'put', 'patch'].includes(method) ? `,
  body: JSON.stringify({"key": "value"})` : ''}
})
.then(response => response.json())
.then(data => console.log(data));`
    };
    
    return examples;
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const executeTest = async () => {
    setTestLoading(true);
    setTestResponse(null);
    
    try {
      // Build the full URL with parameters
      let fullUrl = `${baseUrl}${selectedEndpoint.path}`;
      
      // Replace path parameters
      Object.entries(testParams).forEach(([key, value]) => {
        fullUrl = fullUrl.replace(`{${key}}`, value);
      });
      
      // Prepare headers
      const headers = {
        'Content-Type': 'application/json',
        ...testHeaders
      };
      
      // Make the request through the proxy
      const response = await axios.post(
        getApiUrl('/api/proxy-request'),
        {
          method: selectedEndpoint.method.toUpperCase(),
          url: fullUrl,
          headers,
          data: testBody ? JSON.parse(testBody) : null
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setTestResponse(response.data);
    } catch (error) {
      setTestResponse({
        error: true,
        message: error.response?.data?.detail || error.message
      });
    }
    
    setTestLoading(false);
  };

  const renderParameter = (param) => {
    const typeColors = {
      string: 'text-green-400',
      number: 'text-blue-400',
      integer: 'text-blue-400',
      boolean: 'text-purple-400',
      array: 'text-yellow-400',
      object: 'text-orange-400'
    };
    
    return (
      <div key={param.name} className="flex items-start gap-3 py-2 border-b border-gray-700 last:border-0">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-white font-mono text-sm">{param.name}</span>
            {param.required && (
              <span className="px-1.5 py-0.5 bg-red-500/20 text-red-400 text-xs rounded">Required</span>
            )}
            <span className={`text-xs ${typeColors[param.schema?.type] || 'text-gray-400'}`}>
              {param.schema?.type || 'any'}
            </span>
          </div>
          {param.description && (
            <p className="text-gray-400 text-sm mt-1">{param.description}</p>
          )}
        </div>
        {tryItOut && (
          <input
            type="text"
            placeholder={param.example || `Enter ${param.name}`}
            onChange={(e) => setTestParams({...testParams, [param.name]: e.target.value})}
            className="px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none text-sm"
          />
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  if (!spec) {
    return (
      <div className="space-y-6">
        {/* Project Selector if there are projects */}
        {projects && projects.length > 0 && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Select a Project</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.map(project => (
                <button
                  key={project.id}
                  onClick={() => {
                    if (project.last_task_id) {
                      setSelectedProject(project);
                      setSelectedTaskId(project.last_task_id);
                      fetchOpenApiSpec(project.last_task_id);
                    }
                  }}
                  className={`p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition text-left ${
                    selectedProject?.id === project.id ? 'ring-2 ring-purple-500' : ''
                  }`}
                >
                  <h4 className="font-medium text-white">{project.name}</h4>
                  <p className="text-sm text-gray-400 mt-1">{project.source_path}</p>
                  {project.last_task_id && (
                    <span className="inline-block mt-2 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
                      Has Documentation
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Empty State */}
        <div className="text-center py-20">
          <Book className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400">No API documentation available</p>
          <p className="text-gray-500 text-sm mt-2">
            {projects && projects.length > 0 
              ? "Select a project above or run orchestration to generate API docs"
              : "Run orchestration on a project to generate API docs"
            }
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full max-h-[calc(100vh-300px)] overflow-y-auto">
      <div className="space-y-6 p-2">
      {/* Header */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-4 mb-2">
              <h2 className="text-2xl font-bold text-white">
                {spec.info?.title || 'API Documentation'}
              </h2>
              {selectedProject && (
                <span className="px-3 py-1 bg-gray-700 text-gray-300 text-sm rounded">
                  {selectedProject.name}
                </span>
              )}
            </div>
            {spec.info?.description && (
              <p className="text-gray-400">{spec.info?.description}</p>
            )}
            <div className="flex items-center gap-4 mt-3">
              {spec.info?.version && (
                <span className="px-2 py-1 bg-purple-500/20 text-purple-400 text-sm rounded">
                  v{spec.info.version}
                </span>
              )}
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Server className="w-4 h-4" />
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="px-2 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                  placeholder="Base URL"
                />
              </div>
            </div>
          </div>
          <button
            onClick={() => setTryItOut(!tryItOut)}
            className={`px-4 py-2 rounded-lg transition flex items-center gap-2 ${
              tryItOut 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Play className="w-4 h-4" />
            {tryItOut ? 'Testing Mode' : 'Try It Out'}
          </button>
        </div>
      </div>

      {/* Endpoints */}
      <div className="space-y-4">
        {spec.paths && Object.entries(spec.paths).map(([path, pathItem]) => (
          <div key={path} className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 overflow-hidden">
            {Object.entries(pathItem).map(([method, endpoint]) => {
              const endpointId = `${method}-${path}`;
              const isExpanded = expandedEndpoints.has(endpointId);
              
              return (
                <div key={endpointId}>
                  {/* Endpoint Header */}
                  <button
                    onClick={() => {
                      toggleEndpoint(endpointId);
                      setSelectedEndpoint({ ...endpoint, method, path });
                    }}
                    className="w-full p-4 hover:bg-gray-700/30 transition flex items-center gap-3"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      {isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                      )}
                      <span className={`px-3 py-1 ${getMethodColor(method)} text-white text-xs font-bold rounded uppercase`}>
                        {method}
                      </span>
                      <span className="text-white font-mono">{path}</span>
                      {endpoint.summary && (
                        <span className="text-gray-400 text-sm">{endpoint.summary}</span>
                      )}
                    </div>
                    {endpoint.deprecated && (
                      <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded">Deprecated</span>
                    )}
                    {endpoint.security && (
                      <Shield className="w-4 h-4 text-yellow-400" />
                    )}
                  </button>

                  {/* Endpoint Details */}
                  {isExpanded && (
                    <div className="border-t border-gray-700 p-6 space-y-6">
                      {/* Description */}
                      {endpoint.description && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-2">Description</h4>
                          <p className="text-gray-400 text-sm">{endpoint.description}</p>
                        </div>
                      )}

                      {/* Parameters */}
                      {endpoint.parameters && endpoint.parameters.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-3">Parameters</h4>
                          <div className="bg-gray-900/50 rounded-lg p-4">
                            {endpoint.parameters.map(param => renderParameter(param))}
                          </div>
                        </div>
                      )}

                      {/* Request Body */}
                      {endpoint.requestBody && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-3">Request Body</h4>
                          <div className="bg-gray-900/50 rounded-lg p-4">
                            {endpoint.requestBody.description && (
                              <p className="text-gray-400 text-sm mb-3">{endpoint.requestBody.description}</p>
                            )}
                            {tryItOut && (
                              <textarea
                                value={testBody}
                                onChange={(e) => setTestBody(e.target.value)}
                                placeholder="Enter request body (JSON)"
                                className="w-full h-32 px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none font-mono text-sm"
                              />
                            )}
                          </div>
                        </div>
                      )}

                      {/* Responses */}
                      {endpoint.responses && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-3">Responses</h4>
                          <div className="space-y-2">
                            {Object.entries(endpoint.responses).map(([code, response]) => (
                              <div key={code} className="bg-gray-900/50 rounded-lg p-4">
                                <div className="flex items-center gap-3 mb-2">
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                                    code.startsWith('2') ? 'bg-green-500/20 text-green-400' :
                                    code.startsWith('4') ? 'bg-yellow-500/20 text-yellow-400' :
                                    code.startsWith('5') ? 'bg-red-500/20 text-red-400' :
                                    'bg-gray-500/20 text-gray-400'
                                  }`}>
                                    {code}
                                  </span>
                                  <span className="text-gray-300 text-sm">{response.description}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Code Examples */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-3">Code Examples</h4>
                        <div className="space-y-3">
                          {Object.entries(generateCodeExample(endpoint, method, path)).map(([lang, code]) => (
                            <div key={lang} className="bg-gray-900/50 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-gray-400 uppercase">{lang}</span>
                                <button
                                  onClick={() => copyToClipboard(code, `${endpointId}-${lang}`)}
                                  className="text-gray-400 hover:text-white transition"
                                >
                                  {copiedCode === `${endpointId}-${lang}` ? (
                                    <Check className="w-4 h-4 text-green-400" />
                                  ) : (
                                    <Copy className="w-4 h-4" />
                                  )}
                                </button>
                              </div>
                              <pre className="text-gray-300 text-xs font-mono overflow-x-auto">
                                <code>{code}</code>
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Try It Out */}
                      {tryItOut && (
                        <div className="border-t border-gray-700 pt-6">
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-sm font-semibold text-gray-300">Test This Endpoint</h4>
                            <button
                              onClick={executeTest}
                              disabled={testLoading}
                              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition flex items-center gap-2"
                            >
                              {testLoading ? (
                                <>
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                  <span>Testing...</span>
                                </>
                              ) : (
                                <>
                                  <Send className="w-4 h-4" />
                                  <span>Send Request</span>
                                </>
                              )}
                            </button>
                          </div>

                          {/* Test Response */}
                          {testResponse && (
                            <div className="bg-gray-900/50 rounded-lg p-4">
                              <h5 className="text-sm font-semibold text-gray-300 mb-3">Response</h5>
                              {testResponse.error ? (
                                <div className="text-red-400">
                                  <p className="font-medium">Error:</p>
                                  <p className="text-sm mt-1">{testResponse.message}</p>
                                </div>
                              ) : (
                                <div>
                                  <div className="flex items-center gap-3 mb-3">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                      testResponse.status >= 200 && testResponse.status < 300 
                                        ? 'bg-green-500/20 text-green-400' 
                                        : 'bg-red-500/20 text-red-400'
                                    }`}>
                                      {testResponse.status} {testResponse.statusText}
                                    </span>
                                  </div>
                                  <pre className="text-gray-300 text-xs font-mono overflow-x-auto">
                                    <code>{JSON.stringify(testResponse.data, null, 2)}</code>
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {(!spec.paths || Object.keys(spec.paths).length === 0) && (
        <div className="text-center py-20">
          <FileJson className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400">No endpoints found in this API</p>
        </div>
      )}
      </div>
    </div>
  );
};

export default APIDocumentation;