import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  MarkerType,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom node components for different block types
const ApiCallNode = ({ data, isConnectable }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-gradient-to-r from-blue-500 to-blue-600 border-2 border-blue-400 text-white min-w-[200px]">
      <div className="flex items-center">
        <div className="ml-2">
          <div className="text-lg font-bold">🌐 API Call</div>
          <div className="text-sm opacity-80">{data.method} {data.url || 'Configure endpoint'}</div>
          <div className="text-xs opacity-60">{data.description || 'Make HTTP request'}</div>
        </div>
      </div>
      <div className="mt-2 flex justify-between text-xs">
        <span>Status: {data.status || 'Ready'}</span>
        <span>Timeout: {data.timeout || 30}s</span>
      </div>
    </div>
  );
};

const DecisionNode = ({ data, isConnectable }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-gradient-to-r from-yellow-500 to-yellow-600 border-2 border-yellow-400 text-white min-w-[200px]">
      <div className="flex items-center">
        <div className="ml-2">
          <div className="text-lg font-bold">🤔 Decision</div>
          <div className="text-sm opacity-80">{data.condition || 'Configure condition'}</div>
          <div className="text-xs opacity-60">Conditional logic & branching</div>
        </div>
      </div>
      <div className="mt-2 text-xs">
        <div className="flex justify-between">
          <span className="bg-green-500 px-1 rounded">True →</span>
          <span className="bg-red-500 px-1 rounded">False →</span>
        </div>
      </div>
    </div>
  );
};

const DataTransformNode = ({ data, isConnectable }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-gradient-to-r from-purple-500 to-purple-600 border-2 border-purple-400 text-white min-w-[200px]">
      <div className="flex items-center">
        <div className="ml-2">
          <div className="text-lg font-bold">🔄 Transform</div>
          <div className="text-sm opacity-80">{data.operation || 'Configure transformation'}</div>
          <div className="text-xs opacity-60">Process & transform data</div>
        </div>
      </div>
      <div className="mt-2 text-xs opacity-80">
        <div>Input: {data.inputFormat || 'JSON'}</div>
        <div>Output: {data.outputFormat || 'JSON'}</div>
      </div>
    </div>
  );
};

const AINode = ({ data, isConnectable }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-gradient-to-r from-indigo-500 to-indigo-600 border-2 border-indigo-400 text-white min-w-[200px]">
      <div className="flex items-center">
        <div className="ml-2">
          <div className="text-lg font-bold">🤖 AI Block</div>
          <div className="text-sm opacity-80">{data.aiType || 'Configure AI task'}</div>
          <div className="text-xs opacity-60">AI-powered processing</div>
        </div>
      </div>
      <div className="mt-2 text-xs opacity-80">
        <div>Model: {data.model || 'GPT-4'}</div>
        <div>Task: {data.task || 'Analysis'}</div>
      </div>
    </div>
  );
};

const DelayNode = ({ data, isConnectable }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-gradient-to-r from-gray-500 to-gray-600 border-2 border-gray-400 text-white min-w-[200px]">
      <div className="flex items-center">
        <div className="ml-2">
          <div className="text-lg font-bold">⏱️ Delay</div>
          <div className="text-sm opacity-80">{data.duration || 1000}ms pause</div>
          <div className="text-xs opacity-60">Wait before next step</div>
        </div>
      </div>
    </div>
  );
};

const StartNode = ({ data, isConnectable }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-gradient-to-r from-green-500 to-green-600 border-2 border-green-400 text-white min-w-[150px]">
      <div className="flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-bold">🚀 Start</div>
          <div className="text-xs opacity-80">Workflow begins here</div>
        </div>
      </div>
    </div>
  );
};

const EndNode = ({ data, isConnectable }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-gradient-to-r from-red-500 to-red-600 border-2 border-red-400 text-white min-w-[150px]">
      <div className="flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-bold">🏁 End</div>
          <div className="text-xs opacity-80">Workflow completes</div>
        </div>
      </div>
    </div>
  );
};

// Node type mapping
const nodeTypes = {
  apiCall: ApiCallNode,
  decision: DecisionNode,
  dataTransform: DataTransformNode,
  aiBlock: AINode,
  delay: DelayNode,
  start: StartNode,
  end: EndNode,
};

// Initial nodes and edges
const initialNodes = [
  {
    id: 'start',
    type: 'start',
    position: { x: 250, y: 50 },
    data: { label: 'Start' },
  },
];

const initialEdges = [];

