# Team Collaboration System - Complete Implementation Guide

## Overview

This document provides a comprehensive guide for implementing the team collaboration system in the API Orchestrator platform. The system includes workspaces, team management, role-based access control, real-time collaboration, and resource sharing.

## Architecture Overview

### Core Components

1. **Database Layer**: SQLAlchemy models with PostgreSQL/SQLite support
2. **API Layer**: FastAPI REST endpoints with comprehensive RBAC
3. **WebSocket Layer**: Real-time collaboration via WebSocket connections
4. **Frontend Layer**: React components with Material-UI
5. **Permission System**: Granular role-based access control

### Key Features

- ✅ Multi-tenant workspace architecture
- ✅ Role-based permissions (Owner, Admin, Developer, Viewer)
- ✅ Email invitation system with expiration
- ✅ Real-time collaboration with WebSocket
- ✅ Resource sharing and permissions
- ✅ Activity logging and audit trail
- ✅ Presence indicators and cursor sharing
- ✅ Resource locking for collaborative editing

## Database Schema

### Core Tables

1. **workspaces** - Organization/workspace management
2. **workspace_members** - User membership and roles
3. **workspace_invitations** - Invitation management
4. **workspace_roles** - Custom role definitions
5. **collections** - Shared API request collections
6. **workspace_activity_logs** - Activity tracking
7. **active_sessions** - Real-time collaboration sessions
8. **collaboration_events** - Real-time collaboration events
9. **resource_permissions** - Granular resource permissions
10. **workspace_usage_stats** - Analytics and usage metrics

### Relationships

- Users can belong to multiple workspaces
- Each workspace has one owner and multiple members
- Projects and collections belong to workspaces
- Resources can be shared with specific permissions
- All activities are logged for audit purposes

## API Endpoints Reference

### Workspace Management

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|-------------------|
| POST | `/api/v1/workspaces` | Create new workspace | Authenticated user |
| GET | `/api/v1/workspaces` | Get accessible workspaces | Authenticated user |
| GET | `/api/v1/workspaces/{workspace_id}` | Get workspace details | Workspace member |
| PUT | `/api/v1/workspaces/{workspace_id}` | Update workspace | `workspace.write` |
| DELETE | `/api/v1/workspaces/{workspace_id}` | Delete workspace | `workspace.delete` |

### Member Management

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|-------------------|
| GET | `/api/v1/workspaces/{workspace_id}/members` | List workspace members | Workspace member |
| PUT | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | Update member role | `members.manage_roles` |
| DELETE | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | Remove member | `members.remove` |

### Invitation Management

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|-------------------|
| POST | `/api/v1/workspaces/{workspace_id}/invitations` | Invite new member | `members.invite` |
| GET | `/api/v1/workspaces/{workspace_id}/invitations` | List invitations | `members.invite` |
| POST | `/api/v1/workspaces/invitations/{token}/accept` | Accept invitation | Authenticated user |
| DELETE | `/api/v1/workspaces/{workspace_id}/invitations/{invitation_id}` | Revoke invitation | `members.invite` |

### Collection Management

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|-------------------|
| POST | `/api/v1/workspaces/{workspace_id}/collections` | Create collection | `collections.create` |
| GET | `/api/v1/workspaces/{workspace_id}/collections` | List collections | Workspace member |
| PUT | `/api/v1/workspaces/{workspace_id}/collections/{collection_id}` | Update collection | `collections.write` |
| DELETE | `/api/v1/workspaces/{workspace_id}/collections/{collection_id}` | Delete collection | `collections.delete` |

### Activity and Logs

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|-------------------|
| GET | `/api/v1/workspaces/{workspace_id}/activity` | Get activity log | Workspace member |

### Role Management

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|-------------------|
| GET | `/api/v1/workspaces/{workspace_id}/roles` | List available roles | Workspace member |
| POST | `/api/v1/workspaces/{workspace_id}/roles` | Create custom role | `settings.manage` |
| PUT | `/api/v1/workspaces/{workspace_id}/roles/{role_id}` | Update role | `settings.manage` |
| DELETE | `/api/v1/workspaces/{workspace_id}/roles/{role_id}` | Delete role | `settings.manage` |

### Resource Sharing

