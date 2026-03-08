/**
 * Main Application Controller
 * 
 * This module coordinates between mode detection, Streams API integration,
 * and the application's login/queue viewing flows. It handles both embedded
 * mode (automatic detection via Streams API) and standalone mode (manual login).
 */

class QueueMonitorApp {
    constructor() {
        this.modeDetector = null;
        this.streamsAPI = null;
        this.modeInfo = null;
    }

    /**
     * Initialize the application
     * Detects mode and triggers appropriate flow
     */
    initialize() {
        console.log('🚀 Initializing Amazon Connect Queue Monitor...');
        
        // Step 1: Detect the mode (embedded vs standalone)
        this.modeDetector = new ModeDetector();
        this.modeInfo = this.modeDetector.detectMode();
        
        console.log('Mode detected:', this.modeInfo);
        
        // Step 2: Update UI with mode information
        this.updateModeIndicator();
        
        // Step 3: Initialize based on mode
        if (this.modeInfo.isEmbedded && this.modeInfo.isAmazonConnect) {
            this.initializeEmbeddedMode();
        } else {
            this.initializeStandaloneMode();
        }
    }

    /**
     * Update the mode indicator badge in the UI
     */
    updateModeIndicator() {
        const modeIndicator = document.getElementById('mode-indicator');
        const modeText = document.getElementById('mode-text');
        
        if (!modeIndicator || !modeText) return;
        
        if (this.modeInfo.isEmbedded) {
            modeText.textContent = '🔗 Embedded Mode (Amazon Connect)';
            modeIndicator.classList.add('mode-embedded');
        } else {
            modeText.textContent = '💻 Standalone Mode (Development)';
            modeIndicator.classList.add('mode-standalone');
        }
        modeIndicator.style.display = 'block';
    }

    /**
     * Initialize embedded mode with automatic agent detection
     * Uses Amazon Connect Streams API to detect the logged-in agent
     */
    initializeEmbeddedMode() {
        console.log('📡 Starting automatic agent detection via Streams API...');
        
        // Hide login form, show loading
        this.showElement('loading-container');
        this.hideElement('login-container');
        
        // Get CCP URL from configuration
        const ccpUrl = this.getCCPUrl();
        if (!ccpUrl) {
            console.error('❌ CCP URL not configured');
            this.handleAutoDetectionFailure('CCP URL not configured');
            return;
        }
        
        // Initialize Streams API
        this.streamsAPI = new StreamsAPIIntegration(ccpUrl, 'ccp-container');
        
        this.streamsAPI.initialize()
            .then(agentData => {
                console.log('✅ Agent detected:', agentData.username);
                return this.performAutoLogin(agentData.username);
            })
            .catch(error => {
                console.error('❌ Streams API initialization failed:', error);
                this.handleAutoDetectionFailure('Automatic detection failed. Please use manual login below.');
            });
    }

    /**
     * Initialize standalone mode with manual login form
     */
    initializeStandaloneMode() {
        console.log('📝 Standalone mode - showing manual login form');
        this.showElement('login-container');
        this.hideElement('loading-container');
    }

