/* Sermon Search Context - Preacher filtering, URL state, real-time updates, sorting */

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { supabase } from '../lib/supabase';

// Filter interface
export interface SermonFilters {
  preacher_id: string | null;
  language: string | null;
  date_from: string | null;
  date_to: string | null;
  min_confidence: number;
  search_term: string;
}

// Sort configuration
export interface SortConfig {
  sort_by: string;
  sort_direction: 'asc' | 'desc';
}

// Sort option type
interface SortOption {
  label: string;
  value: string;
  field: string;
  direction: 'asc' | 'desc';
}

// Sort options
export const SORT_OPTIONS: SortOption[] = [
  { label: 'Newest First', value: 'date_desc', field: 'created_at', direction: 'desc' },
  { label: 'Oldest First', value: 'date_asc', field: 'created_at', direction: 'asc' },
  { label: 'Preacher A-Z', value: 'preacher_asc', field: 'profiles.full_name', direction: 'asc' },
  { label: 'Preacher Z-A', value: 'preacher_desc', field: 'profiles.full_name', direction: 'desc' },
  { label: 'Duration Short → Long', value: 'duration_asc', field: 'duration_seconds', direction: 'asc' },
  { label: 'Duration Long → Short', value: 'duration_desc', field: 'duration_seconds', direction: 'desc' },
  { label: 'Confidence High → Low', value: 'confidence_desc', field: 'speaker_confidence_avg', direction: 'desc' },
  { label: 'Confidence Low → High', value: 'confidence_asc', field: 'speaker_confidence_avg', direction: 'asc' },
  { label: 'Title A-Z', value: 'title_asc', field: 'title', direction: 'asc' },
  { label: 'Title Z-A', value: 'title_desc', field: 'title', direction: 'desc' },
];

// Basic sermon type (simplified)
export interface SermonType {
  id: string;
  title: string;
  description: string | null;
  primary_language: string | null;
  speaker_confidence_avg: number | null;
  created_at: string;
  duration_seconds: number | null;
  profiles?: {
    id: string;
    full_name: string;
    avatar_url: string | null;
  };
  sermon_speaker_segments?: Array<{
    language: string | null;
    confidence: number | null;
  }>;
}

// Context type
interface SermonSearchContextType {
  filters: SermonFilters;
  setFilter: (key: keyof SermonFilters, value: any) => void;
  clearFilters: () => void;
  sortConfig: SortConfig;
  setSort: (sortValue: string) => void;
  sortOptions: SortOption[];
  sermons: SermonType[];
  loading: boolean;
  totalCount: number;
  page: number;
  setPage: (page: number) => void;
  refresh: () => void;
}

// Context with null state
const SermonSearchContext = createContext<SermonSearchContextType | null>(null);

// Provider props
interface SermonSearchProviderProps {
  children: ReactNode;
  pageSize?: number;
}

// Get sort field from sort value
export const getSortField = (sortValue: string): string => {
  const option = SORT_OPTIONS.find(opt => opt.value === sortValue);
  return option?.field || 'created_at';
};

// Get sort direction from sort value
export const getSortDirection = (sortValue: string): 'asc' | 'desc' => {
  const option = SORT_OPTIONS.find(opt => opt.value === sortValue);
  return option?.direction || 'desc';
};

