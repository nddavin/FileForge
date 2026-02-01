// Task Dashboard Component
import React, { useState, useEffect } from 'react';
import {
  getTaskStatistics,
  listTasks,
  getStatusColor,
  getTaskTypeLabel,
} from '../../lib/taskApi';
import {
  TaskStatistics,
  TaskAssignment,
  TaskStatus,
  TaskType,
} from '../../lib/types';

const TaskDashboard: React.FC = () => {
  const [statistics, setStatistics] = useState<TaskStatistics | null>(null);
  const [tasks, setTasks] = useState<TaskAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | ''>('');
  const [typeFilter, setTypeFilter] = useState<TaskType | ''>('');

  useEffect(() => {
    loadDashboardData();
  }, [statusFilter, typeFilter]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsResult, tasksResult] = await Promise.all([
        getTaskStatistics().catch(() => ({ success: false, data: null })),
        listTasks({
          limit: 20,
          ...(statusFilter && { status: statusFilter }),
          ...(typeFilter && { task_type: typeFilter }),
        }).catch(() => ({ success: false, data: [], pagination: undefined })),
      ]);

      if (statsResult.success && statsResult.data) {
        setStatistics(statsResult.data);
      }
      if (tasksResult.success) {
        setTasks(tasksResult.data || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Task Dashboard</h1>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">Total Tasks</div>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.total_tasks}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">Completed</div>
            <div className="text-3xl font-bold text-green-600">
              {statistics.completed_tasks}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">In Progress</div>
            <div className="text-3xl font-bold text-purple-600">
              {statistics.in_progress}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">Failed</div>
            <div className="text-3xl font-bold text-red-600">
              {statistics.failed}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status Filter
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as TaskStatus | '')}
              className="block w-40 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2"
            >
              <option value="">All Statuses</option>
              <option value={TaskStatus.PENDING}>Pending</option>
              <option value={TaskStatus.ASSIGNED}>Assigned</option>
              <option value={TaskStatus.IN_PROGRESS}>In Progress</option>
              <option value={TaskStatus.COMPLETED}>Completed</option>
              <option value={TaskStatus.FAILED}>Failed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type Filter
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as TaskType | '')}
              className="block w-48 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2"
            >
              <option value="">All Types</option>
              <option value={TaskType.TRANSCRIPTION}>Transcription</option>
              <option value={TaskType.VIDEO_PROCESSING}>Video Processing</option>
              <option value={TaskType.LOCATION_TAGGING}>Location Tagging</option>
              <option value={TaskType.ARTWORK_QUALITY}>Artwork Quality</option>
              <option value={TaskType.METADATA_AI}>AI Metadata</option>
              <option value={TaskType.THUMBNAIL_GENERATION}>Thumbnail Generation</option>
              <option value={TaskType.SOCIAL_CLIP}>Social Clip</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Task ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Assigned To
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Priority
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tasks.map((task) => (
              <tr key={task.task_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {task.task_id.slice(0, 8)}...
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {getTaskTypeLabel(task.task_type)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                      task.status
                    )}`}
                  >
                    {task.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {task.assigned_to?.full_name || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      task.priority >= 4
                        ? 'bg-red-100 text-red-800'
                        : task.priority >= 3
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {task.priority}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(task.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {tasks.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No tasks found matching the current filters
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskDashboard;
