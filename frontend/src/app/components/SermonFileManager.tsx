import React, { useState, useRef, lazy, Suspense } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { Button } from '@/app/components/ui/button';
import { BulkOperationsBar } from '@/app/components/BulkOperationsBar';
import { Upload, LogOut, RefreshCw } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useFileManager } from '@/contexts/FileManagerContext';
import { fileStorage } from '@/lib/supabase';
import { projectId, publicAnonKey } from '@/utils/supabase/info';
import { toast } from 'sonner';

// Lazy load tab components to reduce initial bundle size
const SmartSortingRules = lazy(() => import('@/app/components/SmartSortingRules').then(m => ({ default: m.SmartSortingRules })));
const RelationshipGraph = lazy(() => import('@/app/components/RelationshipGraph').then(m => ({ default: m.RelationshipGraph })));
const KanbanBoard = lazy(() => import('@/app/components/KanbanBoard').then(m => ({ default: m.KanbanBoard })));
const AdvancedSearch = lazy(() => import('@/app/components/AdvancedSearch').then(m => ({ default: m.AdvancedSearch })));
const CoreDashboard = lazy(() => import('@/app/components/CoreDashboard').then(m => ({ default: m.CoreDashboard })));
const SermonProcessingUI = lazy(() => import('@/app/components/SermonProcessingUI').then(m => ({ default: m.SermonProcessingUI })));
const WorkflowAndIntegrations = lazy(() => import('@/app/components/WorkflowAndIntegrations').then(m => ({ default: m.WorkflowAndIntegrations })));
const Dashboard = lazy(() => import('@/app/components/Dashboard').then(m => ({ default: m.Dashboard })));
const FileUpload = lazy(() => import('@/app/components/FileManagement').then(m => ({ default: m.FileUpload })));
const SmartFileGrid = lazy(() => import('@/app/components/FileManagement').then(m => ({ default: m.SmartFileGrid })));

// Loading fallback component
function TabLoadingFallback() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-gray-500">Loading...</div>
    </div>
  );
}

export function SermonFileManager() {
  const { user, signOut } = useAuth();
  const { refreshFiles } = useFileManager();
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        // Upload to storage
        const path = `${user?.id}/${Date.now()}-${file.name}`;
        await fileStorage.upload(file, path);

        // Create file metadata in database
        await fetch(`https://${projectId}.supabase.co/functions/v1/make-server-24311ee2/files`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${publicAnonKey}`,
          },
          body: JSON.stringify({
            name: file.name,
            path,
            size: file.size,
            type: file.type,
            user_id: user?.id,
          }),
        });
      }

      toast.success(`Successfully uploaded ${files.length} file(s)`);
      await refreshFiles();
    } catch (error) {
      console.error('Error uploading files:', error);
      toast.error('Failed to upload files');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">FileForge</h1>
              <p className="text-sm text-gray-500">Sermon File Management</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-600">
                {user?.user_metadata?.name || user?.email}
              </div>
              <Button variant="outline" size="sm" onClick={() => refreshFiles()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={() => signOut()}>
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="files" className="w-full">
          <div className="flex items-center justify-between mb-6">
            <TabsList>
              <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
              <TabsTrigger value="upload">Upload</TabsTrigger>
              <TabsTrigger value="files">Files</TabsTrigger>
              <TabsTrigger value="processing">Processing</TabsTrigger>
              <TabsTrigger value="workflow">Workflow</TabsTrigger>
              <TabsTrigger value="kanban">Kanban</TabsTrigger>
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="rules">Smart Rules</TabsTrigger>
              <TabsTrigger value="relationships">Relationships</TabsTrigger>
            </TabsList>

            <div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="audio/*,video/*"
                className="hidden"
                onChange={(e) => handleUpload(e.target.files)}
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <Upload className="w-4 h-4 mr-2" />
                {uploading ? 'Uploading...' : 'Upload Files'}
              </Button>
            </div>
          </div>

          <TabsContent value="dashboard" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <CoreDashboard />
            </Suspense>
          </TabsContent>

          <TabsContent value="upload" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <FileUpload />
            </Suspense>
          </TabsContent>

          <TabsContent value="files" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <SmartFileGrid />
            </Suspense>
          </TabsContent>

          <TabsContent value="processing" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <SermonProcessingUI />
            </Suspense>
          </TabsContent>

          <TabsContent value="workflow" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <WorkflowAndIntegrations />
            </Suspense>
          </TabsContent>

          <TabsContent value="kanban" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <KanbanBoard />
            </Suspense>
          </TabsContent>

          <TabsContent value="search" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <AdvancedSearch />
            </Suspense>
          </TabsContent>

          <TabsContent value="rules" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <SmartSortingRules />
            </Suspense>
          </TabsContent>

          <TabsContent value="relationships" className="mt-6">
            <Suspense fallback={<TabLoadingFallback />}>
              <RelationshipGraph />
            </Suspense>
          </TabsContent>
        </Tabs>
      </main>

      <BulkOperationsBar />
    </div>
  );
}
