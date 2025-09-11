import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Globe,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Activity,
  Plus,
  Edit,
  Trash2,
  ExternalLink,
  Settings,
  Eye,
  EyeOff,
  TrendingUp,
  AlertCircle,
  Loader
} from 'lucide-react';

const StatusPages = ({ projectId = null }) => {
  const { token } = useAuth();
  const [statusPages, setStatusPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedPage, setSelectedPage] = useState(null);
  const [healthData, setHealthData] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    services: [
      { name: '', url: '', method: 'GET', expected_status: 200 }
    ],
    is_public: true,
    show_uptime_history: true,
    show_incident_timeline: true,
    show_response_times: true,
    logo_url: '',
    primary_color: '#8B5CF6'
  });

  useEffect(() => {
    fetchStatusPages();
  }, []);

  const fetchStatusPages = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/status-pages/list'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatusPages(response.data.status_pages);
    } catch (error) {
      console.error('Failed to fetch status pages:', error);
    }
  };

  const fetchHealthData = async (pageId) => {
    try {
      const response = await axios.get(getApiUrl(`/api/status-pages/${pageId}/health`), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHealthData(response.data);
    } catch (error) {
      console.error('Failed to fetch health data:', error);
    }
  };

  const createStatusPage = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        getApiUrl('/api/status-pages/create'),
        { ...formData, project_id: projectId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      await fetchStatusPages();
      setShowCreateForm(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create status page:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteStatusPage = async (pageId) => {
    if (!confirm('Are you sure you want to delete this status page?')) return;
    
    try {
      await axios.delete(getApiUrl(`/api/status-pages/${pageId}`), {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchStatusPages();
    } catch (error) {
      console.error('Failed to delete status page:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      slug: '',
      description: '',
      services: [
        { name: '', url: '', method: 'GET', expected_status: 200 }
      ],
      is_public: true,
      show_uptime_history: true,
      show_incident_timeline: true,
      show_response_times: true,
      logo_url: '',
      primary_color: '#8B5CF6'
    });
  };

  const addService = () => {
    setFormData(prev => ({
      ...prev,
      services: [...prev.services, { name: '', url: '', method: 'GET', expected_status: 200 }]
    }));
  };

  const updateService = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      services: prev.services.map((service, i) => 
        i === index ? { ...service, [field]: value } : service
      )
    }));
  };

  const removeService = (index) => {
    setFormData(prev => ({
      ...prev,
      services: prev.services.filter((_, i) => i !== index)
    }));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'partial_outage':
        return <AlertCircle className="w-5 h-5 text-orange-400" />;
      case 'major_outage':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational':
        return 'bg-green-400';
      case 'degraded':
        return 'bg-yellow-400';
      case 'partial_outage':
        return 'bg-orange-400';
      case 'major_outage':
        return 'bg-red-400';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Globe className="w-8 h-8 text-purple-400" />
            <div>
              <h2 className="text-2xl font-bold text-white">Status Pages</h2>
              <p className="text-gray-400">Create public status pages for your APIs</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Create Status Page</span>
          </button>
        </div>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-gray-800 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white mb-4">Create New Status Page</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Page Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="My API Status"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                URL Slug
              </label>
              <div className="flex items-center">
                <span className="text-gray-400 mr-2">/status/</span>
                <input
                  type="text"
                  value={formData.slug}
                  onChange={(e) => setFormData(prev => ({ ...prev, slug: e.target.value.toLowerCase().replace(/\s+/g, '-') }))}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="my-api"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Description
            </label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder="Real-time status of our API services"
            />
          </div>

          {/* Services to Monitor */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-400">Services to Monitor</label>
              <button
                onClick={addService}
                className="text-purple-400 hover:text-purple-300"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            
            {formData.services.map((service, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={service.name}
                  onChange={(e) => updateService(index, 'name', e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="Service name"
                />
                <input
                  type="text"
                  value={service.url}
                  onChange={(e) => updateService(index, 'url', e.target.value)}
                  className="flex-2 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="https://api.example.com/health"
                />
                <select
                  value={service.method}
                  onChange={(e) => updateService(index, 'method', e.target.value)}
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="HEAD">HEAD</option>
                </select>
                <button
                  onClick={() => removeService(index)}
                  className="text-red-400 hover:text-red-300"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Display Options */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-400">Display Options</label>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_public}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_public: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-400">Public Page</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.show_uptime_history}
                  onChange={(e) => setFormData(prev => ({ ...prev, show_uptime_history: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-400">Show Uptime History</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.show_incident_timeline}
                  onChange={(e) => setFormData(prev => ({ ...prev, show_incident_timeline: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-400">Show Incidents</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.show_response_times}
                  onChange={(e) => setFormData(prev => ({ ...prev, show_response_times: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-400">Show Response Times</span>
              </label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                setShowCreateForm(false);
                resetForm();
              }}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              Cancel
            </button>
            <button
              onClick={createStatusPage}
              disabled={loading || !formData.name || !formData.slug}
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Status Page'}
            </button>
          </div>
        </div>
      )}

      {/* Status Pages List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statusPages.map(page => (
          <div key={page.id} className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{page.name}</h3>
                <p className="text-sm text-gray-400">/status/{page.slug}</p>
              </div>
              <div className="flex items-center space-x-2">
                {page.is_public ? (
                  <Eye className="w-4 h-4 text-green-400" title="Public" />
                ) : (
                  <EyeOff className="w-4 h-4 text-gray-400" title="Private" />
                )}
              </div>
            </div>

            <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
              <span>{page.services_count} services monitored</span>
              <span>{new Date(page.created_at).toLocaleDateString()}</span>
            </div>

            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setSelectedPage(page);
                  fetchHealthData(page.id);
                }}
                className="flex-1 px-3 py-1 bg-purple-600/20 text-purple-400 border border-purple-500/50 rounded-lg hover:bg-purple-600/30 transition flex items-center justify-center space-x-1"
              >
                <Activity className="w-4 h-4" />
                <span>View</span>
              </button>
              <a
                href={`/status/${page.slug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 px-3 py-1 bg-blue-600/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-600/30 transition flex items-center justify-center space-x-1"
              >
                <ExternalLink className="w-4 h-4" />
                <span>Public</span>
              </a>
              <button
                onClick={() => deleteStatusPage(page.id)}
                className="px-3 py-1 bg-red-600/20 text-red-400 border border-red-500/50 rounded-lg hover:bg-red-600/30 transition"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}

        {statusPages.length === 0 && !showCreateForm && (
          <div className="col-span-3 text-center py-12">
            <Globe className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No status pages created yet</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            >
              Create Your First Status Page
            </button>
          </div>
        )}
      </div>

      {/* Health Data Modal */}
      {selectedPage && healthData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">{selectedPage.name}</h2>
              <button
                onClick={() => {
                  setSelectedPage(null);
                  setHealthData(null);
                }}
                className="text-gray-400 hover:text-white"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            {/* Overall Status */}
            <div className="bg-gray-700 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <span className="text-lg font-medium text-white">Overall Status</span>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(healthData.overall_status)}
                  <span className="text-white capitalize">{healthData.overall_status.replace('_', ' ')}</span>
                </div>
              </div>
            </div>

            {/* Services */}
            <div className="space-y-3 mb-6">
              <h3 className="text-lg font-semibold text-white">Services</h3>
              {healthData.services.map((service, index) => (
                <div key={index} className="bg-gray-700 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(service.status)}
                      <span className="text-white">{service.name}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-400">
                      <span>{service.uptime.toFixed(2)}% uptime</span>
                      {healthData.show_response_times && (
                        <span>{service.response_time.toFixed(0)}ms</span>
                      )}
                      {service.incidents_today > 0 && (
                        <span className="text-yellow-400">{service.incidents_today} incidents today</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Uptime History */}
            {healthData.uptime_history && healthData.uptime_history.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3">90-Day Uptime</h3>
                <div className="flex space-x-1">
                  {healthData.uptime_history.map((day, index) => (
                    <div
                      key={index}
                      className={`w-1 h-8 rounded ${
                        day.uptime === null ? 'bg-gray-600' :
                        day.uptime >= 99.9 ? 'bg-green-400' :
                        day.uptime >= 95 ? 'bg-yellow-400' :
                        day.uptime >= 80 ? 'bg-orange-400' : 'bg-red-400'
                      }`}
                      title={`${day.date}: ${day.uptime ? day.uptime.toFixed(2) + '%' : 'No data'}`}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatusPages;