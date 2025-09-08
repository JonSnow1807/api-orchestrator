import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  Plus, 
  Edit2, 
  Trash2, 
  Check, 
  X, 
  Server, 
  Cloud,
  Key,
  Save,
  Copy
} from 'lucide-react';

const EnvironmentManager = ({ onEnvironmentChange, currentEnvironment }) => {
  const [environments, setEnvironments] = useState([
    {
      id: 'default',
      name: 'Default',
      variables: {
        baseUrl: 'https://api.example.com',
        apiKey: '',
        token: ''
      },
      color: 'purple'
    }
  ]);
  
  const [activeEnv, setActiveEnv] = useState('default');
  const [showEditor, setShowEditor] = useState(false);
  const [editingEnv, setEditingEnv] = useState(null);
  const [newVariable, setNewVariable] = useState({ key: '', value: '' });

  useEffect(() => {
    // Load environments from localStorage
    const saved = localStorage.getItem('apiEnvironments');
    if (saved) {
      const parsed = JSON.parse(saved);
      setEnvironments(parsed);
      if (parsed.length > 0 && !parsed.find(e => e.id === activeEnv)) {
        setActiveEnv(parsed[0].id);
      }
    }
  }, []);

  useEffect(() => {
    // Save to localStorage whenever environments change
    localStorage.setItem('apiEnvironments', JSON.stringify(environments));
    
    // Notify parent component
    const current = environments.find(e => e.id === activeEnv);
    if (current && onEnvironmentChange) {
      onEnvironmentChange(current);
    }
  }, [environments, activeEnv]);

  const envColors = {
    purple: 'bg-purple-600',
    green: 'bg-green-600',
    blue: 'bg-blue-600',
    yellow: 'bg-yellow-600',
    red: 'bg-red-600'
  };

  const addEnvironment = () => {
    const newEnv = {
      id: `env_${Date.now()}`,
      name: 'New Environment',
      variables: {
        baseUrl: 'https://api.example.com',
        apiKey: '',
        token: ''
      },
      color: 'blue'
    };
    setEnvironments([...environments, newEnv]);
    setEditingEnv(newEnv.id);
    setShowEditor(true);
  };

  const updateEnvironment = (envId, updates) => {
    setEnvironments(environments.map(env => 
      env.id === envId ? { ...env, ...updates } : env
    ));
  };

  const deleteEnvironment = (envId) => {
    if (envId === 'default') {
      alert("Cannot delete default environment");
      return;
    }
    setEnvironments(environments.filter(env => env.id !== envId));
    if (activeEnv === envId) {
      setActiveEnv('default');
    }
  };

  const updateVariable = (envId, key, value) => {
    setEnvironments(environments.map(env => 
      env.id === envId 
        ? { ...env, variables: { ...env.variables, [key]: value } }
        : env
    ));
  };

  const addVariable = (envId) => {
    if (!newVariable.key) return;
    
    setEnvironments(environments.map(env => 
      env.id === envId 
        ? { ...env, variables: { ...env.variables, [newVariable.key]: newVariable.value } }
        : env
    ));
    setNewVariable({ key: '', value: '' });
  };

  const removeVariable = (envId, key) => {
    setEnvironments(environments.map(env => {
      if (env.id === envId) {
        const newVars = { ...env.variables };
        delete newVars[key];
        return { ...env, variables: newVars };
      }
      return env;
    }));
  };

  const duplicateEnvironment = (envId) => {
    const source = environments.find(e => e.id === envId);
    if (source) {
      const newEnv = {
        ...source,
        id: `env_${Date.now()}`,
        name: `${source.name} (Copy)`
      };
      setEnvironments([...environments, newEnv]);
    }
  };

  const exportEnvironments = () => {
    const dataStr = JSON.stringify(environments, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = 'api-environments.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const currentEnv = environments.find(e => e.id === (editingEnv || activeEnv));

  return (
    <div className="space-y-4">
      {/* Environment Selector */}
      <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Globe className="w-4 h-4" />
            Environment
          </h3>
          <button
            onClick={() => setShowEditor(!showEditor)}
            className="text-purple-400 hover:text-purple-300 text-sm"
          >
            {showEditor ? 'Hide' : 'Manage'}
          </button>
        </div>
        
        <div className="flex gap-2 flex-wrap">
          {environments.map(env => (
            <button
              key={env.id}
              onClick={() => {
                setActiveEnv(env.id);
                setEditingEnv(null);
              }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
                activeEnv === env.id
                  ? `${envColors[env.color]} text-white`
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {env.id === 'default' ? <Server className="w-3 h-3" /> : <Cloud className="w-3 h-3" />}
              {env.name}
            </button>
          ))}
          <button
            onClick={addEnvironment}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-700 text-gray-400 hover:text-white hover:bg-gray-600 transition flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            Add
          </button>
        </div>
      </div>

      {/* Environment Editor */}
      {showEditor && currentEnv && (
        <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={currentEnv.name}
                onChange={(e) => updateEnvironment(currentEnv.id, { name: e.target.value })}
                className="px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
              />
              <select
                value={currentEnv.color}
                onChange={(e) => updateEnvironment(currentEnv.id, { color: e.target.value })}
                className="px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
              >
                {Object.keys(envColors).map(color => (
                  <option key={color} value={color}>{color}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => duplicateEnvironment(currentEnv.id)}
                className="p-1.5 text-gray-400 hover:text-white transition"
                title="Duplicate"
              >
                <Copy className="w-4 h-4" />
              </button>
              {currentEnv.id !== 'default' && (
                <button
                  onClick={() => deleteEnvironment(currentEnv.id)}
                  className="p-1.5 text-red-400 hover:text-red-300 transition"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Variables */}
          <div className="space-y-2">
            <div className="text-sm text-gray-400 mb-2">Variables</div>
            {Object.entries(currentEnv.variables).map(([key, value]) => (
              <div key={key} className="flex gap-2">
                <input
                  type="text"
                  value={key}
                  disabled
                  className="flex-1 px-3 py-1 bg-gray-700/50 text-gray-400 rounded border border-gray-600"
                />
                <input
                  type="text"
                  value={value}
                  onChange={(e) => updateVariable(currentEnv.id, key, e.target.value)}
                  placeholder="Value"
                  className="flex-1 px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                />
                <button
                  onClick={() => removeVariable(currentEnv.id, key)}
                  className="p-1.5 text-red-400 hover:text-red-300 transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
            
            {/* Add new variable */}
            <div className="flex gap-2 pt-2 border-t border-gray-700">
              <input
                type="text"
                value={newVariable.key}
                onChange={(e) => setNewVariable({ ...newVariable, key: e.target.value })}
                placeholder="Variable name"
                className="flex-1 px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
              />
              <input
                type="text"
                value={newVariable.value}
                onChange={(e) => setNewVariable({ ...newVariable, value: e.target.value })}
                placeholder="Value"
                className="flex-1 px-3 py-1 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
              />
              <button
                onClick={() => addVariable(currentEnv.id)}
                className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 transition flex items-center gap-1"
              >
                <Plus className="w-4 h-4" />
                Add
              </button>
            </div>
          </div>

          {/* Info */}
          <div className="mt-4 p-3 bg-gray-700/30 rounded text-xs text-gray-400">
            <p>Use variables in your requests with <code className="text-purple-400">{'{{variableName}}'}</code></p>
            <p className="mt-1">Example: <code className="text-purple-400">{'{{baseUrl}}/api/users'}</code></p>
          </div>
        </div>
      )}

      {/* Export Button */}
      {environments.length > 1 && (
        <button
          onClick={exportEnvironments}
          className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          Export Environments
        </button>
      )}
    </div>
  );
};

export default EnvironmentManager;