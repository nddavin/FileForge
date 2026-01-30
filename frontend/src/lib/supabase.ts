import { createClient } from '@supabase/supabase-js';
import { projectId, publicAnonKey } from '/utils/supabase/info';

const supabaseUrl = `https://${projectId}.supabase.co`;
const supabaseKey = publicAnonKey;

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
});

// File storage operations
export const fileStorage = {
  async upload(file: File, path: string) {
    const { data, error } = await supabase.storage
      .from('make-24311ee2-files')
      .upload(path, file, {
        cacheControl: '3600',
        upsert: false,
      });
    
    if (error) throw error;
    return data;
  },

  async getSignedUrl(path: string, expiresIn = 3600) {
    const { data, error } = await supabase.storage
      .from('make-24311ee2-files')
      .createSignedUrl(path, expiresIn);
    
    if (error) throw error;
    return data.signedUrl;
  },

  async delete(path: string) {
    const { error } = await supabase.storage
      .from('make-24311ee2-files')
      .remove([path]);
    
    if (error) throw error;
  },

  async list(prefix?: string) {
    const { data, error } = await supabase.storage
      .from('make-24311ee2-files')
      .list(prefix, {
        limit: 100,
        offset: 0,
        sortBy: { column: 'created_at', order: 'desc' },
      });
    
    if (error) throw error;
    return data;
  },
};

// Auth helper functions
export const authHelpers = {
  async signUp(email: string, password: string, name: string) {
    const response = await fetch(`${supabaseUrl}/functions/v1/make-server-24311ee2/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseKey}`,
      },
      body: JSON.stringify({ email, password, name }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Sign up error: ${error}`);
    }

    return response.json();
  },

  async signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;
    return data;
  },

  async signOut() {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  },

  async getSession() {
    const { data, error } = await supabase.auth.getSession();
    if (error) throw error;
    return data.session;
  },

  async resetPassword(email: string) {
    const { error } = await supabase.auth.resetPasswordForEmail(email);
    if (error) throw error;
  },
};

// Realtime subscription helpers
export const fileRealtime = {
  subscribeToFiles(callback: (payload: any) => void) {
    const channel = supabase
      .channel('file-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'files',
        },
        callback
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  },
};

export interface FileRecord {
  id: string;
  name: string;
  path: string;
  size: number;
  type: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  folder_id?: string;
  metadata?: Record<string, any>;
}

export interface FileUploadResult {
  id: string;
  path: string;
  fullPath: string;
}

// Team members operations
export const teamMembers = {
  async list() {
    const { data, error } = await supabase
      .from('team_members')
      .select('*')
      .order('name');
    
    if (error) {
      console.warn('Team members table not found, using mock data');
      return null;
    }
    return data;
  },

  async getAvailability() {
    const { data, error } = await supabase
      .from('team_members')
      .select('id, name, role, available')
      .order('name');
    
    if (error) {
      console.warn('Team availability not available, using mock data');
      return null;
    }
    return data;
  },

  async updateAssignment(memberId: string, role: string, fileId: string) {
    const { error } = await supabase
      .from('file_assignments')
      .upsert({
        team_member_id: memberId,
        file_id: fileId,
        role,
        assigned_at: new Date().toISOString(),
      });
    
    if (error) throw error;
  },
};
