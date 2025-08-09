#!/usr/bin/env node

/**
 * Test Script for Supervisor Role Functionality
 * Tests all major supervisor features in the Simple Timesheet application
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

class SupervisorRoleTester {
  constructor() {
    this.token = null;
    this.userId = null;
    this.supervisorProfile = null;
    this.staffMembers = [];
    this.pendingTimesheets = [];
    this.teamTimesheets = [];
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
    
    console.log(`
    🔐 AUTHENTICATION REQUIRED
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    To test supervisor functionality, you need to authenticate as a supervisor.
    
    Please follow these steps:
    1. Open your browser and go to: ${FRONTEND_URL}
    2. Click "Login with Google" using a SUPERVISOR account
    3. Complete the Google OAuth flow
    4. Open Developer Tools (F12) and go to Application > Local Storage
    5. Find the "token" key and copy its value
    `);

    const token = await prompt('Enter your supervisor authentication token: ');
    this.token = token.trim();

    // Verify token by getting user info
    const userInfo = await this.makeRequest('GET', '/users/me');
    
    if (!userInfo.success) {
      this.log('Invalid token or authentication failed', 'error');
      return false;
    }

    this.supervisorProfile = userInfo.data;
    this.userId = userInfo.data.id;
    this.log(`Successfully authenticated as: ${userInfo.data.full_name}`, 'success');
    this.log(`User role: ${userInfo.data.is_supervisor ? 'Supervisor' : 'Staff'}`, 'info');
    
    if (!userInfo.data.is_supervisor) {
      this.log('❌ You are not logged in as a supervisor. This test requires supervisor privileges.', 'error');
      return false;
    }
    
    return true;
  }

  async testGetStaffMembers() {
    this.log('Testing Get Staff Members...', 'info');
    
    const result = await this.makeRequest('GET', '/users/staff');
    
    if (!result.success) {
      this.log(`Failed to get staff members: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.staffMembers = result.data;
    this.log(`Successfully retrieved ${result.data.length} staff members`, 'success');
    
    if (result.data.length > 0) {
      result.data.forEach(staff => {
        this.log(`  - ${staff.full_name} (${staff.email})`, 'info');
      });
    } else {
      this.log('⚠️  No staff members found in the system', 'warning');
    }
    
    return true;
  }

  async testGetPendingTimesheets() {
    this.log('Testing Get Pending Timesheets...', 'info');
    
    const result = await this.makeRequest('GET', '/timesheets/pending/review');
    
    if (!result.success) {
      this.log(`Failed to get pending timesheets: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.pendingTimesheets = result.data;
    this.log(`Successfully retrieved ${result.data.length} pending timesheets`, 'success');
    
    if (result.data.length > 0) {
      result.data.forEach(ts => {
        this.log(`  - ${ts.user_name}: ${ts.month_year} (Submitted: ${new Date(ts.submitted_at).toLocaleDateString()})`, 'info');
      });
    } else {
      this.log('ℹ️  No pending timesheets for review', 'info');
    }
    
    return true;
  }

  async testGetAllTeamTimesheets() {
    this.log('Testing Get All Team Timesheets...', 'info');
    
    const result = await this.makeRequest('GET', '/timesheets/team/all');
    
    if (!result.success) {
      this.log(`Failed to get team timesheets: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.teamTimesheets = result.data;
    this.log(`Successfully retrieved ${result.data.length} team timesheets`, 'success');
    
    // Group by status
    const statusGroups = this.teamTimesheets.reduce((acc, ts) => {
      acc[ts.status] = (acc[ts.status] || 0) + 1;
      return acc;
    }, {});
    
    Object.entries(statusGroups).forEach(([status, count]) => {
      this.log(`  - ${status}: ${count} timesheets`, 'info');
    });
    
    return true;
  }

  async testTimesheetApproval() {
    this.log('Testing Timesheet Approval...', 'info');
    
    if (this.pendingTimesheets.length === 0) {
      this.log('No pending timesheets available for approval testing', 'warning');
      this.log('ℹ️  To test approval functionality:', 'info');
      this.log('   1. Have a staff member submit a timesheet', 'info');
      this.log('   2. Run this test again', 'info');
      return true; // Not a failure, just no data to test with
    }
    
    const timesheetToApprove = this.pendingTimesheets[0];
    const reviewNotes = `Approved via automated test - ${new Date().toISOString()}`;
    
    const result = await this.makeRequest('POST', `/timesheets/${timesheetToApprove.id}/approve`, {
      review_notes: reviewNotes
    });
    
    if (!result.success) {
      this.log(`Failed to approve timesheet: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.log(`Successfully approved timesheet for ${timesheetToApprove.user_name}`, 'success');
    this.log(`  - Month/Year: ${timesheetToApprove.month_year}`, 'info');
    this.log(`  - Review Notes: ${reviewNotes}`, 'info');
    
    return true;
  }

  async testTimesheetRejection() {
    this.log('Testing Timesheet Rejection...', 'info');
    
    // Look for another pending timesheet to reject (if available)
    const remainingPending = this.pendingTimesheets.slice(1);
    
    if (remainingPending.length === 0) {
      this.log('No additional pending timesheets available for rejection testing', 'warning');
      this.log('ℹ️  Rejection functionality uses the same endpoint as approval', 'info');
      return true; // Not a failure
    }
    
    const timesheetToReject = remainingPending[0];
    const reviewNotes = `Rejected via automated test - please resubmit with corrections - ${new Date().toISOString()}`;
    
    const result = await this.makeRequest('POST', `/timesheets/${timesheetToReject.id}/reject`, {
      review_notes: reviewNotes
    });
    
    if (!result.success) {
      this.log(`Failed to reject timesheet: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.log(`Successfully rejected timesheet for ${timesheetToReject.user_name}`, 'success');
    this.log(`  - Month/Year: ${timesheetToReject.month_year}`, 'info');
    this.log(`  - Review Notes: ${reviewNotes}`, 'info');
    
    return true;
  }

  async testTeamStatistics() {
    this.log('Testing Team Statistics...', 'info');
    
    const result = await this.makeRequest('GET', '/timesheets/team/statistics');
    
    if (!result.success) {
      this.log(`Failed to get team statistics: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.log('Successfully retrieved team statistics', 'success');
    this.log(`  - Total timesheets: ${result.data.total_timesheets || 0}`, 'info');
    this.log(`  - Pending review: ${result.data.pending_count || 0}`, 'info');
    this.log(`  - Approved: ${result.data.approved_count || 0}`, 'info');
    this.log(`  - Rejected: ${result.data.rejected_count || 0}`, 'info');
    
    return true;
  }

  async testTeamAnalytics() {
    this.log('Testing Team Analytics...', 'info');
    
    const result = await this.makeRequest('GET', '/timesheets/analytics/team-monthly?months=6');
    
    if (!result.success) {
      this.log(`Failed to get team analytics: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.log('Successfully retrieved team analytics', 'success');
    this.log(`  - Analytics data points: ${result.data.length}`, 'info');
    
    return true;
  }

  async testStaffBreakdownAnalytics() {
    this.log('Testing Staff Breakdown Analytics...', 'info');
    
    const result = await this.makeRequest('GET', '/timesheets/analytics/staff-breakdown');
    
    if (!result.success) {
      this.log(`Failed to get staff breakdown: ${result.error.detail || result.error}`, 'error');
      return false;
    }
    
    this.log('Successfully retrieved staff breakdown analytics', 'success');
    this.log(`  - Staff breakdown entries: ${result.data.length}`, 'info');
    
    return true;
  }

  async testTeamExportFunctionality() {
    this.log('Testing Team Export Functionality...', 'info');
    
    try {
      const response = await axios({
        method: 'GET',
        url: `${API_BASE_URL}/timesheets/export/team`,
        headers: {
          'Authorization': `Bearer ${this.token}`
        },
        responseType: 'blob'
      });
      
      if (response.data.size > 0) {
        this.log('Successfully exported team timesheets to Excel format', 'success');
        this.log(`  - Export size: ${response.data.size} bytes`, 'info');
      } else {
        this.log('Export returned empty file', 'warning');
      }
    } catch (error) {
      this.log(`Failed to export team timesheets: ${error.message}`, 'error');
      return false;
    }
    
    return true;
  }

  async testNotificationSystem() {
    this.log('Testing Notification System...', 'info');
    
    // Test sending reminders
    const reminderResult = await this.makeRequest('POST', '/notifications/send-reminders');
    
    if (!reminderResult.success) {
      this.log(`Failed to send reminders: ${reminderResult.error.detail || reminderResult.error}`, 'error');
      return false;
    }
    
    this.log('Successfully triggered reminder notifications', 'success');
    this.log(`  - Notifications sent: ${reminderResult.data.sent_count || 0}`, 'info');
    
    // Test email functionality (if email is configured)
    if (this.supervisorProfile.email) {
      const emailTest = await this.makeRequest('POST', `/notifications/test-email?to_email=${encodeURIComponent(this.supervisorProfile.email)}`);
      
      if (emailTest.success) {
        this.log('Successfully sent test email', 'success');
      } else {
        this.log('Test email failed (email configuration may not be set up)', 'warning');
      }
    }
    
    return true;
  }

  async testFeedbackManagement() {
    this.log('Testing Feedback Management...', 'info');
    
    // Get all feedback (supervisor view)
    const feedbackResult = await this.makeRequest('GET', '/feedback?my_feedback=false');
    
    if (!feedbackResult.success) {
      this.log(`Failed to get all feedback: ${feedbackResult.error.detail || feedbackResult.error}`, 'error');
      return false;
    }
    
    this.log(`Successfully retrieved ${feedbackResult.data.length} feedback items`, 'success');
    
    // Get feedback statistics
    const statsResult = await this.makeRequest('GET', '/feedback/stats/overview?my_stats=false');
    
    if (statsResult.success) {
      this.log('Successfully retrieved feedback statistics', 'success');
      this.log(`  - Total feedback: ${statsResult.data.total_feedback || 0}`, 'info');
      this.log(`  - Average rating: ${statsResult.data.average_rating || 'N/A'}`, 'info');
    }
    
    // Test adding response to feedback (if feedback exists)
    if (feedbackResult.data.length > 0) {
      const firstFeedback = feedbackResult.data[0];
      const responseData = {
        message: 'Thank you for your feedback. We will review this and get back to you.',
        is_internal: false
      };
      
      const responseResult = await this.makeRequest('POST', `/feedback/${firstFeedback.id}/responses`, responseData);
      
      if (responseResult.success) {
        this.log('Successfully added response to feedback', 'success');
      } else {
        this.log(`Failed to add response: ${responseResult.error.detail || responseResult.error}`, 'warning');
      }
    }
    
    return true;
  }

  async testUserManagement() {
    this.log('Testing User Management...', 'info');
    
    // Get all users (supervisor privilege)
    const usersResult = await this.makeRequest('GET', '/users');
    
    if (!usersResult.success) {
      this.log(`Failed to get users: ${usersResult.error.detail || usersResult.error}`, 'error');
      return false;
    }
    
    this.log(`Successfully retrieved ${usersResult.data.length} users`, 'success');
    
    const supervisors = usersResult.data.filter(user => user.is_supervisor);
    const staff = usersResult.data.filter(user => !user.is_supervisor);
    
    this.log(`  - Supervisors: ${supervisors.length}`, 'info');
    this.log(`  - Staff: ${staff.length}`, 'info');
    
    return true;
  }

  async runAllTests() {
    console.log(`
    👑 SIMPLE TIMESHEET - SUPERVISOR ROLE TESTING
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    This script tests all major supervisor functionality in the timesheet application.
    
    Prerequisites:
    - Backend server running on ${API_BASE_URL}
    - Frontend server running on ${FRONTEND_URL}
    - Valid Google OAuth authentication WITH SUPERVISOR PRIVILEGES
    - Some staff members and timesheets in the system for comprehensive testing
    `);

    let passedTests = 0;
    let totalTests = 0;

    const tests = [
      { name: 'Authentication Setup', method: 'testAuthenticationSetup' },
      { name: 'Google Authentication (Supervisor)', method: 'simulateGoogleAuth' },
      { name: 'Get Staff Members', method: 'testGetStaffMembers' },
      { name: 'Get Pending Timesheets', method: 'testGetPendingTimesheets' },
      { name: 'Get All Team Timesheets', method: 'testGetAllTeamTimesheets' },
      { name: 'Timesheet Approval', method: 'testTimesheetApproval' },
      { name: 'Timesheet Rejection', method: 'testTimesheetRejection' },
      { name: 'Team Statistics', method: 'testTeamStatistics' },
      { name: 'Team Analytics', method: 'testTeamAnalytics' },
      { name: 'Staff Breakdown Analytics', method: 'testStaffBreakdownAnalytics' },
      { name: 'Team Export Functionality', method: 'testTeamExportFunctionality' },
      { name: 'Notification System', method: 'testNotificationSystem' },
      { name: 'Feedback Management', method: 'testFeedbackManagement' },
      { name: 'User Management', method: 'testUserManagement' }
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
      this.log('🎉 All supervisor role functionality tests passed!', 'success');
    } else {
      this.log('⚠️  Some tests failed. Check the logs above for details.', 'warning');
    }

    console.log(`\n💡 TESTING TIPS:`);
    console.log(`   - Create test staff accounts and have them submit timesheets`);
    console.log(`   - Test the approval/rejection workflow manually in the UI`);
    console.log(`   - Check email notifications if SMTP is configured`);
    console.log(`   - Review analytics charts in the supervisor dashboard`);

    rl.close();
  }
}

// Run the tests
if (require.main === module) {
  const tester = new SupervisorRoleTester();
  tester.runAllTests().catch(console.error);
}

module.exports = SupervisorRoleTester;