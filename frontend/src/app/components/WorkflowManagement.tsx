// Workflow Management Component
import React, { useState, useEffect } from 'react';
import {
  createWorkflow,
  startWorkflow,
  listWorkflows,
  getWorkflowProgress,
  getStatusColor,
  getTaskTypeLabel,
} from '../../lib/taskApi';
import {
  TaskWorkflow,
  TaskProgress,
  TaskType,
  WorkflowStatus,
  CreateWorkflowRequest,
} from '../../lib/types';

const WorkflowManagement: React.FC = () => {
  const [workflows, setWorkflows] = useState<TaskWorkflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<TaskWorkflow | null>(null);
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkflow, setNewWorkflow] = useState<CreateWorkflowRequest>({
    name: '',
    task_types: [],
    priority: 1,
  });

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const result = await listWorkflows({ limit: 20 });
      if (result.success) {
        setWorkflows(result.data || []);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = async () => {
    try {
      const result = await createWorkflow(newWorkflow);
      if (result.success) {
        setShowCreateModal(false);
        setNewWorkflow({ name: '', task_types: [], priority: 1 });
        loadWorkflows();
      }
    } catch (error) {
      console.error('Failed to create workflow:', error);
    }
  };

  const handleStartWorkflow = async (workflowId: string) => {
    try {
      const result = await startWorkflow(workflowId);
      if (result.success) {
        loadWorkflows();
      }
    } catch (error) {
      console.error('Failed to start workflow:', error);
    }
  };

  const handleViewProgress = async (workflow: TaskWorkflow) => {
    setSelectedWorkflow(workflow);
    try {
      const result = await getWorkflowProgress(workflow.workflow_id);
      if (result.success && result.data) {
        setProgress(result.data);
      }
    } catch (error) {
      console.error('Failed to get progress:', error);
    }
  };

  const toggleTaskType = (taskType: TaskType) => {
    const current = newWorkflow.task_types;
    if (current.includes(taskType)) {
      setNewWorkflow({
        ...newWorkflow,
        task_types: current.filter((t) => t !== taskType),
      });
    } else {
      setNewWorkflow({
        ...newWorkflow,
        task_types: [...current, taskType],
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Workflow Management</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Create Workflow
        </button>
      </div>

      {/* Workflows Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workflows.map((workflow) => (
          <div
            key={workflow.workflow_id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold text-lg">{workflow.name}</h3>
                <p className="text-sm text-gray-500">
                  {workflow.entity_type} / {workflow.entity_id.slice(0, 8)}...
                </p>
              </div>
              <span
                className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                  workflow.status
                )}`}
              >
                {workflow.status}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Tasks</span>
                <span className="font-medium">
                  {workflow.completed_task_count}/{workflow.task_count}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Priority</span>
                <span className="font-medium">{workflow.priority}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Created</span>
                <span className="font-medium">
                  {new Date(workflow.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            {workflow.task_count > 0 && (
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${(workflow.completed_task_count / workflow.task_count) * 100}%`,
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1 text-right">
                  {Math.round(
                    (workflow.completed_task_count / workflow.task_count) * 100
                  )}
                  % Complete
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="mt-4 flex gap-2">
              {workflow.status === WorkflowStatus.CREATED && (
                <button
                  onClick={() => handleStartWorkflow(workflow.workflow_id)}
                  className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                >
                  Start
                </button>
              )}
              <button
                onClick={() => handleViewProgress(workflow)}
                className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
              >
                View Progress
              </button>
            </div>
          </div>
        ))}
      </div>

      {workflows.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          No workflows found. Create your first workflow to get started.
        </div>
      )}

      {/* Create Workflow Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create New Workflow</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Workflow Name
                </label>
                <input
                  type="text"
                  value={newWorkflow.name}
                  onChange={(e) =>
                    setNewWorkflow({ ...newWorkflow, name: e.target.value })
                  }
                  className="w-full rounded-md border-gray-300 border p-2"
                  placeholder="Enter workflow name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <select
                  value={newWorkflow.priority}
                  onChange={(e) =>
                    setNewWorkflow({
                      ...newWorkflow,
                      priority: parseInt(e.target.value),
                    })
                  }
                  className="w-full rounded-md border-gray-300 border p-2"
                >
                  <option value={1}>Low (1)</option>
                  <option value={2}>Medium (2)</option>
                  <option value={3}>High (3)</option>
                  <option value={4}>Urgent (4)</option>
                  <option value={5}>Critical (5)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Task Types
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {Object.values(TaskType).map((type) => (
                    <label
                      key={type}
                      className={`flex items-center p-2 border rounded cursor-pointer ${
                        newWorkflow.task_types.includes(type)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={newWorkflow.task_types.includes(type)}
                        onChange={() => toggleTaskType(type)}
                        className="mr-2"
                      />
                      <span className="text-sm">{getTaskTypeLabel(type)}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 flex gap-3 justify-end">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWorkflow}
                disabled={!newWorkflow.name || newWorkflow.task_types.length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Create Workflow
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress Modal */}
      {selectedWorkflow && progress && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Workflow Progress</h2>
            <p className="text-gray-600 mb-4">{selectedWorkflow.name}</p>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Tasks</span>
                <span className="font-medium">{progress.total}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Completed</span>
                <span className="font-medium text-green-600">{progress.completed}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">In Progress</span>
                <span className="font-medium text-purple-600">{progress.in_progress}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Pending</span>
                <span className="font-medium text-yellow-600">{progress.pending}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Failed</span>
                <span className="font-medium text-red-600">{progress.failed}</span>
              </div>

              <div className="mt-4 pt-4 border-t">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">Progress</span>
                  <span className="font-bold text-blue-600">
                    {progress.percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-blue-600 h-4 rounded-full transition-all"
                    style={{ width: `${progress.percentage}%` }}
                  />
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                setSelectedWorkflow(null);
                setProgress(null);
              }}
              className="mt-6 w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowManagement;
