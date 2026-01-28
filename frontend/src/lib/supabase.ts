"use client"

import { createClient } from "@supabase/supabase-js"
import { Database } from "./database.types"

// Environment variables (set these in your .env.local)
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ""
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""

// Create Supabase client
export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  },
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  }
})

// Types for file operations
export interface FileUploadResult {
  success: boolean
  file?: {
    id: string
    name: string
    path: string
    size: number
    content_type: string
    created_at: string
  }
  error?: string
  publicUrl?: string
}

export interface FileRecord {
  id: string
  user_id: string
  name: string
  path: string
  size: number
  content_type: string
  status: string
  created_at: string
  updated_at: string
}

// File storage operations
export const fileStorage = {
  // Upload file
  async upload(
    file: File,
    userId: string,
    onProgress?: (progress: number) => void
  ): Promise<FileUploadResult> {
    try {
      const filePath = `${userId}/${Date.now()}_${file.name}`
      
      const { data, error } = await supabase.storage
        .from("files")
        .upload(filePath, file, {
          cacheControl: "3600",
          upsert: false,
          onUploadProgress: (progress) => {
            if (progress.totalBytes && onProgress) {
              onProgress((progress.loaded / progress.totalBytes) * 100)
            }
          }
        })

      if (error) {
        return { success: false, error: error.message }
      }

      // Get public URL
      const { data: urlData } = supabase.storage
        .from("files")
        .get_public_url(filePath)

      return {
        success: true,
        file: {
          id: data?.path || filePath,
          name: file.name,
          path: filePath,
          size: file.size,
          content_type: file.type,
          created_at: new Date().toISOString()
        },
        publicUrl: urlData?.publicUrl
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Upload failed"
      }
    }
  },

  // Delete file
  async delete(filePath: string): Promise<{ success: boolean; error?: string }> {
    const { error } = await supabase.storage.from("files").remove([filePath])
    if (error) {
      return { success: false, error: error.message }
    }
    return { success: true }
  },

  // Get signed URL for private file
  async getSignedUrl(
    filePath: string,
    expiresIn: number = 3600
  ): Promise<{ success: boolean; url?: string; error?: string }> {
    const { data, error } = await supabase.storage
      .from("files")
      .create_signed_url(filePath, expiresIn)

    if (error) {
      return { success: false, error: error.message }
    }

    return { success: true, url: data?.signedUrl }
  },

  // List user files
  async listFiles(
    userId: string,
    folder?: string
  ): Promise<{ success: boolean; files?: FileRecord[]; error?: string }> {
    const path = folder ? `${userId}/${folder}` : `${userId}/`

    const { data, error } = await supabase.storage
      .from("files")
      .list(path, {
        limit: 100,
        offset: 0,
        sortBy: { column: "name", order: "asc" }
      })

    if (error) {
      return { success: false, error: error.message }
    }

    return {
      success: true,
      files: data?.map((item) => ({
        id: item.id,
        user_id: userId,
        name: item.name,
        path: `${path}${item.name}`,
        size: item.metadata?.size || 0,
        content_type: item.metadata?.mimetype || "application/octet-stream",
        status: "active",
        created_at: item.created_at || new Date().toISOString(),
        updated_at: item.updated_at || new Date().toISOString()
      }))
    }
  }
}

// Realtime subscriptions for file updates
export const fileRealtime = {
  // Subscribe to file changes
  subscribe(
    userId: string,
    callbacks: {
      onInsert?: (file: FileRecord) => void
      onUpdate?: (file: FileRecord) => void
      onDelete?: (fileId: string) => void
    }
  ) {
    const channel = supabase
      .channel(`files:${userId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "files",
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          if (callbacks.onInsert && payload.new) {
            callbacks.onInsert(payload.new as FileRecord)
          }
        }
      )
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "files",
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          if (callbacks.onUpdate && payload.new) {
            callbacks.onUpdate(payload.new as FileRecord)
          }
        }
      )
      .on(
        "postgres_changes",
        {
          event: "DELETE",
          schema: "public",
          table: "files",
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          if (callbacks.onDelete && payload.old) {
            callbacks.onDelete((payload.old as FileRecord).id)
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  },

  // Subscribe to processing status updates
  subscribeToProcessing(
    fileId: string,
    callback: (status: { status: string; progress?: number }) => void
  ) {
    const channel = supabase
      .channel(`processing:${fileId}`)
      .on("broadcast", { event: "status" }, (payload) => {
        callback(payload.payload)
      })
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  },

  // Broadcast processing status
  async broadcastStatus(
    fileId: string,
    status: { status: string; progress?: number }
  ) {
    await supabase.channel(`processing:${fileId}`).send({
      type: "broadcast",
      event: "status",
      payload: status
    })
  }
}

// Auth helper functions
export const authHelpers = {
  // Sign up
  async signUp(
    email: string,
    password: string,
    metadata?: { name?: string; role?: string }
  ) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata
      }
    })

    if (error) {
      return { success: false, error: error.message }
    }

    return { success: true, user: data.user, session: data.session }
  },

  // Sign in
  async signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.sign_in_with_password({
      email,
      password
    })

    if (error) {
      return { success: false, error: error.message }
    }

    return { success: true, user: data.user, session: data.session }
  },

  // Sign out
  async signOut() {
    const { error } = await supabase.auth.sign_out()
    if (error) {
      return { success: false, error: error.message }
    }
    return { success: true }
  },

  // Get current session
  async getSession() {
    const { data, error } = await supabase.auth.getSession()
    if (error) {
      return { success: false, error: error.message }
    }
    return { success: true, session: data.session }
  },

  // Get user
  async getUser() {
    const { data, error } = await supabase.auth.getUser()
    if (error) {
      return { success: false, error: error.message }
    }
    return { success: true, user: data.user }
  },

  // OAuth sign in
  async signInWithOAuth(provider: "github" | "google" | "discord") {
    const { data, error } = await supabase.auth.sign_in_with_oauth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })

    if (error) {
      return { success: false, error: error.message }
    }

    return { success: true, url: data.url }
  },

  // Reset password
  async resetPassword(email: string) {
    const { error } = await supabase.auth.reset_password_email(email)
    if (error) {
      return { success: false, error: error.message }
    }
    return { success: true }
  },

  // Update user
  async updateUser(metadata: { name?: string; avatar_url?: string }) {
    const { data, error } = await supabase.auth.update_user({
      data: metadata
    })

    if (error) {
      return { success: false, error: error.message }
    }

    return { success: true, user: data.user }
  }
}

// Export types
export type { FileRecord }
