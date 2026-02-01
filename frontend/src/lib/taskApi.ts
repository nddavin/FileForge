// Task Assignment API Service
import {
  TaskWorkflow,
  TaskAssignment,
  TeamMember,
  TaskStatistics,
  TaskProgress,
  TaskStatus,
  TaskType,
  WorkflowStatus,
  AssignmentAlgorithm,
  AssignmentResult,
  CreateWorkflowRequest,
  AssignTaskRequest,
  PaginationParams,
  ApiResponse,
  TeamRole,
} from './types';

const API_BASE = '/api/v1/tasks';

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

// ==================== Workflow Management ====================

export async function createWorkflow(
  request: CreateWorkflowRequest
): Promise<ApiResponse<TaskWorkflow>> {
  const params = new URLSearchParams({
    name: request.name,
    task_types: request.task_types.join(','),
    ...(request.entity_type && { entity_type: request.entity_type }),
    ...(request.entity_id && { entity_id: request.entity_id }),
    ...(request.priority && { priority: request.priority.toString() }),
  });

  return fetchApi<ApiResponse<TaskWorkflow>>(`/workflows?${params}`, {
    method: 'POST',
  });
}

export async function startWorkflow(
  workflowId: string
): Promise<ApiResponse<TaskWorkflow>> {
  return fetchApi<ApiResponse<TaskWorkflow>>(`/workflows/${workflowId}/start`, {
    method: 'POST',
  });
}

export async function getWorkflow(
  workflowId: string
): Promise<ApiResponse<TaskWorkflow>> {
  return fetchApi<ApiResponse<TaskWorkflow>>(`/workflows/${workflowId}`);
}

export async function listWorkflows(
  params: PaginationParams & {
    status?: WorkflowStatus;
    entity_type?: string;
  } = {}
): Promise<ApiResponse<TaskWorkflow[]>> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.entity_type) searchParams.set('entity_type', params.entity_type);
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  return fetchApi<ApiResponse<TaskWorkflow[]>>(
    `/workflows?${searchParams.toString()}`
  );
}

export async function getWorkflowProgress(
  workflowId: string
): Promise<ApiResponse<TaskProgress>> {
  return fetchApi<ApiResponse<TaskProgress>>(`/workflows/${workflowId}`);
}

// ==================== Task Management ====================

export async function assignTask(
  taskId: string,
  request: AssignTaskRequest = {}
): Promise<ApiResponse<AssignmentResult>> {
  const params = new URLSearchParams();
  if (request.assigned_to_id) {
    params.set('assigned_to_id', request.assigned_to_id.toString());
  }
  if (request.algorithm) {
    params.set('algorithm', request.algorithm);
  }

  return fetchApi<ApiResponse<AssignmentResult>>(
    `/${taskId}/assign?${params.toString()}`,
    { method: 'POST' }
  );
}

export async function updateTaskStatus(
  taskId: string,
  status: TaskStatus,
  resultData?: Record<string, unknown>,
  errorMessage?: string
): Promise<ApiResponse<null>> {
  return fetchApi<ApiResponse<null>>(`/${taskId}/status`, {
    method: 'PUT',
    body: JSON.stringify({
      status,
      ...(resultData && { result_data: resultData }),
      ...(errorMessage && { error_message: errorMessage }),
    }),
  });
}

export async function getTask(
  taskId: string
): Promise<ApiResponse<TaskAssignment>> {
  return fetchApi<ApiResponse<TaskAssignment>>(`/${taskId}`);
}

export async function listTasks(
  params: PaginationParams & {
    status?: TaskStatus;
    task_type?: TaskType;
    assigned_to_id?: number;
  } = {}
): Promise<ApiResponse<TaskAssignment[]>> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.task_type) searchParams.set('task_type', params.task_type);
  if (params.assigned_to_id) {
    searchParams.set('assigned_to_id', params.assigned_to_id.toString());
  }
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  return fetchApi<ApiResponse<TaskAssignment[]>>(`/?${searchParams.toString()}`);
}

// ==================== Team Members ====================

export async function listTeamMembers(
  params: PaginationParams & {
    role?: string;
    is_active?: boolean;
  } = {}
): Promise<ApiResponse<TeamMember[]>> {
  const searchParams = new URLSearchParams();
  if (params.role) searchParams.set('role', params.role);
  if (params.is_active !== undefined) {
    searchParams.set('is_active', params.is_active.toString());
  }
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  return fetchApi<ApiResponse<TeamMember[]>>(
    `/team/members?${searchParams.toString()}`
  );
}

export async function getTeamMember(
  memberId: number
): Promise<ApiResponse<TeamMember>> {
  return fetchApi<ApiResponse<TeamMember>>(`/team/members/${memberId}`);
}

// ==================== Statistics ====================

export async function getTaskStatistics(): Promise<ApiResponse<TaskStatistics>> {
  return fetchApi<ApiResponse<TaskStatistics>>('/statistics');
}

// ==================== Celery Orchestration ====================

export interface OrchestrateResult {
  workflow_id: string;
  celery_task_id: string;
}

export async function orchestrateWorkflow(
  uploadedFiles: string[],
  options: {
    church_id?: string;
    name?: string;
    entity_type?: string;
    entity_id?: string;
    priority?: number;
  } = {}
): Promise<ApiResponse<OrchestrateResult>> {
  const searchParams = new URLSearchParams();
  searchParams.set('uploaded_files', JSON.stringify(uploadedFiles));

  return fetchApi<ApiResponse<OrchestrateResult>>(
    `/orchestrate?${searchParams.toString()}`,
    {
      method: 'POST',
      body: JSON.stringify(options),
    }
  );
}

// ==================== Utility Functions ====================

export function getStatusColor(status: TaskStatus | WorkflowStatus): string {
  const colors: Record<string, string> = {
    [TaskStatus.PENDING]: 'bg-yellow-100 text-yellow-800',
    [TaskStatus.ASSIGNED]: 'bg-blue-100 text-blue-800',
    [TaskStatus.IN_PROGRESS]: 'bg-purple-100 text-purple-800',
    [TaskStatus.COMPLETED]: 'bg-green-100 text-green-800',
    [TaskStatus.FAILED]: 'bg-red-100 text-red-800',
    [TaskStatus.CANCELLED]: 'bg-gray-100 text-gray-800',
    [TaskStatus.REVIEW_REQUIRED]: 'bg-orange-100 text-orange-800',
    [WorkflowStatus.CREATED]: 'bg-gray-100 text-gray-800',
    [WorkflowStatus.INTAKE]: 'bg-blue-100 text-blue-800',
    [WorkflowStatus.PROCESSING]: 'bg-purple-100 text-purple-800',
    [WorkflowStatus.PARTIAL_FAILURE]: 'bg-orange-100 text-orange-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}

export function getTaskTypeLabel(type: TaskType): string {
  const labels: Record<TaskType, string> = {
    [TaskType.TRANSCRIPTION]: 'Transcription',
    [TaskType.VIDEO_PROCESSING]: 'Video Processing',
    [TaskType.LOCATION_TAGGING]: 'Location Tagging',
    [TaskType.ARTWORK_QUALITY]: 'Artwork Quality',
    [TaskType.METADATA_AI]: 'AI Metadata',
    [TaskType.THUMBNAIL_GENERATION]: 'Thumbnail Generation',
    [TaskType.SOCIAL_CLIP]: 'Social Clip',
    [TaskType.DISTRIBUTION]: 'Distribution',
  };
  return labels[type] || type;
}

export function getTeamRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    [TeamRole.EDITOR]: 'Editor',
    [TeamRole.PROCESSOR]: 'Processor',
    [TeamRole.MANAGER]: 'Manager',
    [TeamRole.ADMIN]: 'Admin',
    [TeamRole.AUDIO_ENGINEER]: 'Audio Engineer',
    [TeamRole.VIDEO_PROCESSOR]: 'Video Processor',
    [TeamRole.TRANSCRIBER]: 'Transcriber',
    [TeamRole.LOCATION_TAGGER]: 'Location Tagger',
    [TeamRole.MEDIA_COORDINATOR]: 'Media Coordinator',
  };
  return labels[role] || role;
}