| Method | Endpoint | Description | Required Permission |
|--------|----------|-------------|-------------------|
| POST | `/api/v1/workspaces/{workspace_id}/share/{resource_type}/{resource_id}` | Share resource | Resource owner or `{resource_type}.share` |
| GET | `/api/v1/workspaces/{workspace_id}/my-permissions` | Get user permissions | Workspace member |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/collaboration/{workspace_id}?token={jwt_token}` | Real-time collaboration WebSocket |

## Permission System

### Role Hierarchy

1. **Owner** - Full workspace control including billing
2. **Admin** - Manage members and content, no billing access
3. **Developer** - Create and edit content, limited sharing
4. **Viewer** - Read-only access to shared content

### Permission Matrix

| Resource | Action | Owner | Admin | Developer | Viewer |
|----------|--------|--------|-------|-----------|---------|
| Workspace | Read | ✅ | ✅ | ✅ | ✅ |
| Workspace | Write | ✅ | ✅ | ❌ | ❌ |
| Workspace | Delete | ✅ | ❌ | ❌ | ❌ |
| Workspace | Billing | ✅ | ❌ | ❌ | ❌ |
| Members | Invite | ✅ | ✅ | ❌ | ❌ |
| Members | Remove | ✅ | ❌ | ❌ | ❌ |
| Members | Manage Roles | ✅ | ✅ | ❌ | ❌ |
| Projects | Create | ✅ | ✅ | ✅ | ❌ |
| Projects | Read | ✅ | ✅ | ✅ | ✅ |
| Projects | Write | ✅ | ✅ | ✅ | ❌ |
| Projects | Delete | ✅ | ✅ | ❌ | ❌ |
| Projects | Share | ✅ | ✅ | ✅ | ❌ |
| Collections | Create | ✅ | ✅ | ✅ | ❌ |
| Collections | Read | ✅ | ✅ | ✅ | ✅ |
| Collections | Write | ✅ | ✅ | ✅ | ❌ |
| Collections | Delete | ✅ | ✅ | ❌ | ❌ |
| Collections | Share | ✅ | ✅ | ✅ | ❌ |
| Settings | Manage | ✅ | ❌ | ❌ | ❌ |

## Real-time Collaboration Features

### WebSocket Message Types

#### Client to Server

```javascript
// Presence update
{
  type: 'presence_update',
  data: {
    status: 'active' | 'idle' | 'away',
    current_resource: 'resource_id',
    resource_type: 'project' | 'collection'
  }
}

// Cursor update
{
  type: 'cursor_update',
  data: {
    resource_id: 'resource_id',
    position: 123,
    selection: { start: 120, end: 130 }
  }
}

// Resource lock request
{
  type: 'resource_lock',
  data: {
    resource_id: 'resource_id'
  }
}

// Typing indicator
{
  type: 'typing_indicator',
  data: {
    resource_id: 'resource_id',
    is_typing: true
  }
}

// Collaboration event
{
  type: 'collaboration_event',
  data: {
    event_type: 'text_change' | 'cursor_move' | 'selection_change',
    resource_type: 'project' | 'collection',
    resource_id: 'resource_id',
    event_data: { /* event specific data */ }
  }
}
```

#### Server to Client

```javascript
// Initial data on connection
{
  type: 'initial_data',
  data: {
    presence: { /* user presence data */ },
    recent_activity: [ /* recent activities */ ],
    active_collaborators: 3,
    your_session: { /* session info */ }
  }
}

// Presence updates
{
  type: 'presence_update',
  data: {
    user_id: 123,
    presence: { /* presence data */ }
  }
}

// Resource lock status
{
  type: 'resource_locked',
  data: {
    resource_id: 'resource_id',
    locked_by: 123,
    user_name: 'John Doe'
  }
}

// Collaboration events
{
  type: 'collaboration_event',
  data: {
    event_type: 'text_change',
    resource_id: 'resource_id',
    user_id: 123,
    event_data: { /* event data */ }
  }
}
```

## Frontend Components

### Key Components

1. **WorkspaceSwitcher** - Workspace selection and creation
2. **TeamManagement** - Complete team management interface
3. **ActivityFeed** - Real-time activity display
4. **CollaborationIndicators** - Show active collaborators
5. **WorkspaceContext** - React context for workspace state
6. **useCollaboration** - Hook for WebSocket collaboration

### Integration Points

```jsx
// App.jsx - Main application setup
import { WorkspaceProvider } from './contexts/WorkspaceContext';
import WorkspaceSwitcher from './components/WorkspaceSwitcher';

function App() {
  return (
    <WorkspaceProvider>
      <Header>
        <WorkspaceSwitcher />
      </Header>
      {/* Rest of app */}
    </WorkspaceProvider>
  );
}

// Project/Collection views - Add collaboration
import CollaborationIndicators from './components/CollaborationIndicators';
import { useCollaboration } from './hooks/useCollaboration';

