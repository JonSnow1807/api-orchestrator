-- =============================================================================
-- TEAM COLLABORATION SYSTEM - DATABASE SCHEMA
-- =============================================================================
-- Comprehensive database schema for team collaboration in API Orchestrator
-- Supports workspaces, team members, roles, permissions, and real-time collaboration

-- =============================================================================
-- 1. WORKSPACES/ORGANIZATIONS TABLE
-- =============================================================================
CREATE TABLE workspaces (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(100) UNIQUE NOT NULL, -- URL-friendly identifier
    
    -- Owner and settings
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_members INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Billing and subscription
    subscription_tier VARCHAR(50) DEFAULT 'free', -- free, starter, professional, enterprise
    billing_email VARCHAR(255),
    
    -- Settings
    settings JSON DEFAULT '{}', -- Workspace-specific settings
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_workspaces_owner (owner_id),
    INDEX idx_workspaces_slug (slug),
    INDEX idx_workspaces_active (is_active)
);

-- =============================================================================
-- 2. WORKSPACE MEMBERS TABLE
-- =============================================================================
CREATE TABLE workspace_members (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role and permissions
    role VARCHAR(20) NOT NULL DEFAULT 'viewer', -- owner, admin, developer, viewer
    permissions JSON DEFAULT '{}', -- Custom permissions override
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, pending
    
    -- Timestamps
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_workspace_user (workspace_id, user_id),
    
    -- Indexes
    INDEX idx_workspace_members_workspace (workspace_id),
    INDEX idx_workspace_members_user (user_id),
    INDEX idx_workspace_members_role (role),
    INDEX idx_workspace_members_status (status)
);

-- =============================================================================
-- 3. WORKSPACE INVITATIONS TABLE
-- =============================================================================
CREATE TABLE workspace_invitations (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    invited_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Invitation details
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'developer',
    message TEXT,
    
    -- Token and expiration
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, expired, revoked
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP NULL,
    
    -- Indexes
    INDEX idx_invitations_workspace (workspace_id),
    INDEX idx_invitations_email (email),
    INDEX idx_invitations_token (invitation_token),
    INDEX idx_invitations_status (status)
);

-- =============================================================================
-- 4. ROLES AND PERMISSIONS TABLE
-- =============================================================================
CREATE TABLE workspace_roles (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Role definition
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#6B7280', -- Hex color for UI
    
    -- Permissions
    permissions JSON NOT NULL DEFAULT '{}',
    
    -- System roles cannot be deleted
    is_system_role BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_workspace_role (workspace_id, name),
    
    -- Indexes
    INDEX idx_roles_workspace (workspace_id)
);

-- =============================================================================
-- 5. RESOURCE OWNERSHIP AND SHARING
-- =============================================================================

-- Update existing projects table to include workspace
ALTER TABLE projects 
ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
ADD COLUMN visibility VARCHAR(20) DEFAULT 'private', -- private, workspace, public
ADD COLUMN shared_with JSON DEFAULT '[]', -- Array of user IDs with specific access
ADD INDEX idx_projects_workspace (workspace_id),
ADD INDEX idx_projects_visibility (visibility);

-- Collections table for shared request collections
CREATE TABLE collections (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    created_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Collection details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Organization
    folder_path VARCHAR(500) DEFAULT '/', -- Nested folder structure
    tags JSON DEFAULT '[]',
    
    -- Sharing and permissions
    visibility VARCHAR(20) DEFAULT 'private', -- private, workspace, public
    shared_with JSON DEFAULT '[]', -- Array of {user_id, permission} objects
    
    -- Collection data
    requests JSON NOT NULL DEFAULT '[]', -- Array of request objects
    environments JSON DEFAULT '[]', -- Environment variables
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_collections_workspace (workspace_id),
    INDEX idx_collections_user (created_by_user_id),
    INDEX idx_collections_visibility (visibility)
);

-- =============================================================================
-- 6. ACTIVITY LOGS TABLE
-- =============================================================================
CREATE TABLE workspace_activity_logs (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Activity details
    action VARCHAR(50) NOT NULL, -- project_created, member_invited, etc.
    entity_type VARCHAR(50), -- project, collection, member, etc.
    entity_id VARCHAR(50), -- ID of the affected entity
    
    -- Activity data
    details JSON DEFAULT '{}', -- Additional context
    
    -- Metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_activity_workspace (workspace_id),
    INDEX idx_activity_user (user_id),
    INDEX idx_activity_action (action),
    INDEX idx_activity_created (created_at)
);

-- =============================================================================
-- 7. REAL-TIME COLLABORATION
-- =============================================================================
CREATE TABLE active_sessions (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session details
    session_token VARCHAR(255) UNIQUE NOT NULL,
    connection_id VARCHAR(255), -- WebSocket connection ID
    
    -- Current activity
    current_resource_type VARCHAR(50), -- project, collection, api
    current_resource_id VARCHAR(50),
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, idle, away
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_sessions_workspace (workspace_id),
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_token (session_token),
    INDEX idx_sessions_activity (last_activity_at)
);

