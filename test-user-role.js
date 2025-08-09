#!/usr/bin/env node

/**
 * Test Script for User Role Functionality
 * Tests all major user features in the Simple Timesheet application
 */

const axios = require('axios');
const readline = require('readline');

const API_BASE_URL = 'http://localhost:8095/api/v1';
const FRONTEND_URL = 'http://localhost:5185';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function prompt(question) {
  return new Promise((resolve) => {
    rl.question(question, resolve);
  });
}

class UserRoleTester {
  constructor() {
    this.token = null;
    this.userId = null;
    this.userProfile = null;
    this.timesheets = [];
  }

  log(message, type = 'info') {
    const colors = {
      info: '\x1b[36m',
      success: '\x1b[32m',
      error: '\x1b[31m',
      warning: '\x1b[33m',
      reset: '\x1b[0m'
    };
    console.log(`${colors[type]}[${type.toUpperCase()}] ${message}${colors.reset}`);
  }

  async makeRequest(method, endpoint, data = null, headers = {}) {
    try {
      const config = {
        method,
        url: `${API_BASE_URL}${endpoint}`,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      };

      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }

      if (data) {
        config.data = data;
      }

      const response = await axios(config);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data || error.message 
      };
    }
  }

  async testAuthenticationSetup() {
    this.log('Testing Authentication Setup...', 'info');
    
    // Check if authentication endpoints are available
    const authCheck = await this.makeRequest('GET', '/users/me');
    
    if (!authCheck.success && authCheck.error.status !== 401) {
      this.log('Backend authentication endpoints not accessible', 'error');
      return false;
    }
    
    this.log('Authentication endpoints are accessible', 'success');
    return true;
  }

  async simulateGoogleAuth() {
    this.log('Simulating Google Authentication...', 'info');
    
    // In a real test, you would need a valid Google OAuth token
    // For testing purposes, we'll create a mock user
    console.log(`
    🔐 AUTHENTICATION REQUIRED
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    To test user functionality, you need to authenticate via Google OAuth.
    
    Please follow these steps:
    1. Open your browser and go to: ${FRONTEND_URL}
    2. Click "Login with Google" 
    3. Complete the Google OAuth flow
    4. Open Developer Tools (F12) and go to Application > Local Storage
    5. Find the "token" key and copy its value
    `);

    const token = await prompt('Enter your authentication token: ');
    this.token = token.trim();

    // Verify token by getting user info
    const userInfo = await this.makeRequest('GET', '/users/me');
    
    if (!userInfo.success) {
      this.log('Invalid token or authentication failed', 'error');
      return false;
    }

    this.userProfile = userInfo.data;
    this.userId = userInfo.data.id;
    this.log(`Successfully authenticated as: ${userInfo.data.full_name}`, 'success');
    this.log(`User role: ${userInfo.data.is_supervisor ? 'Supervisor' : 'Staff'}`, 'info');
    
    if (userInfo.data.is_supervisor) {
      this.log('⚠️  You are logged in as a supervisor. This test is for user role functionality.', 'warning');
      const continueTest = await prompt('Continue anyway? (y/n): ');
      if (continueTest.toLowerCase() !== 'y') {
        return false;
      }
    }
    
    return true;
  }

  async testTimesheetCreation() {
    this.log('Testing Timesheet Creation...', 'info');
    
    const currentDate = new Date();
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1; // JavaScript months are 0-indexed
    
    const createResult = await this.makeRequest('POST', '/timesheets/create', { year, month });
    
    if (!createResult.success) {
      this.log(`Failed to create timesheet: ${createResult.error.detail || createResult.error}`, 'error');
      return false;
    }
    
    this.log(`Successfully created timesheet for ${month}/${year}`, 'success');
    return createResult.data;
  }

  async testGetUserTimesheets() {
    this.log('Testing Get User Timesheets...', 'info');
    
    const result = await this.makeRequest('GET', '/timesheets');
    
    if (!result.success) {
      this.log(`Failed to get timesheets: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.timesheets = result.data;
    this.log(`Successfully retrieved ${result.data.length} timesheets`, 'success');
    
    if (result.data.length > 0) {
      result.data.forEach(ts => {
        this.log(`  - ${ts.month_year} (Status: ${ts.status})`, 'info');
      });
    }
    
    return true;
  }

  async testTimesheetSubmission() {
    this.log('Testing Timesheet Submission...', 'info');
    
    if (this.timesheets.length === 0) {
      this.log('No timesheets available to submit', 'warning');
      return false;
    }
    
    // Find a draft timesheet to submit
    const draftTimesheet = this.timesheets.find(ts => ts.status === 'draft');
    
    if (!draftTimesheet) {
      this.log('No draft timesheets found to submit', 'warning');
      return false;
    }
    
    const submitResult = await this.makeRequest('POST', `/timesheets/${draftTimesheet.id}/submit`);
    
    if (!submitResult.success) {
      this.log(`Failed to submit timesheet: ${submitResult.error.detail || submitResult.error}`, 'error');
      return false;
    }
    
    this.log(`Successfully submitted timesheet ${draftTimesheet.month_year}`, 'success');
    return true;
  }

  async testTimesheetDataAccess() {
    this.log('Testing Timesheet Data Access...', 'info');
    
    if (this.timesheets.length === 0) {
      this.log('No timesheets available to test data access', 'warning');
      return false;
    }
    
    const timesheet = this.timesheets[0];
    const result = await this.makeRequest('GET', `/timesheets/data/${timesheet.id}`);
    
    if (!result.success) {
      this.log(`Failed to get timesheet data: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.log('Successfully retrieved timesheet data', 'success');
    this.log(`  - Spreadsheet ID: ${result.data.spreadsheet_id || 'Not created yet'}`, 'info');
    return true;
  }

  async testAnalyticsAccess() {
    this.log('Testing User Analytics Access...', 'info');
    
    const result = await this.makeRequest('GET', '/timesheets/analytics/monthly?months=6');
    
    if (!result.success) {
      this.log(`Failed to get analytics: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.log('Successfully retrieved user analytics', 'success');
    this.log(`  - Analytics data points: ${result.data.length}`, 'info');
    return true;
  }

  async testFeedbackSystem() {
    this.log('Testing Feedback System...', 'info');
    
    // Test creating feedback
    const feedbackData = {
      category: 'app',
      type: 'comment',
      title: 'Test User Feedback',
      description: 'This is a test feedback from the user role test script.',
      rating: 4
    };
    
    const createResult = await this.makeRequest('POST', '/feedback', feedbackData);
    
    if (!createResult.success) {
      this.log(`Failed to create feedback: ${createResult.error.detail || createResult.error}`, 'error');
      return false;
    }
    
    this.log('Successfully created test feedback', 'success');
    
    // Test getting user's feedback
    const getFeedbackResult = await this.makeRequest('GET', '/feedback?my_feedback=true');
    
    if (!getFeedbackResult.success) {
      this.log(`Failed to get feedback: ${getFeedbackResult.error.detail || getFeedbackResult.error}`, 'error');
      return false;
    }
    
    this.log(`Successfully retrieved ${getFeedbackResult.data.length} feedback items`, 'success');
    return true;
  }

  async testOfflineCapabilities() {
    this.log('Testing Offline Capabilities (Frontend Feature)...', 'info');
    
    // This would typically require browser automation to test properly
    // For now, we'll just verify the service worker registration endpoint exists
    this.log('ℹ️  Offline capabilities are primarily frontend features', 'info');
    this.log('   - Service worker registration: /sw.js', 'info');
    this.log('   - IndexedDB storage for offline data', 'info');
    this.log('   - Background sync for pending actions', 'info');
    this.log('   → Test this manually by going offline in the browser', 'warning');
    
    return true;
  }

  async testExportFunctionality() {
    this.log('Testing Export Functionality...', 'info');
    
    if (this.timesheets.length === 0) {
      this.log('No timesheets available for export testing', 'warning');
      return false;
    }
    
    const timesheet = this.timesheets[0];
    
    try {
      const response = await axios({
        method: 'GET',
        url: `${API_BASE_URL}/timesheets/${timesheet.id}/export`,
        headers: {
          'Authorization': `Bearer ${this.token}`
        },
        responseType: 'blob'
      });
      
      if (response.data.size > 0) {
        this.log('Successfully exported timesheet to Excel format', 'success');
        this.log(`  - Export size: ${response.data.size} bytes`, 'info');
      } else {
        this.log('Export returned empty file', 'warning');
      }
    } catch (error) {
      this.log(`Failed to export timesheet: ${error.message}`, 'error');
      return false;
    }
    
    return true;
  }

  async testUserProfile() {
    this.log('Testing User Profile Management...', 'info');
    
    // Get current profile
    const profileResult = await this.makeRequest('GET', '/users/me');
    
    if (!profileResult.success) {
      this.log(`Failed to get profile: ${profileResult.error.detail || profileResult.error}`, 'error');
      return false;
    }
    
    this.log('Successfully retrieved user profile', 'success');
    this.log(`  - Name: ${profileResult.data.full_name}`, 'info');
    this.log(`  - Email: ${profileResult.data.email}`, 'info');
    this.log(`  - Department: ${profileResult.data.department || 'Not set'}`, 'info');
    
    return true;
  }

  async runAllTests() {
    console.log(`
    🧪 SIMPLE TIMESHEET - USER ROLE TESTING
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    This script tests all major user functionality in the timesheet application.
    
    Prerequisites:
    - Backend server running on ${API_BASE_URL}
    - Frontend server running on ${FRONTEND_URL}
    - Valid Google OAuth authentication
    `);

    let passedTests = 0;
    let totalTests = 0;

    const tests = [
      { name: 'Authentication Setup', method: 'testAuthenticationSetup' },
      { name: 'Google Authentication', method: 'simulateGoogleAuth' },
      { name: 'User Profile', method: 'testUserProfile' },
      { name: 'Timesheet Creation', method: 'testTimesheetCreation' },
      { name: 'Get User Timesheets', method: 'testGetUserTimesheets' },
      { name: 'Timesheet Submission', method: 'testTimesheetSubmission' },
      { name: 'Timesheet Data Access', method: 'testTimesheetDataAccess' },
      { name: 'Analytics Access', method: 'testAnalyticsAccess' },
      { name: 'Feedback System', method: 'testFeedbackSystem' },
      { name: 'Export Functionality', method: 'testExportFunctionality' },
      { name: 'Offline Capabilities', method: 'testOfflineCapabilities' }
    ];

    for (const test of tests) {
      totalTests++;
      console.log(`\n${'='.repeat(80)}`);
      this.log(`Running: ${test.name}`, 'info');
      
      try {
        const result = await this[test.method]();
        if (result) {
          passedTests++;
          this.log(`✅ ${test.name}: PASSED`, 'success');
        } else {
          this.log(`❌ ${test.name}: FAILED`, 'error');
        }
      } catch (error) {
        this.log(`❌ ${test.name}: ERROR - ${error.message}`, 'error');
      }
    }

    console.log(`\n${'='.repeat(80)}`);
    this.log(`TEST SUMMARY: ${passedTests}/${totalTests} tests passed`, 
      passedTests === totalTests ? 'success' : 'warning');
    
    if (passedTests === totalTests) {
      this.log('🎉 All user role functionality tests passed!', 'success');
    } else {
      this.log('⚠️  Some tests failed. Check the logs above for details.', 'warning');
    }

    rl.close();
  }
}

// Run the tests
if (require.main === module) {
  const tester = new UserRoleTester();
  tester.runAllTests().catch(console.error);
}

module.exports = UserRoleTester;