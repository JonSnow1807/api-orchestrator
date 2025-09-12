import React, { useState, useEffect } from 'react';
import { API_CONFIG, API_ENDPOINTS } from '../config/api';
import { BeakerIcon, SparklesIcon, CodeBracketIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const NaturalLanguageTesting = ({ responseData, onTestGenerated, onTestRun }) => {
  const [naturalLanguage, setNaturalLanguage] = useState('');
  const [generatedTests, setGeneratedTests] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState({});
  const [activeCategory, setActiveCategory] = useState('all');

  const testCategories = {
    all: 'All Tests',
    status: 'Status Codes',
    performance: 'Performance',
    security: 'Security',
    data: 'Data Validation',
    auth: 'Authentication',
    crud: 'CRUD Operations',
    error: 'Error Handling'
  };

  const commonTestPatterns = [
    { text: 'Check if status is 200', category: 'status' },
    { text: 'Response time should be less than 1 second', category: 'performance' },
    { text: 'Response should contain valid email', category: 'data' },
    { text: 'Array should not be empty', category: 'data' },
    { text: 'Check for SQL injection vulnerabilities', category: 'security' },
    { text: 'Verify authentication is required', category: 'auth' },
    { text: 'Test rate limiting is enforced', category: 'security' },
    { text: 'Validate all required fields are present', category: 'data' }
  ];

  useEffect(() => {
    // Load AI suggestions when component mounts
    fetchSuggestions();
  }, [responseData]);

  const fetchSuggestions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.NATURAL_LANGUAGE}/suggestions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  };

  const generateTests = async () => {
    if (!naturalLanguage.trim()) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.NATURAL_LANGUAGE}/generate-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          description: naturalLanguage,
          context: responseData
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGeneratedTests(data.tests || []);
        if (onTestGenerated) {
          onTestGenerated(data.tests);
        }
      }
    } catch (error) {
      console.error('Failed to generate tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateFromResponse = async () => {
    if (!responseData) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.NATURAL_LANGUAGE}/generate-from-response`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          response: responseData,
          test_types: ['status', 'schema', 'data', 'performance']
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGeneratedTests(data.test_suite || []);
        if (onTestGenerated) {
          onTestGenerated(data.test_suite);
        }
      }
    } catch (error) {
      console.error('Failed to generate tests from response:', error);
    } finally {
      setLoading(false);
    }
  };

  const runTest = async (test, index) => {
    try {
      // Execute the test code
      const testFunction = new Function('pm', 'response', test.code);
      const pm = {
        test: (name, callback) => {
          try {
            callback();
            setTestResults(prev => ({
              ...prev,
              [index]: { passed: true, name }
            }));
          } catch (error) {
            setTestResults(prev => ({
              ...prev,
              [index]: { passed: false, name, error: error.message }
            }));
          }
        },
        expect: (value) => ({
          to: {
            equal: (expected) => {
              if (value !== expected) {
                throw new Error(`Expected ${expected} but got ${value}`);
              }
            },
            be: {
              above: (threshold) => {
                if (value <= threshold) {
                  throw new Error(`Expected ${value} to be above ${threshold}`);
                }
              },
              below: (threshold) => {
                if (value >= threshold) {
                  throw new Error(`Expected ${value} to be below ${threshold}`);
                }
              }
            },
            match: (pattern) => {
              if (!pattern.test(value)) {
                throw new Error(`Value does not match pattern ${pattern}`);
              }
            },
            have: {
              property: (prop) => {
                if (!(prop in value)) {
                  throw new Error(`Property ${prop} not found`);
                }
              }
            }
          }
        }),
        response: responseData
      };
      
      testFunction(pm, responseData);
      
      if (onTestRun) {
        onTestRun(test, testResults[index]);
      }
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [index]: { passed: false, error: error.message }
      }));
    }
  };

  const runAllTests = () => {
    generatedTests.forEach((test, index) => {
      runTest(test, index);
    });
  };

  const useSuggestion = (suggestion) => {
    setNaturalLanguage(suggestion);
  };

  const filteredTests = activeCategory === 'all' 
    ? generatedTests 
    : generatedTests.filter(test => test.category === activeCategory);

  return (
    <div className="space-y-6">
      {/* Natural Language Input */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <SparklesIcon className="h-5 w-5 text-purple-400 mr-2" />
          <h3 className="text-lg font-semibold text-white">Natural Language Test Generation</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Describe your test in plain English
            </label>
            <textarea
              value={naturalLanguage}
              onChange={(e) => setNaturalLanguage(e.target.value)}
              placeholder="e.g., Check if status is 200 and response contains valid email..."
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              rows="3"
            />
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={generateTests}
              disabled={loading || !naturalLanguage.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <CodeBracketIcon className="h-4 w-4 mr-2" />
              Generate Tests
            </button>
            
            {responseData && (
              <button
                onClick={generateFromResponse}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <BeakerIcon className="h-4 w-4 mr-2" />
                Auto-Generate from Response
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Test Suggestions */}
      {suggestions.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h4 className="text-sm font-medium text-gray-300 mb-3">AI Suggestions</h4>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => useSuggestion(suggestion.text)}
                className="px-3 py-1 bg-gray-700 text-gray-300 rounded-full text-sm hover:bg-gray-600 transition-colors"
              >
                {suggestion.text}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Common Test Patterns */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h4 className="text-sm font-medium text-gray-300 mb-3">Common Test Patterns</h4>
        <div className="grid grid-cols-2 gap-2">
          {commonTestPatterns.map((pattern, index) => (
            <button
              key={index}
              onClick={() => useSuggestion(pattern.text)}
              className="px-3 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm hover:bg-gray-600 transition-colors text-left"
            >
              <span className="text-xs text-gray-500">{testCategories[pattern.category]}</span>
              <div>{pattern.text}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Generated Tests */}
      {generatedTests.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Generated Tests</h3>
            <button
              onClick={runAllTests}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center"
            >
              <BeakerIcon className="h-4 w-4 mr-2" />
              Run All Tests
            </button>
          </div>

          {/* Category Tabs */}
          <div className="flex space-x-2 mb-4 overflow-x-auto">
            {Object.entries(testCategories).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setActiveCategory(key)}
                className={`px-3 py-1 rounded-lg text-sm whitespace-nowrap ${
                  activeCategory === key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Test List */}
          <div className="space-y-3">
            {filteredTests.map((test, index) => (
              <div key={index} className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h4 className="text-white font-medium">{test.name}</h4>
                      {testResults[index] && (
                        <span className="ml-2">
                          {testResults[index].passed ? (
                            <CheckCircleIcon className="h-5 w-5 text-green-500" />
                          ) : (
                            <XCircleIcon className="h-5 w-5 text-red-500" />
                          )}
                        </span>
                      )}
                    </div>
                    {test.description && (
                      <p className="text-gray-400 text-sm mb-2">{test.description}</p>
                    )}
                    <pre className="bg-gray-800 rounded p-2 text-xs text-gray-300 overflow-x-auto">
                      <code>{test.code}</code>
                    </pre>
                    {testResults[index]?.error && (
                      <div className="mt-2 text-red-400 text-sm">
                        Error: {testResults[index].error}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => runTest(test, index)}
                    className="ml-4 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                  >
                    Run
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NaturalLanguageTesting;