import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  MessageSquare,
  Send,
  Bot,
  User,
  Sparkles,
  X,
  Minimize2,
  Maximize2,
  Code,
  Shield,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Loader2,
  Lightbulb,
  Zap
} from 'lucide-react';

const AIAssistant = ({ context = null, onSuggestion = null }) => {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: "👋 Hi! I'm your AI assistant. I can help you understand your APIs, suggest improvements, and answer questions about best practices.",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Quick action suggestions based on context
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Generate contextual suggestions
    if (context) {
      if (context.type === 'api_endpoint') {
        setSuggestions([
          "What security issues might this endpoint have?",
          "How can I optimize this endpoint's performance?",
          "Generate test cases for this endpoint",
          "What's the best practice for this type of API?"
        ]);
      } else if (context.type === 'error') {
        setSuggestions([
          "What does this error mean?",
          "How do I fix this issue?",
          "Is this a common problem?",
          "Show me similar examples"
        ]);
      }
    } else {
      setSuggestions([
        "How do I design a RESTful API?",
        "What's the difference between REST and GraphQL?",
        "Help me with API authentication",
        "Review my API design"
      ]);
    }
  }, [context]);

  const sendMessage = async (messageText = input) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Prepare context for AI
      const aiContext = {
        message: messageText,
        context: context,
        history: messages.slice(-5) // Last 5 messages for context
      };

      // Call AI endpoint
      const response = await axios.post(
        getApiUrl('/api/ai-chat'),
        aiContext,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response,
        metadata: response.data.metadata || {},
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If AI provided actionable suggestions, notify parent
      if (response.data.action && onSuggestion) {
        onSuggestion(response.data.action);
      }

    } catch (error) {
      // Fallback responses when AI is not available
      const fallbackResponses = getFallbackResponse(messageText);
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: fallbackResponses,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    }

    setLoading(false);
  };

  const getFallbackResponse = (message) => {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('security')) {
      return "🔒 For API security, consider:\n• Use HTTPS everywhere\n• Implement proper authentication (OAuth2, JWT)\n• Validate all inputs\n• Use rate limiting\n• Keep dependencies updated\n• Never expose sensitive data in responses";
    }
    
    if (lowerMessage.includes('performance')) {
      return "⚡ To optimize API performance:\n• Implement caching strategies\n• Use pagination for large datasets\n• Optimize database queries\n• Consider using CDN for static content\n• Implement compression (gzip)\n• Use connection pooling";
    }
    
    if (lowerMessage.includes('test')) {
      return "🧪 For API testing:\n• Test happy paths and edge cases\n• Include negative test cases\n• Test with different data types\n• Verify error handling\n• Check response times\n• Test concurrent requests";
    }
    
    if (lowerMessage.includes('rest') && lowerMessage.includes('graphql')) {
      return "🔄 REST vs GraphQL:\n\n**REST:**\n• Simple, widely adopted\n• Multiple endpoints\n• Can over/under-fetch data\n• Better for simple CRUD\n\n**GraphQL:**\n• Single endpoint\n• Query exactly what you need\n• Better for complex data relationships\n• Requires more setup";
    }
    
    if (lowerMessage.includes('auth')) {
      return "🔐 API Authentication options:\n• **API Keys**: Simple, good for server-to-server\n• **OAuth 2.0**: Industry standard for user authorization\n• **JWT**: Stateless, scalable, good for microservices\n• **Basic Auth**: Simple but less secure (use HTTPS)\n• **Session-based**: Traditional, stateful";
    }
    
    return "I can help you with:\n• API security analysis\n• Performance optimization\n• Best practices\n• Testing strategies\n• Authentication methods\n• Error handling\n\nWhat would you like to know more about?";
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  const getMessageIcon = (message) => {
    if (message.type === 'user') return <User className="w-4 h-4" />;
    
    // Different icons based on content type
    if (message.metadata?.type === 'security') return <Shield className="w-4 h-4 text-red-400" />;
    if (message.metadata?.type === 'performance') return <TrendingUp className="w-4 h-4 text-green-400" />;
    if (message.metadata?.type === 'suggestion') return <Lightbulb className="w-4 h-4 text-yellow-400" />;
    
    return <Bot className="w-4 h-4 text-purple-400" />;
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 p-4 bg-purple-600 text-white rounded-full shadow-lg hover:bg-purple-700 transition transform hover:scale-110 z-50"
        title="AI Assistant"
      >
        <div className="relative">
          <Sparkles className="w-6 h-6" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
        </div>
      </button>
    );
  }

  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 bg-gray-800 rounded-lg shadow-2xl z-50 border border-gray-700">
        <div className="flex items-center justify-between p-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <span className="text-white font-medium">AI Assistant</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMinimized(false)}
              className="text-gray-400 hover:text-white transition"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-gray-800 rounded-lg shadow-2xl z-50 border border-gray-700 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <span className="text-white font-medium">AI Assistant</span>
          <span className="px-2 py-0.5 bg-purple-600/20 text-purple-400 text-xs rounded-full">Beta</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(true)}
            className="text-gray-400 hover:text-white transition"
          >
            <Minimize2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 bg-purple-600/20 rounded-lg flex items-center justify-center">
                {getMessageIcon(message)}
              </div>
            )}
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                message.type === 'user'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-200'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <span className="text-xs opacity-60 mt-1 block">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>
            {message.type === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 bg-purple-600/20 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-purple-400" />
            </div>
            <div className="bg-gray-700 text-gray-200 p-3 rounded-lg">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && messages.length === 1 && (
        <div className="px-4 py-2 border-t border-gray-700">
          <p className="text-xs text-gray-400 mb-2">Suggested questions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.slice(0, 3).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="text-xs px-3 py-1.5 bg-gray-700 text-gray-300 rounded-full hover:bg-gray-600 transition"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !loading && sendMessage()}
            placeholder="Ask me anything about APIs..."
            className="flex-1 px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none text-sm"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">
          Powered by AI • Responses are suggestions
        </p>
      </div>
    </div>
  );
};

export default AIAssistant;