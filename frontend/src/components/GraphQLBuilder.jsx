import React, { useState, useEffect } from 'react';
import { 
  Code2, 
  Play, 
  FileJson, 
  Braces, 
  Variable,
  Download,
  Copy,
  CheckCircle,
  AlertCircle,
  Loader2,
  ChevronRight,
  ChevronDown,
  Book,
  Zap
} from 'lucide-react';

const GraphQLBuilder = ({ 
  endpoint, 
  headers = [], 
  onResponse, 
  currentEnvironment,
  replaceVariables 
}) => {
  const [query, setQuery] = useState(`query {
  # Start typing your GraphQL query here
  # Example:
  # users {
  #   id
  #   name
  #   email
  # }
}`);
  
  const [variables, setVariables] = useState('{}');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('query');
  const [responseTab, setResponseTab] = useState('data');
  const [copied, setCopied] = useState(false);
  const [schema, setSchema] = useState(null);
  const [showDocs, setShowDocs] = useState(false);
  const [queryHistory, setQueryHistory] = useState([]);
  const [savedQueries, setSavedQueries] = useState([]);
  const [queryName, setQueryName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Common GraphQL templates
  const templates = [
    {
      name: 'Basic Query',
      query: `query GetData {
  # Replace with your query
  items {
    id
    name
  }
}`
    },
    {
      name: 'Query with Variables',
      query: `query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
  }
}`,
      variables: '{\n  "id": "1"\n}'
    },
    {
      name: 'Mutation',
      query: `mutation CreateItem($input: ItemInput!) {
  createItem(input: $input) {
    id
    name
    success
  }
}`,
      variables: '{\n  "input": {\n    "name": "New Item"\n  }\n}'
    },
    {
      name: 'Subscription',
      query: `subscription OnItemAdded {
  itemAdded {
    id
    name
    timestamp
  }
}`
    }
  ];

  useEffect(() => {
    // Load saved queries from localStorage
    const saved = localStorage.getItem('savedGraphQLQueries');
    if (saved) {
      setSavedQueries(JSON.parse(saved));
    }
    
    // Load query history
    const history = localStorage.getItem('graphqlQueryHistory');
    if (history) {
      setQueryHistory(JSON.parse(history).slice(0, 10));
    }
  }, []);

  const executeQuery = async () => {
    if (!endpoint) {
      setError('Please enter a GraphQL endpoint URL');
      return;
    }

    setLoading(true);
    setError(null);
    const startTime = Date.now();

    try {
      // Parse variables
      let parsedVariables = {};
      if (variables.trim()) {
        try {
          parsedVariables = JSON.parse(variables);
        } catch (e) {
          throw new Error('Invalid JSON in variables');
        }
      }

      // Build request body
      const requestBody = {
        query: query,
        variables: parsedVariables
      };

      // Build headers
      const requestHeaders = {
        'Content-Type': 'application/json'
      };
      
      headers.forEach(header => {
        if (header.enabled && header.key) {
          let value = header.value;
          if (replaceVariables && currentEnvironment) {
            value = replaceVariables(value, currentEnvironment);
          }
          requestHeaders[header.key] = value;
        }
      });

      // Make request
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: requestHeaders,
        body: JSON.stringify(requestBody)
      });

      const responseTime = Date.now() - startTime;
      const data = await response.json();

      const result = {
        data: data,
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        responseTime
      };

      setResponse(result);
      
      if (onResponse) {
        onResponse(result);
      }

      // Add to history
      const historyItem = {
        query,
        variables,
        endpoint,
        timestamp: new Date().toISOString()
      };
      
      const newHistory = [historyItem, ...queryHistory.slice(0, 9)];
      setQueryHistory(newHistory);
      localStorage.setItem('graphqlQueryHistory', JSON.stringify(newHistory));

      // Check for GraphQL errors
      if (data.errors) {
        setError(`GraphQL Errors: ${data.errors.map(e => e.message).join(', ')}`);
      }
    } catch (err) {
      setError(err.message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  };

  const introspectSchema = async () => {
    const introspectionQuery = `
      query IntrospectionQuery {
        __schema {
          types {
            name
            kind
            description
            fields {
              name
              type {
                name
                kind
              }
            }
          }
        }
      }
    `;

    setLoading(true);
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: introspectionQuery })
      });

      const data = await response.json();
      if (data.data && data.data.__schema) {
        setSchema(data.data.__schema);
        setShowDocs(true);
      }
    } catch (err) {
      setError('Failed to fetch schema');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplate = (template) => {
    setQuery(template.query);
    if (template.variables) {
      setVariables(template.variables);
    }
  };

  const saveQuery = () => {
    if (!queryName.trim()) return;

    const newQuery = {
      id: Date.now().toString(),
      name: queryName,
      query,
      variables,
      createdAt: new Date().toISOString()
    };

    const updated = [...savedQueries, newQuery];
    setSavedQueries(updated);
    localStorage.setItem('savedGraphQLQueries', JSON.stringify(updated));
    setShowSaveDialog(false);
    setQueryName('');
  };

  const loadSavedQuery = (saved) => {
    setQuery(saved.query);
    setVariables(saved.variables || '{}');
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadResponse = () => {
    if (!response) return;
    
    const blob = new Blob([JSON.stringify(response.data, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `graphql-response-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Templates Bar */}
      <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-500" />
            Quick Templates
          </h3>
          <button
            onClick={introspectSchema}
            className="text-xs px-3 py-1 bg-purple-600/20 text-purple-400 rounded-lg hover:bg-purple-600/30 transition-colors flex items-center gap-1"
          >
            <Book className="w-3 h-3" />
            Fetch Schema
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {templates.map((template) => (
            <button
              key={template.name}
              onClick={() => loadTemplate(template)}
              className="px-3 py-1.5 text-xs bg-gray-700/50 text-gray-300 rounded-lg hover:bg-gray-700 hover:text-purple-400 transition-colors"
            >
              {template.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Editor */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Query Editor Side */}
        <div className="space-y-4">
          {/* Tabs */}
          <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700">
            <div className="border-b border-gray-700">
              <div className="flex gap-1 p-1">
                <button
                  onClick={() => setActiveTab('query')}
                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'query'
                      ? 'bg-purple-600/20 text-purple-400'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                  }`}
                >
                  Query
                </button>
                <button
                  onClick={() => setActiveTab('variables')}
                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'variables'
                      ? 'bg-purple-600/20 text-purple-400'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                  }`}
                >
                  Variables
                </button>
                <button
                  onClick={() => setActiveTab('saved')}
                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'saved'
                      ? 'bg-purple-600/20 text-purple-400'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                  }`}
                >
                  Saved ({savedQueries.length})
                </button>
              </div>
            </div>

            <div className="p-4">
              {activeTab === 'query' && (
                <div className="space-y-3">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full h-96 px-3 py-2 bg-gray-900 text-gray-300 font-mono text-sm border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                    placeholder="Enter your GraphQL query here..."
                    spellCheck={false}
                  />
                  <div className="flex justify-between">
                    <button
                      onClick={() => setShowSaveDialog(true)}
                      className="px-3 py-1.5 text-sm bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Save Query
                    </button>
                    <button
                      onClick={() => copyToClipboard(query)}
                      className="px-3 py-1.5 text-sm bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
                    >
                      {copied ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                      Copy
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'variables' && (
                <div className="space-y-3">
                  <textarea
                    value={variables}
                    onChange={(e) => setVariables(e.target.value)}
                    className="w-full h-96 px-3 py-2 bg-gray-900 text-gray-300 font-mono text-sm border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                    placeholder='{\n  "variableName": "value"\n}'
                    spellCheck={false}
                  />
                  <p className="text-xs text-gray-500">
                    Enter variables as valid JSON. These will be sent with your query.
                  </p>
                </div>
              )}

              {activeTab === 'saved' && (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {savedQueries.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No saved queries yet</p>
                  ) : (
                    savedQueries.map((saved) => (
                      <div
                        key={saved.id}
                        className="p-3 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 cursor-pointer transition-colors"
                        onClick={() => loadSavedQuery(saved)}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-300">{saved.name}</span>
                          <span className="text-xs text-gray-500">
                            {new Date(saved.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                        <pre className="text-xs text-gray-500 mt-1 truncate">
                          {saved.query.split('\n')[0]}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Execute Button */}
          <button
            onClick={executeQuery}
            disabled={loading || !endpoint}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
              loading || !endpoint
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Executing...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Execute Query
              </>
            )}
          </button>

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-900/20 border border-red-700 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Response Side */}
        <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700">
          <div className="border-b border-gray-700 p-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-300">Response</h3>
              {response && (
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    response.status === 200 
                      ? 'bg-green-900/20 text-green-400 border border-green-700'
                      : 'bg-red-900/20 text-red-400 border border-red-700'
                  }`}>
                    {response.status} {response.statusText}
                  </span>
                  <span className="text-xs text-gray-500">
                    {response.responseTime}ms
                  </span>
                  <button
                    onClick={downloadResponse}
                    className="p-1 text-gray-400 hover:text-purple-400 transition-colors"
                    title="Download Response"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {response ? (
            <div className="p-4">
              <div className="border-b border-gray-700 mb-3">
                <div className="flex gap-1">
                  <button
                    onClick={() => setResponseTab('data')}
                    className={`px-3 py-2 text-sm font-medium transition-colors ${
                      responseTab === 'data'
                        ? 'text-purple-400 border-b-2 border-purple-400'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Data
                  </button>
                  <button
                    onClick={() => setResponseTab('headers')}
                    className={`px-3 py-2 text-sm font-medium transition-colors ${
                      responseTab === 'headers'
                        ? 'text-purple-400 border-b-2 border-purple-400'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Headers
                  </button>
                </div>
              </div>

              <div className="max-h-96 overflow-auto">
                {responseTab === 'data' && (
                  <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                    {JSON.stringify(response.data, null, 2)}
                  </pre>
                )}
                {responseTab === 'headers' && (
                  <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                    {JSON.stringify(response.headers, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-gray-500">
              <Code2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Execute a query to see the response</p>
            </div>
          )}
        </div>
      </div>

      {/* Save Query Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 rounded-xl border border-gray-700 p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-white mb-4">Save Query</h3>
            <input
              type="text"
              value={queryName}
              onChange={(e) => setQueryName(e.target.value)}
              placeholder="Enter query name..."
              className="w-full px-3 py-2 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 mb-4"
              autoFocus
            />
            <div className="flex gap-3">
              <button
                onClick={saveQuery}
                disabled={!queryName.trim()}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:bg-gray-700 disabled:text-gray-500"
              >
                Save
              </button>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="flex-1 px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphQLBuilder;