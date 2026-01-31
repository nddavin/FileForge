import React, { useState, useCallback, useEffect } from 'react';
import { projectId, publicAnonKey } from '@/utils/supabase/info';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Switch } from '@/app/components/ui/switch';
import { Progress } from '@/app/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select';
import {
  Workflow,
  Settings,
  Play,
  Pause,
  Plus,
  Trash2,
  Edit2,
  Save,
  X,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  BarChart3,
  RefreshCw,
  Rss,
  MessageSquare,
  Users,
  Database,
  Activity,
  Bell,
  FileText,
  Upload,
  Download,
  Eye,
  MoreHorizontal,
  Loader2,
  GitBranch,
  ArrowRight,
  FileAudio,
  Brain,
  Wand2,
  Share2,
} from 'lucide-react';
import { cn } from '@/app/components/ui/utils';
import { toast } from 'sonner';

// Workflow node types
type NodeType = 'trigger' | 'process' | 'condition' | 'action' | 'output';

// Node definition
interface WorkflowNode {
  id: string;
  type: NodeType;
  name: string;
  config: Record<string, any>;
  position: { x: number; y: number };
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: { source: string; target: string }[];
  active: boolean;
  lastRun?: Date;
  config?: Record<string, any>;
}

// Pipeline stage definitions for the visual builder
const PIPELINE_STAGES = [
  { id: 'upload', name: 'Upload', icon: Upload, color: 'bg-blue-500', description: 'File upload trigger' },
  { id: 'extract', name: 'Extract', icon: FileAudio, color: 'bg-green-500', description: 'Extract audio/video' },
  { id: 'analyze', name: 'Analyze', icon: Brain, color: 'bg-purple-500', description: 'AI analysis' },
  { id: 'optimize', name: 'Optimize', icon: Wand2, color: 'bg-orange-500', description: 'Format optimization' },
  { id: 'distribute', name: 'Distribute', icon: Share2, color: 'bg-cyan-500', description: 'Publish & share' },
];

// Integration types
interface Integration {
  id: string;
  name: string;
  icon: React.ReactNode;
  status: 'connected' | 'disconnected' | 'error' | 'syncing';
  lastSync?: string;
  error?: string;
  details: Record<string, any>;
  enabled: boolean;
}

// Mock integrations
const defaultIntegrations: Integration[] = [
  { 
    id: 'slack', 
    name: 'Slack', 
    icon: <MessageSquare className="w-5 h-5" />, 
    status: 'connected', 
    lastSync: '2 min ago', 
    details: { channels: 3, workspace: 'church-team' },
    enabled: true,
  },
  { 
    id: 'teams', 
    name: 'Microsoft Teams', 
    icon: <Users className="w-5 h-5" />, 
    status: 'connected', 
    lastSync: '5 min ago', 
    details: { teams: 2, tenant: 'church.org' },
    enabled: true,
  },
  { 
    id: 'salesforce', 
    name: 'Salesforce', 
    icon: <Database className="w-5 h-5" />, 
    status: 'error', 
    lastSync: '2 hours ago', 
    error: 'Rate limit exceeded',
    details: { objects: ['Contact', 'Campaign'] },
    enabled: false,
  },
];

// Mock batch jobs
const mockBatchJobs = [
  { id: '1', name: 'Transcribe Sermons', progress: 75, status: 'processing' as const, eta: '2m' },
  { id: '2', name: 'Generate Thumbnails', progress: 100, status: 'completed' as const, eta: null },
  { id: '3', name: 'Upload to CDN', progress: 45, status: 'processing' as const, eta: '5m' },
  { id: '4', name: 'Send Notifications', progress: 0, status: 'pending' as const, eta: '10m' },
];

// Processing stats
const mockStats = {
  totalProcessed: 1247,
  avgProcessingTime: '4.2 min',
  successRate: 98.5,
  storageUsed: '45.2 GB',
  apiCalls: 15842,
  errorRate: 1.2,
};

export function WorkflowAndIntegrations() {
  const [activeTab, setActiveTab] = useState<'workflows' | 'jobs' | 'integrations' | 'stats'>('workflows');
  
  // Workflow state
  const [workflows, setWorkflows] = useState<Workflow[]>([
    {
      id: '1',
      name: 'Sermon Processing Pipeline',
      description: 'Auto-transcribe, generate metadata, and notify team',
      active: true,
      lastRun: new Date(),
      nodes: [
        { id: '1', type: 'trigger', name: 'Upload', position: { x: 50, y: 150 }, config: {} },
        { id: '2', type: 'process', name: 'Extract Audio', position: { x: 200, y: 150 }, config: { format: 'mp3' } },
        { id: '3', type: 'process', name: 'AI Analysis', position: { x: 350, y: 150 }, config: { model: 'whisper' } },
        { id: '4', type: 'process', name: 'Optimize', position: { x: 500, y: 150 }, config: { profile: 'web' } },
        { id: '5', type: 'action', name: 'Notify', position: { x: 650, y: 100 }, config: { channel: 'slack' } },
        { id: '6', type: 'output', name: 'Archive', position: { x: 650, y: 200 }, config: {} },
      ],
      edges: [
        { source: '1', target: '2' },
        { source: '2', target: '3' },
        { source: '3', target: '4' },
        { source: '4', target: '5' },
        { source: '4', target: '6' },
      ],
    },
  ]);
  
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(workflows[0]);
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [editingPipeline, setEditingPipeline] = useState<string[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  
  // Integration state
  const [integrations, setIntegrations] = useState<Integration[]>(defaultIntegrations);
  const [isSyncing, setIsSyncing] = useState<string | null>(null);
  
  // Batch jobs state
  const [batchJobs, setBatchJobs] = useState(mockBatchJobs);
  
  // RSS monitors state
  const [rssMonitors, setRssMonitors] = useState([
    { id: '1', url: 'https://feeds.sermon.net', enabled: true, lastCheck: new Date() },
    { id: '2', url: 'https://example.com/podcast', enabled: false, lastCheck: null },
  ]);

  // Fetch integration status from API
  const fetchIntegrationStatus = useCallback(async () => {
    try {
      // In production: GET /integrations/status
      // const response = await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/integrations/status`, {
      //   headers: { Authorization: `Bearer ${publicAnonKey}` },
      // });
      // const data = await response.json();
      // setIntegrations(data);
    } catch (error) {
      console.error('Failed to fetch integration status:', error);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'integrations') {
      fetchIntegrationStatus();
    }
  }, [activeTab, fetchIntegrationStatus]);

  // Get node color
  const getNodeColor = (type: NodeType) => {
    switch (type) {
      case 'trigger': return 'bg-blue-500';
      case 'process': return 'bg-green-500';
      case 'condition': return 'bg-yellow-500';
      case 'action': return 'bg-purple-500';
      case 'output': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected': return <Badge className="bg-green-100 text-green-700">Connected</Badge>;
      case 'error': return <Badge className="bg-red-100 text-red-700">Error</Badge>;
      case 'syncing': return <Badge className="bg-blue-100 text-blue-700">Syncing</Badge>;
      case 'processing': return <Badge className="bg-blue-100 text-blue-700">Processing</Badge>;
      case 'completed': return <Badge className="bg-gray-100 text-gray-700">Completed</Badge>;
      case 'pending': return <Badge className="bg-yellow-100 text-yellow-700">Pending</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Toggle workflow active state
  const toggleWorkflow = (id: string) => {
    setWorkflows(prev => prev.map(w =>
      w.id === id ? { ...w, active: !w.active } : w
    ));
    const workflow = workflows.find(w => w.id === id);
    toast.success(workflow?.active ? 'Workflow paused' : 'Workflow activated');
  };

  // Open pipeline builder
  const openPipelineBuilder = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setEditingPipeline(workflow.nodes.map(n => n.name));
    setIsBuilderOpen(true);
  };

  // Save pipeline configuration
  const savePipelineConfig = async () => {
    if (!selectedWorkflow) return;
    
    try {
      // In production: POST /workflows/execute or PUT /workflows/{id}
      // const response = await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/workflows/${selectedWorkflow.id}`, {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${publicAnonKey}` },
      //   body: JSON.stringify({ nodes: editingPipeline }),
      // });

      setWorkflows(prev => prev.map(w =>
        w.id === selectedWorkflow.id
          ? { ...w, nodes: w.nodes.map((n, i) => ({ ...n, name: editingPipeline[i] || n.name })) }
          : w
      ));

      toast.success('Pipeline configuration saved');
      setIsBuilderOpen(false);
    } catch (error) {
      toast.error('Failed to save pipeline configuration');
    }
  };

  // Execute workflow
  const executeWorkflow = async (workflow: Workflow) => {
    setIsExecuting(true);
    
    try {
      // In production: POST /workflows/execute
      // const response = await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/workflows/execute`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${publicAnonKey}` },
      //   body: JSON.stringify({ workflow_id: workflow.id }),
      // });

      await new Promise(resolve => setTimeout(resolve, 2000));

      toast.success(`Workflow "${workflow.name}" executed successfully`);
      setWorkflows(prev => prev.map(w =>
        w.id === workflow.id ? { ...w, lastRun: new Date() } : w
      ));
    } catch (error) {
      toast.error('Failed to execute workflow');
    } finally {
      setIsExecuting(false);
    }
  };

  // Toggle RSS monitor
  const toggleRssMonitor = (id: string) => {
    setRssMonitors(prev => prev.map(m =>
      m.id === id ? { ...m, enabled: !m.enabled } : m
    ));
    toast.success('RSS monitor updated');
  };

  // Sync integration
  const syncIntegration = async (integrationId: string) => {
    setIsSyncing(integrationId);
    
    try {
      // In production: POST /integrations/{id}/sync
      // await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/integrations/${integrationId}/sync`, {
      //   method: 'POST',
      //   headers: { Authorization: `Bearer ${publicAnonKey}` },
      // });

      await new Promise(resolve => setTimeout(resolve, 2000));

      setIntegrations(prev => prev.map(i =>
        i.id === integrationId
          ? { ...i, status: 'connected' as const, lastSync: 'Just now', error: undefined }
          : i
      ));

      toast.success(`${integrations.find(i => i.id === integrationId)?.name} synced successfully`);
    } catch (error) {
      toast.error('Sync failed');
    } finally {
      setIsSyncing(null);
    }
  };

  // Toggle integration enabled state
  const toggleIntegration = (integrationId: string) => {
    setIntegrations(prev => prev.map(i =>
      i.id === integrationId ? { ...i, enabled: !i.enabled } : i
    ));
    toast.success('Integration updated');
  };

  // Cancel batch job
  const cancelJob = (id: string) => {
    setBatchJobs(prev => prev.filter(j => j.id !== id));
    toast.success('Job cancelled');
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex items-center gap-2 border-b pb-2">
        <Button
          variant={activeTab === 'workflows' ? 'secondary' : 'ghost'}
          onClick={() => setActiveTab('workflows')}
          className="gap-2"
        >
          <GitBranch className="w-4 h-4" />
          Pipelines
        </Button>
        <Button
          variant={activeTab === 'jobs' ? 'secondary' : 'ghost'}
          onClick={() => setActiveTab('jobs')}
          className="gap-2"
        >
          <Activity className="w-4 h-4" />
          Batch Jobs
        </Button>
        <Button
          variant={activeTab === 'integrations' ? 'secondary' : 'ghost'}
          onClick={() => setActiveTab('integrations')}
          className="gap-2"
        >
          <Zap className="w-4 h-4" />
          Integrations
        </Button>
        <Button
          variant={activeTab === 'stats' ? 'secondary' : 'ghost'}
          onClick={() => setActiveTab('stats')}
          className="gap-2"
        >
          <BarChart3 className="w-4 h-4" />
          Stats
        </Button>
      </div>

      {/* Pipelines Tab */}
      {activeTab === 'workflows' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Workflow List */}
          <Card className="lg:col-span-1">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Pipelines</CardTitle>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-1" />
                  New
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {workflows.map(workflow => (
                <div
                  key={workflow.id}
                  className={cn(
                    'p-3 rounded-lg border cursor-pointer transition-colors',
                    selectedWorkflow?.id === workflow.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                  )}
                  onClick={() => setSelectedWorkflow(workflow)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        'w-2 h-2 rounded-full',
                        workflow.active ? 'bg-green-500' : 'bg-gray-300'
                      )} />
                      <span className="font-medium text-sm">{workflow.name}</span>
                    </div>
                    <Switch
                      checked={workflow.active}
                      onCheckedChange={() => toggleWorkflow(workflow.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1 truncate">{workflow.description}</p>
                  {workflow.lastRun && (
                    <p className="text-xs text-gray-400 mt-1">
                      Last run: {workflow.lastRun.toLocaleTimeString()}
                    </p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Workflow Builder */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{selectedWorkflow?.name}</CardTitle>
                  <p className="text-sm text-gray-500">{selectedWorkflow?.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => openPipelineBuilder(selectedWorkflow!)}>
                    <Edit2 className="w-4 h-4 mr-1" />
                    Edit Pipeline
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => executeWorkflow(selectedWorkflow!)}
                    disabled={isExecuting}
                  >
                    {isExecuting ? (
                      <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4 mr-1" />
                    )}
                    Run
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Visual Pipeline Display */}
              <div className="relative bg-gray-50 rounded-lg p-6 min-h-[300px]">
                {/* Grid background */}
                <div className="absolute inset-0 opacity-10 pointer-events-none" style={{
                  backgroundImage: 'radial-gradient(circle, #000 1px, transparent 1px)',
                  backgroundSize: '20px 20px',
                }} />

                {/* Pipeline nodes with arrows */}
                <div className="flex items-center justify-center gap-2">
                  {selectedWorkflow?.nodes.map((node, index) => {
                    const NodeIcon = PIPELINE_STAGES.find(s => s.name.toLowerCase() === node.name.toLowerCase().split(' ')[0].toLowerCase())?.icon || Activity;
                    const stageColor = PIPELINE_STAGES.find(s => s.name.toLowerCase() === node.name.toLowerCase().split(' ')[0].toLowerCase())?.color || 'bg-gray-500';
                    
                    return (
                      <React.Fragment key={node.id}>
                        {/* Node */}
                        <div className={cn(
                          'flex flex-col items-center gap-2 p-4 rounded-lg border-2 bg-white shadow-sm min-w-[120px]',
                          stageColor.replace('bg-', 'border-')
                        )}>
                          <div className={cn('p-2 rounded-full', stageColor)}>
                            <NodeIcon className="w-5 h-5 text-white" />
                          </div>
                          <span className="text-sm font-medium text-center">{node.name}</span>
                        </div>
                        
                        {/* Arrow to next node */}
                        {index < (selectedWorkflow.nodes.length - 1) && (
                          <ArrowRight className="w-6 h-6 text-gray-300 flex-shrink-0" />
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>

              {/* Pipeline Stages Legend */}
              <div className="flex items-center gap-4 mt-4 pt-4 border-t flex-wrap">
                <span className="text-sm font-medium text-gray-500">Pipeline Stages:</span>
                {PIPELINE_STAGES.map(stage => {
                  const StageIcon = stage.icon;
                  return (
                    <div key={stage.id} className="flex items-center gap-2">
                      <div className={cn('w-3 h-3 rounded-full', stage.color)} />
                      <span className="text-xs">{stage.name}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Pipeline Builder Dialog */}
      <Dialog open={isBuilderOpen} onOpenChange={setIsBuilderOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Edit Pipeline: {selectedWorkflow?.name}</DialogTitle>
            <DialogDescription>
              Configure the pipeline stages in order. Drag to reorder or change stages.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Pipeline stage configuration */}
            <div className="space-y-3">
              {PIPELINE_STAGES.map((stage, index) => {
                const currentName = editingPipeline[index] || stage.name;
                const isInPipeline = editingPipeline.includes(stage.name);
                
                return (
                  <div
                    key={stage.id}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-lg border transition-colors',
                      isInPipeline ? 'bg-white border-gray-200' : 'bg-gray-50 border-dashed border-gray-300'
                    )}
                  >
                    <div className={cn('p-2 rounded-lg', stage.color)}>
                      <stage.icon className="w-4 h-4 text-white" />
                    </div>
                    
                    <div className="flex-1">
                      <p className="font-medium text-sm">{stage.name}</p>
                      <p className="text-xs text-gray-500">{stage.description}</p>
                    </div>
                    
                    <Select
                      value={currentName}
                      onValueChange={(value) => {
                        const newPipeline = [...editingPipeline];
                        newPipeline[index] = value;
                        setEditingPipeline(newPipeline);
                      }}
                    >
                      <SelectTrigger className="w-[180px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PIPELINE_STAGES.map(s => (
                          <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        const newPipeline = editingPipeline.filter((_, i) => i !== index);
                        setEditingPipeline(newPipeline);
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                );
              })}
            </div>
            
            {/* Add stage button */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setEditingPipeline([...editingPipeline, 'Optimize'])}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Stage
            </Button>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsBuilderOpen(false)}>
              Cancel
            </Button>
            <Button onClick={savePipelineConfig}>
              <Save className="w-4 h-4 mr-2" />
              Save Configuration
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Batch Jobs Tab */}
      {activeTab === 'jobs' && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Celery Batch Jobs</CardTitle>
              <Button size="sm">
                <Plus className="w-4 h-4 mr-1" />
                New Job
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {batchJobs.map(job => (
                <div key={job.id} className="flex items-center gap-4 p-4 rounded-lg border">
                  <div className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center',
                    job.status === 'processing' ? 'bg-blue-100' :
                    job.status === 'completed' ? 'bg-green-100' : 'bg-gray-100'
                  )}>
                    {job.status === 'processing' ? (
                      <Activity className="w-5 h-5 text-blue-500 animate-pulse" />
                    ) : job.status === 'completed' ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <Clock className="w-5 h-5 text-gray-500" />
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{job.name}</span>
                      <span className="text-sm text-gray-500">
                        {job.eta ? `ETA: ${job.eta}` : 'Completed'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={job.progress} className="flex-1 h-2" />
                      <span className="text-sm font-mono w-12 text-right">{job.progress}%</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusBadge(job.status)}
                    {job.status === 'processing' && (
                      <Button variant="outline" size="sm" onClick={() => cancelJob(job.id)}>
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrations Tab */}
      {activeTab === 'integrations' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Integration Cards with Status */}
          {integrations.map(integration => (
            <Card key={integration.id}>
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className={cn(
                    'p-3 rounded-lg',
                    integration.status === 'connected' ? 'bg-green-100' :
                    integration.status === 'error' ? 'bg-red-100' :
                    integration.status === 'syncing' ? 'bg-blue-100' : 'bg-gray-100'
                  )}>
                    <div className={cn(
                      integration.status === 'connected' ? 'text-green-600' :
                      integration.status === 'error' ? 'text-red-600' :
                      integration.status === 'syncing' ? 'text-blue-600' : 'text-gray-600'
                    )}>
                      {integration.status === 'syncing' ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        integration.icon
                      )}
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">{integration.name}</h3>
                      <Switch
                        checked={integration.enabled}
                        onCheckedChange={() => toggleIntegration(integration.id)}
                      />
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusBadge(integration.status)}
                    </div>
                    <p className="text-sm text-gray-500 mt-2">
                      Last sync: {integration.lastSync || 'Never'}
                    </p>
                    {integration.error && (
                      <p className="text-sm text-red-500 mt-1">{integration.error}</p>
                    )}
                    <div className="flex flex-wrap gap-1 mt-2">
                      {Object.entries(integration.details).map(([key, value]) => (
                        <Badge key={key} variant="outline" className="text-xs">
                          {key}: {value}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 mt-4 pt-4 border-t">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => syncIntegration(integration.id)}
                    disabled={isSyncing !== null || !integration.enabled}
                  >
                    <RefreshCw className={cn(
                      'w-3 h-3 mr-1',
                      isSyncing === integration.id && 'animate-spin'
                    )} />
                    Sync Now
                  </Button>
                  <Button variant="outline" size="sm">
                    <Settings className="w-3 h-3 mr-1" />
                    Configure
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* RSS Feed Monitor */}
          <Card className="md:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Rss className="w-5 h-5" />
                RSS Feed Monitor
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {rssMonitors.map(feed => (
                  <div key={feed.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'w-2 h-2 rounded-full',
                        feed.enabled ? 'bg-green-500' : 'bg-gray-300'
                      )} />
                      <div>
                        <p className="text-sm font-medium">{feed.url}</p>
                        <p className="text-xs text-gray-500">
                          {feed.lastCheck ? `Last check: ${feed.lastCheck.toLocaleString()}` : 'Never checked'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={feed.enabled}
                        onCheckedChange={() => toggleRssMonitor(feed.id)}
                      />
                      <Button variant="ghost" size="icon">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="mt-4">
                <Plus className="w-4 h-4 mr-1" />
                Add RSS Feed
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{mockStats.totalProcessed}</p>
                    <p className="text-xs text-gray-500">Files Processed</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Clock className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{mockStats.avgProcessingTime}</p>
                    <p className="text-xs text-gray-500">Avg Time</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{mockStats.successRate}%</p>
                    <p className="text-xs text-gray-500">Success Rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <Database className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{mockStats.storageUsed}</p>
                    <p className="text-xs text-gray-500">Storage</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 rounded-lg">
                    <Zap className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{mockStats.apiCalls.toLocaleString()}</p>
                    <p className="text-xs text-gray-500">API Calls</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{mockStats.errorRate}%</p>
                    <p className="text-xs text-gray-500">Error Rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Placeholder */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Processing Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-16 h-16 text-gray-300" />
                  <span className="ml-2 text-gray-400">Chart placeholder</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Error Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <Activity className="w-16 h-16 text-gray-300" />
                  <span className="ml-2 text-gray-400">Chart placeholder</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowAndIntegrations;
