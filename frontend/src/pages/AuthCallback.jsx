import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { handleAuthCallback, isSupervisor } = useAuth();
  const [error, setError] = React.useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token');
      const userId = searchParams.get('user_id');

      if (token && userId) {
        try {
          handleAuthCallback(token, userId);
          
          // Small delay to let auth context update
          setTimeout(() => {
            navigate(isSupervisor ? '/supervisor' : '/staff', { replace: true });
          }, 1000);
        } catch (error) {
          console.error('Auth callback error:', error);
          setError('Authentication failed. Please try again.');
          setTimeout(() => {
            navigate('/', { replace: true });
          }, 3000);
        }
      } else {
        setError('Invalid authentication callback.');
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, handleAuthCallback, isSupervisor]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
      }}
    >
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : (
        <>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
            Completing sign in...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please wait while we set up your account.
          </Typography>
        </>
      )}
    </Box>
  );
};

export default AuthCallback;