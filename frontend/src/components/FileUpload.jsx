import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import axios from 'axios';
import {
  Upload,
  File,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileCode,
  FileText,
  Archive
} from 'lucide-react';

const FileUpload = ({ onUploadSuccess }) => {
  const { token } = useAuth();
  const fileInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [message, setMessage] = useState({ type: '', text: '' });
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (fileList) => {
    const newFiles = Array.from(fileList).map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'pending'
    }));
    setFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    if (['py', 'js', 'jsx', 'ts', 'tsx', 'java', 'cpp', 'c', 'h'].includes(ext)) {
      return <FileCode className="w-5 h-5 text-blue-500" />;
    } else if (['zip', 'tar', 'gz', 'rar'].includes(ext)) {
      return <Archive className="w-5 h-5 text-purple-500" />;
    } else if (['txt', 'md', 'json', 'yaml', 'yml'].includes(ext)) {
      return <FileText className="w-5 h-5 text-gray-500" />;
    }
    return <File className="w-5 h-5 text-gray-400" />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      setMessage({ type: 'error', text: 'No files selected' });
      return;
    }

    setUploading(true);
    setMessage({ type: '', text: '' });

    const formData = new FormData();
    files.forEach(fileObj => {
      formData.append('files', fileObj.file);
    });

    try {
      const response = await axios.post(
        getApiUrl('/api/upload'),
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(prev => ({
              ...prev,
              overall: percentCompleted
            }));
          }
        }
      );

      setMessage({ 
        type: 'success', 
        text: `Successfully uploaded ${files.length} file(s)` 
      });

      // Update file statuses
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'completed',
        progress: 100
      })));

      // Callback for parent component
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }

      // Clear files after successful upload
      setTimeout(() => {
        setFiles([]);
        setUploadProgress({});
      }, 2000);
    } catch (error) {
      console.error('Upload failed:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Upload failed' 
      });

      // Update file statuses
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'error'
      })));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-white mb-4">File Upload</h3>

      {/* Message Display */}
      {message.text && (
        <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-900/20 text-green-400 border border-green-700' : 'bg-red-900/20 text-red-400 border border-red-700'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive 
            ? 'border-purple-400 bg-purple-900/10' 
            : 'border-gray-600 bg-gray-700/30 hover:bg-gray-700/50'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
          accept=".py,.js,.jsx,.ts,.tsx,.java,.cpp,.c,.h,.json,.yaml,.yml,.txt,.md,.zip,.tar,.gz"
        />
        
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        
        <label
          htmlFor="file-upload"
          className="cursor-pointer"
        >
          <p className="text-gray-300 font-medium mb-2">
            Drop files here or click to browse
          </p>
          <p className="text-sm text-gray-500">
            Support for Python, JavaScript, TypeScript, Java, C/C++, and archive files
          </p>
        </label>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-300">
              Selected Files ({files.length})
            </h4>
            {uploadProgress.overall && (
              <span className="text-sm text-blue-600">
                {uploadProgress.overall}% uploaded
              </span>
            )}
          </div>
          
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {files.map((fileObj) => (
              <div
                key={fileObj.id}
                className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg border border-gray-700"
              >
                <div className="flex items-center gap-3 flex-1">
                  {getFileIcon(fileObj.file.name)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {fileObj.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(fileObj.file.size)}
                    </p>
                  </div>
                </div>

                {/* Progress/Status */}
                {fileObj.status === 'uploading' && (
                  <div className="w-20">
                    <div className="bg-gray-700 rounded-full h-1.5">
                      <div
                        className="bg-purple-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${fileObj.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                {fileObj.status === 'completed' && (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                )}
                {fileObj.status === 'error' && (
                  <AlertCircle className="w-5 h-5 text-red-500" />
                )}

                {/* Remove Button */}
                {fileObj.status === 'pending' && !uploading && (
                  <button
                    onClick={() => removeFile(fileObj.id)}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Upload Button */}
          <button
            onClick={uploadFiles}
            disabled={uploading || files.every(f => f.status === 'completed')}
            className={`mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              uploading || files.every(f => f.status === 'completed')
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload Files
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUpload;