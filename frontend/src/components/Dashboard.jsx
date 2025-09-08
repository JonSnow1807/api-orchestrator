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
  Code2,
  Home,
  CreditCard,
  BookOpen
} from 'lucide-react';
import StatsDashboard from './StatsDashboard';
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
import RequestHistory from './RequestHistory';
import MonitoringDashboard from './MonitoringDashboard';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('orchestration');
  const [currentTaskId, setCurrentTaskId] = useState(null);

  useEffect(() => {
    fetchProjects();
    fetchStats();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get('/api/projects');
      setProjects(response.data.projects);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/projects/stats/overview');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
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
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-6">
              <Link to="/" className="flex items-center space-x-2">
                <Zap className="w-8 h-8 text-purple-500" />
                <h1 className="text-2xl font-bold text-white">API Orchestrator</h1>
              </Link>
              <span className="px-3 py-1 bg-purple-600/20 text-purple-400 text-sm rounded-full border border-purple-500/30">
                {user?.subscription_tier || 'Free'} Tier
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
              >
                <User className="w-5 h-5" />
                <span>{user?.username || 'Profile'}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
              >
                <LogOut className="w-5 h-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <FolderOpen className="w-8 h-8 text-purple-500" />
              <span className="text-2xl font-bold text-white">{stats?.total_projects || 0}</span>
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
        <div className="mb-8">
          <nav className="flex space-x-1 bg-gray-800/50 backdrop-blur rounded-lg p-1">
            <button
              onClick={() => setActiveTab('orchestration')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'orchestration' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-5 h-5" />
              <span>Orchestration</span>
            </button>
            <button
              onClick={() => setActiveTab('projects')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'projects' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <FolderOpen className="w-5 h-5" />
              <span>Projects</span>
            </button>
            <button
              onClick={() => setActiveTab('statistics')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'statistics' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              <span>Statistics</span>
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'tasks' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <History className="w-5 h-5" />
              <span>Tasks</span>
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'code' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Code2 className="w-5 h-5" />
              <span>Code</span>
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'upload' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Upload className="w-5 h-5" />
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
              <FileArchive className="w-5 h-5" />
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
              <Zap className="w-5 h-5" />
              <span>API Tester</span>
            </button>
            <button
              onClick={() => setActiveTab('documentation')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                activeTab === 'documentation' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <BookOpen className="w-5 h-5" />
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
              <Clock className="w-5 h-5" />
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
              <Shield className="w-5 h-5" />
              <span>Monitoring</span>
            </button>
          </nav>
        </div>

        {/* Content based on active tab */}
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

        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          <StatsDashboard />
        )}

        {/* Tasks Tab */}
        {activeTab === 'tasks' && (
          <TaskManager />
        )}


        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <FileUpload 
            onUploadSuccess={(data) => {
              console.log('Upload success:', data);
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
      
      {/* AI Assistant - Floating, non-intrusive */}
      <AIAssistant />
    </div>
  );
};

export default Dashboard;