    /**
     * Perform automatic login with detected username
     * @param {string} username - The detected agent username
     * @returns {Promise} - Resolves when login is complete
     */
    performAutoLogin(username) {
        return fetch('/agent/auto-login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Redirect to queue view
                window.location.href = '/agent/queues';
            } else {
                // Show error
                this.handleAutoDetectionFailure(data.error);
            }
        })
        .catch(error => {
            console.error('❌ Auto-login failed:', error);
            this.handleAutoDetectionFailure('Automatic login failed. Please try manual login.');
        });
    }

    /**
     * Handle automatic detection failure
     * Falls back to manual login form
     * @param {string} errorMessage - Error message to display
     */
    handleAutoDetectionFailure(errorMessage) {
        this.hideElement('loading-container');
        this.showElement('login-container');
        this.showError(errorMessage, 'login-container');
    }

    /**
     * Get CCP URL from page configuration
     * @returns {string|null} - CCP URL or null if not found
     */
    getCCPUrl() {
        // Try to get from data attribute or global config
        const container = document.getElementById('ccp-container');
        if (container && container.dataset.ccpUrl) {
            return container.dataset.ccpUrl;
        }
        
        // Fallback: try to construct from window config
        if (window.CONNECT_INSTANCE_URL) {
            return `${window.CONNECT_INSTANCE_URL}/ccp-v2`;
        }
        
        return null;
    }

    /**
     * Refresh queue data without page reload
     * Makes AJAX request to refresh endpoint and updates the UI
     */
    refreshQueues() {
        console.log('🔄 Refreshing queue data...');
        
        // Get UI elements
        const refreshBtn = document.getElementById('refresh-btn');
        const loadingIndicator = document.getElementById('loading-indicator');
        const errorContainer = document.getElementById('error-container');
        
        // Disable refresh button and show loading
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.textContent = '⏳ Refreshing...';
        }
        
        this.showElement('loading-indicator');
        this.hideElement('error-container');
        
        // Make AJAX request to refresh endpoint
        fetch('/agent/queues/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('✅ Queue data refreshed successfully');
                
                // Update the queue table
                this.updateQueueTable(data.queues);
                
                // Update timestamp
                this.updateTimestamp();
                
                // Update total contacts
                this.updateTotalContacts(data.queues);
                
            } else {
                console.error('❌ Refresh failed:', data.error);
                this.showError(data.error, 'error-container');
            }
        })
        .catch(error => {
            console.error('❌ Network error during refresh:', error);
            this.showError('Network error. Please try again.', 'error-container');
        })
        .finally(() => {
            // Re-enable refresh button and hide loading
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '🔄 Refresh Queues';
            }
            this.hideElement('loading-indicator');
        });
    }

    /**
     * Update queue table with new data
     * @param {Array} queues - Array of queue objects with metrics
     */
    updateQueueTable(queues) {
        const tbody = document.getElementById('queue-tbody');
        if (!tbody) return;
        
        // Clear existing rows
        tbody.innerHTML = '';
        
        // Add new rows
        queues.forEach(queue => {
            const row = this.createQueueRow(queue);
            tbody.appendChild(row);
        });
    }

    /**
     * Create a table row for a queue
     * @param {Object} queue - Queue object with name, count, and error info
     * @returns {HTMLTableRowElement} - The created row element
     */
    createQueueRow(queue) {
        const row = document.createElement('tr');
        
        // Determine row class based on call count
        let rowClass = 'queue-row';
        if (queue.contacts_in_queue > 10) {
            rowClass += ' high-volume';
        } else if (queue.contacts_in_queue > 5) {
            rowClass += ' medium-volume';
        }
        row.className = rowClass;
        
        // Queue name cell
        const nameCell = document.createElement('td');
        nameCell.className = 'queue-name';
        nameCell.textContent = queue.queue_name;
        row.appendChild(nameCell);
        
        // Count cell
        const countCell = document.createElement('td');
        countCell.className = 'queue-count';
        if (queue.error) {
            countCell.innerHTML = `<span class="error-indicator" title="${queue.error}">⚠️ Error</span>`;
        } else {
            countCell.innerHTML = `<span class="count-badge">${queue.contacts_in_queue}</span>`;
        }
        row.appendChild(countCell);
        
        // Status cell
        const statusCell = document.createElement('td');
        statusCell.className = 'queue-status';
        if (queue.error) {
            statusCell.innerHTML = `<span class="status-error" title="${queue.error}">❌ Failed</span>`;
        } else {
            statusCell.innerHTML = '<span class="status-ok">✅ Active</span>';
        }
        row.appendChild(statusCell);
        
        return row;
    }

    /**
     * Update the last updated timestamp
     */
    updateTimestamp() {
        const timestampElement = document.getElementById('timestamp');
        if (timestampElement) {
            const now = new Date();
            timestampElement.textContent = now.toLocaleTimeString();
        }
    }

    /**
     * Update total contacts count
     * @param {Array} queues - Array of queue objects
     */
    updateTotalContacts(queues) {
        const totalElement = document.getElementById('total-contacts');
        if (totalElement) {
            const total = queues.reduce((sum, q) => sum + (q.contacts_in_queue || 0), 0);
            totalElement.textContent = total;
        }
    }

    /**
     * Show an error message in a container
     * @param {string} message - Error message to display
     * @param {string} containerId - ID of container to show error in
     */
    showError(message, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // If container has error-text child, update it
        const errorText = document.getElementById('error-text');
        if (errorText) {
            errorText.textContent = message;
            container.style.display = 'block';
        } else {
            // Otherwise, create error div and append
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.innerHTML = `<strong>⚠️ Error:</strong> ${message}`;
            container.appendChild(errorDiv);
        }
    }

    /**
     * Show an element by ID
     * @param {string} elementId - ID of element to show
     */
    showElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'block';
        }
    }

    /**
     * Hide an element by ID
     * @param {string} elementId - ID of element to hide
     */
    hideElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    }
}

// Global instance for easy access
let queueMonitorApp = null;

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    queueMonitorApp = new QueueMonitorApp();
    queueMonitorApp.initialize();
});

// Global function for refresh button (called from HTML)
function refreshQueues() {
    if (queueMonitorApp) {
        queueMonitorApp.refreshQueues();
    }
}
