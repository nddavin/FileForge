import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { bulkApi, filesApi, rulesApi, sermonsApi } from './api';

describe('API Module', () => {
  // Mock fetch globally
  let fetchMock: any;

  beforeEach(() => {
    fetchMock = vi.fn();
    global.fetch = fetchMock;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('bulkApi', () => {
    it('should call bulk-sort endpoint with correct parameters', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sorted: 5, rules_applied: 2 }),
      });

      const fileIds = ['file-1', 'file-2', 'file-3'];
      const result = await bulkApi.sort(fileIds, undefined, 'preacher', 'church-1');

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/sort'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            file_ids: fileIds,
            rules: undefined,
            sort_by: 'preacher',
            church_id: 'church-1',
          }),
        })
      );
      expect(result).toEqual({ sorted: 5, rules_applied: 2 });
    });

    it('should call bulk-tag endpoint with correct parameters', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tagged: 3, message: 'Added tags to 3 files' }),
      });

      const fileIds = ['file-1', 'file-2'];
      const tags = ['faith', 'grace', 'sermon'];
      const result = await bulkApi.tag(fileIds, tags);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/tag'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            file_ids: fileIds,
            tags,
          }),
        })
      );
      expect(result).toEqual({ tagged: 3, message: 'Added tags to 3 files' });
    });

    it('should call bulk-move endpoint with correct parameters', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ moved: 2, message: 'Moved 2 files to folder' }),
      });

      const fileIds = ['file-1', 'file-2'];
      const folderId = 'folder-1';
      const result = await bulkApi.move(fileIds, folderId);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/move'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            file_ids: fileIds,
            folder_id: folderId,
          }),
        })
      );
      expect(result).toEqual({ moved: 2, message: 'Moved 2 files to folder' });
    });

    it('should call bulk-optimize endpoint with correct parameters', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ queued: 1, message: 'Queued 1 files for optimization' }),
      });

      const fileIds = ['file-1'];
      const churchId = 'church-1';
      const profile = 'sermon_web';
      const result = await bulkApi.optimize(fileIds, churchId, profile);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/optimize'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            file_ids: fileIds,
            church_id: churchId,
            profile,
          }),
        })
      );
      expect(result).toEqual({ queued: 1, message: 'Queued 1 files for optimization' });
    });

    it('should call bulk-package endpoint with correct parameters', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          package_id: 'pkg-123',
          package_name: 'Sermon Package 2024-01-15',
          file_count: 5,
        }),
      });

      const fileIds = ['file-1', 'file-2', 'file-3', 'file-4', 'file-5'];
      const churchId = 'church-1';
      const name = 'My Package';
      const result = await bulkApi.createPackage(fileIds, churchId, name);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/package'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            file_ids: fileIds,
            church_id: churchId,
            name,
          }),
        })
      );
      expect(result.package_id).toBe('pkg-123');
      expect(result.file_count).toBe(5);
    });
  });

  describe('rulesApi', () => {
    it('should fetch sorting rules', async () => {
      const mockRules = [
        { id: '1', name: 'Rule 1', conditions: [], target_folder: '/sermons/2024' },
        { id: '2', name: 'Rule 2', conditions: [], target_folder: '/sermons/2023' },
      ];
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockRules),
      });

      const result = await rulesApi.list();

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/rules'),
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual(mockRules);
    });

    it('should create a new sorting rule', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'Rule created successfully', rule_id: 'new-rule-1' }),
      });

      const newRule = {
        name: 'New Rule',
        condition_type: 'file_type',
        condition_value: 'video',
        action_type: 'move',
        action_value: '/sermons/videos',
      };
      const result = await rulesApi.create(newRule);

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/rules'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newRule),
        })
      );
      expect(result.rule_id).toBe('new-rule-1');
    });

    it('should delete a sorting rule', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'Rule deleted successfully' }),
      });

      await rulesApi.delete('rule-1');

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/bulk/rules/rule-1'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('filesApi', () => {
    it('should create a new file record', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'new-file-1', message: 'File created successfully' }),
      });

      const fileData = {
        name: 'sermon.mp3',
        path: '/uploads/sermon.mp3',
        size: 1024000,
        content_type: 'audio/mpeg',
        tags: ['sermon', 'faith'],
      };
      const result = await filesApi.create(fileData);

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/files'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(fileData),
        })
      );
      expect(result.id).toBe('new-file-1');
    });

    it('should update a file record', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'File updated successfully' }),
      });

      const fileData = { tags: ['updated', 'tags'] };
      await filesApi.update('file-1', fileData);

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/files/file-1'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(fileData),
        })
      );
    });

    it('should delete a file record', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'File deleted successfully' }),
      });

      await filesApi.delete('file-1');

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/files/file-1'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('sermonsApi', () => {
    it('should fetch sermon stats', async () => {
      const mockStats = {
        total_sermons: 150,
        total_preachers: 12,
        total_duration_hours: 450,
      };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStats),
      });

      const result = await sermonsApi.getStats();

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/sermons/stats'),
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual(mockStats);
    });

    it('should fetch sermon metadata', async () => {
      const mockMetadata = {
        file_id: 'file-1',
        preacher: 'John Doe',
        title: 'Faith and Grace',
        date: '2024-01-14',
        series: 'Foundations',
      };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMetadata),
      });

      const result = await sermonsApi.getMetadata('file-1');

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/sermons/file-1/metadata'),
        expect.objectContaining({ method: 'GET' })
      );
      expect(result.preacher).toBe('John Doe');
    });

    it('should update sermon metadata', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'Metadata updated successfully' }),
      });

      const metadata = { title: 'Updated Title', series: 'New Series' };
      await sermonsApi.updateMetadata('file-1', metadata);

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/sermons/file-1/metadata'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(metadata),
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('should throw error on failed request', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      });

      await expect(bulkApi.sort(['file-1'])).rejects.toThrow('Unauthorized');
    });

    it('should throw generic error on non-JSON response', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.reject(new Error('Failed to parse')),
      });

      await expect(bulkApi.sort(['file-1'])).rejects.toThrow('Request failed');
    });
  });
});
