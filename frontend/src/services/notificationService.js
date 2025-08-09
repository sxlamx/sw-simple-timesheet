class NotificationService {
  constructor() {
    this.permission = 'default';
    this.init();
  }

  async init() {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return;
    }

    // Get current permission status
    this.permission = Notification.permission;
  }

  async requestPermission() {
    if (!('Notification' in window)) {
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    if (this.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      return permission === 'granted';
    }

    return false;
  }

  showNotification(title, options = {}) {
    if (!('Notification' in window) || this.permission !== 'granted') {
      // Fallback to console log for debugging
      console.log('Notification:', title, options);
      return null;
    }

    const defaultOptions = {
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: 'simple-timesheet',
      requireInteraction: false,
      ...options
    };

    const notification = new Notification(title, defaultOptions);

    // Auto close after 5 seconds if not requiring interaction
    if (!defaultOptions.requireInteraction) {
      setTimeout(() => {
        notification.close();
      }, 5000);
    }

    return notification;
  }

  // Predefined notification types
  showTimesheetSubmitted(staffName, period) {
    return this.showNotification(
      'Timesheet Submitted',
      {
        body: `${staffName} has submitted their timesheet for ${period}`,
        icon: '/favicon.ico',
        tag: 'timesheet-submitted',
        requireInteraction: true,
        actions: [
          {
            action: 'review',
            title: 'Review Now'
          },
          {
            action: 'dismiss',
            title: 'Dismiss'
          }
        ]
      }
    );
  }

  showTimesheetApproved(period) {
    return this.showNotification(
      '✅ Timesheet Approved',
      {
        body: `Your timesheet for ${period} has been approved!`,
        icon: '/favicon.ico',
        tag: 'timesheet-approved'
      }
    );
  }

  showTimesheetRejected(period, reason) {
    return this.showNotification(
      '📝 Timesheet Rejected',
      {
        body: `Your timesheet for ${period} requires revision. ${reason || 'Please check review notes.'}`,
        icon: '/favicon.ico',
        tag: 'timesheet-rejected',
        requireInteraction: true
      }
    );
  }

  showReminder(title, message, urgent = false) {
    return this.showNotification(
      `⏰ ${title}`,
      {
        body: message,
        icon: '/favicon.ico',
        tag: 'reminder',
        requireInteraction: urgent,
        actions: urgent ? [
          {
            action: 'open',
            title: 'Open App'
          },
          {
            action: 'snooze',
            title: 'Remind Later'
          }
        ] : undefined
      }
    );
  }

  // Check for overdue timesheets and show reminders
  async checkAndNotifyOverdue(timesheets, userRole) {
    if (this.permission !== 'granted') return;

    const now = new Date();
    
    if (userRole === 'supervisor') {
      // Check for pending reviews older than 3 days
      const overdueReviews = timesheets.filter(ts => {
        if (ts.status !== 'pending' || !ts.submitted_at) return false;
        const submittedDate = new Date(ts.submitted_at);
        const daysDiff = (now - submittedDate) / (1000 * 60 * 60 * 24);
        return daysDiff > 3;
      });

      if (overdueReviews.length > 0) {
        this.showReminder(
          'Overdue Reviews',
          `You have ${overdueReviews.length} timesheet(s) waiting for review for more than 3 days.`,
          true
        );
      }
    } else {
      // Check for draft timesheets older than 7 days
      const oldDrafts = timesheets.filter(ts => {
        if (ts.status !== 'draft' || !ts.period_start) return false;
        const periodStart = new Date(ts.period_start);
        const daysDiff = (now - periodStart) / (1000 * 60 * 60 * 24);
        return daysDiff > 37; // Period ended more than a week ago (30 days + 7 days)
      });

      if (oldDrafts.length > 0) {
        this.showReminder(
          'Incomplete Timesheets',
          `You have ${oldDrafts.length} draft timesheet(s) that should be submitted.`,
          false
        );
      }
    }
  }

  // Service Worker integration for background notifications
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration);
        return registration;
      } catch (error) {
        console.error('Service Worker registration failed:', error);
        return null;
      }
    }
    return null;
  }

  // Schedule periodic checks
  startPeriodicChecks(checkInterval = 15 * 60 * 1000) { // 15 minutes
    setInterval(async () => {
      // This would typically fetch latest data and check for notifications
      // Implementation depends on your app's state management
      console.log('Periodic notification check...');
    }, checkInterval);
  }
}

// Global instance
const notificationService = new NotificationService();

export default notificationService;