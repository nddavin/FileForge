// Task Assignment Types matching backend models

export enum TaskType {
  TRANSCRIPTION = 'transcription',
  VIDEO_PROCESSING = 'video_processing',
  LOCATION_TAGGING = 'location_tagging',
  ARTWORK_QUALITY = 'artwork_quality',
  METADATA_AI = 'metadata_ai',
  THUMBNAIL_GENERATION = 'thumbnail_generation',
  SOCIAL_CLIP = 'social_clip',
  DISTRIBUTION = 'distribution',
}

export enum TaskStatus {
  PENDING = 'pending',
  ASSIGNED = 'assigned',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  REVIEW_REQUIRED = 'review_required',
}

export enum WorkflowStatus {
  CREATED = 'created',
  INTAKE = 'intake',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  PARTIAL_FAILURE = 'partial_failure',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum TeamRole {
  EDITOR = 'editor',
  PROCESSOR = 'processor',
  MANAGER = 'manager',
  ADMIN = 'admin',
  AUDIO_ENGINEER = 'audio_engineer',
  VIDEO_PROCESSOR = 'video_processor',
  TRANSCRIBER = 'transcriber',
  LOCATION_TAGGER = 'location_tagger',
  MEDIA_COORDINATOR = 'media_coordinator',
}

export enum AssignmentAlgorithm {
  AI_MATCHING = 'ai_matching',
  SKILL_MATCH = 'skill_match',
  WORKLOAD_BALANCE = 'workload_balance',
  RANDOM = 'random',
  MANUAL = 'manual',
}

export interface Skill {
  id: number;
  name: string;
  category: string;
  description?: string;
  required_tools: string[];
  proficiency_levels: Record<string, number>;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TeamMember {
  id: number;
  user_id?: number;
  supabase_uid?: string;
  email: string;
  full_name: string;
  team_role: TeamRole;
  is_available: boolean;
  max_concurrent_tasks: number;
  current_workload: number;
  workload_score: number;
  completed_tasks_count: number;
  average_completion_time?: number;
  rating: number;
  notification_channels: string[];
  skills: Skill[];
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TaskAssignment {
  id: number;
  task_id: string;
  workflow_id: number;
  task_type: TaskType;
  status: TaskStatus;
  priority: number;
  assigned_to_id?: number;
  assigned_by?: number;
  assigned_at?: string;
  required_skills: string[];
  ai_assignment_score?: number;
  assignment_reason?: string;
  input_data: Record<string, unknown>;
  result_data: Record<string, unknown>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  deadline?: string;
  retry_count: number;
  max_retries: number;
  error_message?: string;
  celery_task_id?: string;
  assigned_to?: TeamMember;
}

export interface TaskWorkflow {
  id: number;
  workflow_id: string;
  name: string;
  description?: string;
  entity_type: string;
  entity_id: string;
  status: WorkflowStatus;
  priority: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  deadline?: string;
  metadata: Record<string, unknown>;
  error_message?: string;
  created_by?: number;
  task_count: number;
  completed_task_count: number;
}

export interface TaskProgress {
  total: number;
  completed: number;
  percentage: number;
  failed: number;
  in_progress: number;
  pending: number;
}

export interface AssignmentResult {
  success: boolean;
  task_id?: string;
  assigned_to_id?: number;
  assignment_score?: number;
  reason?: string;
  errors: string[];
}

export interface TaskStatistics {
  total_tasks: number;
  completed_tasks: number;
  in_progress: number;
  pending: number;
  failed: number;
  by_type: Record<string, number>;
  by_assignee: Record<number, AssigneeStats>;
  completion_rate: number;
}

export interface AssigneeStats {
  full_name: string;
  email: string;
  role: string;
  assigned_tasks: number;
  completed_tasks: number;
  current_workload: number;
  max_concurrent_tasks: number;
  completion_rate: number;
}

// Storage Types
export interface MediaUrl {
  url: string;
  signed: boolean;
}

export interface StorageStats {
  file_count: number;
  total_size: number;
  public: boolean;
}

export interface StorageUsageStats {
  [bucket: string]: StorageStats;
}

export interface UploadResult {
  success: boolean;
  bucket: string;
  path: string;
  filename: string;
  size: number;
  mime_type: string;
  public_url?: string;
  signed_url?: string;
  metadata?: Record<string, unknown>;
  error?: string;
}

export interface MediaUrlsResult {
  success: boolean;
  urls: Record<string, MediaUrl>;
  error?: string;
}

export interface SyncResult {
  success: boolean;
  metadata_path?: string;
  error?: string;
}

export interface CleanupResult {
  success: boolean;
  deleted_files: number;
  error?: string;
}

export interface StoragePolicyResult {
  success: boolean;
  policies?: string;
  error?: string;
}

// Workflow creation request
export interface CreateWorkflowRequest {
  name: string;
  entity_type?: string;
  entity_id?: string;
  task_types: TaskType[];
  priority?: number;
  metadata?: Record<string, unknown>;
}

// Task assignment request
export interface AssignTaskRequest {
  assigned_to_id?: number;
  algorithm?: AssignmentAlgorithm;
}

// Pagination
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface PaginationResult {
  limit: number;
  offset: number;
  total: number;
}

// API Response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  pagination?: PaginationResult;
  error?: string;
}
