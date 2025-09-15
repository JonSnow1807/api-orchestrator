import React, { useState, useEffect } from 'react';
import { Globe, Eye, Settings, BarChart3, ExternalLink, Copy, Check, AlertCircle } from 'lucide-react';

const PublicDocsManager = ({ projectId }) => {
  const [docsConfig, setDocsConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [analytics, setAnalytics] = useState(null);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    version: '1.0.0',
    theme: 'modern',
    custom_domain: '',
    logo_url: '',
    getting_started: '',
    auth_description: '',
    code_examples: {},
    seo_enabled: true,
    analytics_enabled: false
  });

  useEffect(() => {
    if (projectId) {
      fetchDocsConfig();
      fetchAnalytics();
    }
  }, [projectId]);

  const fetchDocsConfig = async () => {
    try {
      const response = await fetch(`/api/docs/public/${projectId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDocsConfig(data);
        setFormData({
          title: data.title || '',
          description: data.description || '',
          version: data.version || '1.0.0',
          theme: data.theme || 'modern',
          custom_domain: data.custom_domain || '',
          logo_url: data.logo_url || '',
          getting_started: data.getting_started || '',
          auth_description: data.auth_description || '',
          code_examples: data.code_examples || {},
          seo_enabled: true,
          analytics_enabled: !!data.analytics_id
        });
        setPreviewUrl(data.public_url);
      } else if (response.status !== 404) {
        console.error('Failed to fetch docs config');
      }
    } catch (error) {
      console.error('Error fetching docs config:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    if (!docsConfig?.subdomain) return;

    try {
      const response = await fetch(`/api/docs/analytics/${docsConfig.subdomain}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);

    try {
      const payload = {
        project_id: projectId,
        ...formData
      };

      const response = await fetch('/api/docs/public', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        setDocsConfig(data);
        setPreviewUrl(data.public_url);
        alert('Documentation published successfully!');
      } else {
        const error = await response.text();
        alert(`Failed to publish documentation: ${error}`);
      }
    } catch (error) {
      console.error('Error publishing docs:', error);
      alert('Failed to publish documentation');
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    try {
      const payload = {
        project_id: projectId,
        ...formData
      };

      const response = await fetch('/api/docs/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        // Open preview in new window
        const previewWindow = window.open('', '_blank');
        previewWindow.document.write(data.preview_html);
        previewWindow.document.close();
      }
    } catch (error) {
      console.error('Error generating preview:', error);
      alert('Failed to generate preview');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete the public documentation? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/docs/public/${projectId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setDocsConfig(null);
        setPreviewUrl('');
        alert('Documentation deleted successfully');
      }
    } catch (error) {
      console.error('Error deleting docs:', error);
      alert('Failed to delete documentation');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Public Documentation</h1>
          <p className="text-gray-600 mt-1">Share beautiful API docs with your team and customers</p>
        </div>
        {docsConfig && (
          <div className="flex items-center space-x-2 bg-green-100 text-green-800 px-3 py-1 rounded-full">
            <Globe className="w-4 h-4" />
            <span className="text-sm font-medium">Published</span>
          </div>
        )}
      </div>

      {/* Current Status */}
      {docsConfig && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-blue-900">Your documentation is live!</h3>
            <button
              onClick={() => copyToClipboard(previewUrl)}
              className="flex items-center space-x-1 text-blue-600 hover:text-blue-700"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              <span className="text-sm">{copied ? 'Copied!' : 'Copy URL'}</span>
            </button>
          </div>
          <div className="flex items-center space-x-4">
            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-700"
            >
              <ExternalLink className="w-4 h-4" />
              <span className="font-mono text-sm">{previewUrl}</span>
            </a>
          </div>
        </div>
      )}

      {/* Analytics Summary */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Page Views</p>
                <p className="text-2xl font-semibold text-gray-900">{analytics.page_views.toLocaleString()}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <Globe className="w-5 h-5 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Unique Visitors</p>
                <p className="text-2xl font-semibold text-gray-900">{analytics.unique_visitors.toLocaleString()}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <Eye className="w-5 h-5 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Top Page</p>
                <p className="text-lg font-semibold text-gray-900">{analytics.top_pages[0]?.path || 'N/A'}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <Settings className="w-5 h-5 text-orange-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Top Referrer</p>
                <p className="text-lg font-semibold text-gray-900">{analytics.referrers[0]?.source || 'Direct'}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Form */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Configuration</h2>

        <div className="space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Documentation Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="My API Documentation"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Version
              </label>
              <input
                type="text"
                value={formData.version}
                onChange={(e) => setFormData({...formData, version: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="1.0.0"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="A comprehensive API for managing your application..."
            />
          </div>

          {/* Theme Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Theme
            </label>
            <select
              value={formData.theme}
              onChange={(e) => setFormData({...formData, theme: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="modern">Modern</option>
              <option value="minimal">Minimal</option>
              <option value="dark">Dark</option>
              <option value="corporate">Corporate</option>
            </select>
          </div>

          {/* Custom Domain */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Domain (Optional)
            </label>
            <input
              type="text"
              value={formData.custom_domain}
              onChange={(e) => setFormData({...formData, custom_domain: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="docs.mycompany.com"
            />
            <p className="text-xs text-gray-500 mt-1">
              Configure DNS to point to docs.streamapi.dev
            </p>
          </div>

          {/* Logo URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Logo URL (Optional)
            </label>
            <input
              type="url"
              value={formData.logo_url}
              onChange={(e) => setFormData({...formData, logo_url: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://mycompany.com/logo.png"
            />
          </div>

          {/* Getting Started */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Getting Started Guide (Markdown)
            </label>
            <textarea
              value={formData.getting_started}
              onChange={(e) => setFormData({...formData, getting_started: e.target.value})}
              rows={5}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              placeholder="# Getting Started&#10;&#10;Welcome to our API! Here's how to get started:&#10;&#10;1. Get your API key&#10;2. Make your first request&#10;3. Explore the endpoints"
            />
          </div>

          {/* Authentication Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Authentication Guide
            </label>
            <textarea
              value={formData.auth_description}
              onChange={(e) => setFormData({...formData, auth_description: e.target.value})}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Our API uses Bearer token authentication. Include your API key in the Authorization header..."
            />
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-3">
          <button
            onClick={handlePreview}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Eye className="w-4 h-4" />
            <span>Preview</span>
          </button>

          {docsConfig && (
            <button
              onClick={handleDelete}
              className="flex items-center space-x-2 px-4 py-2 text-red-600 border border-red-300 rounded-md hover:bg-red-50"
            >
              <AlertCircle className="w-4 h-4" />
              <span>Delete</span>
            </button>
          )}
        </div>

        <button
          onClick={handleSave}
          disabled={saving || !formData.title}
          className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          <Globe className="w-4 h-4" />
          <span>{saving ? 'Publishing...' : 'Publish Documentation'}</span>
        </button>
      </div>

      {!formData.title && (
        <div className="text-center text-gray-500 text-sm">
          Enter a title to enable publishing
        </div>
      )}
    </div>
  );
};

export default PublicDocsManager;