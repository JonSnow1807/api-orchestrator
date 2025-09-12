import React, { useState, useEffect } from 'react';
import {
  KeyIcon,
  GlobeAltIcon,
  LockClosedIcon,
  LockOpenIcon,
  EyeIcon,
  EyeSlashIcon,
  ShareIcon,
  UserGroupIcon,
  FolderIcon,
  ClockIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  SparklesIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import { toast } from 'react-hot-toast';

const EnhancedVariableManager = ({ projectId, onVariableChange }) => {
  const [variables, setVariables] = useState([]);
  const [scopes, setScopes] = useState(['LOCAL', 'SHARED', 'WORKSPACE', 'COLLECTION', 'ENVIRONMENT', 'GLOBAL']);
  const [selectedScope, setSelectedScope] = useState('LOCAL');
  const [showNewVariable, setShowNewVariable] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVariables, setSelectedVariables] = useState(new Set());
  const [shareModal, setShareModal] = useState(null);
  const [maskSettings, setMaskSettings] = useState({});

  // Variable form state
  const [newVariable, setNewVariable] = useState({
    key: '',
    value: '',
    description: '',
    scope: 'LOCAL',
    visibility: 'PRIVATE',
    type: 'string',
    isSensitive: false,
    isMasked: false,
    autoSave: true
  });

  useEffect(() => {
    fetchVariables();
  }, [selectedScope]);

  const fetchVariables = async () => {
    try {
      const response = await axios.get('/api/variables/enhanced', {
        params: { scope: selectedScope, projectId }
      });
      setVariables(response.data.variables || []);
    } catch (error) {
      console.error('Failed to fetch variables:', error);
    }
  };

  const handleCreateVariable = async () => {
    try {
      const response = await axios.post('/api/variables/enhanced', {
        ...newVariable,
        projectId
      });
      
      setVariables([...variables, response.data]);
      setShowNewVariable(false);
      setNewVariable({
        key: '',
        value: '',
        description: '',
        scope: 'LOCAL',
        visibility: 'PRIVATE',
        type: 'string',
        isSensitive: false,
        isMasked: false,
        autoSave: true
      });
      
      toast.success('Variable created successfully');
      if (onVariableChange) onVariableChange();
    } catch (error) {
      toast.error('Failed to create variable');
    }
  };

  const handleUpdateVariable = async (id, updates) => {
    try {
      const response = await axios.put(`/api/variables/enhanced/${id}`, updates);
      setVariables(variables.map(v => v.id === id ? response.data : v));
      setEditingId(null);
      toast.success('Variable updated');
      if (onVariableChange) onVariableChange();
    } catch (error) {
      toast.error('Failed to update variable');
    }
  };

  const handleDeleteVariable = async (id) => {
    if (!confirm('Are you sure you want to delete this variable?')) return;
    
    try {
      await axios.delete(`/api/variables/enhanced/${id}`);
      setVariables(variables.filter(v => v.id !== id));
      toast.success('Variable deleted');
      if (onVariableChange) onVariableChange();
    } catch (error) {
      toast.error('Failed to delete variable');
    }
  };

  const handleShareVariable = async (variableId, shareSettings) => {
    try {
      await axios.post(`/api/variables/enhanced/${variableId}/share`, shareSettings);
      toast.success('Variable sharing updated');
      fetchVariables();
    } catch (error) {
      toast.error('Failed to update sharing');
    }
  };

  const handleToggleMask = async (variableId, masked) => {
    try {
      await axios.post(`/api/variables/enhanced/${variableId}/mask`, { masked });
      setVariables(variables.map(v => 
        v.id === variableId ? { ...v, isMasked: masked } : v
      ));
      toast.success(masked ? 'Variable masked' : 'Variable unmasked');
    } catch (error) {
      toast.error('Failed to update masking');
    }
  };

  const detectSensitiveValue = (key, value) => {
    const sensitivePatterns = [
      /api[_-]?key/i,
      /secret/i,
      /password/i,
      /token/i,
      /auth/i,
      /credential/i,
      /private[_-]?key/i
    ];
    
    return sensitivePatterns.some(pattern => pattern.test(key)) ||
           sensitivePatterns.some(pattern => pattern.test(value));
  };

  const getScopeIcon = (scope) => {
    switch (scope) {
      case 'LOCAL': return <LockClosedIcon className="w-4 h-4" />;
      case 'SHARED': return <ShareIcon className="w-4 h-4" />;
      case 'WORKSPACE': return <FolderIcon className="w-4 h-4" />;
      case 'COLLECTION': return <FolderIcon className="w-4 h-4" />;
      case 'ENVIRONMENT': return <GlobeAltIcon className="w-4 h-4" />;
      case 'GLOBAL': return <GlobeAltIcon className="w-4 h-4" />;
      default: return <KeyIcon className="w-4 h-4" />;
    }
  };

  const getScopeColor = (scope) => {
    switch (scope) {
      case 'LOCAL': return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
      case 'SHARED': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'WORKSPACE': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'COLLECTION': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'ENVIRONMENT': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'GLOBAL': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'string': return 'text-green-600';
      case 'number': return 'text-blue-600';
      case 'boolean': return 'text-purple-600';
      case 'secret': return 'text-red-600';
      case 'url': return 'text-indigo-600';
      case 'email': return 'text-pink-600';
      default: return 'text-gray-600';
    }
  };

  const filteredVariables = variables.filter(v => 
    v.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.value?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <KeyIcon className="w-5 h-5 text-purple-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Enhanced Variable Manager
            </h3>
            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 rounded-full">
              Local-by-default
            </span>
          </div>
          
          <button
            onClick={() => setShowNewVariable(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            <PlusIcon className="w-4 h-4" />
            New Variable
          </button>
        </div>

        {/* Scope Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {scopes.map(scope => (
            <button
              key={scope}
              onClick={() => setSelectedScope(scope)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition whitespace-nowrap flex items-center gap-2 ${
                selectedScope === scope
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {getScopeIcon(scope)}
              {scope}
              <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
                {variables.filter(v => v.scope === scope).length}
              </span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="mt-3">
          <input
            type="text"
            placeholder="Search variables..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800"
          />
        </div>
      </div>

      {/* New Variable Form */}
      {showNewVariable && (
        <div className="border-b border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800/50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Key
              </label>
              <input
                type="text"
                value={newVariable.key}
                onChange={(e) => {
                  const key = e.target.value;
                  const isSensitive = detectSensitiveValue(key, newVariable.value);
                  setNewVariable({ 
                    ...newVariable, 
                    key,
                    isSensitive,
                    isMasked: isSensitive
                  });
                }}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-900"
                placeholder="VARIABLE_NAME"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Value
              </label>
              <div className="relative">
                <input
                  type={newVariable.isMasked ? 'password' : 'text'}
                  value={newVariable.value}
                  onChange={(e) => {
                    const value = e.target.value;
                    const isSensitive = detectSensitiveValue(newVariable.key, value);
                    setNewVariable({ 
                      ...newVariable, 
                      value,
                      isSensitive,
                      isMasked: isSensitive
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-900 pr-10"
                  placeholder="Variable value"
                />
                <button
                  type="button"
                  onClick={() => setNewVariable({ ...newVariable, isMasked: !newVariable.isMasked })}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2"
                >
                  {newVariable.isMasked ? 
                    <EyeSlashIcon className="w-5 h-5 text-gray-400" /> : 
                    <EyeIcon className="w-5 h-5 text-gray-400" />
                  }
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Type
              </label>
              <select
                value={newVariable.type}
                onChange={(e) => setNewVariable({ ...newVariable, type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-900"
              >
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
                <option value="secret">Secret</option>
                <option value="url">URL</option>
                <option value="email">Email</option>
                <option value="json">JSON</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Scope
              </label>
              <select
                value={newVariable.scope}
                onChange={(e) => setNewVariable({ ...newVariable, scope: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-900"
              >
                {scopes.map(scope => (
                  <option key={scope} value={scope}>{scope}</option>
                ))}
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <input
                type="text"
                value={newVariable.description}
                onChange={(e) => setNewVariable({ ...newVariable, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-900"
                placeholder="Optional description"
              />
            </div>

            <div className="md:col-span-2 flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={newVariable.isSensitive}
                  onChange={(e) => setNewVariable({ ...newVariable, isSensitive: e.target.checked })}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Sensitive</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={newVariable.autoSave}
                  onChange={(e) => setNewVariable({ ...newVariable, autoSave: e.target.checked })}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Auto-save</span>
              </label>

              {newVariable.isSensitive && (
                <span className="flex items-center gap-1 text-xs text-orange-600 dark:text-orange-400">
                  <ShieldCheckIcon className="w-4 h-4" />
                  Auto-detected as sensitive
                </span>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-2 mt-4">
            <button
              onClick={() => setShowNewVariable(false)}
              className="px-3 py-1.5 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateVariable}
              className="px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            >
              Create Variable
            </button>
          </div>
        </div>
      )}

      {/* Variables List */}
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {filteredVariables.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No variables found in {selectedScope} scope
          </div>
        ) : (
          filteredVariables.map(variable => (
            <div key={variable.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-medium text-gray-900 dark:text-white">
                      {variable.key}
                    </span>
                    
                    {/* Badges */}
                    <span className={`px-2 py-0.5 text-xs rounded-full ${getScopeColor(variable.scope)}`}>
                      {variable.scope}
                    </span>
                    
                    <span className={`text-xs font-medium ${getTypeColor(variable.type)}`}>
                      {variable.type}
                    </span>
                    
                    {variable.isSensitive && (
                      <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full">
                        <LockClosedIcon className="w-3 h-3" />
                        Sensitive
                      </span>
                    )}
                    
                    {variable.visibility === 'TEAM' && (
                      <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full">
                        <UserGroupIcon className="w-3 h-3" />
                        Shared
                      </span>
                    )}
                    
                    {variable.autoSave && (
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <ArrowPathIcon className="w-3 h-3" />
                        Auto-save
                      </span>
                    )}
                  </div>
                  
                  {/* Value */}
                  <div className="flex items-center gap-2 mt-1">
                    {editingId === variable.id ? (
                      <input
                        type="text"
                        defaultValue={variable.value}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleUpdateVariable(variable.id, { value: e.target.value });
                          } else if (e.key === 'Escape') {
                            setEditingId(null);
                          }
                        }}
                        className="flex-1 px-2 py-1 border border-gray-200 dark:border-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800"
                        autoFocus
                      />
                    ) : (
                      <code className="flex-1 text-sm text-gray-600 dark:text-gray-400">
                        {variable.isMasked ? '••••••••' : variable.value}
                      </code>
                    )}
                  </div>
                  
                  {/* Description */}
                  {variable.description && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {variable.description}
                    </p>
                  )}
                  
                  {/* Metadata */}
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    {variable.lastModified && (
                      <span className="flex items-center gap-1">
                        <ClockIcon className="w-3 h-3" />
                        Modified {new Date(variable.lastModified).toLocaleDateString()}
                      </span>
                    )}
                    {variable.version && (
                      <span>v{variable.version}</span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 ml-4">
                  <button
                    onClick={() => handleToggleMask(variable.id, !variable.isMasked)}
                    className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition"
                    title={variable.isMasked ? "Show value" : "Hide value"}
                  >
                    {variable.isMasked ? 
                      <EyeIcon className="w-4 h-4" /> : 
                      <EyeSlashIcon className="w-4 h-4" />
                    }
                  </button>
                  
                  <button
                    onClick={() => setEditingId(variable.id)}
                    className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition"
                    title="Edit"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => setShareModal(variable)}
                    className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition"
                    title="Share"
                  >
                    <ShareIcon className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => handleDeleteVariable(variable.id)}
                    className="p-1.5 text-gray-500 hover:text-red-600 transition"
                    title="Delete"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Share Modal */}
      {shareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Share Variable: {shareModal.key}</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Share with users (comma-separated emails)</label>
                <input
                  type="text"
                  placeholder="user1@example.com, user2@example.com"
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Share with teams</label>
                <select className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800">
                  <option>Select teams...</option>
                  <option>Development Team</option>
                  <option>QA Team</option>
                  <option>DevOps Team</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Expires in</label>
                <select className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800">
                  <option value="">Never</option>
                  <option value="24">24 hours</option>
                  <option value="168">1 week</option>
                  <option value="720">30 days</option>
                </select>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShareModal(null)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  handleShareVariable(shareModal.id, {
                    users: [],
                    teams: [],
                    expiresIn: null
                  });
                  setShareModal(null);
                }}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                Share
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedVariableManager;