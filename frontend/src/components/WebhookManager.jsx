import React, { useState, useEffect } from 'react';
import {
  Webhook, Plus, Edit2, Trash2, TestTube, CheckCircle, XCircle,
  AlertCircle, Clock, Send, Shield, Globe, Copy, Eye, EyeOff,
  Activity, Zap, Bell, Server, Code, Users, Lock, RefreshCw
} from 'lucide-react';
import axios from 'axios';
import Toast from './Toast';

const WebhookManager = ({ workspaceId }) => {
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [showSecret, setShowSecret] = useState({});
  const [toast, setToast] = useState(null);

  // Available webhook events
  const WEBHOOK_EVENTS = [
    { value: 'api.discovered', label: 'API Discovered', icon: <Zap className="w-4 h-4" /> },
    { value: 'api.tested', label: 'API Tested', icon: <TestTube className="w-4 h-4" /> },
    { value: 'api.version.changed', label: 'API Version Changed', icon: <RefreshCw className="w-4 h-4" /> },
    { value: 'security.alert', label: 'Security Alert', icon: <Shield className="w-4 h-4" /> },
    { value: 'security.vulnerability.found', label: 'Vulnerability Found', icon: <AlertCircle className="w-4 h-4" /> },
    { value: 'performance.issue', label: 'Performance Issue', icon: <Activity className="w-4 h-4" /> },
    { value: 'mock.server.started', label: 'Mock Server Started', icon: <Server className="w-4 h-4" /> },
    { value: 'mock.server.stopped', label: 'Mock Server Stopped', icon: <Server className="w-4 h-4" /> },
    { value: 'ai.analysis.complete', label: 'AI Analysis Complete', icon: <Code className="w-4 h-4" /> },
    { value: 'error.threshold.exceeded', label: 'Error Threshold Exceeded', icon: <XCircle className="w-4 h-4" /> },
    { value: 'workspace.member.added', label: 'Member Added', icon: <Users className="w-4 h-4" /> },
    { value: 'workspace.member.removed', label: 'Member Removed', icon: <Users className="w-4 h-4" /> },
    { value: 'project.created', label: 'Project Created', icon: <Plus className="w-4 h-4" /> },
    { value: 'project.updated', label: 'Project Updated', icon: <Edit2 className="w-4 h-4" /> },
    { value: 'project.deleted', label: 'Project Deleted', icon: <Trash2 className="w-4 h-4" /> },
  ];

  useEffect(() => {
    if (workspaceId) {
      fetchWebhooks();
    }
  }, [workspaceId]);

  const fetchWebhooks = async () => {
    if (!workspaceId) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`/api/webhooks?workspace_id=${workspaceId}`);
      setWebhooks(response.data);
    } catch (error) {
      console.error('Error fetching webhooks:', error);
      setToast({
        message: 'Failed to fetch webhooks',
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWebhook = async (webhookData) => {
    try {
      const response = await axios.post('/api/webhooks', {
        ...webhookData,
        workspace_id: workspaceId
      });
      setWebhooks([...webhooks, response.data]);
      setShowCreateModal(false);
      setToast({
        message: 'Webhook created successfully',
        type: 'success'
      });
    } catch (error) {
      console.error('Error creating webhook:', error);
      setToast({
        message: error.response?.data?.detail || 'Failed to create webhook',
        type: 'error'
      });
    }
  };

  const handleUpdateWebhook = async (webhookId, updates) => {
    try {
      const response = await axios.patch(`/api/webhooks/${webhookId}`, updates);
      setWebhooks(webhooks.map(w => w.id === webhookId ? response.data : w));
      setShowEditModal(false);
      setSelectedWebhook(null);
      setToast({
        message: 'Webhook updated successfully',
        type: 'success'
      });
    } catch (error) {
      console.error('Error updating webhook:', error);
      setToast({
        message: error.response?.data?.detail || 'Failed to update webhook',
        type: 'error'
      });
    }
  };

  const handleDeleteWebhook = async (webhookId) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return;

    try {
      await axios.delete(`/api/webhooks/${webhookId}`);
      setWebhooks(webhooks.filter(w => w.id !== webhookId));
      setToast({
        message: 'Webhook deleted successfully',
        type: 'success'
      });
    } catch (error) {
      console.error('Error deleting webhook:', error);
      setToast({
        message: error.response?.data?.detail || 'Failed to delete webhook',
        type: 'error'
      });
    }
  };

  const handleTestWebhook = async (webhookId) => {
    setTestResults({ ...testResults, [webhookId]: { loading: true } });

    try {
      const response = await axios.post(`/api/webhooks/${webhookId}/test`, {
        event: 'test',
        data: {
          message: 'This is a test webhook delivery',
          timestamp: new Date().toISOString(),
          workspace_id: workspaceId
        }
      });

      setTestResults({
        ...testResults,
        [webhookId]: {
          loading: false,
          success: response.data.delivered,
          statusCode: response.data.status_code,
          responseTime: response.data.response_time_ms,
          error: response.data.error_message
        }
      });

      setTimeout(() => {
        setTestResults(prev => {
          const newResults = { ...prev };
          delete newResults[webhookId];
          return newResults;
        });
      }, 5000);
    } catch (error) {
      console.error('Error testing webhook:', error);
      setTestResults({
        ...testResults,
        [webhookId]: {
          loading: false,
          success: false,
          error: 'Failed to test webhook'
        }
      });
    }
  };

  const WebhookForm = ({ webhook, onSubmit, onCancel }) => {
    const [formData, setFormData] = useState({
      name: webhook?.name || '',
      url: webhook?.url || '',
      events: webhook?.events || [],
      secret: webhook?.secret || '',
      headers: webhook?.headers || {},
      is_active: webhook?.is_active !== undefined ? webhook.is_active : true
    });
    const [newHeaderKey, setNewHeaderKey] = useState('');
    const [newHeaderValue, setNewHeaderValue] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      onSubmit(formData);
    };

    const toggleEvent = (event) => {
      setFormData({
        ...formData,
        events: formData.events.includes(event)
          ? formData.events.filter(e => e !== event)
          : [...formData.events, event]
      });
    };

    const addHeader = () => {
      if (newHeaderKey && newHeaderValue) {
        setFormData({
          ...formData,
          headers: {
            ...formData.headers,
            [newHeaderKey]: newHeaderValue
          }
        });
        setNewHeaderKey('');
        setNewHeaderValue('');
      }
    };

    const removeHeader = (key) => {
      const newHeaders = { ...formData.headers };
      delete newHeaders[key];
      setFormData({ ...formData, headers: newHeaders });
    };

    return (
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-gray-300 mb-2">Webhook Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
            placeholder="My Webhook"
            required
          />
        </div>

        <div>
          <label className="block text-gray-300 mb-2">Endpoint URL</label>
          <input
            type="url"
            value={formData.url}
            onChange={(e) => setFormData({ ...formData, url: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
            placeholder="https://your-server.com/webhooks"
            required
          />
        </div>

        <div>
          <label className="block text-gray-300 mb-2">Secret (Optional)</label>
          <input
            type="password"
            value={formData.secret}
            onChange={(e) => setFormData({ ...formData, secret: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
            placeholder="Shared secret for signature verification"
          />
          <p className="text-xs text-gray-500 mt-1">
            Used to sign webhook payloads with HMAC-SHA256
          </p>
        </div>

        <div>
          <label className="block text-gray-300 mb-2">Events to Subscribe</label>
          <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto p-2 bg-gray-900 rounded-lg">
            {WEBHOOK_EVENTS.map(event => (
              <label
                key={event.value}
                className="flex items-center gap-2 p-2 rounded hover:bg-gray-800 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={formData.events.includes(event.value)}
                  onChange={() => toggleEvent(event.value)}
                  className="rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                />
                <span className="flex items-center gap-2 text-sm text-gray-300">
                  {event.icon}
                  {event.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-gray-300 mb-2">Custom Headers (Optional)</label>
          <div className="space-y-2">
            {Object.entries(formData.headers).map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <input
                  type="text"
                  value={key}
                  className="flex-1 px-3 py-1 bg-gray-900 border border-gray-700 rounded text-white text-sm"
                  disabled
                />
                <input
                  type="text"
                  value={value}
                  className="flex-1 px-3 py-1 bg-gray-900 border border-gray-700 rounded text-white text-sm"
                  disabled
                />
                <button
                  type="button"
                  onClick={() => removeHeader(key)}
                  className="text-red-400 hover:text-red-300"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            ))}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newHeaderKey}
                onChange={(e) => setNewHeaderKey(e.target.value)}
                className="flex-1 px-3 py-1 bg-gray-900 border border-gray-700 rounded text-white text-sm"
                placeholder="Header Name"
              />
              <input
                type="text"
                value={newHeaderValue}
                onChange={(e) => setNewHeaderValue(e.target.value)}
                className="flex-1 px-3 py-1 bg-gray-900 border border-gray-700 rounded text-white text-sm"
                placeholder="Header Value"
              />
              <button
                type="button"
                onClick={addHeader}
                className="text-green-400 hover:text-green-300"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
            className="rounded border-gray-600 text-purple-600 focus:ring-purple-500"
          />
          <label htmlFor="is_active" className="text-gray-300">
            Webhook is active
          </label>
        </div>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-400 hover:text-white transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition"
          >
            {webhook ? 'Update' : 'Create'} Webhook
          </button>
        </div>
      </form>
    );
  };

  if (!workspaceId) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Bell className="w-12 h-12 text-gray-600 mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">No Workspace Selected</h3>
        <p className="text-gray-400">Select a workspace to manage webhooks</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Webhook Management</h2>
          <p className="text-gray-400">Configure webhooks to receive real-time notifications</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Webhook
        </button>
      </div>

      {/* Webhooks List */}
      {webhooks.length === 0 ? (
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-12 border border-gray-700 text-center">
          <Webhook className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">No Webhooks Configured</h3>
          <p className="text-gray-400 mb-6">Add your first webhook to start receiving notifications</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            Create First Webhook
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {webhooks.map(webhook => (
            <div
              key={webhook.id}
              className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700 hover:border-purple-500/50 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    webhook.is_active ? 'bg-green-500/20' : 'bg-gray-700'
                  }`}>
                    <Webhook className={`w-5 h-5 ${
                      webhook.is_active ? 'text-green-400' : 'text-gray-400'
                    }`} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{webhook.name}</h3>
                    <p className="text-sm text-gray-400 mt-1">{webhook.url}</p>
                    <div className="flex items-center gap-4 mt-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        webhook.is_active
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-700 text-gray-400'
                      }`}>
                        {webhook.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {webhook.failure_count > 0 && (
                        <span className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-400">
                          {webhook.failure_count} failures
                        </span>
                      )}
                      {webhook.last_triggered && (
                        <span className="text-xs text-gray-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Last triggered: {new Date(webhook.last_triggered).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTestWebhook(webhook.id)}
                    className="p-2 text-blue-400 hover:bg-gray-700 rounded-lg transition"
                    title="Test Webhook"
                  >
                    {testResults[webhook.id]?.loading ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedWebhook(webhook);
                      setShowEditModal(true);
                    }}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition"
                    title="Edit Webhook"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteWebhook(webhook.id)}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition"
                    title="Delete Webhook"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Test Results */}
              {testResults[webhook.id] && !testResults[webhook.id].loading && (
                <div className={`mt-4 p-3 rounded-lg ${
                  testResults[webhook.id].success
                    ? 'bg-green-500/20 border border-green-500/50'
                    : 'bg-red-500/20 border border-red-500/50'
                }`}>
                  <div className="flex items-center gap-2">
                    {testResults[webhook.id].success ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400" />
                    )}
                    <span className={`text-sm ${
                      testResults[webhook.id].success ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {testResults[webhook.id].success ? 'Test successful' : 'Test failed'}
                      {testResults[webhook.id].statusCode && ` - Status: ${testResults[webhook.id].statusCode}`}
                      {testResults[webhook.id].responseTime && ` - ${testResults[webhook.id].responseTime}ms`}
                    </span>
                  </div>
                  {testResults[webhook.id].error && (
                    <p className="text-xs text-red-300 mt-1">{testResults[webhook.id].error}</p>
                  )}
                </div>
              )}

              {/* Events */}
              <div className="mt-4">
                <p className="text-sm text-gray-400 mb-2">Subscribed Events:</p>
                <div className="flex flex-wrap gap-2">
                  {webhook.events.map(event => {
                    const eventConfig = WEBHOOK_EVENTS.find(e => e.value === event);
                    return (
                      <span
                        key={event}
                        className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded flex items-center gap-1"
                      >
                        {eventConfig?.icon}
                        {eventConfig?.label || event}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white mb-6">Create New Webhook</h3>
            <WebhookForm
              onSubmit={handleCreateWebhook}
              onCancel={() => setShowCreateModal(false)}
            />
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedWebhook && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white mb-6">Edit Webhook</h3>
            <WebhookForm
              webhook={selectedWebhook}
              onSubmit={(data) => handleUpdateWebhook(selectedWebhook.id, data)}
              onCancel={() => {
                setShowEditModal(false);
                setSelectedWebhook(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default WebhookManager;