function ProjectView({ projectId }) {
  const { currentWorkspace } = useWorkspace();
  const collaboration = useCollaboration(currentWorkspace?.id, projectId);
  
  return (
    <div>
      <CollaborationIndicators 
        resourceId={projectId}
        resourceType="project"
      />
      {/* Project content */}
    </div>
  );
}
```

## Implementation Steps

### Backend Implementation

1. **Database Setup**
   ```bash
   # Run the SQL schema
   psql -h localhost -U postgres -d api_orchestrator < team_collaboration_schema.sql
   ```

2. **Add Models to Database Module**
   ```python
   # In src/database.py, add imports:
   from src.team_collaboration_models import *
   
   # Update User model with workspace relationships
   # Update Project model with workspace_id
   ```

3. **Register API Routes**
   ```python
   # In src/main.py
   from src.team_collaboration_api import router as collaboration_router
   from src.team_collaboration_websocket import websocket_collaboration_handler
   
   app.include_router(collaboration_router)
   
   @app.websocket("/ws/collaboration/{workspace_id}")
   async def websocket_endpoint(websocket: WebSocket, workspace_id: int, token: str):
       await websocket_collaboration_handler(websocket, workspace_id, token)
   ```

4. **Email Service Integration**
   ```python
   # Add workspace invitation templates to email service
   # Configure SMTP settings for invitation emails
   ```

### Frontend Implementation

1. **Install Dependencies**
   ```bash
   npm install socket.io-client date-fns
   ```

2. **Add Context Providers**
   ```jsx
   // In App.jsx or main entry point
   import { WorkspaceProvider } from './contexts/WorkspaceContext';
   
   function App() {
     return (
       <AuthProvider>
         <WorkspaceProvider>
           {/* App content */}
         </WorkspaceProvider>
       </AuthProvider>
     );
   }
   ```

3. **Configure API Client**
   ```javascript
   // In utils/api.js
   import { workspaceAPI } from './workspaceAPI';
   
   // Export workspaceAPI for use throughout app
   export { workspaceAPI };
   ```

4. **Add WebSocket Configuration**
   ```javascript
   // In config or environment files
   const config = {
     WS_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
     // Other config...
   };
   ```

### Database Migrations

1. **Create Alembic Migration**
   ```bash
   alembic revision --autogenerate -m "Add team collaboration tables"
   alembic upgrade head
   ```

2. **Initial Data Setup**
   ```python
   # Create script to add default roles
   # Set up initial workspace for existing users
   ```

### Testing

1. **Backend Tests**
   ```python
   # Test workspace CRUD operations
   # Test permission system
   # Test WebSocket connections
   # Test invitation flow
   ```

2. **Frontend Tests**
   ```javascript
   // Test component rendering
   // Test WebSocket connection
   // Test permission checks
   // Test user interactions
   ```

## Security Considerations

### Authentication & Authorization
- JWT token validation for WebSocket connections
- Role-based access control at API level
- Permission checks for all operations
- Invitation token security with expiration

### Data Protection
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention in frontend components
- CORS configuration for API endpoints

### WebSocket Security
- Token-based authentication for WebSocket connections
- Connection rate limiting
- Message validation and sanitization
- Automatic cleanup of stale connections

## Performance Optimizations

### Database
- Proper indexing on frequently queried columns
- Connection pooling for high concurrency
- Query optimization with selective loading
- Regular cleanup of old sessions and logs

### WebSocket
- Connection management with automatic cleanup
- Message batching for high-frequency updates
- Presence debouncing to reduce message volume
- Resource-based message routing

### Frontend
- Component memoization for collaboration indicators
- Debounced typing indicators
- Virtual scrolling for large team lists
- Lazy loading of activity feeds

## Monitoring & Analytics

### Metrics to Track
- Active workspace count
- Real-time collaboration sessions
- Invitation acceptance rates
- Feature usage by role
- WebSocket connection health

### Logging
- All workspace activities logged
- Permission checks logged for audit
- WebSocket connection events
- Error tracking and reporting

## Deployment Considerations

### Environment Variables
```bash
# WebSocket configuration
WS_URL=wss://your-domain.com
WS_HEARTBEAT_INTERVAL=30000

# Email configuration for invitations
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-password
INVITATION_FROM_EMAIL=noreply@your-domain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis for WebSocket scaling (optional)
REDIS_URL=redis://localhost:6379
```

### Infrastructure
- WebSocket support in load balancer
- Sticky sessions if using multiple servers
- Redis for scaling WebSocket connections
- Email service configuration
- Database backup and recovery

This implementation provides a comprehensive team collaboration system that scales from small teams to large organizations while maintaining security, performance, and user experience standards.