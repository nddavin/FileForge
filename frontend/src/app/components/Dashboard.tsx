import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Progress } from '@/app/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import {
  Upload,
  Clock,
  AlertTriangle,
  Database,
  RefreshCw,
  TrendingUp,
  FileText,
  Activity,
  HardDrive,
  CheckCircle,
  XCircle,
  Play,
  Pause,
} from 'lucide-react';
import { cn, formatFileSize } from '@/app/components/ui/utils';
import { toast } from 'sonner';

// Stats interface
interface DashboardStats {
  uploadCount: number;
  uploadChange: number;
  processingQueue: number;
  failedJobs: number;
  failedChange: number;
  storageUsed: number;
  storageTotal: number;
  successRate: number;
  avgProcessingTime: number;
  recentUploads: number;
}

// Mock stats data (would come from /sermons/stats endpoint)
const mockStats: DashboardStats = {
  uploadCount: 1247,
  uploadChange: 12.5,
  processingQueue: 8,
  failedJobs: 15,
  failedChange: -5.2,
  storageUsed: 45.2,
  storageTotal: 100,
  successRate: 98.5,
  avgProcessingTime: 4.2,
  recentUploads: 23,
};

// Processing job interface
interface ProcessingJob {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  startedAt: Date;
  eta?: string;
}

// Mock processing jobs
const mockJobs: ProcessingJob[] = [
  { id: '1', name: 'Transcribe: Sunday Sermon.mp3', status: 'processing', progress: 75, startedAt: new Date(), eta: '2m' },
  { id: '2', name: 'Generate Thumbnails', status: 'processing', progress: 45, startedAt: new Date(), eta: '5m' },
  { id: '3', name: 'Audio Enhancement', status: 'pending', progress: 0, startedAt: new Date() },
  { id: '4', name: 'Metadata Extraction', status: 'completed', progress: 100, startedAt: new Date() },
  { id: '5', name: 'Upload to CDN', status: 'failed', progress: 0, startedAt: new Date() },
];

// TanStack Query-like hook for data fetching with auto-refresh
function useDashboardStats(refreshInterval = 30000) {
  const [stats, setStats] = useState<DashboardStats>(mockStats);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefetching, setIsRefetching] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchStats = async () => {
    setIsRefetching(true);
    try {
      // In production, this would call /sermons/stats
      // const response = await fetch('/sermons/stats');
      // const data = await response.json();
      // setStats(data);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('Failed to refresh stats');
    } finally {
      setIsRefetching(false);
    }
  };

  React.useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { stats, isLoading, isRefetching, lastUpdated, refetch: fetchStats };
}

