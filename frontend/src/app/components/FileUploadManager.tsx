import React, { useState, useCallback, useRef } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Progress } from '@/app/components/ui/progress';
import { Checkbox } from '@/app/components/ui/checkbox';
import {
  Upload,
  FileAudio,
  FileVideo,
  File as FileIcon,
  Folder,
  Tag,
  Trash2,
  Move,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  CloudUpload,
  Image,
  Film,
  Music,
  FileText,
  MoreVertical,
  Users,
  Eye,
  EyeOff,
  FolderPlus,
  FolderOpen,
  Clock,
} from 'lucide-react';
import { cn, formatFileSize } from '@/app/components/ui/utils';
import { toast } from 'sonner';

interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
  preview?: string;
  metadata?: {
    speaker?: string;
    series?: string;
    tags?: string[];
  };
}

interface BulkOperation {
  type: 'tag' | 'move' | 'delete';
  target?: string;
  tags?: string[];
}

interface SmartFolder {
  id: string;
  name: string;
  icon?: React.ReactNode;
  rule: {
    field: string;
    operator: 'equals' | 'contains' | 'startsWith';
    value: string;
  };
}

export function FileUploadManager() {
  const { user } = useAuth();
  const { files, refreshFiles, selectedFiles, toggleSelection, clearSelection } = useFileManager();
  const [uploadQueue, setUploadQueue] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [ownershipFilter, setOwnershipFilter] = useState<'own' | 'all'>('own');
  const [smartFolders, setSmartFolders] = useState<SmartFolder[]>([
    { id: 'recent', name: 'Recent', icon: <Clock className="w-4 h-4" />, rule: { field: 'created_at', operator: 'contains', value: 'week' } },
    { id: 'audio', name: 'Audio Only', icon: <Music className="w-4 h-4" />, rule: { field: 'type', operator: 'startsWith', value: 'audio' } },
    { id: 'video', name: 'Video Only', icon: <Film className="w-4 h-4" />, rule: { field: 'type', operator: 'startsWith', value: 'video' } },
    { id: 'published', name: 'Published', icon: <CheckCircle className="w-4 h-4" />, rule: { field: 'status', operator: 'equals', value: 'published' } },
  ]);
  const [activeSmartFolder, setActiveSmartFolder] = useState<string | null>(null);
  const [selectedFolder, setSelectedFolder] = useState<string>('all');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Simulate chunked upload with progress
  const uploadFileChunk = async (uploadFile: UploadFile): Promise<void> => {
    const chunkSize = 1024 * 1024; // 1MB chunks
    const totalChunks = Math.ceil(uploadFile.file.size / chunkSize);
    let uploadedChunks = 0;

    return new Promise((resolve, reject) => {
      const uploadChunk = async (chunkIndex: number) => {
        if (chunkIndex >= totalChunks) {
          setUploadQueue(prev =>
            prev.map(f =>
              f.id === uploadFile.id
                ? { ...f, status: 'completed' as const, progress: 100 }
                : f
            )
          );
          resolve();
          return;
        }

        // Simulate chunk upload delay
        await new Promise(resolve => setTimeout(resolve, 200));

        uploadedChunks++;
        const progress = Math.round((uploadedChunks / totalChunks) * 100);

        setUploadQueue(prev =>
          prev.map(f =>
            f.id === uploadFile.id ? { ...f, progress } : f
          )
        );

        uploadChunk(chunkIndex + 1);
      };

      setUploadQueue(prev =>
        prev.map(f =>
          f.id === uploadFile.id ? { ...f, status: 'uploading' as const } : f
        )
      );

      uploadChunk(0);
    });
  };

  const handleFiles = useCallback(async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;

    const newFiles: UploadFile[] = Array.from(fileList).map(file => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      progress: 0,
      status: 'pending' as const,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    }));

    setUploadQueue(prev => [...prev, ...newFiles]);

    // Start uploading
    for (const uploadFile of newFiles) {
      try {
        await uploadFileChunk(uploadFile);
      } catch (error) {
        setUploadQueue(prev =>
          prev.map(f =>
            f.id === uploadFile.id
              ? { ...f, status: 'error' as const, error: 'Upload failed' }
              : f
          )
        );
      }
    }

    toast.success(`Uploaded ${newFiles.length} file(s)`);
    await refreshFiles();
  }, [refreshFiles]);

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

  const removeFromQueue = useCallback((id: string) => {
    setUploadQueue(prev => {
      const file = prev.find(f => f.id === id);
      if (file?.preview) URL.revokeObjectURL(file.preview);
      return prev.filter(f => f.id !== id);
    });
  }, []);

  const clearCompleted = useCallback(() => {
    setUploadQueue(prev => {
      prev.forEach(f => {
        if (f.preview) URL.revokeObjectURL(f.preview);
      });
      return prev.filter(f => f.status !== 'completed');
    });
  }, []);

  const getFileIcon = (type: string) => {
    if (type.startsWith('audio/')) return FileAudio;
    if (type.startsWith('video/')) return FileVideo;
    if (type.startsWith('image/')) return Image;
    if (type.includes('pdf') || type.includes('document')) return FileText;
    return FileIcon;
  };

  // Filter files based on ownership and folder
  const filteredFiles = files.filter(file => {
    // Ownership filter
    if (ownershipFilter === 'own' && file.user_id !== user?.id) {
      return false;
    }

    // Smart folder filter
    if (activeSmartFolder) {
      const folder = smartFolders.find(f => f.id === activeSmartFolder);
      if (folder) {
        const { field, operator, value } = folder.rule;
        const fieldValue = field === 'type' ? file.type : file.metadata?.[field];
        
        switch (operator) {
          case 'equals':
            if (fieldValue !== value) return false;
            break;
          case 'contains':
            if (!String(fieldValue).includes(value)) return false;
            break;
          case 'startsWith':
            if (!String(fieldValue).startsWith(value)) return false;
            break;
        }
      }
    }

    return true;
  });

  // Bulk operations
  const handleBulkDelete = useCallback(async () => {
    if (selectedFiles.size === 0) return;
    
    const confirmDelete = window.confirm(`Delete ${selectedFiles.size} file(s)?`);
    if (!confirmDelete) return;

    // Simulate bulk delete
    toast.success(`Deleted ${selectedFiles.size} file(s)`);
    clearSelection();
    await refreshFiles();
  }, [selectedFiles, clearSelection, refreshFiles]);

  const handleBulkTag = useCallback(async (tags: string[]) => {
    if (selectedFiles.size === 0) return;
    
    // Simulate bulk tagging
    toast.success(`Tagged ${selectedFiles.size} file(s) with ${tags.join(', ')}`);
  }, [selectedFiles]);

  const handleBulkMove = useCallback(async (folderId: string) => {
    if (selectedFiles.size === 0) return;
    
    toast.success(`Moved ${selectedFiles.size} file(s) to folder`);
    clearSelection();
  }, [selectedFiles, clearSelection]);

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <Card
        className={cn(
          'border-2 border-dashed transition-colors',
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="p-8">
          <div className="flex flex-col items-center justify-center text-center">
            <div className={cn(
              'p-4 rounded-full mb-4 transition-colors',
              isDragging ? 'bg-blue-100' : 'bg-gray-100'
            )}>
              <CloudUpload className={cn(
                'w-10 h-10 transition-colors',
                isDragging ? 'text-blue-500' : 'text-gray-400'
              )} />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Drag and drop files here
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              or click to browse (supports audio, video, documents)
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="audio/*,video/*,image/*,.pdf,.doc,.docx"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <Button onClick={() => fileInputRef.current?.click()}>
              <Upload className="w-4 h-4 mr-2" />
              Browse Files
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Upload Queue */}
      {uploadQueue.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Upload Queue</CardTitle>
              <Button variant="outline" size="sm" onClick={clearCompleted}>
                Clear Completed
              </Button>
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
                  {/* Preview or Icon */}
                  <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden">
                    {uploadFile.preview ? (
                      <img
                        src={uploadFile.preview}
                        alt={uploadFile.file.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <Icon className="w-6 h-6 text-gray-400" />
                    )}
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{uploadFile.file.name}</p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(uploadFile.file.size)}
                    </p>
                    <div className="mt-2">
                      <Progress value={uploadFile.progress} className="h-1" />
                    </div>
                  </div>

                  {/* Status */}
                  <div className="flex items-center gap-2">
                    {uploadFile.status === 'uploading' && (
                      <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    )}
                    {uploadFile.status === 'completed' && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {uploadFile.status === 'error' && (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                    <span className="text-sm text-gray-500 w-12 text-right">
                      {uploadFile.progress}%
                    </span>
                    {uploadFile.status !== 'uploading' && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => removeFromQueue(uploadFile.id)}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* File Browser with Smart Folders */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Files</CardTitle>
            <div className="flex items-center gap-3">
              {/* Ownership Filter */}
              <div className="flex items-center gap-2">
                <Button
                  variant={ownershipFilter === 'own' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setOwnershipFilter('own')}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Own
                </Button>
                <Button
                  variant={ownershipFilter === 'all' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setOwnershipFilter('all')}
                >
                  <Users className="w-4 h-4 mr-1" />
                  All
                </Button>
              </div>

              {/* Bulk Actions Toggle */}
              {selectedFiles.size > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">{selectedFiles.size} selected</span>
                  <Button variant="outline" size="sm" onClick={() => setShowBulkActions(!showBulkActions)}>
                    <MoreVertical className="w-4 h-4 mr-1" />
                    Bulk Actions
                  </Button>
                  <Button variant="outline" size="sm" onClick={clearSelection}>
                    Clear
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            {/* Smart Folders Sidebar */}
            <div className="w-48 flex-shrink-0 border-r pr-4">
              <div className="space-y-1">
                <Button
                  variant={selectedFolder === 'all' ? 'secondary' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => {
                    setSelectedFolder('all');
                    setActiveSmartFolder(null);
                  }}
                >
                  <Folder className="w-4 h-4 mr-2" />
                  All Files
                </Button>
                
                <div className="pt-2 pb-1">
                  <p className="text-xs font-medium text-gray-500 uppercase px-2">Smart Folders</p>
                </div>
                
                {smartFolders.map(folder => (
                  <Button
                    key={folder.id}
                    variant={activeSmartFolder === folder.id ? 'secondary' : 'ghost'}
                    className="w-full justify-start"
                    onClick={() => {
                      setActiveSmartFolder(folder.id);
                      setSelectedFolder(folder.id);
                    }}
                  >
                    {folder.icon || <FolderOpen className="w-4 h-4 mr-2" />}
                    {folder.name}
                  </Button>
                ))}
              </div>

              {/* Bulk Actions Panel */}
              {showBulkActions && selectedFiles.size > 0 && (
                <div className="mt-4 pt-4 border-t space-y-2">
                  <p className="text-xs font-medium text-gray-500 uppercase px-2">Bulk Actions</p>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => handleBulkTag(['new', 'bulk'])}
                  >
                    <Tag className="w-4 h-4 mr-2" />
                    Add Tags
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => handleBulkMove('sermons')}
                  >
                    <Move className="w-4 h-4 mr-2" />
                    Move to Folder
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start text-red-600 hover:text-red-700"
                    onClick={handleBulkDelete}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Selected
                  </Button>
                </div>
              )}
            </div>

            {/* File List */}
            <div className="flex-1">
              {filteredFiles.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Folder className="w-16 h-16 text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No files found</h3>
                  <p className="text-sm text-gray-500">
                    {ownershipFilter === 'own' 
                      ? 'Upload files to get started' 
                      : 'No files available'}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredFiles.map(file => {
                    const Icon = getFileIcon(file.type);
                    const isSelected = selectedFiles.has(file.id);

                    return (
                      <div
                        key={file.id}
                        className={cn(
                          'flex items-center gap-4 p-3 rounded-lg border cursor-pointer hover:bg-gray-50 transition-colors',
                          isSelected ? 'bg-blue-50 border-blue-200' : ''
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
                          <p className="text-sm font-medium truncate">{file.name}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {file.metadata?.speaker && (
                              <span className="text-xs text-gray-500">{file.metadata.speaker}</span>
                            )}
                            {file.metadata?.series && (
                              <Badge variant="outline" className="text-[10px]">
                                {file.metadata.series}
                              </Badge>
                            )}
                            <Badge variant="secondary" className="text-[10px]">
                              {file.metadata?.status || 'uploaded'}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>{formatFileSize(file.size)}</span>
                          <span className="text-xs">
                            {new Date(file.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default FileUploadManager;
