// Sermon Workflow Board - Real-time Kanban Dashboard
// React + Supabase Realtime for task distribution

import { useState, useEffect, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

// Task type definitions
interface SermonTask {
  id: string;
  sermon_id: string;
  task_type: TaskType;
  status: TaskStatus;
  assigned_to: string | null;
  priority: number;
  deadline: string | null;
  ai_score: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  retry_count: number;
  result_data: Record<string, unknown> | null;
  profiles?: {
    id: string;
    email: string;
    full_name: string;
    avatar_url: string | null;
    skills: string[];
  };
}

type TaskType = 
  | 'transcription' 
  | 'video_processing' 
  | 'location_tagging' 
  | 'metadata_ai' 
  | 'quality_optimization' 
  | 'thumbnail_generation' 
  | 'social_clip'
  | 'distribution';

type TaskStatus = 
  | 'pending' 
  | 'assigned' 
  | 'in_progress' 
  | 'completed' 
  | 'failed' 
  | 'cancelled';

interface Sermon {
  id: string;
  title: string;
  series_title: string | null;
  processing_status: string;
  thumbnail_urls: string[] | null;
}

// Task type icons and colors
const taskTypeConfig: Record<TaskType, { icon: string; color: string; label: string }> = {
  transcription: { icon: '🎤', color: '#3B82F6', label: 'Transcription' },
  video_processing: { icon: '🎬', color: '#8B5CF6', label: 'Video Processing' },
  location_tagging: { icon: '📍', color: '#10B981', label: 'Location' },
  metadata_ai: { icon: '🤖', color: '#F59E0B', label: 'AI Analysis' },
  quality_optimization: { icon: '⚡', color: '#EF4444', label: 'Quality' },
  thumbnail_generation: { icon: '🖼️', color: '#EC4899', label: 'Thumbnails' },
  social_clip: { icon: '📱', color: '#6366F1', label: 'Social Clips' },
  distribution: { icon: '🚀', color: '#14B8A6', label: 'Distribution' },
};

// Status column configuration
const statusColumns: { key: TaskStatus; label: string; color: string }[] = [
  { key: 'assigned', label: 'To Do', color: '#6B7280' },
  { key: 'in_progress', label: 'In Progress', color: '#3B82F6' },
  { key: 'completed', label: 'Done', color: '#10B981' },
  { key: 'failed', label: 'Failed', color: '#EF4444' },
];

export default function SermonWorkflowBoard() {
  const [tasks, setTasks] = useState<SermonTask[]>([]);
  const [sermons, setSermons] = useState<Record<string, Sermon>>({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'my_tasks' | 'unassigned'>('all');
  const [userId, setUserId] = useState<string | null>(null);

  // Fetch initial data
  const fetchTasks = useCallback(async () => {
    try {
      let query = supabase
        .from('sermon_tasks')
        .select(`
          *,
          profiles!assigned_to_fkey (
            id, email, full_name, avatar_url, skills
          )
        `)
        .in('status', ['assigned', 'in_progress', 'completed', 'failed'])
        .order('priority', { ascending: false })
        .order('created_at', { ascending: false });

      // Apply filter
      if (filter === 'my_tasks' && userId) {
        query = query.eq('assigned_to', userId);
      } else if (filter === 'unassigned') {
        query = query.is('assigned_to', null);
      }

      const { data: taskData, error: taskError } = await query;

      if (taskError) throw taskError;

      setTasks(taskData || []);

      // Fetch sermon details
      const sermonIds = [...new Set(taskData?.map(t => t.sermon_id) || [])];
      if (sermonIds.length > 0) {
        const { data: sermonData } = await supabase
          .from('sermons')
          .select('id, title, series_title, processing_status, thumbnail_urls')
          .in('id', sermonIds);

        const sermonMap = (sermonData || []).reduce((acc, s) => {
          acc[s.id] = s;
          return acc;
        }, {} as Record<string, Sermon>);

        setSermons(sermonMap);
      }
    } catch (error) {
      console.error('Error fetching tasks:', error);
    } finally {
      setLoading(false);
    }
  }, [filter, userId]);

  // Get current user
  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUserId(user?.id || null);
    };
    getUser();
  }, []);

  // Subscribe to realtime updates
  useEffect(() => {
    const channel = supabase
      .channel('sermon_tasks_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'sermon_tasks',
        },
        (payload) => {
          console.log('Task change:', payload);
          fetchTasks();
        }
      )
      .subscribe();

    fetchTasks();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [fetchTasks]);

  // Claim a task
  const claimTask = async (taskId: string) => {
    if (!userId) return;

    try {
      const { error } = await supabase
        .from('sermon_tasks')
        .update({
          assigned_to: userId,
          status: 'assigned',
          started_at: new Date().toISOString()
        })
        .eq('id', taskId);

      if (error) throw error;
    } catch (error) {
      console.error('Error claiming task:', error);
    }
  };

  // Update task status
  const updateTaskStatus = async (taskId: string, newStatus: TaskStatus) => {
    try {
      const updateData: Record<string, unknown> = {
        status: newStatus,
      };

      if (newStatus === 'completed') {
        updateData.completed_at = new Date().toISOString();
      }

      const { error } = await supabase
        .from('sermon_tasks')
        .update(updateData)
        .eq('id', taskId);

      if (error) throw error;
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  // Group tasks by status
  const tasksByStatus = statusColumns.reduce((acc, col) => {
    acc[col.key] = tasks.filter(t => t.status === col.key);
    return acc;
  }, {} as Record<TaskStatus, SermonTask[]>);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sermon Workflow Board</h1>
          <p className="text-gray-500">Real-time task distribution and tracking</p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Filter buttons */}
          <div className="flex rounded-lg overflow-hidden border border-gray-200">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 text-sm font-medium ${
                filter === 'all' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700'
              }`}
            >
              All Tasks
            </button>
            <button
              onClick={() => setFilter('my_tasks')}
              className={`px-4 py-2 text-sm font-medium ${
                filter === 'my_tasks' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700'
              }`}
            >
              My Tasks
            </button>
            <button
              onClick={() => setFilter('unassigned')}
              className={`px-4 py-2 text-sm font-medium ${
                filter === 'unassigned' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700'
              }`}
            >
              Unassigned
            </button>
          </div>

          {/* Refresh button */}
          <button
            onClick={fetchTasks}
            className="p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-4 gap-4">
        {statusColumns.map(column => (
          <div key={column.key} className="bg-gray-100 rounded-xl p-4">
            {/* Column Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: column.color }}
                />
                <h2 className="font-semibold text-gray-700">{column.label}</h2>
              </div>
              <span className="text-sm text-gray-500">
                {tasksByStatus[column.key]?.length || 0}
              </span>
            </div>

            {/* Task Cards */}
            <div className="space-y-3">
              {tasksByStatus[column.key]?.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  sermon={sermons[task.sermon_id]}
                  onClaim={claimTask}
                  onStatusChange={updateTaskStatus}
                  canClaim={!task.assigned_to}
                  currentUserId={userId}
                />
              ))}

              {(!tasksByStatus[column.key] || tasksByStatus[column.key].length === 0) && (
                <div className="text-center py-8 text-gray-400 text-sm">
                  No tasks
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Stats Footer */}
      <div className="mt-6 flex items-center gap-6 text-sm text-gray-600">
        <div>
          <span className="font-semibold">{tasks.length}</span> total tasks
        </div>
        <div>
          <span className="font-semibold text-blue-500">
            {tasks.filter(t => t.status === 'in_progress').length}
          </span> in progress
        </div>
        <div>
          <span className="font-semibold text-green-500">
            {tasks.filter(t => t.status === 'completed').length}
          </span> completed
        </div>
        <div>
          <span className="font-semibold text-red-500">
            {tasks.filter(t => t.status === 'failed').length}
          </span> failed
        </div>
      </div>
    </div>
  );
}

// Task Card Component
interface TaskCardProps {
  task: SermonTask;
  sermon: Sermon | undefined;
  onClaim: (taskId: string) => void;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  canClaim: boolean;
  currentUserId: string | null;
}

function TaskCard({ task, sermon, onClaim, onStatusChange, canClaim, currentUserId }: TaskCardProps) {
  const typeConfig = taskTypeConfig[task.task_type];
  const isAssignedToMe = task.assigned_to === currentUserId;
  const isInProgress = task.status === 'in_progress';

  return (
    <div 
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
      style={{ borderLeft: `4px solid ${typeConfig.color}` }}
    >
      {/* Task Type Badge */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{typeConfig.icon}</span>
        <span className="text-xs font-medium text-gray-600">{typeConfig.label}</span>
        {task.priority >= 4 && (
          <span className="ml-auto px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
            High
          </span>
        )}
      </div>

      {/* Sermon Title */}
      {sermon && (
        <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">
          {sermon.title || 'Untitled Sermon'}
        </h3>
      )}

      {/* Series Info */}
      {sermon?.series_title && (
        <p className="text-xs text-gray-500 mb-2">
          📚 {sermon.series_title}
        </p>
      )}

      {/* AI Score */}
      {task.ai_score > 0 && (
        <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
          <span>🤖 AI Score:</span>
          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-yellow-400 to-green-400"
              style={{ width: `${task.ai_score * 100}%` }}
            />
          </div>
          <span>{Math.round(task.ai_score * 100)}%</span>
        </div>
      )}

      {/* Assignee */}
      {task.profiles ? (
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
          <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
            {task.profiles.avatar_url ? (
              <img src={task.profiles.avatar_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="text-xs">{task.profiles.full_name?.charAt(0) || '?'}</span>
            )}
          </div>
          <span>{task.profiles.full_name || task.profiles.email}</span>
        </div>
      ) : canClaim ? (
        <button
          onClick={() => onClaim(task.id)}
          className="w-full py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors mb-3"
        >
          Claim Task
        </button>
      ) : null}

      {/* Actions for in-progress tasks */}
      {isInProgress && isAssignedToMe && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
          <button
            onClick={() => onStatusChange(task.id, 'completed')}
            className="flex-1 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            Complete
          </button>
          <button
            onClick={() => onStatusChange(task.id, 'failed')}
            className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            Fail
          </button>
        </div>
      )}

      {/* Error message */}
      {task.error_message && (
        <div className="mt-2 p-2 bg-red-50 text-red-700 text-xs rounded-lg">
          ⚠️ {task.error_message}
        </div>
      )}

      {/* Timestamps */}
      <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
        <span>{new Date(task.created_at).toLocaleDateString()}</span>
        {task.retry_count > 0 && (
          <span>🔄 Retry {task.retry_count}</span>
        )}
      </div>
    </div>
  );
}
