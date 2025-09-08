/**
 * Workspace API Client
 * Handles all API calls related to team collaboration and workspace management
 */

import { apiClient } from './api';

class WorkspaceAPI {
  // Workspace management
  async getWorkspaces() {
    const response = await apiClient.get('/workspaces');
    return response.data;
  }

  async getWorkspace(workspaceId) {
    const response = await apiClient.get(`/workspaces/${workspaceId}`);
    return response.data;
  }

  async createWorkspace(workspaceData) {
    const response = await apiClient.post('/workspaces', workspaceData);
    return response.data;
  }

  async updateWorkspace(workspaceId, updates) {
    const response = await apiClient.put(`/workspaces/${workspaceId}`, updates);
    return response.data;
  }

  async deleteWorkspace(workspaceId) {
    const response = await apiClient.delete(`/workspaces/${workspaceId}`);
    return response.data;
  }

  // Member management
  async getMembers(workspaceId) {
    const response = await apiClient.get(`/workspaces/${workspaceId}/members`);
    return response.data;
  }

  async updateMember(workspaceId, userId, updates) {
    const response = await apiClient.put(`/workspaces/${workspaceId}/members/${userId}`, updates);
    return response.data;
  }

  async removeMember(workspaceId, userId) {
    const response = await apiClient.delete(`/workspaces/${workspaceId}/members/${userId}`);
    return response.data;
  }

  // Invitation management
  async inviteMember(workspaceId, invitationData) {
    const response = await apiClient.post(`/workspaces/${workspaceId}/invitations`, invitationData);
    return response.data;
  }

  async getInvitations(workspaceId) {
    const response = await apiClient.get(`/workspaces/${workspaceId}/invitations`);
    return response.data;
  }

  async acceptInvitation(token) {
    const response = await apiClient.post(`/workspaces/invitations/${token}/accept`);
    return response.data;
  }

  async revokeInvitation(workspaceId, invitationId) {
    const response = await apiClient.delete(`/workspaces/${workspaceId}/invitations/${invitationId}`);
    return response.data;
  }

  // Collection management
  async getCollections(workspaceId, includeRequests = false) {
    const response = await apiClient.get(`/workspaces/${workspaceId}/collections`, {
      params: { include_requests: includeRequests }
    });
    return response.data;
  }

  async createCollection(workspaceId, collectionData) {
    const response = await apiClient.post(`/workspaces/${workspaceId}/collections`, collectionData);
    return response.data;
  }

  async updateCollection(workspaceId, collectionId, updates) {
    const response = await apiClient.put(`/workspaces/${workspaceId}/collections/${collectionId}`, updates);
    return response.data;
  }

  async deleteCollection(workspaceId, collectionId) {
    const response = await apiClient.delete(`/workspaces/${workspaceId}/collections/${collectionId}`);
    return response.data;
  }

  // Activity and logs
  async getActivity(workspaceId, params = {}) {
    const response = await apiClient.get(`/workspaces/${workspaceId}/activity`, { params });
    return response.data;
  }

  // Roles and permissions
  async getRoles(workspaceId) {
    const response = await apiClient.get(`/workspaces/${workspaceId}/roles`);
    return response.data;
  }

  async createRole(workspaceId, roleData) {
    const response = await apiClient.post(`/workspaces/${workspaceId}/roles`, roleData);
    return response.data;
  }

  async updateRole(workspaceId, roleId, updates) {
    const response = await apiClient.put(`/workspaces/${workspaceId}/roles/${roleId}`, updates);
    return response.data;
  }

  async deleteRole(workspaceId, roleId) {
    const response = await apiClient.delete(`/workspaces/${workspaceId}/roles/${roleId}`);
    return response.data;
  }

  async getMyPermissions(workspaceId) {
    const response = await apiClient.get(`/workspaces/${workspaceId}/my-permissions`);
    return response.data;
  }

  // Resource sharing
  async shareResource(workspaceId, resourceType, resourceId, shareData) {
    const response = await apiClient.post(
      `/workspaces/${workspaceId}/share/${resourceType}/${resourceId}`,
      shareData
    );
    return response.data;
  }

  async getResourcePermissions(workspaceId, resourceType, resourceId) {
    const response = await apiClient.get(
      `/workspaces/${workspaceId}/resources/${resourceType}/${resourceId}/permissions`
    );
    return response.data;
  }

  async revokeResourceAccess(workspaceId, resourceType, resourceId, userId) {
    const response = await apiClient.delete(
      `/workspaces/${workspaceId}/resources/${resourceType}/${resourceId}/permissions/${userId}`
    );
    return response.data;
  }

  // Workspace statistics and analytics
  async getWorkspaceStats(workspaceId, period = 'month') {
    const response = await apiClient.get(`/workspaces/${workspaceId}/stats`, {
      params: { period }
    });
    return response.data;
  }

  async getUsageStats(workspaceId, period = 'month') {
    const response = await apiClient.get(`/workspaces/${workspaceId}/usage`, {
      params: { period }
    });
    return response.data;
  }

  // Collaboration features
  async getActiveMembers(workspaceId) {
    const response = await apiClient.get(`/workspaces/${workspaceId}/active-members`);
    return response.data;
  }

  async updateMemberPresence(workspaceId, presenceData) {
    const response = await apiClient.post(`/workspaces/${workspaceId}/presence`, presenceData);
    return response.data;
  }
}

// Create singleton instance
export const workspaceAPI = new WorkspaceAPI();

// Export for use in API index
export default workspaceAPI;