-- Migration for Task Assignment Workflow RLS Policies
-- This file contains SQL migrations and RLS policies for task assignment functionality

-- Enable RLS on new tables
ALTER TABLE IF EXISTS skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS task_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS task_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS task_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS team_member_skills ENABLE ROW LEVEL SECURITY;

-- Create default skills
INSERT INTO skills (name, category, description, required_tools, proficiency_levels, is_active) VALUES
    ('whisper_transcription', 'transcription', 'Audio transcription using OpenAI Whisper', ARRAY['whisper', 'ffmpeg'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('fast_transcription', 'transcription', 'Fast typing and manual transcription skills', ARRAY['typing', 'transcription_software'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('ffmpeg_video_processing', 'video', 'Video processing using FFmpeg', ARRAY['ffmpeg', 'ffprobe'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('premiere_video_editing', 'video', 'Advanced video editing with Adobe Premiere', ARRAY['premiere_pro', 'media_encoder'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('exiftool_metadata', 'metadata', 'EXIF/GPS metadata extraction using EXIFTool', ARRAY['exiftool', 'geopy'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('gps_location_tagging', 'metadata', 'GPS coordinate extraction and geocoding', ARRAY['gps_extractor', 'nominatim'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('artwork_design', 'quality', 'Graphic design and artwork creation', ARRAY['photoshop', 'illustrator', 'canva'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('quality_assurance', 'quality', 'Quality checks and content review', ARRAY['qa_checklist', 'review_tools'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('audio_quality_analysis', 'quality', 'Audio quality metrics and optimization', ARRAY['ffmpeg', 'audio_analyzer'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('thumbnail_generation', 'video', 'Video thumbnail creation and optimization', ARRAY['ffmpeg', 'image_editor'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('ai_metadata_extraction', 'metadata', 'AI-powered metadata and content analysis', ARRAY['openai', 'llm'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true),
    ('social_media_clip_creation', 'video', 'Creating short clips for social media', ARRAY['ffmpeg', 'social_media_tools'], '{"beginner": 1, "intermediate": 2, "expert": 3}'::jsonb, true)
ON CONFLICT (name) DO NOTHING;


-- ==================== SKILLS TABLE POLICIES ====================

-- Policy: Everyone can view skills (read-only)
CREATE POLICY "Skills are readable by everyone" ON skills
    FOR SELECT USING (true);


-- ==================== TEAM MEMBERS TABLE POLICIES ====================

-- Policy: Users can view their own team profile
CREATE POLICY "Users can view own team profile" ON team_members
    FOR SELECT USING (auth.uid()::text = supabase_uid);

-- Policy: Users can update their own team profile
CREATE POLICY "Users can update own team profile" ON team_members
    FOR UPDATE USING (auth.uid()::text = supabase_uid)
    WITH CHECK (auth.uid()::text = supabase_uid);

-- Policy: Admins and managers can manage all team members
CREATE POLICY "Admins and managers can manage team members" ON team_members
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Policy: Processors can view available team members (for assignment visibility)
CREATE POLICY "Processors can view available team members" ON team_members
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name = 'processor'
        )
        AND is_active = true
    );


-- ==================== TASK WORKFLOWS TABLE POLICIES ====================

-- Policy: Users can view their own workflows
CREATE POLICY "Users can view own workflows" ON task_workflows
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = created_by
            AND users.supabase_uid = auth.uid()::text
        )
    );

-- Policy: Users can update their own workflows
CREATE POLICY "Users can update own workflows" ON task_workflows
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = created_by
            AND users.supabase_uid = auth.uid()::text
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = created_by
            AND users.supabase_uid = auth.uid()::text
        )
    );

-- Policy: Users can create workflows
CREATE POLICY "Users can create workflows" ON task_workflows
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = created_by
            AND users.supabase_uid = auth.uid()::text
        )
    );

-- Policy: Admins and managers can view all workflows
CREATE POLICY "Admins and managers can view all workflows" ON task_workflows
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Policy: Admins and managers can manage all workflows
CREATE POLICY "Admins and managers can manage all workflows" ON task_workflows
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Policy: Processors can view workflows they're assigned to
CREATE POLICY "Processors can view assigned workflows" ON task_workflows
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM task_assignments
            JOIN team_members ON task_assignments.assigned_to_id = team_members.id
            JOIN user_roles ON team_members.user_id = user_roles.user_id
            JOIN roles ON user_roles.role_id = roles.id
            WHERE task_assignments.workflow_id = task_workflows.id
            AND team_members.supabase_uid = auth.uid()::text
            AND roles.name = 'processor'
        )
    );


-- ==================== TASK ASSIGNMENTS TABLE POLICIES ====================

-- Policy: Users can view their own assigned tasks
CREATE POLICY "Users can view own assigned tasks" ON task_assignments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM team_members
            WHERE team_members.id = task_assignments.assigned_to_id
            AND team_members.supabase_uid = auth.uid()::text
        )
    );

-- Policy: Users can update their own tasks (status, result, etc.)
CREATE POLICY "Users can update own assigned tasks" ON task_assignments
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM team_members
            WHERE team_members.id = task_assignments.assigned_to_id
            AND team_members.supabase_uid = auth.uid()::text
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM team_members
            WHERE team_members.id = task_assignments.assigned_to_id
            AND team_members.supabase_uid = auth.uid()::text
        )
    );

-- Policy: Users can create tasks assigned to themselves (or as system)
CREATE POLICY "Users can create tasks assigned to themselves" ON task_assignments
    FOR INSERT WITH CHECK (
        (EXISTS (
            SELECT 1 FROM team_members
            WHERE team_members.id = task_assignments.assigned_to_id
            AND team_members.supabase_uid = auth.uid()::text
        )) OR
        (task_assignments.assigned_to_id IS NULL)
    );

-- Policy: Admins and managers can view all tasks
CREATE POLICY "Admins and managers can view all tasks" ON task_assignments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Policy: Admins and managers can manage all tasks
CREATE POLICY "Admins and managers can manage all tasks" ON task_assignments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Policy: Processors can only view and update their own assigned tasks (read-only for others)
CREATE POLICY "Processors can only view own tasks" ON task_assignments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM team_members
            JOIN user_roles ON team_members.user_id = user_roles.user_id
            JOIN roles ON user_roles.role_id = roles.id
            WHERE team_members.id = task_assignments.assigned_to_id
            AND team_members.supabase_uid = auth.uid()::text
            AND roles.name = 'processor'
        )
    );


-- ==================== TASK AUDIT LOGS TABLE POLICIES ====================

-- Policy: Everyone can view their own audit logs
CREATE POLICY "Users can view own audit logs" ON task_audit_logs
    FOR SELECT USING (
        (task_audit_logs.performed_by IS NULL) OR
        (EXISTS (
            SELECT 1 FROM users
            WHERE users.id = task_audit_logs.performed_by
            AND users.supabase_uid = auth.uid()::text
        ))
    );

-- Policy: Admins and managers can view all audit logs
CREATE POLICY "Admins and managers can view all audit logs" ON task_audit_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Policy: Only system (Celery workers) and admins can create audit logs
CREATE POLICY "System and admins can create audit logs" ON task_audit_logs
    FOR INSERT WITH CHECK (
        (task_audit_logs.performed_by IS NULL) OR
        (EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = task_audit_logs.performed_by
            AND roles.name IN ('admin', 'manager')
        ))
    );


-- ==================== TEAM MEMBER SKILLS TABLE POLICIES ====================

-- Policy: Read access to skills associations
CREATE POLICY "Team member skills are readable" ON team_member_skills
    FOR SELECT USING (
        (EXISTS (
            SELECT 1 FROM team_members
            WHERE team_members.id = team_member_skills.team_member_id
            AND team_members.supabase_uid = auth.uid()::text
        )) OR
        (EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        ))
    );

-- Policy: Users can manage their own skills
CREATE POLICY "Users can manage their own skills" ON team_member_skills
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM team_members
            WHERE team_members.id = team_member_skills.team_member_id
            AND team_members.supabase_uid = auth.uid()::text
        )
    );

-- Policy: Admins and managers can manage all skills associations
CREATE POLICY "Admins and managers can manage all skills" ON team_member_skills
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );


