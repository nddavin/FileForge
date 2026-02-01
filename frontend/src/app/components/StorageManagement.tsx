// Storage Management Component
import React, { useState, useEffect } from 'react';
import {
  getStorageStats,
  uploadSermonMedia,
  cleanupSermonFiles,
  createStoragePolicies,
  getMediaTypeLabel,
  formatFileSize,
  getBucketIcon,
} from '../../lib/storageApi';
import { StorageUsageStats, UploadResult } from '../../lib/types';

const StorageManagement: React.FC = () => {
  const [stats, setStats] = useState<StorageUsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedSermon, setSelectedSermon] = useState<string>('');
  const [mediaType, setMediaType] = useState<
    'audio' | 'video' | 'transcript' | 'thumbnail' | 'artwork'
  >('video');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  useEffect(() => {
    loadStorageStats();
  }, []);

  const loadStorageStats = async () => {
    setLoading(true);
    try {
      const result = await getStorageStats();
      if (result.success && result.data) {
        setStats(result.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedSermon || !selectedFile) return;

    setUploading(true);
    setUploadResult(null);
    try {
      const result = await uploadSermonMedia(
        selectedSermon,
        mediaType,
        selectedFile
      );
      if (result.success && result.data) {
        setUploadResult(result.data);
        loadStorageStats();
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleCleanup = async () => {
    if (!selectedSermon) return;

    if (!confirm('Are you sure you want to delete all files for this sermon?')) {
      return;
    }

    try {
      const result = await cleanupSermonFiles(selectedSermon);
      if (result.success) {
        alert(`Cleaned up ${result.data?.deleted_files || 0} files`);
        loadStorageStats();
      }
    } catch (error) {
      console.error('Cleanup failed:', error);
    }
  };

  const handleCreatePolicies = async () => {
    try {
      const result = await createStoragePolicies();
      if (result.success && result.data?.policies) {
        // Show policies in a modal or download them
        const blob = new Blob([result.data.policies], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'storage_policies.sql';
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to create policies:', error);
    }
  };

  const getTotalStorage = (): { fileCount: number; totalSize: number } => {
    if (!stats) return { fileCount: 0, totalSize: 0 };
    return Object.values(stats).reduce(
      (acc, bucket) => ({
        fileCount: acc.fileCount + bucket.file_count,
        totalSize: acc.totalSize + bucket.total_size,
      }),
      { fileCount: 0, totalSize: 0 }
    );
  };

  const totals = getTotalStorage();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Storage Management</h1>
        <button
          onClick={handleCreatePolicies}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
        >
          Export RLS Policies
        </button>
      </div>

      {/* Storage Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">Total Files</div>
          <div className="text-3xl font-bold text-gray-900">
            {totals.fileCount.toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">Total Size</div>
          <div className="text-3xl font-bold text-gray-900">
            {formatFileSize(totals.totalSize)}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">Public Buckets</div>
          <div className="text-3xl font-bold text-green-600">
            {stats
              ? Object.values(stats).filter((b) => b.public).length
              : 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">Private Buckets</div>
          <div className="text-3xl font-bold text-blue-600">
            {stats
              ? Object.values(stats).filter((b) => !b.public).length
              : 0}
          </div>
        </div>
      </div>

      {/* Storage Buckets */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Storage Buckets</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {stats &&
            Object.entries(stats).map(([bucket, data]) => (
              <div
                key={bucket}
                className="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl">{getBucketIcon(bucket)}</span>
                  <div>
                    <div className="font-medium">{bucket}</div>
                    <div className="text-sm text-gray-500">
                      {data.public ? 'Public Access' : 'Private (RLS Protected)'}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-8">
                  <div className="text-right">
                    <div className="font-medium">{data.file_count.toLocaleString()} files</div>
                    <div className="text-sm text-gray-500">
                      {formatFileSize(data.total_size)}
                    </div>
                  </div>
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      data.public
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {data.public ? 'Public' : 'Private'}
                  </span>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Upload Media</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sermon ID
            </label>
            <input
              type="text"
              value={selectedSermon}
              onChange={(e) => setSelectedSermon(e.target.value)}
              placeholder="Enter sermon ID"
              className="w-full rounded-md border-gray-300 border p-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Media Type
            </label>
            <select
              value={mediaType}
              onChange={(e) =>
                setMediaType(
                  e.target.value as
                    | 'audio'
                    | 'video'
                    | 'transcript'
                    | 'thumbnail'
                    | 'artwork'
                )
              }
              className="w-full rounded-md border-gray-300 border p-2"
            >
              <option value="audio">Audio</option>
              <option value="video">Video</option>
              <option value="transcript">Transcript</option>
              <option value="thumbnail">Thumbnail</option>
              <option value="artwork">Artwork</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              File
            </label>
            <input
              type="file"
              onChange={handleFileSelect}
              className="w-full rounded-md border-gray-300 border p-2"
            />
          </div>
        </div>
        <div className="flex gap-4">
          <button
            onClick={handleUpload}
            disabled={!selectedSermon || !selectedFile || uploading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
          <button
            onClick={handleCleanup}
            disabled={!selectedSermon}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            Cleanup Sermon Files
          </button>
        </div>

        {/* Upload Result */}
        {uploadResult && (
          <div
            className={`mt-4 p-4 rounded-lg ${
              uploadResult.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            {uploadResult.success ? (
              <div>
                <div className="font-medium text-green-800">Upload Successful!</div>
                <div className="text-sm text-green-700 mt-1">
                  <p>File: {uploadResult.filename}</p>
                  <p>Size: {formatFileSize(uploadResult.size)}</p>
                  <p>Type: {uploadResult.mime_type}</p>
                  {uploadResult.public_url && (
                    <a
                      href={uploadResult.public_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      View File
                    </a>
                  )}
                </div>
              </div>
            ) : (
              <div className="font-medium text-red-800">Upload Failed</div>
            )}
          </div>
        )}
      </div>

      {/* File Size Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Storage Distribution</h2>
        {stats && (
          <div className="space-y-3">
            {Object.entries(stats)
              .sort((a, b) => b[1].total_size - a[1].total_size)
              .map(([bucket, data]) => {
                const percentage = (data.total_size / totals.totalSize) * 100 || 0;
                return (
                  <div key={bucket}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>
                        {getBucketIcon(bucket)} {bucket}
                      </span>
                      <span>{formatFileSize(data.total_size)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-blue-600 h-3 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
};

export default StorageManagement;
