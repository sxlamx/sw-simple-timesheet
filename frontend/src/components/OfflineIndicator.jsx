import React, { useState, useEffect } from 'react';
import {
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  CloudOff as OfflineIcon,
  Cloud as OnlineIcon,
  Sync as SyncIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import offlineService from '../services/offlineService';

function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [syncStatus, setSyncStatus] = useState({
    isOnline: true,
    pendingActions: 0,
    lastSyncAttempt: null
  });
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const updateOnlineStatus = () => {
      setIsOnline(navigator.onLine);
      updateSyncStatus();
    };

    const updateSyncStatus = async () => {
      const status = await offlineService.getSyncStatus();
      setSyncStatus(status);
    };

    // Set up event listeners
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Initial status check
    updateSyncStatus();

    // Periodic status updates
    const interval = setInterval(updateSyncStatus, 30000); // Every 30 seconds

    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
      clearInterval(interval);
    };
  }, []);

  const handleSync = async () => {
    if (!isOnline) return;
    
    setSyncing(true);
    try {
      await offlineService.forcSync();
      const status = await offlineService.getSyncStatus();
      setSyncStatus(status);
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(false);
    }
  };

  const getStatusColor = () => {
    if (!isOnline) return 'error';
    if (syncStatus.pendingActions > 0) return 'warning';
    return 'success';
  };

  const getStatusText = () => {
    if (!isOnline) return 'Offline';
    if (syncStatus.pendingActions > 0) return `${syncStatus.pendingActions} pending`;
    return 'Online';
  };

  const getStatusIcon = () => {
    if (syncing) return <CircularProgress size={16} />;
    if (!isOnline) return <OfflineIcon />;
    if (syncStatus.pendingActions > 0) return <SyncIcon />;
    return <OnlineIcon />;
  };

  return (
    <>
      <Chip
        icon={getStatusIcon()}
        label={getStatusText()}
        color={getStatusColor()}
        variant={isOnline ? 'outlined' : 'filled'}
        size="small"
        onClick={() => setDialogOpen(true)}
        sx={{ cursor: 'pointer' }}
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getStatusIcon()}
            Connection Status
          </Box>
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Alert 
              severity={isOnline ? (syncStatus.pendingActions > 0 ? 'warning' : 'success') : 'error'}
              sx={{ mb: 2 }}
            >
              {isOnline ? (
                syncStatus.pendingActions > 0 ? (
                  `You're online but have ${syncStatus.pendingActions} pending actions that need to sync.`
                ) : (
                  'You\'re online and all data is synced.'
                )
              ) : (
                'You\'re offline. Changes will be saved locally and synced when connection is restored.'
              )}
            </Alert>

            <List dense>
              <ListItem>
                <ListItemIcon>
                  {isOnline ? <OnlineIcon color="success" /> : <OfflineIcon color="error" />}
                </ListItemIcon>
                <ListItemText
                  primary="Network Status"
                  secondary={isOnline ? 'Connected' : 'Disconnected'}
                />
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  <SyncIcon color={syncStatus.pendingActions > 0 ? 'warning' : 'success'} />
                </ListItemIcon>
                <ListItemText
                  primary="Pending Actions"
                  secondary={`${syncStatus.pendingActions} actions waiting to sync`}
                />
              </ListItem>

              {syncStatus.lastSyncAttempt && (
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="info" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Last Sync Attempt"
                    secondary={new Date(syncStatus.lastSyncAttempt).toLocaleString()}
                  />
                </ListItem>
              )}
            </List>

            {!isOnline && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Working Offline:</strong>
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  • You can view cached timesheets
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  • New timesheets will be saved locally
                </Typography>
                <Typography variant="body2">
                  • Changes will sync automatically when you're back online
                </Typography>
              </Box>
            )}

            {isOnline && syncStatus.pendingActions > 0 && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Sync Required:</strong>
                </Typography>
                <Typography variant="body2">
                  You have offline changes that need to be synced with the server.
                  This usually happens automatically, but you can force sync now.
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Close
          </Button>
          {isOnline && syncStatus.pendingActions > 0 && (
            <Button
              variant="contained"
              onClick={handleSync}
              disabled={syncing}
              startIcon={syncing ? <CircularProgress size={16} /> : <SyncIcon />}
            >
              {syncing ? 'Syncing...' : 'Sync Now'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
}

export default OfflineIndicator;