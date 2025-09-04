import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, TrendingUp, CheckCircle, XCircle, Brain, DollarSign, Lock } from 'lucide-react';
import axios from 'axios';

const AIAnalysisDisplay = ({ taskId }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (taskId) {
      fetchAIAnalysis();
    }
  }, [taskId]);

  const fetchAIAnalysis = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/ai-analysis/${taskId}`);
      setAnalysis(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch AI analysis:', err);
      setError('Failed to load AI analysis');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
        {error}
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="text-center p-8 text-gray-500">
        No AI analysis available yet. Run orchestration to generate analysis.
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-500/20 border-green-500/30';
    if (score >= 60) return 'bg-yellow-500/20 border-yellow-500/30';
    return 'bg-red-500/20 border-red-500/30';
  };

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      {analysis.executive_summary && (
        <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg p-6 border border-purple-500/20">
          <div className="flex items-start gap-3">
            <Brain className="w-6 h-6 text-purple-400 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">AI Executive Summary</h3>
              <p className="text-gray-300 leading-relaxed">{analysis.executive_summary}</p>
            </div>
          </div>
        </div>
      )}

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Security Score */}
        <div className={`rounded-lg border p-6 ${getScoreBg(analysis.security_score || 0)}`}>
          <div className="flex items-center justify-between mb-4">
            <Shield className="w-8 h-8 text-purple-400" />
            <span className={`text-3xl font-bold ${getScoreColor(analysis.security_score || 0)}`}>
              {analysis.security_score || 0}%
            </span>
          </div>
          <h3 className="text-white font-semibold mb-1">Security Score</h3>
          <p className="text-gray-400 text-sm">Overall API security rating</p>
        </div>

        {/* Business Value */}
        {analysis.business_value && (
          <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <DollarSign className="w-8 h-8 text-green-400" />
              <span className="text-2xl font-bold text-green-400">
                ${(analysis.business_value / 1000).toFixed(1)}k
              </span>
            </div>
            <h3 className="text-white font-semibold mb-1">Estimated Value</h3>
            <p className="text-gray-400 text-sm">Potential annual savings</p>
          </div>
        )}

        {/* Compliance Status */}
        <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <Lock className="w-8 h-8 text-blue-400" />
            <span className="text-xl font-bold text-blue-400">
              {analysis.compliance ? Object.values(analysis.compliance).filter(v => v).length : 0}/{analysis.compliance ? Object.keys(analysis.compliance).length : 0}
            </span>
          </div>
          <h3 className="text-white font-semibold mb-1">Compliance</h3>
          <p className="text-gray-400 text-sm">Standards met</p>
        </div>
      </div>

      {/* Vulnerabilities */}
      {analysis.vulnerabilities && analysis.vulnerabilities.length > 0 && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-400" />
            <h3 className="text-lg font-semibold text-white">Security Vulnerabilities</h3>
            <span className="bg-red-500/30 text-red-300 px-2 py-1 rounded text-sm">
              {analysis.vulnerabilities.length} Found
            </span>
          </div>
          <div className="space-y-3">
            {analysis.vulnerabilities.map((vuln, index) => (
              <div key={index} className="bg-gray-900/50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        vuln.severity?.toLowerCase() === 'high' ? 'bg-red-500/30 text-red-300' :
                        vuln.severity?.toLowerCase() === 'medium' ? 'bg-yellow-500/30 text-yellow-300' :
                        'bg-blue-500/30 text-blue-300'
                      }`}>
                        {vuln.severity?.toUpperCase()}
                      </span>
                      <span className="text-gray-400 text-sm">{vuln.type}</span>
                    </div>
                    <p className="text-white font-medium">{vuln.description}</p>
                    {vuln.recommendation && (
                      <p className="text-gray-400 text-sm mt-2">
                        <span className="text-green-400">Fix:</span> {vuln.recommendation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Optimizations */}
      {analysis.optimizations && analysis.optimizations.length > 0 && (
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-6 h-6 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">Performance Optimizations</h3>
            <span className="bg-blue-500/30 text-blue-300 px-2 py-1 rounded text-sm">
              {analysis.optimizations.length} Suggestions
            </span>
          </div>
          <div className="space-y-3">
            {analysis.optimizations.map((opt, index) => (
              <div key={index} className="bg-gray-900/50 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-white font-medium">{opt.title || opt.description}</p>
                    {opt.impact && (
                      <p className="text-gray-400 text-sm mt-1">Impact: {opt.impact}</p>
                    )}
                    {opt.effort && (
                      <p className="text-gray-400 text-sm">Effort: {opt.effort}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compliance Details */}
      {analysis.compliance && Object.keys(analysis.compliance).length > 0 && (
        <div className="bg-gray-800/50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Lock className="w-6 h-6 text-purple-400" />
            Compliance Status
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(analysis.compliance).map(([standard, compliant]) => (
              <div key={standard} className="flex items-center gap-2 bg-gray-900/50 rounded-lg px-3 py-2">
                {compliant ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                <span className={`text-sm ${compliant ? 'text-green-300' : 'text-red-300'}`}>
                  {standard.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional Insights */}
      {analysis.insights && (
        <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-3">Additional AI Insights</h3>
          <ul className="space-y-2">
            {analysis.insights.map((insight, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-purple-400 mt-1">•</span>
                <span className="text-gray-300">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default AIAnalysisDisplay;