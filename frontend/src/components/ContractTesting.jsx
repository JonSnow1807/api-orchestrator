import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  FileCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Upload,
  Download,
  Play,
  Shield,
  Code2,
  AlertCircle,
  Loader
} from 'lucide-react';

const ContractTesting = ({ projectId = null }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [contract, setContract] = useState({
    name: '',
    description: '',
    endpoint: '',
    method: 'GET',
    request_schema: '{}',
    response_schema: '{}',
    headers_schema: '{}',
    strict_mode: true
  });

  const validateContract = async () => {
    setLoading(true);
    setResults(null);
    
    try {
      // First create the contract
      const contractResponse = await axios.post(
        getApiUrl('/api/contracts/create'),
        {
          ...contract,
          request_schema: JSON.parse(contract.request_schema),
          response_schema: JSON.parse(contract.response_schema),
          headers_schema: JSON.parse(contract.headers_schema),
          project_id: projectId
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const contractId = contractResponse.data.contract.id;
      
      // Then validate it
      const validateResponse = await axios.post(
        getApiUrl(`/api/contracts/${contractId}/validate`),
        { test_data: {} },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setResults(validateResponse.data);
    } catch (error) {
      setResults({
        success: false,
        error: error.response?.data?.detail || error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const loadSampleContract = () => {
    setContract({
      name: 'User API Contract',
      description: 'Contract for user management endpoints',
      endpoint: '/api/users/{id}',
      method: 'GET',
      request_schema: JSON.stringify({
        "type": "object",
        "properties": {
          "id": { "type": "integer", "minimum": 1 }
        },
        "required": ["id"]
      }, null, 2),
      response_schema: JSON.stringify({
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "name": { "type": "string" },
          "email": { "type": "string", "format": "email" },
          "created_at": { "type": "string", "format": "date-time" }
        },
        "required": ["id", "name", "email"]
      }, null, 2),
      headers_schema: JSON.stringify({
        "type": "object",
        "properties": {
          "Authorization": { "type": "string", "pattern": "^Bearer .*" }
        },
        "required": ["Authorization"]
      }, null, 2),
      strict_mode: true
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-purple-400" />
            <div>
              <h2 className="text-2xl font-bold text-white">API Contract Testing</h2>
              <p className="text-gray-400">Define and validate API contracts to ensure consistency</p>
            </div>
          </div>
          <button
            onClick={loadSampleContract}
            className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
          >
            Load Sample
          </button>
        </div>
      </div>

      {/* Contract Definition */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Contract Definition</h3>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Contract Name
            </label>
            <input
              type="text"
              value={contract.name}
              onChange={(e) => setContract(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder="e.g., User API Contract"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Endpoint Pattern
            </label>
            <input
              type="text"
              value={contract.endpoint}
              onChange={(e) => setContract(prev => ({ ...prev, endpoint: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder="e.g., /api/users/{id}"
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Description
          </label>
          <input
            type="text"
            value={contract.description}
            onChange={(e) => setContract(prev => ({ ...prev, description: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            placeholder="Describe the contract purpose"
          />
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              HTTP Method
            </label>
            <select
              value={contract.method}
              onChange={(e) => setContract(prev => ({ ...prev, method: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={contract.strict_mode}
              onChange={(e) => setContract(prev => ({ ...prev, strict_mode: e.target.checked }))}
              className="mr-2"
            />
            <label className="text-sm text-gray-400">
              Strict Mode (fail on extra fields)
            </label>
          </div>
        </div>
      </div>

      {/* Schema Definitions */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center">
            <Code2 className="w-4 h-4 mr-2 text-blue-400" />
            Request Schema (JSON Schema)
          </h4>
          <textarea
            value={contract.request_schema}
            onChange={(e) => setContract(prev => ({ ...prev, request_schema: e.target.value }))}
            className="w-full h-48 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white font-mono text-sm"
            placeholder='{"type": "object", "properties": {...}}'
          />
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center">
            <Code2 className="w-4 h-4 mr-2 text-green-400" />
            Response Schema (JSON Schema)
          </h4>
          <textarea
            value={contract.response_schema}
            onChange={(e) => setContract(prev => ({ ...prev, response_schema: e.target.value }))}
            className="w-full h-48 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white font-mono text-sm"
            placeholder='{"type": "object", "properties": {...}}'
          />
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center">
            <Code2 className="w-4 h-4 mr-2 text-yellow-400" />
            Headers Schema (JSON Schema)
          </h4>
          <textarea
            value={contract.headers_schema}
            onChange={(e) => setContract(prev => ({ ...prev, headers_schema: e.target.value }))}
            className="w-full h-48 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white font-mono text-sm"
            placeholder='{"type": "object", "properties": {...}}'
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4">
        <button
          onClick={validateContract}
          disabled={loading || !contract.name || !contract.endpoint}
          className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50 flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              <span>Validating...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Validate Contract</span>
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {results && (
        <div className={`rounded-lg p-6 ${
          results.success 
            ? 'bg-green-900/20 border border-green-500/50' 
            : 'bg-red-900/20 border border-red-500/50'
        }`}>
          <div className="flex items-start space-x-3">
            {results.success ? (
              <CheckCircle className="w-6 h-6 text-green-400 mt-0.5" />
            ) : (
              <XCircle className="w-6 h-6 text-red-400 mt-0.5" />
            )}
            <div className="flex-1">
              <h3 className={`text-lg font-semibold ${
                results.success ? 'text-green-400' : 'text-red-400'
              }`}>
                {results.success ? 'Contract Valid' : 'Contract Validation Failed'}
              </h3>
              
              {results.validation_results && (
                <div className="mt-4 space-y-3">
                  {/* Request Validation */}
                  {results.validation_results.request_validation && (
                    <div className="bg-gray-800 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-400">Request Schema</span>
                        {results.validation_results.request_validation.is_valid ? (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                      </div>
                      {results.validation_results.request_validation.errors && (
                        <p className="text-xs text-red-400 mt-1">
                          {results.validation_results.request_validation.errors.join(', ')}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Response Validation */}
                  {results.validation_results.response_validation && (
                    <div className="bg-gray-800 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-400">Response Schema</span>
                        {results.validation_results.response_validation.is_valid ? (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                      </div>
                      {results.validation_results.response_validation.errors && (
                        <p className="text-xs text-red-400 mt-1">
                          {results.validation_results.response_validation.errors.join(', ')}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Breaking Changes */}
                  {results.breaking_changes && results.breaking_changes.length > 0 && (
                    <div className="bg-yellow-900/20 border border-yellow-500/50 rounded-lg p-3">
                      <div className="flex items-center space-x-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-400" />
                        <span className="text-sm font-medium text-yellow-400">Breaking Changes Detected</span>
                      </div>
                      <ul className="text-xs text-gray-400 space-y-1">
                        {results.breaking_changes.map((change, i) => (
                          <li key={i}>• {change}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {results.error && (
                <p className="text-sm text-gray-400 mt-2">{results.error}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractTesting;