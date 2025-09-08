import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import axios from 'axios';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  Download,
  Eye,
  Trash2,
  Filter
} from 'lucide-react';

const TaskManager = () => {
  const { token } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedTask, setSelectedTask] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    try {
      setError(null);
      const response = await axios.get(getApiUrl('/api/tasks'), {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const tasksData = response.data.tasks || [];
      // Ensure tasks is always an array
      setTasks(Array.isArray(tasksData) ? tasksData : Object.values(tasksData));
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      setError('Failed to load tasks. Please try again.');
      // Set empty array on error to prevent white screen
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTaskDetails = async (taskId) => {
    try {
      const response = await axios.get(getApiUrl(`/api/tasks/${taskId}`), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedTask(response.data);
    } catch (error) {
      console.error('Failed to fetch task details:', error);
    }
  };

  const downloadArtifact = async (taskId, fileType) => {
    try {
      const response = await axios.get(
        getApiUrl(`/api/download/${taskId}/${fileType}`),
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${taskId}-${fileType}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'in_progress':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredTasks = (tasks || []).filter(task => {
    if (filter === 'all') return true;
    return task && task.status === filter;
  });

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (start, end) => {
    if (!start || !end) return 'N/A';
    const duration = new Date(end) - new Date(start);
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800">Task History</h2>
          <div className="flex items-center gap-4">
            {/* Filter Buttons */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Tasks</option>
                <option value="completed">Completed</option>
                <option value="in_progress">In Progress</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
            <button
              onClick={fetchTasks}
              className="p-2 text-gray-500 hover:text-blue-600 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Task List */}
      {error ? (
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-red-500">{error}</p>
          <button 
            onClick={fetchTasks}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      ) : loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500">No tasks found</p>
          <p className="text-gray-400 text-sm mt-2">Tasks will appear here when you run orchestrations</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className="px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {getStatusIcon(task.status)}
                    <h3 className="font-medium text-white">
                      {task.project_name || `Task ${task.id}`}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>Started: {formatDate(task.created_at)}</p>
                    {task.completed_at && (
                      <p>Duration: {formatDuration(task.created_at, task.completed_at)}</p>
                    )}
                    {task.message && (
                      <p className="text-gray-500">{task.message}</p>
                    )}
                  </div>

                  {/* Progress Bar */}
                  {task.status === 'in_progress' && task.progress !== undefined && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>Progress</span>
                        <span>{Math.round(task.progress)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Artifacts */}
                  {task.status === 'completed' && task.artifacts && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {task.artifacts.openapi && (
                        <button
                          onClick={() => downloadArtifact(task.id, 'openapi.json')}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                        >
                          <Download className="w-3 h-3" />
                          OpenAPI Spec
                        </button>
                      )}
                      {task.artifacts.tests && (
                        <button
                          onClick={() => downloadArtifact(task.id, 'tests.zip')}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-green-50 text-green-600 rounded hover:bg-green-100"
                        >
                          <Download className="w-3 h-3" />
                          Tests
                        </button>
                      )}
                      {task.artifacts.mock && (
                        <button
                          onClick={() => downloadArtifact(task.id, 'mock.zip')}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-purple-50 text-purple-600 rounded hover:bg-purple-100"
                        >
                          <Download className="w-3 h-3" />
                          Mock Server
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => fetchTaskDetails(task.id)}
                    className="p-2 text-gray-500 hover:text-blue-600 transition-colors"
                    title="View Details"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg border border-gray-700 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Task Details</h3>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
                {JSON.stringify(selectedTask, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskManager;