#!/usr/bin/env node

/**
 * Test Runner for Simple Timesheet Application
 * Orchestrates both user and supervisor role testing
 */

const readline = require('readline');
const { spawn } = require('child_process');
const path = require('path');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function prompt(question) {
  return new Promise((resolve) => {
    rl.question(question, resolve);
  });
}

function log(message, type = 'info') {
  const colors = {
    info: '\x1b[36m',
    success: '\x1b[32m',
    error: '\x1b[31m',
    warning: '\x1b[33m',
    reset: '\x1b[0m'
  };
  console.log(`${colors[type]}[${type.toUpperCase()}] ${message}${colors.reset}`);
}

function runScript(scriptPath) {
  return new Promise((resolve, reject) => {
    const child = spawn('node', [scriptPath], {
      stdio: 'inherit',
      cwd: process.cwd()
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve(true);
      } else {
        reject(new Error(`Script exited with code ${code}`));
      }
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

async function checkPrerequisites() {
  log('Checking prerequisites...', 'info');
  
  try {
    // Check if axios is available for the test scripts
    require.resolve('axios');
    log('✅ axios module is available', 'success');
  } catch (error) {
    log('❌ axios module not found. Please run: npm install axios', 'error');
    return false;
  }

  try {
    // Check if backend is running
    const axios = require('axios');
    await axios.get('http://localhost:8095/api/v1/users/me');
    log('✅ Backend API is accessible (expected auth error is normal)', 'success');
  } catch (error) {
    if (error.response && error.response.status === 401) {
      log('✅ Backend API is accessible', 'success');
    } else {
      log('❌ Backend API not accessible. Make sure it\'s running on port 8095', 'error');
      return false;
    }
  }

  try {
    // Check if frontend is running
    const axios = require('axios');
    await axios.get('http://localhost:5185');
    log('✅ Frontend is accessible', 'success');
  } catch (error) {
    log('❌ Frontend not accessible. Make sure it\'s running on port 5185', 'error');
    return false;
  }

  return true;
}

async function main() {
  console.log(`
  🧪 SIMPLE TIMESHEET - COMPREHENSIVE TESTING SUITE
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  This test suite will help you verify all functionality of the Simple Timesheet
  application for both user and supervisor roles.
  
  Available Tests:
  1. User Role Testing - Tests all staff/user functionality
  2. Supervisor Role Testing - Tests all supervisor/admin functionality  
  3. Run Both Tests - Comprehensive testing of all roles
  
  Prerequisites:
  - Docker containers must be running (frontend + backend)
  - Google OAuth must be configured
  - Test users with appropriate roles must be available
  `);

  // Check prerequisites
  const prereqsOk = await checkPrerequisites();
  if (!prereqsOk) {
    log('Prerequisites not met. Please fix the issues above and try again.', 'error');
    rl.close();
    return;
  }

  const choice = await prompt(`
  Select test to run:
  [1] User Role Testing
  [2] Supervisor Role Testing  
  [3] Run Both Tests
  [4] Exit
  
  Enter your choice (1-4): `);

  switch (choice.trim()) {
    case '1':
      log('Starting User Role Testing...', 'info');
      try {
        await runScript(path.join(__dirname, 'test-user-role.js'));
        log('User Role Testing completed', 'success');
      } catch (error) {
        log(`User Role Testing failed: ${error.message}`, 'error');
      }
      break;

    case '2':
      log('Starting Supervisor Role Testing...', 'info');
      try {
        await runScript(path.join(__dirname, 'test-supervisor-role.js'));
        log('Supervisor Role Testing completed', 'success');
      } catch (error) {
        log(`Supervisor Role Testing failed: ${error.message}`, 'error');
      }
      break;

    case '3':
      log('Starting Comprehensive Testing (Both Roles)...', 'info');
      
      try {
        log('Phase 1: User Role Testing', 'info');
        await runScript(path.join(__dirname, 'test-user-role.js'));
        log('✅ User Role Testing completed', 'success');
        
        console.log('\n' + '='.repeat(80) + '\n');
        
        log('Phase 2: Supervisor Role Testing', 'info');
        await runScript(path.join(__dirname, 'test-supervisor-role.js'));
        log('✅ Supervisor Role Testing completed', 'success');
        
        log('🎉 Comprehensive Testing completed successfully!', 'success');
      } catch (error) {
        log(`Comprehensive Testing failed: ${error.message}`, 'error');
      }
      break;

    case '4':
      log('Goodbye!', 'info');
      break;

    default:
      log('Invalid choice. Please run the script again.', 'error');
      break;
  }

  rl.close();
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  log('Testing interrupted by user', 'warning');
  rl.close();
  process.exit(0);
});

// Run the main function
if (require.main === module) {
  main().catch(console.error);
}