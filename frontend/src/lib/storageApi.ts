// Storage Sync API Service
import type {
  MediaUrlsResult,
  StorageUsageStats,
  UploadResult,
  SyncResult,
  CleanupResult,
  StoragePolicyResult,
  ApiResponse,
} from './types';

const API_BASE = '/api/v1/storage';

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      // Let Content-Type be set automatically for FormData
      ...(!(options.body instanceof FormData) && {
        'Content-Type': 'application/json',
      }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

// ==================== Upload Media ====================

export async function uploadSermonMedia(
  sermonId: string,
  mediaType: 'audio' | 'video' | 'transcript' | 'thumbnail' | 'artwork',
  file: File
): Promise<ApiResponse<UploadResult>> {
  const formData = new FormData();
  formData.append('file', file);

  return fetchApi<ApiResponse<UploadResult>>(
    `/upload-sermon-media?sermon_id=${sermonId}&media_type=${mediaType}`,
    {
      method: 'POST',
      body: formData,
    }
  );
}

// ==================== Get Media URLs ====================

export async function getSermonMediaUrls(
  sermonId: string,
  mediaTypes?: Array<'audio' | 'video' | 'transcript' | 'thumbnail' | 'artwork'>
): Promise<ApiResponse<MediaUrlsResult>> {
  const params = new URLSearchParams();
  params.set('sermon_id', sermonId);
  if (mediaTypes) {
    params.set('media_types', mediaTypes.join(','));
  }

  return fetchApi<ApiResponse<MediaUrlsResult>>(
    `/sermon-media-urls/${sermonId}?${params.toString()}`
  );
}

// ==================== Sync Metadata ====================

export async function syncSermonMetadata(
  sermonId: string,
  metadata: Record<string, unknown>
): Promise<ApiResponse<SyncResult>> {
  return fetchApi<ApiResponse<SyncResult>>(`/sync-sermon-metadata/${sermonId}`, {
    method: 'POST',
    body: JSON.stringify(metadata),
  });
}

export async function syncTaskAssignment(
  taskId: string,
  assignment: Record<string, unknown>
): Promise<ApiResponse<SyncResult>> {
  return fetchApi<ApiResponse<SyncResult>>(`/sync-task-assignment/${taskId}`, {
    method: 'POST',
    body: JSON.stringify(assignment),
  });
}

// ==================== Cleanup ====================

export async function cleanupSermonFiles(
  sermonId: string
): Promise<ApiResponse<CleanupResult>> {
  return fetchApi<ApiResponse<CleanupResult>>(
    `/cleanup-sermon-files/${sermonId}`,
    { method: 'DELETE' }
  );
}

// ==================== Storage Stats ====================

export async function getStorageStats(): Promise<ApiResponse<StorageUsageStats>> {
  return fetchApi<ApiResponse<StorageUsageStats>>('/storage-stats');
}

// ==================== RLS Policies ====================

export async function createStoragePolicies(): Promise<ApiResponse<StoragePolicyResult>> {
  return fetchApi<ApiResponse<StoragePolicyResult>>('/create-storage-rls-policies', {
    method: 'POST',
  });
}

// ==================== Utility Functions ====================

export function getMediaTypeLabel(
  type: 'audio' | 'video' | 'transcript' | 'thumbnail' | 'artwork'
): string {
  const labels: Record<string, string> = {
    audio: 'Audio',
    video: 'Video',
    transcript: 'Transcript',
    thumbnail: 'Thumbnail',
    artwork: 'Artwork',
  };
  return labels[type] || type;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function getBucketIcon(bucket: string): string {
  const icons: Record<string, string> = {
    'sermon-audio': '🎵',
    'sermon-video': '🎬',
    'sermon-transcripts': '📄',
    'sermon-thumbnails': '🖼️',
    'sermon-artwork': '🎨',
  };
  return icons[bucket] || '📁';
}
