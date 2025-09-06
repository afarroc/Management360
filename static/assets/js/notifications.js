/**
 * Notification System API Client
 * Handles all notification-related functionality through REST API
 */

class NotificationManager {
    constructor() {
        this.baseUrl = '/chat/api/notifications';
        this.intervalId = null;
        this.refreshTimeout = null;
        this.isInitialized = false;
        this.lastTotalUnread = 0;
    }

    /**
     * Initialize the notification system
     */
    init() {
        if (this.isInitialized) return;

        console.log('Initializing notification system...');
        this.loadNotifications();
        this.setupPeriodicRefresh();
        this.bindEvents();

        this.isInitialized = true;
        console.log('Notification system initialized successfully');

        // Force an immediate refresh after 2 seconds to catch any missed notifications
        setTimeout(() => {
            console.log('Performing initial notification refresh...');
            this.loadNotifications();
        }, 2000);
    }

    /**
     * Load unread notifications from API
     */
    async loadNotifications() {
        try {
            console.log('Loading notifications from:', `${this.baseUrl}/unread/`);
            const response = await fetch(`${this.baseUrl}/unread/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });

            console.log('Notification API response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                console.error('Failed to parse JSON response:', jsonError);
                throw new Error('Invalid JSON response from server');
            }

            console.log('Notification data received:', data);
            console.log('Total unread count:', data.total_unread);
            console.log('Notifications array length:', data.notifications ? data.notifications.length : 'undefined');

            // Validate response data
            if (typeof data !== 'object' || data === null) {
                throw new Error('Invalid response format');
            }

            // Ensure total_unread is a valid number
            const totalUnread = typeof data.total_unread === 'number' ? data.total_unread : 0;
            console.log('Validated total unread:', totalUnread);

            // Only update if count has changed to avoid unnecessary DOM updates
            if (totalUnread !== this.lastTotalUnread) {
                console.log('Count changed, updating badge and notifications');
                this.updateBadge(totalUnread);
                this.displayNotifications(data.notifications || []);
                this.lastTotalUnread = totalUnread;
            } else {
                console.log('No change in notification count, skipping update');
            }

        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError('Failed to load notifications');
        }
    }

    /**
     * Mark notifications as read
     */
    async markAsRead(notificationIds) {
        // Validate input
        if (!Array.isArray(notificationIds)) {
            console.error('notificationIds must be an array');
            this.showError('Invalid notification IDs format');
            return false;
        }

        try {
            const response = await fetch(`${this.baseUrl}/mark-read/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify({ notification_ids: notificationIds })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                await this.loadNotifications(); // Refresh the list
                return true;
            } else {
                throw new Error(data.error || 'Failed to mark notifications as read');
            }

        } catch (error) {
            console.error('Error marking notifications as read:', error);
            this.showError('Failed to mark notifications as read. Please try again.');
            return false;
        }
    }

    /**
     * Update notification badge
     */
    updateBadge(count) {
        console.log('Updating notification badge with count:', count, '(previous:', this.lastTotalUnread, ')');

        const badge = document.getElementById('header-notification-badge');
        const markAllBtn = document.getElementById('header-mark-all-read-btn');

        console.log('Badge element found:', !!badge);
        console.log('Mark all button found:', !!markAllBtn);

        if (!badge) {
            console.error('Notification badge element not found! Available elements:', document.querySelectorAll('[id*="notification"]'));
            return;
        }

        // Update last count
        this.lastTotalUnread = count;

        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'block';
            if (markAllBtn) {
                markAllBtn.style.display = 'block';
                console.log('Mark all button shown');
            }
            console.log('Badge updated to show:', badge.textContent);
        } else {
            badge.style.display = 'none';
            if (markAllBtn) {
                markAllBtn.style.display = 'none';
                console.log('Mark all button hidden');
            }
            console.log('Badge hidden');
        }
    }

    /**
     * Display notifications in the dropdown
     */
    displayNotifications(notifications) {
        const container = document.getElementById('header-notifications-list');

        if (!container) {
            console.warn('Notification container not found');
            return;
        }

        if (notifications.length === 0) {
            container.innerHTML = `
                <div class="text-center p-4">
                    <i class="bi bi-bell-slash fs-1 text-muted"></i>
                    <p class="text-muted mt-2">No notifications</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        notifications.slice(0, 5).forEach(notification => {
            const notificationElement = document.createElement('li');
            notificationElement.className = 'notification-item border-bottom';
            notificationElement.setAttribute('data-id', notification.id);
            notificationElement.innerHTML = `
                <i class="bi bi-chat-dots text-primary me-2"></i>
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${this.escapeHtml(notification.title)}</h6>
                        <p class="mb-1 text-muted small">${this.escapeHtml(notification.message)}</p>
                        <small class="text-muted">${this.formatDate(notification.created_at)}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-secondary ms-2" data-notification-id="${notification.id}">
                        <i class="bi bi-check"></i>
                    </button>
                </div>
            `;
            container.appendChild(notificationElement);
        });

        // Add "View all" link if there are more than 5
        if (notifications.length > 5) {
            const viewAllElement = document.createElement('li');
            viewAllElement.className = 'text-center p-2';
            viewAllElement.innerHTML = `
                <a href="/chat/room/" class="text-primary">
                    View all ${notifications.length} notifications
                </a>
            `;
            container.appendChild(viewAllElement);
        }
    }

    /**
     * Setup periodic refresh
     */
    setupPeriodicRefresh() {
        // Refresh every 1 second for ultra-fast responsiveness
        this.intervalId = setInterval(() => {
            this.loadNotifications();
        }, 1000);
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Mark individual notification as read
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-notification-id]')) {
                const notificationId = e.target.closest('[data-notification-id]').getAttribute('data-notification-id');
                if (notificationId) {
                    this.markAsRead([notificationId]);
                }
            }
        });

        // Mark all notifications as read
        const markAllBtn = document.getElementById('header-mark-all-read-btn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', async () => {
                try {
                    const success = await this.markAsRead([]); // Empty array marks all as read
                    if (success) {
                        console.log('All notifications marked as read');
                    }
                } catch (error) {
                    console.error('Error marking all notifications as read:', error);
                    this.showError('Failed to mark all notifications as read');
                }
            });
        } else {
            console.warn('Mark all button not found');
        }

        // Listen for new messages to update counter immediately
        this.setupWebSocketListener();
    }

    /**
     * Setup WebSocket listener for real-time updates
     */
    setupWebSocketListener() {
        // Listen for chat messages and update counter immediately
        document.addEventListener('chatMessageReceived', () => {
            console.log('New chat message received, updating notifications immediately...');
            // Update immediately when a new message is received
            this.forceRefresh();
        });

        // Also listen for any WebSocket messages that might indicate new content
        document.addEventListener('websocketMessage', (event) => {
            const data = event.detail;
            if (data.type === 'chat_message' || data.type === 'message') {
                console.log('WebSocket message received, updating notifications...');
                this.forceRefresh();
            }
        });

        // Listen for storage events (in case multiple tabs are open)
        window.addEventListener('storage', (event) => {
            if (event.key === 'chat_new_message') {
                console.log('Storage event detected, updating notifications...');
                this.forceRefresh();
            }
        });

        // Listen for widget events
        document.addEventListener('messagesMarkedAsRead', (event) => {
            console.log('Widget marked messages as read, updating notifications...');
            this.forceRefresh();
        });

        // Listen for new messages from widget
        document.addEventListener('widgetNewMessage', (event) => {
            console.log('New message from widget, updating notifications...');
            this.forceRefresh();
        });

        // Listen for room view events to mark messages as read
        document.addEventListener('roomViewed', (event) => {
            const roomId = event.detail?.roomId;
            if (roomId) {
                console.log(`Room ${roomId} viewed, marking messages as read...`);
                // Mark messages as read for this room
                this.markRoomMessagesAsRead(roomId);
            }
        });
    }

    /**
     * Force immediate refresh of notifications
     */
    forceRefresh() {
        console.log('Forcing immediate notification refresh...');
        // Clear any pending refresh
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }
        // Refresh immediately
        this.loadNotifications();
    }

    /**
     * Mark messages in a specific room as read
     */
    async markRoomMessagesAsRead(roomId) {
        try {
            console.log(`Marking messages as read for room ${roomId}...`);
            const response = await fetch('/chat/api/chat/reset-unread/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify({ room_id: roomId })
            });

            if (response.ok) {
                console.log(`Messages marked as read for room ${roomId}`);
                // Refresh notifications after marking as read
                setTimeout(() => this.loadNotifications(), 500);
            } else {
                console.error('Failed to mark room messages as read:', response.status);
            }
        } catch (error) {
            console.error('Error marking room messages as read:', error);
        }
    }

    /**
     * Get CSRF token
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.querySelector('#csrf-form [name=csrfmiddlewaretoken]')?.value ||
               document.querySelector('#dummy-csrf-form [name=csrfmiddlewaretoken]')?.value || '';
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleString();
        } catch (e) {
            return dateString;
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        // You can implement a toast notification system here
        console.error(message);

        // For now, just show a simple alert
        // In production, you'd want a proper toast system
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        errorDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(errorDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    /**
     * Cleanup resources
     */
    destroy() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isInitialized = false;
    }

    /**
     * Debug function to check notification system status
     */
    debug() {
        console.log('=== NOTIFICATION SYSTEM DEBUG ===');
        console.log('Is initialized:', this.isInitialized);
        console.log('Base URL:', this.baseUrl);
        console.log('Interval ID:', this.intervalId);
        console.log('Last total unread:', this.lastTotalUnread);
        console.log('Badge element:', document.getElementById('header-notification-badge'));
        console.log('Notifications list element:', document.getElementById('header-notifications-list'));
        console.log('Mark all button:', document.getElementById('header-mark-all-read-btn'));
        console.log('CSRF Token available:', !!this.getCSRFToken());
        console.log('Current user authenticated:', this.checkAuthentication());
        console.log('==================================');
    }

    /**
     * Test function to create a test notification
     */
    async testCreateNotification() {
        try {
            console.log('Creating test notification...');
            const response = await fetch(`${this.baseUrl}/test-create/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    message: 'Test notification from frontend',
                    room_id: 1
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Test notification created:', result);
                // Refresh notifications after creating test
                setTimeout(() => this.loadNotifications(), 1000);
            } else {
                console.error('Failed to create test notification:', response.status);
            }
        } catch (error) {
            console.error('Error creating test notification:', error);
        }
    }

    /**
     * Check if user is authenticated
     */
    checkAuthentication() {
        return document.querySelector('[data-user-authenticated="true"]') ||
               document.body.classList.contains('authenticated') ||
               document.body.hasAttribute('data-user-authenticated') ||
               document.querySelector('meta[name="user-authenticated"][content="true"]') ||
               (window.django && window.django.user && window.django.user.is_authenticated);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize for authenticated users
    const isAuthenticated = document.querySelector('[data-user-authenticated="true"]') ||
                            document.body.classList.contains('authenticated') ||
                            document.body.hasAttribute('data-user-authenticated') ||
                            document.querySelector('meta[name="user-authenticated"][content="true"]') ||
                            (window.django && window.django.user && window.django.user.is_authenticated);

    console.log('Notification system check - isAuthenticated:', isAuthenticated);
    console.log('Body attributes:', document.body.attributes);
    console.log('Body classes:', document.body.classList);

    if (isAuthenticated) {
        console.log('Initializing notification system...');
        const notificationManager = new NotificationManager();
        notificationManager.init();

        // Make debug and test functions available globally
        window.debugNotifications = () => notificationManager.debug();
        window.testCreateNotification = () => notificationManager.testCreateNotification();
        window.forceNotificationRefresh = () => notificationManager.forceRefresh();

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            notificationManager.destroy();
        });
    } else {
        console.log('User not authenticated, skipping notification initialization');
    }
});

// Export for potential use in other scripts
window.NotificationManager = NotificationManager;