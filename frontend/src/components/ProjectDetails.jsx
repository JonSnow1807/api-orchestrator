import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import AIAnalysisDisplay from './AIAnalysisDisplay';
import MockServerManager from './MockServerManager';
import { 
  ArrowLeft,
  Folder,
  PlayCircle,
  Download,
  Activity,
  FileCode,
  TestTube,
  Brain,
  Server,
  CheckCircle,
  XCircle,
  Clock,
  MoreVertical,
  Loader,
  Terminal,
  Shield,
  TrendingUp
} from 'lucide-react';

const ProjectDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [orchestrating, setOrchestrating] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);
  const [messages, setMessages] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [wsConnected, setWsConnected] = useState(false);
  const [orchestrationProgress, setOrchestrationProgress] = useState({
    discovery: { status: 'pending', count: 0 },
    spec: { status: 'pending', count: 0 },
    test: { status: 'pending', count: 0 },
    ai: { status: 'pending', count: 0 },
    mock: { status: 'pending', count: 0 }
  });

  useEffect(() => {
    fetchProject();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchProject = async () => {
    try {
      const response = await axios.get(`/api/projects/${id}`);
      setProject(response.data);
      
      // Check if there's an active task
      if (response.data.tasks && response.data.tasks.length > 0) {
        const latestTask = response.data.tasks[response.data.tasks.length - 1];
        if (latestTask.status === 'running') {
          setOrchestrating(true);
          setCurrentTask(latestTask);
        }
      }
    } catch (error) {
      console.error('Failed to fetch project:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        setWsConnected(true);
        addMessage('Connected to orchestration server', 'success');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
      
      ws.onclose = () => {
        setWsConnected(false);
        addMessage('Disconnected from server', 'error');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
            connectWebSocket();
          }
        }, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('Connection error', 'error');
      };
      
      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      setWsConnected(false);
    }
  };

  const handleWebSocketMessage = (data) => {
    // Only process messages for this project
    if (data.project_id && data.project_id !== parseInt(id)) {
      return;
    }

    switch(data.type) {
      case 'progress':
        addMessage(data.message, 'info');
        updateAgentStatus(data.stage, 'active');
        break;
        
      case 'discovery_complete':
        setOrchestrationProgress(prev => ({
          ...prev,
          discovery: { status: 'completed', count: data.apis_found }
        }));
        addMessage(`Discovery complete: ${data.apis_found} APIs found`, 'discovery');
        break;
        
      case 'spec_complete':
        setOrchestrationProgress(prev => ({
          ...prev,
          spec: { status: 'completed', count: data.paths }
        }));
        addMessage(`Spec generation complete: ${data.paths} paths`, 'spec');
        break;
        
      case 'tests_complete':
        setOrchestrationProgress(prev => ({
          ...prev,
          test: { status: 'completed', count: data.tests_generated }
        }));
        addMessage(`Test generation complete: ${data.tests_generated} tests`, 'test');
        break;
        
      case 'ai_complete':
        setOrchestrationProgress(prev => ({
          ...prev,
          ai: { status: 'completed', count: 1 }
        }));
        addMessage('AI analysis complete', 'ai');
        break;
        
      case 'mock_complete':
        setOrchestrationProgress(prev => ({
          ...prev,
          mock: { status: 'completed', count: 1 }
        }));
        addMessage('Mock server ready', 'mock');
        break;
        
      case 'orchestration_complete':
        setOrchestrating(false);
        setCurrentTask(null);
        addMessage('✨ Orchestration complete!', 'success');
        fetchProject(); // Refresh project data
        break;
        
      case 'error':
        addMessage(`Error: ${data.error}`, 'error');
        break;
    }
  };

  const updateAgentStatus = (stage, status) => {
    const agentMap = {
      'discovery': 'discovery',
      'spec_generation': 'spec',
      'test_generation': 'test',
      'ai_analysis': 'ai',
      'mock_server': 'mock'
    };
    
    const agent = agentMap[stage];
    if (agent) {
      setOrchestrationProgress(prev => ({
        ...prev,
        [agent]: { ...prev[agent], status: 'active' }
      }));
    }
  };

  const addMessage = (text, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev, { text, type, timestamp }]);
  };

  const startOrchestration = async () => {
    try {
      setOrchestrating(true);
      setMessages([]);
      setOrchestrationProgress({
        discovery: { status: 'pending', count: 0 },
        spec: { status: 'pending', count: 0 },
        test: { status: 'pending', count: 0 },
        ai: { status: 'pending', count: 0 },
        mock: { status: 'pending', count: 0 }
      });
      
      const response = await axios.post(`/api/projects/${id}/orchestrate`);
      setCurrentTask(response.data);
      addMessage(`Orchestration started: Task ${response.data.task_id}`, 'info');
    } catch (error) {
      addMessage(`Failed to start orchestration: ${error.message}`, 'error');
      setOrchestrating(false);
    }
  };

  const downloadArtifact = async (format) => {
    try {
      const response = await axios.get(`/api/export/${currentTask?.task_id || project.tasks[0]?.task_id}?format=${format}`, {
        responseType: format === 'zip' ? 'blob' : 'json'
      });
      
      if (format === 'zip') {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${project.name}-artifacts.zip`);
        document.body.appendChild(link);
        link.click();
      } else {
        const dataStr = JSON.stringify(response.data, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        const link = document.createElement('a');
        link.setAttribute('href', dataUri);
        link.setAttribute('download', `${project.name}-${format}.json`);
        link.click();
      }
    } catch (error) {
      addMessage(`Download failed: ${error.message}`, 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <Loader className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Project Not Found</h2>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const agents = [
    { 
      id: 'discovery', 
      name: 'Discovery Agent', 
      icon: FileCode,
      description: 'Scanning for API endpoints',
      status: orchestrationProgress.discovery.status,
      count: orchestrationProgress.discovery.count
    },
    { 
      id: 'spec', 
      name: 'Spec Generator', 
      icon: FileCode,
      description: 'Creating OpenAPI specs',
      status: orchestrationProgress.spec.status,
      count: orchestrationProgress.spec.count
    },
    { 
      id: 'test', 
      name: 'Test Generator', 
      icon: TestTube,
      description: 'Generating test suites',
      status: orchestrationProgress.test.status,
      count: orchestrationProgress.test.count
    },
    { 
      id: 'ai', 
      name: 'AI Analyzer', 
      icon: Brain,
      description: 'AI-powered insights',
      status: orchestrationProgress.ai.status,
      count: orchestrationProgress.ai.count
    },
    { 
      id: 'mock', 
      name: 'Mock Server', 
      icon: Server,
      description: 'Creating mock server',
      status: orchestrationProgress.mock.status,
      count: orchestrationProgress.mock.count
    }
  ];

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center space-x-2 text-gray-400 hover:text-white transition"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Dashboard</span>
              </button>
              
              <div className="flex items-center space-x-3">
                <Folder className="w-6 h-6 text-purple-500" />
                <h1 className="text-xl font-semibold text-white">{project.name}</h1>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* WebSocket Status */}
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                wsConnected 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                  : 'bg-red-500/20 text-red-400 border border-red-500/50'
              }`}>
                <Activity className="w-4 h-4" />
                <span className="text-sm">{wsConnected ? 'Connected' : 'Disconnected'}</span>
              </div>

              {/* Actions */}
              <button
                onClick={startOrchestration}
                disabled={orchestrating}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {orchestrating ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    <span>Orchestrating...</span>
                  </>
                ) : (
                  <>
                    <PlayCircle className="w-5 h-5" />
                    <span>Start Orchestration</span>
                  </>
                )}
              </button>

              <button className="p-2 text-gray-400 hover:text-white">
                <MoreVertical className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="border-b border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'agents', 'ai-analysis', 'mock-server', 'console', 'artifacts'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize transition ${
                  activeTab === tab
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Project Info */}
            <div className="lg:col-span-2 bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Project Information</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-400">Description</label>
                  <p className="text-white">{project.description || 'No description provided'}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-400">Source Type</label>
                    <p className="text-white capitalize">{project.source_type || 'Not specified'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Created</label>
                    <p className="text-white">{new Date(project.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm text-gray-400">Source Path</label>
                  <p className="text-white font-mono text-sm bg-gray-900 p-2 rounded">
                    {project.source_path || 'Not configured'}
                  </p>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Statistics</h2>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">APIs Found</span>
                  <span className="text-2xl font-bold text-purple-400">
                    {project.api_count || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Tests Generated</span>
                  <span className="text-2xl font-bold text-blue-400">
                    {project.test_count || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Security Score</span>
                  <span className="text-2xl font-bold text-green-400">
                    {project.security_score || 'N/A'}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Tasks Run</span>
                  <span className="text-2xl font-bold text-yellow-400">
                    {project.task_count || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => {
              const Icon = agent.icon;
              const isActive = agent.status === 'active';
              const isCompleted = agent.status === 'completed';
              
              return (
                <div
                  key={agent.id}
                  className={`bg-gray-800/50 backdrop-blur rounded-xl border p-6 transition ${
                    isActive 
                      ? 'border-purple-500 shadow-lg shadow-purple-500/20' 
                      : isCompleted
                      ? 'border-green-500/50'
                      : 'border-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        isActive 
                          ? 'bg-purple-600/20' 
                          : isCompleted
                          ? 'bg-green-600/20'
                          : 'bg-gray-700'
                      }`}>
                        <Icon className={`w-6 h-6 ${
                          isActive 
                            ? 'text-purple-400' 
                            : isCompleted
                            ? 'text-green-400'
                            : 'text-gray-400'
                        }`} />
                      </div>
                      <div>
                        <h3 className="text-white font-medium">{agent.name}</h3>
                        <p className="text-xs text-gray-400">{agent.description}</p>
                      </div>
                    </div>
                    
                    {isActive && <Loader className="w-5 h-5 text-purple-400 animate-spin" />}
                    {isCompleted && <CheckCircle className="w-5 h-5 text-green-400" />}
                  </div>
                  
                  {agent.count > 0 && (
                    <div className="text-center py-2 px-3 bg-gray-900 rounded-lg">
                      <span className="text-2xl font-bold text-white">{agent.count}</span>
                      <span className="text-xs text-gray-400 ml-2">
                        {agent.id === 'discovery' && 'endpoints'}
                        {agent.id === 'spec' && 'paths'}
                        {agent.id === 'test' && 'tests'}
                        {agent.id === 'ai' && 'insights'}
                        {agent.id === 'mock' && 'server'}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {activeTab === 'console' && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center">
                <Terminal className="w-5 h-5 mr-2" />
                Live Console
              </h2>
              <button
                onClick={() => setMessages([])}
                className="text-sm text-gray-400 hover:text-white transition"
              >
                Clear
              </button>
            </div>
            
            <div className="bg-gray-900 rounded-lg h-96 overflow-y-auto p-4 font-mono text-sm">
              {messages.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                  No messages yet. Start orchestration to see live updates.
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`mb-2 ${
                      msg.type === 'error' ? 'text-red-400' :
                      msg.type === 'success' ? 'text-green-400' :
                      msg.type === 'discovery' ? 'text-purple-400' :
                      msg.type === 'spec' ? 'text-blue-400' :
                      msg.type === 'test' ? 'text-yellow-400' :
                      msg.type === 'ai' ? 'text-cyan-400' :
                      msg.type === 'mock' ? 'text-orange-400' :
                      'text-gray-300'
                    }`}
                  >
                    <span className="text-gray-500">[{msg.timestamp}]</span> {msg.text}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {activeTab === 'ai-analysis' && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center">
              <Brain className="w-6 h-6 mr-2 text-purple-400" />
              AI Analysis Results
            </h2>
            <AIAnalysisDisplay taskId={currentTask} />
          </div>
        )}

        {activeTab === 'mock-server' && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center">
              <Server className="w-6 h-6 mr-2 text-purple-400" />
              Mock Server Management
            </h2>
            <MockServerManager taskId={currentTask} />
          </div>
        )}

        {activeTab === 'artifacts' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Download Cards */}
            {currentTask || (project.tasks && project.tasks.length > 0) ? (
              <>
                <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
                  <FileCode className="w-8 h-8 text-blue-500 mb-4" />
                  <h3 className="text-white font-semibold mb-2">OpenAPI Specification</h3>
                  <p className="text-gray-400 text-sm mb-4">Complete API documentation in OpenAPI 3.0 format</p>
                  <button
                    onClick={() => downloadArtifact('json')}
                    className="w-full px-4 py-2 bg-blue-600/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-600/30 transition"
                  >
                    <Download className="w-4 h-4 inline mr-2" />
                    Download JSON
                  </button>
                </div>

                <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
                  <TestTube className="w-8 h-8 text-yellow-500 mb-4" />
                  <h3 className="text-white font-semibold mb-2">Test Suites</h3>
                  <p className="text-gray-400 text-sm mb-4">Comprehensive tests for all endpoints</p>
                  <button
                    onClick={() => downloadArtifact('postman')}
                    className="w-full px-4 py-2 bg-yellow-600/20 text-yellow-400 border border-yellow-500/50 rounded-lg hover:bg-yellow-600/30 transition"
                  >
                    <Download className="w-4 h-4 inline mr-2" />
                    Postman Collection
                  </button>
                </div>

                <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
                  <Server className="w-8 h-8 text-orange-500 mb-4" />
                  <h3 className="text-white font-semibold mb-2">Mock Server</h3>
                  <p className="text-gray-400 text-sm mb-4">Ready-to-run mock server with Docker</p>
                  <button
                    onClick={() => downloadArtifact('zip')}
                    className="w-full px-4 py-2 bg-orange-600/20 text-orange-400 border border-orange-500/50 rounded-lg hover:bg-orange-600/30 transition"
                  >
                    <Download className="w-4 h-4 inline mr-2" />
                    Download All
                  </button>
                </div>
              </>
            ) : (
              <div className="col-span-3 text-center py-12">
                <FileCode className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No artifacts yet</h3>
                <p className="text-gray-500">Run orchestration to generate artifacts</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectDetails;