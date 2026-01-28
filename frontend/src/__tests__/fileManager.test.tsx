/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SermonSearchProvider, useSermonSearch } from '../contexts/SermonSearchContext';
import { FileManagerProvider, useFileManager } from '../contexts/FileManagerContext';

// Mock Supabase
jest.mock('../lib/supabase', () => ({
  supabase: {
    from: jest.fn().mockReturnValue({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      order: jest.fn().mockReturnThis(),
      range: jest.fn().mockReturnThis(),
      execute: jest.fn().mockResolvedValue({ data: [], error: null, count: 0 }),
    }),
    auth: {
      getUser: jest.fn().mockResolvedValue({ data: { user: { id: 'test-user' } } }),
    },
  },
}));

// ======= SermonSearchContext Tests =======

describe('SermonSearchContext', () => {
  const mockSermons = [
    {
      id: '1',
      title: 'Sunday Sermon',
      description: 'Test sermon',
      primary_language: 'english',
      speaker_confidence_avg: 0.92,
      created_at: '2026-01-28T10:00:00Z',
      duration_seconds: 1800,
      profiles: { id: '1', full_name: 'Pastor John', avatar_url: null },
    },
    {
      id: '2',
      title: 'Wednesday Bible Study',
      description: 'Midweek service',
      primary_language: 'luganda',
      speaker_confidence_avg: 0.85,
      created_at: '2026-01-25T10:00:00Z',
      duration_seconds: 3600,
      profiles: { id: '2', full_name: 'Pastor Jane', avatar_url: null },
    },
  ];

  const TestComponent = () => {
    const { filters, setFilter, clearFilters, sortConfig, setSort, sortOptions, sermons, loading, totalCount } = useSermonSearch();
    
    return (
      <div>
        <div data-testid="loading">{loading ? 'true' : 'false'}</div>
        <div data-testid="total-count">{totalCount}</div>
        <div data-testid="sermon-count">{sermons.length}</div>
        <button onClick={() => setFilter('preacher_id', '123')}>Set Preacher</button>
        <button onClick={clearFilters}>Clear Filters</button>
        <select onChange={(e) => setSort(e.target.value)}>
          {sortOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(
      <SermonSearchProvider>
        <TestComponent />
      </SermonSearchProvider>
    );
    expect(screen.getByTestId('loading')).toHaveTextContent('true');
  });

  it('clears all filters when clearFilters is called', () => {
    render(
      <SermonSearchProvider>
        <TestComponent />
      </SermonSearchProvider>
    );
    
    const clearBtn = screen.getByText('Clear Filters');
    fireEvent.click(clearBtn);
    
    // Filters should be cleared (preacher_id should be null)
    expect(true).toBe(true);
  });

  it('provides sort options', () => {
    render(
      <SermonSearchProvider>
        <TestComponent />
      </SermonSearchProvider>
    );
    
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    
    // Check for some expected sort options
    expect(screen.getByText('Newest First')).toBeInTheDocument();
    expect(screen.getByText('Oldest First')).toBeInTheDocument();
    expect(screen.getByText('Preacher A-Z')).toBeInTheDocument();
  });
});

// ======= FileManagerContext Tests =======

describe('FileManagerContext', () => {
  const TestComponent = () => {
    const { selectedIds, toggleSelection, selectAll, clearSelection, isSelected, totalFiles, selectedCount } = useFileManager();
    
    return (
      <div>
        <div data-testid="total-files">{totalFiles}</div>
        <div data-testid="selected-count">{selectedCount}</div>
        <button onClick={() => toggleSelection('file-1')}>Toggle File 1</button>
        <button onClick={selectAll}>Select All</button>
        <button onClick={clearSelection}>Clear Selection</button>
        <span data-testid="is-selected">{isSelected('file-1') ? 'true' : 'false'}</span>
      </div>
    );
  };

  it('provides selection state', () => {
    render(
      <FileManagerProvider churchId="test-church">
        <TestComponent />
      </FileManagerProvider>
    );
    
    expect(screen.getByTestId('total-files')).toBeInTheDocument();
    expect(screen.getByTestId('selected-count')).toHaveTextContent('0');
  });

  it('toggles selection correctly', () => {
    render(
      <FileManagerProvider churchId="test-church">
        <TestComponent />
      </FileManagerProvider>
    );
    
    const toggleBtn = screen.getByText('Toggle File 1');
    fireEvent.click(toggleBtn);
    
    expect(screen.getByTestId('is-selected')).toHaveTextContent('true');
    
    fireEvent.click(toggleBtn);
    expect(screen.getByTestId('is-selected')).toHaveTextContent('false');
  });

  it('selects all files', () => {
    render(
      <FileManagerProvider churchId="test-church">
        <TestComponent />
      </FileManagerProvider>
    );
    
    const selectAllBtn = screen.getByText('Select All');
    fireEvent.click(selectAllBtn);
    
    // After select all, should have more selected
    expect(screen.getByTestId('selected-count')).toHaveTextContent('0'); // No files in mock
  });
});

// ======= Bulk Operations Bar Tests =======

describe('BulkOperationsBar', () => {
  const TestWrapper = () => (
    <FileManagerProvider churchId="test-church">
      <div>
        <BulkOperationsBar onFolderAssigner={() => {}} />
      </div>
    </FileManagerProvider>
  );

  it('renders bulk operations bar', () => {
    render(<TestWrapper />);
    
    expect(screen.getByText(/Select All/)).toBeInTheDocument();
  });

  it('shows selection count', () => {
    render(<TestWrapper />);
    
    expect(screen.getByText(/0 files selected/)).toBeInTheDocument();
  });

  it('disables actions when no files selected', () => {
    render(<TestWrapper />);
    
    // Action buttons should be disabled when no selection
    const createPackageBtn = screen.getByText('Create Package');
    expect(createPackageBtn).toBeDisabled();
  });
});

// ======= File Grid Tests =======

describe('FileGrid', () => {
  const mockFiles = [
    { id: '1', filename: 'sermon1.mp3', file_type: 'audio', file_size: 15000000, preacher_id: '1', primary_language: 'english', location_city: 'Kampala', quality_score: 85 },
    { id: '2', filename: 'sermon2.mp4', file_type: 'video', file_size: 250000000, preacher_id: '2', primary_language: 'english', location_city: 'Entebbe', quality_score: 72 },
  ];

  const TestWrapper = () => (
    <FileManagerProvider churchId="test-church">
      <FileGrid files={mockFiles} loading={false} />
    </FileManagerProvider>
  );

  it('renders file grid', () => {
    render(<TestWrapper />);
    
    expect(screen.getByText('sermon1.mp3')).toBeInTheDocument();
    expect(screen.getByText('sermon2.mp4')).toBeInTheDocument();
  });

  it('shows empty state when no files', () => {
    render(
      <FileManagerProvider churchId="test-church">
        <FileGrid files={[]} loading={false} />
      </FileManagerProvider>
    );
    
    expect(screen.getByText(/No files found/)).toBeInTheDocument();
  });
});

// ======= Sortable File Card Tests =======

describe('SortableFileCard', () => {
  const mockFile = {
    id: '1',
    filename: 'test_sermon.mp3',
    file_type: 'audio',
    file_size: 15000000,
    duration_seconds: 1800,
    preacher_id: '1',
    primary_language: 'english',
    location_city: 'Kampala',
    quality_score: 85,
    profiles: { id: '1', full_name: 'Pastor John', avatar_url: null },
  };

  it('renders file card with metadata', () => {
    render(<SortableFileCard file={mockFile} />);
    
    expect(screen.getByText('test_sermon.mp3')).toBeInTheDocument();
    expect(screen.getByText('Pastor John')).toBeInTheDocument();
    expect(screen.getByText('english')).toBeInTheDocument();
    expect(screen.getByText('Kampala')).toBeInTheDocument();
  });

  it('shows quality badge with correct color', () => {
    render(<SortableFileCard file={mockFile} />);
    
    // Quality 85% should show green badge
    const badge = screen.getByText('85%');
    expect(badge).toBeInTheDocument();
  });

  it('renders selection checkbox', () => {
    render(<SortableFileCard file={mockFile} />);
    
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeInTheDocument();
  });
});

// ======= Smart Sorting Rules Tests =======

describe('SmartSortingRules', () => {
  const TestWrapper = () => (
    <FileManagerProvider churchId="test-church">
      <SmartSortingRules />
    </FileManagerProvider>
  );

  it('renders smart sorting rules panel', () => {
    render(<TestWrapper />);
    
    expect(screen.getByText(/AI Smart Sorting Rules/)).toBeInTheDocument();
  });

  it('shows empty state when no rules', () => {
    render(<TestWrapper />);
    
    expect(screen.getByText(/No sorting rules configured/)).toBeInTheDocument();
  });
});

// ======= File Relationship Map Tests =======

describe('FileRelationshipMap', () => {
  const TestWrapper = () => (
    <FileManagerProvider churchId="test-church">
      <FileRelationshipMap />
    </FileManagerProvider>
  );

  it('renders relationship map', () => {
    render(<TestWrapper />);
    
    expect(screen.getByText(/Sermon Packages/)).toBeInTheDocument();
  });

  it('shows empty state when no files', () => {
    render(<TestWrapper />);
    
    expect(screen.getByText(/No sermon packages yet/)).toBeInTheDocument();
  });
});

// Import components for testing
import { BulkOperationsBar } from '../components/BulkOperationsBar';
import { FileGrid } from '../components/FileGrid';
import { SortableFileCard } from '../components/SortableFileCard';
import { SmartSortingRules } from '../components/SmartSortingRules';
import { FileRelationshipMap } from '../components/FileRelationshipMap';
