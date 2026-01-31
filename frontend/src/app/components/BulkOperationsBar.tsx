import React, { useState } from 'react';
import { useFileManager } from '@/contexts/FileManagerContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select';
import {
  Trash2,
  FolderInput,
  Tag,
  Zap,
  X,
  MoreHorizontal,
  Loader2,
  CheckCircle,
} from 'lucide-react';
import { bulkApi, filesApi } from '@/lib/api';
import { toast } from 'sonner';

// Bulk operation types
type BulkAction = 'tag' | 'move' | 'delete' | 'optimize';

interface BulkOperationResponse {
  success: boolean;
  message?: string;
  errors?: string[];
}

export function BulkOperationsBar() {
  const { selectedFiles, clearSelection, refreshFiles } = useFileManager();
  const { session } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeAction, setActiveAction] = useState<BulkAction | null>(null);
  
  // Dialog states
  const [isTagDialogOpen, setIsTagDialogOpen] = useState(false);
  const [isMoveDialogOpen, setIsMoveDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isOptimizeDialogOpen, setIsOptimizeDialogOpen] = useState(false);
  
  // Form states
  const [tagInput, setTagInput] = useState('');
  const [targetFolder, setTargetFolder] = useState('');
  const [optimizationProfile, setOptimizationProfile] = useState<string>('');

  // Check if user has manager/admin role
  const userRole = session?.user?.user_metadata?.role || session?.user?.user_metadata?.user_type;
  const isManagerOrAdmin = userRole === 'manager' || userRole === 'admin' || userRole === 'administrator';

  // Available folders for move operation
  const folders = [
    { id: 'folder_1', name: 'Sermons 2024' },
    { id: 'folder_2', name: 'Sermons 2023' },
    { id: 'folder_3', name: 'Pending Review' },
    { id: 'folder_4', name: 'Published' },
    { id: 'folder_5', name: 'Archive' },
  ];

  // Optimization profiles
  const optimizationProfiles = [
    { id: 'sermon_web', name: 'Web', description: '720p, 2Mbps, streaming optimized' },
    { id: 'sermon_podcast', name: 'Podcast', description: 'Audio-only, 128kbps, RSS ready' },
    { id: 'sermon_archive', name: 'Archive', description: '1080p, 10Mbps, full quality' },
  ];

  // Updated bulk API call function using FastAPI backend
  const handleTag = async () => {
    if (!tagInput.trim()) {
      toast.error('Please enter at least one tag');
      return;
    }

    setLoading(true);
    try {
      const tags = tagInput.split(',').map(t => t.trim()).filter(Boolean);
      
      await bulkApi.tag(Array.from(selectedFiles), tags);
      
      toast.success(`Added tags to ${selectedFiles.size} file(s)`, {
        description: `Tags: ${tags.join(', ')}`,
      });
      
      setIsTagDialogOpen(false);
      setTagInput('');
      clearSelection();
      await refreshFiles();
    } catch (error) {
      toast.error('Failed to add tags');
    } finally {
      setLoading(false);
    }
  };

  const handleMove = async () => {
    if (!targetFolder) {
      toast.error('Please select a destination folder');
      return;
    }

    setLoading(true);
    try {
      await bulkApi.move(Array.from(selectedFiles), targetFolder);
      
      const folder = folders.find(f => f.id === targetFolder);
      toast.success(`Moved ${selectedFiles.size} file(s)`, {
        description: `To: ${folder?.name || 'Unknown folder'}`,
      });
      
      setIsMoveDialogOpen(false);
      setTargetFolder('');
      clearSelection();
      await refreshFiles();
    } catch (error) {
      toast.error('Failed to move files');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setLoading(true);
    try {
      // Delete each file individually
      const deletePromises = Array.from(selectedFiles).map((fileId) =>
        filesApi.delete(fileId)
      );

      const results = await Promise.all(deletePromises);
      const successCount = results.length;
      
      toast.success(`Successfully deleted ${successCount} file(s)`);
      
      setIsDeleteDialogOpen(false);
      clearSelection();
      await refreshFiles();
    } catch (error) {
      toast.error('Failed to delete files');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!optimizationProfile) {
      toast.error('Please select an optimization profile');
      return;
    }

    setLoading(true);
    try {
      await bulkApi.optimize(Array.from(selectedFiles), 'default', optimizationProfile);
      
      const profile = optimizationProfiles.find(p => p.id === optimizationProfile);
      toast.success(`Optimization started for ${selectedFiles.size} file(s)`, {
        description: `Profile: ${profile?.name || optimizationProfile}`,
      });
      
      setIsOptimizeDialogOpen(false);
      setOptimizationProfile('');
      clearSelection();
    } catch (error) {
      toast.error('Failed to start optimization');
    } finally {
      setLoading(false);
    }
  };

  if (selectedFiles.size === 0) {
    return null;
  }

  // Don't render if user doesn't have required role
  if (!isManagerOrAdmin) {
    return null;
  }

  return (
    <>
      <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-white shadow-lg rounded-lg border p-4 flex items-center gap-4 z-50 min-w-[600px]">
        {/* Selection count */}
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-sm">
            {selectedFiles.size} selected
          </Badge>
        </div>
        
        {/* Action buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsTagDialogOpen(true)}
            disabled={loading}
          >
            <Tag className="w-4 h-4 mr-2" />
            Add Tags
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsMoveDialogOpen(true)}
            disabled={loading}
          >
            <FolderInput className="w-4 h-4 mr-2" />
            Move
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsOptimizeDialogOpen(true)}
            disabled={loading}
          >
            <Zap className="w-4 h-4 mr-2" />
            Optimize Batch
          </Button>
          
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setIsDeleteDialogOpen(true)}
            disabled={loading}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
        </div>
        
        {/* Clear selection */}
        <Button
          variant="ghost"
          size="sm"
          onClick={clearSelection}
          disabled={loading}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Tag Dialog */}
      <Dialog open={isTagDialogOpen} onOpenChange={setIsTagDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Tags to {selectedFiles.size} File(s)</DialogTitle>
            <DialogDescription>
              Enter comma-separated tags to add to all selected files.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Input
              placeholder="faith, grace, salvation (comma separated)"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
            />
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="cursor-pointer" onClick={() => setTagInput(prev => prev ? `${prev}, faith` : 'faith')}>
                faith
              </Badge>
              <Badge variant="secondary" className="cursor-pointer" onClick={() => setTagInput(prev => prev ? `${prev}, grace` : 'grace')}>
                grace
              </Badge>
              <Badge variant="secondary" className="cursor-pointer" onClick={() => setTagInput(prev => prev ? `${prev}, salvation` : 'salvation')}>
                salvation
              </Badge>
              <Badge variant="secondary" className="cursor-pointer" onClick={() => setTagInput(prev => prev ? `${prev}, sermon` : 'sermon')}>
                sermon
              </Badge>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsTagDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleTag} disabled={loading}>
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Apply Tags
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Move Dialog */}
      <Dialog open={isMoveDialogOpen} onOpenChange={setIsMoveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Move {selectedFiles.size} File(s)</DialogTitle>
            <DialogDescription>
              Select a destination folder for the selected files.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Select value={targetFolder} onValueChange={setTargetFolder}>
              <SelectTrigger>
                <SelectValue placeholder="Select destination folder" />
              </SelectTrigger>
              <SelectContent>
                {folders.map(folder => (
                  <SelectItem key={folder.id} value={folder.id}>
                    {folder.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsMoveDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleMove} disabled={loading || !targetFolder}>
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Move Files
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Optimize Dialog */}
      <Dialog open={isOptimizeDialogOpen} onOpenChange={setIsOptimizeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Optimize {selectedFiles.size} File(s)</DialogTitle>
            <DialogDescription>
              Select an optimization profile for batch processing.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid gap-3">
              {optimizationProfiles.map(profile => (
                <div
                  key={profile.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    optimizationProfile === profile.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setOptimizationProfile(profile.id)}
                >
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    optimizationProfile === profile.id 
                      ? 'border-blue-500 bg-blue-500' 
                      : 'border-gray-300'
                  }`}>
                    {optimizationProfile === profile.id && (
                      <CheckCircle className="w-3 h-3 text-white" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium">{profile.name}</p>
                    <p className="text-sm text-gray-500">{profile.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOptimizeDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleOptimize} disabled={loading || !optimizationProfile}>
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Start Optimization
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {selectedFiles.size} File(s)</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedFiles.size} file(s)? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg text-red-700">
              <Trash2 className="w-5 h-5" />
              <span className="font-medium">This will permanently delete the selected files.</span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete} disabled={loading}>
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Delete Files
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default BulkOperationsBar;
