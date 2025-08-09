import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Paper,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  Rating,
  Alert,
  Snackbar,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Feedback as FeedbackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Reply as ReplyIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import dayjs from 'dayjs';
import { useAuth } from '../contexts/AuthContext';
import { feedbackAPI } from '../services/api';
import FeedbackDialog from '../components/FeedbackDialog';

function FeedbackPage() {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [feedback, setFeedback] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [responseDialogOpen, setResponseDialogOpen] = useState(false);
  const [responseText, setResponseText] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    priority: ''
  });

  useEffect(() => {
    fetchFeedback();
    fetchStats();
  }, [tabValue, filters]);

  const fetchFeedback = async () => {
    try {
      setLoading(true);
      const params = {
        my_feedback: tabValue === 0, // My Feedback tab
        ...filters
      };
      
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '') delete params[key];
      });
      
      const response = await feedbackAPI.getFeedbackList(params);
      setFeedback(response.data);
    } catch (error) {
      showSnackbar('Failed to fetch feedback', 'error');
      console.error('Error fetching feedback:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await feedbackAPI.getStats(tabValue === 0); // My stats for My Feedback tab
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleFeedbackSubmit = async (newFeedback) => {
    showSnackbar('Feedback submitted successfully!', 'success');
    await fetchFeedback();
    await fetchStats();
  };

  const handleViewFeedback = async (feedbackId) => {
    try {
      const response = await feedbackAPI.getFeedback(feedbackId);
      setSelectedFeedback(response.data);
      setDetailDialogOpen(true);
    } catch (error) {
      showSnackbar('Failed to load feedback details', 'error');
    }
  };

  const handleAddResponse = async () => {
    if (!responseText.trim()) {
      showSnackbar('Please enter a response', 'warning');
      return;
    }

    try {
      await feedbackAPI.addResponse(selectedFeedback.id, {
        message: responseText,
        is_internal: isInternal
      });
      
      showSnackbar('Response added successfully', 'success');
      setResponseText('');
      setIsInternal(false);
      setResponseDialogOpen(false);
      
      // Refresh feedback details
      await handleViewFeedback(selectedFeedback.id);
    } catch (error) {
      showSnackbar('Failed to add response', 'error');
    }
  };

  const handleDeleteFeedback = async (feedbackId) => {
    if (!window.confirm('Are you sure you want to delete this feedback?')) {
      return;
    }

    try {
      await feedbackAPI.deleteFeedback(feedbackId);
      showSnackbar('Feedback deleted successfully', 'success');
      await fetchFeedback();
      await fetchStats();
    } catch (error) {
      showSnackbar('Failed to delete feedback', 'error');
    }
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ open: false, message: '', severity: 'info' });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'primary';
      case 'in_review': return 'warning';
      case 'resolved': return 'success';
      case 'closed': return 'default';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'low': return 'info';
      case 'medium': return 'warning';
      case 'high': return 'error';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return dayjs(dateString).format('MMM DD, YYYY HH:mm');
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Feedback & Support
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Share your feedback, report issues, and help us improve the app.
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setFeedbackDialogOpen(true)}
          >
            Submit Feedback
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <FeedbackIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Feedback</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {stats.total_feedback}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Resolved</Typography>
                </Box>
                <Typography variant="h4" color="success.main">
                  {stats.by_status.resolved || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AssessmentIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">In Review</Typography>
                </Box>
                <Typography variant="h4" color="warning.main">
                  {stats.by_status.in_review || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Average Rating
                </Typography>
                {stats.average_rating ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="h4">
                      {stats.average_rating.toFixed(1)}
                    </Typography>
                    <Rating value={stats.average_rating} readOnly size="small" />
                  </Box>
                ) : (
                  <Typography variant="h4" color="text.secondary">
                    N/A
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs and Filters */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="My Feedback" />
          {user?.is_supervisor && <Tab label="All Feedback" />}
        </Tabs>

        {/* Filters */}
        <Box sx={{ p: 2, display: 'flex', gap: 2, borderTop: 1, borderColor: 'divider' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={filters.category}
              label="Category"
              onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="app">App</MenuItem>
              <MenuItem value="feature">Feature</MenuItem>
              <MenuItem value="bug">Bug</MenuItem>
              <MenuItem value="suggestion">Suggestion</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={filters.status}
              label="Status"
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="open">Open</MenuItem>
              <MenuItem value="in_review">In Review</MenuItem>
              <MenuItem value="resolved">Resolved</MenuItem>
              <MenuItem value="closed">Closed</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Priority</InputLabel>
            <Select
              value={filters.priority}
              label="Priority"
              onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Feedback List */}
        <Box sx={{ p: 2 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : feedback.length === 0 ? (
            <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
              No feedback found. {tabValue === 0 ? 'Submit your first feedback!' : 'No feedback submitted yet.'}
            </Typography>
          ) : (
            <List>
              {feedback.map((item) => (
                <ListItem key={item.id} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {item.title}
                        </Typography>
                        <Chip 
                          label={item.category} 
                          size="small" 
                          color="primary" 
                          variant="outlined" 
                        />
                        <Chip 
                          label={item.status} 
                          size="small" 
                          color={getStatusColor(item.status)} 
                        />
                        <Chip 
                          label={item.priority} 
                          size="small" 
                          color={getPriorityColor(item.priority)}
                          variant="outlined" 
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {item.description && item.description.length > 100 
                            ? `${item.description.substring(0, 100)}...` 
                            : item.description
                          }
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          By {item.user_name || 'Unknown'} • {formatDate(item.created_at)}
                          {item.rating && (
                            <>
                              {' • '}
                              <Rating value={item.rating} readOnly size="small" sx={{ ml: 1 }} />
                            </>
                          )}
                        </Typography>
                      </Box>
                    }
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="View Details">
                      <IconButton onClick={() => handleViewFeedback(item.id)}>
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    {(user?.is_supervisor || item.user_id === user?.id) && (
                      <Tooltip title="Add Response">
                        <IconButton 
                          onClick={() => {
                            setSelectedFeedback(item);
                            setResponseDialogOpen(true);
                          }}
                        >
                          <ReplyIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {(user?.is_supervisor || item.user_id === user?.id) && (
                      <Tooltip title="Delete">
                        <IconButton 
                          onClick={() => handleDeleteFeedback(item.id)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </Paper>

      {/* Feedback Submission Dialog */}
      <FeedbackDialog
        open={feedbackDialogOpen}
        onClose={() => setFeedbackDialogOpen(false)}
        onSubmit={handleFeedbackSubmit}
      />

      {/* Feedback Detail Dialog */}
      <Dialog open={detailDialogOpen} onClose={() => setDetailDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Feedback Details</DialogTitle>
        <DialogContent>
          {selectedFeedback && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    {selectedFeedback.title}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Chip label={selectedFeedback.category} color="primary" size="small" />
                    <Chip label={selectedFeedback.status} color={getStatusColor(selectedFeedback.status)} size="small" />
                    <Chip label={selectedFeedback.priority} color={getPriorityColor(selectedFeedback.priority)} variant="outlined" size="small" />
                  </Box>
                  {selectedFeedback.rating && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" gutterBottom>Rating:</Typography>
                      <Rating value={selectedFeedback.rating} readOnly />
                    </Box>
                  )}
                  <Typography variant="body1" paragraph>
                    {selectedFeedback.description}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Submitted by {selectedFeedback.user_name} on {formatDate(selectedFeedback.created_at)}
                  </Typography>
                </Grid>
              </Grid>

              {/* Responses */}
              {selectedFeedback.responses && selectedFeedback.responses.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Responses
                  </Typography>
                  {selectedFeedback.responses.map((response, index) => (
                    <Box key={response.id} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="body2" paragraph>
                        {response.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {response.user_name} • {formatDate(response.created_at)}
                        {response.is_internal && (
                          <Chip label="Internal" size="small" color="warning" sx={{ ml: 1 }} />
                        )}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Add Response Dialog */}
      <Dialog open={responseDialogOpen} onClose={() => setResponseDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Response</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Response"
            value={responseText}
            onChange={(e) => setResponseText(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          {user?.is_supervisor && (
            <FormControl>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <input
                  type="checkbox"
                  checked={isInternal}
                  onChange={(e) => setIsInternal(e.target.checked)}
                />
                <Typography variant="body2">
                  Internal note (not visible to user)
                </Typography>
              </Box>
            </FormControl>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResponseDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddResponse}>
            Add Response
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
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
  );
}

export default FeedbackPage;