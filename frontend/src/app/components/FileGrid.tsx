import React from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { Checkbox } from '@/app/components/ui/checkbox';
import { Card, CardContent } from '@/app/components/ui/card';
import { FileAudio, FileVideo, File as FileIcon, Folder } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export function FileGrid() {
  const { files, loading, selectedFiles, toggleSelection } = useFileManager();

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-lg text-gray-500">Loading files...</div>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <FileIcon className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No files yet</h3>
        <p className="text-sm text-gray-500">Upload your first sermon file to get started</p>
      </div>
    );
  }

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

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4">
      {files.map((file) => {
        const Icon = getFileIcon(file.type);
        const isSelected = selectedFiles.has(file.id);

        return (
          <Card
            key={file.id}
            className={`cursor-pointer transition-all ${
              isSelected ? 'ring-2 ring-blue-500' : ''
            }`}
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
                    <Icon className="w-8 h-8 text-blue-500 flex-shrink-0 mt-1" />
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatFileSize(file.size)}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {formatDistanceToNow(new Date(file.created_at), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              {file.metadata?.speaker && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs text-gray-600">
                    Speaker: {file.metadata.speaker}
                  </p>
                </div>
              )}
              {file.metadata?.series && (
                <div className="mt-1">
                  <p className="text-xs text-gray-600">
                    Series: {file.metadata.series}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
