import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { 
  FolderPlus, 
  ArrowLeft, 
  Zap, 
  GitBranch,
  Upload,
  AlertCircle
} from 'lucide-react';

const ProjectCreate = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sourceType, setSourceType] = useState('directory');
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    source_path: '',
    github_url: '',
    framework: 'auto-detect',
    include_tests: true,
    include_mock: true,
    include_ai_analysis: true
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Create the project
      const projectData = {
        name: formData.name,
        description: formData.description,
        source_type: sourceType,
        source_path: sourceType === 'directory' ? formData.source_path : formData.github_url,
        config: {
          framework: formData.framework,
          include_tests: formData.include_tests,
          include_mock: formData.include_mock,
          include_ai_analysis: formData.include_ai_analysis
        }
      };

      const response = await axios.post('/api/projects', projectData);
      const project = response.data;

      // Start orchestration if source is provided
      if (projectData.source_path) {
        await axios.post(`/api/projects/${project.id}/orchestrate`);
      }

      // Navigate to project details
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

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
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-8">
          {/* Title */}
          <div className="flex items-center space-x-3 mb-8">
            <div className="bg-gradient-to-br from-purple-600 to-blue-600 p-3 rounded-xl">
              <FolderPlus className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Create New Project</h1>
              <p className="text-gray-400">Set up your API orchestration project</p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Project Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-2.5 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="My API Project"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-2.5 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Describe your project..."
              />
            </div>

            {/* Source Type Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Source Type
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setSourceType('directory')}
                  className={`p-4 rounded-lg border-2 transition ${
                    sourceType === 'directory'
                      ? 'bg-purple-600/20 border-purple-500 text-purple-400'
                      : 'bg-gray-900/50 border-gray-700 text-gray-400 hover:border-gray-600'
                  }`}
                >
                  <Upload className="w-6 h-6 mx-auto mb-2" />
                  <span className="text-sm">Local Directory</span>
                </button>
                
                <button
                  type="button"
                  onClick={() => setSourceType('github')}
                  className={`p-4 rounded-lg border-2 transition ${
                    sourceType === 'github'
                      ? 'bg-purple-600/20 border-purple-500 text-purple-400'
                      : 'bg-gray-900/50 border-gray-700 text-gray-400 hover:border-gray-600'
                  }`}
                >
                  <GitBranch className="w-6 h-6 mx-auto mb-2" />
                  <span className="text-sm">GitHub Repository</span>
                </button>
              </div>
            </div>

            {/* Source Path/URL */}
            {sourceType === 'directory' ? (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Source Directory Path
                </label>
                <input
                  type="text"
                  name="source_path"
                  value={formData.source_path}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="/path/to/your/api/code"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Leave empty to configure later
                </p>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  GitHub Repository URL
                </label>
                <input
                  type="url"
                  name="github_url"
                  value={formData.github_url}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="https://github.com/username/repository"
                />
              </div>
            )}

            {/* Framework Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Framework
              </label>
              <select
                name="framework"
                value={formData.framework}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="auto-detect">Auto-detect</option>
                <option value="fastapi">FastAPI</option>
                <option value="flask">Flask</option>
                <option value="django">Django</option>
                <option value="express">Express.js</option>
                <option value="nestjs">NestJS</option>
              </select>
            </div>

            {/* Options */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Generation Options
              </label>
              
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="include_tests"
                  checked={formData.include_tests}
                  onChange={handleChange}
                  className="w-4 h-4 bg-gray-900 border-gray-700 rounded text-purple-600 focus:ring-purple-500"
                />
                <span className="text-gray-300">Generate test suites</span>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="include_mock"
                  checked={formData.include_mock}
                  onChange={handleChange}
                  className="w-4 h-4 bg-gray-900 border-gray-700 rounded text-purple-600 focus:ring-purple-500"
                />
                <span className="text-gray-300">Create mock server</span>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="include_ai_analysis"
                  checked={formData.include_ai_analysis}
                  onChange={handleChange}
                  disabled={user?.subscription_tier === 'free'}
                  className="w-4 h-4 bg-gray-900 border-gray-700 rounded text-purple-600 focus:ring-purple-500 disabled:opacity-50"
                />
                <span className="text-gray-300">
                  AI-powered analysis
                  {user?.subscription_tier === 'free' && (
                    <span className="ml-2 text-xs text-yellow-500">(Pro feature)</span>
                  )}
                </span>
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4 pt-4">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="flex-1 py-3 px-4 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
              >
                Cancel
              </button>
              
              <button
                type="submit"
                disabled={loading || !formData.name}
                className="flex-1 py-3 px-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg shadow-lg hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                    Creating...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <Zap className="w-5 h-5 mr-2" />
                    Create Project
                  </span>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProjectCreate;