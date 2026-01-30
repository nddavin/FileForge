import React, { useState, useEffect, useCallback, useRef } from 'react';
import { projectId, publicAnonKey } from '/utils/supabase/info';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Progress } from '@/app/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select';
import {
  Search,
  Filter,
  RefreshCw,
  Bell,
  Upload,
  CheckCircle,
  Clock,
  Activity,
  Loader2,
  X,
  FileAudio,
  FileVideo,
} from 'lucide-react';
import { cn, formatDistanceToNow } from '@/app/components/ui/utils';
import { toast } from 'sonner';

// Job types for real-time tracking
interface ProcessingJob {
  id: string;
  fileId: string;
  fileName: string;
  type: 'transcribe' | 'optimize' | 'analyze' | 'thumbnail' | 'upload';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  createdAt: Date;
  completedAt?: Date;
}

interface Notification {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

// File filter types
interface FileFilters {
  preacher: string;
  dateRange: string;
  quality: string;
  status: string;
  search: string;
}

// Mock preachers for filter
const mockPreachers = ['Pastor John', 'Sarah Miller', 'Mike Johnson', 'Emily Davis'];

export function RealTimeFeatures() {
  // Job tracking state
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [pollingJobIds, setPollingJobIds] = useState<Set<string>>(new Set());
  
  // Notification state
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  
  // Filter state
  const [filters, setFilters] = useState<FileFilters>({
    preacher: 'all',
    dateRange: 'all',
    quality: 'all',
    status: 'all',
    search: '',
  });
  
  // Refetch trigger
  const [refetchTrigger, setRefetchTrigger] = useState(0);
  const [isRefetching, setIsRefetching] = useState(false);

  // Simulated file data for live search demo
  const [files, setFiles] = useState([
    { id: '1', name: 'sermon-2024-01-28.mp3', preacher: 'Pastor John', date: '2024-01-28', quality: 95, status: 'ready', type: 'audio/mpeg' },
    { id: '2', name: 'sermon-2024-01-25.mp4', preacher: 'Sarah Miller', date: '2024-01-25', quality: 88, status: 'processing', type: 'video/mp4' },
    { id: '3', name: 'teaching-faith.mp3', preacher: 'Mike Johnson', date: '2024-01-24', quality: 92, status: 'ready', type: 'audio/mpeg' },
    { id: '4', name: 'wednesday-study.mp3', preacher: 'Pastor John', date: '2024-01-23', quality: 78, status: 'failed', type: 'audio/mpeg' },
    { id: '5', name: 'sunday-service.mp4', preacher: 'Emily Davis', date: '2024-01-22', quality: 90, status: 'ready', type: 'video/mp4' },
  ]);

  // Add a notification
  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: `notif_${Date.now()}`,
      timestamp: new Date(),
      read: false,
    };
    
    setNotifications(prev => [newNotification, ...prev].slice(0, 50)); // Keep last 50
    
    // Show toast
    toast(notification.title, {
      description: notification.message,
      duration: 5000,
    });
  }, []);

  // Simulate job progress updates
  useEffect(() => {
    // Add some initial jobs
    const initialJobs: ProcessingJob[] = [
      { id: 'job_1', fileId: 'file_1', fileName: 'sermon-2024-01-28.mp3', type: 'transcribe', status: 'processing', progress: 65, message: 'Transcribing audio...', createdAt: new Date() },
      { id: 'job_2', fileId: 'file_2', fileName: 'wednesday-study.mp4', type: 'optimize', status: 'pending', progress: 0, message: 'Queued for optimization', createdAt: new Date() },
      { id: 'job_3', fileId: 'file_3', fileName: 'teaching-grace.mp3', type: 'analyze', status: 'processing', progress: 45, message: 'Analyzing content...', createdAt: new Date() },
    ];
    
    setJobs(initialJobs);
    setPollingJobIds(new Set(['job_1', 'job_3']));
    
    // Add initial notifications
    addNotification({ type: 'info', title: 'Processing Started', message: '3 jobs are being processed' });
  }, [addNotification]);

  // Poll jobs for progress updates
  useEffect(() => {
    if (pollingJobIds.size === 0) return;

    const interval = setInterval(() => {
      setJobs(prevJobs => {
        return prevJobs.map(job => {
          if (!pollingJobIds.has(job.id) || job.status !== 'processing') return job;

          // Simulate progress update
          const newProgress = Math.min(job.progress + Math.random() * 15, 100);
          
          // Check for completion
          if (newProgress >= 100) {
            const completedJob = { ...job, progress: 100, status: 'completed' as const, completedAt: new Date() };
            
            // Add notification
            addNotification({
              type: 'success',
              title: 'Processing Complete',
              message: `${job.fileName} has been processed successfully`,
            });
            
            // Remove from polling
            setPollingJobIds(prev => {
              const next = new Set(prev);
              next.delete(job.id);
              return next;
            });
            
            return completedJob;
          }

          return { ...job, progress: newProgress };
        });
      });
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [pollingJobIds, addNotification]);

  // Live search with instant refetch
  const filteredFiles = useCallback(() => {
    let result = [...files];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(f => 
        f.name.toLowerCase().includes(searchLower) ||
        f.preacher.toLowerCase().includes(searchLower)
      );
    }

    // Preacher filter
    if (filters.preacher !== 'all') {
      result = result.filter(f => f.preacher === filters.preacher);
    }

    // Quality filter
    if (filters.quality !== 'all') {
      if (filters.quality === 'high') result = result.filter(f => f.quality >= 90);
      else if (filters.quality === 'medium') result = result.filter(f => f.quality >= 70 && f.quality < 90);
      else if (filters.quality === 'low') result = result.filter(f => f.quality < 70);
    }

    // Status filter
    if (filters.status !== 'all') {
      result = result.filter(f => f.status === filters.status);
    }

    // Date filter
    if (filters.dateRange !== 'all') {
      const now = new Date();
      const today = now.toISOString().split('T')[0];
      
      if (filters.dateRange === 'today') {
        result = result.filter(f => f.date === today);
      } else if (filters.dateRange === 'week') {
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        result = result.filter(f => new Date(f.date) >= weekAgo);
      } else if (filters.dateRange === 'month') {
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        result = result.filter(f => new Date(f.date) >= monthAgo);
      }
    }

    return result;
  }, [files, filters]);

  // Refetch files (simulates /sermons API call)
  const refetchFiles = useCallback(async () => {
    setIsRefetching(true);
    
    try {
      // In production: GET /sermons with filters
      // const params = new URLSearchParams();
      // if (filters.preacher !== 'all') params.append('preacher', filters.preacher);
      // if (filters.dateRange !== 'all') params.append('date', filters.dateRange);
      // ...
      // const response = await fetch(`/sermons?${params}`, {
      //   headers: { Authorization: `Bearer ${publicAnonKey}` },
      // });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Simulate some file changes
      setFiles(prev => {
        // Randomly update one file status
        const updated = [...prev];
        const randomIndex = Math.floor(Math.random() * updated.length);
        if (updated[randomIndex].status === 'processing') {
          updated[randomIndex] = { ...updated[randomIndex], status: 'ready', quality: 95 };
        }
        return updated;
      });
      
      addNotification({
        type: 'info',
        title: 'Files Refreshed',
        message: 'File list has been updated',
      });
    } catch (error) {
      toast.error('Failed to refresh files');
    } finally {
      setIsRefetching(false);
      setRefetchTrigger(prev => prev + 1);
    }
  }, [filters, addNotification]);

  // Trigger refetch when filters change (instant)
  useEffect(() => {
    const timer = setTimeout(() => {
      refetchFiles();
    }, 300); // Debounce filter changes

    return () => clearTimeout(timer);
  }, [filters, refetchFiles]);

  // Get file icon
  const getFileIcon = (type: string) => {
    return type.startsWith('audio/') ? <FileAudio className="w-4 h-4" /> : <FileVideo className="w-4 h-4" />;
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready': return <Badge className="bg-green-100 text-green-700">Ready</Badge>;
      case 'processing': return <Badge className="bg-blue-100 text-blue-700">Processing</Badge>;
      case 'failed': return <Badge className="bg-red-100 text-red-700">Failed</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Get quality badge
  const getQualityBadge = (quality: number) => {
    if (quality >= 90) return <Badge className="bg-green-100 text-green-700">{quality}%</Badge>;
    if (quality >= 70) return <Badge className="bg-yellow-100 text-yellow-700">{quality}%</Badge>;
    return <Badge className="bg-red-100 text-red-700">{quality}%</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header with Notifications */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Real-Time Features</h2>
          <p className="text-gray-500">Live processing updates and instant search</p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Notification Bell */}
          <div className="relative">
            <Button variant="outline" size="icon" onClick={() => setShowNotifications(!showNotifications)}>
              <Bell className="w-4 h-4" />
              {notifications.filter(n => !n.read).length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center">
                  {notifications.filter(n => !n.read).length}
                </span>
              )}
            </Button>
            
            {/* Notification Dropdown */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border p-4 z-50">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium">Notifications</h3>
                  <Button variant="ghost" size="sm" onClick={() => setNotifications([])}>
                    Clear
                  </Button>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="text-sm text-gray-500 text-center py-4">No notifications</p>
                  ) : (
                    notifications.map(notif => (
                      <div key={notif.id} className={cn(
                        'p-2 rounded text-sm',
                        notif.type === 'success' && 'bg-green-50 text-green-700',
                        notif.type === 'error' && 'bg-red-50 text-red-700',
                        notif.type === 'info' && 'bg-blue-50 text-blue-700',
                        notif.type === 'warning' && 'bg-yellow-50 text-yellow-700'
                      )}>
                        <p className="font-medium">{notif.title}</p>
                        <p className="text-xs opacity-80">{notif.message}</p>
                        <p className="text-xs opacity-60 mt-1">
                          {formatDistanceToNow(notif.timestamp, { addSuffix: true })}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          
          {/* Refresh Button */}
          <Button variant="outline" onClick={refetchFiles} disabled={isRefetching}>
            <RefreshCw className={cn('w-4 h-4 mr-2', isRefetching && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Live Search & Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="w-5 h-5" />
            Live Search & Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {/* Search Input */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search files, preachers..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-9"
                />
                {filters.search && (
                  <button
                    className="absolute right-3 top-1/2 -translate-y-1/2"
                    onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
                  >
                    <X className="w-4 h-4 text-gray-400 hover:text-gray-600" />
                  </button>
                )}
              </div>
            </div>

            {/* Preacher Filter */}
            <Select
              value={filters.preacher}
              onValueChange={(value) => setFilters(prev => ({ ...prev, preacher: value }))}
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Preacher" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Preachers</SelectItem>
                {mockPreachers.map(p => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Date Range Filter */}
            <Select
              value={filters.dateRange}
              onValueChange={(value) => setFilters(prev => ({ ...prev, dateRange: value }))}
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Date Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Time</SelectItem>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="week">Last 7 Days</SelectItem>
                <SelectItem value="month">Last 30 Days</SelectItem>
              </SelectContent>
            </Select>

            {/* Quality Filter */}
            <Select
              value={filters.quality}
              onValueChange={(value) => setFilters(prev => ({ ...prev, quality: value }))}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Quality" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Quality</SelectItem>
                <SelectItem value="high">High (90%+)</SelectItem>
                <SelectItem value="medium">Medium (70-90%)</SelectItem>
                <SelectItem value="low">Low (70% or less)</SelectItem>
              </SelectContent>
            </Select>

            {/* Status Filter */}
            <Select
              value={filters.status}
              onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="ready">Ready</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Active Filters Display */}
          {(filters.preacher !== 'all' || filters.dateRange !== 'all' || filters.quality !== 'all' || filters.status !== 'all' || filters.search) && (
            <div className="flex items-center gap-2 mt-3 pt-3 border-t flex-wrap">
              <span className="text-xs text-gray-500">Active filters:</span>
              {filters.preacher !== 'all' && (
                <Badge variant="secondary" className="cursor-pointer" onClick={() => setFilters(prev => ({ ...prev, preacher: 'all' }))}>
                  {filters.preacher} ×
                </Badge>
              )}
              {filters.dateRange !== 'all' && (
                <Badge variant="secondary" className="cursor-pointer" onClick={() => setFilters(prev => ({ ...prev, dateRange: 'all' }))}>
                  {filters.dateRange} ×
                </Badge>
              )}
              {filters.quality !== 'all' && (
                <Badge variant="secondary" className="cursor-pointer" onClick={() => setFilters(prev => ({ ...prev, quality: 'all' }))}>
                  Quality: {filters.quality} ×
                </Badge>
              )}
              {filters.status !== 'all' && (
                <Badge variant="secondary" className="cursor-pointer" onClick={() => setFilters(prev => ({ ...prev, status: 'all' }))}>
                  {filters.status} ×
                </Badge>
              )}
              {filters.search && (
                <Badge variant="secondary" className="cursor-pointer" onClick={() => setFilters(prev => ({ ...prev, search: '' }))}>
                  "{filters.search}" ×
                </Badge>
              )}
              <Button variant="ghost" size="sm" className="text-xs h-6" onClick={() => setFilters({
                preacher: 'all',
                dateRange: 'all',
                quality: 'all',
                status: 'all',
                search: '',
              })}>
                Clear all
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* File Results with Live Updates */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Files ({filteredFiles().length})</CardTitle>
            <span className="text-sm text-gray-500">
              {isRefetching ? 'Updating...' : 'Live'}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredFiles().map(file => (
              <div key={file.id} className="flex items-center gap-4 p-3 rounded-lg border hover:bg-gray-50">
                <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                  {getFileIcon(file.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium truncate">{file.name}</p>
                    {getStatusBadge(file.status)}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                    <span>{file.preacher}</span>
                    <span>{file.date}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500">Quality:</span>
                  {getQualityBadge(file.quality)}
                </div>
              </div>
            ))}
            
            {filteredFiles().length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Filter className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                <p>No files match your filters</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Real-Time Job Progress */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Processing Jobs (Live Progress)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {jobs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-300" />
                <p>No active jobs</p>
              </div>
            ) : (
              jobs.map(job => (
                <div key={job.id} className="p-4 rounded-lg border">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {job.status === 'processing' && (
                        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                      )}
                      <span className="font-medium">{job.fileName}</span>
                      <Badge variant="outline" className="text-xs">
                        {job.type.charAt(0).toUpperCase() + job.type.slice(1)}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      {job.status === 'completed' && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {job.status === 'failed' && (
                        <span className="text-red-500 text-sm">Failed</span>
                      )}
                      <span className="text-sm font-mono">{job.progress}%</span>
                    </div>
                  </div>
                  
                  <Progress 
                    value={job.progress} 
                    className={cn(
                      'h-2',
                      job.status === 'completed' && 'bg-green-100',
                      job.status === 'failed' && 'bg-red-100'
                    )} 
                  />
                  
                  {job.message && (
                    <p className="text-sm text-gray-500 mt-2">{job.message}</p>
                  )}
                  
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Started {formatDistanceToNow(job.createdAt, { addSuffix: true })}
                    </span>
                    {job.completedAt && (
                      <span>Completed {formatDistanceToNow(job.completedAt, { addSuffix: true })}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default RealTimeFeatures;
