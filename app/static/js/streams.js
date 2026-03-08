/**
 * Amazon Connect Streams API Integration
 * 
 * This module integrates with Amazon Connect's Streams API to automatically
 * detect the logged-in agent when the app is embedded in the agent workspace.
 * 
 * Key Concepts for Beginners:
 * - Streams API: Amazon Connect's JavaScript library that lets you interact with the agent workspace
 * - CCP (Contact Control Panel): The interface agents use to handle calls
 * - Agent Object: Represents the logged-in agent with their configuration and state
 * - Callback: A function that runs when something happens (like agent login)
 * 
 * Why This Matters:
 * When your app is embedded in Amazon Connect, the Streams API gives you access to:
 * - Who the agent is (username, ID)
 * - Agent state (available, on call, offline)
 * - Contact information (current calls)
 * 
 * This means no login form needed - the app automatically knows who's using it!
 */

class StreamsAPIIntegration {
    /**
     * Create a new Streams API integration instance.
     * 
     * @param {string} ccpUrl - The URL of your Amazon Connect instance's CCP
     *                          Example: "https://myinstance.my.connect.aws/ccp-v2"
     * @param {string} containerId - The HTML element ID where CCP will be embedded
     *                               Example: "ccp-container"
     */
    constructor(ccpUrl, containerId = 'ccp-container') {
        // Store configuration
        this.ccpUrl = ccpUrl;
        this.containerId = containerId;
        
        // State tracking
        this.initialized = false;      // True after successful initialization
        this.agentUsername = null;     // Will store the detected agent username
        this.agentData = null;         // Will store full agent configuration
        this.initializationError = null; // Stores any initialization errors
        
        // Timeout configuration (10 seconds as per requirements)
        this.INITIALIZATION_TIMEOUT = 10000; // 10 seconds in milliseconds
        this.initializationTimer = null;
        
        console.log('StreamsAPIIntegration created');
        console.log('CCP URL:', this.ccpUrl);
        console.log('Container ID:', this.containerId);
    }

    /**
     * Initialize the Streams API connection.
     * 
     * This method:
     * 1. Embeds the CCP in a hidden container
     * 2. Connects to the Streams API
     * 3. Subscribes to agent events
     * 4. Extracts agent username
     * 5. Times out after 10 seconds if unsuccessful
     * 
     * @returns {Promise<string>} Resolves with agent username, rejects on error
     */
    initialize() {
        return new Promise((resolve, reject) => {
            console.log('=== Initializing Streams API ===');
            
            // Check if connect library is loaded
            if (typeof connect === 'undefined') {
                const error = 'Amazon Connect Streams library not loaded. Include the script from Amazon Connect CDN.';
                console.error(error);
                this.initializationError = error;
                reject(new Error(error));
                return;
            }
            
            // Check if container exists
            const container = document.getElementById(this.containerId);
            if (!container) {
                const error = `Container element '${this.containerId}' not found in DOM.`;
                console.error(error);
                this.initializationError = error;
                reject(new Error(error));
                return;
            }
            
            // Set up timeout
            this.initializationTimer = setTimeout(() => {
                if (!this.initialized) {
                    const error = 'Streams API initialization timeout (10 seconds exceeded)';
                    console.error(error);
                    this.initializationError = error;
                    reject(new Error(error));
                }
            }, this.INITIALIZATION_TIMEOUT);
            
            try {
                // Initialize the CCP
                console.log('Initializing CCP...');
                connect.core.initCCP(container, {
                    ccpUrl: this.ccpUrl,
                    loginPopup: false,               // Don't show login popup
                    loginPopupAutoClose: true,       // Auto-close if it appears
                    softphone: {
                        allowFramedSoftphone: true   // Allow softphone in iframe
                    }
                });
                
                console.log('✓ CCP initialization started');
                
                // Subscribe to agent events
                console.log('Subscribing to agent events...');
                connect.agent((agent) => {
                    console.log('✓ Agent event received!');
                    
                    try {
                        // Extract agent data
                        this.agentData = this._extractAgentData(agent);
                        this.agentUsername = this.agentData.username;
                        
                        console.log('✓ Agent username extracted:', this.agentUsername);
                        
                        // Mark as initialized
                        this.initialized = true;
                        
                        // Clear timeout
                        if (this.initializationTimer) {
                            clearTimeout(this.initializationTimer);
                            this.initializationTimer = null;
                        }
                        
                        console.log('=== Streams API Initialization Complete ===');
                        
                        // Resolve the promise with username
                        resolve(this.agentUsername);
                        
                    } catch (error) {
                        console.error('Error extracting agent data:', error);
                        this.initializationError = error.message;
                        
                        // Clear timeout
                        if (this.initializationTimer) {
                            clearTimeout(this.initializationTimer);
                        }
                        
                        reject(error);
                    }
                });
                
                console.log('✓ Agent event subscription registered');
                
            } catch (error) {
                console.error('Error during Streams API initialization:', error);
                this.initializationError = error.message;
                
                // Clear timeout
                if (this.initializationTimer) {
                    clearTimeout(this.initializationTimer);
                }
                
                reject(error);
            }
        });
    }

