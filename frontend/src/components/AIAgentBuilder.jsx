import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Brain,
  Bot,
  Sparkles,
  Play,
  Plus,
  Settings,
  Code,
  Workflow,
  Shield,
  Zap,
  Database,
  Globe,
  Bell,
  Calendar,
  Link,
  GitBranch,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader,
  Rocket,
  TestTube,
  Copy,
  Trash2,
  Edit,
  Eye,
  Download,
  Upload,
  ArrowRight,
  ChevronRight,
  Terminal,
  FileText,
  BarChart,
  Lock,
  Cpu
} from 'lucide-react';

const AIAgentBuilder = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [agentTypes, setAgentTypes] = useState([]);
  const [activeTab, setActiveTab] = useState('templates');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Create agent form
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    type: 'api_tester',
    capabilities: [],
    model: 'gpt-4',
    temperature: 0.7,
    custom_prompt: '',
    auto_deploy: false
  });

  // Test input
  const [testInput, setTestInput] = useState('{}');

  useEffect(() => {
    loadTemplates();
    loadAgents();
    loadCapabilities();
    loadAgentTypes();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await axios.get(
        getApiUrl('/api/ai-agents/templates'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTemplates(response.data.templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const response = await axios.get(
        getApiUrl('/api/ai-agents/list'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAgents(response.data.agents);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const loadCapabilities = async () => {
    try {
      const response = await axios.get(
        getApiUrl('/api/ai-agents/capabilities/list'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCapabilities(response.data.capabilities);
    } catch (error) {
      console.error('Failed to load capabilities:', error);
    }
  };

  const loadAgentTypes = async () => {
    try {
      const response = await axios.get(
        getApiUrl('/api/ai-agents/types/list'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAgentTypes(response.data.types);
    } catch (error) {
      console.error('Failed to load agent types:', error);
    }
  };

  const createFromTemplate = async (templateName) => {
    setLoading(true);
    try {
      const response = await axios.post(
        getApiUrl('/api/ai-agents/create-from-template'),
        {
          template_name: templateName,
          auto_deploy: true
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      await loadAgents();
      setActiveTab('my-agents');
      setSelectedAgent(response.data.agent);
    } catch (error) {
      console.error('Failed to create agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const createCustomAgent = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        getApiUrl('/api/ai-agents/create'),
        newAgent,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      await loadAgents();
      setShowCreateModal(false);
      setSelectedAgent(response.data.agent);
      setActiveTab('my-agents');
      
      // Reset form
      setNewAgent({
        name: '',
        description: '',
        type: 'api_tester',
        capabilities: [],
        model: 'gpt-4',
        temperature: 0.7,
        custom_prompt: '',
        auto_deploy: false
      });
    } catch (error) {
      console.error('Failed to create agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const testAgent = async (agentId) => {
    setLoading(true);
    setTestResult(null);
    try {
      const response = await axios.post(
        getApiUrl(`/api/ai-agents/${agentId}/test`),
        {
          test_input: JSON.parse(testInput)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTestResult(response.data);
    } catch (error) {
      setTestResult({
        success: false,
        error: error.response?.data?.detail || error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const deployAgent = async (agentId) => {
    setLoading(true);
    try {
      const response = await axios.post(
        getApiUrl(`/api/ai-agents/${agentId}/deploy`),
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      await loadAgents();
      setSelectedAgent(response.data);
    } catch (error) {
      console.error('Failed to deploy agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteAgent = async (agentId) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    setLoading(true);
    try {
      await axios.delete(
        getApiUrl(`/api/ai-agents/${agentId}`),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      await loadAgents();
      setSelectedAgent(null);
    } catch (error) {
      console.error('Failed to delete agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIconForType = (type) => {
    const icons = {
      api_tester: TestTube,
      data_processor: Database,
      workflow_automator: Workflow,
      security_scanner: Shield,
      performance_optimizer: Zap,
      documentation_generator: FileText,
      mock_data_generator: Copy,
      integration_builder: Link,
      custom: Bot
    };
    return icons[type] || Bot;
  };

  const getIconForCapability = (capability) => {
    const icons = {
      http_requests: Globe,
      data_transformation: GitBranch,
      file_operations: FileText,
      database_queries: Database,
      code_generation: Code,
      natural_language: Brain,
      scheduling: Calendar,
      notifications: Bell,
      chain_apis: Link,
      conditional_logic: GitBranch
    };
    return icons[capability] || Cpu;
  };

  return (
    <div className="space-y-6">
      {/* Header - KILLER FEATURE ANNOUNCEMENT */}
      <div className="bg-gradient-to-r from-purple-900 to-pink-900 rounded-lg p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-pink-600/20 animate-pulse"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-white/10 rounded-lg backdrop-blur">
                <Brain className="w-10 h-10 text-white" />
              </div>
              <div>
                <h2 className="text-3xl font-bold text-white flex items-center gap-2">
                  AI Agent Builder
                  <span className="px-2 py-1 bg-red-500 text-white text-xs rounded-full animate-pulse">
                    POSTMAN KILLER
                  </span>
                </h2>
                <p className="text-purple-200">Build intelligent agents that automate API workflows - No code required!</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-white text-purple-900 rounded-lg font-bold hover:bg-purple-100 transition flex items-center space-x-2 shadow-xl"
            >
              <Plus className="w-5 h-5" />
              <span>Create Agent</span>
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 mt-6">
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{agents.length}</div>
              <div className="text-sm text-purple-200">Active Agents</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{templates.length}</div>
              <div className="text-sm text-purple-200">Templates</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-2xl font-bold text-white">∞</div>
              <div className="text-sm text-purple-200">Automations</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-2xl font-bold text-white">100%</div>
              <div className="text-sm text-purple-200">No Code</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-gray-800 rounded-lg p-1">
        <div className="flex space-x-1">
          {['templates', 'my-agents', 'marketplace'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition ${
                activeTab === tab
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {tab === 'templates' && 'Agent Templates'}
              {tab === 'my-agents' && 'My Agents'}
              {tab === 'marketplace' && 'Marketplace'}
            </button>
          ))}
        </div>
      </div>

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="grid grid-cols-2 gap-6">
          {templates.map((template) => {
            const Icon = getIconForType(template.type);
            return (
              <div
                key={template.name}
                className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition border border-gray-700 hover:border-purple-500"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-3 bg-purple-600/20 rounded-lg">
                      <Icon className="w-8 h-8 text-purple-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">{template.name}</h3>
                      <p className="text-sm text-gray-400">{template.type}</p>
                    </div>
                  </div>
                </div>
                
                <p className="text-gray-300 mb-4">{template.description}</p>
                
                <div className="flex flex-wrap gap-2 mb-4">
                  {template.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="px-2 py-1 bg-gray-700 text-gray-300 rounded-full text-xs"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">
                    {template.workflow_steps} workflow steps
                  </span>
                  <button
                    onClick={() => createFromTemplate(template.name)}
                    disabled={loading}
                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition flex items-center space-x-2"
                  >
                    <Rocket className="w-4 h-4" />
                    <span>Use Template</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* My Agents Tab */}
      {activeTab === 'my-agents' && (
        <div className="space-y-4">
          {agents.length === 0 ? (
            <div className="bg-gray-800 rounded-lg p-12 text-center">
              <Bot className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No Agents Yet</h3>
              <p className="text-gray-400 mb-6">Create your first AI agent from a template or build a custom one</p>
              <button
                onClick={() => setActiveTab('templates')}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                Browse Templates
              </button>
            </div>
          ) : (
            agents.map((agent) => {
              const Icon = getIconForType(agent.type);
              return (
                <div
                  key={agent.id}
                  className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-purple-600/20 rounded-lg">
                        <Icon className="w-8 h-8 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white">{agent.name}</h3>
                        <p className="text-gray-400">{agent.description}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <span className="text-sm text-gray-500">
                            Type: {agent.type}
                          </span>
                          <span className="text-sm text-gray-500">
                            Created: {new Date(agent.created_at).toLocaleDateString()}
                          </span>
                          {agent.deployed && (
                            <span className="px-2 py-1 bg-green-600/20 text-green-400 rounded-full text-xs">
                              Deployed
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setSelectedAgent(agent)}
                        className="p-2 text-gray-400 hover:text-white transition"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => testAgent(agent.id)}
                        className="p-2 text-blue-400 hover:text-blue-300 transition"
                      >
                        <TestTube className="w-5 h-5" />
                      </button>
                      {!agent.deployed && (
                        <button
                          onClick={() => deployAgent(agent.id)}
                          className="p-2 text-green-400 hover:text-green-300 transition"
                        >
                          <Rocket className="w-5 h-5" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteAgent(agent.id)}
                        className="p-2 text-red-400 hover:text-red-300 transition"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                  
                  {selectedAgent?.id === agent.id && (
                    <div className="mt-6 pt-6 border-t border-gray-700">
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                          <h4 className="text-sm font-semibold text-gray-400 mb-2">Agent Details</h4>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-500">Model:</span>
                              <span className="text-sm text-white">{agent.model || 'gpt-4'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-500">Workflow Steps:</span>
                              <span className="text-sm text-white">{agent.workflow_steps}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-500">Test Cases:</span>
                              <span className="text-sm text-white">{agent.test_cases}</span>
                            </div>
                          </div>
                        </div>
                        
                        {agent.deployed && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-400 mb-2">API Endpoint</h4>
                            <div className="bg-gray-900 rounded-lg p-3">
                              <code className="text-xs text-green-400 break-all">
                                {agent.endpoint}
                              </code>
                              {agent.api_key && (
                                <div className="mt-2">
                                  <span className="text-xs text-gray-500">API Key:</span>
                                  <code className="text-xs text-yellow-400 ml-2">
                                    {agent.api_key.substring(0, 8)}...
                                  </code>
                                  <button
                                    onClick={() => navigator.clipboard.writeText(agent.api_key)}
                                    className="ml-2 text-gray-400 hover:text-white"
                                  >
                                    <Copy className="w-3 h-3 inline" />
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Test Interface */}
                      <div className="mt-6">
                        <h4 className="text-sm font-semibold text-gray-400 mb-2">Test Agent</h4>
                        <div className="flex space-x-2">
                          <textarea
                            value={testInput}
                            onChange={(e) => setTestInput(e.target.value)}
                            className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono text-sm"
                            placeholder='{"query": "test input"}'
                            rows="3"
                          />
                          <button
                            onClick={() => testAgent(agent.id)}
                            disabled={loading}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                          >
                            {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Marketplace Tab */}
      {activeTab === 'marketplace' && (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-white mb-2">Agent Marketplace Coming Soon!</h3>
          <p className="text-gray-400 max-w-md mx-auto">
            Share and discover AI agents created by the community. 
            Get paid when others use your agents!
          </p>
        </div>
      )}

      {/* Test Results */}
      {testResult && (
        <div className={`rounded-lg p-6 ${
          testResult.success 
            ? 'bg-green-900/20 border border-green-500/50' 
            : 'bg-red-900/20 border border-red-500/50'
        }`}>
          <div className="flex items-start space-x-3">
            {testResult.success ? (
              <CheckCircle className="w-6 h-6 text-green-400 mt-0.5" />
            ) : (
              <XCircle className="w-6 h-6 text-red-400 mt-0.5" />
            )}
            <div className="flex-1">
              <h3 className={`text-lg font-semibold ${
                testResult.success ? 'text-green-400' : 'text-red-400'
              }`}>
                {testResult.success ? 'Test Successful' : 'Test Failed'}
              </h3>
              {testResult.output && (
                <pre className="mt-2 p-3 bg-gray-900 rounded text-xs text-gray-300 overflow-x-auto">
                  {JSON.stringify(testResult.output, null, 2)}
                </pre>
              )}
              {testResult.error && (
                <p className="mt-2 text-sm text-red-400">{testResult.error}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create Agent Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-2xl font-bold text-white mb-6">Create Custom Agent</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Agent Name</label>
                <input
                  type="text"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="My Custom Agent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Description</label>
                <textarea
                  value={newAgent.description}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="What does this agent do?"
                  rows="3"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Agent Type</label>
                <select
                  value={newAgent.type}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, type: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                >
                  {agentTypes.map(type => (
                    <option key={type.name} value={type.name}>
                      {type.name} - {type.description}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Capabilities</label>
                <div className="grid grid-cols-2 gap-2">
                  {capabilities.map(cap => (
                    <label key={cap.name} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={newAgent.capabilities.includes(cap.name)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewAgent(prev => ({
                              ...prev,
                              capabilities: [...prev.capabilities, cap.name]
                            }));
                          } else {
                            setNewAgent(prev => ({
                              ...prev,
                              capabilities: prev.capabilities.filter(c => c !== cap.name)
                            }));
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm text-gray-300">{cap.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Model</label>
                  <select
                    value={newAgent.model}
                    onChange={(e) => setNewAgent(prev => ({ ...prev, model: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    <option value="claude-3-opus">Claude 3 Opus</option>
                    <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Temperature</label>
                  <input
                    type="number"
                    value={newAgent.temperature}
                    onChange={(e) => setNewAgent(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                    min="0"
                    max="1"
                    step="0.1"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Custom System Prompt (Optional)</label>
                <textarea
                  value={newAgent.custom_prompt}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, custom_prompt: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white font-mono text-sm"
                  placeholder="Override the default system prompt..."
                  rows="4"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={newAgent.auto_deploy}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, auto_deploy: e.target.checked }))}
                  className="rounded"
                />
                <label className="text-sm text-gray-300">Auto-deploy agent after creation</label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition"
              >
                Cancel
              </button>
              <button
                onClick={createCustomAgent}
                disabled={loading || !newAgent.name || newAgent.capabilities.length === 0}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition disabled:opacity-50"
              >
                {loading ? <Loader className="w-4 h-4 animate-spin" /> : 'Create Agent'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAgentBuilder;