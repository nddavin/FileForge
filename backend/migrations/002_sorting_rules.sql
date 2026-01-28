-- Database Migration: Smart Sorting Rules Schema
-- Run this in Supabase SQL Editor

-- Sorting Rules Table
CREATE TABLE IF NOT EXISTS sorting_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    church_id UUID NOT NULL,
    name TEXT NOT NULL,
    conditions JSONB NOT NULL DEFAULT '[]',
    target_folder TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    auto_apply BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for church lookups
CREATE INDEX IF NOT EXISTS idx_sorting_rules_church_id 
ON sorting_rules(church_id);

-- Index for auto-apply queries
CREATE INDEX IF NOT EXISTS idx_sorting_rules_auto_apply 
ON sorting_rules(church_id, auto_apply) WHERE auto_apply = true;

-- Add columns to files table for sorting metadata
ALTER TABLE files ADD COLUMN IF NOT EXISTS predicted_folder TEXT;
ALTER TABLE files ADD COLUMN IF NOT EXISTS sorting_score FLOAT;
ALTER TABLE files ADD COLUMN IF NOT EXISTS sermon_package_id UUID;

-- Index for package lookups
CREATE INDEX IF NOT EXISTS idx_files_sermon_package 
ON files(sermon_package_id);

-- Index for folder lookups
CREATE INDEX IF NOT EXISTS idx_files_folder 
ON files(folder_id);

-- RLS Policies for sorting_rules
ALTER TABLE sorting_rules ENABLE ROW LEVEL SECURITY;

-- Church admins can manage sorting rules
CREATE POLICY "Church admins can manage sorting rules"
ON sorting_rules FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM churches
        WHERE churches.id = sorting_rules.church_id
        AND churches.admin_id = auth.uid()
    )
);

-- All church members can view sorting rules
CREATE POLICY "Church members can view sorting rules"
ON sorting_rules FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM church_members
        WHERE church_members.church_id = sorting_rules.church_id
        AND church_members.user_id = auth.uid()
    )
);

-- RLS Policies for files (update sermon_package_id)
ALTER TABLE files ENABLE ROW LEVEL SECURITY;

-- Allow updates to sorting metadata for church members
CREATE POLICY "Church members can update file sorting metadata"
ON files FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM church_members
        WHERE church_members.church_id = files.church_id
        AND church_members.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM church_members
        WHERE church_members.church_id = files.church_id
        AND church_members.user_id = auth.uid()
    )
);

-- Trigger to update timestamp
CREATE OR REPLACE FUNCTION update_sorting_rules_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sorting_rules_updated_at
    BEFORE UPDATE ON sorting_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_sorting_rules_timestamp();
