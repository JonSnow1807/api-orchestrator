import React, { useState, useEffect, useRef } from 'react';
import { 
  Zap, Activity, Code, FileSearch, TestTube, Shield, 
  Sparkles, Terminal, CheckCircle, AlertCircle, Loader,
  Download, Github, Upload, Brain, Rocket
} from 'lucide-react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [sourcePath, setSourcePath] = useState('src');
  const [isOrchestrating, setIsOrchestrating] = useState(false);
  const [stats, setStats] = useState({ apis: 0, specs: 0, tests: 0 });
  const [currentPhase, setCurrentPhase] = useState('');
  const [taskId, setTaskId] = useState(null);
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      setConnected(true);
      addMessage('Connected to API Orchestrator', 'success');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
      setConnected(false);
      addMessage('Disconnected from server', 'error');
    };
    
    socketRef.current = ws;
    
    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleWebSocketMessage = (data) => {
    switch(data.type) {
      case 'progress':
        setCurrentPhase(data.stage);
        addMessage(data.message, 'info');
        break;
      case 'discovery_complete':
        setStats(prev => ({ ...prev, apis: data.apis_found }));
        addMessage(`Found ${data.apis_found} API endpoints`, 'discovery');
        break;
      case 'spec_complete':
        setStats(prev => ({ ...prev, specs: data.paths }));
        addMessage(`Generated ${data.paths} OpenAPI paths`, 'spec');
        break;
      case 'tests_complete':
        setStats(prev => ({ ...prev, tests: data.tests_generated }));
        addMessage(`Created ${data.tests_generated} test suites`, 'test');
        break;
      case 'orchestration_complete':
        setIsOrchestrating(false);
        setCurrentPhase('complete');
        setTaskId(data.task_id);
        addMessage('✨ Orchestration complete!', 'success');
        break;
      case 'error':
        setIsOrchestrating(false);
        addMessage(`Error: ${data.error}`, 'error');
        break;
    }
  };

  const addMessage = (text, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev, { text, type, timestamp }]);
  };

  const startOrchestration = async () => {
    if (!sourcePath) return;
    
    setIsOrchestrating(true);
    setStats({ apis: 0, specs: 0, tests: 0 });
    setMessages([]);
    setCurrentPhase('starting');
    
    try {
      const response = await fetch(`${API_URL}/api/orchestrate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_type: 'directory',
          source_path: sourcePath
        })
      });
      
      const data = await response.json();
      setTaskId(data.task_id);
      addMessage(`Task started: ${data.task_id}`, 'info');
    } catch (error) {
      addMessage(`Failed to start: ${error.message}`, 'error');
      setIsOrchestrating(false);
    }
  };

  const agents = [
    { 
      id: 'discovery', 
      name: 'Discovery Agent', 
      icon: FileSearch, 
      description: 'Scanning codebase for API endpoints',
      active: currentPhase === 'discovery'
    },
    { 
      id: 'spec', 
      name: 'Spec Generator', 
      icon: Code, 
      description: 'Creating OpenAPI specifications',
      active: currentPhase === 'spec_generation'
    },
    { 
      id: 'test', 
      name: 'Test Generator', 
      icon: TestTube, 
      description: 'Generating comprehensive test suites',
      active: currentPhase === 'test_generation'
    },
    { 
      id: 'ai', 
      name: 'AI Enhancer', 
      icon: Brain, 
      description: 'Adding intelligence to your APIs',
      active: false
    }
  ];

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <Rocket size={32} style={{ color: '#a855f7' }} />
            <h1 className="logo">API Orchestrator AI</h1>
            <span className="status-badge" style={{ background: 'rgba(250, 204, 21, 0.2)', color: '#facc15', border: '1px solid rgba(250, 204, 21, 0.5)' }}>
              Next-Gen
            </span>
          </div>
          
          <div className={`status-badge ${connected ? 'connected' : 'disconnected'}`}>
            <Activity size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            {connected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        
        {/* Control Panel */}
        <div className="card">
          <h2>
            <Zap size={20} style={{ color: '#facc15' }} />
            Command Center
          </h2>
          
          <div className="input-group">
            <label>Source Path</label>
            <input
              type="text"
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
              placeholder="Enter path..."
            />
          </div>
          
          <button
            className="btn-primary"
            onClick={startOrchestration}
            disabled={isOrchestrating || !connected}
          >
            {isOrchestrating ? (
              <>
                <Loader size={20} className="spinner" />
                <span>Orchestrating...</span>
              </>
            ) : (
              <>
                <Sparkles size={20} />
                <span>Start AI Orchestration</span>
              </>
            )}
          </button>

          <div className="btn-group">
            <button className="btn-secondary">
              <Github size={16} style={{ display: 'inline', marginRight: '0.25rem' }} />
              GitHub
            </button>
            <button className="btn-secondary">
              <Upload size={16} style={{ display: 'inline', marginRight: '0.25rem' }} />
              Upload
            </button>
          </div>

          {/* Stats */}
          <div style={{ marginTop: '2rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Statistics</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">APIs Found</span>
                <span className="stat-value">{stats.apis}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Specs Generated</span>
                <span className="stat-value">{stats.specs}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Tests Created</span>
                <span className="stat-value">{stats.tests}</span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Agents */}
        <div className="card">
          <h2>AI Agents</h2>
          <div className="agents-list">
            {agents.map((agent) => {
              const Icon = agent.icon;
              return (
                <div
                  key={agent.id}
                  className={`agent-card ${agent.active ? 'active' : ''}`}
                >
                  <div className="agent-header">
                    <div className="agent-info">
                      <Icon size={24} />
                      <div>
                        <div className="agent-name">{agent.name}</div>
                        <div className="agent-desc">{agent.description}</div>
                      </div>
                    </div>
                    {agent.active && (
                      <Loader size={20} className="spinner" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Feed */}
        <div className="card">
          <h2>
            <Terminal size={20} />
            Live Feed
          </h2>
          
          <div className="messages-container">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`message message-${msg.type}`}
              >
                <div className="message-time">[{msg.timestamp}]</div>
                <div className="message-text">{msg.text}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Bottom Action Bar */}
      {currentPhase === 'complete' && taskId && (
        <div style={{ 
          margin: '2rem auto', 
          maxWidth: '1400px', 
          padding: '0 2rem' 
        }}>
          <div className="card" style={{
            background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2))',
            border: '1px solid rgba(34, 197, 94, 0.5)'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center' 
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <CheckCircle size={24} style={{ color: '#22c55e' }} />
                <div>
                  <div style={{ fontWeight: '600' }}>Orchestration Complete!</div>
                  <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                    Your API artifacts are ready
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <a
                  href={`${API_URL}/api/download/${taskId}/spec`}
                  className="btn-secondary"
                  style={{ 
                    padding: '0.5rem 1rem',
                    textDecoration: 'none',
                    color: 'white',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                >
                  <Download size={16} />
                  Download Spec
                </a>
                <a
                  href={`${API_URL}/api/download/${taskId}/tests`}
                  className="btn-secondary"
                  style={{ 
                    padding: '0.5rem 1rem',
                    textDecoration: 'none',
                    color: 'white',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                >
                  <Download size={16} />
                  Download Tests
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;