-- ==================== Role-Specific Permissions ====================

-- Create editor role (full access to all tasks)
INSERT INTO roles (name, description, is_active) VALUES
    ('editor', 'Full access to all file processing tasks and assignment management', true)
ON CONFLICT (name) DO NOTHING;

-- Create processor role (task-specific access)
INSERT INTO roles (name, description, is_active) VALUES
    ('processor', 'Task-specific access to assigned processing tasks', true)
ON CONFLICT (name) DO NOTHING;


-- ==================== Editor Role Permissions ====================
-- Grant all permissions to editors (admin-level access to tasks)

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    p.id
FROM permissions p
WHERE p.resource IN ('tasks', 'workflows', 'team')
ON CONFLICT DO NOTHING;

-- Grant specific task management permissions
INSERT INTO permissions (name, resource, action, description, is_active) VALUES
    ('tasks:view', 'tasks', 'read', 'View all tasks', true),
    ('tasks:create', 'tasks', 'create', 'Create new tasks', true),
    ('tasks:update', 'tasks', 'update', 'Update tasks', true),
    ('tasks:delete', 'tasks', 'delete', 'Delete tasks', true),
    ('tasks:assign', 'tasks', 'update', 'Assign tasks to team members', true),
    ('tasks:view_all', 'tasks', 'read', 'View all tasks in system', true),
    ('workflows:view', 'workflows', 'read', 'View all workflows', true),
    ('workflows:create', 'workflows', 'create', 'Create workflows', true),
    ('workflows:update', 'workflows', 'update', 'Update workflows', true),
    ('workflows:delete', 'workflows', 'delete', 'Delete workflows', true),
    ('workflows:execute', 'workflows', 'update', 'Execute workflows', true),
    ('workflows:view_all', 'workflows', 'read', 'View all workflows in system', true),
    ('team:view', 'team', 'read', 'View team members', true),
    ('team:create', 'team', 'create', 'Create team members', true),
    ('team:update', 'team', 'update', 'Update team members', true),
    ('team:delete', 'team', 'delete', 'Delete team members', true)
