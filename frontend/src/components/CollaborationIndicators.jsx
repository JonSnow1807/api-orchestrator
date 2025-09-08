/**
 * Collaboration Indicators Component
 * Shows real-time collaboration indicators including active users, cursors, and typing status
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Avatar,
  AvatarGroup,
  Chip,
  Tooltip,
  Badge,
  Typography,
  Popover,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  IconButton,
  Zoom,
  Fade
} from '@mui/material';
import {
  Circle as CircleIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Lock as LockIcon,
  Group as GroupIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useCollaboration } from '../hooks/useCollaboration';

const CollaborationIndicators = ({ 
  resourceId,
  resourceType,
  showDetailed = true,
  maxAvatars = 5,
  sx = {}
}) => {
  const { currentWorkspace } = useWorkspace();
  const { 
    activeUsers, 
    userPresence, 
    resourceLocks, 
    collaborationCursors,
    typingUsers,
    isConnected 
  } = useCollaboration(currentWorkspace?.id, resourceId);

  const [presencePopover, setPresencePopover] = useState(null);
  const [hoveredUser, setHoveredUser] = useState(null);

  // Get users actively viewing this resource
  const activeViewers = activeUsers.filter(user => 
    userPresence[user.id]?.current_resource === resourceId &&
    userPresence[user.id]?.status === 'active'
  );

  // Get resource lock status
  const resourceLock = resourceLocks[resourceId];
  const isLocked = Boolean(resourceLock);
  const lockedByCurrentUser = resourceLock?.user_id === getCurrentUserId();

  // Get typing users for this resource
  const currentlyTyping = typingUsers.filter(typing => 
    typing.resource_id === resourceId
  );

  const getCurrentUserId = () => {
    // Get current user ID from your auth context
    // This is a placeholder - implement based on your auth system
    return null;
  };

  const getStatusColor = (status) => {
    const colors = {
      active: '#10B981',
      idle: '#F59E0B',
      away: '#6B7280'
    };
    return colors[status] || '#6B7280';
  };

  const getStatusText = (status) => {
    const texts = {
      active: 'Active',
      idle: 'Idle',
      away: 'Away'
    };
    return texts[status] || 'Unknown';
  };

  const handlePresenceClick = (event) => {
    setPresencePopover(event.currentTarget);
  };

  const handlePresenceClose = () => {
    setPresencePopover(null);
  };

  if (!currentWorkspace || !isConnected) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ...sx }}>
      {/* Resource Lock Indicator */}
      <AnimatePresence>
        {isLocked && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2 }}
          >
            <Tooltip 
              title={
                lockedByCurrentUser 
                  ? `You are editing this ${resourceType}`
                  : `Being edited by ${resourceLock?.user_name || 'someone'}`
              }
            >
              <Chip
                icon={<LockIcon />}
                label={lockedByCurrentUser ? 'Editing' : 'Locked'}
                color={lockedByCurrentUser ? 'primary' : 'warning'}
                size=\"small\"
                variant={lockedByCurrentUser ? 'filled' : 'outlined'}
                sx={{ 
                  height: 24,
                  fontSize: 11,
                  '& .MuiChip-icon': { fontSize: 14 }
                }}
              />
            </Tooltip>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Typing Indicators */}
      <AnimatePresence>
        {currentlyTyping.length > 0 && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.2 }}
          >
            <Chip
              icon={<EditIcon />}
              label={
                currentlyTyping.length === 1
                  ? `${currentlyTyping[0].user_name} is typing...`
                  : `${currentlyTyping.length} people are typing...`
              }
              color=\"info\"
              size=\"small\"
              variant=\"outlined\"
              sx={{
                height: 24,
                fontSize: 11,
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': { opacity: 1 },
                  '50%': { opacity: 0.7 },
                  '100%': { opacity: 1 }
                }
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Active Viewers */}
      {activeViewers.length > 0 && (
        <Tooltip 
          title={`${activeViewers.length} ${activeViewers.length === 1 ? 'person' : 'people'} viewing`}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={handlePresenceClick}>
            <AvatarGroup 
              max={maxAvatars} 
              sx={{ 
                '& .MuiAvatar-root': { 
                  width: 24, 
                  height: 24, 
                  fontSize: 11,
                  border: '1px solid',
                  borderColor: 'background.paper'
                }
              }}
            >
              {activeViewers.map((user) => {
                const presence = userPresence[user.id];
                const statusColor = getStatusColor(presence?.status);
                
                return (
                  <Badge
                    key={user.id}
                    overlap=\"circular\"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    badgeContent={
                      <CircleIcon 
                        sx={{ 
                          fontSize: 8, 
                          color: statusColor,
                          backgroundColor: 'background.paper',
                          borderRadius: '50%',
                          padding: '1px'
                        }} 
                      />
                    }
                  >
                    <Avatar
                      sx={{
                        bgcolor: presence?.color || 'primary.main',
                        fontSize: 11
                      }}
                      onMouseEnter={() => setHoveredUser(user)}
                      onMouseLeave={() => setHoveredUser(null)}
                    >
                      {user.name?.charAt(0)?.toUpperCase() || user.email?.charAt(0)?.toUpperCase()}
                    </Avatar>
                  </Badge>
                );
              })}
            </AvatarGroup>
            
            {showDetailed && activeViewers.length > 0 && (
              <ViewIcon 
                sx={{ 
                  ml: 0.5, 
                  fontSize: 16, 
                  color: 'text.secondary' 
                }} 
              />
            )}
          </Box>
        </Tooltip>
      )}

      {/* Connection Status */}
      {!isConnected && (
        <Tooltip title=\"Real-time collaboration disconnected\">
          <Chip
            icon={<CircleIcon sx={{ color: '#EF4444' }} />}
            label=\"Offline\"
            size=\"small\"
            variant=\"outlined\"
            color=\"error\"
            sx={{ height: 24, fontSize: 11 }}
          />
        </Tooltip>
      )}

      {/* Presence Details Popover */}
      <Popover
        open={Boolean(presencePopover)}
        anchorEl={presencePopover}
        onClose={handlePresenceClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        PaperProps={{
          sx: { minWidth: 280, maxWidth: 400 }
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant=\"h6\" gutterBottom>
            <GroupIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Active Collaborators
          </Typography>
          
          <List dense>
            {activeViewers.map((user) => {
              const presence = userPresence[user.id];
              const lastSeen = presence?.last_seen ? new Date(presence.last_seen) : null;
              
              return (
                <ListItem key={user.id} disableGutters>
                  <ListItemAvatar>
                    <Badge
                      overlap=\"circular\"
                      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                      badgeContent={
                        <CircleIcon 
                          sx={{ 
                            fontSize: 12, 
                            color: getStatusColor(presence?.status),
                            backgroundColor: 'background.paper',
                            borderRadius: '50%',
                            padding: '1px'
                          }} 
                        />
                      }
                    >
                      <Avatar
                        sx={{
                          width: 32,
                          height: 32,
                          bgcolor: presence?.color || 'primary.main'
                        }}
                      >
                        {user.name?.charAt(0)?.toUpperCase() || user.email?.charAt(0)?.toUpperCase()}
                      </Avatar>
                    </Badge>
                  </ListItemAvatar>
                  <ListItemText
                    primary={user.name || user.email}
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={getStatusText(presence?.status)}
                          size=\"small\"
                          variant=\"outlined\"
                          sx={{ height: 18, fontSize: 10 }}
                        />
                        {lastSeen && (
                          <Typography variant=\"caption\" color=\"text.secondary\">
                            {formatDistanceToNow(lastSeen, { addSuffix: true })}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              );
            })}
          </List>
          
          {activeViewers.length === 0 && (
            <Typography variant=\"body2\" color=\"text.secondary\" align=\"center\" sx={{ py: 2 }}>
              No one else is currently viewing this {resourceType}
            </Typography>
          )}
        </Box>
      </Popover>

      {/* Hover Tooltip for User Details */}
      {hoveredUser && (
        <Zoom in={Boolean(hoveredUser)}>
          <Box
            sx={{
              position: 'absolute',
              top: -40,
              left: 0,
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 1,
              boxShadow: 2,
              zIndex: 1000,
              pointerEvents: 'none'
            }}
          >
            <Typography variant=\"caption\" fontWeight={500}>
              {hoveredUser.name || hoveredUser.email}
            </Typography>
            <br />
            <Typography variant=\"caption\" color=\"text.secondary\">
              {getStatusText(userPresence[hoveredUser.id]?.status)}
            </Typography>
          </Box>
        </Zoom>
      )}
    </Box>
  );
};

export default CollaborationIndicators;