const VisualWorkflowBuilder = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionLog, setExecutionLog] = useState([]);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [savedWorkflows, setSavedWorkflows] = useState([]);

  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // Load saved workflows on mount
  useEffect(() => {
    const saved = localStorage.getItem('visualWorkflows');
    if (saved) {
      setSavedWorkflows(JSON.parse(saved));
    }
  }, []);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, markerEnd: { type: MarkerType.ArrowClosed } }, eds)),
    [setEdges],
  );

  const addNode = useCallback((type, position = null) => {
    const id = `${type}-${Date.now()}`;
    const newPosition = position || {
      x: Math.random() * 400 + 100,
      y: Math.random() * 400 + 200
    };

    const nodeData = {
      apiCall: { method: 'GET', url: '', description: 'API request block' },
      decision: { condition: 'response.status === 200', description: 'Conditional branching' },
      dataTransform: { operation: 'JSON.parse', inputFormat: 'String', outputFormat: 'JSON' },
      aiBlock: { aiType: 'Text Analysis', model: 'GPT-4', task: 'Analyze response' },
      delay: { duration: 1000, description: 'Wait before next step' },
      end: { description: 'Workflow completion' }
    };

    const newNode = {
      id,
      type,
      position: newPosition,
      data: { label: type, ...nodeData[type] },
    };

    setNodes((nds) => nds.concat(newNode));
  }, [setNodes]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');

      if (typeof type === 'undefined' || !type || !reactFlowInstance) {
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      addNode(type, position);
    },
    [reactFlowInstance, addNode],
  );

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const executeWorkflow = async () => {
    setIsExecuting(true);
    setExecutionLog([]);

    // Simulate workflow execution
    const log = [];

    try {
      log.push({ time: new Date().toLocaleTimeString(), message: '🚀 Starting workflow execution...', type: 'info' });

      // Find start node and traverse the workflow
      const startNode = nodes.find(n => n.type === 'start');
      if (!startNode) {
        throw new Error('No start node found');
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
      log.push({ time: new Date().toLocaleTimeString(), message: '✅ Workflow initialized', type: 'success' });

      // Simulate execution of each connected node
      const executedNodes = new Set();
      const executeNode = async (nodeId, depth = 0) => {
        if (executedNodes.has(nodeId) || depth > 10) return;

        const node = nodes.find(n => n.id === nodeId);
        if (!node) return;

        executedNodes.add(nodeId);

        await new Promise(resolve => setTimeout(resolve, 800));

        switch (node.type) {
          case 'apiCall':
            log.push({
              time: new Date().toLocaleTimeString(),
              message: `🌐 Executing API call: ${node.data.method} ${node.data.url || 'endpoint'}`,
              type: 'info'
            });
            break;
          case 'decision':
            log.push({
              time: new Date().toLocaleTimeString(),
              message: `🤔 Evaluating condition: ${node.data.condition}`,
              type: 'info'
            });
            break;
          case 'dataTransform':
            log.push({
              time: new Date().toLocaleTimeString(),
              message: `🔄 Transforming data: ${node.data.operation}`,
              type: 'info'
            });
            break;
          case 'aiBlock':
            log.push({
              time: new Date().toLocaleTimeString(),
              message: `🤖 Running AI task: ${node.data.task}`,
              type: 'info'
            });
            break;
          case 'delay':
            log.push({
              time: new Date().toLocaleTimeString(),
              message: `⏱️ Waiting ${node.data.duration}ms...`,
              type: 'info'
            });
            break;
        }

        setExecutionLog([...log]);

        // Find and execute connected nodes
        const outgoingEdges = edges.filter(e => e.source === nodeId);
        for (const edge of outgoingEdges) {
          await executeNode(edge.target, depth + 1);
        }
      };

      await executeNode(startNode.id);

      log.push({
        time: new Date().toLocaleTimeString(),
        message: '🏁 Workflow execution completed successfully!',
        type: 'success'
      });

    } catch (error) {
      log.push({
        time: new Date().toLocaleTimeString(),
        message: `❌ Execution failed: ${error.message}`,
        type: 'error'
      });
    }

    setExecutionLog(log);
    setIsExecuting(false);
  };

  const saveWorkflow = () => {
    const workflow = {
      id: Date.now(),
      name: workflowName,
      nodes,
      edges,
      createdAt: new Date().toISOString(),
    };

    const updated = [...savedWorkflows, workflow];
    setSavedWorkflows(updated);
    localStorage.setItem('visualWorkflows', JSON.stringify(updated));

    alert('Workflow saved successfully!');
  };

  const loadWorkflow = (workflow) => {
    setNodes(workflow.nodes);
    setEdges(workflow.edges);
    setWorkflowName(workflow.name);
  };

  const clearWorkflow = () => {
    setNodes([{
      id: 'start',
      type: 'start',
      position: { x: 250, y: 50 },
      data: { label: 'Start' },
    }]);
    setEdges([]);
    setWorkflowName('New Workflow');
  };

  return (
    <div className="h-screen bg-gray-900 text-white">
      <div className="h-full flex">
        {/* Sidebar */}
        <div className="w-80 bg-gray-800 p-4 border-r border-gray-700 overflow-y-auto">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white mb-4">🔄 Visual Workflow Builder</h2>
            <p className="text-sm text-gray-400 mb-4">
              Create no-code API workflows with drag-and-drop blocks. The Postman Flows killer!
            </p>

            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white mb-4"
              placeholder="Workflow name"
            />

            <div className="flex gap-2 mb-4">
              <button
                onClick={saveWorkflow}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
              >
                💾 Save
              </button>
              <button
                onClick={clearWorkflow}
                className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
              >
                🗑️ Clear
              </button>
            </div>
          </div>

          {/* Block Palette */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3">📦 Building Blocks</h3>
            <div className="grid grid-cols-1 gap-2">
              {[
                { type: 'apiCall', icon: '🌐', name: 'API Call', desc: 'Make HTTP requests' },
                { type: 'decision', icon: '🤔', name: 'Decision', desc: 'Conditional logic' },
                { type: 'dataTransform', icon: '🔄', name: 'Transform', desc: 'Process data' },
                { type: 'aiBlock', icon: '🤖', name: 'AI Block', desc: 'AI-powered tasks' },
                { type: 'delay', icon: '⏱️', name: 'Delay', desc: 'Wait/pause' },
                { type: 'end', icon: '🏁', name: 'End', desc: 'Workflow end' },
              ].map(({ type, icon, name, desc }) => (
                <div
                  key={type}
                  className="p-3 bg-gray-700 hover:bg-gray-600 rounded cursor-move border border-gray-600 transition-colors"
                  draggable
                  onDragStart={(event) => onDragStart(event, type)}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{icon}</span>
                    <div>
                      <div className="font-medium text-white">{name}</div>
                      <div className="text-xs text-gray-400">{desc}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Saved Workflows */}
          {savedWorkflows.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3">💾 Saved Workflows</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {savedWorkflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="p-2 bg-gray-700 rounded cursor-pointer hover:bg-gray-600 transition-colors"
                    onClick={() => loadWorkflow(workflow)}
                  >
                    <div className="font-medium text-white">{workflow.name}</div>
                    <div className="text-xs text-gray-400">
                      {new Date(workflow.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Execution Controls */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3">⚡ Execution</h3>
            <button
              onClick={executeWorkflow}
              disabled={isExecuting}
              className={`w-full px-4 py-2 rounded font-medium transition-colors ${
                isExecuting
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {isExecuting ? '⏳ Executing...' : '▶️ Run Workflow'}
            </button>
          </div>

          {/* Execution Log */}
          {executionLog.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">📜 Execution Log</h3>
              <div className="bg-gray-900 rounded p-3 max-h-60 overflow-y-auto">
                {executionLog.map((entry, index) => (
                  <div key={index} className="text-sm mb-2">
                    <span className="text-gray-400 text-xs">{entry.time}</span>
                    <div className={`${
                      entry.type === 'error' ? 'text-red-400' :
                      entry.type === 'success' ? 'text-green-400' :
                      'text-blue-400'
                    }`}>
                      {entry.message}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Main Canvas */}
        <div className="flex-1 relative">
          <div className="w-full h-full" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={nodeTypes}
              fitView
              className="bg-gray-900"
              onNodeClick={(_, node) => setSelectedNode(node)}
            >
              <Controls className="bg-gray-800 border-gray-600" />
              <MiniMap
                className="bg-gray-800 border-gray-600"
                nodeStrokeWidth={3}
                nodeColor={(node) => {
                  switch (node.type) {
                    case 'start': return '#10b981';
                    case 'end': return '#ef4444';
                    case 'apiCall': return '#3b82f6';
                    case 'decision': return '#f59e0b';
                    case 'dataTransform': return '#8b5cf6';
                    case 'aiBlock': return '#6366f1';
                    default: return '#6b7280';
                  }
                }}
              />
              <Background color="#374151" gap={16} />

              <Panel position="top-right">
                <div className="bg-gray-800 p-3 rounded border border-gray-600">
                  <div className="text-sm text-gray-300">
                    <div>Nodes: {nodes.length}</div>
                    <div>Connections: {edges.length}</div>
                    <div className="mt-1 text-xs text-gray-400">
                      Drag blocks from sidebar to canvas
                    </div>
                  </div>
                </div>
              </Panel>
            </ReactFlow>
          </div>
        </div>
      </div>

      {/* Node Configuration Modal */}
      {selectedNode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-white mb-4">
              Configure {selectedNode.type} Node
            </h3>

            {selectedNode.type === 'apiCall' && (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-300 mb-1">Method</label>
                  <select
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                    defaultValue={selectedNode.data.method}
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">URL</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                    placeholder="https://api.example.com/endpoint"
                    defaultValue={selectedNode.data.url}
                  />
                </div>
              </div>
            )}

            {selectedNode.type === 'decision' && (
              <div>
                <label className="block text-sm text-gray-300 mb-1">Condition</label>
                <textarea
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  rows="3"
                  placeholder="response.status === 200 && response.data.success"
                  defaultValue={selectedNode.data.condition}
                />
              </div>
            )}

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setSelectedNode(null)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => setSelectedNode(null)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualWorkflowBuilder;