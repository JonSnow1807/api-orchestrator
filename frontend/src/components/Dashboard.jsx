import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  LayoutDashboard, 
  FolderOpen, 
  PlayCircle, 
  Download,
  LogOut,
  User,
  Users,
  Zap,
  Shield,
  Clock,
  TrendingUp,
  Plus,
  Search,
  MoreVertical,
  BarChart3,
  History,
  Upload,
  FileArchive,
  FileCheck,
  Globe,
  Code2,
  Home,
  CreditCard,
  BookOpen,
  Building2,
  Brain,
  Keyboard,
  HelpCircle
} from 'lucide-react';
import Breadcrumbs from './Breadcrumbs';
import FontSizeControl from './FontSizeControl';
import OnboardingTour from './OnboardingTour';
import KeyboardShortcutsGuide from './KeyboardShortcutsGuide';
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts';
import TaskManager from './TaskManager';
import FileUpload from './FileUpload';
import ExportImport from './ExportImport';
import CodeEditor from './CodeEditor';
import OrchestrationHub from './OrchestrationHub';
import RealtimeMonitor from './RealtimeMonitor';
import AIAnalysis from './AIAnalysis';
import MockServerManager from './MockServerManager';
import APIRequestBuilder from './APIRequestBuilder';
import AIAssistant from './AIAssistant';
import APIDocumentation from './APIDocumentation';
import AIEmployee from './AIEmployee';
import RequestHistory from './RequestHistory';
import MonitoringDashboard from './MonitoringDashboard';
import CodeGenerator from './CodeGenerator/CodeGenerator';
import WorkspaceSwitcher from './WorkspaceSwitcherFixed';
import TeamManagement from './TeamManagement';
import AdvancedAnalytics from './AdvancedAnalytics';
import WebhookManager from './WebhookManager';
import LoadTesting from './LoadTesting';
import ContractTesting from './ContractTesting';
import StatusPages from './StatusPages';
import AIAgentBuilder from './AIAgentBuilder';
import NaturalLanguageTesting from './NaturalLanguageTesting';
import OfflineMode from './OfflineMode';
import ServiceVirtualization from './ServiceVirtualization';
import PrivacyAI from './PrivacyAI';
import EnhancedVariableManager from './EnhancedVariableManager';
import VisualWorkflowBuilder from './VisualWorkflowBuilder';
import ApiGovernance from './ApiGovernance';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('analytics');
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [showShortcutsGuide, setShowShortcutsGuide] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  
  // Initialize keyboard shortcuts
  useKeyboardShortcuts({
    '?': () => setShowShortcutsGuide(true),
    'escape': () => setShowShortcutsGuide(false)
  });

  useEffect(() => {
    fetchProjects();
    fetchStats();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get('/api/projects');
      setProjects(response.data.projects);
    } catch (error) {
      // Error fetching projects - handled silently
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/projects/stats/overview');
      setStats(response.data);
    } catch (error) {
      // Error fetching stats - handled silently
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleOrchestrate = async (projectId) => {
    try {
      const response = await axios.post(`/api/projects/${projectId}/orchestrate`);
      alert(`Orchestration started! Task ID: ${response.data.task_id}`);
    } catch (error) {
      alert('Failed to start orchestration');
    }
  };

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Onboarding Tour */}
      {showOnboarding && <OnboardingTour onComplete={() => setShowOnboarding(false)} />}
      
      {/* Keyboard Shortcuts Guide */}
      <KeyboardShortcutsGuide isOpen={showShortcutsGuide} onClose={() => setShowShortcutsGuide(false)} />
      
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700 flex-shrink-0" role="banner">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-6">
              <Link to="/" className="flex items-center space-x-2">
                <Zap className="w-8 h-8 text-purple-500" />
                <h1 className="text-2xl font-bold text-white">API Orchestrator</h1>
              </Link>
              <WorkspaceSwitcher onWorkspaceChange={setCurrentWorkspace} />
              <span className="px-3 py-1 bg-purple-600/20 text-purple-400 text-sm rounded-full border border-purple-500/30 whitespace-nowrap">
                {(user?.subscription_tier || 'Free').charAt(0).toUpperCase() + (user?.subscription_tier || 'free').slice(1)}
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link
                to="/"
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
              >
                <Home className="w-5 h-5" />
                <span>Home</span>
              </Link>
              <Link
                to="/dashboard"
                className="flex items-center space-x-2 px-4 py-2 text-purple-400 transition"
              >
                <LayoutDashboard className="w-5 h-5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/billing"
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
              >
                <CreditCard className="w-5 h-5" />
                <span>Billing</span>
              </Link>
              <Link
                to="/profile"
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
                aria-label="User Profile"
              >
                <User className="w-5 h-5" />
                <span>{user?.username || 'Profile'}</span>
              </Link>
              
              {/* Font Size Control */}
              <FontSizeControl />
              
              {/* Help Button */}
              <button
                onClick={() => setShowShortcutsGuide(true)}
                className="p-2 text-gray-400 hover:text-white transition"
                aria-label="Keyboard shortcuts"
                title="Press ? for keyboard shortcuts"
              >
                <Keyboard className="w-5 h-5" />
              </button>
              
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
                aria-label="Logout"
              >
                <LogOut className="w-5 h-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Breadcrumbs */}
      <Breadcrumbs />

      {/* Main Content Container with Scroll */}
      <div className="flex-1 overflow-auto" role="main">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8 relative z-10" role="region" aria-label="Dashboard Statistics">
          <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700" role="article" aria-label="Total Projects">
            <div className="flex items-center justify-between mb-4">
              <FolderOpen className="w-8 h-8 text-purple-500" aria-hidden="true" />
              <span className="text-2xl font-bold text-white" aria-label={`${stats?.total_projects || 0} projects`}>{stats?.total_projects || 0}</span>
            </div>
            <h3 className="text-gray-400 text-sm">Total Projects</h3>
          </div>

          <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <Zap className="w-8 h-8 text-blue-500" />
              <span className="text-2xl font-bold text-white">{stats?.total_apis || 0}</span>
            </div>
            <h3 className="text-gray-400 text-sm">APIs Discovered</h3>
          </div>

          <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <Shield className="w-8 h-8 text-green-500" />
              <span className="text-2xl font-bold text-white">
                {stats?.average_security_score ? `${Math.round(stats.average_security_score)}%` : 'N/A'}
              </span>
            </div>
            <h3 className="text-gray-400 text-sm">Security Score</h3>
          </div>

          <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <TrendingUp className="w-8 h-8 text-yellow-500" />
              <span className="text-2xl font-bold text-white">
                ${Math.round(stats?.money_saved || 0).toLocaleString()}
              </span>
            </div>
            <h3 className="text-gray-400 text-sm">Money Saved</h3>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
          <nav className="flex gap-1 bg-gray-800/50 backdrop-blur rounded-lg p-1 min-w-fit">
            <button
              onClick={() => setActiveTab('ai-employee')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'ai-employee'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Brain className="w-5 h-5" />
              <span>AI Employee</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-green-500 text-white text-xs rounded-full animate-pulse">100%</span>
            </button>
            <button
              onClick={() => setActiveTab('ai-agents')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'ai-agents'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Brain className="w-4 h-4" />
              <span>AI Agents</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-red-500 text-white text-xs rounded-full animate-pulse">NEW</span>
            </button>
            <button
              onClick={() => setActiveTab('orchestration')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'orchestration' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Orchestration</span>
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'analytics' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Analytics</span>
            </button>
            <button
              onClick={() => setActiveTab('projects')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'projects' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <FolderOpen className="w-4 h-4" />
              <span>Projects</span>
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'tasks' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <History className="w-4 h-4" />
              <span>Tasks</span>
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'upload' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>Upload</span>
            </button>
            <button
              onClick={() => setActiveTab('export')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'export' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <FileArchive className="w-4 h-4" />
              <span>Export/Import</span>
            </button>
            <button
              onClick={() => setActiveTab('api-tester')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'api-tester' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>API Tester</span>
            </button>
            <button
              onClick={() => setActiveTab('code-generator')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'code-generator' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Code2 className="w-4 h-4" />
              <span>Code Gen</span>
            </button>
            <button
              onClick={() => setActiveTab('documentation')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'documentation' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>API Docs</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'history' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>History</span>
            </button>
            <button
              onClick={() => setActiveTab('monitoring')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'monitoring' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Monitoring</span>
            </button>
            <button
              onClick={() => setActiveTab('load-testing')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'load-testing' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Load Testing</span>
            </button>
            <button
              onClick={() => setActiveTab('contract-testing')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'contract-testing' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <FileCheck className="w-4 h-4" />
              <span>Contracts</span>
            </button>
            <button
              onClick={() => setActiveTab('status-pages')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'status-pages' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Globe className="w-4 h-4" />
              <span>Status</span>
            </button>
            <button
              onClick={() => setActiveTab('team')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'team' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Team</span>
            </button>
            <button
              onClick={() => setActiveTab('webhooks')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'webhooks' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Webhooks</span>
            </button>
            
            {/* V5.0 POSTMAN KILLER Features */}
            <button
              onClick={() => setActiveTab('visual-workflows')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'visual-workflows'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Visual Workflows</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-red-500 text-white text-xs rounded-full animate-pulse">NEW</span>
            </button>
            <button
              onClick={() => setActiveTab('api-governance')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'api-governance'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>API Governance</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-red-500 text-white text-xs rounded-full animate-pulse">NEW</span>
            </button>
            <button
              onClick={() => setActiveTab('enhanced-variables')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'enhanced-variables'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Code2 className="w-4 h-4" />
              <span>Enhanced Variables</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-green-500 text-white text-xs rounded-full animate-pulse">v5</span>
            </button>
            <button
              onClick={() => setActiveTab('natural-language')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'natural-language' 
                  ? 'bg-gradient-to-r from-green-600 to-blue-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Brain className="w-4 h-4" />
              <span>Natural Language</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-green-500 text-white text-xs rounded-full animate-pulse">v5</span>
            </button>
            <button
              onClick={() => setActiveTab('offline-mode')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'offline-mode' 
                  ? 'bg-gradient-to-r from-orange-600 to-yellow-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Download className="w-4 h-4" />
              <span>Offline Mode</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-green-500 text-white text-xs rounded-full animate-pulse">v5</span>
            </button>
            <button
              onClick={() => setActiveTab('virtualization')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'virtualization' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Globe className="w-4 h-4" />
              <span>Service Virtualization</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-green-500 text-white text-xs rounded-full animate-pulse">v5</span>
            </button>
            <button
              onClick={() => setActiveTab('privacy-ai')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition relative ${
                activeTab === 'privacy-ai' 
                  ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Privacy AI</span>
              <span className="absolute -top-1 -right-1 px-1 py-0.5 bg-green-500 text-white text-xs rounded-full animate-pulse">v5</span>
            </button>
          </nav>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'ai-employee' && (
          <AIEmployee />
        )}

        {activeTab === 'ai-agents' && (
          <AIAgentBuilder />
        )}
        
        {activeTab === 'orchestration' && (
          <OrchestrationHub />
        )}

        {activeTab === 'projects' && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">Your Projects</h2>
              <div className="flex items-center space-x-4">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search projects..."
                    className="pl-10 pr-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                
                {/* New Project Button */}
                <button
                  onClick={() => navigate('/create-project')}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                >
                  <Plus className="w-5 h-5" />
                  <span>New Project</span>
                </button>
              </div>
            </div>
          </div>

          {/* Projects List */}
          <div className="p-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-flex items-center space-x-2 text-gray-400">
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  <span>Loading projects...</span>
                </div>
              </div>
            ) : filteredProjects.length === 0 ? (
              <div className="text-center py-12">
                <FolderOpen className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No projects yet</h3>
                <p className="text-gray-500 mb-4">Create your first project to get started</p>
                <button
                  onClick={() => navigate('/create-project')}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                >
                  Create Project
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredProjects.map(project => (
                  <div key={project.id} className="bg-gray-900/50 rounded-lg p-6 border border-gray-700 hover:border-purple-500/50 transition">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-semibold text-white">{project.name}</h3>
                      <button className="text-gray-400 hover:text-white">
                        <MoreVertical className="w-5 h-5" />
                      </button>
                    </div>
                    
                    <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                      {project.description || 'No description'}
                    </p>
                    
                    <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                      <span>{project.api_count} APIs</span>
                      <span>{project.task_count} Tasks</span>
                    </div>
                    
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleOrchestrate(project.id)}
                        className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-purple-600/20 text-purple-400 rounded-lg hover:bg-purple-600/30 transition"
                      >
                        <PlayCircle className="w-4 h-4" />
                        <span>Orchestrate</span>
                      </button>
                      <button
                        onClick={() => navigate(`/projects/${project.id}`)}
                        className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-gray-700/50 text-gray-300 rounded-lg hover:bg-gray-700 transition"
                      >
                        <LayoutDashboard className="w-4 h-4" />
                        <span>View</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        )}

        {/* Tasks Tab */}
        {activeTab === 'tasks' && (
          <TaskManager />
        )}


        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <FileUpload 
            onUploadSuccess={(data) => {
              // Upload successful
              // Optionally refresh projects or show success message
              fetchProjects();
            }}
          />
        )}

        {/* Export/Import Tab */}
        {activeTab === 'export' && (
          <ExportImport 
            taskId={projects[0]?.last_task_id} // Use the most recent task ID
          />
        )}

        {/* API Tester Tab */}
        {activeTab === 'api-tester' && (
          <APIRequestBuilder />
        )}

        {/* Code Generator Tab */}
        {activeTab === 'code-generator' && (
          <CodeGenerator 
            apiSpec={projects[0]?.api_spec}
            requestData={null}
            selectedEndpoint={null}
          />
        )}

        {/* API Documentation Tab */}
        {activeTab === 'documentation' && (
          <APIDocumentation 
            projects={projects}
            currentTaskId={currentTaskId}
          />
        )}

        {/* Request History Tab */}
        {activeTab === 'history' && (
          <RequestHistory 
            onReplay={(requestData) => {
              // Switch to API Tester tab and populate with the replayed request
              setActiveTab('api-tester');
              // The APIRequestBuilder will need to accept initial data
            }}
          />
        )}

        {/* Monitoring Tab */}
        {activeTab === 'monitoring' && (
          <MonitoringDashboard />
        )}
        
        {/* Load Testing Tab */}
        {activeTab === 'load-testing' && (
          <LoadTesting />
        )}
        
        {/* Contract Testing Tab */}
        {activeTab === 'contract-testing' && (
          <ContractTesting />
        )}
        
        {/* Status Pages Tab */}
        {activeTab === 'status-pages' && (
          <StatusPages />
        )}
        
        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <AdvancedAnalytics workspaceId={currentWorkspace?.id} />
        )}
        
        {/* Team Management Tab */}
        {activeTab === 'team' && currentWorkspace && (
          <TeamManagement workspaceId={currentWorkspace.id} />
        )}
        {activeTab === 'team' && !currentWorkspace && (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <Building2 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Workspace Selected</h3>
            <p className="text-gray-400 mb-4">Please select or create a workspace to manage your team.</p>
            <WorkspaceSwitcher onWorkspaceChange={setCurrentWorkspace} />
          </div>
        )}

        {/* Webhooks Tab */}
        {activeTab === 'webhooks' && (
          <WebhookManager workspaceId={currentWorkspace?.id} />
        )}

        {/* V5.0 POSTMAN KILLER Features Content */}

        {/* Visual Workflow Builder */}
        {activeTab === 'visual-workflows' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Visual Workflow Builder</h2>
              <p className="opacity-90">Drag & drop interface with 7 block types including AI blocks. Better than Postman Flows!</p>
            </div>
            <VisualWorkflowBuilder />
          </div>
        )}

        {/* API Governance Engine */}
        {activeTab === 'api-governance' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">API Governance Engine</h2>
              <p className="opacity-90">8 built-in rules, 4 predefined rulesets. Complete compliance scoring system!</p>
            </div>
            <ApiGovernance />
          </div>
        )}

        {/* Enhanced Variable Manager */
        } {activeTab === 'enhanced-variables' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Enhanced Variable Management</h2>
              <p className="opacity-90">6 scope levels with local-by-default privacy. Auto-detects sensitive data!</p>
            </div>
            <EnhancedVariableManager 
              projectId={projects[0]?.id}
              onVariableChange={(variables) => { /* Handle variable changes */ }}
            />
          </div>
        )}
        
        {/* Natural Language Testing */}
        {activeTab === 'natural-language' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-green-600 to-blue-600 rounded-xl p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Natural Language Test Generation</h2>
              <p className="opacity-90">Generate comprehensive test suites using plain English - no coding required!</p>
            </div>
            <NaturalLanguageTesting 
              responseData={null}
              onTestGenerated={(tests) => { /* Handle generated tests */ }}
              onTestRun={(test, result) => { /* Handle test results */ }}
            />
          </div>
        )}
        
        {/* Offline Mode */}
        {activeTab === 'offline-mode' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-orange-600 to-yellow-600 rounded-xl p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Offline-First Mode</h2>
              <p className="opacity-90">Work offline with Git-friendly storage formats. Perfect for version control!</p>
            </div>
            <OfflineMode 
              collections={projects}
              onCollectionSave={(collection, format) => { /* Handle collection save */ }}
              onCollectionLoad={(collection) => { /* Handle collection load */ }}
              onSync={(synced) => { /* Handle sync */ }}
            />
          </div>
        )}
        
        {/* Service Virtualization */}
        {activeTab === 'virtualization' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Service Virtualization</h2>
              <p className="opacity-90">Mock entire API services with 8 advanced behaviors including chaos engineering!</p>
            </div>
            <ServiceVirtualization 
              openApiSpec={null}
              projectId={projects[0]?.id}
              onServiceCreated={(service) => { /* Handle service creation */ }}
            />
          </div>
        )}
        
        {/* Privacy-First AI */}
        {activeTab === 'privacy-ai' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Privacy-First AI Mode</h2>
              <p className="opacity-90">Your data NEVER trains our models. GDPR/HIPAA compliant with local AI options!</p>
            </div>
            <PrivacyAI 
              data={null}
              onProcessed={(result) => { /* Handle AI processing */ }}
              onAnonymized={(anonymized) => { /* Handle data anonymization */ }}
            />
          </div>
        )}

        {/* API Limits - Show on all tabs */}
        <div className="mt-8 bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">API Usage</h3>
              <p className="text-gray-400">
                {user?.api_calls_remaining || 0} calls remaining this month
              </p>
            </div>
            <button 
              onClick={() => navigate('/billing')}
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition">
              Upgrade Plan
            </button>
          </div>
          
          <div className="mt-4 bg-gray-900 rounded-lg p-2">
            <div 
              className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded"
              style={{ width: `${((100 - (user?.api_calls_remaining || 0)) / 100) * 100}%` }}
            />
          </div>
        </div>
      </div>
      </div>

      {/* AI Assistant - Floating, non-intrusive */}
      <AIAssistant />
    </div>
  );
};

export default Dashboard;