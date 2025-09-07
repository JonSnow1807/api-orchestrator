import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import {
  Code2,
  Play,
  Copy,
  Check,
  FileCode,
  Loader2,
  Sparkles,
  ChevronDown,
  Terminal
} from 'lucide-react';

const CodeEditor = ({ onOrchestrationStart }) => {
  const { token } = useAuth();
  const [code, setCode] = useState('');
  const [framework, setFramework] = useState('auto');
  const [fileName, setFileName] = useState('api.py');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [showFrameworks, setShowFrameworks] = useState(false);

  const frameworks = [
    { value: 'auto', label: 'Auto-detect', icon: <Sparkles className="w-4 h-4" /> },
    { value: 'fastapi', label: 'FastAPI', icon: <Code2 className="w-4 h-4" /> },
    { value: 'flask', label: 'Flask', icon: <FileCode className="w-4 h-4" /> },
    { value: 'django', label: 'Django', icon: <Terminal className="w-4 h-4" /> }
  ];

  const sampleCode = {
    fastapi: `from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str
    price: float

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
def create_item(item: Item):
    return item`,
    
    flask: `from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Hello World"})

@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        return jsonify({"users": []})
    else:
        return jsonify({"created": True})

@app.route('/users/<int:user_id>')
def get_user(user_id):
    return jsonify({"user_id": user_id})`,
    
    django: `from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET', 'POST'])
def products(request):
    if request.method == 'GET':
        return Response({"products": []})
    return Response({"created": True})

@api_view(['GET', 'PUT', 'DELETE'])
def product_detail(request, pk):
    return Response({"id": pk})

urlpatterns = [
    path('api/products/', products),
    path('api/products/<int:pk>/', product_detail),
]`
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const loadSample = (fw) => {
    setCode(sampleCode[fw] || '');
    setFramework(fw);
    setFileName(`sample_${fw}_api.py`);
    setMessage({ type: 'info', text: `Loaded ${fw} sample code` });
  };

  const handleOrchestrate = async () => {
    if (!code.trim()) {
      setMessage({ type: 'error', text: 'Please enter some code' });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await axios.post('/api/orchestrate', {
        source_type: 'code',
        source_path: fileName,
        code_content: code,
        options: {
          framework: framework === 'auto' ? null : framework
        }
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.task_id) {
        setMessage({ type: 'success', text: 'Orchestration started successfully!' });
        if (onOrchestrationStart) {
          onOrchestrationStart(response.data.task_id);
        }
        // Clear code after successful submission
        setCode('');
      }
    } catch (error) {
      console.error('Orchestration error:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to start orchestration' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Code2 className="w-6 h-6 text-indigo-600" />
          <h3 className="text-xl font-semibold text-gray-900">Code Editor</h3>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Framework Selector */}
          <div className="relative">
            <button
              onClick={() => setShowFrameworks(!showFrameworks)}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              {frameworks.find(f => f.value === framework)?.icon}
              <span className="text-sm font-medium">
                {frameworks.find(f => f.value === framework)?.label}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {showFrameworks && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                {frameworks.map(fw => (
                  <button
                    key={fw.value}
                    onClick={() => {
                      setFramework(fw.value);
                      setShowFrameworks(false);
                    }}
                    className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-gray-50 transition-colors"
                  >
                    {fw.icon}
                    <span className="text-sm">{fw.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={handleCopy}
            className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-5 h-5 text-green-600" /> : <Copy className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* File Name Input */}
      <div className="mb-4">
        <input
          type="text"
          value={fileName}
          onChange={(e) => setFileName(e.target.value)}
          placeholder="filename.py"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
      </div>

      {/* Code Editor */}
      <div className="relative mb-4">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="# Paste your API code here or load a sample below..."
          className="w-full h-96 px-4 py-3 font-mono text-sm bg-gray-900 text-gray-100 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
          spellCheck={false}
        />
        
        {/* Line Numbers (optional enhancement) */}
        <div className="absolute top-0 left-0 py-3 px-2 text-gray-500 text-sm font-mono pointer-events-none">
          {code.split('\n').map((_, i) => (
            <div key={i} className="leading-6">{i + 1}</div>
          ))}
        </div>
      </div>

      {/* Sample Code Buttons */}
      <div className="flex items-center space-x-2 mb-4">
        <span className="text-sm text-gray-600">Load sample:</span>
        {Object.keys(sampleCode).map(fw => (
          <button
            key={fw}
            onClick={() => loadSample(fw)}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors capitalize"
          >
            {fw}
          </button>
        ))}
      </div>

      {/* Message Display */}
      {message.text && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.type === 'error' ? 'bg-red-50 text-red-700' :
          message.type === 'success' ? 'bg-green-50 text-green-700' :
          'bg-blue-50 text-blue-700'
        }`}>
          {message.text}
        </div>
      )}

      {/* Orchestrate Button */}
      <button
        onClick={handleOrchestrate}
        disabled={loading || !code.trim()}
        className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Processing...</span>
          </>
        ) : (
          <>
            <Play className="w-5 h-5" />
            <span>Start Orchestration</span>
          </>
        )}
      </button>

      {/* Features Info */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Features:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Auto-detects FastAPI, Flask, and Django frameworks</li>
          <li>• Discovers all API endpoints automatically</li>
          <li>• Generates OpenAPI specifications</li>
          <li>• Creates test suites (Pytest, Postman)</li>
          <li>• Provides instant mock servers</li>
        </ul>
      </div>
    </div>
  );
};

export default CodeEditor;