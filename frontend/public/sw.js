// Service Worker for background notifications and caching
const CACHE_NAME = 'simple-timesheet-v1';
const DATA_CACHE_NAME = 'simple-timesheet-data-v1';

const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico',
  '/assets/index.js', // Vite builds
  '/assets/index.css'
];

const apiUrls = [
  '/api/v1/users/me',
  '/api/v1/timesheets',
  '/api/v1/users/staff'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache when offline with network-first strategy for API
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    // Network-first strategy for API requests
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // If network request succeeds, cache the response
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(DATA_CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // If network fails, try to return cached version
          return caches.match(event.request)
            .then((cachedResponse) => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // Return a custom offline response for API requests
              return new Response(
                JSON.stringify({ 
                  error: 'Offline', 
                  message: 'This request requires an internet connection' 
                }),
                {
                  status: 503,
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            });
        })
    );
  } else {
    // Cache-first strategy for static assets
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          if (response) {
            return response;
          }
          return fetch(event.request);
        })
        .catch(() => {
          // Return offline page for navigation requests
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
        })
    );
  }
});

// Push event - handle background notifications
self.addEventListener('push', (event) => {
  console.log('Push event received:', event);
  
  let data = {};
  if (event.data) {
    data = event.data.json();
  }

  const title = data.title || 'Simple Timesheet';
  const options = {
    body: data.body || 'You have a new notification',
    icon: data.icon || '/favicon.ico',
    badge: '/favicon.ico',
    tag: data.tag || 'default',
    data: data.data || {},
    actions: data.actions || [],
    requireInteraction: data.requireInteraction || false
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();

  // Handle notification actions
  if (event.action === 'review') {
    event.waitUntil(
      clients.openWindow('/?tab=pending')
    );
  } else if (event.action === 'open') {
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification
    return;
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Background sync for offline functionality
self.addEventListener('sync', (event) => {
  console.log('Background sync event:', event.tag);
  
  if (event.tag === 'timesheet-sync') {
    event.waitUntil(syncTimesheets());
  }
});

// Sync timesheets when online
async function syncTimesheets() {
  try {
    const db = await openIndexedDB();
    const pendingActions = await getPendingSyncData(db);
    
    if (pendingActions.length > 0) {
      console.log('Syncing pending actions:', pendingActions.length);
      
      for (const action of pendingActions) {
        try {
          await executeAction(action);
          await removeAction(db, action.id);
          console.log(`Synced action ${action.id}`);
        } catch (error) {
          console.error(`Failed to sync action ${action.id}:`, error);
          // Increment retry count or remove if too many retries
          action.retries = (action.retries || 0) + 1;
          if (action.retries > 3) {
            await removeAction(db, action.id);
          }
        }
      }
    }
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

// IndexedDB helper functions
async function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('SimpleTimesheetDB', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offline_actions')) {
        const store = db.createObjectStore('offline_actions', { 
          keyPath: 'id', 
          autoIncrement: true 
        });
        store.createIndex('timestamp', 'timestamp');
      }
    };
  });
}

async function getPendingSyncData(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offline_actions'], 'readonly');
    const store = transaction.objectStore('offline_actions');
    const request = store.getAll();
    
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

async function removeAction(db, actionId) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offline_actions'], 'readwrite');
    const store = transaction.objectStore('offline_actions');
    const request = store.delete(actionId);
    
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

async function executeAction(action) {
  const { type, data, endpoint } = action;
  const token = await getStoredToken();
  
  const response = await fetch(`${self.location.origin}${endpoint}`, {
    method: type === 'CREATE_TIMESHEET' ? 'POST' : 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: data ? JSON.stringify(data) : undefined
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  return response.json();
}

async function getStoredToken() {
  // This would need to be implemented based on how tokens are stored
  // For now, return empty string
  return '';
}

// Periodic background checks
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'reminder-check') {
    event.waitUntil(checkForReminders());
  }
});

async function checkForReminders() {
  try {
    // This would typically make an API call to check for overdue items
    console.log('Checking for reminder notifications...');
    
    // Example: Check if user has overdue timesheets
    // const response = await fetch('/api/v1/notifications/check-overdue');
    // const data = await response.json();
    
    // if (data.hasOverdue) {
    //   self.registration.showNotification('Reminder', {
    //     body: 'You have overdue timesheets that need attention.',
    //     icon: '/favicon.ico',
    //     tag: 'reminder',
    //     requireInteraction: true
    //   });
    // }
  } catch (error) {
    console.error('Reminder check failed:', error);
  }
}