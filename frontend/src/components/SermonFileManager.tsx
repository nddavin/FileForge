/* Sermon File Manager - Smart Sorting Dashboard with Bulk Operations */

import React, { useState } from 'react';
import { useFileManager } from '../contexts/FileManagerContext';
import { BulkOperationsBar } from './BulkOperationsBar';
import { SmartSortingRules } from './SmartSortingRules';
import { FileGrid } from './FileGrid';
import { FileRelationshipMap } from './FileRelationshipMap';
import styles from './SermonFileManager.module.css';

interface SermonFileManagerProps {
  churchId: string;
}

export const SermonFileManager: React.FC<SermonFileManagerProps> = ({ churchId }) => {
  const [activeTab, setActiveTab] = useState<'files' | 'rules' | 'map'>('files');
  const [showFolderAssigner, setShowFolderAssigner] = useState(false);
  
  const { 
    files, 
    loading, 
    refreshFiles, 
    selectedCount,
    totalFiles 
  } = useFileManager();

  return (
    <div className={styles.fileManager}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h2>📁 Sermon File Manager</h2>
          <span className={styles.fileCount}>
            {totalFiles} files • {selectedCount} selected
          </span>
        </div>
        
        {/* Tab Navigation */}
        <div className={styles.tabs}>
          <button 
            className={`${styles.tab} ${activeTab === 'files' ? styles.active : ''}`}
            onClick={() => setActiveTab('files')}
          >
            📂 Files
          </button>
          <button 
            className={`${styles.tab} ${activeTab === 'rules' ? styles.active : ''}`}
            onClick={() => setActiveTab('rules')}
          >
            🤖 Smart Rules
          </button>
          <button 
            className={`${styles.tab} ${activeTab === 'map' ? styles.active : ''}`}
            onClick={() => setActiveTab('map')}
          >
            📊 Relationships
          </button>
        </div>
        
        {/* Actions */}
        <div className={styles.actions}>
          <button className={styles.refreshBtn} onClick={refreshFiles}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Bulk Operations Bar */}
      <BulkOperationsBar onFolderAssigner={() => setShowFolderAssigner(true)} />

      {/* Folder Assigner Modal */}
      {showFolderAssigner && (
        <FolderAssignerModal 
          onClose={() => setShowFolderAssigner(false)}
          onAssign={(folderId) => {
            // Handle folder assignment
            setShowFolderAssigner(false);
          }}
        />
      )}

      {/* Main Content */}
      <div className={styles.content}>
        {activeTab === 'files' && (
          <FileGrid 
            files={files}
            loading={loading}
            showPreviewToggle={true}
          />
        )}
        
        {activeTab === 'rules' && (
          <SmartSortingRules />
        )}
        
        {activeTab === 'map' && (
          <FileRelationshipMap />
        )}
      </div>
    </div>
  );
};

// Folder Assigner Modal
interface FolderAssignerModalProps {
  onClose: () => void;
  onAssign: (folderId: string) => void;
}

const FolderAssignerModal: React.FC<FolderAssignerModalProps> = ({ 
  onClose, 
  onAssign 
}) => {
  const [folders] = useState([
    { id: '1', name: 'Sunday Services', path: '/sermons/sunday' },
    { id: '2', name: 'Youth Sermons', path: '/sermons/youth' },
    { id: '3', name: 'Womens Ministry', path: '/sermons/women' },
    { id: '4', name: 'Mens Ministry', path: '/sermons/men' },
    { id: '5', name: 'Special Events', path: '/sermons/events' },
    { id: '6', name: 'Archive', path: '/archive' }
  ]);
  const [selectedFolder, setSelectedFolder] = useState('');

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h3>📁 Assign to Folder</h3>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>
        
        <div className={styles.modalContent}>
          <div className={styles.folderList}>
            {folders.map(folder => (
              <div 
                key={folder.id}
                className={`${styles.folderItem} ${selectedFolder === folder.id ? styles.selected : ''}`}
                onClick={() => setSelectedFolder(folder.id)}
              >
                <span className={styles.folderIcon}>📁</span>
                <div className={styles.folderInfo}>
                  <span className={styles.folderName}>{folder.name}</span>
                  <span className={styles.folderPath}>{folder.path}</span>
                </div>
              </div>
            ))}
          </div>
          
          {/* Create New Folder Option */}
          <div className={styles.newFolder}>
            <input 
              type="text" 
              placeholder="Or type new folder path..."
              className={styles.newFolderInput}
            />
          </div>
        </div>
        
        <div className={styles.modalFooter}>
          <button className={styles.cancelBtn} onClick={onClose}>
            Cancel
          </button>
          <button 
            className={styles.assignBtn}
            disabled={!selectedFolder}
            onClick={() => onAssign(selectedFolder)}
          >
            Move to Folder
          </button>
        </div>
      </div>
    </div>
  );
};

export default SermonFileManager;
