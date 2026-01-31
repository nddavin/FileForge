// FileForge API Utility
// Provides a unified interface for API calls to the FastAPI backend

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: Record<string, unknown>;
  headers?: Record<string, string>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Bulk Operations API
export const bulkApi = {
  sort: (fileIds: string[], rules?: unknown[], sortBy?: string, churchId?: string) =>
    request('/bulk/bulk-sort', {
      method: 'POST',
      body: { file_ids: fileIds, rules, sort_by: sortBy, church_id: churchId },
    }),

  tag: (fileIds: string[], tags: string[]) =>
    request('/bulk/bulk-tag', {
      method: 'POST',
      body: { file_ids: fileIds, tags },
    }),

  move: (fileIds: string[], folderId: string) =>
    request('/bulk/bulk-move', {
      method: 'POST',
      body: { file_ids: fileIds, folder_id: folderId },
    }),

  optimize: (fileIds: string[], churchId: string, profile?: string) =>
    request('/bulk/bulk-optimize', {
      method: 'POST',
      body: { file_ids: fileIds, church_id: churchId, profile },
    }),

  createPackage: (fileIds: string[], churchId: string, name?: string) =>
    request('/bulk/bulk-package', {
      method: 'POST',
      body: { file_ids: fileIds, church_id: churchId, name },
    }),
};

// Rules API
export const rulesApi = {
  list: () => request('/bulk/rules'),
  create: (rule: {
    name: string;
    condition_type: string;
    condition_value: string;
    action_type: string;
    action_value: string;
  }) =>
    request('/bulk/rules', {
      method: 'POST',
      body: rule,
    }),
  delete: (ruleId: string) => request(`/bulk/rules/${ruleId}`, { method: 'DELETE' }),
};

// Files API
export const filesApi = {
  create: (fileData: {
    name: string;
    path: string;
    size: number;
    content_type?: string;
    metadata?: Record<string, unknown>;
    tags?: string[];
  }) =>
    request('/bulk/files', {
      method: 'POST',
      body: fileData,
    }),

  update: (fileId: string, fileData: Record<string, unknown>) =>
    request(`/bulk/files/${fileId}`, {
      method: 'PATCH',
      body: fileData,
    }),

  delete: (fileId: string) => request(`/bulk/files/${fileId}`, { method: 'DELETE' }),
};

// Sermons API
export const sermonsApi = {
  getStats: () => request('/sermons/stats'),
  getMetadata: (fileId: string) => request(`/sermons/${fileId}/metadata`),
  updateMetadata: (fileId: string, metadata: Record<string, unknown>) =>
    request(`/sermons/${fileId}/metadata`, {
      method: 'PATCH',
      body: metadata,
    }),
  optimize: (fileId: string, profile: string) =>
    request(`/sermons/${fileId}/optimize`, {
      method: 'POST',
      body: { profile },
    }),
  getQuality: (fileId: string) => request(`/sermons/${fileId}/quality`),
};

// RBAC API
export const rbacApi = {
  listRoles: () => request('/rbac/roles'),
  createRole: (role: { name: string; description?: string; permission_ids?: number[] }) =>
    request('/rbac/roles', {
      method: 'POST',
      body: role,
    }),
  updateRole: (
    roleId: number,
    role: { name?: string; description?: string; permission_ids?: number[] }
  ) =>
    request(`/rbac/roles/${roleId}`, {
      method: 'PUT',
      body: role,
    }),
  deleteRole: (roleId: number) => request(`/rbac/roles/${roleId}`, { method: 'DELETE' }),
};

// Integrations API
export const integrationsApi = {
  listAvailable: () => request('/integrations/available'),
  getStatus: () => request('/integrations/status'),
  connect: (type: string, config: Record<string, unknown>) =>
    request(`/integrations/connect/${type}`, {
      method: 'POST',
      body: config,
    }),
};
