// Database types for Supabase
// Generated from Supabase SQL schema

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      files: {
        Row: {
          id: string
          user_id: string
          name: string
          path: string
          size: number
          content_type: string
          status: string
          metadata: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          path: string
          size: number
          content_type: string
          status?: string
          metadata?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          path?: string
          size?: number
          content_type?: string
          status?: string
          metadata?: Json | null
          created_at?: string
          updated_at?: string
        }
      }
      users: {
        Row: {
          id: string
          email: string
          name: string | null
          avatar_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      workflows: {
        Row: {
          id: string
          user_id: string
          name: string
          description: string | null
          config: Json
          status: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          description?: string | null
          config?: Json
          status?: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          description?: string | null
          config?: Json
          status?: string
          created_at?: string
          updated_at?: string
        }
      }
      roles: {
        Row: {
          id: number
          name: string
          description: string | null
          is_active: boolean
          created_at: string
        }
        Insert: {
          id?: number
          name: string
          description?: string | null
          is_active?: boolean
          created_at?: string
        }
        Update: {
          id?: number
          name?: string
          description?: string | null
          is_active?: boolean
          created_at?: string
        }
      }
      permissions: {
        Row: {
          id: number
          name: string
          resource: string
          action: string
          description: string | null
          is_active: boolean
          created_at: string
        }
        Insert: {
          id?: number
          name: string
          resource: string
          action: string
          description?: string | null
          is_active?: boolean
          created_at?: string
        }
        Update: {
          id?: number
          name?: string
          resource?: string
          action?: string
          description?: string | null
          is_active?: boolean
          created_at?: string
        }
      }
      audit_logs: {
        Row: {
          id: number
          user_id: string | null
          action: string
          resource: string
          resource_id: string | null
          details: Json | null
          ip_address: string | null
          status: string
          created_at: string
        }
        Insert: {
          id?: number
          user_id?: string | null
          action: string
          resource: string
          resource_id?: string | null
          details?: Json | null
          ip_address?: string | null
          status?: string
          created_at?: string
        }
        Update: {
          id?: number
          user_id?: string | null
          action?: string
          resource?: string
          resource_id?: string | null
          details?: Json | null
          ip_address?: string | null
          status?: string
          created_at?: string
        }
      }
    }
    Views: {}
    Functions: {}
    Enums: {}
    CompositeTypes: {}
  }
}

// Type exports
export type File = Database["public"]["Tables"]["files"]["Row"]
export type User = Database["public"]["Tables"]["users"]["Row"]
export type Workflow = Database["public"]["Tables"]["workflows"]["Row"]
export type Role = Database["public"]["Tables"]["roles"]["Row"]
export type Permission = Database["public"]["Tables"]["permissions"]["Row"]
export type AuditLog = Database["public"]["Tables"]["audit_logs"]["Row"]

// Insert types
export type FileInsert = Database["public"]["Tables"]["files"]["Insert"]
export type UserInsert = Database["public"]["Tables"]["users"]["Insert"]
export type WorkflowInsert = Database["public"]["Tables"]["workflows"]["Insert"]

// Update types
export type FileUpdate = Database["public"]["Tables"]["files"]["Update"]
export type UserUpdate = Database["public"]["Tables"]["users"]["Update"]
export type WorkflowUpdate = Database["public"]["Tables"]["workflows"]["Update"]
