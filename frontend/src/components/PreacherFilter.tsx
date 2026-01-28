/* Preacher Filter Component - Dropdown with avatars */

import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { useSermonSearch, SermonFilters } from '../contexts/SermonSearchContext';

interface Preacher {
  id: string;
  full_name: string;
  avatar_url: string | null;
}

interface PreacherFilterProps {
  className?: string;
}

const PreacherFilter: React.FC<PreacherFilterProps> = ({ className = '' }) => {
  const { filters, setFilter } = useSermonSearch();
  const [preachers, setPreachers] = useState<Preacher[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPreachers();
  }, []);

  const fetchPreachers = async () => {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('id, full_name, avatar_url')
        .eq('role', 'preacher')
        .order('full_name');
      
      if (error) {
        console.error('Error fetching preachers:', error);
      } else {
        setPreachers(data || []);
      }
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectedPreacher = preachers.find(p => p.id === filters.preacher_id);

  return (
    <div className={`filter-group preacher-filter ${className}`}>
      <label htmlFor="preacher-select">Preacher</label>
      
      <div className="filter-select">
        <select
          id="preacher-select"
          value={filters.preacher_id || ''}
          onChange={(e) => setFilter('preacher_id', e.target.value || null)}
          disabled={loading}
        >
          <option value="">All Preachers</option>
          {preachers.map((preacher) => (
            <option key={preacher.id} value={preacher.id}>
              {preacher.full_name}
            </option>
          ))}
        </select>
        
        {loading && (
          <span className="loading-indicator">...</span>
        )}
      </div>
      
      {/* Selected preacher avatar chip */}
      {filters.preacher_id && selectedPreacher && (
        <div className="selected-preacher-chip">
          {selectedPreacher.avatar_url ? (
            <img 
              src={selectedPreacher.avatar_url} 
              alt={selectedPreacher.full_name}
              className="preacher-avatar-small"
            />
          ) : (
            <div className="preacher-avatar-placeholder">
              {selectedPreacher.full_name.charAt(0)}
            </div>
          )}
          <span className="preacher-name">{selectedPreacher.full_name}</span>
          <button
            onClick={() => setFilter('preacher_id', null)}
            className="clear-filter-btn"
            aria-label="Clear preacher filter"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
};

export default PreacherFilter;
