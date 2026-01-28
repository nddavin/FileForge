/* File Manager Context - Bulk operations, sorting rules, selection state */

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { supabase } from '../lib/supabase';

// File type
export interface FileType {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  folder_id: string | null;
  preacher_id: string | null;
  primary_language: string | null;
  location_city: string | null;
  quality_score: number | null;
  sermon_package_id: string | null;
  predicted_folder: string | null;
  sorting_score: number | null;
  created_at: string;
  profiles?: {
    id: string;
    full_name: string;
    avatar_url: string | null;
  };
}

// Sorting rule condition
export interface SortCondition {
  field: string;
  operator: 'eq' | 'ne' | 'contains' | 'gt' | 'lt' | 'gte' | 'lte';
  value: string | number | boolean;
}

// Sorting rule
export interface SortingRule {
  id?: string;
  church_id: string;
  name: string;
  conditions: SortCondition[];
  target_folder: string;
  priority: number;
  auto_apply: boolean;
}

// Sermon package
export interface SermonPackage {
  id: string;
  name: string;
  file_count: number;
  has_audio: boolean;
  has_video: boolean;
  has_transcript: boolean;
  created_at: string;
}

// Context type
interface FileManagerContextType {
  // Files
  files: FileType[];
  loading: boolean;
  refreshFiles: () => void;
  
  // Selection
  selectedIds: Set<string>;
  toggleSelection: (id: string) => void;
  selectAll: () => void;
  clearSelection: () => void;
  isSelected: (id: string) => boolean;
  
  // Sorting Rules
  sortingRules: SortingRule[];
  saveRule: (rule: SortingRule) => Promise<void>;
  deleteRule: (ruleId: string) => Promise<void>;
  
  // Bulk Operations
  bulkPackage: () => Promise<void>;
  bulkOptimize: () => Promise<void>;
  bulkAiSort: () => Promise<void>;
  bulkAssignFolder: (folderId: string) => Promise<void>;
  
  // Preview Mode
  previewMode: boolean;
  previewSortBy: string | null;
  setPreviewMode: (enabled: boolean) => void;
  previewSort: (field: string) => void;
  applyPreviewSort: () => Promise<void>;
  
  // Sermon Packages
  sermonPackages: SermonPackage[];
  relationshipMap: Map<string, FileType[]>;
  
  // Stats
  totalFiles: number;
  selectedCount: number;
}

const FileManagerContext = createContext<FileManagerContextType | null>(null);

// Provider props
interface FileManagerProviderProps {
  children: ReactNode;
  churchId: string;
}

