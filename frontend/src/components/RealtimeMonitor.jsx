import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Activity,
  CheckCircle,
  AlertCircle,
  Loader2,
  Terminal,
  Info,
  XCircle,
  Clock,
  Zap,
  Shield,
  TestTube,
  Server,
  Brain,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

const RealtimeMonitor = ({ taskId, onComplete }) => {
  const { token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('connecting');
  const [currentPhase, setCurrentPhase] = useState('');
  const [progress, setProgress] = useState(0);
  const [expandedMessages, setExpandedMessages] = useState({});
  const [autoScroll, setAutoScroll] = useState(true);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const phaseIcons = {
    discovery: <Zap className="w-5 h-5 text-blue-500" />,
    specs: <Terminal className="w-5 h-5 text-purple-500" />,
    security: <Shield className="w-5 h-5 text-green-500" />,
    testing: <TestTube className="w-5 h-5 text-yellow-500" />,
    mock: <Server className="w-5 h-5 text-indigo-500" />,
    ai_analysis: <Brain className="w-5 h-5 text-pink-500" />
  };

  const getMessageIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
      case 'progress':
        return <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsHost = window.location.hostname;
    const wsPort = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
    const wsUrl = `${wsProtocol}://${wsHost}:${wsPort}/ws`;

    console.log('Connecting to WebSocket:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setStatus('connected');
      
      // Authenticate
      ws.send(JSON.stringify({
        type: 'auth',
        token: token
      }));

      // Subscribe to task updates if taskId provided
      if (taskId) {
        ws.send(JSON.stringify({
          type: 'subscribe',
          task_id: taskId
        }));
      }

      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setStatus('disconnected');
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('Attempting to reconnect...');
        connectWebSocket();
      }, 3000);
    };
  };

  const handleWebSocketMessage = (data) => {
    const timestamp = new Date().toLocaleTimeString();
    
    // Handle different message types
    switch (data.type) {
      case 'task_update':
        setCurrentPhase(data.phase || '');
        setProgress(data.progress || 0);
        
        const message = {
          id: Date.now() + Math.random(),
          timestamp,
          type: data.status === 'error' ? 'error' : 'info',
          phase: data.phase,
          content: data.message || `${data.phase} ${data.status}`,
          details: data.details || null
        };
        
        setMessages(prev => [...prev, message]);
        
        if (data.status === 'completed') {
          if (onComplete) {
            onComplete(data);
          }
        }
        break;

      case 'agent_message':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          timestamp,
          type: 'info',
          phase: data.agent,
          content: data.message,
          details: data.data || null
        }]);
        break;

      case 'progress':
        setProgress(data.percentage || 0);
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          timestamp,
          type: 'progress',
          content: data.message || `Progress: ${data.percentage}%`
        }]);
        break;

      case 'error':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          timestamp,
          type: 'error',
          content: data.message || 'An error occurred',
          details: data.error || null
        }]);
        break;

      case 'result':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          timestamp,
          type: 'success',
          phase: data.phase,
          content: `${data.phase} completed successfully`,
          details: data.data || null
        }]);
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const toggleMessageExpanded = (messageId) => {
    setExpandedMessages(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  const scrollToBottom = () => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, taskId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Activity className="w-6 h-6 text-indigo-600" />
          <h3 className="text-xl font-semibold text-gray-900">Real-time Monitor</h3>
          {taskId && (
            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              Task: {taskId.slice(0, 8)}...
            </span>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            {status === 'connected' ? (
              <>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-green-600">Connected</span>
              </>
            ) : status === 'connecting' ? (
              <>
                <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
                <span className="text-sm text-gray-500">Connecting...</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 bg-red-500 rounded-full" />
                <span className="text-sm text-red-600">Disconnected</span>
              </>
            )}
          </div>

          {/* Auto-scroll Toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-1 text-sm rounded ${
              autoScroll 
                ? 'bg-indigo-100 text-indigo-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            Auto-scroll {autoScroll ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      {progress > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>{currentPhase || 'Processing'}</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Current Phase */}
      {currentPhase && (
        <div className="mb-4 p-3 bg-indigo-50 rounded-lg flex items-center space-x-2">
          {phaseIcons[currentPhase] || <Activity className="w-5 h-5 text-indigo-500" />}
          <span className="text-sm font-medium text-indigo-700">
            Current Phase: {currentPhase.replace('_', ' ').toUpperCase()}
          </span>
        </div>
      )}

      {/* Messages */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Waiting for updates...</p>
          </div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id}
              className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-start space-x-3">
                {getMessageIcon(message.type)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {message.phase && (
                        <span className="text-xs px-2 py-1 bg-white rounded text-gray-600">
                          {message.phase}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">{message.timestamp}</span>
                    </div>
                    
                    {message.details && (
                      <button
                        onClick={() => toggleMessageExpanded(message.id)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {expandedMessages[message.id] ? 
                          <ChevronDown className="w-4 h-4" /> : 
                          <ChevronRight className="w-4 h-4" />
                        }
                      </button>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-700 mt-1">{message.content}</p>
                  
                  {/* Expanded Details */}
                  {message.details && expandedMessages[message.id] && (
                    <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                      <pre className="text-xs text-gray-600 overflow-x-auto">
                        {typeof message.details === 'object' 
                          ? JSON.stringify(message.details, null, 2)
                          : message.details
                        }
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Actions */}
      <div className="mt-4 flex justify-between items-center">
        <button
          onClick={() => setMessages([])}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Clear Messages
        </button>
        
        {status === 'disconnected' && (
          <button
            onClick={connectWebSocket}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Reconnect
          </button>
        )}
      </div>
    </div>
  );
};

export default RealtimeMonitor;