-- Collaboration events for real-time updates
CREATE TABLE collaboration_events (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL, -- cursor_move, text_change, etc.
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(50) NOT NULL,
    
    -- Event data
    event_data JSON NOT NULL DEFAULT '{}',
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_collab_workspace (workspace_id),
    INDEX idx_collab_resource (resource_type, resource_id),
    INDEX idx_collab_created (created_at)
);

-- =============================================================================
-- 8. WORKSPACE SETTINGS AND PREFERENCES
-- =============================================================================
CREATE TABLE workspace_settings (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- General settings
    default_visibility VARCHAR(20) DEFAULT 'private',
    allow_public_sharing BOOLEAN DEFAULT FALSE,
    require_approval_for_joins BOOLEAN DEFAULT TRUE,
    
    -- Collaboration settings
    enable_real_time_collaboration BOOLEAN DEFAULT TRUE,
    auto_save_interval_seconds INTEGER DEFAULT 30,
    max_concurrent_editors INTEGER DEFAULT 10,
    
    -- Notification settings
    notify_on_member_join BOOLEAN DEFAULT TRUE,
    notify_on_project_share BOOLEAN DEFAULT TRUE,
    notify_on_collection_update BOOLEAN DEFAULT FALSE,
    
    -- Security settings
    enforce_2fa BOOLEAN DEFAULT FALSE,
    allowed_domains JSON DEFAULT '[]', -- Email domain restrictions
    session_timeout_minutes INTEGER DEFAULT 480, -- 8 hours
    
    -- API settings
    api_rate_limit_per_user INTEGER DEFAULT 1000,
    enable_api_key_access BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_workspace_settings (workspace_id)
);

-- =============================================================================
-- 9. SHARED RESOURCES PERMISSIONS
-- =============================================================================
CREATE TABLE resource_permissions (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Resource identification
    resource_type VARCHAR(50) NOT NULL, -- project, collection, api, etc.
    resource_id VARCHAR(50) NOT NULL,
    
    -- Permission details
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_name VARCHAR(50), -- Either user_id OR role_name should be set
    
    -- Permissions
    can_read BOOLEAN DEFAULT TRUE,
    can_write BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_share BOOLEAN DEFAULT FALSE,
    can_admin BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_permissions_workspace (workspace_id),
    INDEX idx_permissions_resource (resource_type, resource_id),
    INDEX idx_permissions_user (user_id),
    INDEX idx_permissions_role (role_name)
);

-- =============================================================================
-- 10. WORKSPACE USAGE AND ANALYTICS
-- =============================================================================
CREATE TABLE workspace_usage_stats (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Usage metrics
    total_projects INTEGER DEFAULT 0,
    total_apis INTEGER DEFAULT 0,
    total_collections INTEGER DEFAULT 0,
    total_requests_made INTEGER DEFAULT 0,
    
    -- Member activity
    active_members_count INTEGER DEFAULT 0,
    total_members_count INTEGER DEFAULT 0,
    
    -- Collaboration metrics
    total_shares INTEGER DEFAULT 0,
    total_collaboration_sessions INTEGER DEFAULT 0,
    
    -- Billing period
    billing_period VARCHAR(7) NOT NULL, -- YYYY-MM format
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_workspace_period (workspace_id, billing_period),
    
    -- Indexes
    INDEX idx_usage_workspace (workspace_id),
    INDEX idx_usage_period (billing_period)
);

-- =============================================================================
-- INITIAL DATA - DEFAULT ROLES
-- =============================================================================

-- Insert default system roles for all workspaces
INSERT INTO workspace_roles (workspace_id, name, display_name, description, permissions, is_system_role, color) 
VALUES 
-- Owner role (workspace creator)
(NULL, 'owner', 'Owner', 'Full access to workspace and billing', 
 '{"workspace":{"read":true,"write":true,"delete":true,"billing":true},"members":{"invite":true,"remove":true,"manage_roles":true},"projects":{"create":true,"read":true,"write":true,"delete":true,"share":true},"collections":{"create":true,"read":true,"write":true,"delete":true,"share":true},"settings":{"manage":true}}', 
 true, '#EF4444'),

-- Admin role (can manage members and content)
(NULL, 'admin', 'Admin', 'Manage members and workspace content', 
 '{"workspace":{"read":true,"write":true,"delete":false,"billing":false},"members":{"invite":true,"remove":false,"manage_roles":true},"projects":{"create":true,"read":true,"write":true,"delete":true,"share":true},"collections":{"create":true,"read":true,"write":true,"delete":true,"share":true},"settings":{"manage":false}}', 
 true, '#F59E0B'),