    /**
     * Extract agent data from the Streams API agent object.
     * 
     * The agent object from Streams API contains lots of information.
     * We need to extract the username in a format that matches what
     * the Amazon Connect API expects.
     * 
     * Agent Configuration Structure:
     * {
     *   username: "agent-username",
     *   name: "Agent Full Name",
     *   softphoneEnabled: true,
     *   extension: "1234",
     *   routingProfile: {...},
     *   ...
     * }
     * 
     * @param {Object} agent - The agent object from Streams API
     * @returns {Object} Extracted agent data with username
     * @private
     */
    _extractAgentData(agent) {
        console.log('Extracting agent data...');
        
        // Get agent configuration
        const config = agent.getConfiguration();
        console.log('Agent configuration:', config);
        
        // Extract username
        // The username is typically in config.username
        let username = config.username;
        
        // Sometimes the username includes the instance ID prefix
        // Format: "instance-id/username" or just "username"
        // We want just the username part
        if (username && username.includes('/')) {
            // Split by '/' and take the last part
            const parts = username.split('/');
            username = parts[parts.length - 1];
            console.log('Extracted username from path:', username);
        }
        
        // Validate username
        if (!username || username.trim() === '') {
            throw new Error('Agent username is empty or invalid');
        }
        
        // Return extracted data
        const extractedData = {
            username: username,
            fullName: config.name || 'Unknown',
            extension: config.extension || null,
            routingProfile: config.routingProfile || null,
            softphoneEnabled: config.softphoneEnabled || false
        };
        
        console.log('Extracted agent data:', extractedData);
        
        return extractedData;
    }

    /**
     * Get the detected agent username.
     * 
     * Call this after initialize() completes successfully.
     * 
     * @returns {string|null} Agent username or null if not initialized
     */
    getAgentUsername() {
        if (!this.initialized) {
            console.warn('Streams API not initialized yet. Call initialize() first.');
            return null;
        }
        return this.agentUsername;
    }

    /**
     * Get full agent data.
     * 
     * @returns {Object|null} Agent data object or null if not initialized
     */
    getAgentData() {
        if (!this.initialized) {
            console.warn('Streams API not initialized yet. Call initialize() first.');
            return null;
        }
        return this.agentData;
    }

    /**
     * Check if Streams API is initialized.
     * 
     * @returns {boolean} True if initialized successfully
     */
    isInitialized() {
        return this.initialized;
    }

    /**
     * Get initialization error if any.
     * 
     * @returns {string|null} Error message or null if no error
     */
    getInitializationError() {
        return this.initializationError;
    }

    /**
     * Optional: Subscribe to agent state changes.
     * 
     * This is for future enhancements. You can use this to:
     * - Show agent status (Available, On Call, Offline)
     * - Update UI based on agent state
     * - Track agent activity
     * 
     * @param {Function} callback - Function to call when agent state changes
     *                              Receives agent state object as parameter
     */
    onAgentStateChange(callback) {
        if (typeof connect === 'undefined') {
            console.error('Streams API not loaded');
            return;
        }
        
        connect.agent((agent) => {
            // Subscribe to state changes
            agent.onStateChange((agentStateChange) => {
                console.log('Agent state changed:', agentStateChange);
                
                // Get current state
                const currentState = agent.getState();
                console.log('Current state:', currentState);
                
                // Call the callback with state information
                if (callback && typeof callback === 'function') {
                    callback({
                        state: currentState.name,
                        type: currentState.type,
                        timestamp: new Date()
                    });
                }
            });
        });
    }
}

/**
 * Helper function to check if Streams API library is loaded.
 * 
 * Call this before trying to use StreamsAPIIntegration to ensure
 * the Amazon Connect Streams library is available.
 * 
 * @returns {boolean} True if Streams API library is loaded
 */
function isStreamsAPIAvailable() {
    return typeof connect !== 'undefined';
}

/**
 * Helper function to load Streams API library dynamically.
 * 
 * If you haven't included the Streams API script in your HTML,
 * you can use this function to load it dynamically.
 * 
 * @param {string} instanceUrl - Your Amazon Connect instance URL
 * @returns {Promise<void>} Resolves when library is loaded
 */
function loadStreamsAPI(instanceUrl) {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (isStreamsAPIAvailable()) {
            console.log('Streams API already loaded');
            resolve();
            return;
        }
        
        console.log('Loading Streams API library...');
        
        // Create script element
        const script = document.createElement('script');
        script.src = `${instanceUrl}/connect/static/connect-streams-min.js`;
        script.type = 'text/javascript';
        
        // Handle successful load
        script.onload = () => {
            console.log('✓ Streams API library loaded successfully');
            resolve();
        };
        
        // Handle load error
        script.onerror = () => {
            const error = 'Failed to load Streams API library';
            console.error(error);
            reject(new Error(error));
        };
        
        // Add script to page
        document.head.appendChild(script);
    });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment (for testing)
    module.exports = { 
        StreamsAPIIntegration, 
        isStreamsAPIAvailable,
        loadStreamsAPI
    };
}
