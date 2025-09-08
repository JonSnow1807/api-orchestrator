/**
 * Workspace Context
 * Manages workspace state, permissions, and team collaboration features
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { workspaceAPI } from '../utils/api';

const WorkspaceContext = createContext(null);

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};

export const WorkspaceProvider = ({ children }) => {
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [permissions, setPermissions] = useState({});

  // Load workspaces on mount
  useEffect(() => {
    loadWorkspaces();
  }, []);

  // Load workspace permissions when current workspace changes
  useEffect(() => {
    if (currentWorkspace?.id) {
      loadPermissions(currentWorkspace.id);
    } else {
      setPermissions({});
    }
  }, [currentWorkspace?.id]);

  const loadWorkspaces = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await workspaceAPI.getWorkspaces();
      setWorkspaces(data);
      
      // If no current workspace but workspaces exist, select the first one
      if (!currentWorkspace && data.length > 0) {
        setCurrentWorkspace(data[0]);
      }
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      setError('Failed to load workspaces');
    } finally {
      setLoading(false);
    }
  }, [currentWorkspace]);

  const loadPermissions = useCallback(async (workspaceId) => {
    try {
      const data = await workspaceAPI.getMyPermissions(workspaceId);
      setPermissions(data.workspace_permissions?.permissions || {});
    } catch (error) {
      console.error('Failed to load permissions:', error);
      setPermissions({});
    }
  }, []);

  const refreshWorkspaces = useCallback(async () => {
    await loadWorkspaces();
  }, [loadWorkspaces]);

  const switchWorkspace = useCallback(async (workspace) => {
    setCurrentWorkspace(workspace);
    // Persist to localStorage
    localStorage.setItem('currentWorkspaceId', workspace.id.toString());
  }, []);

  const createWorkspace = useCallback(async (workspaceData) => {
    try {
      const newWorkspace = await workspaceAPI.createWorkspace(workspaceData);
      setWorkspaces(prev => [...prev, newWorkspace]);
      setCurrentWorkspace(newWorkspace);
      return newWorkspace;
    } catch (error) {
      console.error('Failed to create workspace:', error);
      throw error;
    }
  }, []);

  const updateWorkspace = useCallback(async (workspaceId, updates) => {
    try {
      const updatedWorkspace = await workspaceAPI.updateWorkspace(workspaceId, updates);
      setWorkspaces(prev =>
        prev.map(w => w.id === workspaceId ? updatedWorkspace : w)
      );
      if (currentWorkspace?.id === workspaceId) {
        setCurrentWorkspace(updatedWorkspace);
      }
      return updatedWorkspace;
    } catch (error) {
      console.error('Failed to update workspace:', error);
      throw error;
    }
  }, [currentWorkspace]);

  const deleteWorkspace = useCallback(async (workspaceId) => {
    try {
      await workspaceAPI.deleteWorkspace(workspaceId);
      setWorkspaces(prev => prev.filter(w => w.id !== workspaceId));
      
      // If deleted workspace was current, switch to another one
      if (currentWorkspace?.id === workspaceId) {
        const remainingWorkspaces = workspaces.filter(w => w.id !== workspaceId);
        setCurrentWorkspace(remainingWorkspaces.length > 0 ? remainingWorkspaces[0] : null);
      }
    } catch (error) {
      console.error('Failed to delete workspace:', error);
      throw error;
    }
  }, [currentWorkspace, workspaces]);

  // Permission checking functions
  const hasPermission = useCallback((resourceType, action) => {
    if (!permissions || !currentWorkspace) return false;
    
    const resourcePermissions = permissions[resourceType];
    if (!resourcePermissions) return false;
    
    return resourcePermissions[action] === true;
  }, [permissions, currentWorkspace]);

  const canManageMembers = useCallback(() => {
    return hasPermission('members', 'manage_roles') || hasPermission('members', 'invite');
  }, [hasPermission]);

  const canCreateProjects = useCallback(() => {
    return hasPermission('projects', 'create');
  }, [hasPermission]);

  const canCreateCollections = useCallback(() => {
    return hasPermission('collections', 'create');
  }, [hasPermission]);

  const canManageWorkspace = useCallback(() => {
    return hasPermission('workspace', 'write') || hasPermission('settings', 'manage');
  }, [hasPermission]);

  const isOwner = useCallback(() => {
    return currentWorkspace?.user_role === 'owner';
  }, [currentWorkspace]);

  const isAdmin = useCallback(() => {
    return ['owner', 'admin'].includes(currentWorkspace?.user_role);
  }, [currentWorkspace]);

  const getUserRole = useCallback(() => {
    return currentWorkspace?.user_role || null;
  }, [currentWorkspace]);

  // Helper function to check if user can access a resource
  const canAccessResource = useCallback((resource, action = 'read') => {
    // Check if user owns the resource
    if (resource.created_by_user_id === getCurrentUserId()) {
      return true;
    }

    // Check workspace permissions
    if (resource.workspace_id === currentWorkspace?.id) {
      const resourceType = getResourceType(resource);
      return hasPermission(resourceType, action);
    }

    // Check specific sharing permissions
    if (resource.shared_with && Array.isArray(resource.shared_with)) {
      const share = resource.shared_with.find(s => s.user_id === getCurrentUserId());
      return share && share[action] === true;
    }

    // Public resources
    return resource.visibility === 'public';
  }, [currentWorkspace, hasPermission]);

  // Helper function to get current user ID (implement based on your auth system)
  const getCurrentUserId = () => {
    // This should return the current user's ID from your auth context
    // For now, returning null - implement based on your auth system
    return null;
  };

  // Helper function to determine resource type
  const getResourceType = (resource) => {
    if (resource.hasOwnProperty('apis')) return 'projects';
    if (resource.hasOwnProperty('requests')) return 'collections';
    return 'unknown';
  };

  // Workspace statistics
  const getWorkspaceStats = useCallback(() => {
    if (!currentWorkspace?.stats) return null;
    
    return {
      memberCount: currentWorkspace.stats.member_count || 0,
      projectCount: currentWorkspace.stats.project_count || 0,
      collectionCount: currentWorkspace.stats.collection_count || 0,
      pendingInvitations: currentWorkspace.stats.pending_invitations || 0
    };
  }, [currentWorkspace]);

  // Context value
  const contextValue = {
    // State
    currentWorkspace,
    workspaces,
    loading,
    error,
    permissions,

    // Actions
    setCurrentWorkspace: switchWorkspace,
    refreshWorkspaces,
    createWorkspace,
    updateWorkspace,
    deleteWorkspace,

    // Permission checks
    hasPermission,
    canManageMembers,
    canCreateProjects,
    canCreateCollections,
    canManageWorkspace,
    canAccessResource,
    
    // Role checks
    isOwner,
    isAdmin,
    getUserRole,

    // Stats
    getWorkspaceStats,

    // Utility
    getCurrentUserId
  };

  return (
    <WorkspaceContext.Provider value={contextValue}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export default WorkspaceContext;