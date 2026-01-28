/* File Grid - Advanced grid with live sorting preview */

import React from 'react';
import { useFileManager, FileType } from '../contexts/FileManagerContext';
import { SortableFileCard } from './SortableFileCard';
import styles from './FileGrid.module.css';

interface FileGridProps {
  files?: FileType[];
  loading?: boolean;
  showPreviewToggle?: boolean;
}

export const FileGrid: React.FC<FileGridProps> = ({ 
  files: propFiles,
  loading = false,
  showPreviewToggle = false
}) => {
  const { 
    files: contextFiles,
    previewMode,
    previewSortBy,
    setPreviewMode,
    previewSort,
    applyPreviewSort,
    selectedCount
  } = useFileManager();

  const displayFiles = propFiles || contextFiles;

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Loading files...</p>
      </div>
    );
  }

  if (displayFiles.length === 0) {
    return (
      <div className={styles.empty}>
        <span className={styles.emptyIcon}>📂</span>
        <h3>No files found</h3>
        <p>Upload some sermon files to get started</p>
      </div>
    );
  }

  return (
    <div className={styles.fileGrid}>
      {/* Sort Preview Bar */}
      {showPreviewToggle && (
        <div className={styles.previewBar}>
          <div className={styles.previewInfo}>
            {previewMode ? (
              <span className={styles.previewActive}>
                🔍 Previewing sort by: <strong>{previewSortBy}</strong>
              </span>
            ) : (
              <span>Drag files or select preview mode to see changes</span>
            )}
          </div>
          
          <div className={styles.previewActions}>
            {!previewMode && (
              <>
                <button 
                  className={styles.previewBtn}
                  onClick={() => previewSort('preacher')}
                >
                  Preview by Preacher
                </button>
                <button 
                  className={styles.previewBtn}
                  onClick={() => previewSort('location')}
                >
                  Preview by Location
                </button>
                <button 
                  className={styles.previewBtn}
                  onClick={() => previewSort('quality')}
                >
                  Preview by Quality
                </button>
              </>
            )}
            
            {previewMode && (
              <button 
                className={styles.applyBtn}
                onClick={applyPreviewSort}
              >
                ✅ Apply Smart Sort ({selectedCount} selected)
              </button>
            )}
            
            {previewMode && (
              <button 
                className={styles.cancelBtn}
                onClick={() => setPreviewMode(false)}
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      )}

      {/* Files Grid */}
      <div className={styles.grid}>
        {displayFiles.map((file) => (
          <SortableFileCard 
            key={file.id}
            file={file}
            previewMode={previewMode}
          />
        ))}
      </div>

      {/* Load More */}
      {displayFiles.length >= 500 && (
        <div className={styles.loadMore}>
          <button className={styles.loadMoreBtn}>
            Load More Files
          </button>
        </div>
      )}
    </div>
  );
};

export default FileGrid;
