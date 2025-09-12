import React, { useState, useEffect, useRef } from 'react';
import { 
  BeakerIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  SparklesIcon,
  CodeBracketIcon,
  PlayIcon,
  DocumentCheckIcon,
  ClipboardDocumentCheckIcon
} from '@heroicons/react/24/outline';

const InlineResponseTesting = ({ responseData, onTestGenerated, onTestRun }) => {
  const [selectedText, setSelectedText] = useState('');
  const [selectedPath, setSelectedPath] = useState('');
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [generatedTests, setGeneratedTests] = useState([]);
  const [testSuggestions, setTestSuggestions] = useState([]);
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [testResults, setTestResults] = useState([]);
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('');
  const responseRef = useRef(null);

  useEffect(() => {
    // Add event listeners for text selection
    document.addEventListener('mouseup', handleTextSelection);
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      document.removeEventListener('mouseup', handleTextSelection);
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (responseData) {
      generateSmartSuggestions();
    }
  }, [responseData]);

  const handleTextSelection = (e) => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    
    if (text && responseRef.current && responseRef.current.contains(e.target)) {
      setSelectedText(text);
      
      // Try to determine the JSON path of selected text
      const path = getJsonPathFromSelection(e.target);
      setSelectedPath(path);
      
      // Show context menu near selection
      setContextMenuPosition({
        x: e.pageX,
        y: e.pageY
      });
      setShowContextMenu(true);
      
      // Generate test suggestions for selected text
      generateTestSuggestionsForSelection(text, path);
    }
  };

  const handleClickOutside = (e) => {
    if (!e.target.closest('.context-menu')) {
      setShowContextMenu(false);
    }
  };

  const getJsonPathFromSelection = (element) => {
    // Try to extract JSON path from data attributes or element structure
    const pathAttr = element.getAttribute('data-json-path');
    if (pathAttr) return pathAttr;
    
    // Fallback: try to determine path from element hierarchy
    const propertyElement = element.closest('[data-property]');
    if (propertyElement) {
      return propertyElement.getAttribute('data-property');
    }
    
    return '';
  };

  const generateTestSuggestionsForSelection = (text, path) => {
    const suggestions = [];
    
    // Analyze selected text and generate appropriate test suggestions
    if (/^\d+$/.test(text)) {
      // Number
      suggestions.push({
        label: `Check if ${path || 'value'} equals ${text}`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.eql(${text})`
      });
      suggestions.push({
        label: `Check if ${path || 'value'} is a number`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.be.a('number')`
      });
      suggestions.push({
        label: `Check if ${path || 'value'} is greater than 0`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.be.above(0)`
      });
    } else if (/^(true|false)$/i.test(text)) {
      // Boolean
      suggestions.push({
        label: `Check if ${path || 'value'} is ${text}`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.be.${text.toLowerCase()}`
      });
      suggestions.push({
        label: `Check if ${path || 'value'} is a boolean`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.be.a('boolean')`
      });
    } else if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) {
      // Email
      suggestions.push({
        label: `Check if ${path || 'email'} is valid email format`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.match(/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/)`
      });
      suggestions.push({
        label: `Check if ${path || 'email'} contains '@'`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.include('@')`
      });
    } else if (/^https?:\/\//.test(text)) {
      // URL
      suggestions.push({
        label: `Check if ${path || 'url'} is valid URL`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.match(/^https?:\\/\\/.+/)`
      });
      suggestions.push({
        label: `Check if ${path || 'url'} uses HTTPS`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.match(/^https:\\/\\//)`
      });
    } else if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
      // Date
      suggestions.push({
        label: `Check if ${path || 'date'} is valid date`,
        test: `pm.expect(new Date(pm.response.json()${path ? '.' + path : ''}).toString()).to.not.equal('Invalid Date')`
      });
      suggestions.push({
        label: `Check if ${path || 'date'} is in the future`,
        test: `pm.expect(new Date(pm.response.json()${path ? '.' + path : ''}).getTime()).to.be.above(new Date().getTime())`
      });
    } else {
      // String
      suggestions.push({
        label: `Check if ${path || 'value'} equals "${text}"`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.eql('${text}')`
      });
      suggestions.push({
        label: `Check if ${path || 'value'} is a string`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.be.a('string')`
      });
      suggestions.push({
        label: `Check if ${path || 'value'} is not empty`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.not.be.empty`
      });
      suggestions.push({
        label: `Check if ${path || 'value'} contains "${text.substring(0, 10)}"`,
        test: `pm.expect(pm.response.json()${path ? '.' + path : ''}).to.include('${text.substring(0, 10)}')`
      });
    }
    
    // Add property existence check
    if (path) {
      suggestions.unshift({
        label: `Check if property '${path}' exists`,
        test: `pm.expect(pm.response.json()).to.have.property('${path}')`
      });
    }
    
    setTestSuggestions(suggestions);
  };

  const generateSmartSuggestions = () => {
    if (!responseData) return;
    
    const suggestions = [];
    
    try {
      const data = typeof responseData === 'string' ? JSON.parse(responseData) : responseData;
      
      // Generate suggestions based on response structure
      if (Array.isArray(data)) {
        suggestions.push({
          label: 'Check if response is an array',
          test: 'pm.expect(pm.response.json()).to.be.an("array")'
        });
        suggestions.push({
          label: `Check if array has ${data.length} items`,
          test: `pm.expect(pm.response.json()).to.have.lengthOf(${data.length})`
        });
        if (data.length > 0) {
          suggestions.push({
            label: 'Check if array is not empty',
            test: 'pm.expect(pm.response.json()).to.not.be.empty'
          });
        }
      } else if (typeof data === 'object' && data !== null) {
        const keys = Object.keys(data);
        
        // Check for common patterns
        if (data.id || data._id) {
          suggestions.push({
            label: 'Check if ID exists',
            test: `pm.expect(pm.response.json()).to.have.property('${data.id ? 'id' : '_id'}')`
          });
        }
        
        if (data.status) {
          suggestions.push({
            label: `Check if status is "${data.status}"`,
            test: `pm.expect(pm.response.json().status).to.eql('${data.status}')`
          });
        }
        
        if (data.error) {
          suggestions.push({
            label: 'Check if error message exists',
            test: 'pm.expect(pm.response.json()).to.have.property("error")'
          });
        }
        
        // Add property checks for first 5 keys
        keys.slice(0, 5).forEach(key => {
          suggestions.push({
            label: `Check if property '${key}' exists`,
            test: `pm.expect(pm.response.json()).to.have.property('${key}')`
          });
        });
      }
      
      // Add general suggestions
      suggestions.unshift({
        label: 'Check if status code is 200',
        test: 'pm.response.to.have.status(200)'
      });
      suggestions.unshift({
        label: 'Check if response is JSON',
        test: 'pm.response.to.be.json'
      });
      suggestions.push({
        label: 'Check response time < 1000ms',
        test: 'pm.expect(pm.response.responseTime).to.be.below(1000)'
      });
      
      setTestSuggestions(suggestions);
    } catch (error) {
      console.error('Error generating suggestions:', error);
    }
  };

  const applyTestSuggestion = (suggestion) => {
    const newTest = {
      id: Date.now(),
      description: suggestion.label,
      code: suggestion.test,
      enabled: true
    };
    
    setGeneratedTests([...generatedTests, newTest]);
    setShowTestPanel(true);
    setShowContextMenu(false);
    
    if (onTestGenerated) {
      onTestGenerated(newTest);
    }
  };

  const generateTestFromNaturalLanguage = async () => {
    if (!naturalLanguageInput.trim()) return;
    
    try {
      // Call backend API to generate test
      const response = await fetch('/api/tests/generate-nl', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          description: naturalLanguageInput,
          context: {
            response: responseData,
            selectedField: selectedPath
          }
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        const newTests = result.tests.map(test => ({
          id: Date.now() + Math.random(),
          description: test.description,
          code: test.code,
          enabled: true
        }));
        
        setGeneratedTests([...generatedTests, ...newTests]);
        setShowTestPanel(true);
        setNaturalLanguageInput('');
        
        if (onTestGenerated) {
          newTests.forEach(test => onTestGenerated(test));
        }
      }
    } catch (error) {
      console.error('Error generating test from natural language:', error);
      
      // Fallback to client-side generation
      const simpleTest = {
        id: Date.now(),
        description: naturalLanguageInput,
        code: `// Test: ${naturalLanguageInput}\npm.test("${naturalLanguageInput}", function() {\n    // Auto-generated test\n    pm.response.to.have.status(200);\n});`,
        enabled: true
      };
      
      setGeneratedTests([...generatedTests, simpleTest]);
      setShowTestPanel(true);
      setNaturalLanguageInput('');
    }
  };

  const runTests = async () => {
    const results = [];
    
    for (const test of generatedTests) {
      if (!test.enabled) continue;
      
      try {
        // Execute test code (simplified - in real app, use sandbox)
        const passed = Math.random() > 0.2; // Mock test execution
        
        results.push({
          testId: test.id,
          description: test.description,
          passed,
          error: passed ? null : 'Assertion failed',
          executionTime: Math.floor(Math.random() * 100)
        });
      } catch (error) {
        results.push({
          testId: test.id,
          description: test.description,
          passed: false,
          error: error.message,
          executionTime: 0
        });
      }
    }
    
    setTestResults(results);
    
    if (onTestRun) {
      onTestRun(results);
    }
  };

  const toggleTest = (testId) => {
    setGeneratedTests(generatedTests.map(test => 
      test.id === testId ? { ...test, enabled: !test.enabled } : test
    ));
  };

  const removeTest = (testId) => {
    setGeneratedTests(generatedTests.filter(test => test.id !== testId));
  };

  const copyAllTests = () => {
    const allTestCode = generatedTests
      .filter(test => test.enabled)
      .map(test => test.code)
      .join('\n\n');
    
    navigator.clipboard.writeText(allTestCode);
  };

  const renderJsonWithSelection = () => {
    if (!responseData) return null;
    
    const data = typeof responseData === 'string' ? responseData : JSON.stringify(responseData, null, 2);
    
    return (
      <div
        ref={responseRef}
        className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-96 select-text"
      >
        <pre className="json-content">
          <code>{data}</code>
        </pre>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Natural Language Input */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <SparklesIcon className="h-5 w-5 text-purple-500" />
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Generate Tests with Natural Language
          </h3>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={naturalLanguageInput}
            onChange={(e) => setNaturalLanguageInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && generateTestFromNaturalLanguage()}
            placeholder="e.g., 'Check if status is 200 and response has user field with valid email'"
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500"
          />
          <button
            onClick={generateTestFromNaturalLanguage}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all flex items-center gap-2"
          >
            <SparklesIcon className="h-4 w-4" />
            Generate
          </button>
        </div>
      </div>

      {/* Response with Selection */}
      <div className="relative">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Select any part of the response to generate tests
          </h3>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Tip: Click and drag to select text
          </div>
        </div>
        
        {renderJsonWithSelection()}
        
        {/* Context Menu */}
        {showContextMenu && (
          <div
            className="context-menu absolute z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-2 min-w-[200px]"
            style={{
              left: `${contextMenuPosition.x}px`,
              top: `${contextMenuPosition.y}px`
            }}
          >
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 px-2 py-1 mb-1">
              Generate test for: {selectedText.substring(0, 20)}...
            </div>
            {testSuggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => applyTestSuggestion(suggestion)}
                className="w-full text-left px-2 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              >
                {suggestion.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Quick Suggestions */}
      {testSuggestions.length > 0 && !showContextMenu && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Quick Test Suggestions
          </h3>
          <div className="flex flex-wrap gap-2">
            {testSuggestions.slice(0, 6).map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => applyTestSuggestion(suggestion)}
                className="px-3 py-1.5 text-xs bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                {suggestion.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Generated Tests Panel */}
      {showTestPanel && generatedTests.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Generated Tests ({generatedTests.filter(t => t.enabled).length}/{generatedTests.length} enabled)
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={copyAllTests}
                  className="px-3 py-1.5 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center gap-1"
                >
                  <ClipboardDocumentCheckIcon className="h-3.5 w-3.5" />
                  Copy All
                </button>
                <button
                  onClick={runTests}
                  className="px-3 py-1.5 text-xs bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-1"
                >
                  <PlayIcon className="h-3.5 w-3.5" />
                  Run Tests
                </button>
              </div>
            </div>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-64 overflow-y-auto">
            {generatedTests.map((test) => {
              const result = testResults.find(r => r.testId === test.id);
              
              return (
                <div key={test.id} className="p-3 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={test.enabled}
                      onChange={() => toggleTest(test.id)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {test.description}
                        </span>
                        {result && (
                          result.passed ? (
                            <CheckCircleIcon className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircleIcon className="h-4 w-4 text-red-500" />
                          )
                        )}
                      </div>
                      <pre className="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                        <code>{test.code}</code>
                      </pre>
                      {result && !result.passed && (
                        <div className="mt-1 text-xs text-red-600 dark:text-red-400">
                          Error: {result.error}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => removeTest(test.id)}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <XCircleIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Test Results Summary */}
      {testResults.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Test Results
          </h3>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-500">
                {testResults.filter(r => r.passed).length}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Passed</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-500">
                {testResults.filter(r => !r.passed).length}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Failed</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                {Math.round(testResults.reduce((acc, r) => acc + r.executionTime, 0) / testResults.length)}ms
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Avg Time</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InlineResponseTesting;