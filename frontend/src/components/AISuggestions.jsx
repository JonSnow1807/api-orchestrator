import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, Zap, Shield, AlertCircle, CheckCircle, Brain, Lightbulb, TrendingUp } from 'lucide-react';

const AISuggestions = ({ 
  type, 
  context, 
  onApplySuggestion,
  position = 'right',
  trigger = 'hover'
}) => {
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [appliedSuggestions, setAppliedSuggestions] = useState(new Set());

  const fetchSuggestions = useCallback(async () => {
    if (!type || !context) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const endpoint = `/api/ai-suggestions/${type}`;
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(context)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch suggestions: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSuggestions(data);
    } catch (err) {
      console.error('Error fetching AI suggestions:', err);
      setError(err.message);
      // Use fallback suggestions
      setSuggestions(getFallbackSuggestions(type, context));
    } finally {
      setLoading(false);
    }
  }, [type, context]);

  useEffect(() => {
    if (trigger === 'auto' && type && context) {
      fetchSuggestions();
    }
  }, [type, context, trigger, fetchSuggestions]);

  const handleTrigger = () => {
    if (trigger === 'hover' || trigger === 'click') {
      setIsVisible(!isVisible);
      if (!suggestions && !loading) {
        fetchSuggestions();
      }
    }
  };

  const handleApplySuggestion = (suggestion, index) => {
    if (onApplySuggestion) {
      onApplySuggestion(suggestion);
      setAppliedSuggestions(prev => new Set([...prev, index]));
    }
  };

  const getFallbackSuggestions = (type, context) => {
    // Provide intelligent fallback suggestions
    const fallbacks = {
      headers: {
        suggestions: [
          { header: 'Content-Type', value: 'application/json', description: 'Specify JSON content' },
          { header: 'Authorization', value: 'Bearer <token>', description: 'Add authentication' }
        ],
        confidence: 0.7,
        explanation: 'Common header suggestions'
      },
      payload: {
        suggestions: [
          { scenario: 'Valid data', payload: { name: 'Test', email: 'test@example.com' } },
          { scenario: 'Edge case', payload: { name: '', email: 'invalid' } }
        ],
        confidence: 0.6,
        explanation: 'Sample payloads'
      },
      tests: {
        suggestions: [
          { assertion: 'Status check', path: 'status', expected: 200 },
          { assertion: 'Has data', path: 'data', type: 'exists' }
        ],
        confidence: 0.65,
        explanation: 'Basic test assertions'
      }
    };
    
    return fallbacks[type] || { suggestions: [], confidence: 0.5 };
  };

  const getIcon = () => {
    switch (type) {
      case 'headers': return <Zap className="w-4 h-4" />;
      case 'security': return <Shield className="w-4 h-4" />;
      case 'error-fix': return <AlertCircle className="w-4 h-4" />;
      case 'optimization': return <TrendingUp className="w-4 h-4" />;
      case 'tests': return <CheckCircle className="w-4 h-4" />;
      default: return <Sparkles className="w-4 h-4" />;
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.6) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const renderSuggestion = (suggestion, index) => {
    const isApplied = appliedSuggestions.has(index);
    
    return (
      <div 
        key={index}
        className={`p-3 rounded-lg border transition-all ${
          isApplied 
            ? 'bg-green-50 border-green-200' 
            : 'bg-gray-50 border-gray-200 hover:bg-blue-50 hover:border-blue-200'
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {type === 'headers' && (
              <>
                <div className="font-mono text-sm font-semibold text-gray-900">
                  {suggestion.header}: {suggestion.value}
                </div>
                <div className="text-xs text-gray-600 mt-1">{suggestion.description}</div>
              </>
            )}
            
            {type === 'payload' && (
              <>
                <div className="text-sm font-semibold text-gray-900">{suggestion.scenario}</div>
                <pre className="text-xs bg-gray-900 text-gray-100 p-2 rounded mt-1 overflow-x-auto">
                  {JSON.stringify(suggestion.payload, null, 2)}
                </pre>
                <div className="text-xs text-gray-600 mt-1">{suggestion.description}</div>
              </>
            )}
            
            {type === 'tests' && (
              <>
                <div className="text-sm font-semibold text-gray-900">{suggestion.assertion}</div>
                <div className="text-xs font-mono bg-gray-100 p-1 rounded mt-1">
                  {suggestion.path} {suggestion.type || '=='} {suggestion.expected}
                </div>
              </>
            )}
            
            {type === 'error-fix' && (
              <>
                <div className="text-sm font-semibold text-red-600">{suggestion.fix}</div>
                <div className="text-xs text-gray-700 mt-1">{suggestion.action}</div>
                {suggestion.example && (
                  <code className="text-xs bg-gray-100 px-1 py-0.5 rounded inline-block mt-1">
                    {suggestion.example}
                  </code>
                )}
                <div className="text-xs text-gray-500 mt-1">
                  Likelihood: {Math.round((suggestion.likelihood || 0.5) * 100)}%
                </div>
              </>
            )}
            
            {type === 'optimization' && (
              <>
                <div className="text-sm font-semibold text-blue-600">{suggestion.optimization}</div>
                <div className="text-xs text-gray-700 mt-1">{suggestion.implementation}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    suggestion.impact === 'high' ? 'bg-red-100 text-red-700' :
                    suggestion.impact === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {suggestion.impact} impact
                  </span>
                  <span className="text-xs text-gray-500">
                    ~{suggestion.estimated_improvement} improvement
                  </span>
                </div>
              </>
            )}
            
            {type === 'security' && (
              <>
                <div className="text-sm font-semibold text-purple-600">{suggestion.issue}</div>
                <div className="text-xs text-gray-700 mt-1">{suggestion.fix}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    suggestion.severity === 'critical' ? 'bg-red-100 text-red-700' :
                    suggestion.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                    suggestion.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {suggestion.severity}
                  </span>
                  <span className="text-xs text-gray-500">{suggestion.reference}</span>
                </div>
              </>
            )}
          </div>
          
          {!isApplied && onApplySuggestion && (
            <button
              onClick={() => handleApplySuggestion(suggestion, index)}
              className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Apply
            </button>
          )}
          
          {isApplied && (
            <CheckCircle className="w-4 h-4 text-green-500 ml-2" />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="relative inline-block">
      {/* Trigger Button */}
      <button
        onClick={trigger === 'click' ? handleTrigger : undefined}
        onMouseEnter={trigger === 'hover' ? () => setIsVisible(true) : undefined}
        onMouseLeave={trigger === 'hover' ? () => setIsVisible(false) : undefined}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
          suggestions && suggestions.suggestions?.length > 0
            ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white animate-pulse'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        {loading ? (
          <div className="animate-spin">
            <Sparkles className="w-4 h-4" />
          </div>
        ) : (
          getIcon()
        )}
        <span>AI Suggestions</span>
        {suggestions && suggestions.suggestions?.length > 0 && (
          <span className="bg-white/20 px-1.5 py-0.5 rounded text-xs">
            {suggestions.suggestions.length}
          </span>
        )}
      </button>

      {/* Suggestions Popup */}
      {isVisible && (
        <div 
          className={`absolute z-50 mt-2 w-96 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden ${
            position === 'left' ? 'right-0' : 'left-0'
          }`}
          onMouseEnter={trigger === 'hover' ? () => setIsVisible(true) : undefined}
          onMouseLeave={trigger === 'hover' ? () => setIsVisible(false) : undefined}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                <h3 className="font-semibold">AI-Powered Suggestions</h3>
              </div>
              {suggestions && (
                <div className={`text-xs ${getConfidenceColor(suggestions.confidence)}`}>
                  {Math.round((suggestions.confidence || 0) * 100)}% confidence
                </div>
              )}
            </div>
            {suggestions?.explanation && (
              <p className="text-xs text-white/90 mt-1">{suggestions.explanation}</p>
            )}
          </div>

          {/* Content */}
          <div className="p-4 max-h-96 overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin">
                  <Sparkles className="w-8 h-8 text-blue-500" />
                </div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-500 mt-0.5" />
                  <div>
                    <div className="text-sm font-medium text-red-800">Error loading suggestions</div>
                    <div className="text-xs text-red-600 mt-1">{error}</div>
                  </div>
                </div>
              </div>
            )}

            {suggestions && suggestions.suggestions && suggestions.suggestions.length > 0 ? (
              <div className="space-y-2">
                {suggestions.suggestions.map((suggestion, index) => renderSuggestion(suggestion, index))}
              </div>
            ) : (
              !loading && !error && (
                <div className="text-center py-8 text-gray-500">
                  <Lightbulb className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No suggestions available</p>
                </div>
              )
            )}
          </div>

          {/* Footer */}
          {suggestions && suggestions.suggestions && suggestions.suggestions.length > 0 && (
            <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  Powered by AI • Better than Postman
                </span>
                {appliedSuggestions.size > 0 && (
                  <span className="text-xs text-green-600">
                    {appliedSuggestions.size} applied
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AISuggestions;