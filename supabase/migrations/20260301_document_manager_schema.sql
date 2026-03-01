-- ===== Document Manager Schema =====

-- Temp files table (임시 저장)
CREATE TABLE IF NOT EXISTS temp_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE
);

-- File management table (파일 관리 - 최종본 메타데이터)
CREATE TABLE IF NOT EXISTS file_management (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE
);

-- File contents table (파일 내용 - 가변적 데이터)
-- data 컬럼은 JSONB로 엑셀 헤더 기반 동적 필드를 저장
CREATE TABLE IF NOT EXISTS file_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES file_management(id) ON DELETE CASCADE,
    row_index INTEGER NOT NULL,
    data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for faster file content lookups
CREATE INDEX IF NOT EXISTS idx_file_contents_file_id
    ON file_contents(file_id);

CREATE INDEX IF NOT EXISTS idx_file_contents_file_row
    ON file_contents(file_id, row_index);

-- ===== Row Level Security =====

ALTER TABLE temp_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_management ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_contents ENABLE ROW LEVEL SECURITY;

-- Temp files: users can only access their own files
CREATE POLICY temp_files_user_policy ON temp_files
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- File management: users can only access their own files
CREATE POLICY file_management_user_policy ON file_management
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- File contents: users can access contents of their own files
CREATE POLICY file_contents_user_policy ON file_contents
    FOR ALL
    USING (
        file_id IN (
            SELECT id FROM file_management WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        file_id IN (
            SELECT id FROM file_management WHERE user_id = auth.uid()
        )
    );

-- ===== Storage Bucket =====
-- Run this in the Supabase dashboard SQL editor:
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('files', 'files', false)
-- ON CONFLICT (id) DO NOTHING;
