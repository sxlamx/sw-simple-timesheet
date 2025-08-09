# 🧪 Simple Timesheet Testing Guide

This directory contains comprehensive test scripts for verifying all functionality of the Simple Timesheet application.

## 🚀 Quick Start

1. **Start the application:**
   ```bash
   ./scripts/dev-start.sh
   ```

2. **Install test dependencies:**
   ```bash
   npm install axios
   ```

3. **Run the tests:**
   ```bash
   node run-tests.js
   ```

## 📋 Test Scripts

### `run-tests.js` - Main Test Runner
Interactive test runner that guides you through all testing options.

### `test-user-role.js` - User/Staff Role Testing
Tests all functionality available to regular staff members:

- ✅ Google OAuth authentication
- ✅ User profile management
- ✅ Timesheet creation and submission
- ✅ Personal analytics access
- ✅ Feedback system
- ✅ Export functionality
- ✅ Offline capabilities
- ✅ Data access permissions

### `test-supervisor-role.js` - Supervisor Role Testing
Tests all functionality available to supervisors:

- ✅ Supervisor authentication
- ✅ Staff member management
- ✅ Pending timesheet review
- ✅ Timesheet approval/rejection
- ✅ Team analytics and statistics
- ✅ Notification system
- ✅ Feedback management
- ✅ Team export functionality
- ✅ User management

## 🔧 Prerequisites

### System Requirements
- Docker and Docker Compose
- Node.js (for running test scripts)
- Active internet connection (for Google OAuth)

### Application Setup
1. **Backend running on:** http://localhost:8095
2. **Frontend running on:** http://localhost:5185
3. **Google OAuth configured** with valid credentials
4. **Test users created** with appropriate roles

### Test Data Requirements
For comprehensive testing, ensure you have:
- At least one supervisor account
- At least one staff account  
- Some submitted timesheets (for approval testing)
- Google Sheets API access configured

## 🧪 Running Individual Tests

### User Role Testing
```bash
node test-user-role.js
```

### Supervisor Role Testing
```bash
node test-supervisor-role.js
```

## 📊 Test Coverage

### User Role Features Tested
| Feature | Endpoint | Test Status |
|---------|----------|-------------|
| Authentication | `/auth/google` | ✅ |
| Profile Access | `/users/me` | ✅ |
| Timesheet Creation | `/timesheets/create` | ✅ |
| Timesheet List | `/timesheets` | ✅ |
| Timesheet Submission | `/timesheets/{id}/submit` | ✅ |
| Personal Analytics | `/timesheets/analytics/monthly` | ✅ |
| Feedback Creation | `/feedback` | ✅ |
| Export Timesheet | `/timesheets/{id}/export` | ✅ |

### Supervisor Role Features Tested
| Feature | Endpoint | Test Status |
|---------|----------|-------------|
| Staff Management | `/users/staff` | ✅ |
| Pending Review | `/timesheets/pending/review` | ✅ |
| Team Timesheets | `/timesheets/team/all` | ✅ |
| Approve Timesheet | `/timesheets/{id}/approve` | ✅ |
| Reject Timesheet | `/timesheets/{id}/reject` | ✅ |
| Team Statistics | `/timesheets/team/statistics` | ✅ |
| Team Analytics | `/timesheets/analytics/team-monthly` | ✅ |
| Send Notifications | `/notifications/send-reminders` | ✅ |
| Feedback Management | `/feedback` | ✅ |
| Team Export | `/timesheets/export/team` | ✅ |

## 🔐 Authentication Testing

Both test scripts require valid Google OAuth tokens. To obtain a token:

1. Open the frontend application in your browser
2. Complete the Google OAuth flow
3. Open Developer Tools (F12) → Application → Local Storage
4. Copy the value of the `token` key
5. Paste it when prompted by the test script

## 🐛 Troubleshooting

### Common Issues

**Error: "Backend API not accessible"**
- Ensure Docker containers are running: `docker compose -f docker-compose.dev.yml ps`
- Check backend logs: `docker compose -f docker-compose.dev.yml logs backend`

**Error: "Frontend not accessible"**  
- Check if frontend container is running and healthy
- Verify Vite server started successfully in logs

**Error: "Invalid token or authentication failed"**
- Ensure you're using a fresh, valid OAuth token
- Check that Google OAuth is properly configured
- Verify the user account has the correct role (staff vs supervisor)

**Error: "No pending timesheets for approval testing"**
- Create test data by having staff members submit timesheets
- Use the frontend application to create and submit test timesheets

### Getting Help

1. Check the application logs:
   ```bash
   docker compose -f docker-compose.dev.yml logs
   ```

2. Verify API endpoints manually:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8095/api/v1/users/me
   ```

3. Test frontend accessibility:
   ```bash
   curl http://localhost:5185
   ```

## 📈 Test Results

The test scripts provide detailed output including:
- ✅ **PASSED** tests with green checkmarks
- ❌ **FAILED** tests with error details  
- ⚠️ **WARNING** for tests with missing data
- ℹ️ **INFO** for additional context and tips

### Interpreting Results

- **100% Pass Rate:** All functionality working correctly
- **Partial Pass Rate:** Some features may need attention
- **Low Pass Rate:** Significant issues requiring investigation

## 🚀 Integration with CI/CD

These test scripts can be integrated into automated pipelines:

```bash
# Example CI/CD integration
npm install axios
npm run start:test-env  # Start test environment
node test-user-role.js --automated
node test-supervisor-role.js --automated
npm run stop:test-env   # Clean up
```

## 📝 Contributing

When adding new features to the application:

1. Add corresponding test cases to the appropriate test script
2. Update the test coverage tables in this README
3. Ensure new endpoints are covered in both positive and negative test scenarios
4. Test with various user roles and permission levels

---

**Happy Testing! 🎉**

For questions or issues, please refer to the main project documentation or create an issue in the project repository.