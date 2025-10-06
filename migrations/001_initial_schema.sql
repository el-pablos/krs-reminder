-- KRS Reminder Bot - Multi-User Database Schema
-- Migration: 001_initial_schema
-- Date: 2025-10-07
-- Description: Initial database schema for multi-user support

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    secret_key_hash VARCHAR(255) NOT NULL,
    google_calendar_token_encrypted TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for username lookup
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ============================================================
-- SCHEDULES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    course_name VARCHAR(255) NOT NULL,
    course_code VARCHAR(50),
    day_of_week INTEGER, -- 0=Monday, 6=Sunday
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    facilitator VARCHAR(255),
    class_type VARCHAR(50), -- 'Kuliah Teori', 'Praktikum', etc.
    google_event_id VARCHAR(255), -- Link to Google Calendar event
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, google_event_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_start_time ON schedules(start_time);
CREATE INDEX IF NOT EXISTS idx_schedules_user_start ON schedules(user_id, start_time);

-- ============================================================
-- SESSIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    telegram_chat_id BIGINT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for session lookup
CREATE INDEX IF NOT EXISTS idx_sessions_telegram_chat_id ON sessions(telegram_chat_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);

-- ============================================================
-- ADMINS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS admins (
    admin_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_chat_id BIGINT UNIQUE NOT NULL,
    permissions JSONB DEFAULT '{"can_add_user": true, "can_delete_user": true, "can_import_schedule": true, "can_view_all_users": true}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for admin lookup
CREATE INDEX IF NOT EXISTS idx_admins_telegram_chat_id ON admins(telegram_chat_id);

-- ============================================================
-- REMINDERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS reminders (
    reminder_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    schedule_id UUID NOT NULL REFERENCES schedules(schedule_id) ON DELETE CASCADE,
    reminder_type VARCHAR(20) NOT NULL, -- '5h', '3h', '2h', '1h', 'exact'
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for reminder processing
CREATE INDEX IF NOT EXISTS idx_reminders_user_schedule ON reminders(user_id, schedule_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status_time ON reminders(status, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_reminders_pending ON reminders(status) WHERE status = 'pending';

-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for schedules table
DROP TRIGGER IF EXISTS update_schedules_updated_at ON schedules;
CREATE TRIGGER update_schedules_updated_at
    BEFORE UPDATE ON schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update session last_activity
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for sessions table
DROP TRIGGER IF EXISTS update_sessions_activity ON sessions;
CREATE TRIGGER update_sessions_activity
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_session_activity();

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);

-- Policy: Schedules - users can only see their own schedules
CREATE POLICY schedules_select_own ON schedules
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);

-- Policy: Sessions - users can only see their own sessions
CREATE POLICY sessions_select_own ON sessions
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);

-- Policy: Reminders - users can only see their own reminders
CREATE POLICY reminders_select_own ON reminders
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);

-- Note: Service role key bypasses RLS, which is what we'll use for bot operations

-- ============================================================
-- INITIAL DATA
-- ============================================================

-- Insert initial admin (Owner)
INSERT INTO admins (telegram_chat_id, permissions)
VALUES (
    5476148500,
    '{"can_add_user": true, "can_delete_user": true, "can_import_schedule": true, "can_view_all_users": true, "is_owner": true}'::jsonb
)
ON CONFLICT (telegram_chat_id) DO NOTHING;

-- ============================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================

-- View: Active sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    s.session_id,
    s.user_id,
    u.username,
    s.telegram_chat_id,
    s.created_at,
    s.expires_at,
    s.last_activity,
    EXTRACT(EPOCH FROM (s.expires_at - NOW())) / 3600 AS hours_until_expiry
FROM sessions s
JOIN users u ON s.user_id = u.user_id
WHERE s.is_active = TRUE
  AND s.expires_at > NOW()
ORDER BY s.last_activity DESC;

-- View: Upcoming schedules (next 7 days)
CREATE OR REPLACE VIEW upcoming_schedules AS
SELECT 
    s.schedule_id,
    s.user_id,
    u.username,
    s.course_name,
    s.course_code,
    s.start_time,
    s.end_time,
    s.location,
    s.facilitator,
    s.class_type
FROM schedules s
JOIN users u ON s.user_id = u.user_id
WHERE s.start_time >= NOW()
  AND s.start_time <= NOW() + INTERVAL '7 days'
ORDER BY s.start_time;

-- View: Pending reminders
CREATE OR REPLACE VIEW pending_reminders AS
SELECT 
    r.reminder_id,
    r.user_id,
    u.username,
    s.course_name,
    r.reminder_type,
    r.scheduled_time,
    EXTRACT(EPOCH FROM (r.scheduled_time - NOW())) / 60 AS minutes_until_send
FROM reminders r
JOIN users u ON r.user_id = u.user_id
JOIN schedules s ON r.schedule_id = s.schedule_id
WHERE r.status = 'pending'
  AND r.scheduled_time > NOW()
ORDER BY r.scheduled_time;

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE users IS 'User accounts with authentication credentials';
COMMENT ON TABLE schedules IS 'Course schedules imported from Google Calendar';
COMMENT ON TABLE sessions IS 'Active user sessions for Telegram bot';
COMMENT ON TABLE admins IS 'Admin users with elevated permissions';
COMMENT ON TABLE reminders IS 'Scheduled reminders for courses';

COMMENT ON COLUMN users.secret_key_hash IS 'Bcrypt hash of user secret key';
COMMENT ON COLUMN users.google_calendar_token_encrypted IS 'AES-256 encrypted Google Calendar token';
COMMENT ON COLUMN schedules.day_of_week IS '0=Monday, 1=Tuesday, ..., 6=Sunday';
COMMENT ON COLUMN sessions.expires_at IS 'Session expiry time (default: 24 hours from creation)';
COMMENT ON COLUMN reminders.reminder_type IS 'Type: 5h, 3h, 2h, 1h, or exact';

-- ============================================================
-- GRANT PERMISSIONS
-- ============================================================

-- Grant all permissions to service role (used by bot)
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Grant read-only to anon role (for future web interface)
GRANT SELECT ON active_sessions TO anon;
GRANT SELECT ON upcoming_schedules TO anon;
GRANT SELECT ON pending_reminders TO anon;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_initial_schema completed successfully';
    RAISE NOTICE 'Tables created: users, schedules, sessions, admins, reminders';
    RAISE NOTICE 'Initial admin inserted: telegram_chat_id = 5476148500';
END $$;