export const FileManagerProvider: React.FC<FileManagerProviderProps> = ({ 
  children, 
  churchId 
}) => {
  // Files state
  const [files, setFiles] = useState<FileType[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  
  // Sorting rules state
  const [sortingRules, setSortingRules] = useState<SortingRule[]>([]);
  
  // Preview mode state
  const [previewMode, setPreviewMode] = useState(false);
  const [previewSortBy, setPreviewSortBy] = useState<string | null>(null);
  const [previewedFiles, setPreviewedFiles] = useState<FileType[]>([]);
  
  // Sermon packages
  const [sermonPackages, setSermonPackages] = useState<SermonPackage[]>([]);
  
  // Fetch files
  const refreshFiles = useCallback(async () => {
    setLoading(true);
    
    try {
      const { data, error } = await supabase
        .from('files')
        .select(`
          *,
          profiles!preacher_id_fkey (id, full_name, avatar_url)
        `)
        .eq('church_id', churchId)
        .order('created_at', { ascending: false })
        .limit(500);
      
      if (error) {
        console.error('Error fetching files:', error);
      } else {
        setFiles(data || []);
      }
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [churchId]);
  
  // Fetch sorting rules
  const fetchSortingRules = useCallback(async () => {
    const { data, error } = await supabase
      .from('sorting_rules')
      .select('*')
      .eq('church_id', churchId)
      .order('priority', { ascending: true });
    
    if (!error && data) {
      setSortingRules(data as SortingRule[]);
    }
  }, [churchId]);
  
  // Fetch on mount
  useEffect(() => {
    refreshFiles();
    fetchSortingRules();
  }, [refreshFiles, fetchSortingRules]);
  
  // Selection helpers
  const toggleSelection = useCallback((id: string) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);
  
  const selectAll = useCallback(() => {
    setSelectedIds(new Set(files.map(f => f.id)));
  }, [files]);
  
  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);
  
  const isSelected = useCallback((id: string) => {
    return selectedIds.has(id);
  }, [selectedIds]);
  
  // Sorting rules
  const saveRule = useCallback(async (rule: SortingRule) => {
    const { data, error } = await supabase
      .from('sorting_rules')
      .upsert({ ...rule, church_id: churchId })
      .select()
      .single();
    
    if (!error && data) {
      setSortingRules(prev => {
        const filtered = prev.filter(r => r.id !== data.id);
        return [...filtered, data as SortingRule];
      });
    }
  }, [churchId]);
  
  const deleteRule = useCallback(async (ruleId: string) => {
    const { error } = await supabase
      .from('sorting_rules')
      .delete()
      .eq('id', ruleId);
    
    if (!error) {
      setSortingRules(prev => prev.filter(r => r.id !== ruleId));
    }
  }, []);
  
  // Bulk operations
  const bulkPackage = useCallback(async () => {
    const fileIds = Array.from(selectedIds);
    const response = await fetch('/api/v1/files/bulk-package', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_ids: fileIds, church_id: churchId })
    });
    
    if (response.ok) {
      refreshFiles();
      clearSelection();
    }
  }, [selectedIds, churchId, refreshFiles, clearSelection]);
  
  const bulkOptimize = useCallback(async () => {
    const fileIds = Array.from(selectedIds);
    const response = await fetch('/api/v1/files/bulk-optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_ids: fileIds, church_id: churchId })
    });
    
    if (response.ok) {
      clearSelection();
    }
  }, [selectedIds, churchId, clearSelection]);
  
  const bulkAiSort = useCallback(async () => {
    const fileIds = Array.from(selectedIds);
    const response = await fetch('/api/v1/files/bulk-sort', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_ids: fileIds, rules: sortingRules, church_id: churchId })
    });
    
    if (response.ok) {
      refreshFiles();
      clearSelection();
    }
  }, [selectedIds, sortingRules, churchId, refreshFiles, clearSelection]);
  
  const bulkAssignFolder = useCallback(async (folderId: string) => {
    const fileIds = Array.from(selectedIds);
    const response = await fetch('/api/v1/files/bulk-move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_ids: fileIds, folder_id: folderId })
    });
    
    if (response.ok) {
      refreshFiles();
      clearSelection();
    }
  }, [selectedIds, refreshFiles, clearSelection]);
  
  // Preview mode
  const setPreviewModeEnabled = useCallback((enabled: boolean) => {
    setPreviewMode(enabled);
    if (!enabled) {
      setPreviewSortBy(null);
      setPreviewedFiles([]);
    }
  }, []);
  
  const previewSort = useCallback((field: string) => {
    setPreviewSortBy(field);
    const sorted = [...files].sort((a, b) => {
      switch (field) {
        case 'preacher':
          return (a.profiles?.full_name || '').localeCompare(b.profiles?.full_name || '');
        case 'location':
          return (a.location_city || '').localeCompare(b.location_city || '');
        case 'quality':
          return (b.quality_score || 0) - (a.quality_score || 0);
        default:
          return 0;
      }
    });
    setPreviewedFiles(sorted);
  }, [files]);
  
  const applyPreviewSort = useCallback(async () => {
    if (!previewSortBy) return;
    
    const response = await fetch('/api/v1/files/bulk-sort', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        file_ids: Array.from(selectedIds),
        sort_by: previewSortBy,
        church_id: churchId
      })
    });
    
    if (response.ok) {
      setPreviewMode(false);
      setPreviewSortBy(null);
      setPreviewedFiles([]);
      refreshFiles();
      clearSelection();
    }
  }, [previewSortBy, selectedIds, churchId, refreshFiles, clearSelection]);
  
  // Compute relationship map
  const relationshipMap = React.useMemo(() => {
    const map = new Map<string, FileType[]>();
    files.forEach(file => {
      if (file.sermon_package_id) {
        const existing = map.get(file.sermon_package_id) || [];
        map.set(file.sermon_package_id, [...existing, file]);
      }
    });
    return map;
  }, [files]);
  
  return (
    <FileManagerContext.Provider
      value={{
        files,
        loading,
        refreshFiles,
        selectedIds,
        toggleSelection,
        selectAll,
        clearSelection,
        isSelected,
        sortingRules,
        saveRule,
        deleteRule,
        bulkPackage,
        bulkOptimize,
        bulkAiSort,
        bulkAssignFolder,
        previewMode,
        previewSortBy,
        setPreviewMode: setPreviewModeEnabled,
        previewSort,
        applyPreviewSort,
        sermonPackages,
        relationshipMap,
        totalFiles: files.length,
        selectedCount: selectedIds.size
      }}
    >
      {children}
    </FileManagerContext.Provider>
  );
};

export const useFileManager = (): FileManagerContextType => {
  const context = useContext(FileManagerContext);
  if (!context) {
    throw new Error('useFileManager must be used within FileManagerProvider');
  }
  return context;
};

// Helper to predict folder based on file
export const predictFolder = (file: FileType, rules: SortingRule[]): string => {
  for (const rule of rules) {
    const matches = rule.conditions.every(cond => {
      const value = (file as any)[cond.field];
      switch (cond.operator) {
        case 'eq': return value === cond.value;
        case 'ne': return value !== cond.value;
        case 'contains': return String(value).includes(String(cond.value));
        case 'gt': return Number(value) > Number(cond.value);
        case 'lt': return Number(value) < Number(cond.value);
        default: return false;
      }
    });
    if (matches) return rule.target_folder;
  }
  return 'unsorted';
};

// Helper to get quality color
export const getQualityColor = (score: number | null): string => {
  if (score === null) return 'gray';
  if (score >= 80) return 'green';
  if (score >= 60) return 'yellow';
  if (score >= 40) return 'orange';
  return 'red';
};
