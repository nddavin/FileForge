import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/lib/supabase';

// Polling interval for background tasks (ms)
const DEFAULT_POLL_INTERVAL = 5000;

interface RealtimeConfig {
  table: string;
  filter?: string;
  pollInterval?: number;
  onInsert?: (payload: any) => void;
  onUpdate?: (payload: any) => void;
  onDelete?: (payload: any) => void;
}

interface UseRealtimeOptions {
  enabled?: boolean;
  table: string;
  channelName?: string;
  pollInterval?: number;
  filters?: Record<string, any>;
}

interface BatchJobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  created_at: string;
  updated_at: string;
}

// Hook for real-time updates via WebSocket
export function useRealtimeUpdates<T>(
  options: UseRealtimeOptions,
  callback: (data: T[]) => void
) {
  const { enabled = true, table, channelName, pollInterval = DEFAULT_POLL_INTERVAL, filters } = options;
  const subscriptionRef = useRef<any>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      let query = supabase.from(table).select('*');
      
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          query = query.eq(key, value);
        });
      }

      const { data, error } = await query.order('created_at', { ascending: false });
      
      if (error) {
        console.error(`Error fetching ${table}:`, error);
        return;
      }

      callback(data as T);
    } catch (err) {
      console.error(`Error in fetchData for ${table}:`, err);
    }
  }, [table, filters, callback]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchData();

    // Set up WebSocket subscription
    const channel = channelName || `${table}-changes`;
    subscriptionRef.current = supabase
      .channel(channel)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table,
          filter: filters ? Object.entries(filters).map(([k, v]) => `${k}=${v}`).join(',') : undefined,
        },
        (payload) => {
          console.log(`Real-time update for ${table}:`, payload);
          fetchData();
        }
      )
      .subscribe();

    // Set up polling as fallback
    pollTimerRef.current = setInterval(fetchData, pollInterval);

    return () => {
      if (subscriptionRef.current) {
        supabase.removeChannel(subscriptionRef.current);
      }
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, [enabled, table, channelName, pollInterval, filters, fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { refetch };
}

// Hook for batch job status tracking
export function useBatchJobStatus(jobIds: string[]) {
  const [jobs, setJobs] = useState<Map<string, BatchJobStatus>>(new Map());
  const [isLoading, setIsLoading] = useState(true);

  const fetchJobStatus = useCallback(async () => {
    if (jobIds.length === 0) {
      setIsLoading(false);
      return;
    }

    try {
      const { data, error } = await supabase
        .from('batch_jobs')
        .select('*')
        .in('id', jobIds);

      if (error) {
        console.error('Error fetching batch jobs:', error);
        return;
      }

      const jobMap = new Map<string, BatchJobStatus>();
      data?.forEach(job => {
        jobMap.set(job.id, job);
      });
      setJobs(jobMap);
    } catch (err) {
      console.error('Error in fetchJobStatus:', err);
    } finally {
      setIsLoading(false);
    }
  }, [jobIds]);

  useEffect(() => {
    fetchJobStatus();
    
    // Poll for updates
    const interval = setInterval(fetchJobStatus, 3000);
    
    return () => clearInterval(interval);
  }, [fetchJobStatus]);

  const getJobStatus = useCallback((jobId: string) => {
    return jobs.get(jobId);
  }, [jobs]);

  return { jobs: Array.from(jobs.values()), getJobStatus, isLoading, refetch: fetchJobStatus };
}

// Hook for processing progress tracking
export function useProcessingProgress(fileId: string) {
  const [progress, setProgress] = useState({
    status: 'idle' as 'idle' | 'transcribing' | 'analyzing' | 'completed' | 'failed',
    percent: 0,
    currentStep: '',
    estimatedTimeRemaining: 0,
  });
  const [isActive, setIsActive] = useState(false);

  const updateProgress = useCallback(async () => {
    if (!fileId) return;

    try {
      const { data, error } = await supabase
        .from('processing_tasks')
        .select('*')
        .eq('file_id', fileId)
        .single();

      if (error || !data) {
        // No active processing task
        return;
      }

      setProgress({
        status: data.status,
        percent: data.progress || 0,
        currentStep: data.current_step || '',
        estimatedTimeRemaining: data.estimated_time_remaining || 0,
      });
      setIsActive(data.status === 'transcribing' || data.status === 'analyzing');
    } catch (err) {
      console.error('Error fetching processing progress:', err);
    }
  }, [fileId]);

  useEffect(() => {
    if (!fileId) return;

    updateProgress();
    
    // Poll for progress updates
    const interval = setInterval(updateProgress, 2000);
    
    return () => clearInterval(interval);
  }, [fileId, updateProgress]);

  return { progress, isActive, refetch: updateProgress };
}

// Hook for file notifications
export function useFileNotifications(userId: string) {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = useCallback(async () => {
    if (!userId) return;

    try {
      const { data, error } = await supabase
        .from('notifications')
        .select('*')
        .eq('user_id', userId)
        .eq('read', false)
        .order('created_at', { ascending: false })
        .limit(10);

      if (error) {
        console.error('Error fetching notifications:', error);
        return;
      }

      setNotifications(data || []);
      setUnreadCount(data?.length || 0);
    } catch (err) {
      console.error('Error in fetchNotifications:', err);
    }
  }, [userId]);

  useEffect(() => {
    if (!userId) return;

    fetchNotifications();

    // Subscribe to new notifications
    const channel = supabase
      .channel('notifications-changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log('New notification:', payload);
          setNotifications(prev => [payload.new, ...prev]);
          setUnreadCount(prev => prev + 1);
        }
      )
      .subscribe();

    // Poll for new notifications
    const interval = setInterval(fetchNotifications, 10000);

    return () => {
      supabase.removeChannel(channel);
      clearInterval(interval);
    };
  }, [userId, fetchNotifications]);

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await supabase
        .from('notifications')
        .update({ read: true })
        .eq('id', notificationId);

      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await supabase
        .from('notifications')
        .update({ read: true })
        .eq('user_id', userId)
        .eq('read', false);

      setNotifications([]);
      setUnreadCount(0);
    } catch (err) {
      console.error('Error marking all notifications as read:', err);
    }
  }, [userId]);

  return { notifications, unreadCount, markAsRead, markAllAsRead, refetch: fetchNotifications };
}

export default {
  useRealtimeUpdates,
  useBatchJobStatus,
  useProcessingProgress,
  useFileNotifications,
};
