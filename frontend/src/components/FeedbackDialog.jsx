import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
  Box,
  Typography,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Feedback as FeedbackIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { feedbackAPI } from '../services/api';

function FeedbackDialog({ open, onClose, onSubmit }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    category: '',
    type: '',
    title: '',
    description: '',
    rating: null
  });
  const [errors, setErrors] = useState({});

  const categories = [
    { value: 'app', label: 'General App Experience' },
    { value: 'feature', label: 'Feature Request' },
    { value: 'bug', label: 'Bug Report' },
    { value: 'suggestion', label: 'Suggestion/Improvement' }
  ];

  const types = [
    { value: 'rating', label: 'Rating & Review' },
    { value: 'comment', label: 'General Comment' },
    { value: 'feature_request', label: 'Feature Request' }
  ];

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.category) newErrors.category = 'Category is required';
    if (!formData.type) newErrors.type = 'Type is required';
    if (!formData.title.trim()) newErrors.title = 'Title is required';
    
    // Rating is required for rating type
    if (formData.type === 'rating' && (!formData.rating || formData.rating === 0)) {
      newErrors.rating = 'Rating is required for rating type';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      const response = await feedbackAPI.createFeedback(formData);
      
      if (onSubmit) {
        onSubmit(response.data);
      }
      
      // Reset form
      setFormData({
        category: '',
        type: '',
        title: '',
        description: '',
        rating: null
      });
      setErrors({});
      onClose();
      
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setErrors({
        submit: error.response?.data?.detail || 'Failed to submit feedback'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFormData({
        category: '',
        type: '',
        title: '',
        description: '',
        rating: null
      });
      setErrors({});
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FeedbackIcon />
          Submit Feedback
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {errors.submit && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errors.submit}
          </Alert>
        )}
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth error={!!errors.category}>
              <InputLabel>Category</InputLabel>
              <Select
                value={formData.category}
                label="Category"
                onChange={(e) => handleChange('category', e.target.value)}
              >
                {categories.map((cat) => (
                  <MenuItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </MenuItem>
                ))}
              </Select>
              {errors.category && (
                <Typography variant="caption" color="error" sx={{ ml: 2 }}>
                  {errors.category}
                </Typography>
              )}
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth error={!!errors.type}>
              <InputLabel>Type</InputLabel>
              <Select
                value={formData.type}
                label="Type"
                onChange={(e) => handleChange('type', e.target.value)}
              >
                {types.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
              {errors.type && (
                <Typography variant="caption" color="error" sx={{ ml: 2 }}>
                  {errors.type}
                </Typography>
              )}
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Title"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              error={!!errors.title}
              helperText={errors.title}
              placeholder="Brief summary of your feedback"
            />
          </Grid>
          
          {formData.type === 'rating' && (
            <Grid item xs={12}>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" gutterBottom>
                  Overall Rating *
                </Typography>
                <Rating
                  value={formData.rating}
                  onChange={(event, newValue) => handleChange('rating', newValue)}
                  size="large"
                />
                {errors.rating && (
                  <Typography variant="caption" color="error" display="block">
                    {errors.rating}
                  </Typography>
                )}
              </Box>
            </Grid>
          )}
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder={
                formData.category === 'bug' 
                  ? 'Please describe the bug, steps to reproduce, and expected behavior'
                  : formData.category === 'feature'
                  ? 'Please describe the feature you would like to see and how it would help'
                  : 'Please provide any additional details'
              }
            />
          </Grid>
          
          <Grid item xs={12}>
            <Alert severity="info">
              Your feedback helps us improve the app. We review all submissions and will respond when appropriate.
            </Alert>
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <SendIcon />}
        >
          {loading ? 'Submitting...' : 'Submit Feedback'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default FeedbackDialog;