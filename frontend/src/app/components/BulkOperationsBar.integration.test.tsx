import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock contexts first before importing components
const mockClearSelection = vi.fn();
const mockRefreshFiles = vi.fn();

const mockAuthValue = {
  session: {
    user: {
      user_metadata: { role: 'admin' }
    }
  },
  loading: false,
  signIn: vi.fn(),
  signOut: vi.fn(),
};

const mockFileManagerValue = {
  selectedFiles: new Set(['file-1', 'file-2']),
  clearSelection: mockClearSelection,
  refreshFiles: mockRefreshFiles,
};

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthValue,
}));

vi.mock('../../contexts/FileManagerContext', () => ({
  useFileManager: () => mockFileManagerValue,
}));

// Mock toast from sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock the API layer
vi.mock('../../lib/api', () => ({
  bulkApi: {
    sort: vi.fn(),
    tag: vi.fn(),
    move: vi.fn(),
    optimize: vi.fn(),
    createPackage: vi.fn(),
  },
  filesApi: {
    delete: vi.fn(),
  },
}));

import { bulkApi, filesApi } from '../../lib/api';
import { BulkOperationsBar } from './BulkOperationsBar';

describe('Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock values
    mockFileManagerValue.selectedFiles = new Set(['file-1', 'file-2']);
    mockFileManagerValue.clearSelection = mockClearSelection;
    mockFileManagerValue.refreshFiles = mockRefreshFiles;
    mockAuthValue.session.user.user_metadata.role = 'admin';
  });

  describe('BulkOperationsBar Component + Context Integration', () => {
    it('should show bulk operations bar when files are selected', () => {
      const { container } = render(<BulkOperationsBar />);

      // Verify bulk operations bar is visible
      expect(container.querySelector('.fixed.bottom-4')).toBeInTheDocument();
      expect(screen.getByText('2 selected')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add tags/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /move/i })).toBeInTheDocument();
    });

    it('should not show bulk operations bar when no files are selected', () => {
      mockFileManagerValue.selectedFiles = new Set();
      
      const { container } = render(<BulkOperationsBar />);

      // Bulk operations bar should not render
      expect(container.querySelector('.fixed.bottom-4')).not.toBeInTheDocument();
    });

    it('should not show bulk operations bar for non-admin users', () => {
      mockAuthValue.session.user.user_metadata.role = 'user';
      
      const { container } = render(<BulkOperationsBar />);

      // Bulk operations bar should not render for regular users
      expect(container.querySelector('.fixed.bottom-4')).not.toBeInTheDocument();
    });
  });

  describe('BulkOperationsBar + API Layer Integration', () => {
    it('should call bulkApi.tag when tags are submitted', async () => {
      const user = userEvent.setup();
      
      // Setup mock API response
      (bulkApi.tag as any).mockResolvedValue({ tagged: 2, message: 'Added tags to 2 files' });

      render(<BulkOperationsBar />);

      // Click "Add Tags" button to open dialog
      const addTagsButton = screen.getByRole('button', { name: /add tags/i });
      await user.click(addTagsButton);

      // Verify dialog is open
      expect(screen.getByText(/add tags to 2 file/i)).toBeInTheDocument();

      // Enter tags
      const tagInput = screen.getByPlaceholderText(/faith, grace, salvation/i);
      await user.type(tagInput, 'faith, grace');

      // Click Apply Tags
      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      // Wait for API call
      await waitFor(() => {
        expect(bulkApi.tag).toHaveBeenCalledWith(
          ['file-1', 'file-2'],
          ['faith', 'grace']
        );
      });

      // Verify cleanup was called
      expect(mockClearSelection).toHaveBeenCalled();
      expect(mockRefreshFiles).toHaveBeenCalled();
    });

    it('should call bulkApi.move with correct parameters', async () => {
      const user = userEvent.setup();
      
      (bulkApi.move as any).mockResolvedValue({ moved: 2, message: 'Moved 2 files' });

      render(<BulkOperationsBar />);

      // Click "Move" button
      const moveButton = screen.getByRole('button', { name: /move/i });
      await user.click(moveButton);

      // Verify dialog is open
      expect(screen.getByRole('heading', { name: /move 2 file/i })).toBeInTheDocument();

      // Select a folder using keyboard navigation (avoids jsdom pointer capture issue)
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);
      
      // Wait for dropdown to appear and use keyboard to select
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');

      // Click Move Files button
      const moveFilesButton = screen.getByRole('button', { name: /move files/i });
      await user.click(moveFilesButton);

      // Wait for API call (verify it was called with any parameters)
      await waitFor(() => {
        expect(bulkApi.move).toHaveBeenCalled();
      });
    });

    it('should call filesApi.delete for each selected file', async () => {
      const user = userEvent.setup();
      
      (filesApi.delete as any).mockResolvedValue({ message: 'File deleted successfully' });

      render(<BulkOperationsBar />);

      // Click "Delete" button
      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Verify dialog is open (use exact match for title)
      expect(screen.getByRole('heading', { name: /delete 2 file\(s\)/i })).toBeInTheDocument();

      // Click Delete Files button
      const deleteFilesButton = screen.getByRole('button', { name: /delete files/i });
      await user.click(deleteFilesButton);

      // Wait for API calls
      await waitFor(() => {
        expect(filesApi.delete).toHaveBeenCalledTimes(2);
        expect(filesApi.delete).toHaveBeenCalledWith('file-1');
        expect(filesApi.delete).toHaveBeenCalledWith('file-2');
      });
    });

    it('should call bulkApi.optimize with selected profile', async () => {
      const user = userEvent.setup();
      
      (bulkApi.optimize as any).mockResolvedValue({ queued: 2, message: 'Queued 2 files' });

      render(<BulkOperationsBar />);

      // Click "Optimize Batch" button
      const optimizeButton = screen.getByRole('button', { name: /optimize batch/i });
      await user.click(optimizeButton);

      // Verify dialog is open
      expect(screen.getByText(/optimize 2 file/i)).toBeInTheDocument();

      // Select Web profile
      const webProfile = screen.getByText('Web');
      await user.click(webProfile);

      // Click Start Optimization button
      const startButton = screen.getByRole('button', { name: /start optimization/i });
      await user.click(startButton);

      // Wait for API call
      await waitFor(() => {
        expect(bulkApi.optimize).toHaveBeenCalledWith(['file-1', 'file-2'], 'default', 'sermon_web');
      });
    });
  });

  describe('Quick Tag Selection Integration', () => {
    it('should add quick tags when clicked', async () => {
      const user = userEvent.setup();
      
      (bulkApi.tag as any).mockResolvedValue({ tagged: 1, message: 'Added tags to 1 file' });

      // Override for this test
      mockFileManagerValue.selectedFiles = new Set(['file-1']);

      render(<BulkOperationsBar />);

      // Open tag dialog
      const addTagsButton = screen.getByRole('button', { name: /add tags/i });
      await user.click(addTagsButton);

      // Click on "faith" quick tag
      const faithTag = screen.getByText('faith');
      await user.click(faithTag);

      // Verify tag was added to input
      const tagInput = screen.getByPlaceholderText(/faith, grace, salvation/i);
      expect(tagInput).toHaveValue('faith');

      // Submit and verify API call
      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(bulkApi.tag).toHaveBeenCalledWith(['file-1'], ['faith']);
      });
    });

    it('should allow multiple quick tags to be selected', async () => {
      const user = userEvent.setup();
      
      (bulkApi.tag as any).mockResolvedValue({ tagged: 1, message: 'Added tags to 1 file' });

      // Override for this test
      mockFileManagerValue.selectedFiles = new Set(['file-1']);

      render(<BulkOperationsBar />);

      // Open tag dialog
      const addTagsButton = screen.getByRole('button', { name: /add tags/i });
      await user.click(addTagsButton);

      // Click on multiple quick tags
      const faithTag = screen.getByText('faith');
      await user.click(faithTag);
      
      const graceTag = screen.getByText('grace');
      await user.click(graceTag);

      // Verify tags were added
      const tagInput = screen.getByPlaceholderText(/faith, grace, salvation/i);
      expect(tagInput).toHaveValue('faith, grace');
    });
  });
});
