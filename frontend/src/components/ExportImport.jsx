import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import axios from 'axios';
import {
  Download,
  Upload,
  FileJson,
  FileCode,
  FileText,
  Package,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';

const ExportImport = ({ projectId, taskId }) => {
  const { token } = useAuth();
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [exportFormats, setExportFormats] = useState([]);
  const [selectedFormat, setSelectedFormat] = useState('json');
  const [message, setMessage] = useState({ type: '', text: '' });

  // Fetch available export formats
  React.useEffect(() => {
    fetchExportFormats();
  }, []);

  const fetchExportFormats = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/export/formats'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setExportFormats(response.data.formats || ['json', 'yaml', 'markdown', 'zip']);
    } catch (error) {
      console.error('Failed to fetch export formats:', error);
      setExportFormats(['json', 'yaml', 'markdown', 'zip']);
    }
  };

  const handleExport = async (format) => {
    if (!taskId) {
      setMessage({ type: 'error', text: 'No task ID provided for export' });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await axios.get(
        getApiUrl(`/api/export/${taskId}?format=${format}`),
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: format === 'zip' ? 'blob' : 'json'
        }
      );

      // Create download link
      let blob;
      let filename;

      if (format === 'zip') {
        blob = new Blob([response.data], { type: 'application/zip' });
        filename = `api-orchestrator-${taskId}.zip`;
      } else {
        const contentType = format === 'yaml' ? 'text/yaml' : 
                          format === 'markdown' ? 'text/markdown' : 
                          'application/json';
        const data = typeof response.data === 'string' ? response.data : JSON.stringify(response.data, null, 2);
        blob = new Blob([data], { type: contentType });
        filename = `api-orchestrator-${taskId}.${format}`;
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setMessage({ type: 'success', text: `Successfully exported as ${format.toUpperCase()}` });
    } catch (error) {
      console.error('Export failed:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Export failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setMessage({ type: '', text: '' });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        getApiUrl('/api/import'),
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setMessage({ 
        type: 'success', 
        text: `Successfully imported: ${response.data.project_name || 'Project'}` 
      });

      // Refresh page after successful import
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      console.error('Import failed:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Import failed. Please check file format.' 
      });
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const getFormatIcon = (format) => {
    switch (format) {
      case 'json':
        return <FileJson className="w-4 h-4" />;
      case 'yaml':
        return <FileCode className="w-4 h-4" />;
      case 'markdown':
        return <FileText className="w-4 h-4" />;
      case 'zip':
        return <Package className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-6">
      <h3 className="text-lg font-semibold mb-4">Export & Import</h3>

      {/* Message Display */}
      {message.text && (
        <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Export Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">Export Data</h4>
          <div className="space-y-2">
            {exportFormats.map((format) => (
              <button
                key={format}
                onClick={() => handleExport(format)}
                disabled={loading || !taskId}
                className={`w-full flex items-center justify-between px-4 py-2 border rounded-lg transition-colors ${
                  loading || !taskId
                    ? 'bg-gray-50 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-purple-400 border-gray-600 hover:border-purple-500'
                }`}
              >
                <div className="flex items-center gap-2">
                  {getFormatIcon(format)}
                  <span className="capitalize">{format}</span>
                </div>
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
              </button>
            ))}
          </div>
          {!taskId && (
            <p className="text-xs text-gray-500 mt-2">
              Complete orchestration first to enable export
            </p>
          )}
        </div>

        {/* Import Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">Import Data</h4>
          <div className="space-y-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.yaml,.yml,.zip"
              onChange={handleImport}
              disabled={loading}
              className="hidden"
              id="import-file"
            />
            <label
              htmlFor="import-file"
              className={`w-full flex items-center justify-center gap-2 px-4 py-6 border-2 border-dashed rounded-lg transition-colors cursor-pointer ${
                loading
                  ? 'bg-gray-50 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-purple-400 border-gray-600 hover:border-purple-500'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Importing...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Click to import file</span>
                </>
              )}
            </label>
            <p className="text-xs text-gray-500">
              Supports JSON, YAML, and ZIP formats
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportImport;