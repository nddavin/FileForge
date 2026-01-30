import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { fileRealtime } from '@/lib/supabase';
import { projectId, publicAnonKey } from '/utils/supabase/info';

interface FileData {
  id: string;
  name: string;
  path: string;
  size: number;
  type: string;
  created_at: string;
  folder_id?: string;
  metadata?: Record<string, any>;
  url?: string;
}

interface FileManagerContextType {
  files: FileData[];
  loading: boolean;
  selectedFiles: Set<string>;
  toggleSelection: (fileId: string) => void;
  selectAll: () => void;
  clearSelection: () => void;
  refreshFiles: () => Promise<void>;
  uploadProgress: Map<string, number>;
  updateFileStatus: (fileId: string, status: string) => Promise<void>;
}

const FileManagerContext = createContext<FileManagerContextType | undefined>(undefined);

export function FileManagerProvider({ children }: { children: ReactNode }) {
  const [files, setFiles] = useState<FileData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [uploadProgress, setUploadProgress] = useState<Map<string, number>>(new Map());

  const fetchFiles = useCallback(async () => {
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/files`,
        {
          headers: {
            Authorization: `Bearer ${publicAnonKey}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch files');
      }

      const data = await response.json();
      setFiles(data);
    } catch (error) {
      console.error('Error fetching files:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles();

    // Subscribe to realtime changes
    const unsubscribe = fileRealtime.subscribeToFiles((payload) => {
      console.log('File change:', payload);
      fetchFiles();
    });

    return () => {
      unsubscribe();
    };
  }, [fetchFiles]);

  const toggleSelection = (fileId: string) => {
    setSelectedFiles((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(fileId)) {
        newSet.delete(fileId);
      } else {
        newSet.add(fileId);
      }
      return newSet;
    });
  };

  const selectAll = () => {
    setSelectedFiles(new Set(files.map((f) => f.id)));
  };

  const clearSelection = () => {
    setSelectedFiles(new Set());
  };

  const refreshFiles = async () => {
    setLoading(true);
    await fetchFiles();
  };

  const updateFileStatus = async (fileId: string, status: string) => {
    try {
      const file = files.find(f => f.id === fileId);
      if (!file) return;

      const newMetadata = { ...file.metadata, status };
      
      // Optimistic update
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, metadata: newMetadata } : f
      ));

      // Persist to backend
      await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/files/${fileId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${publicAnonKey}`,
        },
        body: JSON.stringify({ metadata: newMetadata }),
      });
    } catch (error) {
      console.error('Error updating file status:', error);
      // Revert on error
      await fetchFiles();
      throw error;
    }
  };

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
        uploadProgress,
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
