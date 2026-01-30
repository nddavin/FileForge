import React, { useState, useMemo } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/app/components/ui/select';
import { Checkbox } from '@/app/components/ui/checkbox';
import {
  Search,
  Upload,
  Filter,
  Grid,
  List,
  SortAsc,
  SortDesc,
  Calendar,
  User,
  FolderOpen,
  FileAudio,
  FileVideo,
  File as FileIcon,
  Clock,
  TrendingUp,
  HardDrive,
  BarChart3,
  RefreshCw,
  Play,
  MoreHorizontal,
  Star,
  Zap,
} from 'lucide-react';
import { cn, formatFileSize, formatDistanceToNow } from '@/app/components/ui/utils';
import { format } from 'date-fns';
import { toast } from 'sonner';

type ViewMode = 'grid' | 'list';
type SortField = 'created_at' | 'name' | 'size' | 'qualityScore' | 'confidence';
type SortOrder = 'asc' | 'desc';

interface DashboardStats {
  totalFiles: number;
  totalSize: number;
  audioCount: number;
  videoCount: number;
  byStatus: Record<string, number>;
  recentUploads: number;
  speakers: string[];
  series: string[];
}

export function CoreDashboard() {
  const { files, loading, refreshFiles, selectedFiles, toggleSelection, selectAll, clearSelection } = useFileManager();
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [speakerFilter, setSpeakerFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [showFilters, setShowFilters] = useState(false);

  // Calculate dashboard stats
  const stats: DashboardStats = useMemo(() => {
    const totalSize = files.reduce((acc, f) => acc + f.size, 0);
    const audioCount = files.filter(f => f.type.startsWith('audio/')).length;
    const videoCount = files.filter(f => f.type.startsWith('video/')).length;
    const recentUploads = files.filter(f => {
      const dayAgo = new Date();
      dayAgo.setDate(dayAgo.getDate() - 7);
      return new Date(f.created_at) >= dayAgo;
    }).length;

    const byStatus: Record<string, number> = {};
    const speakers = new Set<string>();
    const series = new Set<string>();

    files.forEach(f => {
      const status = f.metadata?.status || 'uploaded';
      byStatus[status] = (byStatus[status] || 0) + 1;
      if (f.metadata?.speaker) speakers.add(f.metadata.speaker);
      if (f.metadata?.series) series.add(f.metadata.series);
    });

    return {
      totalFiles: files.length,
      totalSize,
      audioCount,
      videoCount,
      byStatus,
      recentUploads,
      speakers: Array.from(speakers).sort(),
      series: Array.from(series).sort(),
    };
  }, [files]);

  // Filter and sort files
  const filteredFiles = useMemo(() => {
    let result = [...files];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(f =>
        f.name.toLowerCase().includes(query) ||
        f.metadata?.speaker?.toLowerCase().includes(query) ||
        f.metadata?.series?.toLowerCase().includes(query) ||
        f.metadata?.tags?.some((t: string) => t.toLowerCase().includes(query))
      );
    }

    // Speaker filter
    if (speakerFilter !== 'all') {
      result = result.filter(f => f.metadata?.speaker === speakerFilter);
    }

    // Sorting
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'size':
          comparison = a.size - b.size;
          break;
        case 'qualityScore':
          comparison = (a.metadata?.qualityScore || 0) - (b.metadata?.qualityScore || 0);
          break;
        case 'confidence':
          comparison = (a.metadata?.confidence || 0) - (b.metadata?.confidence || 0);
          break;
        case 'created_at':
        default:
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });

    return result;
  }, [files, searchQuery, speakerFilter, sortBy, sortOrder]);

  const getFileIcon = (type: string) => {
    if (type.startsWith('audio/')) return FileAudio;
    if (type.startsWith('video/')) return FileVideo;
    return FileIcon;
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { label: string; className: string }> = {
      uploaded: { label: 'Uploaded', className: 'bg-gray-100 text-gray-700' },
      transcribed: { label: 'Transcribed', className: 'bg-blue-100 text-blue-700' },
      reviewed: { label: 'Reviewed', className: 'bg-yellow-100 text-yellow-700' },
      published: { label: 'Published', className: 'bg-green-100 text-green-700' },
    };
    const { label, className } = config[status] || { label: status, className: 'bg-gray-100 text-gray-700' };
    return <Badge className={cn('text-xs', className)}>{label}</Badge>;
  };

  const getQualityScore = (file: typeof files[0]) => {
    const score = file.metadata?.qualityScore || Math.floor(Math.random() * 30 + 70);
    const color = score >= 90 ? 'text-green-600' : score >= 70 ? 'text-yellow-600' : 'text-red-600';
    return (
      <div className={cn('flex items-center gap-1 text-sm font-medium', color)}>
        <Star className="w-3 h-3" />
        {score}%
      </div>
    );
  };

  const getConfidence = (file: typeof files[0]) => {
    const conf = file.metadata?.confidence || Math.floor(Math.random() * 25 + 75);
    const color = conf >= 90 ? 'text-green-600' : conf >= 70 ? 'text-yellow-600' : 'text-red-600';
    return (
      <div className={cn('flex items-center gap-1 text-sm font-medium', color)}>
        <Zap className="w-3 h-3" />
        {conf}%
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="col-span-1">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.totalFiles}</p>
                <p className="text-xs text-gray-500">Total Files</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <HardDrive className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatFileSize(stats.totalSize)}</p>
                <p className="text-xs text-gray-500">Total Size</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <FileAudio className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.audioCount}</p>
                <p className="text-xs text-gray-500">Audio</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <FileVideo className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.videoCount}</p>
                <p className="text-xs text-gray-500">Video</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.recentUploads}</p>
                <p className="text-xs text-gray-500">This Week</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <User className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.speakers.length}</p>
                <p className="text-xs text-gray-500">Speakers</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions & Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
            <div className="flex items-center gap-3 flex-1 w-full lg:w-auto">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search files, speakers, series..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              <Select value={speakerFilter} onValueChange={setSpeakerFilter}>
                <SelectTrigger className="w-[180px]">
                  <User className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="All Speakers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Speakers</SelectItem>
                  {stats.speakers.map(speaker => (
                    <SelectItem key={speaker} value={speaker}>{speaker}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
                className="hidden lg:flex"
              >
                <Filter className="w-4 h-4 mr-1" />
                Filters
              </Button>
            </div>

            <div className="flex items-center gap-3">
              {/* Selection actions */}
              {selectedFiles.size > 0 && (
                <div className="flex items-center gap-2 mr-4">
                  <span className="text-sm text-gray-500">{selectedFiles.size} selected</span>
                  <Button variant="outline" size="sm" onClick={clearSelection}>
                    Clear
                  </Button>
                  <Button variant="outline" size="sm" onClick={selectAll}>
                    Select All
                  </Button>
                </div>
              )}

              {/* Sort controls */}
              <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortField)}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at">Date</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="size">Size</SelectItem>
                  <SelectItem value="qualityScore">Quality Score</SelectItem>
                  <SelectItem value="confidence">Confidence</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="icon"
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
              </Button>

              <div className="flex items-center border rounded-md">
                <Button
                  variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                  size="icon"
                  className="rounded-r-none"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid className="w-4 h-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                  size="icon"
                  className="rounded-l-none"
                  onClick={() => setViewMode('list')}
                >
                  <List className="w-4 h-4" />
                </Button>
              </div>

              <Button variant="outline" size="icon" onClick={() => refreshFiles()}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Active filters */}
          {(searchQuery || speakerFilter !== 'all') && (
            <div className="flex items-center gap-2 mt-3 pt-3 border-t">
              {searchQuery && (
                <Badge variant="secondary" className="gap-1">
                  Search: {searchQuery}
                  <button onClick={() => setSearchQuery('')}>
                    <span className="sr-only">Clear</span>
                    ×
                  </button>
                </Badge>
              )}
              {speakerFilter !== 'all' && (
                <Badge variant="secondary" className="gap-1">
                  Speaker: {speakerFilter}
                  <button onClick={() => setSpeakerFilter('all')}>
                    <span className="sr-only">Clear</span>
                    ×
                  </button>
                </Badge>
              )}
              <Button variant="ghost" size="sm" onClick={() => {
                setSearchQuery('');
                setSpeakerFilter('all');
              }}>
                Clear all
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Showing {filteredFiles.length} of {files.length} files
        </p>
        {stats.series.length > 0 && (
          <div className="flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-500">{stats.series.length} series</span>
          </div>
        )}
      </div>

      {/* File Grid/List */}
      {filteredFiles.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Search className="w-16 h-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No files found</h3>
            <p className="text-sm text-gray-500">Try adjusting your search or filters</p>
          </CardContent>
        </Card>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredFiles.map((file) => {
            const Icon = getFileIcon(file.type);
            const isSelected = selectedFiles.has(file.id);

            return (
              <Card
                key={file.id}
                className={cn(
                  'cursor-pointer transition-all hover:shadow-md',
                  isSelected ? 'ring-2 ring-blue-500' : ''
                )}
                onClick={() => toggleSelection(file.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleSelection(file.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-2">
                        <Icon className="w-10 h-10 text-blue-500 flex-shrink-0 mt-1" />
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {file.name}
                          </h3>
                          <div className="flex items-center gap-2 mt-1">
                            {getStatusBadge(file.metadata?.status || 'uploaded')}
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 space-y-1">
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {format(new Date(file.created_at), 'MMM d, yyyy')}
                          </span>
                          <span>{formatFileSize(file.size)}</span>
                        </div>

                        {file.metadata?.speaker && (
                          <p className="text-xs text-gray-600 flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {file.metadata.speaker}
                          </p>
                        )}

                        {file.metadata?.series && (
                          <p className="text-xs text-gray-500 flex items-center gap-1">
                            <FolderOpen className="w-3 h-3" />
                            {file.metadata.series}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center justify-between mt-3 pt-3 border-t">
                        {getQualityScore(file)}
                        {getConfidence(file)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {filteredFiles.map((file) => {
                const Icon = getFileIcon(file.type);
                const isSelected = selectedFiles.has(file.id);

                return (
                  <div
                    key={file.id}
                    className={cn(
                      'flex items-center gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors',
                      isSelected ? 'bg-blue-50' : ''
                    )}
                    onClick={() => toggleSelection(file.id)}
                  >
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleSelection(file.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <Icon className="w-8 h-8 text-blue-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 truncate">{file.name}</h3>
                      <div className="flex items-center gap-3 mt-1">
                        {file.metadata?.speaker && (
                          <span className="text-xs text-gray-500">{file.metadata.speaker}</span>
                        )}
                        {file.metadata?.series && (
                          <span className="text-xs text-gray-400">| {file.metadata.series}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {getQualityScore(file)}
                      {getConfidence(file)}
                      {getStatusBadge(file.metadata?.status || 'uploaded')}
                      <span className="text-xs text-gray-500 w-24 text-right">
                        {formatDistanceToNow(new Date(file.created_at), { addSuffix: true })}
                      </span>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default CoreDashboard;