ON CONFLICT (name) DO NOTHING;

-- Assign all task permissions to editor role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'tasks:view')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'tasks:create')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'tasks:update')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'tasks:delete')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'tasks:assign')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'tasks:view_all')
ON CONFLICT DO NOTHING;

-- Assign all workflow permissions to editor role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'workflows:view')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'workflows:create')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'workflows:update')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'workflows:delete')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'workflows:execute')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'workflows:view_all')
ON CONFLICT DO NOTHING;

-- Assign all team permissions to editor role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'team:view')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'team:create')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'team:update')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'editor'),
    (SELECT id FROM permissions WHERE name = 'team:delete')
ON CONFLICT DO NOTHING;


-- ==================== Processor Role Permissions ====================
-- Grant task-specific permissions to processors

INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'processor'),
    (SELECT id FROM permissions WHERE name IN ('tasks:view', 'tasks:update'))
ON CONFLICT DO NOTHING;

-- Grant workflow view permission to processors
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'processor'),
    (SELECT id FROM permissions WHERE name = 'workflows:view')
ON CONFLICT DO NOTHING;


-- ==================== Indexes for Performance ====================

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_task_type ON task_assignments(task_type);
CREATE INDEX IF NOT EXISTS idx_task_status ON task_assignments(status);
CREATE INDEX IF NOT EXISTS idx_task_deadline ON task_assignments(deadline);
CREATE INDEX IF NOT EXISTS idx_workflow_status ON task_workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflow_entity ON task_workflows(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_team_member_email ON team_members(email);
CREATE INDEX IF NOT EXISTS idx_team_member_role ON team_members(team_role);
CREATE INDEX IF NOT EXISTS idx_team_member_supabase ON team_members(supabase_uid);
CREATE INDEX IF NOT EXISTS idx_audit_task ON task_audit_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON task_audit_logs(action);

-- Create GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_task_input_data ON task_assignments USING GIN(input_data);
CREATE INDEX IF NOT EXISTS idx_task_result_data ON task_assignments USING GIN(result_data);
CREATE INDEX IF NOT EXISTS idx_task_metadata ON task_workflows USING GIN(metadata);

-- Create GIN indexes for array fields
CREATE INDEX IF NOT EXISTS idx_skills_required_skills ON task_assignments USING GIN(required_skills);
CREATE INDEX IF NOT EXISTS idx_team_notification_channels ON team_members USING GIN(notification_channels);

-- Create indexes for association tables
CREATE INDEX IF NOT EXISTS idx_team_member_skills_member ON team_member_skills(team_member_id);
CREATE INDEX IF NOT EXISTS idx_team_member_skills_skill ON team_member_skills(skill_id);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_task_assigned_status ON task_assignments(assigned_to_id, status);
CREATE INDEX IF NOT EXISTS idx_task_workflow_type ON task_assignments(workflow_id, task_type);
CREATE INDEX IF NOT EXISTS idx_workflow_status_created ON task_workflows(status, created_at DESC);
