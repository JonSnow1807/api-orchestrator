/**
 * Collaboration Hook
 * Custom hook for managing real-time collaboration features via WebSocket
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';

export const useCollaboration = (workspaceId, resourceId = null) => {
  const { user, token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [activeUsers, setActiveUsers] = useState([]);
  const [userPresence, setUserPresence] = useState({});
  const [resourceLocks, setResourceLocks] = useState({});
  const [collaborationCursors, setCollaborationCursors] = useState({});
  const [typingUsers, setTypingUsers] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const currentResourceRef = useRef(resourceId);
  
  // Update current resource ref when resourceId changes
  useEffect(() => {
    currentResourceRef.current = resourceId;
  }, [resourceId]);

  const connect = useCallback(() => {
    if (!workspaceId || !token || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      setConnectionStatus('connecting');
      
      // Construct WebSocket URL
      const wsUrl = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/ws/collaboration/${workspaceId}?token=${token}`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('Collaboration WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        
        // Send initial presence update if viewing a resource
        if (currentResourceRef.current) {
          updatePresence({
            status: 'active',
            current_resource: currentResourceRef.current,
            resource_type: 'project' // or determine dynamically
          });
        }
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = (event) => {
        console.log('Collaboration WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Clear state
        setActiveUsers([]);
        setUserPresence({});
        setResourceLocks({});
        setCollaborationCursors({});
        setTypingUsers([]);
        
        // Attempt reconnection if not intentional
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('Collaboration WebSocket error:', error);
        setConnectionStatus('error');
      };
      
    } catch (error) {
      console.error('Error connecting to collaboration WebSocket:', error);
      setConnectionStatus('error');
    }
  }, [workspaceId, token]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const handleMessage = useCallback((message) => {
    const { type, data } = message;
    
    switch (type) {
      case 'initial_data':
        setUserPresence(data.presence || {});
        setRecentActivity(data.recent_activity || []);
        updateActiveUsers(data.presence || {});
        break;
        
      case 'presence_update':
        setUserPresence(prev => ({
          ...prev,
          [data.user_id]: data.presence
        }));
        updateActiveUsers();
        break;
        
      case 'cursor_update':
        setCollaborationCursors(prev => ({
          ...prev,
          [data.resource_id]: {
            ...prev[data.resource_id],
            [data.user_id]: data.cursor
          }
        }));
        break;
        
      case 'resource_locked':
        setResourceLocks(prev => ({
          ...prev,
          [data.resource_id]: {
            user_id: data.locked_by,
            user_name: data.user_name,
            locked_at: new Date().toISOString()
          }
        }));
        break;
        
      case 'resource_unlocked':
        setResourceLocks(prev => {
          const updated = { ...prev };
          delete updated[data.resource_id];
          return updated;
        });
        break;
        
      case 'lock_granted':
        setResourceLocks(prev => ({
          ...prev,
          [data.resource_id]: {
            user_id: user?.id,
            user_name: user?.full_name || user?.email,
            locked_at: new Date().toISOString(),
            expires_at: data.expires_at
          }
        }));
        break;
        
      case 'lock_denied':
        console.warn('Resource lock denied:', data.reason);
        // Could show a notification here
        break;
        
      case 'typing_indicator':
        if (data.is_typing) {
          setTypingUsers(prev => {
            const existing = prev.find(t => 
              t.user_id === data.user_id && t.resource_id === data.resource_id
            );
            if (!existing) {
              return [...prev, {
                user_id: data.user_id,
                user_name: data.user_name,
                resource_id: data.resource_id,
                timestamp: data.timestamp
              }];
            }
            return prev;
          });
          
          // Remove typing indicator after 3 seconds
          setTimeout(() => {
            setTypingUsers(prev => prev.filter(t => 
              !(t.user_id === data.user_id && t.resource_id === data.resource_id)
            ));
          }, 3000);
        } else {
          setTypingUsers(prev => prev.filter(t => 
            !(t.user_id === data.user_id && t.resource_id === data.resource_id)
          ));
        }
        break;
        
      case 'collaboration_event':
        // Handle various collaboration events
        console.log('Collaboration event:', data);
        setRecentActivity(prev => [data, ...prev.slice(0, 19)]);
        break;
        
      case 'error':
        console.error('Collaboration error:', data.message);
        break;
        
      default:
        console.log('Unknown message type:', type, data);
    }
  }, [user]);

  const updateActiveUsers = useCallback((presenceData = null) => {
    const presence = presenceData || userPresence;
    const active = Object.entries(presence)
      .filter(([_, data]) => data.status === 'active')
      .map(([userId, data]) => ({
        id: parseInt(userId),
        name: data.user_name,
        email: data.user_email,
        status: data.status,
        current_resource: data.current_resource
      }));
    
    setActiveUsers(active);
  }, [userPresence]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Public methods for interacting with collaboration features
  const updatePresence = useCallback((presenceData) => {
    sendMessage({
      type: 'presence_update',
      data: presenceData
    });
  }, [sendMessage]);

  const updateCursor = useCallback((resourceId, position, selection = null) => {
    sendMessage({
      type: 'cursor_update',
      data: {
        resource_id: resourceId,
        position,
        selection
      }
    });
  }, [sendMessage]);

  const requestResourceLock = useCallback((resourceId) => {
    sendMessage({
      type: 'resource_lock',
      data: {
        resource_id: resourceId
      }
    });
  }, [sendMessage]);

  const releaseResourceLock = useCallback((resourceId) => {
    sendMessage({
      type: 'resource_unlock',
      data: {
        resource_id: resourceId
      }
    });
  }, [sendMessage]);

  const sendTypingIndicator = useCallback((resourceId, isTyping) => {
    sendMessage({
      type: 'typing_indicator',
      data: {
        resource_id: resourceId,
        is_typing: isTyping
      }
    });
  }, [sendMessage]);

  const sendCollaborationEvent = useCallback((eventType, resourceType, resourceId, eventData) => {
    sendMessage({
      type: 'collaboration_event',
      data: {
        event_type: eventType,
        resource_type: resourceType,
        resource_id: resourceId,
        event_data: eventData
      }
    });
  }, [sendMessage]);

  // Auto-connect when workspace changes
  useEffect(() => {
    if (workspaceId && token) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [workspaceId, token, connect, disconnect]);

  // Update presence when resource changes
  useEffect(() => {
    if (isConnected && resourceId) {
      updatePresence({
        status: 'active',
        current_resource: resourceId,
        resource_type: 'project' // or determine dynamically
      });
    }
  }, [resourceId, isConnected, updatePresence]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    // Connection state
    isConnected,
    connectionStatus,
    
    // Collaboration data
    activeUsers,
    userPresence,
    resourceLocks,
    collaborationCursors,
    typingUsers,
    recentActivity,
    
    // Actions
    connect,
    disconnect,
    updatePresence,
    updateCursor,
    requestResourceLock,
    releaseResourceLock,
    sendTypingIndicator,
    sendCollaborationEvent,
    
    // Utilities
    sendMessage
  };
};

export default useCollaboration;