"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"
import { jwtDecode } from "jwt-decode"

// Types
interface User {
  id: number
  email: string
  name: string
  roles: string[]
  permissions: string[]
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
  hasRole: (roles: string | string[]) => boolean
  hasPermission: (permission: string) => boolean
  refreshUser: () => Promise<void>
}

interface JWTPayload {
  sub: string
  roles?: string[]
  permissions?: string[]
  exp?: number
  iat?: number
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

// Role guard hook
export function useRoleGuard(requiredRoles: string | string[]) {
  const { user, hasRole, isLoading } = useAuth()
  const [hasAccess, setHasAccess] = useState(false)

  useEffect(() => {
    if (!isLoading) {
      const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles]
      setHasAccess(hasRole(roles))
    }
  }, [user, isLoading, requiredRoles, hasRole])

  return { hasAccess, isLoading }
}

// Permission guard hook
export function usePermissionGuard(requiredPermission: string) {
  const { user, hasPermission, isLoading } = useAuth()
  const [hasAccess, setHasAccess] = useState(false)

  useEffect(() => {
    if (!isLoading) {
      setHasAccess(hasPermission(requiredPermission))
    }
  }, [user, isLoading, requiredPermission, hasPermission])

  return { hasAccess, isLoading }
}

// Provider component
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Parse JWT token
  const parseToken = useCallback((token: string): User | null => {
    try {
      const payload = jwtDecode<JWTPayload>(token)
      
      // Check if token is expired
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        return null
      }

      return {
        id: parseInt(payload.sub),
        email: "",
        name: "",
        roles: payload.roles || [],
        permissions: payload.permissions || []
      }
    } catch {
      return null
    }
  }, [])

  // Initialize from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token")
    if (storedToken) {
      const decodedUser = parseToken(storedToken)
      if (decodedUser) {
        setToken(storedToken)
        setUser(decodedUser)
      } else {
        // Token is invalid or expired
        localStorage.removeItem("auth_token")
      }
    }
    setIsLoading(false)
  }, [parseToken])

  // Login function
  const login = useCallback((newToken: string) => {
    const decodedUser = parseToken(newToken)
    if (decodedUser) {
      localStorage.setItem("auth_token", newToken)
      setToken(newToken)
      setUser(decodedUser)
    }
  }, [parseToken])

  // Logout function
  const logout = useCallback(() => {
    localStorage.removeItem("auth_token")
    setToken(null)
    setUser(null)
  }, [])

  // Refresh user data from API
  const refreshUser = useCallback(async () => {
    if (!token) return

    try {
      const response = await fetch("/api/v1/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        const userData = await response.json()
        // Merge with decoded token data
        setUser(prev => prev ? {
          ...prev,
          ...userData,
          roles: prev.roles, // Keep roles from token
          permissions: prev.permissions // Keep permissions from token
        } : null)
      }
    } catch (error) {
      console.error("Failed to refresh user:", error)
    }
  }, [token])

  // Check if user has any of the required roles
  const hasRole = useCallback((roles: string | string[]): boolean => {
    if (!user) return false

    const requiredRoles = Array.isArray(roles) ? roles : [roles]
    return requiredRoles.some(role => user.roles.includes(role))
  }, [user])

  // Check if user has a specific permission
  const hasPermission = useCallback((permission: string): boolean => {
    if (!user) return false

    // Check token permissions first
    if (user.permissions.includes(permission)) {
      return true
    }

    // Admin has all permissions
    if (user.roles.includes("admin")) {
      return true
    }

    return false
  }, [user])

  // Update token in localStorage when it changes
  useEffect(() => {
    if (token) {
      localStorage.setItem("auth_token", token)
    }
  }, [token])

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    hasRole,
    hasPermission,
    refreshUser
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Higher-order component for protected routes
interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRoles?: string | string[]
  requiredPermission?: string
  fallback?: React.ReactNode
}

export function ProtectedRoute({
  children,
  requiredRoles,
  requiredPermission,
  fallback = <AccessDenied />
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, hasRole, hasPermission } = useAuth()

  if (isLoading) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>
  }

  if (!isAuthenticated) {
    return <AccessDenied message="Please log in to access this page" />
  }

  if (requiredRoles && !hasRole(requiredRoles)) {
    return fallback
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return fallback
  }

  return <>{children}</>
}

// Access Denied component
interface AccessDeniedProps {
  message?: string
}

export function AccessDenied({ message = "You don't have permission to access this page" }: AccessDeniedProps) {
  const { logout } = useAuth()

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-red-600">403</h1>
        <h2 className="mt-4 text-2xl font-semibold text-gray-800">Access Denied</h2>
        <p className="mt-2 text-gray-600">{message}</p>
        <div className="mt-6 space-x-4">
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 text-white bg-gray-500 rounded hover:bg-gray-600"
          >
            Go Back
          </button>
          <button
            onClick={logout}
            className="px-4 py-2 text-white bg-blue-600 rounded hover:bg-blue-700"
          >
            Log Out
          </button>
        </div>
      </div>
    </div>
  )
}

// Role-based UI component
interface RoleBasedUIProps {
  roles: string | string[]
  children: React.ReactNode
  fallback?: React.ReactNode
  showWhenAllowed?: boolean
}

export function RoleBasedUI({
  roles,
  children,
  fallback = null,
  showWhenAllowed = true
}: RoleBasedUIProps) {
  const { hasRole, isLoading } = useAuth()

  if (isLoading) {
    return null
  }

  const hasAccess = hasRole(roles)
  const shouldShow = showWhenAllowed ? hasAccess : !hasAccess

  return shouldShow ? <>{children}</> : <>{fallback}</>
}

// Permission-based UI component
interface PermissionBasedUIProps {
  permission: string
  children: React.ReactNode
  fallback?: React.ReactNode
  showWhenAllowed?: boolean
}

export function PermissionBasedUI({
  permission,
  children,
  fallback = null,
  showWhenAllowed = true
}: PermissionBasedUIProps) {
  const { hasPermission, isLoading } = useAuth()

  if (isLoading) {
    return null
  }

  const hasAccess = hasPermission(permission)
  const shouldShow = showWhenAllowed ? hasAccess : !hasAccess

  return shouldShow ? <>{children}</> : <>{fallback}</>
}

// Admin-only component
export function AdminOnly({ children }: { children: React.ReactNode }) {
  return (
    <RoleBasedUI roles="admin">
      {children}
    </RoleBasedUI>
  )
}

// Manager or admin component
export function ManagerOnly({ children }: { children: React.ReactNode }) {
  return (
    <RoleBasedUI roles={["admin", "manager"]}>
      {children}
    </RoleBasedUI>
  )
}

// Export types for external use
export type { User, AuthContextType, JWTPayload }
