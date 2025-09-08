import React, { useState, useEffect } from 'react';
import {
  Users, UserPlus, Mail, Shield, Trash2, Edit2, 
  ChevronDown, Check, X, Send, Copy, Clock,
  Activity, Settings, AlertCircle, Crown
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const TeamManagement = ({ workspaceId }) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('members');
  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteData, setInviteData] = useState({ email: '', role: 'developer', message: '' });
  const [workspace, setWorkspace] = useState(null);
  const [activity, setActivity] = useState([]);

  // Role colors and icons
  const roleConfig = {
    owner: { color: 'text-purple-400', bg: 'bg-purple-500/20', icon: Crown },
    admin: { color: 'text-blue-400', bg: 'bg-blue-500/20', icon: Shield },
    developer: { color: 'text-green-400', bg: 'bg-green-500/20', icon: Edit2 },
    viewer: { color: 'text-gray-400', bg: 'bg-gray-500/20', icon: Check }
  };

  useEffect(() => {
    if (workspaceId) {
      fetchWorkspaceData();
      fetchMembers();
      fetchInvitations();
      fetchActivity();
    }
  }, [workspaceId]);

  const fetchWorkspaceData = async () => {
    try {
      const response = await axios.get(`/api/workspaces/${workspaceId}`);
      setWorkspace(response.data);
    } catch (error) {
      console.error('Error fetching workspace:', error);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`/api/workspaces/${workspaceId}/members`);
      setMembers(response.data);
    } catch (error) {
      console.error('Error fetching members:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInvitations = async () => {
    try {
      const response = await axios.get(`/api/workspaces/${workspaceId}/invitations`);
      setInvitations(response.data || []);
    } catch (error) {
      console.error('Error fetching invitations:', error);
    }
  };

  const fetchActivity = async () => {
    try {
      const response = await axios.get(`/api/workspaces/${workspaceId}/activity`);
      setActivity(response.data);
    } catch (error) {
      console.error('Error fetching activity:', error);
    }
  };

  const handleInvite = async () => {
    try {
      await axios.post(`/api/workspaces/${workspaceId}/invitations`, inviteData);
      setShowInviteModal(false);
      setInviteData({ email: '', role: 'developer', message: '' });
      fetchInvitations();
      // Show success message
    } catch (error) {
      console.error('Error sending invitation:', error);
      // Show error message
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await axios.put(`/api/workspaces/${workspaceId}/members/${userId}`, { role: newRole });
      fetchMembers();
    } catch (error) {
      console.error('Error updating role:', error);
    }
  };

  const handleRemoveMember = async (userId) => {
    if (window.confirm('Are you sure you want to remove this member?')) {
      try {
        await axios.delete(`/api/workspaces/${workspaceId}/members/${userId}`);
        fetchMembers();
      } catch (error) {
        console.error('Error removing member:', error);
      }
    }
  };

  const copyInviteLink = (token) => {
    const link = `${window.location.origin}/invite/${workspaceId}/${token}`;
    navigator.clipboard.writeText(link);
    // Show copied message
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Team Management</h2>
          <p className="text-gray-400">
            Manage your workspace members and permissions
          </p>
        </div>
        {workspace?.role === 'owner' || workspace?.role === 'admin' ? (
          <button
            onClick={() => setShowInviteModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition flex items-center gap-2"
          >
            <UserPlus className="w-4 h-4" />
            Invite Member
          </button>
        ) : null}
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-700">
        {['members', 'invitations', 'activity'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 px-1 capitalize transition relative ${
              activeTab === tab
                ? 'text-purple-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            {tab}
            {activeTab === tab && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-500" />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'members' && (
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8 text-gray-400">Loading members...</div>
          ) : (
            members.map((member) => {
              const config = roleConfig[member.role];
              const RoleIcon = config.icon;
              
              return (
                <div
                  key={member.id}
                  className="flex items-center justify-between p-4 bg-gray-900 rounded-lg hover:bg-gray-900/70 transition"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {member.username?.[0]?.toUpperCase() || member.email[0].toUpperCase()}
                    </div>
                    <div>
                      <div className="text-white font-medium">{member.username || member.email}</div>
                      <div className="text-gray-400 text-sm">{member.email}</div>
                    </div>
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${config.bg}`}>
                      <RoleIcon className={`w-3 h-3 ${config.color}`} />
                      <span className={`text-xs ${config.color} capitalize`}>{member.role}</span>
                    </div>
                  </div>

                  {(workspace?.role === 'owner' || workspace?.role === 'admin') && member.role !== 'owner' && (
                    <div className="flex items-center gap-2">
                      <select
                        value={member.role}
                        onChange={(e) => handleRoleChange(member.id, e.target.value)}
                        className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                        disabled={member.id === user?.id}
                      >
                        <option value="admin">Admin</option>
                        <option value="developer">Developer</option>
                        <option value="viewer">Viewer</option>
                      </select>
                      {member.id !== user?.id && (
                        <button
                          onClick={() => handleRemoveMember(member.id)}
                          className="p-2 text-red-400 hover:bg-red-500/20 rounded transition"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === 'invitations' && (
        <div className="space-y-4">
          {invitations.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              No pending invitations
            </div>
          ) : (
            invitations.map((invitation) => (
              <div
                key={invitation.id}
                className="flex items-center justify-between p-4 bg-gray-900 rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <Mail className="w-5 h-5 text-purple-400" />
                  <div>
                    <div className="text-white">{invitation.email}</div>
                    <div className="text-gray-400 text-sm">
                      Invited as {invitation.role} • Expires {new Date(invitation.expires_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => copyInviteLink(invitation.token)}
                    className="p-2 text-gray-400 hover:text-white transition"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {/* Resend invitation */}}
                    className="p-2 text-gray-400 hover:text-white transition"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'activity' && (
        <div className="space-y-3">
          {activity.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              No activity yet
            </div>
          ) : (
            activity.map((item) => (
              <div key={item.id} className="flex items-start gap-3 p-3 hover:bg-gray-900/50 rounded transition">
                <Activity className="w-4 h-4 text-purple-400 mt-1" />
                <div className="flex-1">
                  <div className="text-white text-sm">
                    <span className="font-medium">{item.user_name}</span>
                    {' '}
                    <span className="text-gray-400">{item.action.replace('_', ' ')}</span>
                    {item.resource_name && (
                      <>
                        {' '}
                        <span className="text-purple-400">{item.resource_name}</span>
                      </>
                    )}
                  </div>
                  <div className="text-gray-500 text-xs mt-1">
                    {new Date(item.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">Invite Team Member</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-gray-300 mb-2">Email Address</label>
                <input
                  type="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                  placeholder="colleague@company.com"
                />
              </div>

              <div>
                <label className="block text-gray-300 mb-2">Role</label>
                <select
                  value={inviteData.role}
                  onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                >
                  <option value="admin">Admin - Can manage team and settings</option>
                  <option value="developer">Developer - Can create and edit</option>
                  <option value="viewer">Viewer - Can view only</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-300 mb-2">Message (Optional)</label>
                <textarea
                  value={inviteData.message}
                  onChange={(e) => setInviteData({ ...inviteData, message: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                  rows="3"
                  placeholder="Add a personal message..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowInviteModal(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition"
              >
                Cancel
              </button>
              <button
                onClick={handleInvite}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition"
              >
                Send Invitation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamManagement;