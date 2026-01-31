// Supabase configuration for FileForge frontend
// These values should be set in environment variables in production

export const projectId = import.meta.env.VITE_SUPABASE_PROJECT_ID || 'demo-project';
export const publicAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'demo-anon-key';
export const supabaseUrl = `https://${projectId}.supabase.co`;
