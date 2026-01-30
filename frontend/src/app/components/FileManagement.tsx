import React, { useState, useCallback, useMemo } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Checkbox } from '@/app/components/ui/checkbox';
import { Progress } from '@/app/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/app/components/ui/table';
import {
  Upload,
  FileAudio,
  FileVideo,
  File as FileIcon,
  X,
  CheckCircle,
  AlertCircle,
  Clock,
  User,
  Star,
  Users,
  ChevronDown,
  ChevronUp,
  ArrowUpDown,
  Filter,
  Loader2,
} from 'lucide-react';
import { cn, formatFileSize, formatDistanceToNow } from '@/app/components/ui/utils';
import { toast } from 'sonner';

// File validation config (would come from backend)
const UPLOAD_CONFIG = {
  maxFileSize: 500 * 1024 * 1024, // 500MB
  allowedTypes: ['audio/mpeg', 'audio/wav', 'audio/ogg', 'video/mp4', 'video/webm', 'video/quicktime'],
  maxFiles: 20,
};

interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

interface SortConfig {
  field: 'name' | 'date' | 'size' | 'confidence' | 'status';
  direction: 'asc' | 'desc';
}

// File Upload Component with Drag-and-Drop
export function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<UploadFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    if (file.size > UPLOAD_CONFIG.maxFileSize) {
      return `File size exceeds ${formatFileSize(UPLOAD_CONFIG.maxFileSize)}`;
    }
    if (!UPLOAD_CONFIG.allowedTypes.includes(file.type)) {
      return `File type ${file.type} not allowed`;
    }
    return null;
  }, []);

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    if (files.length > UPLOAD_CONFIG.maxFiles) {
      toast.error(`Maximum ${UPLOAD_CONFIG.maxFiles} files allowed at once`);
      return;
    }

    const newFiles: UploadFile[] = [];

    for (const file of Array.from(files)) {
      const error = validateFile(file);
      if (error) {
        toast.error(`${file.name}: ${error}`);
        continue;
      }

      newFiles.push({
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        progress: 0,
        status: 'pending',
      });
    }

    setUploadQueue(prev => [...prev, ...newFiles]);
    await uploadFiles(newFiles);
  }, [validateFile]);

  const uploadFiles = async (files: UploadFile[]) => {
    setIsUploading(true);

    for (const uploadFile of files) {
      setUploadQueue(prev =>
        prev.map(f =>
          f.id === uploadFile.id ? { ...f, status: 'uploading' } : f
        )
      );

      try {
        // Simulate chunked upload
        const chunkSize = 1024 * 1024; // 1MB
        const totalChunks = Math.ceil(uploadFile.file.size / chunkSize);
        
        for (let i = 0; i < totalChunks; i++) {
          await new Promise(resolve => setTimeout(resolve, 100));
          
          setUploadQueue(prev =>
            prev.map(f =>
              f.id === uploadFile.id
                ? { ...f, progress: Math.round(((i + 1) / totalChunks) * 100) }
                : f
            )
          );
        }

        // Upload successful - trigger processing pipeline
        setUploadQueue(prev =>
          prev.map(f =>
            f.id === uploadFile.id ? { ...f, status: 'processing' } : f
          )
        );

        // Simulate processing pipeline
        await new Promise(resolve => setTimeout(resolve, 1500));

        setUploadQueue(prev =>
          prev.map(f =>
            f.id === uploadFile.id ? { ...f, status: 'completed', progress: 100 } : f
          )
        );

        toast.success(`Uploaded: ${uploadFile.file.name}`);
      } catch (error) {
        setUploadQueue(prev =>
          prev.map(f =>
            f.id === uploadFile.id
              ? { ...f, status: 'error', error: 'Upload failed' }
              : f
          )
        );
      }
    }

    setIsUploading(false);
  };

  const removeFile = useCallback((id: string) => {
    setUploadQueue(prev => prev.filter(f => f.id !== id));
  }, []);

  const clearCompleted = useCallback(() => {
    setUploadQueue(prev => prev.filter(f => f.status !== 'completed'));
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const getFileIcon = (type: string) => {
    if (type.startsWith('audio/')) return FileAudio;
    if (type.startsWith('video/')) return FileVideo;
    return FileIcon;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'uploading':
        return <Badge className="bg-blue-100 text-blue-700">Uploading</Badge>;
      case 'processing':
        return <Badge className="bg-purple-100 text-purple-700">Processing</Badge>;
      case 'completed':
        return <Badge className="bg-green-100 text-green-700">Completed</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-700">Failed</Badge>;
      default:
        return <Badge variant="secondary">Pending</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className={cn('w-10 h-10 mx-auto mb-4', isDragging ? 'text-blue-500' : 'text-gray-400')} />
        <p className="text-lg font-medium text-gray-900 mb-2">
          Drag and drop files here
        </p>
        <p className="text-sm text-gray-500 mb-4">
          or click to browse (audio/video up to 500MB)
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="audio/*,video/*"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <Button onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
          <Upload className="w-4 h-4 mr-2" />
          Select Files
        </Button>
      </div>

      {/* Upload Queue */}
      {uploadQueue.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Upload Queue</CardTitle>
              {uploadQueue.some(f => f.status === 'completed') && (
                <Button variant="outline" size="sm" onClick={clearCompleted}>
                  Clear Completed
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {uploadQueue.map((uploadFile) => {
              const Icon = getFileIcon(uploadFile.file.type);
              
              return (
                <div
                  key={uploadFile.id}
                  className="flex items-center gap-4 p-3 rounded-lg border bg-white"
                >
                  <Icon className="w-8 h-8 text-blue-500 flex-shrink-0" />
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium truncate">{uploadFile.file.name}</p>
                      {getStatusBadge(uploadFile.status)}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">
                        {formatFileSize(uploadFile.file.size)}
                      </span>
                      {uploadFile.status === 'uploading' && (
                        <Progress value={uploadFile.progress} className="flex-1 h-1.5" />
                      )}
                      {uploadFile.status === 'processing' && (
                        <Loader2 className="w-4 h-4 text-purple-500 animate-spin" />
                      )}
                      {uploadFile.status === 'completed' && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {uploadFile.status === 'error' && (
                        <AlertCircle className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                    
                    {uploadFile.error && (
                      <p className="text-xs text-red-500 mt-1">{uploadFile.error}</p>
                    )}
                  </div>
                  
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => removeFile(uploadFile.id)}
                    disabled={uploadFile.status === 'uploading' || uploadFile.status === 'processing'}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Smart File Grid with DataTable features
export function SmartFileGrid() {
  const { files, loading, selectedFiles, toggleSelection, selectAll, clearSelection } = useFileManager();
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'date', direction: 'desc' });
  const [preacherFilter, setPreacherFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Extract unique preachers
  const preachers = useMemo(() => {
    const set = new Set<string>();
    files.forEach(f => {
      if (f.metadata?.speaker) set.add(f.metadata.speaker);
    });
    return Array.from(set).sort();
  }, [files]);

  // Filter and sort files
  const filteredFiles = useMemo(() => {
    let result = [...files];

    // Apply filters
    if (preacherFilter !== 'all') {
      result = result.filter(f => f.metadata?.speaker === preacherFilter);
    }
    if (statusFilter !== 'all') {
      result = result.filter(f => (f.metadata?.status || 'ready') === statusFilter);
    }

    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortConfig.field) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'size':
          comparison = a.size - b.size;
          break;
        case 'confidence':
          comparison = ((a.metadata?.confidence || 0) * 100) - ((b.metadata?.confidence || 0) * 100);
          break;
        case 'status':
          comparison = (a.metadata?.status || '').localeCompare(b.metadata?.status || '');
          break;
      }
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [files, sortConfig, preacherFilter, statusFilter]);

  const handleSort = (field: SortConfig['field']) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('audio/')) return FileAudio;
    if (type.startsWith('video/')) return FileVideo;
    return FileIcon;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'processing':
        return <Badge className="bg-blue-100 text-blue-700">Processing</Badge>;
      case 'ready':
        return <Badge className="bg-green-100 text-green-700">Ready</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-700">Failed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const SortIcon = ({ field }: { field: SortConfig['field'] }) => {
    if (sortConfig.field !== field) return <ArrowUpDown className="w-4 h-4 text-gray-400" />;
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium">Filters:</span>
        </div>
        
        <Select value={preacherFilter} onValueChange={setPreacherFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Preachers" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Preachers</SelectItem>
            {preachers.map(preacher => (
              <SelectItem key={preacher} value={preacher}>{preacher}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="ready">Ready</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>

        <div className="ml-auto flex items-center gap-2">
          {selectedFiles.size > 0 && (
            <>
              <span className="text-sm text-gray-500">{selectedFiles.size} selected</span>
              <Button variant="outline" size="sm" onClick={clearSelection}>Clear</Button>
              <Button variant="outline" size="sm" onClick={selectAll}>Select All</Button>
            </>
          )}
        </div>
      </div>

      {/* Data Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={files.length > 0 && selectedFiles.size === files.length}
                    onCheckedChange={(checked) => {
                      if (checked) selectAll();
                      else clearSelection();
                    }}
                  />
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('name')}>
                  <div className="flex items-center gap-2">
                    Filename
                    <SortIcon field="name" />
                  </div>
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('status')}>
                  <div className="flex items-center gap-2">
                    Status
                    <SortIcon field="status" />
                  </div>
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('date')}>
                  <div className="flex items-center gap-2">
                    Date
                    <SortIcon field="date" />
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Preacher
                  </div>
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('confidence')}>
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4" />
                    Quality
                    <SortIcon field="confidence" />
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    Team
                  </div>
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('size')}>
                  <div className="flex items-center gap-2">
                    Size
                    <SortIcon field="size" />
                  </div>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredFiles.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-12">
                    <FileIcon className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500">No files found</p>
                  </TableCell>
                </TableRow>
              ) : (
                filteredFiles.map((file) => {
                  const Icon = getFileIcon(file.type);
                  const isSelected = selectedFiles.has(file.id);

                  return (
                    <TableRow
                      key={file.id}
                      className={cn(isSelected && 'bg-blue-50')}
                    >
                      <TableCell>
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleSelection(file.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Icon className="w-5 h-5 text-blue-500" />
                          <span className="font-medium truncate max-w-[200px]">
                            {file.name}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(file.metadata?.status || 'ready')}
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {formatDistanceToNow(new Date(file.created_at), { addSuffix: true })}
                      </TableCell>
                      <TableCell>
                        {file.metadata?.speaker ? (
                          <Badge variant="outline">{file.metadata.speaker}</Badge>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Star className={cn(
                            'w-4 h-4',
                            (file.metadata?.confidence || 0.9) >= 0.9 ? 'text-green-500' :
                            (file.metadata?.confidence || 0.9) >= 0.8 ? 'text-yellow-500' : 'text-red-500'
                          )} />
                          <span className="text-sm">
                            {Math.round((file.metadata?.confidence || 0.9) * 100)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {file.metadata?.assignedTo ? (
                          <Badge variant="secondary">{file.metadata.assignedTo}</Badge>
                        ) : (
                          <span className="text-gray-400">Unassigned</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {formatFileSize(file.size)}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="text-sm text-gray-500">
        Showing {filteredFiles.length} of {files.length} files
      </div>
    </div>
  );
}

export default { FileUpload, SmartFileGrid };
