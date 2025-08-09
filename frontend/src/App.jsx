import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Box, Button, Avatar, Menu, MenuItem } from '@mui/material';
import { AuthProvider, useAuth } from './contexts/AuthContext.jsx';
import Layout from './components/Layout.jsx';
import offlineService from './services/offlineService';
import LoginPage from './pages/LoginPage.jsx';
import StaffDashboard from './pages/StaffDashboard.jsx';
import SupervisorDashboard from './pages/SupervisorDashboard.jsx';
import AuthCallback from './pages/AuthCallback.jsx';
import FeedbackPage from './pages/FeedbackPage.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';

function AppContent() {
  const { user, isAuthenticated, isSupervisor, logout } = useAuth();
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleClose();
  };

  return (
    <Router>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Simple Timesheet
            </Typography>
            
            {isAuthenticated && user && (
              <div>
                <Button
                  onClick={handleMenu}
                  color="inherit"
                  startIcon={
                    <Avatar
                      src={user.profile_picture}
                      sx={{ width: 32, height: 32 }}
                    >
                      {user.full_name?.charAt(0)}
                    </Avatar>
                  }
                >
                  {user.full_name}
                </Button>
                <Menu
                  anchorEl={anchorEl}
                  open={Boolean(anchorEl)}
                  onClose={handleClose}
                >
                  <MenuItem onClick={handleClose}>Profile</MenuItem>
                  <MenuItem onClick={handleLogout}>Logout</MenuItem>
                </Menu>
              </div>
            )}
          </Toolbar>
        </AppBar>
        
        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <Routes>
            <Route path="/" element={
              isAuthenticated ? 
                <Navigate to={isSupervisor ? "/supervisor" : "/staff"} replace /> : 
                <LoginPage />
            } />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/staff" element={
              <ProtectedRoute>
                <StaffDashboard />
              </ProtectedRoute>
            } />
            <Route path="/supervisor" element={
              <ProtectedRoute requireSupervisor>
                <SupervisorDashboard />
              </ProtectedRoute>
            } />
            <Route path="/feedback" element={
              <ProtectedRoute>
                <FeedbackPage />
              </ProtectedRoute>
            } />
          </Routes>
        </Container>
      </Box>
    </Router>
  );
}

function App() {
  useEffect(() => {
    // Initialize offline service when app starts
    offlineService.init();
  }, []);
  
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;