function useProcessingJobs(refreshInterval = 5000) {
  const [jobs, setJobs] = useState<ProcessingJob[]>(mockJobs);
  const [isLoading, setIsLoading] = useState(false);

  const fetchJobs = async () => {
    try {
      // In production: await fetch('/sermons/processing-jobs')
      await new Promise(resolve => setTimeout(resolve, 300));
      // Jobs updated via WebSocket in real implementation
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  React.useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { jobs, isLoading };
}

export function Dashboard() {
  const { stats, isRefetching, lastUpdated, refetch } = useDashboardStats();
  const { jobs } = useProcessingJobs();
  const [activeTab, setActiveTab] = useState('overview');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return 'text-blue-500';
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'processing': return 'bg-blue-100 text-blue-700';
      case 'completed': return 'bg-green-100 text-green-700';
      case 'failed': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Real-time sermon processing overview
            <span className="ml-2 text-xs text-gray-400">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={cn('w-4 h-4 mr-2', isRefetching && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Upload Count */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Uploads</p>
                <p className="text-3xl font-bold mt-1">{stats.uploadCount.toLocaleString()}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-600">+{stats.uploadChange}%</span>
                </div>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <Upload className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Processing Queue */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Processing Queue</p>
                <p className="text-3xl font-bold mt-1">{stats.processingQueue}</p>
                <p className="text-sm text-gray-400 mt-1">Active jobs</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <Activity className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={Math.min(stats.processingQueue * 10, 100)} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Failed Jobs */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Failed Jobs</p>
                <p className="text-3xl font-bold mt-1">{stats.failedJobs}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className={cn('w-4 h-4', stats.failedChange < 0 ? 'text-green-500' : 'text-red-500')} />
                  <span className={cn('text-sm', stats.failedChange < 0 ? 'text-green-600' : 'text-red-600')}>
                    {stats.failedChange > 0 ? '+' : ''}{stats.failedChange}%
                  </span>
                </div>
              </div>
              <div className="p-3 bg-red-100 rounded-full">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Storage Usage */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Storage Used</p>
                <p className="text-3xl font-bold mt-1">{formatFileSize(stats.storageUsed * 1024 * 1024 * 1024)}</p>
                <p className="text-sm text-gray-400 mt-1">of {formatFileSize(stats.storageTotal * 1024 * 1024 * 1024)}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <HardDrive className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={(stats.storageUsed / stats.storageTotal) * 100} className="h-2" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Details */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="processing">Processing Queue</TabsTrigger>
          <TabsTrigger value="recent">Recent Activity</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span>Success Rate</span>
                  </div>
                  <span className="font-semibold">{stats.successRate}%</span>
                </div>
                <Progress value={stats.successRate} className="h-2" />
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Clock className="w-5 h-5 text-blue-500" />
                    <span>Avg Processing Time</span>
                  </div>
                  <span className="font-semibold">{stats.avgProcessingTime} min</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-purple-500" />
                    <span>Recent Uploads (7 days)</span>
                  </div>
                  <span className="font-semibold">{stats.recentUploads}</span>
                </div>
              </CardContent>
            </Card>

            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">System Health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-green-600" />
                    <span>API Status</span>
                  </div>
                  <Badge className="bg-green-100 text-green-700">Operational</Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Database className="w-5 h-5 text-green-600" />
                    <span>Database</span>
                  </div>
                  <Badge className="bg-green-100 text-green-700">Connected</Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-green-600" />
                    <span>Celery Workers</span>
                  </div>
                  <Badge className="bg-green-100 text-green-700">4 Active</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Processing Queue Tab */}
        <TabsContent value="processing" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Processing Queue</CardTitle>
                <Badge variant="secondary">{jobs.filter(j => j.status === 'processing').length} active</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {jobs.map(job => (
                  <div
                    key={job.id}
                    className="flex items-center gap-4 p-4 rounded-lg border"
                  >
                    <div className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center',
                      job.status === 'processing' ? 'bg-blue-100' :
                      job.status === 'completed' ? 'bg-green-100' :
                      job.status === 'failed' ? 'bg-red-100' : 'bg-gray-100'
                    )}>
                      {job.status === 'processing' && <Play className="w-5 h-5 text-blue-600" />}
                      {job.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-600" />}
                      {job.status === 'failed' && <XCircle className="w-5 h-5 text-red-600" />}
                      {job.status === 'pending' && <Pause className="w-5 h-5 text-gray-600" />}
                    </div>
                    
                    <div className="flex-1">
                      <p className="font-medium">{job.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge className={cn('text-xs', getStatusBg(job.status))}>
                          {job.status}
                        </Badge>
                        {job.eta && (
                          <span className="text-xs text-gray-500">ETA: {job.eta}</span>
                        )}
                      </div>
                      {job.status === 'processing' && (
                        <Progress value={job.progress} className="h-1 mt-2" />
                      )}
                    </div>
                    
                    <div className="text-right">
                      <span className={cn('font-semibold', getStatusColor(job.status))}>
                        {job.status === 'processing' ? `${job.progress}%` : job.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recent Activity Tab */}
        <TabsContent value="recent" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { action: 'Upload', file: 'Sunday Sermon.mp3', time: '2 min ago', status: 'success' },
                  { action: 'Transcribe', file: 'Wednesday Prayer.mp3', time: '5 min ago', status: 'success' },
                  { action: 'Process', file: 'Youth Meeting.mp4', time: '10 min ago', status: 'processing' },
                  { action: 'Failed', file: 'Test Audio.wav', time: '15 min ago', status: 'failed' },
                  { action: 'Publish', file: 'Sunday Sermon.mp3', time: '1 hour ago', status: 'success' },
                ].map((activity, index) => (
                  <div key={index} className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50">
                    <div className={cn(
                      'w-2 h-2 rounded-full',
                      activity.status === 'success' ? 'bg-green-500' :
                      activity.status === 'processing' ? 'bg-blue-500' : 'bg-red-500'
                    )} />
                    <div className="flex-1">
                      <p className="text-sm">
                        <span className="font-medium">{activity.action}</span>
                        {' - '}
                        <span className="text-gray-600">{activity.file}</span>
                      </p>
                    </div>
                    <span className="text-xs text-gray-400">{activity.time}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default Dashboard;
