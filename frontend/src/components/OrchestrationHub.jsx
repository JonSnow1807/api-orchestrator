import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Lock, Info, AlertCircle } from 'lucide-react';
import CodeEditor from './CodeEditor';
import FileUpload from './FileUpload';
import RealtimeMonitor from './RealtimeMonitor';
import AIAnalysis from './AIAnalysis';
import MockServerManager from './MockServerManager';

const OrchestrationHub = () => {
  const { user } = useAuth();
  const { showInfo, showWarning, showUpgradePrompt } = useToast();
  const [activeTab, setActiveTab] = useState('code');
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [currentSpecs, setCurrentSpecs] = useState(null);
  const [orchestrationResults, setOrchestrationResults] = useState(null);

  const handleOrchestrationStart = (taskId) => {
    setCurrentTaskId(taskId);
    setActiveTab('monitor'); // Switch to monitoring tab
  };

  const handleUploadSuccess = (data) => {
    if (data.task_id) {
      setCurrentTaskId(data.task_id);
      setActiveTab('monitor');
    }
  };

  const handleOrchestrationComplete = (results) => {
    setOrchestrationResults(results);
    if (results.specs) {
      setCurrentSpecs(results.specs);
    }
    // Show AI analysis if available
    if (results.ai_analysis) {
      setActiveTab('analysis');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">API Orchestration Hub</h1>
        <p className="text-gray-400">
          Discover, test, and deploy your APIs with AI-powered insights
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700">
        <div className="border-b border-gray-700">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('code')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'code'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-white hover:border-gray-500'
              }`}
            >
              Code Input
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'upload'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-white hover:border-gray-500'
              }`}
            >
              File Upload
            </button>
            <button
              onClick={() => {
                if (!currentTaskId) {
                  showInfo('Please start an orchestration first by using Code Input or File Upload');
                } else {
                  setActiveTab('monitor');
                }
              }}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors relative group ${
                activeTab === 'monitor'
                  ? 'border-purple-500 text-purple-400'
                  : currentTaskId 
                    ? 'border-transparent text-gray-400 hover:text-white hover:border-gray-500'
                    : 'border-transparent text-gray-500 cursor-not-allowed opacity-60'
              }`}
            >
              <span className="flex items-center">
                Real-time Monitor
                {!currentTaskId && (
                  <Info className="w-4 h-4 ml-1" />
                )}
                {currentTaskId && (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-purple-600/20 text-purple-400 rounded-full">
                    Active
                  </span>
                )}
              </span>
              {!currentTaskId && (
                <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  Start an orchestration to enable monitoring
                </span>
              )}
            </button>
            <button
              onClick={() => {
                if (user?.subscription_tier === 'free') {
                  showUpgradePrompt('AI Analysis');
                } else if (!currentTaskId && !orchestrationResults) {
                  showInfo('Please complete an orchestration first to view AI analysis');
                } else {
                  setActiveTab('analysis');
                }
              }}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors relative group ${
                activeTab === 'analysis'
                  ? 'border-purple-500 text-purple-400'
                  : (currentTaskId || orchestrationResults) && user?.subscription_tier !== 'free'
                    ? 'border-transparent text-gray-400 hover:text-white hover:border-gray-500'
                    : 'border-transparent text-gray-500 cursor-not-allowed opacity-60'
              }`}
            >
              <span className="flex items-center">
                AI Analysis
                {user?.subscription_tier === 'free' && (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-600/20 text-yellow-400 rounded-full flex items-center">
                    <Lock className="w-3 h-3 mr-1" />
                    Pro
                  </span>
                )}
                {(!currentTaskId && !orchestrationResults && user?.subscription_tier !== 'free') && (
                  <Info className="w-4 h-4 ml-1" />
                )}
              </span>
              {user?.subscription_tier === 'free' && (
                <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  Upgrade to Pro for AI-powered insights
                </span>
              )}
              {(!currentTaskId && !orchestrationResults && user?.subscription_tier !== 'free') && (
                <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  Complete an orchestration first
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('mock')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'mock'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-white hover:border-gray-500'
              }`}
            >
              Mock Servers
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'code' && (
            <CodeEditor onOrchestrationStart={handleOrchestrationStart} />
          )}

          {activeTab === 'upload' && (
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          )}

          {activeTab === 'monitor' && (
            <RealtimeMonitor 
              taskId={currentTaskId} 
              onComplete={handleOrchestrationComplete}
            />
          )}

          {activeTab === 'analysis' && (
            <AIAnalysis 
              taskId={currentTaskId}
              projectId={null}
            />
          )}

          {activeTab === 'mock' && (
            <MockServerManager 
              taskId={currentTaskId}
              specs={currentSpecs}
            />
          )}
        </div>
      </div>

      {/* Quick Stats */}
      {orchestrationResults && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-4">
            <div className="text-2xl font-bold text-indigo-600">
              {orchestrationResults.endpoints_count || 0}
            </div>
            <div className="text-sm text-gray-600">Endpoints Discovered</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-4">
            <div className="text-2xl font-bold text-green-600">
              {orchestrationResults.tests_generated || 0}
            </div>
            <div className="text-sm text-gray-600">Tests Generated</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-4">
            <div className="text-2xl font-bold text-purple-600">
              {orchestrationResults.security_score || 'N/A'}%
            </div>
            <div className="text-sm text-gray-600">Security Score</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {orchestrationResults.mock_servers || 0}
            </div>
            <div className="text-sm text-gray-600">Mock Servers Available</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrchestrationHub;