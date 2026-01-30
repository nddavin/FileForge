import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { supabase, teamMembers } from '@/lib/supabase';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Textarea } from '@/app/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/app/components/ui/select';
import { Progress } from '@/app/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/app/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/app/components/ui/form';
import {
  Play,
  Pause,
  Clock,
  Users,
  BookOpen,
  Tag,
  Target,
  Zap,
  Globe,
  Radio,
  Archive,
  Settings,
  Edit2,
  CheckCircle,
  AlertTriangle,
  FileAudio,
  FileVideo,
  Mic,
  TrendingUp,
  BarChart2,
  Speaker,
  Calendar,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash2,
  Save,
  RefreshCw,
  Loader2,
  Scan,
  Brain,
  Shield,
  UserCheck,
  Wand2,
  Loader,
} from 'lucide-react';
import { cn, formatFileSize, formatDuration } from '@/app/components/ui/utils';
import { toast } from 'sonner';
import { useForm } from 'react-hook-form';

// Mock AI-extracted segments data
const mockSegments = [
  { id: '1', start: 0, end: 120, type: 'intro', title: 'Opening Prayer', speaker: 'Pastor John', scripture: '', confidence: 0.95 },
  { id: '2', start: 120, end: 480, type: 'teaching', title: 'The Power of Faith', speaker: 'Pastor John', scripture: 'Hebrews 11:1-6', confidence: 0.92 },
  { id: '3', start: 480, end: 900, type: 'teaching', title: 'Examples of Faith', speaker: 'Pastor John', scripture: 'Hebrews 11:7-12', confidence: 0.89 },
  { id: '4', start: 900, end: 1080, type: 'illustration', title: 'Personal Story', speaker: 'Pastor John', scripture: '', confidence: 0.88 },
  { id: '5', start: 1080, end: 1380, type: 'application', title: 'Living by Faith Today', speaker: 'Pastor John', scripture: 'James 2:14-17', confidence: 0.91 },
  { id: '6', start: 1380, end: 1500, type: 'conclusion', title: 'Closing Remarks', speaker: 'Pastor John', scripture: '', confidence: 0.94 },
];

const mockThemes = ['Faith', 'Grace', 'Salvation', 'Obedience', 'Trust', 'Miracles'];
const mockTeamMembers = [
  { id: '1', name: 'Pastor John', role: 'Preacher', available: true },
  { id: '2', name: 'Sarah Miller', role: 'Editor', available: true },
  { id: '3', name: 'Mike Johnson', role: 'Reviewer', available: false },
  { id: '4', name: 'Emily Davis', role: 'Uploader', available: true },
];

// Pipeline stages for processing timeline
const PIPELINE_STAGES = [
  { id: 'component_detection', label: 'Component Detection', icon: Scan, description: 'Identifying sermon segments and audio/video components' },
  { id: 'ai_analysis', label: 'AI Analysis', icon: Brain, description: 'Extracting themes, scripture references, and insights' },
  { id: 'quality_check', label: 'Quality Check', icon: Shield, description: 'Verifying audio/video quality and metadata accuracy' },
  { id: 'team_assignment', label: 'Team Assignment', icon: UserCheck, description: 'Assigning team members for review and publishing' },
];

interface TeamMember {
  id: string;
  name: string;
  role?: string;
  available?: boolean;
}

interface Segment {
  id: string;
  start: number;
  end: number;
  type: 'intro' | 'teaching' | 'illustration' | 'application' | 'conclusion';
  title: string;
  speaker: string;
  scripture: string;
  confidence: number;
}

interface SermonMetadata {
  title: string;
  speaker: string;
  series: string;
  date: string;
  location: string;
  scripture: string[];
  themes: string[];
  tags: string[];
  description: string;
}

interface ProcessingStatus {
  currentStage: string;
  progress: number;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  message?: string;
  completedAt?: string;
}

export function SermonProcessingUI() {
  const { files, loading } = useFileManager();
  const [selectedFile, setSelectedFile] = useState(files[0] || null);
  const [segments, setSegments] = useState<Segment[]>(mockSegments);
  const [expandedSegments, setExpandedSegments] = useState<Set<string>>(new Set(['1', '2']));
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  
  // Metadata Editor Dialog state
  const [isMetadataDialogOpen, setIsMetadataDialogOpen] = useState(false);
  const [isSavingMetadata, setIsSavingMetadata] = useState(false);
  
  // Processing Timeline state
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    currentStage: 'quality_check',
    progress: 75,
    status: 'in_progress',
    message: 'Analyzing audio quality metrics...',
  });
  
  // Optimization state
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationProfile, setOptimizationProfile] = useState<string | null>(null);
  
  const [teamMembersList, setTeamMembersList] = useState<TeamMember[]>(mockTeamMembers);
  const [loadingTeam, setLoadingTeam] = useState(false);

  // Form for metadata editing
  const metadataForm = useForm<SermonMetadata>({
    defaultValues: {
      title: selectedFile?.name || '',
      speaker: 'Pastor John',
      series: 'Faith Series',
      date: new Date().toISOString().split('T')[0],
      location: 'Main Sanctuary',
      scripture: [],
      themes: ['Faith', 'Grace'],
      tags: ['faith', 'sermon', '2024'],
      description: '',
    },
  });

  const themes = useMemo(() => {
    const allThemes = new Set<string>();
    segments.forEach(s => {
      if (s.type === 'teaching') allThemes.add('Faith');
      if (s.type === 'application') allThemes.add('Grace');
    });
    return Array.from(allThemes);
  }, [segments]);

  const totalDuration = useMemo(() => {
    return segments.reduce((acc, s) => acc + (s.end - s.start), 0);
  }, [segments]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const toggleSegment = (id: string) => {
    const newExpanded = new Set(expandedSegments);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedSegments(newExpanded);
  };

  const getSegmentColor = (type: string) => {
    switch (type) {
      case 'intro': return 'bg-blue-100 border-blue-300';
      case 'teaching': return 'bg-green-100 border-green-300';
      case 'illustration': return 'bg-purple-100 border-purple-300';
      case 'application': return 'bg-orange-100 border-orange-300';
      case 'conclusion': return 'bg-gray-100 border-gray-300';
      default: return 'bg-gray-100';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'intro': return 'Introduction';
      case 'teaching': return 'Teaching';
      case 'illustration': return 'Illustration';
      case 'application': return 'Application';
      case 'conclusion': return 'Conclusion';
      default: return type;
    }
  };

  const getStageStatus = (stageId: string): 'completed' | 'in_progress' | 'pending' => {
    const stageIndex = PIPELINE_STAGES.findIndex(s => s.id === stageId);
    const currentIndex = PIPELINE_STAGES.findIndex(s => s.id === processingStatus.currentStage);
    
    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'in_progress';
    return 'pending';
  };

  // Fetch real-time processing updates from /sermons/{id}/quality
  const fetchProcessingStatus = useCallback(async () => {
    if (!selectedFile?.id) return;
    
    try {
      // In production, this would fetch from /sermons/{id}/quality
      // const response = await fetch(`/sermons/${selectedFile.id}/quality`);
      // const data = await response.json();
      // setProcessingStatus(data);
      
      // Simulating real-time updates for demo
      setProcessingStatus(prev => {
        const stageIndex = PIPELINE_STAGES.findIndex(s => s.id === prev.currentStage);
        if (stageIndex < PIPELINE_STAGES.length - 1 && prev.status === 'completed') {
          return {
            ...prev,
            currentStage: PIPELINE_STAGES[stageIndex + 1].id,
            progress: ((stageIndex + 2) / PIPELINE_STAGES.length) * 100,
            status: 'in_progress',
          };
        }
        return prev;
      });
    } catch (error) {
      console.error('Error fetching processing status:', error);
    }
  }, [selectedFile?.id]);

  // Poll for real-time updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(fetchProcessingStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchProcessingStatus]);

  // Handle optimization profile selection
  const handleOptimize = async (profile: 'sermon_web' | 'sermon_podcast' | 'sermon_archive') => {
    if (!selectedFile?.id) return;
    
    setIsOptimizing(true);
    setOptimizationProfile(profile);
    
    const profiles = {
      sermon_web: { 
        label: 'Web', 
        icon: <Globe className="w-4 h-4" />, 
        desc: 'Optimized for streaming (720p, 2Mbps)',
        settings: { resolution: '1280x720', bitrate: '2 Mbps', format: 'mp4' }
      },
      sermon_podcast: { 
        label: 'Podcast', 
        icon: <Radio className="w-4 h-4" />, 
        desc: 'Audio-only, RSS feed ready (128kbps)',
        settings: { bitrate: '128 kbps', format: 'mp3', audioOnly: true }
      },
      sermon_archive: { 
        label: 'Archive', 
        icon: <Archive className="w-4 h-4" />, 
        desc: 'Full quality, long-term storage (1080p, 10Mbps)',
        settings: { resolution: '1920x1080', bitrate: '10 Mbps', format: 'mp4', preserveAll: true }
      },
    };
    
    try {
      // In production: POST /sermons/{id}/optimize
      // await fetch(`/sermons/${selectedFile.id}/optimize`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ profile }),
      // });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast.success(`Optimization started for ${profiles[profile].label} profile`, {
        description: profiles[profile].desc,
      });
    } catch (error) {
      toast.error('Failed to start optimization');
    } finally {
      setIsOptimizing(false);
      setOptimizationProfile(null);
    }
  };

  const handleAssignTeam = (memberId: string, role: string) => {
    toast.success(`Assigned team member to ${role}`);
  };

  // Handle metadata form submission with optimistic updates
  const onSubmitMetadata = async (data: SermonMetadata) => {
    if (!selectedFile?.id) return;
    
    setIsSavingMetadata(true);
    
    try {
      // In production: PATCH /sermons/{id}/metadata
      // const response = await fetch(`/sermons/${selectedFile.id}/metadata`, {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(data),
      // });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Optimistic update - update local state immediately
      setIsMetadataDialogOpen(false);
      toast.success('Metadata saved successfully');
    } catch (error) {
      toast.error('Failed to save metadata');
    } finally {
      setIsSavingMetadata(false);
    }
  };

  // Fetch team members from Supabase
  useEffect(() => {
    const fetchTeamMembers = async () => {
      setLoadingTeam(true);
      try {
        const data = await teamMembers.getAvailability();
        if (data && data.length > 0) {
          setTeamMembersList(data);
        }
      } catch (error) {
        console.log('Using mock team data');
      } finally {
        setLoadingTeam(false);
      }
    };

    fetchTeamMembers();
  }, []);

  const getQualityMetrics = () => {
    return {
      audio: {
        score: 92,
        bitrate: '256 kbps',
        sampleRate: '48 kHz',
        clarity: 0.95,
        noise: 0.02,
      },
      video: {
        score: 88,
        resolution: '1080p',
        bitrate: '8 Mbps',
        frameRate: '30 fps',
        brightness: 0.88,
        contrast: 0.92,
      },
      overall: 90,
    };
  };

  const metrics = getQualityMetrics();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-500">Loading processing UI...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* File Selector */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <Select value={selectedFile?.id} onValueChange={(id) => setSelectedFile(files.find(f => f.id === id) || null)}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="Select a sermon" />
              </SelectTrigger>
              <SelectContent>
                {files.map(file => (
                  <SelectItem key={file.id} value={file.id}>{file.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              {formatDuration(totalDuration)}
            </div>
            
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <FileAudio className="w-4 h-4" />
              {formatFileSize(selectedFile?.size || 0)}
            </div>

            <div className="ml-auto flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                <CheckCircle className="w-3 h-3 text-green-500" />
                AI Processed
              </Badge>
              <Badge variant="outline">
                {Math.round(metrics.overall)}% Quality
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Processing Timeline - Custom Timeline Component using Tabs + Progress */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <RefreshCw className="w-5 h-5" />
            Processing Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={processingStatus.currentStage} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              {PIPELINE_STAGES.map((stage) => {
                const status = getStageStatus(stage.id);
                const StageIcon = stage.icon;
                
                return (
                  <TabsTrigger
                    key={stage.id}
                    value={stage.id}
                    className="flex items-center gap-2"
                    disabled={status === 'completed'}
                  >
                    <StageIcon className={cn(
                      'w-4 h-4',
                      status === 'completed' && 'text-green-500',
                      status === 'in_progress' && 'text-blue-500 animate-pulse',
                      status === 'pending' && 'text-gray-400'
                    )} />
                    <span className="hidden sm:inline">{stage.label}</span>
                  </TabsTrigger>
                );
              })}
            </TabsList>
            
            {PIPELINE_STAGES.map((stage) => {
              const status = getStageStatus(stage.id);
              const StageIcon = stage.icon;
              
              return (
                <TabsContent key={stage.id} value={stage.id} className="mt-4">
                  <div className="space-y-4">
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        'w-12 h-12 rounded-full flex items-center justify-center',
                        status === 'completed' && 'bg-green-100',
                        status === 'in_progress' && 'bg-blue-100',
                        status === 'pending' && 'bg-gray-100'
                      )}>
                        <StageIcon className={cn(
                          'w-6 h-6',
                          status === 'completed' && 'text-green-600',
                          status === 'in_progress' && 'text-blue-600',
                          status === 'pending' && 'text-gray-400'
                        )} />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium">{stage.label}</h3>
                        <p className="text-sm text-gray-500">{stage.description}</p>
                      </div>
                      <Badge variant={
                        status === 'completed' ? 'default' :
                        status === 'in_progress' ? 'secondary' : 'outline'
                      }>
                        {status === 'completed' && <CheckCircle className="w-3 h-3 mr-1" />}
                        {status === 'in_progress' && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                        {status === 'completed' ? 'Completed' : status === 'in_progress' ? 'In Progress' : 'Pending'}
                      </Badge>
                    </div>
                    
                    {/* Progress bar for current stage */}
                    {status === 'in_progress' && (
                      <div className="space-y-2">
                        <Progress value={processingStatus.progress} className="h-2" />
                        <p className="text-sm text-gray-500">{processingStatus.message}</p>
                      </div>
                    )}
                    
                    {/* Show completion time when completed */}
                    {status === 'completed' && processingStatus.completedAt && (
                      <p className="text-sm text-green-600">
                        Completed at {new Date(processingStatus.completedAt).toLocaleString()}
                      </p>
                    )}
                  </div>
                </TabsContent>
              );
            })}
          </Tabs>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline & Segments */}
        <div className="lg:col-span-2 space-y-6">
          {/* Interactive Timeline */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Timeline</CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setIsPlaying(!isPlaying)}
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <span className="text-sm font-mono">
                    {formatTime(currentTime)} / {formatTime(totalDuration)}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Timeline visualization */}
              <div className="relative h-16 bg-gray-100 rounded-lg mb-4">
                <div className="absolute inset-0 flex">
                  {segments.map((segment, index) => (
                    <div
                      key={segment.id}
                      className={cn(
                        'h-full border-r border-white/50 cursor-pointer transition-opacity hover:opacity-80',
                        getSegmentColor(segment.type)
                      )}
                      style={{
                        width: `${((segment.end - segment.start) / totalDuration) * 100}%`,
                      }}
                      onClick={() => {
                        setCurrentTime(segment.start);
                        setExpandedSegments(new Set([segment.id]));
                      }}
                    />
                  ))}
                </div>
                {/* Playhead */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-red-500"
                  style={{ left: `${(currentTime / totalDuration) * 100}%` }}
                />
              </div>

              {/* Segments list */}
              <div className="space-y-2">
                {segments.map((segment, index) => {
                  const isExpanded = expandedSegments.has(segment.id);
                  
                  return (
                    <div
                      key={segment.id}
                      className={cn(
                        'rounded-lg border overflow-hidden transition-all',
                        getSegmentColor(segment.type),
                        isExpanded ? 'ring-2 ring-blue-500' : ''
                      )}
                    >
                      {/* Segment header */}
                      <div
                        className="flex items-center gap-3 p-3 cursor-pointer"
                        onClick={() => toggleSegment(segment.id)}
                      >
                        <div className="flex-shrink-0">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </div>
                        
                        <div className="flex-shrink-0 w-20 text-sm font-mono text-gray-500">
                          {formatTime(segment.start)} - {formatTime(segment.end)}
                        </div>
                        
                        <Badge variant="outline" className="text-xs">
                          {getTypeLabel(segment.type)}
                        </Badge>
                        
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{segment.title}</p>
                          <p className="text-xs text-gray-500">{segment.speaker}</p>
                        </div>
                        
                        {segment.scripture && (
                          <Badge variant="secondary" className="text-xs gap-1">
                            <BookOpen className="w-3 h-3" />
                            {segment.scripture}
                          </Badge>
                        )}
                        
                        <div className="flex items-center gap-1">
                          <Zap className={cn(
                            'w-4 h-4',
                            segment.confidence >= 0.9 ? 'text-green-500' :
                            segment.confidence >= 0.8 ? 'text-yellow-500' : 'text-red-500'
                          )} />
                          <span className="text-xs text-gray-500">
                            {Math.round(segment.confidence * 100)}%
                          </span>
                        </div>
                      </div>

                      {/* Expanded segment details */}
                      {isExpanded && (
                        <div className="px-3 pb-3 pt-0 border-t bg-white/50">
                          <div className="grid grid-cols-2 gap-4 mt-3">
                            <div>
                              <label className="text-xs font-medium text-gray-500">Speaker</label>
                              <Input
                                value={segment.speaker}
                                className="mt-1 h-8 text-sm"
                                onChange={(e) => {
                                  setSegments(prev => prev.map(s =>
                                    s.id === segment.id ? { ...s, speaker: e.target.value } : s
                                  ));
                                }}
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-gray-500">Scripture</label>
                              <Input
                                value={segment.scripture}
                                placeholder="Add scripture reference"
                                className="mt-1 h-8 text-sm"
                                onChange={(e) => {
                                  setSegments(prev => prev.map(s =>
                                    s.id === segment.id ? { ...s, scripture: e.target.value } : s
                                  ));
                                }}
                              />
                            </div>
                            <div className="col-span-2">
                              <label className="text-xs font-medium text-gray-500">Title</label>
                              <Input
                                value={segment.title}
                                className="mt-1 h-8 text-sm"
                                onChange={(e) => {
                                  setSegments(prev => prev.map(s =>
                                    s.id === segment.id ? { ...s, title: e.target.value } : s
                                  ));
                                }}
                              />
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2 mt-3">
                            <Button size="sm" variant="outline">
                              <Play className="w-3 h-3 mr-1" />
                              Preview Segment
                            </Button>
                            <Button size="sm" variant="outline">
                              <Mic className="w-3 h-3 mr-1" />
                              Transcribe
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Quality Reports */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <BarChart2 className="w-5 h-5" />
                Quality Report
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6">
                {/* Audio Metrics */}
                <div>
                  <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                    <FileAudio className="w-4 h-4 text-blue-500" />
                    Audio Quality
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span>Overall Score</span>
                        <span className="font-medium">{metrics.audio.score}%</span>
                      </div>
                      <Progress value={metrics.audio.score} className="h-2" />
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="bg-gray-50 p-2 rounded">
                        <p className="text-gray-500">Bitrate</p>
                        <p className="font-medium">{metrics.audio.bitrate}</p>
                      </div>
                      <div className="bg-gray-50 p-2 rounded">
                        <p className="text-gray-500">Sample Rate</p>
                        <p className="font-medium">{metrics.audio.sampleRate}</p>
                      </div>
                      <div className="bg-gray-50 p-2 rounded">
                        <p className="text-gray-500">Clarity</p>
                        <p className="font-medium">{Math.round(metrics.audio.clarity * 100)}%</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Video Metrics */}
                <div>
                  <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                    <FileVideo className="w-4 h-4 text-purple-500" />
                    Video Quality
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span>Overall Score</span>
                        <span className="font-medium">{metrics.video.score}%</span>
                      </div>
                      <Progress value={metrics.video.score} className="h-2" />
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="bg-gray-50 p-2 rounded">
                        <p className="text-gray-500">Resolution</p>
                        <p className="font-medium">{metrics.video.resolution}</p>
                      </div>
                      <div className="bg-gray-50 p-2 rounded">
                        <p className="text-gray-500">Frame Rate</p>
                        <p className="font-medium">{metrics.video.frameRate}</p>
                      </div>
                      <div className="bg-gray-50 p-2 rounded">
                        <p className="text-gray-500">Bitrate</p>
                        <p className="font-medium">{metrics.video.bitrate}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Overall Quality */}
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    <span className="font-medium">Overall Quality Score</span>
                  </div>
                  <span className="text-2xl font-bold text-green-600">{metrics.overall}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar - Metadata, Team, Optimization */}
        <div className="space-y-6">
          {/* Metadata Editor - Dialog with Form */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Edit2 className="w-4 h-4" />
                  Metadata
                </CardTitle>
                <Dialog open={isMetadataDialogOpen} onOpenChange={setIsMetadataDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <Edit2 className="w-4 h-4 mr-1" />
                      Edit
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                      <DialogTitle>Edit Sermon Metadata</DialogTitle>
                      <DialogDescription>
                        Auto-populated from AI extraction. Make changes and save.
                      </DialogDescription>
                    </DialogHeader>
                    
                    <Form {...metadataForm}>
                      <form onSubmit={metadataForm.handleSubmit(onSubmitMetadata)} className="space-y-4">
                        <FormField
                          control={metadataForm.control}
                          name="title"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Title</FormLabel>
                              <FormControl>
                                <Input {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <div className="grid grid-cols-2 gap-4">
                          <FormField
                            control={metadataForm.control}
                            name="speaker"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Speaker</FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select speaker" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {teamMembersList.map(member => (
                                      <SelectItem key={member.id} value={member.name}>
                                        {member.name}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          
                          <FormField
                            control={metadataForm.control}
                            name="date"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Date</FormLabel>
                                <FormControl>
                                  <Input type="date" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        
                        <FormField
                          control={metadataForm.control}
                          name="series"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Series</FormLabel>
                              <FormControl>
                                <Input {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={metadataForm.control}
                          name="location"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Location</FormLabel>
                              <FormControl>
                                <Input {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={metadataForm.control}
                          name="description"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Description</FormLabel>
                              <FormControl>
                                <Textarea {...field} placeholder="Sermon description..." />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={metadataForm.control}
                          name="tags"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Tags</FormLabel>
                              <FormControl>
                                <Input {...field} placeholder="faith, grace, salvation (comma separated)" />
                              </FormControl>
                              <FormDescription>
                                Separate tags with commas
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <DialogFooter>
                          <Button type="button" variant="outline" onClick={() => setIsMetadataDialogOpen(false)}>
                            Cancel
                          </Button>
                          <Button type="submit" disabled={isSavingMetadata}>
                            {isSavingMetadata ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Saving...
                              </>
                            ) : (
                              <>
                                <Save className="w-4 h-4 mr-2" />
                                Save Changes
                              </>
                            )}
                          </Button>
                        </DialogFooter>
                      </form>
                    </Form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-gray-500">Title</label>
                <p className="text-sm mt-1">{metadataForm.getValues('title') || 'Not set'}</p>
              </div>
              
              <div>
                <label className="text-xs font-medium text-gray-500">Speaker</label>
                <p className="text-sm mt-1">{metadataForm.getValues('speaker')}</p>
              </div>
              
              <div>
                <label className="text-xs font-medium text-gray-500">Series</label>
                <p className="text-sm mt-1">{metadataForm.getValues('series')}</p>
              </div>
              
              <div>
                <label className="text-xs font-medium text-gray-500">Location</label>
                <p className="text-sm mt-1">{metadataForm.getValues('location')}</p>
              </div>
              
              <div>
                <label className="text-xs font-medium text-gray-500">Tags</label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {metadataForm.getValues('tags').map(tag => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Team Assignment */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="w-4 h-4" />
                Team Assignment
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {loadingTeam ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="ml-2 text-sm text-gray-500">Loading team...</span>
                </div>
              ) : (
                teamMembersList.map(member => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between p-2 rounded-lg bg-gray-50"
                  >
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        'w-2 h-2 rounded-full',
                        member.available ? 'bg-green-500' : 'bg-gray-300'
                      )} />
                      <div>
                        <p className="text-sm font-medium">{member.name}</p>
                        <p className="text-xs text-gray-500">{member.role || 'Team Member'}</p>
                      </div>
                    </div>
                    <Select onValueChange={(role) => handleAssignTeam(member.id, role)}>
                      <SelectTrigger className="w-[100px] h-8 text-xs">
                        <SelectValue placeholder="Assign" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="preacher">Preacher</SelectItem>
                        <SelectItem value="editor">Editor</SelectItem>
                        <SelectItem value="reviewer">Reviewer</SelectItem>
                        <SelectItem value="uploader">Uploader</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* One-Click Optimization - Dropdown Selector */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Export & Optimize
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Select 
                onValueChange={(value) => handleOptimize(value as 'sermon_web' | 'sermon_podcast' | 'sermon_archive')}
                disabled={isOptimizing}
              >
                <SelectTrigger className="w-full">
                  {isOptimizing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      <span>Optimizing...</span>
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-4 h-4 mr-2" />
                      <SelectValue placeholder="Select optimization profile" />
                    </>
                  )}
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sermon_web" disabled={isOptimizing}>
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      <div className="text-left">
                        <p className="font-medium">Web Profile</p>
                        <p className="text-xs text-gray-500">720p, 2Mbps, optimized for streaming</p>
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="sermon_podcast" disabled={isOptimizing}>
                    <div className="flex items-center gap-2">
                      <Radio className="w-4 h-4" />
                      <div className="text-left">
                        <p className="font-medium">Podcast Profile</p>
                        <p className="text-xs text-gray-500">Audio-only, 128kbps, RSS ready</p>
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="sermon_archive" disabled={isOptimizing}>
                    <div className="flex items-center gap-2">
                      <Archive className="w-4 h-4" />
                      <div className="text-left">
                        <p className="font-medium">Archive Profile</p>
                        <p className="text-xs text-gray-500">1080p, 10Mbps, full quality storage</p>
                      </div>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              
              {/* Optimization Progress */}
              {isOptimizing && (
                <div className="space-y-2 mt-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Processing...</span>
                    <span className="font-medium">50%</span>
                  </div>
                  <Progress value={50} className="h-2" />
                </div>
              )}
              
              {/* Recent optimizations */}
              <div className="pt-2 border-t">
                <p className="text-xs text-gray-500 mb-2">Recent optimizations</p>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm">
                    <Globe className="w-3 h-3 text-blue-500" />
                    <span className="text-gray-600">Web - Jan 28, 2024</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Radio className="w-3 h-3 text-green-500" />
                    <span className="text-gray-600">Podcast - Jan 25, 2024</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Extracted Themes */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Target className="w-4 h-4" />
                AI-Extracted Themes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {mockThemes.map(theme => (
                  <Badge key={theme} variant="secondary" className="text-sm">
                    {theme}
                  </Badge>
                ))}
              </div>
              <Button variant="ghost" size="sm" className="mt-3 w-full">
                <Plus className="w-4 h-4 mr-1" />
                Add Theme
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default SermonProcessingUI;
