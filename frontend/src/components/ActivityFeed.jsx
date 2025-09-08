/**
 * Activity Feed Component
 * Real-time activity feed showing workspace events and collaboration
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Menu,
  MenuItem,
  Divider,
  Skeleton,
  Alert
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Person as PersonIcon,
  Group as GroupIcon,
  Folder as ProjectIcon,
  Collection as CollectionIcon,
  Settings as SettingsIcon,
  Share as ShareIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Email as EmailIcon,
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow, format } from 'date-fns';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { workspaceAPI } from '../utils/api';

const ActivityFeed = ({ maxHeight = 600, showFilters = true }) => {
  const { currentWorkspace } = useWorkspace();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterAnchor, setFilterAnchor] = useState(null);
  const [filters, setFilters] = useState({
    actions: [],
    users: [],
    timeRange: 'all'
  });
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    if (currentWorkspace?.id) {
      loadActivities(true);
    }
  }, [currentWorkspace?.id]);

  const loadActivities = useCallback(async (reset = false) => {
    if (!currentWorkspace?.id) return;

    setLoading(true);
    setError(null);

    try {
      const offset = reset ? 0 : activities.length;
      const data = await workspaceAPI.getActivity(currentWorkspace.id, {
        limit: 20,
        offset
      });

      if (reset) {
        setActivities(data);
        setPage(0);
      } else {
        setActivities(prev => [...prev, ...data]);
      }

      setHasMore(data.length === 20);
      setPage(prev => prev + 1);
    } catch (error) {
      console.error('Failed to load activities:', error);
      setError('Failed to load activity feed');
    } finally {
      setLoading(false);
    }
  }, [currentWorkspace?.id, activities.length]);

  const handleRefresh = () => {
    loadActivities(true);
  };

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      loadActivities(false);
    }
  };

  const getActivityIcon = (action, entityType) => {
    const iconMap = {
      // Member actions
      member_joined: <GroupIcon />,
      member_invited: <EmailIcon />,
      member_updated: <EditIcon />,
      member_removed: <DeleteIcon />,
      invitation_accepted: <CheckIcon />,
      
      // Project actions
      project_created: <AddIcon />,
      project_updated: <EditIcon />,
      project_deleted: <DeleteIcon />,
      project_shared: <ShareIcon />,
      
      // Collection actions
      collection_created: <CollectionIcon />,
      collection_updated: <EditIcon />,
      collection_shared: <ShareIcon />,
      
      // Workspace actions
      workspace_created: <AddIcon />,
      workspace_updated: <SettingsIcon />,
      
      // Collaboration actions
      resource_shared: <ShareIcon />,
      role_created: <SecurityIcon />,
      role_updated: <SecurityIcon />
    };

    return iconMap[action] || <CodeIcon />;
  };

  const getActivityColor = (action) => {
    const colorMap = {
      // Create actions - green
      member_joined: '#10B981',
      project_created: '#10B981',
      collection_created: '#10B981',
      workspace_created: '#10B981',
      invitation_accepted: '#10B981',
      
      // Update actions - blue
      member_updated: '#3B82F6',
      project_updated: '#3B82F6',
      collection_updated: '#3B82F6',
      workspace_updated: '#3B82F6',
      
      // Share actions - purple
      project_shared: '#8B5CF6',
      collection_shared: '#8B5CF6',
      resource_shared: '#8B5CF6',
      
      // Delete/Remove actions - red
      member_removed: '#EF4444',
      project_deleted: '#EF4444',
      
      // Invite actions - orange
      member_invited: '#F59E0B',
      
      // Security actions - indigo
      role_created: '#6366F1',
      role_updated: '#6366F1'
    };

    return colorMap[action] || '#6B7280';
  };

  const formatActivityMessage = (activity) => {
    const { action, entity_type, details, user_name } = activity;
    const userName = user_name || 'Someone';

    const messages = {
      member_joined: `${userName} joined the workspace`,
      member_invited: `${userName} invited ${details?.email} to join as ${details?.role}`,
      member_updated: `${userName} updated member role`,
      member_removed: `${userName} removed a team member`,
      invitation_accepted: `${userName} accepted the workspace invitation`,
      
      project_created: `${userName} created project \"${details?.name}\"`,
      project_updated: `${userName} updated a project`,
      project_deleted: `${userName} deleted a project`,
      project_shared: `${userName} shared a project with the team`,
      
      collection_created: `${userName} created collection \"${details?.name}\"`,
      collection_updated: `${userName} updated a collection`,
      collection_shared: `${userName} shared a collection`,
      
      workspace_created: `${userName} created the workspace`,
      workspace_updated: `${userName} updated workspace settings`,
      
      resource_shared: `${userName} shared a ${entity_type} with team members`,
      role_created: `${userName} created a custom role`,
      role_updated: `${userName} updated role permissions`
    };

    return messages[action] || `${userName} performed ${action} on ${entity_type}`;
  };

  const getRelativeTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = (now - date) / (1000 * 60 * 60);

    if (diffHours < 24) {
      return formatDistanceToNow(date, { addSuffix: true });
    } else {
      return format(date, 'MMM d, yyyy');
    }
  };

  if (!currentWorkspace) {
    return (
      <Card>
        <CardContent>
          <Typography variant=\"h6\" color=\"text.secondary\" align=\"center\">
            Select a workspace to view activity
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant=\"h6\" component=\"h2\">
            Team Activity
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {showFilters && (
              <IconButton
                size=\"small\"
                onClick={(e) => setFilterAnchor(e.currentTarget)}
              >
                <FilterIcon />
              </IconButton>
            )}
            <IconButton
              size=\"small\"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>

        {error && (
          <Alert severity=\"error\" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
      </CardContent>

      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <List
          sx={{
            height: '100%',
            overflow: 'auto',
            maxHeight: maxHeight,
            px: 2,
            py: 0
          }}
        >
          <AnimatePresence>
            {activities.map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
              >
                <ListItem
                  alignItems=\"flex-start\"
                  sx={{
                    px: 0,
                    py: 1.5,
                    '&:hover': {
                      bgcolor: 'action.hover',
                      borderRadius: 1
                    }
                  }}
                >
                  <ListItemAvatar>
                    <Avatar
                      sx={{
                        bgcolor: getActivityColor(activity.action),
                        width: 36,
                        height: 36
                      }}
                    >
                      {getActivityIcon(activity.action, activity.entity_type)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Typography variant=\"body2\" component=\"div\">
                        {formatActivityMessage(activity)}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Typography variant=\"caption\" color=\"text.secondary\">
                          {getRelativeTime(activity.created_at)}
                        </Typography>
                        {activity.entity_type && (
                          <Chip
                            label={activity.entity_type}
                            size=\"small\"
                            variant=\"outlined\"
                            sx={{ height: 18, fontSize: 10 }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                {index < activities.length - 1 && <Divider variant=\"inset\" component=\"li\" />}
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <Box sx={{ px: 2 }}>
              {[...Array(3)].map((_, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 2, py: 2 }}>
                  <Skeleton variant=\"circular\" width={36} height={36} />
                  <Box sx={{ flex: 1 }}>
                    <Skeleton variant=\"text\" width=\"70%\" />
                    <Skeleton variant=\"text\" width=\"40%\" />
                  </Box>
                </Box>
              ))}
            </Box>
          )}

          {!loading && activities.length === 0 && (
            <ListItem>
              <ListItemText
                primary={
                  <Typography variant=\"body2\" color=\"text.secondary\" align=\"center\">
                    No activity yet
                  </Typography>
                }
                secondary={
                  <Typography variant=\"caption\" color=\"text.secondary\" align=\"center\">
                    Team activity will appear here as members collaborate
                  </Typography>
                }
              />
            </ListItem>
          )}

          {hasMore && !loading && activities.length > 0 && (
            <ListItem>
              <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
                <Button
                  variant=\"outlined\"
                  onClick={handleLoadMore}
                  size=\"small\"
                >
                  Load More
                </Button>
              </Box>
            </ListItem>
          )}
        </List>
      </Box>

      {/* Filter Menu */}
      <Menu
        anchorEl={filterAnchor}
        open={Boolean(filterAnchor)}
        onClose={() => setFilterAnchor(null)}
        PaperProps={{ sx: { minWidth: 200 } }}
      >
        <MenuItem onClick={() => setFilterAnchor(null)}>
          <Typography variant=\"body2\" fontWeight={500}>
            Filter by Action
          </Typography>
        </MenuItem>
        <Divider />
        <MenuItem>Member Actions</MenuItem>
        <MenuItem>Project Actions</MenuItem>
        <MenuItem>Collection Actions</MenuItem>
        <MenuItem>Settings Actions</MenuItem>
        <Divider />
        <MenuItem onClick={() => setFilterAnchor(null)}>
          Clear Filters
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default ActivityFeed;