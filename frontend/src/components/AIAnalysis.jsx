import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import {
  Brain,
  Shield,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  DollarSign,
  FileText,
  ChevronDown,
  ChevronRight,
  Loader2,
  Info,
  Zap,
  Award,
  XCircle
} from 'lucide-react';

const AIAnalysis = ({ taskId, projectId }) => {
  const { token } = useAuth();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    security: true,
    performance: true,
    compliance: false,
    recommendations: false
  });

  useEffect(() => {
    if (taskId || projectId) {
      fetchAnalysis();
    }
  }, [taskId, projectId]);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const endpoint = taskId 
        ? `/api/tasks/${taskId}/ai-analysis`
        : `/api/projects/${projectId}/ai-analysis`;
        
      const response = await axios.get(endpoint, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      setAnalysis(response.data);
    } catch (err) {
      console.error('Failed to fetch AI analysis:', err);
      setError(err.response?.data?.detail || 'Failed to load AI analysis');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-600 bg-red-50';
      case 'high':
        return 'text-orange-600 bg-orange-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getComplianceIcon = (status) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'partial':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'non-compliant':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          <span className="ml-3 text-gray-600">Analyzing your APIs...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center py-12">
          <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">No AI Analysis Available</h3>
          <p className="text-gray-500">Run an orchestration to generate AI-powered insights</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Brain className="w-6 h-6 text-indigo-600" />
          <h3 className="text-xl font-semibold text-gray-900">AI Analysis</h3>
        </div>
        
        {/* Overall Score */}
        {analysis.overall_score && (
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <div className={`text-3xl font-bold ${getScoreColor(analysis.overall_score)}`}>
                {analysis.overall_score}%
              </div>
              <div className="text-xs text-gray-500">Overall Score</div>
            </div>
          </div>
        )}
      </div>

      {/* Executive Summary */}
      {analysis.executive_summary && (
        <div className="mb-6 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
            <FileText className="w-5 h-5 mr-2 text-indigo-600" />
            Executive Summary
          </h4>
          <p className="text-gray-700 text-sm leading-relaxed">
            {analysis.executive_summary}
          </p>
        </div>
      )}

      {/* Business Value */}
      {analysis.business_value && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              <span className="text-2xl font-bold text-green-700">
                ${analysis.business_value.cost_savings || 0}
              </span>
            </div>
            <div className="text-sm text-gray-600">Estimated Savings</div>
          </div>
          
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <span className="text-2xl font-bold text-blue-700">
                {analysis.business_value.efficiency_gain || 0}%
              </span>
            </div>
            <div className="text-sm text-gray-600">Efficiency Gain</div>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <Award className="w-5 h-5 text-purple-600" />
              <span className="text-2xl font-bold text-purple-700">
                {analysis.business_value.roi || 0}%
              </span>
            </div>
            <div className="text-sm text-gray-600">ROI</div>
          </div>
        </div>
      )}

      {/* Security Analysis */}
      <div className="mb-4">
        <button
          onClick={() => toggleSection('security')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <Shield className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-gray-900">Security Analysis</span>
            {analysis.security_score && (
              <span className={`px-2 py-1 text-xs rounded-full ${getScoreColor(analysis.security_score)} bg-opacity-10`}>
                Score: {analysis.security_score}%
              </span>
            )}
          </div>
          {expandedSections.security ? 
            <ChevronDown className="w-5 h-5 text-gray-500" /> : 
            <ChevronRight className="w-5 h-5 text-gray-500" />
          }
        </button>
        
        {expandedSections.security && analysis.security_vulnerabilities && (
          <div className="mt-2 p-4 bg-white border border-gray-200 rounded-lg">
            {analysis.security_vulnerabilities.length === 0 ? (
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-5 h-5" />
                <span>No security vulnerabilities detected</span>
              </div>
            ) : (
              <div className="space-y-3">
                {analysis.security_vulnerabilities.map((vuln, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={`px-2 py-1 text-xs rounded ${getSeverityColor(vuln.severity)}`}>
                            {vuln.severity}
                          </span>
                          <span className="font-medium text-gray-900">{vuln.type}</span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{vuln.description}</p>
                        {vuln.recommendation && (
                          <div className="text-sm">
                            <span className="font-medium text-gray-700">Fix: </span>
                            <span className="text-gray-600">{vuln.recommendation}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Performance Optimization */}
      <div className="mb-4">
        <button
          onClick={() => toggleSection('performance')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <Zap className="w-5 h-5 text-yellow-600" />
            <span className="font-semibold text-gray-900">Performance Optimization</span>
            {analysis.performance_score && (
              <span className={`px-2 py-1 text-xs rounded-full ${getScoreColor(analysis.performance_score)} bg-opacity-10`}>
                Score: {analysis.performance_score}%
              </span>
            )}
          </div>
          {expandedSections.performance ? 
            <ChevronDown className="w-5 h-5 text-gray-500" /> : 
            <ChevronRight className="w-5 h-5 text-gray-500" />
          }
        </button>
        
        {expandedSections.performance && analysis.performance_recommendations && (
          <div className="mt-2 p-4 bg-white border border-gray-200 rounded-lg">
            <div className="space-y-3">
              {analysis.performance_recommendations.map((rec, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      <Zap className="w-4 h-4 text-yellow-500" />
                    </div>
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900 mb-1">{rec.title}</h5>
                      <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                      {rec.impact && (
                        <div className="flex items-center space-x-4 text-xs">
                          <span className="text-gray-500">Impact:</span>
                          <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                            {rec.impact}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Compliance Check */}
      <div className="mb-4">
        <button
          onClick={() => toggleSection('compliance')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <Award className="w-5 h-5 text-purple-600" />
            <span className="font-semibold text-gray-900">Compliance Check</span>
          </div>
          {expandedSections.compliance ? 
            <ChevronDown className="w-5 h-5 text-gray-500" /> : 
            <ChevronRight className="w-5 h-5 text-gray-500" />
          }
        </button>
        
        {expandedSections.compliance && analysis.compliance && (
          <div className="mt-2 p-4 bg-white border border-gray-200 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(analysis.compliance).map(([standard, status]) => (
                <div key={standard} className="flex items-center space-x-2">
                  {getComplianceIcon(status)}
                  <span className="text-sm font-medium text-gray-700">
                    {standard.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="mb-4">
        <button
          onClick={() => toggleSection('recommendations')}
          className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <Info className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-gray-900">Recommendations</span>
            {analysis.recommendations && (
              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                {analysis.recommendations.length} items
              </span>
            )}
          </div>
          {expandedSections.recommendations ? 
            <ChevronDown className="w-5 h-5 text-gray-500" /> : 
            <ChevronRight className="w-5 h-5 text-gray-500" />
          }
        </button>
        
        {expandedSections.recommendations && analysis.recommendations && (
          <div className="mt-2 p-4 bg-white border border-gray-200 rounded-lg">
            <div className="space-y-2">
              {analysis.recommendations.map((rec, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5" />
                  <span className="text-sm text-gray-700">{rec}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={fetchAnalysis}
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition-colors"
        >
          Refresh Analysis
        </button>
      </div>
    </div>
  );
};

export default AIAnalysis;