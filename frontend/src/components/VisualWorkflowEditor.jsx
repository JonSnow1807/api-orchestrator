import React, { useState, useCallback, useRef, useEffect } from 'react';
import { 
  Play, 
  Plus, 
  Trash2, 
  Save, 
  Download, 
  Upload,
  Link2,
  Settings,
  Eye,
  Code,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle
} from 'lucide-react';

const VisualWorkflowEditor = ({ projectId }) => {
  const [workflow, setWorkflow] = useState({
    name: 'New Workflow',
    description: '',
    nodes: [],
    connections: [],
    variables: {}
  });
  
  const [selectedNode, setSelectedNode] = useState(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState(null);
  const [executionResults, setExecutionResults] = useState({});
  const [isExecuting, setIsExecuting] = useState(false);
  
  const canvasRef = useRef(null);
  const [canvasSize, setCanvasSize] = useState({ width: 1200, height: 800 });

  // Node types
  const nodeTypes = [
    { type: 'http', label: 'HTTP Request', icon: '🌐', color: 'bg-blue-500' },
    { type: 'condition', label: 'Condition', icon: '🔀', color: 'bg-yellow-500' },
    { type: 'loop', label: 'Loop', icon: '🔄', color: 'bg-purple-500' },
    { type: 'delay', label: 'Delay', icon: '⏱️', color: 'bg-gray-500' },
    { type: 'script', label: 'Script', icon: '📝', color: 'bg-green-500' },
    { type: 'parallel', label: 'Parallel', icon: '⚡', color: 'bg-orange-500' },
    { type: 'data', label: 'Data Transform', icon: '🔧', color: 'bg-indigo-500' },
    { type: 'webhook', label: 'Webhook', icon: '🪝', color: 'bg-pink-500' }
  ];

  // Add a new node
  const addNode = (type) => {
    const newNode = {
      id: `node_${Date.now()}`,
      type: type.type,
      label: type.label,
      icon: type.icon,
      color: type.color,
      position: {
        x: Math.random() * 600 + 100,
        y: Math.random() * 400 + 100
      },
      config: getDefaultConfig(type.type),
      status: 'idle' // idle, running, success, error
    };
    
    setWorkflow(prev => ({
      ...prev,
      nodes: [...prev.nodes, newNode]
    }));
    
    setSelectedNode(newNode.id);
  };

  // Get default configuration for node type
  const getDefaultConfig = (type) => {
    switch (type) {
      case 'http':
        return {
          method: 'GET',
          url: '',
          headers: {},
          body: '',
          extract: {} // Variable extraction
        };
      case 'condition':
        return {
          expression: '',
          trueNode: null,
          falseNode: null
        };
      case 'loop':
        return {
          items: '[]',
          variable: 'item',
          maxIterations: 100
        };
      case 'delay':
        return {
          duration: 1000,
          unit: 'ms'
        };
      case 'script':
        return {
          language: 'javascript',
          code: ''
        };
      case 'parallel':
        return {
          branches: [],
          waitForAll: true
        };
      case 'data':
        return {
          transform: '',
          inputVariable: '',
          outputVariable: ''
        };
      case 'webhook':
        return {
          url: '',
          secret: '',
          timeout: 30000
        };
      default:
        return {};
    }
  };

  // Handle node drag
  const handleNodeDrag = (nodeId, newPosition) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: prev.nodes.map(node =>
        node.id === nodeId
          ? { ...node, position: newPosition }
          : node
      )
    }));
  };

  // Handle connection creation
  const startConnection = (nodeId) => {
    setIsConnecting(true);
    setConnectionStart(nodeId);
  };

  const endConnection = (nodeId) => {
    if (isConnecting && connectionStart && connectionStart !== nodeId) {
      const newConnection = {
        id: `conn_${Date.now()}`,
        from: connectionStart,
        to: nodeId
      };
      
      setWorkflow(prev => ({
        ...prev,
        connections: [...prev.connections, newConnection]
      }));
    }
    
    setIsConnecting(false);
    setConnectionStart(null);
  };

  // Delete node
  const deleteNode = (nodeId) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: prev.nodes.filter(n => n.id !== nodeId),
      connections: prev.connections.filter(
        c => c.from !== nodeId && c.to !== nodeId
      )
    }));
    
    if (selectedNode === nodeId) {
      setSelectedNode(null);
    }
  };

  // Execute workflow
  const executeWorkflow = async () => {
    setIsExecuting(true);
    setExecutionResults({});
    
    try {
      const response = await fetch(`/api/workflows/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          workflow: workflow,
          projectId: projectId
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setExecutionResults(result.results);
        
        // Update node statuses based on results
        setWorkflow(prev => ({
          ...prev,
          nodes: prev.nodes.map(node => ({
            ...node,
            status: result.results[node.id]?.success ? 'success' : 
                   result.results[node.id]?.error ? 'error' : 'idle'
          }))
        }));
      }
    } catch (error) {
      console.error('Workflow execution failed:', error);
    } finally {
      setIsExecuting(false);
    }
  };

  // Save workflow
  const saveWorkflow = async () => {
    try {
      const response = await fetch(`/api/workflows`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...workflow,
          projectId: projectId
        })
      });
      
      if (response.ok) {
        alert('Workflow saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save workflow:', error);
    }
  };

  // Export workflow
  const exportWorkflow = () => {
    const dataStr = JSON.stringify(workflow, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `${workflow.name.replace(/\s+/g, '_')}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  // Import workflow
  const importWorkflow = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          setWorkflow(imported);
        } catch (error) {
          alert('Invalid workflow file');
        }
      };
      reader.readAsText(file);
    }
  };

  // Render connection line
  const renderConnection = (connection) => {
    const fromNode = workflow.nodes.find(n => n.id === connection.from);
    const toNode = workflow.nodes.find(n => n.id === connection.to);
    
    if (!fromNode || !toNode) return null;
    
    const x1 = fromNode.position.x + 100;
    const y1 = fromNode.position.y + 40;
    const x2 = toNode.position.x;
    const y2 = toNode.position.y + 40;
    
    // Calculate control points for curved line
    const dx = x2 - x1;
    const dy = y2 - y1;
    const cx1 = x1 + dx * 0.5;
    const cy1 = y1;
    const cx2 = x2 - dx * 0.5;
    const cy2 = y2;
    
    return (
      <svg
        key={connection.id}
        className="absolute top-0 left-0 pointer-events-none"
        style={{ width: '100%', height: '100%' }}
      >
        <path
          d={`M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`}
          stroke="#94a3b8"
          strokeWidth="2"
          fill="none"
          strokeDasharray="5,5"
        />
        <circle cx={x2} cy={y2} r="4" fill="#94a3b8" />
      </svg>
    );
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Toolbar */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            value={workflow.name}
            onChange={(e) => setWorkflow(prev => ({ ...prev, name: e.target.value }))}
            className="text-lg font-semibold px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          <button
            onClick={executeWorkflow}
            disabled={isExecuting}
            className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            <span>{isExecuting ? 'Running...' : 'Run'}</span>
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={saveWorkflow}
            className="p-2 hover:bg-gray-100 rounded"
            title="Save Workflow"
          >
            <Save className="w-5 h-5" />
          </button>
          
          <button
            onClick={exportWorkflow}
            className="p-2 hover:bg-gray-100 rounded"
            title="Export Workflow"
          >
            <Download className="w-5 h-5" />
          </button>
          
          <label className="p-2 hover:bg-gray-100 rounded cursor-pointer" title="Import Workflow">
            <Upload className="w-5 h-5" />
            <input
              type="file"
              accept=".json"
              onChange={importWorkflow}
              className="hidden"
            />
          </label>
        </div>
      </div>
      
      <div className="flex-1 flex">
        {/* Node Palette */}
        <div className="w-64 bg-white border-r p-4">
          <h3 className="font-semibold mb-4">Add Nodes</h3>
          <div className="space-y-2">
            {nodeTypes.map(type => (
              <button
                key={type.type}
                onClick={() => addNode(type)}
                className="w-full flex items-center space-x-3 px-3 py-2 hover:bg-gray-50 rounded border"
              >
                <span className="text-xl">{type.icon}</span>
                <span className="text-sm">{type.label}</span>
              </button>
            ))}
          </div>
          
          {/* Variables */}
          <div className="mt-6">
            <h3 className="font-semibold mb-2">Variables</h3>
            <div className="space-y-1 text-sm">
              {Object.entries(workflow.variables).map(([key, value]) => (
                <div key={key} className="flex justify-between p-2 bg-gray-50 rounded">
                  <span className="font-mono">{key}</span>
                  <span className="text-gray-500 truncate max-w-[100px]">{JSON.stringify(value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Canvas */}
        <div className="flex-1 relative overflow-auto">
          <div
            ref={canvasRef}
            className="relative"
            style={{ width: canvasSize.width, height: canvasSize.height }}
          >
            {/* Render connections */}
            {workflow.connections.map(conn => renderConnection(conn))}
            
            {/* Render nodes */}
            {workflow.nodes.map(node => (
              <div
                key={node.id}
                className={`absolute bg-white rounded-lg shadow-lg border-2 cursor-move
                  ${selectedNode === node.id ? 'border-blue-500' : 'border-gray-200'}
                  ${node.status === 'running' ? 'animate-pulse' : ''}
                `}
                style={{
                  left: node.position.x,
                  top: node.position.y,
                  width: '200px'
                }}
                onClick={() => setSelectedNode(node.id)}
                onMouseDown={(e) => {
                  const startX = e.clientX - node.position.x;
                  const startY = e.clientY - node.position.y;
                  
                  const handleMouseMove = (e) => {
                    handleNodeDrag(node.id, {
                      x: e.clientX - startX,
                      y: e.clientY - startY
                    });
                  };
                  
                  const handleMouseUp = () => {
                    document.removeEventListener('mousemove', handleMouseMove);
                    document.removeEventListener('mouseup', handleMouseUp);
                  };
                  
                  document.addEventListener('mousemove', handleMouseMove);
                  document.addEventListener('mouseup', handleMouseUp);
                }}
              >
                <div className={`px-3 py-2 ${node.color} text-white rounded-t-lg flex items-center justify-between`}>
                  <div className="flex items-center space-x-2">
                    <span>{node.icon}</span>
                    <span className="text-sm font-medium">{node.label}</span>
                  </div>
                  
                  {/* Status indicator */}
                  {node.status === 'success' && <CheckCircle className="w-4 h-4" />}
                  {node.status === 'error' && <XCircle className="w-4 h-4" />}
                  {node.status === 'running' && <Clock className="w-4 h-4 animate-spin" />}
                </div>
                
                <div className="p-3">
                  {/* Node-specific content */}
                  {node.type === 'http' && (
                    <div className="text-xs space-y-1">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Method:</span>
                        <span className="font-mono">{node.config.method}</span>
                      </div>
                      <div className="truncate">
                        <span className="text-gray-500">URL:</span>
                        <span className="font-mono ml-1">{node.config.url || 'Not set'}</span>
                      </div>
                    </div>
                  )}
                  
                  {node.type === 'condition' && (
                    <div className="text-xs">
                      <span className="text-gray-500">Expression:</span>
                      <div className="font-mono mt-1 truncate">{node.config.expression || 'Not set'}</div>
                    </div>
                  )}
                  
                  {node.type === 'delay' && (
                    <div className="text-xs">
                      <span className="text-gray-500">Duration:</span>
                      <span className="font-mono ml-1">{node.config.duration}{node.config.unit}</span>
                    </div>
                  )}
                  
                  {/* Connection points */}
                  <div className="flex justify-between mt-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (isConnecting) {
                          endConnection(node.id);
                        }
                      }}
                      className="w-3 h-3 bg-blue-500 rounded-full hover:ring-2 hover:ring-blue-300"
                      title="Input"
                    />
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startConnection(node.id);
                      }}
                      className="w-3 h-3 bg-green-500 rounded-full hover:ring-2 hover:ring-green-300"
                      title="Output"
                    />
                  </div>
                  
                  {/* Action buttons */}
                  <div className="flex justify-end mt-2 space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // Open config modal
                      }}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <Settings className="w-3 h-3" />
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNode(node.id);
                      }}
                      className="p-1 hover:bg-red-100 rounded text-red-500"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Properties Panel */}
        {selectedNode && (
          <div className="w-80 bg-white border-l p-4">
            <h3 className="font-semibold mb-4">Node Properties</h3>
            {(() => {
              const node = workflow.nodes.find(n => n.id === selectedNode);
              if (!node) return null;
              
              return (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Node ID</label>
                    <input
                      type="text"
                      value={node.id}
                      disabled
                      className="w-full px-3 py-2 border rounded bg-gray-50"
                    />
                  </div>
                  
                  {node.type === 'http' && (
                    <>
                      <div>
                        <label className="block text-sm font-medium mb-1">Method</label>
                        <select
                          value={node.config.method}
                          onChange={(e) => {
                            setWorkflow(prev => ({
                              ...prev,
                              nodes: prev.nodes.map(n =>
                                n.id === node.id
                                  ? { ...n, config: { ...n.config, method: e.target.value } }
                                  : n
                              )
                            }));
                          }}
                          className="w-full px-3 py-2 border rounded"
                        >
                          <option>GET</option>
                          <option>POST</option>
                          <option>PUT</option>
                          <option>DELETE</option>
                          <option>PATCH</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium mb-1">URL</label>
                        <input
                          type="text"
                          value={node.config.url}
                          onChange={(e) => {
                            setWorkflow(prev => ({
                              ...prev,
                              nodes: prev.nodes.map(n =>
                                n.id === node.id
                                  ? { ...n, config: { ...n.config, url: e.target.value } }
                                  : n
                              )
                            }));
                          }}
                          placeholder="https://api.example.com/endpoint"
                          className="w-full px-3 py-2 border rounded"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium mb-1">Headers (JSON)</label>
                        <textarea
                          value={JSON.stringify(node.config.headers, null, 2)}
                          onChange={(e) => {
                            try {
                              const headers = JSON.parse(e.target.value);
                              setWorkflow(prev => ({
                                ...prev,
                                nodes: prev.nodes.map(n =>
                                  n.id === node.id
                                    ? { ...n, config: { ...n.config, headers } }
                                    : n
                                )
                              }));
                            } catch (error) {
                              // Invalid JSON
                            }
                          }}
                          className="w-full px-3 py-2 border rounded font-mono text-xs"
                          rows="4"
                        />
                      </div>
                    </>
                  )}
                  
                  {node.type === 'condition' && (
                    <div>
                      <label className="block text-sm font-medium mb-1">Expression</label>
                      <textarea
                        value={node.config.expression}
                        onChange={(e) => {
                          setWorkflow(prev => ({
                            ...prev,
                            nodes: prev.nodes.map(n =>
                              n.id === node.id
                                ? { ...n, config: { ...n.config, expression: e.target.value } }
                                : n
                            )
                          }));
                        }}
                        placeholder="response.status === 200"
                        className="w-full px-3 py-2 border rounded font-mono text-xs"
                        rows="3"
                      />
                    </div>
                  )}
                  
                  {/* Execution results */}
                  {executionResults[node.id] && (
                    <div className="border-t pt-4">
                      <h4 className="font-medium mb-2">Execution Result</h4>
                      <div className="bg-gray-50 p-2 rounded text-xs">
                        {executionResults[node.id].success ? (
                          <div className="text-green-600">
                            <CheckCircle className="w-4 h-4 inline mr-1" />
                            Success
                          </div>
                        ) : (
                          <div className="text-red-600">
                            <XCircle className="w-4 h-4 inline mr-1" />
                            {executionResults[node.id].error}
                          </div>
                        )}
                        
                        {executionResults[node.id].data && (
                          <pre className="mt-2 overflow-auto">
                            {JSON.stringify(executionResults[node.id].data, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualWorkflowEditor;