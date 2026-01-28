/* Sortable File Card - Draggable file with metadata and preview */

import React from 'react';
import { useFileManager, FileType, getQualityColor } from '../contexts/FileManagerContext';
import styles from './SortableFileCard.module.css';

interface SortableFileCardProps {
  file: FileType;
  previewMode?: boolean;
}

export const SortableFileCard: React.FC<SortableFileCardProps> = ({ 
  file, 
  previewMode = false 
}) => {
  const { isSelected, toggleSelection } = useFileManager();

  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('file-id', file.id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const getFileIcon = () => {
    const type = file.file_type?.toLowerCase();
    if (type?.includes('audio') || type?.includes('mp3') || type?.includes('wav')) {
      return '🎵';
    }
    if (type?.includes('video') || type?.includes('mp4') || type?.includes('mov')) {
      return '🎬';
    }
    if (type?.includes('image') || type?.includes('jpg') || type?.includes('png')) {
      return '🖼️';
    }
    if (type?.includes('text') || type?.includes('pdf')) {
      return '📄';
    }
    return '📁';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div
      className={`
        ${styles.fileCard}
        ${isSelected(file.id) ? styles.selected : ''}
        ${previewMode ? styles.preview : ''}
      `}
      draggable={!previewMode}
      onDragStart={handleDragStart}
    >
      {/* File Preview */}
      <div className={styles.filePreview}>
        <span className={styles.fileIcon}>{getFileIcon()}</span>
        {file.quality_score !== null && (
          <span className={styles.qualityBadge} style={{ background: getQualityColor(file.quality_score) }}>
            {file.quality_score}%
          </span>
        )}
      </div>

      {/* File Info */}
      <div className={styles.fileInfo}>
        <h4 className={styles.fileName} title={file.filename}>
          {file.filename}
        </h4>
        
        <div className={styles.fileMeta}>
          <span>{formatFileSize(file.file_size)}</span>
          <span>•</span>
          <span>{formatDuration(file.duration_seconds || null)}</span>
        </div>
      </div>

      {/* Smart Metadata Tags */}
      <div className={styles.fileTags}>
        {file.profiles && (
          <span className={`${styles.tag} ${styles.preacher}`}>
            {file.profiles.avatar_url ? (
              <img src={file.profiles.avatar_url} alt="" className={styles.avatar} />
            ) : (
              <span className={styles.avatarPlaceholder}>
                {file.profiles.full_name?.charAt(0) || '?'}
              </span>
            )}
            {file.profiles.full_name || 'Unknown'}
          </span>
        )}
        
        {file.primary_language && (
          <span className={`${styles.tag} ${styles.language}`}>
            {file.primary_language}
          </span>
        )}
        
        {file.location_city && (
          <span className={`${styles.tag} ${styles.location}`}>
            📍 {file.location_city}
          </span>
        )}
      </div>

      {/* Sort Preview Folder */}
      {previewMode && (
        <div className={styles.previewFolder}>
          <span className={styles.folderIcon}>📁</span>
          <span className={styles.folderName}>
            {file.predicted_folder || 'unsorted'}
          </span>
        </div>
      )}

      {/* Selection Checkbox */}
      <div className={styles.selection}>
        <input
          type="checkbox"
          checked={isSelected(file.id)}
          onChange={() => toggleSelection(file.id)}
          className={styles.checkbox}
        />
      </div>

      {/* Package Indicator */}
      {file.sermon_package_id && (
        <div className={styles.packageIndicator}>
          <span title="Part of sermon package">📦</span>
        </div>
      )}
    </div>
  );
};

export default SortableFileCard;