export const SermonSearchProvider: React.FC<SermonSearchProviderProps> = ({ 
  children, 
  pageSize = 20 
}) => {
  // Filter state
  const [filters, setFiltersState] = useState<SermonFilters>({
    preacher_id: null,
    language: null,
    date_from: null,
    date_to: null,
    min_confidence: 0.7,
    search_term: ''
  });
  
  // Sort state
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    sort_by: 'date_desc',
    sort_direction: 'desc'
  });
  
  // Data state
  const [sermons, setSermons] = useState<SermonType[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPageState] = useState(1);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Build Supabase query
  const buildQuery = useCallback(() => {
    let query = supabase
      .from('sermons')
      .select(`
        *,
        profiles!primary_preacher_id_fkey (
          id,
          full_name,
          avatar_url
        ),
        sermon_speaker_segments (language, confidence)
      `, { count: 'exact' });

    // Apply filters
    if (filters.preacher_id) {
      query = query.eq('primary_preacher_id', filters.preacher_id);
    }
    if (filters.language) {
      query = query.eq('primary_language', filters.language);
    }
    query = query.gte('speaker_confidence_avg', filters.min_confidence);
    if (filters.date_from) query = query.gte('created_at', filters.date_from);
    if (filters.date_to) query = query.lte('created_at', filters.date_to);
    
    if (filters.search_term) {
      query = query.or(`
        title.ilike.%${filters.search_term}%,
        description.ilike.%${filters.search_term}%,
        theme_scripture.ilike.%${filters.search_term}%,
        profiles.full_name.ilike.%${filters.search_term}%
      `);
    }

    // Apply sorting
    const sortField = getSortField(sortConfig.sort_by);
    query = query.order(sortField, { 
      ascending: sortConfig.sort_direction === 'asc',
      nullsfirst: false 
    });

    // Apply pagination
    const from = (page - 1) * pageSize;
    const to = from + pageSize - 1;
    query = query.range(from, to);

    return query;
  }, [filters, page, sortConfig]);

  // Fetch sermons
  const fetchSermons = useCallback(async () => {
    setLoading(true);
    
    try {
      const query = buildQuery();
      const { data, error, count } = await query;

      if (error) {
        console.error('Error fetching sermons:', error);
      } else {
        setSermons(data || []);
        setTotalCount(count || 0);
      }
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [buildQuery]);

  // Set filter helper
  const setFilter = useCallback((key: keyof SermonFilters, value: any) => {
    setFiltersState(prev => ({ ...prev, [key]: value }));
    setPageState(1);
  }, []);

  // Set sort helper
  const setSort = useCallback((sortValue: string) => {
    const direction = sortValue.endsWith('_asc') ? 'asc' : 'desc';
    setSortConfig({ sort_by: sortValue, sort_direction: direction });
    setPageState(1);
  }, []);

  // Clear all filters (keep sort)
  const clearFilters = useCallback(() => {
    setFiltersState({
      preacher_id: null,
      language: null,
      date_from: null,
      date_to: null,
      min_confidence: 0.7,
      search_term: ''
    });
    setPageState(1);
  }, []);

  // Refresh data
  const refresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // Set page
  const setPage = useCallback((newPage: number) => {
    setPageState(newPage);
  }, []);

  // Sync URL on filter/sort changes
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (filters.preacher_id) params.set('preacher', filters.preacher_id);
    if (filters.language) params.set('lang', filters.language);
    if (filters.search_term) params.set('q', filters.search_term);
    if (filters.date_from) params.set('from', filters.date_from);
    if (filters.date_to) params.set('to', filters.date_to);
    if (sortConfig.sort_by !== 'date_desc') params.set('sort', sortConfig.sort_by);
    if (page > 1) params.set('page', page.toString());

    const newUrl = `?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
  }, [filters, sortConfig, page]);

  // Load filters/sort from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    
    setFiltersState(prev => ({
      ...prev,
      preacher_id: params.get('preacher') || null,
      language: params.get('lang') || null,
      search_term: params.get('q') || '',
      date_from: params.get('from') || null,
      date_to: params.get('to') || null
    }));
    
    const urlSort = params.get('sort');
    if (urlSort && SORT_OPTIONS.some(opt => opt.value === urlSort)) {
      const direction = urlSort.endsWith('_asc') ? 'asc' : 'desc';
      setSortConfig({ sort_by: urlSort, sort_direction: direction });
    }
    
    const urlPage = params.get('page');
    if (urlPage) {
      setPageState(parseInt(urlPage, 10));
    }
  }, []);

  // Fetch on any state change
  useEffect(() => {
    fetchSermons();
  }, [fetchSermons, refreshTrigger]);

  return (
    <SermonSearchContext.Provider
      value={{
        filters,
        setFilter,
        clearFilters,
        sortConfig,
        setSort,
        sortOptions: SORT_OPTIONS,
        sermons,
        loading,
        totalCount,
        page,
        setPage,
        refresh
      }}
    >
      {children}
    </SermonSearchContext.Provider>
  );
};

// Hook to use context
export const useSermonSearch = (): SermonSearchContextType => {
  const context = useContext(SermonSearchContext);
  if (!context) {
    throw new Error('useSermonSearch must be used within SermonSearchProvider');
  }
  return context;
};

// Active filter count helper
export const getActiveFilterCount = (filters: SermonFilters): number => {
  let count = 0;
  if (filters.preacher_id) count++;
  if (filters.language) count++;
  if (filters.date_from) count++;
  if (filters.date_to) count++;
  if (filters.search_term) count++;
  if (filters.min_confidence < 0.7) count++;
  return count;
};
