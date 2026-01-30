import React, { useState, useCallback, useMemo } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { cn } from '@/app/components/ui/utils';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
  DragOverEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  Upload,
  FileAudio,
  FileVideo,
  File as FileIcon,
  MoreHorizontal,
  Calendar,
  User,
  GripVertical,
  CheckCircle2,
  Circle,
  Clock,
  Eye,
  Send,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';

interface KanbanCardProps {
  file: any;
  onStatusChange: (fileId: string, newStatus: string) => void;
}

function KanbanCard({ file, onStatusChange }: KanbanCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: file.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('audio/')) return FileAudio;
    if (type.startsWith('video/')) return FileVideo;
    return FileIcon;
  };

  const Icon = getFileIcon(file.type);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploaded':
        return 'bg-gray-100 text-gray-700';
      case 'transcribed':
        return 'bg-blue-100 text-blue-700';
      case 'reviewed':
        return 'bg-yellow-100 text-yellow-700';
      case 'published':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'bg-white rounded-lg shadow-sm border p-3 cursor-pointer transition-all',
        isDragging ? 'opacity-50 shadow-lg' : 'hover:shadow-md'
      )}
    >
      <div className="flex items-start gap-2">
        <button
          {...attributes}
          {...listeners}
          className="text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing mt-1"
        >
          <GripVertical className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Icon className="w-5 h-5 text-blue-500 flex-shrink-0" />
            <h4 className="text-sm font-medium truncate">{file.name}</h4>
          </div>
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            {file.metadata?.speaker && (
              <div className="flex items-center gap-1">
                <User className="w-3 h-3" />
                <span className="truncate">{file.metadata.speaker}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{formatDistanceToNow(new Date(file.created_at), { addSuffix: true })}</span>
            </div>
          </div>
          {file.metadata?.series && (
            <Badge variant="secondary" className="mt-2 text-[10px]">
              {file.metadata.series}
            </Badge>
          )}
        </div>
        <Button variant="ghost" size="icon" className="h-6 w-6">
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}

interface KanbanColumnProps {
  id: string;
  title: string;
  icon: React.ReactNode;
  files: any[];
  color: string;
  onStatusChange: (fileId: string, newStatus: string) => void;
}

function KanbanColumn({ id, title, icon, files, color, onStatusChange }: KanbanColumnProps) {
  const { setNodeRef } = useSortable({ id });

  return (
    <div className="flex flex-col bg-gray-50 rounded-xl h-full">
      <div className="flex items-center gap-2 p-3 border-b bg-white rounded-t-xl">
        <div className={cn('p-1.5 rounded-lg', color)}>{icon}</div>
        <h3 className="font-medium text-sm">{title}</h3>
        <Badge variant="secondary" className="ml-auto">
          {files.length}
        </Badge>
      </div>
      <div
        ref={setNodeRef}
        className="flex-1 p-2 overflow-y-auto space-y-2 min-h-[200px]"
      >
        <SortableContext items={files.map((f) => f.id)} strategy={verticalListSortingStrategy}>
          {files.map((file) => (
            <KanbanCard key={file.id} file={file} onStatusChange={onStatusChange} />
          ))}
        </SortableContext>
        {files.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center text-gray-400">
            <Circle className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-xs">Drop files here</p>
          </div>
        )}
      </div>
    </div>
  );
}

const COLUMNS = [
  { id: 'uploaded', title: 'Uploaded', icon: <Upload className="w-4 h-4" />, color: 'bg-gray-100 text-gray-600' },
  { id: 'transcribed', title: 'Transcribed', icon: <FileAudio className="w-4 h-4" />, color: 'bg-blue-100 text-blue-600' },
  { id: 'reviewed', title: 'Reviewed', icon: <Eye className="w-4 h-4" />, color: 'bg-yellow-100 text-yellow-600' },
  { id: 'published', title: 'Published', icon: <CheckCircle2 className="w-4 h-4" />, color: 'bg-green-100 text-green-600' },
];

export function KanbanBoard() {
  const { files, loading, updateFileStatus } = useFileManager();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [localFiles, setLocalFiles] = useState<any[]>([]);

  // Initialize local files when files load
  React.useEffect(() => {
    if (files.length > 0) {
      setLocalFiles(files);
    }
  }, [files]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const columns = useMemo(() => {
    const result: Record<string, any[]> = {
      uploaded: [],
      transcribed: [],
      reviewed: [],
      published: [],
    };

    localFiles.forEach((file) => {
      const status = file.metadata?.status || 'uploaded';
      if (result[status]) {
        result[status].push(file);
      } else {
        result['uploaded'].push(file);
      }
    });

    return result;
  }, [localFiles]);

  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  }, []);

  const handleDragOver = useCallback((event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeContainer = findContainer(active.id as string);
    const overContainer = findContainer(over.id as string);

    if (!activeContainer || !overContainer || activeContainer === overContainer) {
      return;
    }

    setLocalFiles((prev) => {
      const activeItems = prev.filter((f) => f.id === active.id);
      if (activeItems.length === 0) return prev;

      const activeItem = activeItems[0];
      const overItems = prev.filter((f) => {
        const container = findContainer(f.id);
        return container === overContainer;
      });

      const overIndex = overItems.findIndex((f) => f.id === over.id);
      const newIndex = overIndex >= 0 ? overIndex : overItems.length;

      return prev;
    });
  }, []);

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeContainer = findContainer(active.id as string);
    const overContainer = findContainer(over.id as string) || over.id;

    if (!activeContainer || !overContainer) return;

    if (activeContainer !== overContainer) {
      const newStatus = overContainer as string;
      try {
        await updateFileStatus(active.id as string, newStatus);
        const file = files.find((f) => f.id === active.id);
        if (file) {
          toast.success(`Moved "${file.name}" to ${COLUMNS.find((c) => c.id === newStatus)?.title}`);
        }
      } catch {
        toast.error('Failed to update file status');
      }
    }
  }, [files, updateFileStatus]);

  const findContainer = useCallback((id: string) => {
    if (COLUMNS.some((col) => col.id === id)) return id;
    return localFiles.find((f) => f.id === id)?.metadata?.status || 'uploaded';
  }, [localFiles]);

  const handleStatusChange = useCallback((fileId: string, newStatus: string) => {
    setLocalFiles((prev) =>
      prev.map((f) =>
        f.id === fileId ? { ...f, metadata: { ...f.metadata, status: newStatus } } : f
      )
    );
    const file = localFiles.find((f) => f.id === fileId);
    if (file) {
      toast.success(`Moved "${file.name}" to ${COLUMNS.find((c) => c.id === newStatus)?.title}`);
    }
  }, [localFiles]);

  const activeFile = activeId ? localFiles.find((f) => f.id === activeId) : null;

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <div className="text-lg text-gray-500">Loading Kanban board...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-4 gap-4 h-[600px]">
        {COLUMNS.map((column) => (
          <KanbanColumn
            key={column.id}
            id={column.id}
            title={column.title}
            icon={column.icon}
            color={column.color}
            files={columns[column.id] || []}
            onStatusChange={handleStatusChange}
          />
        ))}
      </div>
      <DragOverlay>
        {activeFile ? (
          <div className="bg-white rounded-lg shadow-lg border p-3 w-[280px]">
            <div className="flex items-center gap-2">
              <FileIcon className="w-5 h-5 text-blue-500" />
              <h4 className="text-sm font-medium truncate">{activeFile.name}</h4>
            </div>
            {activeFile.metadata?.speaker && (
              <p className="text-xs text-gray-500 mt-1">{activeFile.metadata.speaker}</p>
            )}
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
