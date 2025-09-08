import React, { useState, useEffect, useRef } from 'react';
import { 
  Building2, ChevronDown, Plus, Check, Users, 
  Crown, Settings, LogOut, Activity 
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const WorkspaceSwitcher = ({ onWorkspaceChange }) => {
  const { user } = useAuth();
  const [workspaces, setWorkspaces] = useState([]);
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkspace, setNewWorkspace] = useState({ name: '', description: '' });
  const [creating, setCreating] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchWorkspaces = async () => {
    try {
      const response = await axios.get('/api/workspaces');
      setWorkspaces(response.data);
      
      // Set current workspace from localStorage or first workspace
      const savedWorkspaceId = localStorage.getItem('currentWorkspaceId');
      const savedWorkspace = response.data.find(w => w.id === parseInt(savedWorkspaceId));
      const workspace = savedWorkspace || response.data[0];
      
      if (workspace) {
        setCurrentWorkspace(workspace);
        onWorkspaceChange?.(workspace);
      }
    } catch (error) {
      console.error('Error fetching workspaces:', error);
    }
  };

  const handleWorkspaceSelect = (workspace) => {
    setCurrentWorkspace(workspace);
    localStorage.setItem('currentWorkspaceId', workspace.id);
    onWorkspaceChange?.(workspace);
    setIsOpen(false);
  };

  const handleCreateWorkspace = async () => {
    if (!newWorkspace.name.trim()) return;
    
    setCreating(true);
    try {
      const response = await axios.post('/api/workspaces', newWorkspace);
      setWorkspaces([...workspaces, response.data]);
      handleWorkspaceSelect(response.data);
      setShowCreateModal(false);
      setNewWorkspace({ name: '', description: '' });
    } catch (error) {
      console.error('Error creating workspace:', error);
      // Show error message
    } finally {
      setCreating(false);
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-3 h-3" />;
      case 'admin':
        return <Settings className="w-3 h-3" />;
      default:
        return <Users className="w-3 h-3" />;
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'owner':
        return 'text-purple-400';
      case 'admin':
        return 'text-blue-400';
      case 'developer':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <>
      <div className="relative z-[99999]" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-3 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
              <Building2 className="w-4 h-4 text-white" />
            </div>
            <div className="text-left">
              <div className="text-white font-medium text-sm">
                {currentWorkspace?.name || 'Select Workspace'}
              </div>
              {currentWorkspace && (
                <div className="text-xs text-gray-400 flex items-center gap-1">
                  {getRoleIcon(currentWorkspace.role)}
                  <span className={getRoleColor(currentWorkspace.role)}>
                    {currentWorkspace.role}
                  </span>
                  <span className="text-gray-500">•</span>
                  <span>{currentWorkspace.member_count} members</span>
                </div>
              )}
            </div>
          </div>
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute top-full left-0 mt-2 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-[9999]">
            <div className="p-2">
              <div className="text-xs text-gray-500 px-3 py-2 font-semibold uppercase">
                Your Workspaces
              </div>
              
              <div className="max-h-64 overflow-y-auto">
                {workspaces.map((workspace) => (
                  <button
                    key={workspace.id}
                    onClick={() => handleWorkspaceSelect(workspace)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors ${
                      currentWorkspace?.id === workspace.id
                        ? 'bg-purple-600/20 text-purple-400'
                        : 'hover:bg-gray-700 text-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gradient-to-br from-purple-600/20 to-blue-600/20 rounded-lg flex items-center justify-center">
                        <Building2 className="w-4 h-4 text-purple-400" />
                      </div>
                      <div className="text-left">
                        <div className="font-medium">{workspace.name}</div>
                        <div className="text-xs text-gray-500 flex items-center gap-1">
                          {getRoleIcon(workspace.role)}
                          <span className={getRoleColor(workspace.role)}>
                            {workspace.role}
                          </span>
                          <span className="text-gray-600">•</span>
                          <span>{workspace.member_count} members</span>
                        </div>
                      </div>
                    </div>
                    {currentWorkspace?.id === workspace.id && (
                      <Check className="w-4 h-4 text-purple-400" />
                    )}
                  </button>
                ))}
              </div>

              <div className="border-t border-gray-700 mt-2 pt-2">
                <button
                  onClick={() => {
                    setIsOpen(false);
                    setShowCreateModal(true);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="w-8 h-8 border-2 border-dashed border-gray-600 rounded-lg flex items-center justify-center">
                    <Plus className="w-4 h-4 text-gray-400" />
                  </div>
                  <span className="font-medium">Create New Workspace</span>
                </button>
              </div>

              {currentWorkspace && (
                <div className="border-t border-gray-700 mt-2 pt-2">
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      // Navigate to workspace settings
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <Settings className="w-4 h-4 text-gray-400" />
                    <span>Workspace Settings</span>
                  </button>
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      // Navigate to activity log
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <Activity className="w-4 h-4 text-gray-400" />
                    <span>Activity Log</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[10000]">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">Create New Workspace</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-gray-300 mb-2">Workspace Name</label>
                <input
                  type="text"
                  value={newWorkspace.name}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, name: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                  placeholder="My Awesome Team"
                  maxLength={100}
                />
              </div>

              <div>
                <label className="block text-gray-300 mb-2">Description (Optional)</label>
                <textarea
                  value={newWorkspace.description}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, description: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                  rows="3"
                  placeholder="What will this workspace be used for?"
                />
              </div>

              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-sm text-gray-400 space-y-2">
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-400" />
                    <span>You'll be the workspace owner</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-400" />
                    <span>Invite unlimited team members</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-green-400" />
                    <span>Collaborate on APIs in real-time</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewWorkspace({ name: '', description: '' });
                }}
                className="px-4 py-2 text-gray-400 hover:text-white transition"
                disabled={creating}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWorkspace}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition disabled:opacity-50"
                disabled={!newWorkspace.name.trim() || creating}
              >
                {creating ? 'Creating...' : 'Create Workspace'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default WorkspaceSwitcher;