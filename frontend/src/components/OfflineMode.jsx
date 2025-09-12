import React, { useState, useEffect } from 'react';
import { API_CONFIG, API_ENDPOINTS } from '../config/api';
import { 
  CloudArrowDownIcon, 
  CloudArrowUpIcon, 
  DocumentTextIcon,
  FolderOpenIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const OfflineMode = ({ collections, onCollectionSave, onCollectionLoad, onSync }) => {
  const [selectedFormat, setSelectedFormat] = useState('BRU');
  const [syncStatus, setSyncStatus] = useState('idle'); // idle, syncing, success, error
  const [localCollections, setLocalCollections] = useState([]);
  const [watchingDirectory, setWatchingDirectory] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [selectedCollection, setSelectedCollection] = useState(null);

  const storageFormats = {
    BRU: {
      name: 'Bruno Format',
      extension: '.bru',
      description: 'Git-friendly, Bruno-compatible format',
      icon: '📦'
    },
    JSON: {
      name: 'JSON',
      extension: '.json',
      description: 'Standard JSON format',
      icon: '📄'
    },
    YAML: {
      name: 'YAML',
      extension: '.yaml',
      description: 'Human-readable YAML format',
      icon: '📝'
    },
    HTTP: {
      name: 'HTTP',
      extension: '.http',
      description: 'Plain HTTP format for VS Code',
      icon: '🌐'
    },
    MARKDOWN: {
      name: 'Markdown',
      extension: '.md',
      description: 'Documentation-friendly format',
      icon: '📑'
    }
  };

  useEffect(() => {
    loadLocalCollections();
    checkLastSync();
  }, []);

  const loadLocalCollections = () => {
    // Load collections from localStorage (simulating local file access)
    const stored = localStorage.getItem('offline_collections');
    if (stored) {
      setLocalCollections(JSON.parse(stored));
    }
  };

  const checkLastSync = () => {
    const lastSyncTime = localStorage.getItem('last_sync_time');
    if (lastSyncTime) {
      setLastSync(new Date(lastSyncTime));
    }
  };

  const saveCollectionOffline = async (collection) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.OFFLINE}/save-collection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          collection: collection || selectedCollection,
          format: selectedFormat,
          path: `./collections/${collection?.id || 'default'}`
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update local storage
        const updatedCollections = [...localCollections, {
          ...collection,
          format: selectedFormat,
          savedAt: new Date().toISOString(),
          filePath: data.file_path
        }];
        setLocalCollections(updatedCollections);
        localStorage.setItem('offline_collections', JSON.stringify(updatedCollections));
        
        if (onCollectionSave) {
          onCollectionSave(collection, selectedFormat);
        }
        
        return data.file_path;
      }
    } catch (error) {
      console.error('Failed to save collection offline:', error);
      throw error;
    }
  };

  const loadCollectionFromFile = async (filePath) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.OFFLINE}/load-collection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          file_path: filePath,
          format: selectedFormat
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        if (onCollectionLoad) {
          onCollectionLoad(data.collection);
        }
        
        return data.collection;
      }
    } catch (error) {
      console.error('Failed to load collection:', error);
      throw error;
    }
  };

  const syncWithCloud = async () => {
    setSyncStatus('syncing');
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.OFFLINE}/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          path: './collections'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSyncStatus('success');
        setLastSync(new Date());
        localStorage.setItem('last_sync_time', new Date().toISOString());
        
        if (onSync) {
          onSync(data.synced);
        }
        
        setTimeout(() => setSyncStatus('idle'), 3000);
      } else {
        setSyncStatus('error');
        setTimeout(() => setSyncStatus('idle'), 3000);
      }
    } catch (error) {
      console.error('Sync failed:', error);
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  };

  const startWatching = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.OFFLINE}/watch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          directory: './collections'
        })
      });

      if (response.ok) {
        setWatchingDirectory(true);
      }
    } catch (error) {
      console.error('Failed to start watching:', error);
    }
  };

  const exportAllCollections = async () => {
    for (const collection of collections) {
      await saveCollectionOffline(collection);
    }
  };

  const getFormatIcon = (format) => {
    return storageFormats[format]?.icon || '📄';
  };

  const getTimeSinceSync = () => {
    if (!lastSync) return 'Never synced';
    
    const diff = Date.now() - lastSync.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
  };

  return (
    <div className="space-y-6">
      {/* Sync Status Bar */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              {syncStatus === 'syncing' && (
                <ArrowPathIcon className="h-5 w-5 text-blue-400 animate-spin mr-2" />
              )}
              {syncStatus === 'success' && (
                <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
              )}
              {syncStatus === 'error' && (
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
              )}
              {syncStatus === 'idle' && (
                <CloudArrowUpIcon className="h-5 w-5 text-gray-400 mr-2" />
              )}
              <span className="text-white font-medium">Offline Mode</span>
            </div>
            <span className="text-gray-400 text-sm">
              Last sync: {getTimeSinceSync()}
            </span>
            {watchingDirectory && (
              <span className="flex items-center text-green-400 text-sm">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                Watching for changes
              </span>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={syncWithCloud}
              disabled={syncStatus === 'syncing'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Sync Now
            </button>
            <button
              onClick={startWatching}
              disabled={watchingDirectory}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <FolderOpenIcon className="h-4 w-4 mr-2" />
              {watchingDirectory ? 'Watching...' : 'Watch Directory'}
            </button>
          </div>
        </div>
      </div>

      {/* Storage Format Selection */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Storage Format</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {Object.entries(storageFormats).map(([key, format]) => (
            <button
              key={key}
              onClick={() => setSelectedFormat(key)}
              className={`p-4 rounded-lg border-2 transition-all ${
                selectedFormat === key
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-gray-600 bg-gray-700 hover:border-gray-500'
              }`}
            >
              <div className="text-2xl mb-2">{format.icon}</div>
              <div className="text-white font-medium">{format.name}</div>
              <div className="text-gray-400 text-xs mt-1">{format.extension}</div>
              <div className="text-gray-500 text-xs mt-2">{format.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Collections Management */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cloud Collections */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <CloudArrowDownIcon className="h-5 w-5 mr-2" />
              Cloud Collections
            </h3>
            <button
              onClick={exportAllCollections}
              className="px-3 py-1 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 text-sm"
            >
              Export All
            </button>
          </div>
          <div className="space-y-2">
            {collections && collections.length > 0 ? (
              collections.map((collection) => (
                <div
                  key={collection.id}
                  className="bg-gray-700 rounded-lg p-3 flex items-center justify-between hover:bg-gray-600 cursor-pointer"
                  onClick={() => setSelectedCollection(collection)}
                >
                  <div className="flex items-center">
                    <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <div className="text-white">{collection.name}</div>
                      <div className="text-gray-400 text-xs">
                        {collection.requests?.length || 0} requests
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      saveCollectionOffline(collection);
                    }}
                    className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                  >
                    Save Offline
                  </button>
                </div>
              ))
            ) : (
              <div className="text-gray-400 text-center py-8">
                No collections available
              </div>
            )}
          </div>
        </div>

        {/* Local Collections */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <FolderOpenIcon className="h-5 w-5 mr-2" />
              Local Collections
            </h3>
            <button
              onClick={loadLocalCollections}
              className="px-3 py-1 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 text-sm"
            >
              Refresh
            </button>
          </div>
          <div className="space-y-2">
            {localCollections.length > 0 ? (
              localCollections.map((collection, index) => (
                <div
                  key={index}
                  className="bg-gray-700 rounded-lg p-3 flex items-center justify-between hover:bg-gray-600"
                >
                  <div className="flex items-center">
                    <span className="text-xl mr-3">
                      {getFormatIcon(collection.format)}
                    </span>
                    <div>
                      <div className="text-white">{collection.name}</div>
                      <div className="text-gray-400 text-xs">
                        {collection.format} • Saved {new Date(collection.savedAt).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => loadCollectionFromFile(collection.filePath)}
                    className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                  >
                    Load
                  </button>
                </div>
              ))
            ) : (
              <div className="text-gray-400 text-center py-8">
                No local collections found
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Git Integration Info */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Git Integration</h3>
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="space-y-2 text-sm">
            <div className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span className="text-gray-300">
                All collections are saved as plain text files, perfect for version control
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span className="text-gray-300">
                BRU format is compatible with Bruno, allowing seamless migration
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span className="text-gray-300">
                HTTP format works with VS Code REST Client extension
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span className="text-gray-300">
                Auto-sync keeps local and cloud collections in perfect harmony
              </span>
            </div>
          </div>
          <div className="mt-4 bg-gray-800 rounded p-3">
            <code className="text-xs text-gray-400">
              git add collections/<br />
              git commit -m "Update API collections"<br />
              git push origin main
            </code>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OfflineMode;