import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
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
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Badge,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
  CircularProgress,
  Link
} from '@mui/material';
import {
  Check as ApproveIcon,
  Close as RejectIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
  Pending as PendingIcon,
  Warning as WarningIcon,
  OpenInNew as OpenInNewIcon,
  Analytics as AnalyticsIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import dayjs from 'dayjs';
import { useAuth } from '../contexts/AuthContext';
import { timesheetsAPI, usersAPI, notificationsAPI } from '../services/api';
import AnalyticsChart from '../components/AnalyticsChart';
import notificationService from '../services/notificationService';

function SupervisorDashboard() {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [selectedTimesheet, setSelectedTimesheet] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  
  const [pendingTimesheets, setPendingTimesheets] = useState([]);
  const [allTimesheets, setAllTimesheets] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [analyticsData, setAnalyticsData] = useState([]);
  const [staffBreakdown, setStaffBreakdown] = useState([]);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [notificationDialogOpen, setNotificationDialogOpen] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [stats, setStats] = useState({
    totalTeamMembers: 0,
    pendingCount: 0,
    overdueCount: 0,
    approvedThisMonth: 0,
    currentMonthHours: 0
  });

  useEffect(() => {
    fetchData();
    // Request notification permission
    notificationService.requestPermission();
    // Start periodic checks
    notificationService.startPeriodicChecks();
  }, []);

  // Remove the calculateStats useEffect since we get stats from API

  const fetchData = async () => {
    try {
      setLoading(true);
      const [pendingResponse, teamResponse, allTimesheetsResponse, statsResponse] = await Promise.all([
        timesheetsAPI.getPendingTimesheets(),
        usersAPI.getStaffMembers(),
        timesheetsAPI.getAllTeamTimesheets(),
        timesheetsAPI.getTeamStatistics()
      ]);
      
      // Fetch analytics data
      fetchAnalytics();
      
      setPendingTimesheets(pendingResponse.data);
      setTeamMembers(teamResponse.data);
      setAllTimesheets(allTimesheetsResponse.data);
      setStats({
        totalTeamMembers: statsResponse.data.team_member_count,
        pendingCount: statsResponse.data.pending_count,
        overdueCount: statsResponse.data.overdue_count,
        approvedThisMonth: statsResponse.data.approved_count,
        currentMonthHours: statsResponse.data.current_month_hours
      });
      
    } catch (error) {
      showSnackbar('Failed to fetch data', 'error');
      console.error('Error fetching supervisor data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusFilter = async (status) => {
    setStatusFilter(status);
    try {
      const filterValue = status === 'all' ? null : status;
      const response = await timesheetsAPI.getAllTeamTimesheets(filterValue);
      setAllTimesheets(response.data);
    } catch (error) {
      showSnackbar('Failed to filter timesheets', 'error');
      console.error('Error filtering timesheets:', error);
    }
  };

  const handleReview = (timesheet) => {
    setSelectedTimesheet(timesheet);
    setReviewNotes('');
    setReviewDialogOpen(true);
  };

  const handleApprove = async () => {
    if (!selectedTimesheet) return;
    
    try {
      setProcessing(true);
      await timesheetsAPI.approveTimesheet(selectedTimesheet.id, reviewNotes);
      
      showSnackbar('Timesheet approved successfully!', 'success');
      setReviewDialogOpen(false);
      setSelectedTimesheet(null);
      setReviewNotes('');
      
      // Refresh data
      await fetchData();
      
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to approve timesheet';
      showSnackbar(errorMessage, 'error');
      console.error('Error approving timesheet:', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!selectedTimesheet || !reviewNotes.trim()) {
      showSnackbar('Please provide review notes for rejection', 'warning');
      return;
    }
    
    try {
      setProcessing(true);
      await timesheetsAPI.rejectTimesheet(selectedTimesheet.id, reviewNotes);
      
      showSnackbar('Timesheet rejected', 'info');
      setReviewDialogOpen(false);
      setSelectedTimesheet(null);
      setReviewNotes('');
      
      // Refresh data
      await fetchData();
      
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to reject timesheet';
      showSnackbar(errorMessage, 'error');
      console.error('Error rejecting timesheet:', error);
    } finally {
      setProcessing(false);
    }
  };

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

  const getStaffName = (timesheet) => {
    // Use the enriched data from the API response
    return timesheet.staff_name || 'Unknown Staff';
  };

  // Remove getStaffAvatar since we're using enriched API data

  const getInitials = (name) => {
    return name ? name.split(' ').map(n => n[0]).join('') : '?';
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

  const handleExportIndividual = async (timesheet) => {
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
      const staffName = getStaffName(timesheet).replace(/\s+/g, '_');
      const period = dayjs(timesheet.period_start).format('YYYY-MM');
      link.download = `timesheet_${staffName}_${period}.xlsx`;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showSnackbar('Individual timesheet exported successfully!', 'success');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to export timesheet';
      showSnackbar(errorMessage, 'error');
      console.error('Error exporting individual timesheet:', error);
    }
  };

  const handleExportTeam = async () => {
    try {
      const response = await timesheetsAPI.exportTeamTimesheets();
      
      // Create blob from response
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename
      const currentDate = dayjs().format('YYYY-MM-DD');
      link.download = `team_timesheets_${user?.email}_${currentDate}.xlsx`;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showSnackbar('Team report exported successfully!', 'success');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to export team report';
      showSnackbar(errorMessage, 'error');
      console.error('Error exporting team report:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setAnalyticsLoading(true);
      const [monthlyResponse, staffResponse] = await Promise.all([
        timesheetsAPI.getTeamMonthlyAnalytics(6),
        timesheetsAPI.getStaffBreakdownAnalytics()
      ]);
      setAnalyticsData(monthlyResponse.data);
      setStaffBreakdown(staffResponse.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleSendReminders = async () => {
    try {
      await notificationsAPI.sendReminders();
      showSnackbar('Reminder notifications are being sent', 'success');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to send reminders';
      showSnackbar(errorMessage, 'error');
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail) {
      showSnackbar('Please enter an email address', 'warning');
      return;
    }
    
    try {
      await notificationsAPI.testEmail(testEmail);
      showSnackbar(`Test email sent to ${testEmail}`, 'success');
      setNotificationDialogOpen(false);
      setTestEmail('');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to send test email';
      showSnackbar(errorMessage, 'error');
    }
  };

  // Check for overdue reviews and show browser notifications
  useEffect(() => {
    if (pendingTimesheets.length > 0) {
      notificationService.checkAndNotifyOverdue(pendingTimesheets, 'supervisor');
    }
  }, [pendingTimesheets]);

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
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Supervisor Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Welcome back, {user?.full_name}! Review and approve team timesheet submissions.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<NotificationsIcon />}
              onClick={() => setNotificationDialogOpen(true)}
              size="small"
            >
              Notifications
            </Button>
            <Button
              variant="outlined"
              color="warning"
              onClick={handleSendReminders}
              size="small"
            >
              Send Reminders
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PersonIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Team Members</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {stats.totalTeamMembers}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Direct reports
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Badge badgeContent={stats.pendingCount} color="warning">
                  <PendingIcon color="warning" sx={{ mr: 1 }} />
                </Badge>
                <Typography variant="h6">Pending</Typography>
              </Box>
              <Typography variant="h4" color="warning.main">
                {stats.pendingCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Awaiting review
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WarningIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">Overdue</Typography>
              </Box>
              <Typography variant="h4" color="error.main">
                {stats.overdueCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Overdue submissions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ScheduleIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">This Month</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {stats.currentMonthHours}h
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total hours logged
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label={`Pending Review (${pendingTimesheets.length})`} />
          <Tab label="All Timesheets" />
          <Tab label="Team Members" />
          <Tab label="Analytics" icon={<AnalyticsIcon />} />
        </Tabs>

        {/* Pending Review Tab */}
        {tabValue === 0 && (
          <Box sx={{ p: 2 }}>
            {pendingTimesheets.length === 0 ? (
              <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
                No pending timesheets to review
              </Typography>
            ) : (
              <List>
                {pendingTimesheets.map((timesheet) => (
                  <ListItem key={timesheet.id} divider>
                    <ListItemAvatar>
                      <Avatar 
                        sx={{ bgcolor: 'primary.main' }}
                      >
                        {getInitials(getStaffName(timesheet))}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={getStaffName(timesheet)}
                      secondary={
                        <>
                          <Typography variant="body2" component="span">
                            {timesheet.staff_email} • {formatPeriod(timesheet)} • {timesheet.total_hours || 0} hours • 
                            Submitted {formatDate(timesheet.submitted_at)}
                          </Typography>
                        </>
                      }
                    />
                    <Box sx={{ ml: 2 }}>
                      {timesheet.google_sheet_url && (
                        <Tooltip title="View Google Sheet">
                          <IconButton 
                            onClick={() => window.open(timesheet.google_sheet_url, '_blank')}
                          >
                            <OpenInNewIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Review & Approve/Reject">
                        <IconButton 
                          color="primary"
                          onClick={() => handleReview(timesheet)}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        )}

        {/* All Timesheets Tab */}
        {tabValue === 1 && (
          <Box sx={{ p: 2 }}>
            <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant={statusFilter === 'all' ? 'contained' : 'outlined'}
                onClick={() => handleStatusFilter('all')}
                size="small"
              >
                All ({allTimesheets.length})
              </Button>
              <Button
                variant={statusFilter === 'pending' ? 'contained' : 'outlined'}
                onClick={() => handleStatusFilter('pending')}
                color="warning"
                size="small"
              >
                Pending ({stats.pendingCount})
              </Button>
              <Button
                variant={statusFilter === 'approved' ? 'contained' : 'outlined'}
                onClick={() => handleStatusFilter('approved')}
                color="success"
                size="small"
              >
                Approved
              </Button>
              <Button
                variant={statusFilter === 'rejected' ? 'contained' : 'outlined'}
                onClick={() => handleStatusFilter('rejected')}
                color="error"
                size="small"
              >
                Rejected
              </Button>
              <Button
                variant={statusFilter === 'draft' ? 'contained' : 'outlined'}
                onClick={() => handleStatusFilter('draft')}
                color="info"
                size="small"
              >
                Draft
              </Button>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Staff Member</TableCell>
                    <TableCell>Period</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Total Hours</TableCell>
                    <TableCell>Submitted</TableCell>
                    <TableCell>Reviewed</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                {allTimesheets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                      <Typography variant="body1" color="text.secondary">
                        No timesheets found
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  allTimesheets.map((timesheet) => (
                    <TableRow key={timesheet.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar 
                            sx={{ width: 32, height: 32, mr: 1, bgcolor: 'primary.main' }}
                          >
                            {getInitials(getStaffName(timesheet))}
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {getStaffName(timesheet)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {timesheet.staff_email}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
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
                        <Typography variant="body2" fontWeight="medium">
                          {timesheet.total_hours || 0}h
                        </Typography>
                      </TableCell>
                      <TableCell>{formatDate(timesheet.submitted_at)}</TableCell>
                      <TableCell>
                        <Box>
                          {formatDate(timesheet.reviewed_at)}
                          {timesheet.review_notes && (
                            <Tooltip title={timesheet.review_notes}>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', cursor: 'help' }}>
                                (Has notes)
                              </Typography>
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {timesheet.google_sheet_url && (
                            <Tooltip title="View Google Sheet">
                              <IconButton 
                                size="small"
                                onClick={() => window.open(timesheet.google_sheet_url, '_blank')}
                              >
                                <OpenInNewIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="View Details">
                            <IconButton 
                              size="small" 
                              onClick={() => handleReview(timesheet)}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Export Individual">
                            <IconButton 
                              size="small"
                              onClick={() => handleExportIndividual(timesheet)}
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

        {/* Team Members Tab */}
        {tabValue === 2 && (
          <Box sx={{ p: 2 }}>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">Team Members ({teamMembers.length})</Typography>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={handleExportTeam}
                disabled={teamMembers.length === 0}
              >
                Export Team Report
              </Button>
            </Box>
            {teamMembers.length === 0 ? (
              <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
                No team members found
              </Typography>
            ) : (
              <List>
                {teamMembers.map((member) => (
                  <ListItem key={member.id} divider>
                    <ListItemAvatar>
                      <Avatar 
                        src={member.profile_picture}
                        sx={{ bgcolor: 'primary.main' }}
                      >
                        {getInitials(member.full_name)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={member.full_name}
                      secondary={`${member.email} • ${member.department || 'No department'}`}
                    />
                    <Box sx={{ ml: 2 }}>
                      <Button variant="outlined" size="small">
                        View Timesheets
                      </Button>
                    </Box>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        )}

        {/* Analytics Tab */}
        {tabValue === 3 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Team Analytics (Last 6 Months)
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
                        Team Hours Over Time
                      </Typography>
                      <AnalyticsChart 
                        type="team-bar" 
                        data={analyticsData} 
                        height={350}
                      />
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Team Status Distribution
                      </Typography>
                      {analyticsData.length > 0 && (
                        <AnalyticsChart 
                          type="pie" 
                          data={[
                            { name: 'Approved', value: analyticsData.reduce((sum, item) => sum + item.approved_count, 0) },
                            { name: 'Pending', value: analyticsData.reduce((sum, item) => sum + item.pending_count, 0) },
                            { name: 'Submitted', value: analyticsData.reduce((sum, item) => sum + item.submitted_count, 0) }
                          ]}
                          height={300}
                        />
                      )}
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Staff Performance
                      </Typography>
                      <AnalyticsChart 
                        type="staff-bar" 
                        data={staffBreakdown.slice(0, 8)} 
                        height={300}
                      />
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Staff Performance Breakdown
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Staff Member</TableCell>
                              <TableCell align="right">Total Hours</TableCell>
                              <TableCell align="right">This Month</TableCell>
                              <TableCell align="right">Total Timesheets</TableCell>
                              <TableCell align="right">Approved</TableCell>
                              <TableCell align="right">Pending</TableCell>
                              <TableCell align="right">Approval Rate</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {staffBreakdown.map((staff, index) => (
                              <TableRow key={index}>
                                <TableCell>{staff.staff_name}</TableCell>
                                <TableCell align="right">{staff.total_hours}h</TableCell>
                                <TableCell align="right">{staff.current_month_hours}h</TableCell>
                                <TableCell align="right">{staff.total_timesheets}</TableCell>
                                <TableCell align="right">{staff.approved_count}</TableCell>
                                <TableCell align="right">{staff.pending_count}</TableCell>
                                <TableCell align="right">{staff.approval_rate.toFixed(1)}%</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}
          </Box>
        )}
      </Paper>

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Review Timesheet - {getStaffName(selectedTimesheet)} ({formatPeriod(selectedTimesheet)})
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Typography variant="body1">
                <strong>Staff Member:</strong> {getStaffName(selectedTimesheet)}
              </Typography>
              <Typography variant="body1">
                <strong>Period:</strong> {formatPeriod(selectedTimesheet)}
              </Typography>
              <Typography variant="body1">
                <strong>Total Hours:</strong> {selectedTimesheet?.total_hours || 0}
              </Typography>
              <Typography variant="body1">
                <strong>Submitted:</strong> {formatDate(selectedTimesheet?.submitted_at)}
              </Typography>
              <Typography variant="body1">
                <strong>Status:</strong> 
                <Chip
                  icon={getStatusIcon(selectedTimesheet?.status)}
                  label={selectedTimesheet?.status?.toUpperCase() || 'UNKNOWN'}
                  color={getStatusColor(selectedTimesheet?.status)}
                  variant="outlined"
                  size="small"
                  sx={{ ml: 1 }}
                />
              </Typography>
            </Grid>
            
            {selectedTimesheet?.review_notes && (
              <Grid item xs={12}>
                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>Previous Review Notes:</strong> {selectedTimesheet.review_notes}
                  </Typography>
                </Alert>
              </Grid>
            )}
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label={selectedTimesheet?.status === 'rejected' ? "Review Notes (Required for rejection)" : "Review Notes (Optional)"}
                variant="outlined"
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add any notes about this timesheet review..."
              />
            </Grid>
            
            {selectedTimesheet?.google_sheet_url && (
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  startIcon={<OpenInNewIcon />}
                  onClick={() => window.open(selectedTimesheet.google_sheet_url, '_blank')}
                  fullWidth
                >
                  Open Google Sheet in New Tab
                </Button>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setReviewDialogOpen(false)}
            disabled={processing}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={processing ? <CircularProgress size={20} /> : <RejectIcon />}
            onClick={handleReject}
            disabled={processing}
            sx={{ mr: 1 }}
          >
            {processing ? 'Processing...' : 'Reject'}
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={processing ? <CircularProgress size={20} /> : <ApproveIcon />}
            onClick={handleApprove}
            disabled={processing}
          >
            {processing ? 'Processing...' : 'Approve'}
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

      {/* Notification Settings Dialog */}
      <Dialog open={notificationDialogOpen} onClose={() => setNotificationDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Notification Settings</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Alert severity="info">
                Configure email notifications and test the notification system.
              </Alert>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Test Email Notification
              </Typography>
              <TextField
                fullWidth
                label="Test Email Address"
                variant="outlined"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="Enter email address to test"
                type="email"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Browser Notifications
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Enable browser notifications to get real-time alerts about timesheet submissions.
              </Typography>
              <Button
                variant="outlined"
                onClick={() => notificationService.requestPermission()}
                disabled={notificationService.permission === 'granted'}
              >
                {notificationService.permission === 'granted' ? 'Notifications Enabled' : 'Enable Browser Notifications'}
              </Button>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNotificationDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleTestEmail}
            disabled={!testEmail}
          >
            Send Test Email
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default SupervisorDashboard;