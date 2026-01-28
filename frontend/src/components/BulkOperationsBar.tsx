/* Bulk Operations Bar - File selection and bulk actions */

import React from 'react';
import { useFileManager } from '../contexts/FileManagerContext';
import styles from './BulkOperationsBar.module.css';

interface BulkOperationsBarProps {
  onFolderAssigner: () => void;
}

export const BulkOperationsBar: React.FC<BulkOperationsBarProps> = ({ 
  onFolderAssigner 
}) => {
  const { 
    selectedCount, 
    totalFiles,
    selectAll, 
    clearSelection, 
    bulkPackage,
    bulkOptimize,
    bulkAiSort,
    selectedIds
  } = useFileManager();

  const handlePackage = async () => {
    if (selectedCount < 2) {
      alert('Select at least 2 files to create a sermon package');
      return;
    }
    await bulkPackage();
  };

  const handleAiSort = async () => {
    await bulkAiSort();
  };

  return (
    <div className={styles.bulkBar}>
      {/* Selection Info */}
      <div className={styles.selectionInfo}>
        <button 
          className={styles.selectBtn}
          onClick={() => {
            if (selectedCount === totalFiles) {
              clearSelection();
            } else {
              selectAll();
            }
          }}
        >
          {selectedCount === totalFiles ? '☑️ Clear All' : `☑️ Select All (${totalFiles})`}
        </button>
        <span className={styles.count}>
          {selectedCount} file{selectedCount !== 1 ? 's' : ''} selected
        </span>
      </div>

      {/* Bulk Actions */}
      <div className={styles.bulkActions}>
        <button 
          className={styles.actionBtn}
          onClick={handlePackage}
          disabled={selectedCount < 2}
          title="Create sermon package from selected files"
        >
          <span className={styles.icon}>✂️</span>
          <span className={styles.label}>Create Package</span>
        </button>

        <button 
          className={styles.actionBtn}
          onClick={bulkOptimize}
          disabled={selectedCount === 0}
          title="Optimize quality for selected files"
        >
          <span className={styles.icon}>🎥</span>
          <span className={styles.label}>Optimize Quality</span>
        </button>

        <button 
          className={styles.actionBtn}
          onClick={handleAiSort}
          disabled={selectedCount === 0}
          title="Apply AI smart sorting to selected files"
        >
          <span className={styles.icon}>🔖</span>
          <span className={styles.label}>AI Sort & Tag</span>
        </button>

        <button 
          className={styles.actionBtn}
          onClick={onFolderAssigner}
          disabled={selectedCount === 0}
          title="Move selected files to a folder"
        >
          <span className={styles.icon}>📁</span>
          <span className={styles.label}>Assign Folder</span>
        </button>
      </div>

      {/* Quick Stats */}
      {selectedCount > 0 && (
        <div className={styles.quickStats}>
          <span className={styles.statLabel}>Quick Actions:</span>
          <button 
            className={styles.quickAction}
            onClick={() => {
              // Quick export selected
              const ids = Array.from(selectedIds);
              window.open(`/api/v1/files/export?ids=${ids.join(',')}`, '_blank');
            }}
          >
            📤 Export
          </button>
          <button 
            className={styles.quickAction}
            onClick={() => {
              // Quick download as ZIP
              const ids = Array.from(selectedIds);
              window.location.href = `/api/v1/files/download?ids=${ids.join(',')}`;
            }}
          >
            ⬇️ Download ZIP
          </button>
          <button 
            className={styles.quickAction}
            onClick={() => {
              // Clear selection
              clearSelection();
            }}
          >
            ✕ Clear
          </button>
        </div>
      )}
    </div>
  );
};

export default BulkOperationsBar;
