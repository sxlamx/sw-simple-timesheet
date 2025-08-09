import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
  CircularProgress,
  Link,
  Divider,
  Tabs,
  Tab
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Schedule as ScheduleIcon,
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
  Pending as PendingIcon,
  Send as SendIcon,
  OpenInNew as OpenInNewIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import { useAuth } from '../contexts/AuthContext';
import { timesheetsAPI } from '../services/api';
import AnalyticsChart from '../components/AnalyticsChart';
import notificationService from '../services/notificationService';
import offlineService from '../services/offlineService';

function StaffDashboard() {
  const { user } = useAuth();
  const [timesheets, setTimesheets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedYear, setSelectedYear] = useState(dayjs().year());
  const [selectedMonth, setSelectedMonth] = useState(dayjs().month() + 1);
  const [creating, setCreating] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [submitting, setSubmitting] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [analyticsData, setAnalyticsData] = useState([]);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [stats, setStats] = useState({
    currentMonthHours: 0,
    approvedCount: 0,
    pendingCount: 0,
    rejectedCount: 0
  });

  useEffect(() => {
    fetchTimesheets();
    fetchAnalytics();
    // Request notification permission
    notificationService.requestPermission();
  }, []);

  useEffect(() => {
    calculateStats();
  }, [timesheets]);

  const fetchTimesheets = async () => {
    try {
      setLoading(true);
      
      if (!navigator.onLine) {
        // Load from offline storage
        const offlineTimesheets = await offlineService.getTimesheetsOffline(user?.id);
        setTimesheets(offlineTimesheets);
        showSnackbar('Loaded cached timesheets (offline)', 'info');
        return;
      }
      
      const response = await timesheetsAPI.getUserTimesheets();
      setTimesheets(response.data);
      
      // Store in offline cache
      await offlineService.storeTimesheetsOffline(response.data);
      
    } catch (error) {
      // Try to load from offline storage as fallback
      try {
        const offlineTimesheets = await offlineService.getTimesheetsOffline(user?.id);
        if (offlineTimesheets && offlineTimesheets.length > 0) {
          setTimesheets(offlineTimesheets);
          showSnackbar('Loaded cached timesheets (connection failed)', 'warning');
        } else {
          showSnackbar('Failed to fetch timesheets and no cached data available', 'error');
        }
      } catch (offlineError) {
        showSnackbar('Failed to fetch timesheets', 'error');
      }
      console.error('Error fetching timesheets:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = () => {
    const currentMonth = dayjs().month() + 1;
    const currentYear = dayjs().year();
    
    let currentMonthHours = 0;
    let approvedCount = 0;
    let pendingCount = 0;
    let rejectedCount = 0;

    timesheets.forEach(timesheet => {
      const periodStart = dayjs(timesheet.period_start);
      
      if (periodStart.year() === currentYear && periodStart.month() + 1 === currentMonth) {
        currentMonthHours = timesheet.total_hours || 0;
      }

      switch (timesheet.status) {
        case 'approved':
          approvedCount++;
          break;
        case 'pending':
          pendingCount++;
          break;
        case 'rejected':
          rejectedCount++;
          break;
      }
    });

    setStats({
      currentMonthHours,
      approvedCount,
      pendingCount,
      rejectedCount
    });
  };

  const handleCreateTimesheet = async () => {
    try {
      setCreating(true);
      
      if (!navigator.onLine) {
        // Create timesheet offline
        const offlineTimesheet = await offlineService.createTimesheetOffline({
          year: selectedYear,
          month: selectedMonth,
          user_id: user.id
        });
        
        // Add to local state
        setTimesheets(prev => [offlineTimesheet, ...prev]);
        showSnackbar('Timesheet created offline - will sync when online', 'info');
        setCreateDialogOpen(false);
        return;
      }
      
      const response = await timesheetsAPI.createTimesheet(selectedYear, selectedMonth);
      
      showSnackbar('Timesheet created successfully!', 'success');
      setCreateDialogOpen(false);
      
      // Refresh timesheets
      await fetchTimesheets();
      
    } catch (error) {
      // Check if this is a network error
      if (!navigator.onLine) {
        // Handle as offline creation
        const offlineTimesheet = await offlineService.createTimesheetOffline({
          year: selectedYear,
          month: selectedMonth,
          user_id: user.id
        });
        
        setTimesheets(prev => [offlineTimesheet, ...prev]);
        showSnackbar('Created offline - will sync when connection is restored', 'warning');
        setCreateDialogOpen(false);
      } else {
        const errorMessage = error.response?.data?.detail || 'Failed to create timesheet';
        showSnackbar(errorMessage, 'error');
        console.error('Error creating timesheet:', error);
      }
    } finally {
      setCreating(false);
    }
  };

  const handleSubmitTimesheet = async (timesheetId) => {
    try {
      setSubmitting(timesheetId);
      
      if (!navigator.onLine) {
        // Submit offline
        await offlineService.submitTimesheetOffline(timesheetId);
        
        // Update local state
        setTimesheets(prev => 
          prev.map(ts => 
            ts.id === timesheetId 
              ? { ...ts, status: 'pending', submitted_at: new Date().toISOString() }
              : ts
          )
        );
        
        showSnackbar('Timesheet queued for submission - will sync when online', 'info');
        return;
      }
      
      await timesheetsAPI.submitTimesheet(timesheetId);
      
      showSnackbar('Timesheet submitted for approval!', 'success');
      
      // Refresh timesheets
      await fetchTimesheets();
      
    } catch (error) {
      if (!navigator.onLine) {
        // Handle as offline submission
        await offlineService.submitTimesheetOffline(timesheetId);
        setTimesheets(prev => 
          prev.map(ts => 
            ts.id === timesheetId 
              ? { ...ts, status: 'pending', submitted_at: new Date().toISOString() }
              : ts
          )
        );
        showSnackbar('Queued for submission - will sync when connection is restored', 'warning');
      } else {
        const errorMessage = error.response?.data?.detail || 'Failed to submit timesheet';
        showSnackbar(errorMessage, 'error');
        console.error('Error submitting timesheet:', error);
      }
    } finally {
      setSubmitting(null);
    }
  };

  const handleExportTimesheet = async (timesheet) => {
    try {
      const response = await timesheetsAPI.exportTimesheet(timesheet.id);
      
      // Create blob from response
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename
      const period = dayjs(timesheet.period_start).format('YYYY-MM');
      link.download = `timesheet_${user?.email}_${period}.xlsx`;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showSnackbar('Timesheet exported successfully!', 'success');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to export timesheet';
      showSnackbar(errorMessage, 'error');
      console.error('Error exporting timesheet:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setAnalyticsLoading(true);
      const response = await timesheetsAPI.getMonthlyAnalytics(6);
      setAnalyticsData(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  // Check for draft timesheets and show browser notifications
  useEffect(() => {
    if (timesheets.length > 0) {
      notificationService.checkAndNotifyOverdue(timesheets, 'staff');
    }
  }, [timesheets]);

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false, message: '', severity: 'info' });
  };

  const formatPeriod = (timesheet) => {
    const start = dayjs(timesheet.period_start);
    return start.format('MMM YYYY');
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return dayjs(dateString).format('MMM DD, YYYY');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <ApprovedIcon color="success" />;
      case 'rejected': return <RejectedIcon color="error" />;
      case 'pending': return <PendingIcon color="warning" />;
      default: return <ScheduleIcon />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'success';
      case 'rejected': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const canSubmit = (timesheet) => {
    return timesheet.status === 'draft';
  };

  const canEdit = (timesheet) => {
    return timesheet.status === 'draft' || timesheet.status === 'rejected';
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Container maxWidth="lg">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            My Timesheet
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Welcome back, {user?.full_name}! Manage your timesheet entries and track approval status.
          </Typography>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <ScheduleIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">This Month</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {stats.currentMonthHours}h
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Current period hours
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <ApprovedIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Approved</Typography>
                </Box>
                <Typography variant="h4" color="success.main">
                  {stats.approvedCount}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Approved timesheets
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <PendingIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">Pending</Typography>
                </Box>
                <Typography variant="h4" color="warning.main">
                  {stats.pendingCount}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Awaiting approval
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <RejectedIcon color="error" sx={{ mr: 1 }} />
                  <Typography variant="h6">Rejected</Typography>
                </Box>
                <Typography variant="h4" color="error.main">
                  {stats.rejectedCount}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Needs revision
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab icon={<ScheduleIcon />} label="My Timesheets" />
            <Tab icon={<AnalyticsIcon />} label="Analytics" />
          </Tabs>

          {/* Timesheets Tab */}
          {tabValue === 0 && (
            <Box>
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">My Timesheets ({timesheets.length})</Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  New Timesheet
                </Button>
              </Box>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Period</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Total Hours</TableCell>
                  <TableCell>Submitted</TableCell>
                  <TableCell>Reviewed</TableCell>
                  <TableCell>Google Sheet</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {timesheets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                      <Typography variant="body1" color="text.secondary">
                        No timesheets found. Create your first timesheet to get started!
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  timesheets.map((timesheet) => (
                    <TableRow key={timesheet.id}>
                      <TableCell>{formatPeriod(timesheet)}</TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(timesheet.status)}
                          label={timesheet.status.toUpperCase()}
                          color={getStatusColor(timesheet.status)}
                          variant="outlined"
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {timesheet.total_hours ? `${timesheet.total_hours}h` : '-'}
                      </TableCell>
                      <TableCell>{formatDate(timesheet.submitted_at)}</TableCell>
                      <TableCell>{formatDate(timesheet.reviewed_at)}</TableCell>
                      <TableCell>
                        {timesheet.google_sheet_url && (
                          <Link
                            href={timesheet.google_sheet_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
                          >
                            View Sheet <OpenInNewIcon fontSize="small" />
                          </Link>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {canSubmit(timesheet) && (
                            <Tooltip title="Submit for Approval">
                              <IconButton 
                                size="small" 
                                color="primary"
                                onClick={() => handleSubmitTimesheet(timesheet.id)}
                                disabled={submitting === timesheet.id}
                              >
                                {submitting === timesheet.id ? (
                                  <CircularProgress size={20} />
                                ) : (
                                  <SendIcon />
                                )}
                              </IconButton>
                            </Tooltip>
                          )}
                          
                          {canEdit(timesheet) && timesheet.google_sheet_url && (
                            <Tooltip title="Edit in Google Sheets">
                              <IconButton 
                                size="small"
                                color="secondary"
                                onClick={() => window.open(timesheet.google_sheet_url, '_blank')}
                              >
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          
                          <Tooltip title="View Details">
                            <IconButton size="small">
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title="Export to Excel">
                            <IconButton 
                              size="small"
                              onClick={() => handleExportTimesheet(timesheet)}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
            </Box>
          )}

          {/* Analytics Tab */}
          {tabValue === 1 && (
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                My Timesheet Analytics (Last 6 Months)
              </Typography>
              
              {analyticsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Hours Worked Over Time
                        </Typography>
                        <AnalyticsChart 
                          type="line" 
                          data={analyticsData} 
                          height={300}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Monthly Breakdown
                        </Typography>
                        <AnalyticsChart 
                          type="bar" 
                          data={analyticsData} 
                          height={300}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Status Distribution
                        </Typography>
                        {analyticsData.length > 0 && (
                          <AnalyticsChart 
                            type="pie" 
                            data={[
                              { name: 'Approved', value: analyticsData.reduce((sum, item) => sum + item.approved_count, 0) },
                              { name: 'Submitted', value: analyticsData.reduce((sum, item) => sum + (item.submitted_count - item.approved_count), 0) },
                              { name: 'Total Timesheets', value: analyticsData.reduce((sum, item) => sum + item.timesheets, 0) }
                            ]}
                            height={300}
                          />
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              )}
            </Box>
          )}
        </Paper>

        {/* Create Timesheet Dialog */}
        <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create New Timesheet</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Year</InputLabel>
                  <Select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(e.target.value)}
                    label="Year"
                  >
                    {Array.from({ length: 5 }, (_, i) => dayjs().year() - 2 + i).map(year => (
                      <MenuItem key={year} value={year}>{year}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Month</InputLabel>
                  <Select
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                    label="Month"
                  >
                    {Array.from({ length: 12 }, (_, i) => i + 1).map(month => (
                      <MenuItem key={month} value={month}>
                        {dayjs().month(month - 1).format('MMMM')}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Alert severity="info">
                  A new Google Sheet will be created in your Google Drive for this timesheet period. 
                  You can edit it directly in Google Sheets and then submit it for approval.
                </Alert>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)} disabled={creating}>
              Cancel
            </Button>
            <Button 
              variant="contained" 
              onClick={handleCreateTimesheet}
              disabled={creating}
              startIcon={creating ? <CircularProgress size={20} /> : <AddIcon />}
            >
              {creating ? 'Creating...' : 'Create Timesheet'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </LocalizationProvider>
  );
}

export default StaffDashboard;