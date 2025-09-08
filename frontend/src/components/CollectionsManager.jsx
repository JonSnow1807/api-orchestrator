import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { getApiUrl } from '../config';
import {
  Folder,
  FolderOpen,
  Plus,
  ChevronRight,
  ChevronDown,
  Send,
  Edit2,
  Trash2,
  Copy,
  Download,
  Upload,
  Search,
  Star,
  StarOff,
  FileUp,
  CheckCircle
} from 'lucide-react';

const CollectionsManager = ({ onRequestSelect, onRequestSave, currentRequest }) => {
  const { token } = useAuth();
  const [collections, setCollections] = useState([]);
  const [expandedCollections, setExpandedCollections] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [showNewCollection, setShowNewCollection] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [editingCollection, setEditingCollection] = useState(null);
  const [editingRequest, setEditingRequest] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importSuccess, setImportSuccess] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Load collections from localStorage
    const saved = localStorage.getItem('apiCollections');
    if (saved) {
      setCollections(JSON.parse(saved));
    } else {
      // Initialize with a default collection
      const defaultCollection = {
        id: 'default',
        name: 'My Collection',
        description: 'Default collection for API requests',
        requests: [],
        createdAt: new Date().toISOString()
      };
      setCollections([defaultCollection]);
    }
  }, []);

  useEffect(() => {
    // Save to localStorage whenever collections change
    localStorage.setItem('apiCollections', JSON.stringify(collections));
  }, [collections]);

  const createCollection = () => {
    if (!newCollectionName.trim()) return;
    
    const newCollection = {
      id: `col_${Date.now()}`,
      name: newCollectionName,
      description: '',
      requests: [],
      createdAt: new Date().toISOString()
    };
    
    setCollections([...collections, newCollection]);
    setNewCollectionName('');
    setShowNewCollection(false);
    setExpandedCollections(new Set([...expandedCollections, newCollection.id]));
  };

  const deleteCollection = (collectionId) => {
    if (confirm('Are you sure you want to delete this collection?')) {
      setCollections(collections.filter(c => c.id !== collectionId));
    }
  };

  const updateCollection = (collectionId, updates) => {
    setCollections(collections.map(col =>
      col.id === collectionId ? { ...col, ...updates } : col
    ));
  };

  const addRequestToCollection = (collectionId, request) => {
    const newRequest = {
      ...request,
      id: `req_${Date.now()}`,
      createdAt: new Date().toISOString(),
      favorite: false
    };
    
    setCollections(collections.map(col =>
      col.id === collectionId
        ? { ...col, requests: [...col.requests, newRequest] }
        : col
    ));
    
    return newRequest;
  };

  const updateRequest = (collectionId, requestId, updates) => {
    setCollections(collections.map(col =>
      col.id === collectionId
        ? {
            ...col,
            requests: col.requests.map(req =>
              req.id === requestId ? { ...req, ...updates } : req
            )
          }
        : col
    ));
  };

  const deleteRequest = (collectionId, requestId) => {
    setCollections(collections.map(col =>
      col.id === collectionId
        ? { ...col, requests: col.requests.filter(req => req.id !== requestId) }
        : col
    ));
  };

  const duplicateRequest = (collectionId, requestId) => {
    const collection = collections.find(c => c.id === collectionId);
    const request = collection?.requests.find(r => r.id === requestId);
    
    if (request) {
      const duplicate = {
        ...request,
        id: `req_${Date.now()}`,
        name: `${request.name} (Copy)`,
        createdAt: new Date().toISOString()
      };
      
      setCollections(collections.map(col =>
        col.id === collectionId
          ? { ...col, requests: [...col.requests, duplicate] }
          : col
      ));
    }
  };

  const toggleFavorite = (collectionId, requestId) => {
    setCollections(collections.map(col =>
      col.id === collectionId
        ? {
            ...col,
            requests: col.requests.map(req =>
              req.id === requestId ? { ...req, favorite: !req.favorite } : req
            )
          }
        : col
    ));
  };

  const toggleCollection = (collectionId) => {
    const newExpanded = new Set(expandedCollections);
    if (newExpanded.has(collectionId)) {
      newExpanded.delete(collectionId);
    } else {
      newExpanded.add(collectionId);
    }
    setExpandedCollections(newExpanded);
  };

  const exportCollection = (collection) => {
    const dataStr = JSON.stringify(collection, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `${collection.name.toLowerCase().replace(/\s+/g, '-')}-collection.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const importCollection = async (event) => {
    const file = event.target.files[0];
    if (file) {
      setImporting(true);
      setImportSuccess(false);
      
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          
          // Check if it's a Postman collection
          if (imported.info && imported.item) {
            // It's a Postman collection, use the backend endpoint to convert it
            const formData = new FormData();
            formData.append('file', file);
            
            try {
              const response = await axios.post(
                getApiUrl('/api/collections/import-postman'),
                formData,
                {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                  }
                }
              );
              
              if (response.data) {
                const newCollection = {
                  id: `col_${Date.now()}`,
                  name: response.data.name || 'Imported from Postman',
                  description: response.data.description || 'Collection imported from Postman',
                  requests: response.data.requests || [],
                  createdAt: new Date().toISOString()
                };
                
                setCollections([...collections, newCollection]);
                setExpandedCollections(new Set([...expandedCollections, newCollection.id]));
                setImportSuccess(true);
                
                // Reset success message after 3 seconds
                setTimeout(() => setImportSuccess(false), 3000);
              }
            } catch (error) {
              console.error('Failed to import Postman collection:', error);
              alert('Failed to import Postman collection. Please check the file format.');
            }
          } else if (imported.id && imported.requests) {
            // It's already an API Orchestrator collection format
            imported.id = `col_${Date.now()}`;
            imported.name = `${imported.name} (Imported)`;
            setCollections([...collections, imported]);
            setExpandedCollections(new Set([...expandedCollections, imported.id]));
            setImportSuccess(true);
            
            // Reset success message after 3 seconds
            setTimeout(() => setImportSuccess(false), 3000);
          } else {
            throw new Error('Invalid collection format');
          }
        } catch (error) {
          console.error('Import error:', error);
          alert('Invalid collection file. Please upload a valid Postman or API Orchestrator collection.');
        } finally {
          setImporting(false);
          // Reset file input
          event.target.value = '';
        }
      };
      reader.readAsText(file);
    }
  };

  const getMethodColor = (method) => {
    const colors = {
      GET: 'text-green-400',
      POST: 'text-yellow-400',
      PUT: 'text-blue-400',
      PATCH: 'text-purple-400',
      DELETE: 'text-red-400'
    };
    return colors[method] || 'text-gray-400';
  };

  // Filter collections and requests based on search
  const filteredCollections = collections.map(col => ({
    ...col,
    requests: col.requests.filter(req =>
      searchTerm === '' ||
      req.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.url?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })).filter(col =>
    searchTerm === '' ||
    col.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    col.requests.length > 0
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">Collections</h3>
          <div className="flex items-center gap-2">
            <label className={`p-1.5 cursor-pointer transition relative group ${
              importing ? 'text-yellow-400' : importSuccess ? 'text-green-400' : 'text-gray-400 hover:text-white'
            }`} title="Import collection (Postman or API Orchestrator format)">
              {importing ? (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : importSuccess ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              <input
                type="file"
                accept=".json"
                onChange={importCollection}
                className="hidden"
                disabled={importing}
                ref={fileInputRef}
              />
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                Import Postman/API Orchestrator collection
              </div>
            </label>
            <button
              onClick={() => setShowNewCollection(true)}
              className="p-1.5 text-purple-400 hover:text-purple-300 transition"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search collections..."
            className="w-full pl-9 pr-3 py-1.5 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Collections List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {showNewCollection && (
          <div className="p-3 bg-gray-700/50 rounded-lg">
            <input
              type="text"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              placeholder="Collection name"
              className="w-full px-3 py-1.5 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-purple-500 focus:outline-none mb-2"
              autoFocus
              onKeyPress={(e) => e.key === 'Enter' && createCollection()}
            />
            <div className="flex gap-2">
              <button
                onClick={createCollection}
                className="flex-1 px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition"
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowNewCollection(false);
                  setNewCollectionName('');
                }}
                className="flex-1 px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-500 transition"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {filteredCollections.map(collection => (
          <div key={collection.id} className="bg-gray-800/30 rounded-lg">
            {/* Collection Header */}
            <div className="flex items-center p-2 hover:bg-gray-700/30 transition">
              <button
                onClick={() => toggleCollection(collection.id)}
                className="p-1 text-gray-400 hover:text-white transition"
              >
                {expandedCollections.has(collection.id) ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              
              <button
                onClick={() => toggleCollection(collection.id)}
                className="flex-1 flex items-center gap-2 text-left"
              >
                {expandedCollections.has(collection.id) ? (
                  <FolderOpen className="w-4 h-4 text-purple-400" />
                ) : (
                  <Folder className="w-4 h-4 text-purple-400" />
                )}
                {editingCollection === collection.id ? (
                  <input
                    type="text"
                    value={collection.name}
                    onChange={(e) => updateCollection(collection.id, { name: e.target.value })}
                    onBlur={() => setEditingCollection(null)}
                    onKeyPress={(e) => e.key === 'Enter' && setEditingCollection(null)}
                    className="flex-1 px-2 py-0.5 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <span className="text-white text-sm font-medium">{collection.name}</span>
                )}
                <span className="text-gray-500 text-xs">({collection.requests.length})</span>
              </button>
              
              <div className="flex items-center gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingCollection(collection.id);
                  }}
                  className="p-1 text-gray-500 hover:text-white transition opacity-0 group-hover:opacity-100"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    exportCollection(collection);
                  }}
                  className="p-1 text-gray-500 hover:text-white transition"
                >
                  <Download className="w-3 h-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteCollection(collection.id);
                  }}
                  className="p-1 text-gray-500 hover:text-red-400 transition"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Requests */}
            {expandedCollections.has(collection.id) && (
              <div className="pl-6 pb-2 space-y-1">
                {collection.requests.map(request => (
                  <div
                    key={request.id}
                    className="flex items-center gap-2 p-2 hover:bg-gray-700/30 rounded transition group cursor-pointer"
                    onClick={() => onRequestSelect && onRequestSelect(request)}
                  >
                    <span className={`text-xs font-bold ${getMethodColor(request.method)}`}>
                      {request.method}
                    </span>
                    {editingRequest === request.id ? (
                      <input
                        type="text"
                        value={request.name}
                        onChange={(e) => updateRequest(collection.id, request.id, { name: e.target.value })}
                        onBlur={() => setEditingRequest(null)}
                        onKeyPress={(e) => e.key === 'Enter' && setEditingRequest(null)}
                        className="flex-1 px-2 py-0.5 bg-gray-700 text-white text-sm rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span className="flex-1 text-gray-300 text-sm truncate">{request.name}</span>
                    )}
                    
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(collection.id, request.id);
                        }}
                        className="p-1 text-gray-500 hover:text-yellow-400 transition"
                      >
                        {request.favorite ? (
                          <Star className="w-3 h-3 fill-current" />
                        ) : (
                          <StarOff className="w-3 h-3" />
                        )}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingRequest(request.id);
                        }}
                        className="p-1 text-gray-500 hover:text-white transition"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          duplicateRequest(collection.id, request.id);
                        }}
                        className="p-1 text-gray-500 hover:text-white transition"
                      >
                        <Copy className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteRequest(collection.id, request.id);
                        }}
                        className="p-1 text-gray-500 hover:text-red-400 transition"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
                
                {collection.requests.length === 0 && (
                  <p className="text-gray-500 text-xs italic p-2">No requests in this collection</p>
                )}
              </div>
            )}
          </div>
        ))}
        
        {filteredCollections.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <Folder className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No collections found</p>
            <button
              onClick={() => setShowNewCollection(true)}
              className="mt-3 text-purple-400 hover:text-purple-300 text-sm"
            >
              Create your first collection
            </button>
          </div>
        )}
      </div>

      {/* Save Current Request */}
      {onRequestSave && (
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={() => {
              const collectionId = collections[0]?.id;
              if (collectionId && currentRequest) {
                const saved = addRequestToCollection(collectionId, currentRequest);
                onRequestSave(saved);
              }
            }}
            className="w-full px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition flex items-center justify-center gap-2"
            disabled={!currentRequest}
          >
            <Plus className="w-4 h-4" />
            Save Current Request
          </button>
        </div>
      )}
    </div>
  );
};

export default CollectionsManager;