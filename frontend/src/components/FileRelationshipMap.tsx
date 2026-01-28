/* File Relationship Map - Visual sermon package overview */

import React, { useMemo } from 'react';
import { useFileManager, FileType } from '../contexts/FileManagerContext';
import styles from './FileRelationshipMap.module.css';

interface PackageNodeProps {
  pkg: {
    id: string;
    name: string;
    created_at: string;
  };
  files: FileType[];
}

const PackageNode: React.FC<PackageNodeProps> = ({ pkg, files }) => {
  const hasAudio = files.some(f => f.file_type?.includes('audio'));
  const hasVideo = files.some(f => f.file_type?.includes('video'));
  const hasTranscript = files.some(f => 
    f.file_type?.includes('text') || f.file_type?.includes('pdf')
  );

  return (
    <div className={styles.packageNode}>
      <div className={styles.packageHeader}>
        <span className={styles.packageIcon}>📦</span>
        <span className={styles.packageName}>{pkg.name}</span>
        <span className={styles.fileCount}>{files.length} files</span>
      </div>

      <div className={styles.fileIcons}>
        {hasAudio && <span className={styles.fileTypeIcon} title="Audio">🎵 Audio</span>}
        {hasVideo && <span className={styles.fileTypeIcon} title="Video">🎬 Video</span>}
        {hasTranscript && <span className={styles.fileTypeIcon} title="Transcript">📄 Transcript</span>}
      </div>

      <div className={styles.fileList}>
        {files.slice(0, 5).map(file => (
          <div key={file.id} className={styles.miniFile}>
            <span className={styles.miniIcon}>
              {file.file_type?.includes('audio') ? '🎵' : 
               file.file_type?.includes('video') ? '🎬' : '📄'}
            </span>
            <span className={styles.miniName}>{file.filename}</span>
          </div>
        ))}
        {files.length > 5 && (
          <div className={styles.moreFiles}>+{files.length - 5} more</div>
        )}
      </div>

      <div className={styles.completeness}>
        <span className={styles.completenessLabel}>Package Status:</span>
        <div className={styles.completenessBar}>
          <div 
            className={styles.completenessFill}
            style={{ 
              width: `${((Number(hasAudio) + Number(hasVideo) + Number(hasTranscript)) / 3) * 100}%`,
              background: hasAudio && hasVideo && hasTranscript ? '#2b8a3e' : '#e67700'
            }}
          />
        </div>
        <span className={styles.completenessStatus}>
          {hasAudio && hasVideo && hasTranscript ? 'Complete' : 'Incomplete'}
        </span>
      </div>
    </div>
  );
};

export const FileRelationshipMap: React.FC = () => {
  const { files, relationshipMap } = useFileManager();

  // Group files into sermon packages
  const sermonPackages = useMemo(() => {
    const packages: { id: string; name: string; created_at: string; files: FileType[] }[] = [];
    
    relationshipMap.forEach((pkgFiles, pkgId) => {
      // Extract package name from first file
      const firstFile = pkgFiles[0];
      const packageName = firstFile.profiles?.full_name 
        ? `Sermon Package - ${firstFile.profiles.full_name}`
        : `Sermon Package ${pkgId.slice(0, 8)}`;
      
      packages.push({
        id: pkgId,
        name: packageName,
        created_at: firstFile.created_at,
        files: pkgFiles
      });
    });
    
    // Sort by date (most recent first)
    return packages.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [relationshipMap]);

  // Count incomplete packages
  const completePackages = sermonPackages.filter(pkg => {
    const hasAudio = pkg.files.some(f => f.file_type?.includes('audio'));
    const hasVideo = pkg.files.some(f => f.file_type?.includes('video'));
    return hasAudio && hasVideo;
  }).length;

  if (files.length === 0) {
    return (
      <div className={styles.emptyMap}>
        <span className={styles.emptyIcon}>📊</span>
        <h3>No sermon packages yet</h3>
        <p>Select multiple files and create a package to see relationships</p>
      </div>
    );
  }

  return (
    <div className={styles.relationshipMap}>
      {/* Stats Header */}
      <div className={styles.mapHeader}>
        <h3>📊 Sermon Packages ({sermonPackages.length} total)</h3>
        <div className={styles.mapStats}>
          <span className={styles.stat}>
            ✅ {completePackages} complete
          </span>
          <span className={styles.stat}>
            📦 {files.length} total files
          </span>
          <span className={styles.stat}>
            🔗 {sermonPackages.length} packages
          </span>
        </div>
      </div>

      {/* Unpackaged Files */}
      {(() => {
        const packagedIds = new Set<string>();
        sermonPackages.forEach(pkg => {
          pkg.files.forEach(f => packagedIds.add(f.id));
        });
        
        const unpackaged = files.filter(f => !packagedIds.has(f.id));
        
        if (unpackaged.length > 0) {
          return (
            <div className={styles.unpackagedSection}>
              <h4>📂 Unpackaged Files ({unpackaged.length})</h4>
              <div className={styles.unpackagedGrid}>
                {unpackaged.slice(0, 12).map(file => (
                  <div key={file.id} className={styles.unpackagedFile}>
                    <span>{file.file_type?.includes('audio') ? '🎵' : 
                           file.file_type?.includes('video') ? '🎬' : '📄'}</span>
                    <span className={styles.fileLabel}>{file.filename}</span>
                  </div>
                ))}
                {unpackaged.length > 12 && (
                  <div className={styles.moreUnpackaged}>
                    +{unpackaged.length - 12} more
                  </div>
                )}
              </div>
            </div>
          );
        }
      })()}

      {/* Package Grid */}
      <div className={styles.packageGrid}>
        {sermonPackages.map(pkg => (
          <PackageNode key={pkg.id} pkg={pkg} files={pkg.files} />
        ))}
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        <h4>Legend</h4>
        <div className={styles.legendItems}>
          <div className={styles.legendItem}>
            <span>🎵</span> Audio file (MP3, WAV)
          </div>
          <div className={styles.legendItem}>
            <span>🎬</span> Video file (MP4, MOV)
          </div>
          <div className={styles.legendItem}>
            <span>📄</span> Transcript/Document
          </div>
          <div className={styles.legendItem}>
            <span>📦</span> Complete package
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileRelationshipMap;
