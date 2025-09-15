import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon, CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const ApiGovernance = () => {
  const [spec, setSpec] = useState('');
  const [format, setFormat] = useState('yaml');
  const [ruleset, setRuleset] = useState('enterprise-standards');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rules, setRules] = useState({});
  const [rulesets, setRulesets] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedSections, setExpandedSections] = useState({
    violations: true,
    summary: true,
    rules: false
  });

  // Load rules and rulesets on component mount
  useEffect(() => {
    loadRulesAndRulesets();
  }, []);

  const loadRulesAndRulesets = async () => {
    try {
      const token = localStorage.getItem('token');

      // Load rules
      const rulesResponse = await fetch('/api/governance/rules', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const rulesData = await rulesResponse.json();
      setRules(rulesData.rules || {});

      // Load rulesets
      const rulesetsResponse = await fetch('/api/governance/rulesets', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const rulesetsData = await rulesetsResponse.json();
      setRulesets(rulesetsData.rulesets || {});

    } catch (error) {
      console.error('Failed to load governance data:', error);
    }
  };

  const validateSpec = async () => {
    if (!spec.trim()) {
      alert('Please provide an OpenAPI specification');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/governance/validate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          spec_content: spec,
          format: format,
          ruleset: ruleset
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Validation failed');
      }

      const data = await response.json();
      setReport(data);
    } catch (error) {
      console.error('Validation error:', error);
      alert(`Validation failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-green-50 border-green-200 text-green-800';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackground = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const filteredViolations = report?.violations?.filter(v =>
    selectedCategory === 'all' || v.category === selectedCategory
  ) || [];

  const categories = [...new Set(report?.violations?.map(v => v.category) || [])];

  const sampleSpec = `openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
  description: A sample API for governance testing
servers:
  - url: http://api.example.com/v1
paths:
  /users:
    get:
      responses:
        '200':
          description: List of users
    post:
      responses:
        '201':
          description: User created
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: query
      name: api_key`;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            🛡️ API Governance Engine
          </h1>
          <p className="text-gray-400">
            Advanced API governance and compliance checking - The Postman killer feature
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Panel */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-xl font-semibold text-white mb-4">OpenAPI Specification</h2>

              {/* Controls */}
              <div className="flex gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Format</label>
                  <select
                    value={format}
                    onChange={(e) => setFormat(e.target.value)}
                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="yaml">YAML</option>
                    <option value="json">JSON</option>
                  </select>
                </div>

                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-300 mb-2">Ruleset</label>
                  <select
                    value={ruleset}
                    onChange={(e) => setRuleset(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:ring-2 focus:ring-blue-500"
                  >
                    {Object.entries(rulesets).map(([key, rs]) => (
                      <option key={key} value={key}>{rs.name}</option>
                    ))}
                  </select>
                </div>

                <div className="flex items-end">
                  <button
                    onClick={() => setSpec(sampleSpec)}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
                  >
                    Load Sample
                  </button>
                </div>
              </div>

              {/* Spec Input */}
              <div className="mb-4">
                <textarea
                  value={spec}
                  onChange={(e) => setSpec(e.target.value)}
                  placeholder="Paste your OpenAPI specification here..."
                  className="w-full h-64 px-4 py-3 bg-gray-700 border border-gray-600 rounded text-white font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Validate Button */}
              <button
                onClick={validateSpec}
                disabled={loading || !spec.trim()}
                className={`w-full py-3 px-6 rounded font-medium transition-colors ${
                  loading || !spec.trim()
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Validating...
                  </div>
                ) : (
                  '🔍 Validate API Specification'
                )}
              </button>
            </div>

            {/* Report Results */}
            {report && (
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-white">Governance Report</h2>
                  <div className={`px-4 py-2 rounded-full text-lg font-bold ${getScoreBackground(report.score)}`}>
                    <span className={getScoreColor(report.score)}>
                      {report.score.toFixed(1)}% Score
                    </span>
                  </div>
                </div>

                {/* Summary Section */}
                <div className="mb-6">
                  <button
                    onClick={() => toggleSection('summary')}
                    className="flex items-center justify-between w-full text-left text-lg font-medium text-white mb-4"
                  >
                    📊 Summary
                    {expandedSections.summary ?
                      <ChevronUpIcon className="h-5 w-5" /> :
                      <ChevronDownIcon className="h-5 w-5" />
                    }
                  </button>

                  {expandedSections.summary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="bg-red-900/30 p-4 rounded border border-red-700">
                        <div className="text-2xl font-bold text-red-400">{report.errors}</div>
                        <div className="text-sm text-red-300">Errors</div>
                      </div>
                      <div className="bg-yellow-900/30 p-4 rounded border border-yellow-700">
                        <div className="text-2xl font-bold text-yellow-400">{report.warnings}</div>
                        <div className="text-sm text-yellow-300">Warnings</div>
                      </div>
                      <div className="bg-blue-900/30 p-4 rounded border border-blue-700">
                        <div className="text-2xl font-bold text-blue-400">{report.info}</div>
                        <div className="text-sm text-blue-300">Info</div>
                      </div>
                      <div className="bg-gray-700 p-4 rounded border border-gray-600">
                        <div className="text-2xl font-bold text-white">{report.total_rules}</div>
                        <div className="text-sm text-gray-300">Rules Applied</div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Violations Section */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <button
                      onClick={() => toggleSection('violations')}
                      className="flex items-center text-lg font-medium text-white"
                    >
                      🚨 Violations ({report.violations.length})
                      {expandedSections.violations ?
                        <ChevronUpIcon className="h-5 w-5 ml-2" /> :
                        <ChevronDownIcon className="h-5 w-5 ml-2" />
                      }
                    </button>

                    {categories.length > 0 && (
                      <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                      >
                        <option value="all">All Categories</option>
                        {categories.map(cat => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                    )}
                  </div>

                  {expandedSections.violations && (
                    <div className="space-y-3">
                      {filteredViolations.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                          {report.violations.length === 0 ?
                            '🎉 No violations found! Your API spec is compliant.' :
                            'No violations in selected category.'
                          }
                        </div>
                      ) : (
                        filteredViolations.map((violation, index) => (
                          <div
                            key={index}
                            className={`p-4 rounded border ${getSeverityColor(violation.severity)}`}
                          >
                            <div className="flex items-start gap-3">
                              {getSeverityIcon(violation.severity)}
                              <div className="flex-1">
                                <div className="font-medium">{violation.rule_name}</div>
                                <div className="text-sm opacity-90 mt-1">{violation.message}</div>
                                <div className="text-xs mt-2 space-x-4">
                                  <span>Path: {violation.path}</span>
                                  <span>Category: {violation.category}</span>
                                </div>
                                {violation.suggested_fix && (
                                  <div className="mt-2 p-2 bg-black/20 rounded text-xs">
                                    <strong>💡 Suggested fix:</strong> {violation.suggested_fix}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Ruleset Info */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">📋 Current Ruleset</h3>
              {rulesets[ruleset] && (
                <div>
                  <h4 className="font-medium text-white">{rulesets[ruleset].name}</h4>
                  <p className="text-sm text-gray-400 mt-1 mb-4">{rulesets[ruleset].description}</p>
                  <div className="text-sm text-gray-300">
                    <div className="flex justify-between">
                      <span>Rules:</span>
                      <span>{rulesets[ruleset].rules?.length || 0}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Rules List */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <button
                onClick={() => toggleSection('rules')}
                className="flex items-center justify-between w-full text-left text-lg font-semibold text-white mb-4"
              >
                🔧 Available Rules
                {expandedSections.rules ?
                  <ChevronUpIcon className="h-5 w-5" /> :
                  <ChevronDownIcon className="h-5 w-5" />
                }
              </button>

              {expandedSections.rules && (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {Object.entries(rules).map(([ruleId, rule]) => (
                    <div key={ruleId} className="p-3 bg-gray-700 rounded border border-gray-600">
                      <div className="flex items-start gap-2 mb-2">
                        {getSeverityIcon(rule.severity)}
                        <div>
                          <div className="font-medium text-white text-sm">{rule.name}</div>
                          <div className="text-xs text-gray-400">{rule.category}</div>
                        </div>
                      </div>
                      <p className="text-xs text-gray-300">{rule.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">⚡ Quick Actions</h3>
              <div className="space-y-3">
                <button
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors text-sm"
                  onClick={() => {
                    const url = prompt('Enter OpenAPI spec URL:');
                    if (url) {
                      // TODO: Implement URL validation
                      alert('URL validation coming soon!');
                    }
                  }}
                >
                  🌐 Validate from URL
                </button>
                <button
                  className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors text-sm"
                  onClick={() => {
                    if (report) {
                      const exportData = {
                        ...report,
                        exported_at: new Date().toISOString()
                      };
                      const blob = new Blob([JSON.stringify(exportData, null, 2)],
                        { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `governance-report-${Date.now()}.json`;
                      a.click();
                    } else {
                      alert('No report to export. Run a validation first.');
                    }
                  }}
                >
                  📄 Export Report
                </button>
                <button
                  className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors text-sm"
                  onClick={() => {
                    alert('Custom rule builder coming in next update!');
                  }}
                >
                  ⚙️ Custom Rules
                </button>
              </div>
            </div>

            {/* Tips */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">💡 Pro Tips</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>• Use HTTPS for all server URLs</li>
                <li>• Add summaries to all operations</li>
                <li>• Use camelCase for parameter names</li>
                <li>• Include response time expectations</li>
                <li>• Document security requirements</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiGovernance;