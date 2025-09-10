import React, { useState, useMemo } from 'react';
import { 
  ChevronRightIcon, ChevronDownIcon, DocumentTextIcon, 
  PhotoIcon, TableCellsIcon, CodeBracketIcon,
  MagnifyingGlassIcon, ClipboardDocumentIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const ResponseViewer = ({ response, responseTime, statusCode }) => {
  const [viewMode, setViewMode] = useState('pretty'); // pretty, raw, preview, table
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedPath, setCopiedPath] = useState('');

  // Detect response type
  const responseType = useMemo(() => {
    if (!response) return 'unknown';
    
    if (typeof response === 'object') {
      if (Array.isArray(response)) return 'array';
      return 'json';
    }
    
    // Check if it's HTML
    if (typeof response === 'string') {
      if (response.trim().startsWith('<')) return 'html';
      if (response.includes('data:image')) return 'image';
      
      // Try to parse as JSON
      try {
        JSON.parse(response);
        return 'json';
      } catch {
        return 'text';
      }
    }
    
    return 'text';
  }, [response]);

  // Parse response if it's a string JSON
  const parsedResponse = useMemo(() => {
    if (typeof response === 'string' && responseType === 'json') {
      try {
        return JSON.parse(response);
      } catch {
        return response;
      }
    }
    return response;
  }, [response, responseType]);

  // Toggle node expansion in tree view
  const toggleNode = (path) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedNodes(newExpanded);
  };

  // Copy value to clipboard
  const copyToClipboard = (value, path = '') => {
    const textToCopy = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
    navigator.clipboard.writeText(textToCopy);
    setCopiedPath(path);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopiedPath(''), 2000);
  };

  // Search filter for JSON
  const filterJson = (obj, query, path = '') => {
    if (!query) return obj;
    
    const lowerQuery = query.toLowerCase();
    
    if (typeof obj === 'object' && obj !== null) {
      if (Array.isArray(obj)) {
        return obj.map((item, index) => 
          filterJson(item, query, `${path}[${index}]`)
        ).filter(item => item !== undefined);
      } else {
        const filtered = {};
        for (const [key, value] of Object.entries(obj)) {
          const keyPath = path ? `${path}.${key}` : key;
          
          // Check if key matches
          if (key.toLowerCase().includes(lowerQuery)) {
            filtered[key] = value;
          } 
          // Check if value matches
          else if (typeof value === 'string' && value.toLowerCase().includes(lowerQuery)) {
            filtered[key] = value;
          }
          // Recursively check nested objects
          else if (typeof value === 'object') {
            const filteredValue = filterJson(value, query, keyPath);
            if (Object.keys(filteredValue).length > 0 || (Array.isArray(filteredValue) && filteredValue.length > 0)) {
              filtered[key] = filteredValue;
            }
          }
        }
        return filtered;
      }
    }
    
    // For primitive values
    if (String(obj).toLowerCase().includes(lowerQuery)) {
      return obj;
    }
    
    return undefined;
  };

  // Render JSON tree node
  const renderJsonNode = (data, path = '', level = 0) => {
    if (data === null) return <span className="text-gray-500">null</span>;
    if (data === undefined) return <span className="text-gray-500">undefined</span>;
    
    const isExpanded = expandedNodes.has(path) || level === 0 || searchQuery;
    
    if (typeof data === 'object') {
      const isArray = Array.isArray(data);
      const entries = isArray ? data.map((v, i) => [i, v]) : Object.entries(data);
      
      if (entries.length === 0) {
        return <span className="text-gray-500">{isArray ? '[]' : '{}'}</span>;
      }
      
      return (
        <div className={level > 0 ? 'ml-4' : ''}>
          <div 
            className="flex items-center gap-1 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded px-1"
            onClick={() => !searchQuery && toggleNode(path)}
          >
            {!searchQuery && (
              isExpanded ? 
                <ChevronDownIcon className="w-3 h-3 text-gray-500" /> : 
                <ChevronRightIcon className="w-3 h-3 text-gray-500" />
            )}
            <span className="text-gray-500">{isArray ? '[' : '{'}</span>
            {!isExpanded && (
              <span className="text-gray-400 text-xs ml-1">
                {entries.length} {isArray ? 'items' : 'keys'}
              </span>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                copyToClipboard(data, path);
              }}
              className={`ml-auto opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 ${
                copiedPath === path ? 'opacity-100' : ''
              }`}
            >
              <ClipboardDocumentIcon className="w-3 h-3 text-gray-500" />
            </button>
          </div>
          
          {isExpanded && (
            <div className="ml-4">
              {entries.map(([key, value]) => {
                const keyPath = isArray ? `${path}[${key}]` : (path ? `${path}.${key}` : key);
                
                return (
                  <div key={key} className="group flex items-start gap-2 py-0.5">
                    <span className="text-blue-600 dark:text-blue-400">
                      {isArray ? key : `"${key}"`}:
                    </span>
                    {typeof value === 'object' ? (
                      renderJsonNode(value, keyPath, level + 1)
                    ) : (
                      <div className="flex items-center gap-1 flex-1">
                        {renderPrimitiveValue(value)}
                        <button
                          onClick={() => copyToClipboard(value, keyPath)}
                          className={`opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 ${
                            copiedPath === keyPath ? 'opacity-100' : ''
                          }`}
                        >
                          <ClipboardDocumentIcon className="w-3 h-3 text-gray-500" />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          
          <span className="text-gray-500">{isArray ? ']' : '}'}</span>
        </div>
      );
    }
    
    return renderPrimitiveValue(data);
  };

  // Render primitive values with syntax highlighting
  const renderPrimitiveValue = (value) => {
    if (typeof value === 'string') {
      // Check if it's a URL
      if (value.startsWith('http://') || value.startsWith('https://')) {
        return (
          <a 
            href={value} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-green-600 dark:text-green-400 hover:underline"
          >
            "{value}"
          </a>
        );
      }
      return <span className="text-green-600 dark:text-green-400">"{value}"</span>;
    }
    if (typeof value === 'number') {
      return <span className="text-purple-600 dark:text-purple-400">{value}</span>;
    }
    if (typeof value === 'boolean') {
      return <span className="text-orange-600 dark:text-orange-400">{String(value)}</span>;
    }
    return <span className="text-gray-700 dark:text-gray-300">{String(value)}</span>;
  };

  // Render table view for arrays
  const renderTableView = (data) => {
    if (!Array.isArray(data) || data.length === 0) {
      return <div className="text-gray-500">No tabular data available</div>;
    }
    
    // Get all unique keys from all objects
    const allKeys = new Set();
    data.forEach(item => {
      if (typeof item === 'object' && item !== null) {
        Object.keys(item).forEach(key => allKeys.add(key));
      }
    });
    
    const keys = Array.from(allKeys);
    
    if (keys.length === 0) {
      return <div className="text-gray-500">Data is not in tabular format</div>;
    }
    
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                #
              </th>
              {keys.map(key => (
                <th 
                  key={key}
                  className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {data.map((item, index) => (
              <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-4 py-2 text-sm text-gray-500">
                  {index + 1}
                </td>
                {keys.map(key => (
                  <td key={key} className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100">
                    {item && typeof item === 'object' ? 
                      (typeof item[key] === 'object' ? 
                        JSON.stringify(item[key]) : 
                        String(item[key] ?? '-')
                      ) : '-'
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Get status color
  const getStatusColor = (code) => {
    if (code >= 200 && code < 300) return 'text-green-600';
    if (code >= 300 && code < 400) return 'text-blue-600';
    if (code >= 400 && code < 500) return 'text-yellow-600';
    if (code >= 500) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {statusCode && (
              <span className={`font-semibold ${getStatusColor(statusCode)}`}>
                {statusCode}
              </span>
            )}
            {responseTime && (
              <span className="text-sm text-gray-500">
                {responseTime}ms
              </span>
            )}
            <span className="text-sm text-gray-500">
              {responseType.toUpperCase()}
            </span>
          </div>
          
          {/* View mode tabs */}
          <div className="flex items-center gap-2">
            {responseType === 'json' && (
              <>
                <button
                  onClick={() => setViewMode('pretty')}
                  className={`px-3 py-1 text-sm rounded ${
                    viewMode === 'pretty' 
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' 
                      : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                  }`}
                >
                  <CodeBracketIcon className="w-4 h-4 inline mr-1" />
                  Pretty
                </button>
                {Array.isArray(parsedResponse) && (
                  <button
                    onClick={() => setViewMode('table')}
                    className={`px-3 py-1 text-sm rounded ${
                      viewMode === 'table' 
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' 
                        : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                    }`}
                  >
                    <TableCellsIcon className="w-4 h-4 inline mr-1" />
                    Table
                  </button>
                )}
              </>
            )}
            
            <button
              onClick={() => setViewMode('raw')}
              className={`px-3 py-1 text-sm rounded ${
                viewMode === 'raw' 
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' 
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
              }`}
            >
              <DocumentTextIcon className="w-4 h-4 inline mr-1" />
              Raw
            </button>
            
            {responseType === 'html' && (
              <button
                onClick={() => setViewMode('preview')}
                className={`px-3 py-1 text-sm rounded ${
                  viewMode === 'preview' 
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' 
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                }`}
              >
                <PhotoIcon className="w-4 h-4 inline mr-1" />
                Preview
              </button>
            )}
          </div>
        </div>
        
        {/* Search bar for JSON */}
        {responseType === 'json' && viewMode === 'pretty' && (
          <div className="mt-3">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search in response..."
                className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800"
              />
            </div>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="p-4 max-h-[600px] overflow-auto">
        {!response ? (
          <div className="text-gray-500 text-center py-8">No response data</div>
        ) : (
          <>
            {/* Pretty JSON View */}
            {viewMode === 'pretty' && responseType === 'json' && (
              <div className="font-mono text-sm">
                {renderJsonNode(
                  searchQuery ? filterJson(parsedResponse, searchQuery) : parsedResponse
                )}
              </div>
            )}
            
            {/* Table View */}
            {viewMode === 'table' && responseType === 'json' && (
              renderTableView(parsedResponse)
            )}
            
            {/* Raw View */}
            {viewMode === 'raw' && (
              <pre className="font-mono text-sm whitespace-pre-wrap break-words text-gray-700 dark:text-gray-300">
                {typeof response === 'object' ? 
                  JSON.stringify(response, null, 2) : 
                  response
                }
              </pre>
            )}
            
            {/* HTML Preview */}
            {viewMode === 'preview' && responseType === 'html' && (
              <div className="border border-gray-200 dark:border-gray-700 rounded p-4">
                <iframe
                  srcDoc={response}
                  className="w-full h-[500px]"
                  sandbox="allow-scripts"
                  title="HTML Preview"
                />
              </div>
            )}
            
            {/* Image Preview */}
            {responseType === 'image' && (
              <div className="flex justify-center">
                <img 
                  src={response} 
                  alt="Response" 
                  className="max-w-full h-auto"
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ResponseViewer;