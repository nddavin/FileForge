import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { FileManagerProvider } from '@/contexts/FileManagerContext';
import { AuthForm } from '@/app/components/AuthForm';
import { SermonFileManager } from '@/app/components/SermonFileManager';
import { Toaster } from '@/app/components/ui/sonner';

// 3D Glowing Sphere Demo - Open src/app/components/GlowingSphere3D.html in browser to view

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <AuthForm />;
  }

  return (
    <FileManagerProvider>
      <SermonFileManager />
    </FileManagerProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster />
    </AuthProvider>
  );
}
