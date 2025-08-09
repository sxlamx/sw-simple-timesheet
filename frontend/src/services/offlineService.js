class OfflineService {
  constructor() {
    this.dbName = 'SimpleTimesheetDB';
    this.dbVersion = 1;
    this.db = null;
    this.isOnline = navigator.onLine;
    
    this.init();
    this.setupEventListeners();
  }

  async init() {
    await this.initIndexedDB();
    await this.registerServiceWorker();
  }

  setupEventListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.handleOnlineStatusChange(true);
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.handleOnlineStatusChange(false);
    });
  }

  async initIndexedDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // User data store
        if (!db.objectStoreNames.contains('users')) {
          const userStore = db.createObjectStore('users', { keyPath: 'id' });
          userStore.createIndex('email', 'email', { unique: true });
        }

        // Timesheets store
        if (!db.objectStoreNames.contains('timesheets')) {
          const timesheetStore = db.createObjectStore('timesheets', { keyPath: 'id' });
          timesheetStore.createIndex('user_id', 'user_id');
          timesheetStore.createIndex('status', 'status');
          timesheetStore.createIndex('period_start', 'period_start');
        }

        // Offline actions store (for sync)
        if (!db.objectStoreNames.contains('offline_actions')) {
          const actionStore = db.createObjectStore('offline_actions', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          actionStore.createIndex('timestamp', 'timestamp');
          actionStore.createIndex('type', 'type');
        }

        // Cached API responses
        if (!db.objectStoreNames.contains('api_cache')) {
          const cacheStore = db.createObjectStore('api_cache', { keyPath: 'key' });
          cacheStore.createIndex('timestamp', 'timestamp');
          cacheStore.createIndex('endpoint', 'endpoint');
        }
      };
    });
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered for offline support:', registration);
        
        // Enable background sync if supported
        if ('sync' in registration) {
          console.log('Background sync supported');
        }
        
        return registration;
      } catch (error) {
        console.error('Service Worker registration failed:', error);
        return null;
      }
    }
    return null;
  }

  // IndexedDB operations
  async storeData(storeName, data) {
    if (!this.db) await this.initIndexedDB();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      const request = Array.isArray(data) 
        ? Promise.all(data.map(item => store.put(item)))
        : store.put(data);

      transaction.oncomplete = () => resolve(true);
      transaction.onerror = () => reject(transaction.error);
    });
  }

  async getData(storeName, key = null, index = null, indexValue = null) {
    if (!this.db) await this.initIndexedDB();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      
      let request;
      
      if (key) {
        request = store.get(key);
      } else if (index && indexValue) {
        const indexObj = store.index(index);
        request = indexObj.getAll(indexValue);
      } else {
        request = store.getAll();
      }

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async deleteData(storeName, key) {
    if (!this.db) await this.initIndexedDB();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      const request = store.delete(key);
      
      transaction.oncomplete = () => resolve(true);
      transaction.onerror = () => reject(transaction.error);
    });
  }

  // Cache API responses
  async cacheAPIResponse(endpoint, data, ttl = 5 * 60 * 1000) { // 5 minutes default
    const cacheData = {
      key: endpoint,
      endpoint: endpoint,
      data: data,
      timestamp: Date.now(),
      ttl: ttl
    };
    
    await this.storeData('api_cache', cacheData);
  }

  async getCachedAPIResponse(endpoint) {
    const cached = await this.getData('api_cache', endpoint);
    
    if (!cached) return null;
    
    // Check if cache is still valid
    const now = Date.now();
    if (now - cached.timestamp > cached.ttl) {
      await this.deleteData('api_cache', endpoint);
      return null;
    }
    
    return cached.data;
  }

  // Store offline actions for later sync
  async storeOfflineAction(type, data, endpoint) {
    const action = {
      type: type, // 'CREATE', 'UPDATE', 'DELETE', 'SUBMIT'
      data: data,
      endpoint: endpoint,
      timestamp: Date.now(),
      retries: 0
    };
    
    await this.storeData('offline_actions', action);
    
    // Try to sync immediately if online
    if (this.isOnline) {
      this.syncOfflineActions();
    }
  }

  // Sync offline actions when online
  async syncOfflineActions() {
    if (!this.isOnline) return;
    
    const actions = await this.getData('offline_actions');
    if (!actions || actions.length === 0) return;
    
    console.log(`Syncing ${actions.length} offline actions...`);
    
    for (const action of actions) {
      try {
        await this.executeOfflineAction(action);
        await this.deleteData('offline_actions', action.id);
        console.log(`Synced action ${action.id}`);
      } catch (error) {
        console.error(`Failed to sync action ${action.id}:`, error);
        
        // Increment retry count
        action.retries = (action.retries || 0) + 1;
        
        // Remove action if too many retries
        if (action.retries > 3) {
          await this.deleteData('offline_actions', action.id);
          console.warn(`Removed action ${action.id} after ${action.retries} failed retries`);
        } else {
          await this.storeData('offline_actions', action);
        }
      }
    }
  }

  async executeOfflineAction(action) {
    // This would integrate with your API service
    const { type, data, endpoint } = action;
    
    switch (type) {
      case 'CREATE_TIMESHEET':
        // Call API to create timesheet
        return fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(data)
        });
        
      case 'SUBMIT_TIMESHEET':
        return fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
      case 'UPDATE_TIMESHEET':
        return fetch(endpoint, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(data)
        });
        
      default:
        throw new Error(`Unknown action type: ${type}`);
    }
  }

  // Handle online/offline status changes
  handleOnlineStatusChange(isOnline) {
    console.log(`Network status changed: ${isOnline ? 'online' : 'offline'}`);
    
    if (isOnline) {
      // Sync when coming back online
      this.syncOfflineActions();
      
      // Show success notification
      this.showConnectionStatus('Back online - syncing data...', 'success');
    } else {
      // Show offline notification
      this.showConnectionStatus('Working offline - changes will sync when connection is restored', 'info');
    }
  }

  showConnectionStatus(message, type = 'info') {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
      color: white;
      border-radius: 4px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.2);
      z-index: 10000;
      font-family: Arial, sans-serif;
      font-size: 14px;
      max-width: 300px;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Remove after 5 seconds
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast);
      }
    }, 5000);
  }

  // Timesheet-specific offline methods
  async storeTimesheetsOffline(timesheets) {
    await this.storeData('timesheets', timesheets);
  }

  async getTimesheetsOffline(userId = null) {
    if (userId) {
      return await this.getData('timesheets', null, 'user_id', userId);
    }
    return await this.getData('timesheets');
  }

  async createTimesheetOffline(timesheetData) {
    // Create a temporary ID for offline timesheet
    const tempId = `temp_${Date.now()}`;
    const timesheet = {
      ...timesheetData,
      id: tempId,
      status: 'draft',
      created_offline: true,
      created_at: new Date().toISOString()
    };
    
    // Store locally
    await this.storeData('timesheets', timesheet);
    
    // Queue for sync
    await this.storeOfflineAction('CREATE_TIMESHEET', timesheetData, '/api/v1/timesheets/create');
    
    return timesheet;
  }

  async submitTimesheetOffline(timesheetId) {
    // Update local status
    const timesheet = await this.getData('timesheets', timesheetId);
    if (timesheet) {
      timesheet.status = 'pending';
      timesheet.submitted_at = new Date().toISOString();
      await this.storeData('timesheets', timesheet);
    }
    
    // Queue for sync
    await this.storeOfflineAction('SUBMIT_TIMESHEET', {}, `/api/v1/timesheets/${timesheetId}/submit`);
  }

  // Check if we have offline data
  async hasOfflineData() {
    const actions = await this.getData('offline_actions');
    return actions && actions.length > 0;
  }

  // Get sync status
  async getSyncStatus() {
    const actions = await this.getData('offline_actions');
    return {
      isOnline: this.isOnline,
      pendingActions: actions ? actions.length : 0,
      lastSyncAttempt: localStorage.getItem('lastSyncAttempt')
    };
  }

  // Manual sync trigger
  async forcSync() {
    localStorage.setItem('lastSyncAttempt', new Date().toISOString());
    return await this.syncOfflineActions();
  }
}

// Global instance
const offlineService = new OfflineService();

export default offlineService;