import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Checkbox } from '@/app/components/ui/checkbox';
import { Popover, PopoverContent, PopoverTrigger } from '@/app/components/ui/popover';
import { Calendar } from '@/app/components/ui/calendar';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/app/components/ui/command';
import { cn } from '@/app/components/ui/utils';
import {
  Search,
  Filter,
  X,
  Calendar as CalendarIcon,
  Tag,
  User,
  FolderOpen,
  FileAudio,
  FileVideo,
  File as FileIcon,
  SortAsc,
  SortDesc,
  RefreshCw,
} from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

interface SearchFilters {
  query: string;
  fileTypes: string[];
  dateRange: { from?: Date; to?: Date } | null;
  series: string[];
  speakers: string[];
  tags: string[];
  statuses: string[];
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

const FILE_TYPES = [
  { id: 'audio', label: 'Audio', icon: FileAudio },
  { id: 'video', label: 'Video', icon: FileVideo },
  { id: 'document', label: 'Document', icon: FileIcon },
];

const STATUSES = [
  { id: 'uploaded', label: 'Uploaded' },
  { id: 'transcribed', label: 'Transcribed' },
  { id: 'reviewed', label: 'Reviewed' },
  { id: 'published', label: 'Published' },
];

const SORT_OPTIONS = [
  { id: 'created_at', label: 'Date Created' },
  { id: 'name', label: 'Name' },
  { id: 'size', label: 'File Size' },
  { id: 'metadata.series', label: 'Series' },
  { id: 'metadata.speaker', label: 'Speaker' },
];

export function AdvancedSearch() {
  const { files, loading, refreshFiles } = useFileManager();
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [activeFiltersCount, setActiveFiltersCount] = useState(0);

  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    fileTypes: [],
    dateRange: null,
    series: [],
    speakers: [],
    tags: [],
    statuses: [],
    sortBy: 'created_at',
    sortOrder: 'desc',
  });

  // Extract unique values from files for suggestions
  const allSeries = useMemo(() => {
    const series = new Set<string>();
    files.forEach((file) => {
      if (file.metadata?.series) {
        series.add(file.metadata.series);
      }
    });
    return Array.from(series).sort();
  }, [files]);

  const allSpeakers = useMemo(() => {
    const speakers = new Set<string>();
    files.forEach((file) => {
      if (file.metadata?.speaker) {
        speakers.add(file.metadata.speaker);
      }
    });
    return Array.from(speakers).sort();
  }, [files]);

  const allTags = useMemo(() => {
    const tags = new Set<string>();
    files.forEach((file) => {
      if (file.metadata?.tags) {
        file.metadata.tags.forEach((tag: string) => tags.add(tag));
      }
    });
    return Array.from(tags).sort();
  }, [files]);

  // Calculate active filters count
  useEffect(() => {
    let count = 0;
    if (filters.fileTypes.length > 0) count++;
    if (filters.dateRange?.from || filters.dateRange?.to) count++;
    if (filters.series.length > 0) count++;
    if (filters.speakers.length > 0) count++;
    if (filters.tags.length > 0) count++;
    if (filters.statuses.length > 0) count++;
    setActiveFiltersCount(count);
  }, [filters]);

  const filteredFiles = useMemo(() => {
    let result = [...files];

    // Text search
    if (filters.query) {
      const query = filters.query.toLowerCase();
      result = result.filter(
        (file) =>
          file.name.toLowerCase().includes(query) ||
          file.metadata?.series?.toLowerCase().includes(query) ||
          file.metadata?.speaker?.toLowerCase().includes(query) ||
          file.metadata?.tags?.some((tag: string) => tag.toLowerCase().includes(query))
      );
    }

    // File type filter
    if (filters.fileTypes.length > 0) {
      result = result.filter((file) => {
        const fileType = file.type.startsWith('audio/')
          ? 'audio'
          : file.type.startsWith('video/')
          ? 'video'
          : 'document';
        return filters.fileTypes.includes(fileType);
      });
    }

    // Date range filter
    if (filters.dateRange?.from) {
      result = result.filter((file) => new Date(file.created_at) >= filters.dateRange!.from!);
    }
    if (filters.dateRange?.to) {
      result = result.filter((file) => new Date(file.created_at) <= filters.dateRange!.to!);
    }

    // Series filter
    if (filters.series.length > 0) {
      result = result.filter((file) => filters.series.includes(file.metadata?.series));
    }

    // Speaker filter
    if (filters.speakers.length > 0) {
      result = result.filter((file) => filters.speakers.includes(file.metadata?.speaker));
    }

    // Tags filter
    if (filters.tags.length > 0) {
      result = result.filter((file) =>
        file.metadata?.tags?.some((tag: string) => filters.tags.includes(tag))
      );
    }

    // Status filter
    if (filters.statuses.length > 0) {
      result = result.filter((file) =>
        filters.statuses.includes(file.metadata?.status || 'uploaded')
      );
    }

    // Sorting
    result.sort((a, b) => {
      let comparison = 0;
      switch (filters.sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'size':
          comparison = a.size - b.size;
          break;
        case 'metadata.series':
          comparison = (a.metadata?.series || '').localeCompare(b.metadata?.series || '');
          break;
        case 'metadata.speaker':
          comparison = (a.metadata?.speaker || '').localeCompare(b.metadata?.speaker || '');
          break;
        case 'created_at':
        default:
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }
      return filters.sortOrder === 'desc' ? -comparison : comparison;
    });

    return result;
  }, [files, filters]);

  const toggleFileType = useCallback((typeId: string) => {
    setFilters((prev) => ({
      ...prev,
      fileTypes: prev.fileTypes.includes(typeId)
        ? prev.fileTypes.filter((t) => t !== typeId)
        : [...prev.fileTypes, typeId],
    }));
  }, []);

  const toggleSeries = useCallback((series: string) => {
    setFilters((prev) => ({
      ...prev,
      series: prev.series.includes(series)
        ? prev.series.filter((s) => s !== series)
        : [...prev.series, series],
    }));
  }, []);

  const toggleSpeaker = useCallback((speaker: string) => {
    setFilters((prev) => ({
      ...prev,
      speakers: prev.speakers.includes(speaker)
        ? prev.speakers.filter((s) => s !== speaker)
        : [...prev.speakers, speaker],
    }));
  }, []);

  const toggleTag = useCallback((tag: string) => {
    setFilters((prev) => ({
      ...prev,
      tags: prev.tags.includes(tag) ? prev.tags.filter((t) => t !== tag) : [...prev.tags, tag],
    }));
  }, []);

  const toggleStatus = useCallback((status: string) => {
    setFilters((prev) => ({
      ...prev,
      statuses: prev.statuses.includes(status)
        ? prev.statuses.filter((s) => s !== status)
        : [...prev.statuses, status],
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      query: '',
      fileTypes: [],
      dateRange: null,
      series: [],
      speakers: [],
      tags: [],
      statuses: [],
      sortBy: 'created_at',
      sortOrder: 'desc',
    });
    toast.success('Filters cleared');
  }, []);

  const getFileIcon = (type: string) => {
    if (type.startsWith('audio/')) return FileAudio;
    if (type.startsWith('video/')) return FileVideo;
    return FileIcon;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { label: string; variant: 'default' | 'secondary' | 'outline' | 'destructive' }> = {
      uploaded: { label: 'Uploaded', variant: 'secondary' },
      transcribed: { label: 'Transcribed', variant: 'default' },
      reviewed: { label: 'Reviewed', variant: 'outline' },
      published: { label: 'Published', variant: 'default' },
    };
    const config = statusConfig[status] || { label: status, variant: 'secondary' };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <div className="text-lg text-gray-500">Loading files...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Advanced Search</CardTitle>
          <div className="flex items-center gap-2">
            {activeFiltersCount > 0 && (
              <Button variant="outline" size="sm" onClick={clearFilters}>
                <X className="w-4 h-4 mr-1" />
                Clear ({activeFiltersCount})
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => refreshFiles()}>
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search by name, series, speaker, or tags..."
            value={filters.query}
            onChange={(e) => setFilters((prev) => ({ ...prev, query: e.target.value }))}
            className="pl-10"
          />
        </div>

        {/* Filter row */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* File type filter */}
          <Popover open={isFilterOpen} onOpenChange={setIsFilterOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="relative">
                <Filter className="w-4 h-4 mr-1" />
                Filters
                {activeFiltersCount > 0 && (
                  <Badge
                    variant="default"
                    className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center text-xs"
                  >
                    {activeFiltersCount}
                  </Badge>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="start">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-sm mb-2">File Type</h4>
                  <div className="flex flex-wrap gap-2">
                    {FILE_TYPES.map((type) => {
                      const Icon = type.icon;
                      return (
                        <button
                          key={type.id}
                          onClick={() => toggleFileType(type.id)}
                          className={cn(
                            'flex items-center gap-1 px-3 py-1.5 rounded-md text-sm transition-colors',
                            filters.fileTypes.includes(type.id)
                              ? 'bg-blue-100 text-blue-700 border border-blue-300'
                              : 'bg-gray-100 text-gray-600 border border-transparent hover:bg-gray-200'
                          )}
                        >
                          <Icon className="w-3 h-3" />
                          {type.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-sm mb-2">Date Range</h4>
                  <Calendar
                    mode="range"
                    selected={filters.dateRange || undefined}
                    onSelect={(range) => setFilters((prev) => ({ ...prev, dateRange: range || null }))}
                    className="rounded-md border"
                  />
                </div>

                <div>
                  <h4 className="font-medium text-sm mb-2">Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {STATUSES.map((status) => (
                      <button
                        key={status.id}
                        onClick={() => toggleStatus(status.id)}
                        className={cn(
                          'px-3 py-1.5 rounded-md text-sm transition-colors',
                          filters.statuses.includes(status.id)
                            ? 'bg-blue-100 text-blue-700 border border-blue-300'
                            : 'bg-gray-100 text-gray-600 border border-transparent hover:bg-gray-200'
                        )}
                      >
                        {status.label}
                      </button>
                    ))}
                  </div>
                </div>

                {allSeries.length > 0 && (
                  <div>
                    <h4 className="font-medium text-sm mb-2">Series</h4>
                    <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                      {allSeries.map((series) => (
                        <button
                          key={series}
                          onClick={() => toggleSeries(series)}
                          className={cn(
                            'px-2 py-0.5 rounded text-xs transition-colors',
                            filters.series.includes(series)
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          )}
                        >
                          {series}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {allSpeakers.length > 0 && (
                  <div>
                    <h4 className="font-medium text-sm mb-2">Speakers</h4>
                    <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                      {allSpeakers.map((speaker) => (
                        <button
                          key={speaker}
                          onClick={() => toggleSpeaker(speaker)}
                          className={cn(
                            'px-2 py-0.5 rounded text-xs transition-colors',
                            filters.speakers.includes(speaker)
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          )}
                        >
                          {speaker}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {allTags.length > 0 && (
                  <div>
                    <h4 className="font-medium text-sm mb-2">Tags</h4>
                    <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                      {allTags.map((tag) => (
                        <button
                          key={tag}
                          onClick={() => toggleTag(tag)}
                          className={cn(
                            'px-2 py-0.5 rounded text-xs transition-colors',
                            filters.tags.includes(tag)
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          )}
                        >
                          <Tag className="w-3 h-3 inline mr-1" />
                          {tag}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </PopoverContent>
          </Popover>

          {/* Sort controls */}
          <div className="flex items-center gap-2 ml-auto">
            <span className="text-sm text-gray-500">Sort by:</span>
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters((prev) => ({ ...prev, sortBy: e.target.value }))}
              className="text-sm border rounded-md px-2 py-1"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() =>
                setFilters((prev) => ({
                  ...prev,
                  sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc',
                }))
              }
            >
              {filters.sortOrder === 'asc' ? (
                <SortAsc className="w-4 h-4" />
              ) : (
                <SortDesc className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Active filters display */}
        {(filters.fileTypes.length > 0 ||
          filters.series.length > 0 ||
          filters.speakers.length > 0 ||
          filters.tags.length > 0 ||
          filters.statuses.length > 0) && (
          <div className="flex flex-wrap gap-1">
            {filters.fileTypes.map((type) => (
              <Badge key={type} variant="secondary" className="gap-1">
                {type}
                <X
                  className="w-3 h-3 cursor-pointer"
                  onClick={() => toggleFileType(type)}
                />
              </Badge>
            ))}
            {filters.series.map((series) => (
              <Badge key={series} variant="secondary" className="gap-1">
                <FolderOpen className="w-3 h-3" />
                {series}
                <X className="w-3 h-3 cursor-pointer" onClick={() => toggleSeries(series)} />
              </Badge>
            ))}
            {filters.speakers.map((speaker) => (
              <Badge key={speaker} variant="secondary" className="gap-1">
                <User className="w-3 h-3" />
                {speaker}
                <X className="w-3 h-3 cursor-pointer" onClick={() => toggleSpeaker(speaker)} />
              </Badge>
            ))}
            {filters.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="gap-1">
                <Tag className="w-3 h-3" />
                {tag}
                <X className="w-3 h-3 cursor-pointer" onClick={() => toggleTag(tag)} />
              </Badge>
            ))}
            {filters.statuses.map((status) => (
              <Badge key={status} variant="secondary" className="gap-1">
                {status}
                <X className="w-3 h-3 cursor-pointer" onClick={() => toggleStatus(status)} />
              </Badge>
            ))}
          </div>
        )}

        {/* Results count */}
        <div className="text-sm text-gray-500">
          {filteredFiles.length} of {files.length} files
        </div>

        {/* Results list */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {filteredFiles.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="w-12 h-12 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No files found</h3>
              <p className="text-sm text-gray-500">Try adjusting your search or filters</p>
            </div>
          ) : (
            filteredFiles.map((file) => {
              const Icon = getFileIcon(file.type);
              return (
                <div
                  key={file.id}
                  className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                >
                  <Icon className="w-8 h-8 text-blue-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate">{file.name}</h4>
                    <div className="flex items-center gap-3 mt-1">
                      {file.metadata?.speaker && (
                        <span className="text-xs text-gray-500">{file.metadata.speaker}</span>
                      )}
                      {file.metadata?.series && (
                        <span className="text-xs text-gray-400">| {file.metadata.series}</span>
                      )}
                      <span className="text-xs text-gray-400">{formatFileSize(file.size)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(file.metadata?.status || 'uploaded')}
                    {file.metadata?.tags?.map((tag: string) => (
                      <Badge key={tag} variant="outline" className="text-[10px]">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}