-- Developer role (can create and edit content)
(NULL, 'developer', 'Developer', 'Create and edit projects and collections', 
 '{"workspace":{"read":true,"write":false,"delete":false,"billing":false},"members":{"invite":false,"remove":false,"manage_roles":false},"projects":{"create":true,"read":true,"write":true,"delete":false,"share":true},"collections":{"create":true,"read":true,"write":true,"delete":false,"share":true},"settings":{"manage":false}}', 
 true, '#10B981'),

-- Viewer role (read-only access)
(NULL, 'viewer', 'Viewer', 'Read-only access to shared content', 
 '{"workspace":{"read":true,"write":false,"delete":false,"billing":false},"members":{"invite":false,"remove":false,"manage_roles":false},"projects":{"create":false,"read":true,"write":false,"delete":false,"share":false},"collections":{"create":false,"read":true,"write":false,"delete":false,"share":false},"settings":{"manage":false}}', 
 true, '#6B7280');

-- =============================================================================
-- INDEXES AND CONSTRAINTS
-- =============================================================================

-- Add foreign key constraints for workspace association to existing tables
-- (These would be added via migrations in a real implementation)

-- Performance indexes
CREATE INDEX idx_workspace_members_active ON workspace_members(workspace_id, status) WHERE status = 'active';
CREATE INDEX idx_invitations_pending ON workspace_invitations(workspace_id, status) WHERE status = 'pending';
CREATE INDEX idx_activity_recent ON workspace_activity_logs(workspace_id, created_at) WHERE created_at > NOW() - INTERVAL '30 days';

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for workspace member details with user information
CREATE VIEW workspace_member_details AS
SELECT 
    wm.id,
    wm.workspace_id,
    wm.user_id,
    wm.role,
    wm.status,
    wm.joined_at,
    wm.last_active_at,
    u.email,
    u.username,
    u.full_name,
    u.last_login,
    w.name as workspace_name
FROM workspace_members wm
JOIN users u ON wm.user_id = u.id
JOIN workspaces w ON wm.workspace_id = w.id
WHERE wm.status = 'active';

-- View for workspace statistics
CREATE VIEW workspace_stats AS
SELECT 
    w.id,
    w.name,
    w.owner_id,
    COUNT(DISTINCT wm.user_id) as member_count,
    COUNT(DISTINCT p.id) as project_count,
    COUNT(DISTINCT c.id) as collection_count,
    COUNT(DISTINCT CASE WHEN wm.last_active_at > NOW() - INTERVAL '7 days' THEN wm.user_id END) as active_members_week
FROM workspaces w
LEFT JOIN workspace_members wm ON w.id = wm.workspace_id AND wm.status = 'active'
LEFT JOIN projects p ON w.id = p.workspace_id
LEFT JOIN collections c ON w.id = c.workspace_id
GROUP BY w.id, w.name, w.owner_id;

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Trigger to update workspace activity when members join
DELIMITER $$
CREATE TRIGGER after_member_join
    AFTER INSERT ON workspace_members
    FOR EACH ROW
BEGIN
    INSERT INTO workspace_activity_logs (workspace_id, user_id, action, entity_type, entity_id, details)
    VALUES (NEW.workspace_id, NEW.user_id, 'member_joined', 'member', NEW.id, 
            JSON_OBJECT('role', NEW.role, 'joined_at', NEW.joined_at));
END$$
DELIMITER ;

-- Trigger to update last_activity_at for workspace members
DELIMITER $$
CREATE TRIGGER update_member_activity
    BEFORE UPDATE ON workspace_members
    FOR EACH ROW
BEGIN
    IF NEW.status != OLD.status OR NEW.role != OLD.role THEN
        SET NEW.last_active_at = CURRENT_TIMESTAMP;
    END IF;
END$$
DELIMITER ;

-- =============================================================================
-- SAMPLE DATA FOR TESTING
-- =============================================================================

-- Sample workspace
INSERT INTO workspaces (name, description, slug, owner_id, settings) VALUES
('Acme API Team', 'Main workspace for Acme Corp API development team', 'acme-api-team', 1, 
 '{"default_visibility": "workspace", "enable_notifications": true, "auto_save": true}');

-- Sample members (assuming user IDs 1-5 exist)
INSERT INTO workspace_members (workspace_id, user_id, role, status) VALUES
(1, 1, 'owner', 'active'),
(1, 2, 'admin', 'active'),
(1, 3, 'developer', 'active'),
(1, 4, 'developer', 'active'),
(1, 5, 'viewer', 'active');

-- Sample invitation
INSERT INTO workspace_invitations (workspace_id, invited_by_user_id, email, role, invitation_token, expires_at) VALUES
(1, 1, 'newdev@acme.com', 'developer', 'inv_' || LOWER(HEX(RANDOM_BYTES(16))), NOW() + INTERVAL '7 days');