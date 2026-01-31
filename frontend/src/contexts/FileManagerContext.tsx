import { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from 'react';
import { fileRealtime, FileRecord } from '@/lib/supabase';
import { toast } from 'sonner';

interface FileManagerContextType {
  files: FileRecord[];
  loading: boolean;
  selectedFiles: Set<string>;
  toggleSelection: (fileId: string) => void;
  selectAll: () => void;
  clearSelection: () => void;
  refreshFiles: () => Promise<void>;
  updateFileStatus: (fileId: string, status: string) => Promise<void>;
}

const FileManagerContext = createContext<FileManagerContextType | undefined>(undefined);

// Mock data for demonstration
const MOCK_FILES: FileRecord[] = [
  {
    id: '1',
    name: 'sermon-jan-01.mp3',
    path: 'user-1/sermon-jan-01.mp3',
    size: 15_000_000,
    type: 'audio/mpeg',
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    user_id: 'user-1',
    metadata: {
      speaker: 'Pastor John',
      series: 'New Year Series',
      status: 'published',
      confidence: 0.95,
    },
  },
  {
    id: '2',
    name: 'sermon-jan-08.mp3',
    path: 'user-1/sermon-jan-08.mp3',
    size: 18_500_000,
    type: 'audio/mpeg',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    user_id: 'user-1',
    metadata: {
      speaker: 'Pastor John',
      series: 'New Year Series',
      status: 'reviewed',
      confidence: 0.92,
    },
  },
  {
    id: '3',
    name: 'special-message.mp4',
    path: 'user-1/special-message.mp4',
    size: 125_000_000,
    type: 'video/mp4',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'user-1',
    metadata: {
      speaker: 'Guest Speaker',
      status: 'uploaded',
      confidence: 0.88,
      tags: ['special', 'guest'],
    },
  },
  {
    id: '4',
    name: 'youth-service.mp3',
    path: 'user-1/youth-service.mp3',
    size: 12_000_000,
    type: 'audio/mpeg',
    created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    user_id: 'user-1',
    metadata: {
      speaker: 'Youth Pastor',
      series: 'Youth Series',
      status: 'transcribed',
      confidence: 0.90,
    },
  },
  {
    id: '5',
    name: 'bible-study-wk1.mp3',
    path: 'user-1/bible-study-wk1.mp3',
    size: 22_000_000,
    type: 'audio/mpeg',
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    user_id: 'user-1',
    metadata: {
      speaker: 'Elder Smith',
      series: 'Bible Study',
      status: 'published',
      confidence: 0.94,
    },
  },
];

export function FileManagerProvider({ children }: { children: ReactNode }) {
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

  // Load initial files
  useEffect(() => {
    // Simulate API call
    const loadFiles = async () => {
      setLoading(true);
      try {
        // In production, this would fetch from Supabase
        await new Promise(resolve => setTimeout(resolve, 500));
        setFiles(MOCK_FILES);
      } catch (error) {
        console.error('Error loading files:', error);
        toast.error('Failed to load files');
      } finally {
        setLoading(false);
      }
    };

    loadFiles();
  }, []);

  // Subscribe to real-time updates
  // (moved below refreshFiles declaration to avoid using it before it's defined)

  const refreshFiles = useCallback(async () => {
    setLoading(true);
    try {
      // In production, this would fetch from Supabase
      await new Promise(resolve => setTimeout(resolve, 300));
      setFiles([...MOCK_FILES]);
    } catch (error) {
      console.error('Error refreshing files:', error);
      toast.error('Failed to refresh files');
    } finally {
      setLoading(false);
    }
  }, []);

  // Subscribe to real-time updates (placed after refreshFiles so it's safe to reference)
  useEffect(() => {
    const isRefreshingRef = useRef(false);
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    const scheduleRefresh = () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }

      debounceTimer = setTimeout(async () => {
        const attempt = async () => {
          if (!isRefreshingRef.current) {
            isRefreshingRef.current = true;
            try {
              await refreshFiles();
            } catch (e) {
              // errors handled in refreshFiles
            } finally {
              isRefreshingRef.current = false;
            }
          } else {
            // If a refresh is already in progress, retry after a short delay
            setTimeout(attempt, 100);
          }
        };

        await attempt();
      }, 200);
    };

    const unsubscribe = fileRealtime.subscribeToFiles((payload) => {
      console.log('Real-time update:', payload);
      scheduleRefresh();
    });

    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      unsubscribe();
    };
  }, [refreshFiles]);

  const toggleSelection = useCallback((fileId: string) => {
    setSelectedFiles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(fileId)) {
        newSet.delete(fileId);
      } else {
        newSet.add(fileId);
      }
      return newSet;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedFiles(new Set(files.map(f => f.id)));
  }, [files]);

  const clearSelection = useCallback(() => {
    setSelectedFiles(new Set());
  }, []);

  const updateFileStatus = useCallback(async (fileId: string, status: string) => {
    try {
      // In production, this would update Supabase
      await new Promise(resolve => setTimeout(resolve, 200));
      setFiles(prev =>
        prev.map(f =>
          f.id === fileId
            ? { ...f, metadata: { ...f.metadata, status } }
            : f
        )
      );
    } catch (error) {
      console.error('Error updating file status:', error);
      throw error;
    }
  }, []);

  return (
    <FileManagerContext.Provider
      value={{
        files,
        loading,
        selectedFiles,
        toggleSelection,
        selectAll,
        clearSelection,
        refreshFiles,
        updateFileStatus,
      }}
    >
      {children}
    </FileManagerContext.Provider>
  );
}

export function useFileManager() {
  const context = useContext(FileManagerContext);
  if (context === undefined) {
    throw new Error('useFileManager must be used within a FileManagerProvider');
  }
  return context;
}
