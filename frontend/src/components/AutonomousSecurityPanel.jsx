import React, { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Play,
  Pause,
  Zap,
  Bot,
  Lock,
  Unlock,
  FileCheck,
  AlertCircle,
  Settings,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';

const AutonomousSecurityPanel = ({ projectId, endpoint }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [autoExecute, setAutoExecute] = useState(false);
  const [safeMode, setSafeMode] = useState(true);
  const [executionLog, setExecutionLog] = useState([]);
  const [error, setError] = useState(null);

  const getApiUrl = (path) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${baseUrl}${path}`;
  };

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setExecutionLog(prev => [...prev, { message, type, timestamp }]);
  };

  const runAutonomousAnalysis = async () => {
    setIsAnalyzing(true);
    setError(null);
    setExecutionLog([]);
    addLog('🚀 Starting autonomous security analysis...', 'info');

    try {
      // Call the autonomous security analysis endpoint
      const response = await axios.post(
        getApiUrl('/api/ultra-premium/autonomous-security-analysis'),
        {
          endpoint_data: {
            path: endpoint?.path || '/api/test',
            method: endpoint?.method || 'GET',
            security: endpoint?.security || []
          },
          project_id: projectId,
          auto_execute: autoExecute,
          auto_fix_low_risk: !safeMode,
          require_approval_medium_risk: true,
          business_context: 'API Security Analysis'
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (response.data.success) {
        const result = response.data.data;
        setAnalysisResult(result);

        // Log the analysis results
        addLog(`✅ Analysis complete!`, 'success');

        if (result.plan) {
          addLog(`📋 Created plan with ${result.plan.actions?.length || 0} actions`, 'info');
          addLog(`⚠️ Risk level: ${result.plan.risk_assessment}`, 'warning');
        }

        if (result.vulnerabilities_found) {
          addLog(`🔍 Found ${result.vulnerabilities_found.length} vulnerabilities`, 'warning');
          result.vulnerabilities_found.forEach(vuln => {
            addLog(`  • ${vuln.type}: ${vuln.issue}`, 'warning');
          });
        }

        if (result.execution_results) {
          addLog(`🔧 Executed ${result.execution_results.length} actions`, 'success');
          result.execution_results.forEach(exec => {
            if (exec.status === 'completed') {
              addLog(`  ✅ ${exec.action}: ${exec.result}`, 'success');
            } else {
              addLog(`  ❌ ${exec.action}: ${exec.error}`, 'error');
            }
          });
        }

        if (result.fixes_applied > 0) {
          addLog(`🛠️ Applied ${result.fixes_applied} automatic fixes`, 'success');
        }
      } else {
        throw new Error(response.data.error || 'Analysis failed');
      }
    } catch (err) {
      console.error('Autonomous analysis error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to run analysis');
      addLog(`❌ Error: ${err.message}`, 'error');

      // Check if it's a subscription issue
      if (err.response?.status === 402) {
        setError('Ultra Premium subscription required for autonomous AI agents');
        addLog('⚠️ Ultra Premium subscription required', 'warning');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const executeApprovedPlan = async (planId) => {
    try {
      addLog('🤖 Executing approved plan...', 'info');

      const response = await axios.post(
        getApiUrl('/api/ultra-premium/execute-approved-plan'),
        {
          plan_id: planId,
          project_id: projectId,
          endpoint_data: endpoint
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (response.data.success) {
        addLog('✅ Plan executed successfully', 'success');
        setAnalysisResult(prev => ({
          ...prev,
          execution_results: response.data.data.results
        }));
      }
    } catch (err) {
      addLog(`❌ Execution failed: ${err.message}`, 'error');
    }
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-600/20 rounded-lg">
            <Shield className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Autonomous Security AI</h3>
            <p className="text-sm text-gray-400">AI-powered security analysis and remediation</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-purple-400" />
          <span className="text-sm text-purple-400">Ultra Premium</span>
        </div>
      </div>

      {/* Settings */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
          <div className="flex items-center gap-2">
            {safeMode ? <Lock className="w-4 h-4 text-green-400" /> : <Unlock className="w-4 h-4 text-yellow-400" />}
            <span className="text-sm text-gray-300">Safe Mode</span>
          </div>
          <button
            onClick={() => setSafeMode(!safeMode)}
            className={`px-3 py-1 text-xs rounded-full transition ${
              safeMode
                ? 'bg-green-600/20 text-green-400 border border-green-500/30'
                : 'bg-yellow-600/20 text-yellow-400 border border-yellow-500/30'
            }`}
          >
            {safeMode ? 'ON' : 'OFF'}
          </button>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-gray-300">Auto-Execute</span>
          </div>
          <button
            onClick={() => setAutoExecute(!autoExecute)}
            disabled={safeMode}
            className={`px-3 py-1 text-xs rounded-full transition ${
              autoExecute
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'bg-gray-600/20 text-gray-400 border border-gray-500/30'
            } ${safeMode ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {autoExecute ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Analysis Button */}
      <button
        onClick={runAutonomousAnalysis}
        disabled={isAnalyzing}
        className={`w-full py-3 px-4 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
          isAnalyzing
            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700'
        }`}
      >
        {isAnalyzing ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Play className="w-5 h-5" />
            Run Autonomous Analysis
          </>
        )}
      </button>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        </div>
      )}

      {/* Results Display */}
      {analysisResult && (
        <div className="mt-6 space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-gray-700/50 rounded-lg text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {analysisResult.vulnerabilities_found?.length || 0}
              </div>
              <div className="text-xs text-gray-400">Vulnerabilities</div>
            </div>
            <div className="p-3 bg-gray-700/50 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-400">
                {analysisResult.fixes_applied || 0}
              </div>
              <div className="text-xs text-gray-400">Fixes Applied</div>
            </div>
            <div className="p-3 bg-gray-700/50 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-400">
                {analysisResult.plan?.confidence_score ?
                  `${(analysisResult.plan.confidence_score * 100).toFixed(0)}%` :
                  'N/A'
                }
              </div>
              <div className="text-xs text-gray-400">Confidence</div>
            </div>
          </div>

          {/* Action Plan */}
          {analysisResult.plan && analysisResult.plan.requires_approval && (
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  <span className="text-sm font-medium text-yellow-400">
                    Approval Required - {analysisResult.plan.actions?.length || 0} Actions Planned
                  </span>
                </div>
                <button
                  onClick={() => executeApprovedPlan(analysisResult.plan.plan_id)}
                  className="px-3 py-1 bg-yellow-600/20 text-yellow-400 rounded-lg text-sm hover:bg-yellow-600/30 transition"
                >
                  Approve & Execute
                </button>
              </div>
              <div className="space-y-1">
                {analysisResult.plan.actions?.slice(0, 3).map((action, idx) => (
                  <div key={idx} className="text-xs text-gray-400">
                    • {action.tool_name}: {action.reasoning}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Vulnerabilities List */}
          {analysisResult.vulnerabilities_found && analysisResult.vulnerabilities_found.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-300">Vulnerabilities Found:</h4>
              {analysisResult.vulnerabilities_found.slice(0, 5).map((vuln, idx) => (
                <div key={idx} className="p-3 bg-gray-700/30 rounded-lg flex items-start gap-3">
                  <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${
                    vuln.severity === 'HIGH' ? 'bg-red-400' :
                    vuln.severity === 'MEDIUM' ? 'bg-yellow-400' :
                    'bg-blue-400'
                  }`} />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-200">{vuln.type}</div>
                    <div className="text-xs text-gray-400 mt-1">{vuln.issue}</div>
                    {vuln.fixed && (
                      <div className="flex items-center gap-1 mt-2">
                        <CheckCircle className="w-3 h-3 text-green-400" />
                        <span className="text-xs text-green-400">Fixed automatically</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Execution Log */}
      {executionLog.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Execution Log:</h4>
          <div className="bg-gray-900/50 rounded-lg p-3 max-h-48 overflow-y-auto space-y-1">
            {executionLog.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs">
                <span className="text-gray-500">{log.timestamp}</span>
                <span className={`flex-1 ${
                  log.type === 'error' ? 'text-red-400' :
                  log.type === 'success' ? 'text-green-400' :
                  log.type === 'warning' ? 'text-yellow-400' :
                  'text-gray-400'
                }`}>
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AutonomousSecurityPanel;