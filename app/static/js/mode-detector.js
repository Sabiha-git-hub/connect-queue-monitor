/**
 * Mode Detector for Amazon Connect Third-Party App
 * 
 * This JavaScript module detects whether the app is running:
 * 1. EMBEDDED MODE: Inside Amazon Connect's agent workspace (as an iframe)
 * 2. STANDALONE MODE: On its own in a regular browser window
 * 
 * Key Concepts for Beginners:
 * - Iframe: A webpage embedded inside another webpage (like a picture-in-picture)
 * - window.self: Reference to the current window
 * - window.top: Reference to the topmost window (parent of all iframes)
 * - window.parent: Reference to the immediate parent window
 * 
 * Why This Matters:
 * When embedded in Amazon Connect, we can automatically detect the agent.
 * When standalone, the agent needs to manually enter their username.
 */

class ModeDetector {
    /**
     * Create a new ModeDetector instance.
     * 
     * The constructor initializes the detector but doesn't run detection yet.
     * Call detectMode() to actually perform the detection.
     */
    constructor() {
        // Store detection results here
        this.mode = null;           // Will be 'embedded' or 'standalone'
        this.isInIframe = false;    // True if running in any iframe
        this.isInConnect = false;   // True if parent is Amazon Connect
        this.detected = false;      // True after detection runs
    }

    /**
     * Detect if the app is running inside an iframe.
     * 
     * How it works:
     * - If window.self === window.top, we're NOT in an iframe
     * - If window.self !== window.top, we ARE in an iframe
     * 
     * Think of it like this:
     * - window.self is "me" (this window)
     * - window.top is "the main window"
     * - If "me" is not "the main window", then I'm inside something else (iframe)
     * 
     * @returns {boolean} True if running in an iframe, false otherwise
     */
    _isRunningInIframe() {
        try {
            // Compare current window with top window
            return window.self !== window.top;
        } catch (e) {
            // If we get an error, it's likely due to cross-origin restrictions
            // This usually means we ARE in an iframe but can't access parent
            console.log('Cross-origin iframe detected (likely embedded)');
            return true;
        }
    }

    /**
     * Detect if the parent window is Amazon Connect.
     * 
     * How it works:
     * We check the parent window's URL to see if it contains Amazon Connect domains.
     * 
     * Amazon Connect URLs typically look like:
     * - https://[instance-name].my.connect.aws/
     * - https://[instance-name].awsapps.com/connect/
     * 
     * Security Note:
     * Due to browser security (CORS), we might not be able to read parent URL.
     * If we can't read it, we assume it's Amazon Connect (safe assumption in production).
     * 
     * @returns {boolean} True if parent appears to be Amazon Connect
     */
    _isParentAmazonConnect() {
        // Only check if we're actually in an iframe
        if (!this.isInIframe) {
            return false;
        }

        try {
            // Try to access parent window's location
            const parentUrl = window.parent.location.href;
            
            // Check if URL contains Amazon Connect domains
            const isConnect = 
                parentUrl.includes('.my.connect.aws') ||
                parentUrl.includes('.awsapps.com/connect') ||
                parentUrl.includes('connect.aws');
            
            console.log('Parent URL detected:', parentUrl);
            console.log('Is Amazon Connect:', isConnect);
            
            return isConnect;
            
        } catch (e) {
            // Cross-origin error - can't read parent URL
            // In production, this likely means we're embedded in Amazon Connect
            // (Amazon Connect uses a different domain than our app)
            console.log('Cannot access parent URL (cross-origin). Assuming Amazon Connect.');
            
            // In a real deployment, if we're in an iframe and can't read parent,
            // it's very likely Amazon Connect. For development/testing, you might
            // want to return false here.
            return true;
        }
    }

    /**
     * Perform mode detection and return the results.
     * 
     * This is the main method you call to detect the mode.
     * It runs all the checks and returns a result object.
     * 
     * @returns {Object} Detection results with the following properties:
     *   - mode: 'embedded' or 'standalone'
     *   - isInIframe: boolean - true if running in any iframe
     *   - isInConnect: boolean - true if parent is Amazon Connect
     *   - useAutomaticDetection: boolean - true if should use Streams API
     *   - useManualLogin: boolean - true if should show login form
     */
    detectMode() {
        console.log('=== Mode Detection Started ===');
        
        // Step 1: Check if we're in an iframe
        this.isInIframe = this._isRunningInIframe();
        console.log('Running in iframe:', this.isInIframe);
        
        // Step 2: If in iframe, check if parent is Amazon Connect
        if (this.isInIframe) {
            this.isInConnect = this._isParentAmazonConnect();
            console.log('Parent is Amazon Connect:', this.isInConnect);
        }
        
        // Step 3: Determine the mode
        if (this.isInIframe && this.isInConnect) {
            // We're embedded in Amazon Connect
            this.mode = 'embedded';
            console.log('✓ Mode: EMBEDDED (inside Amazon Connect)');
        } else {
            // We're running standalone
            this.mode = 'standalone';
            console.log('✓ Mode: STANDALONE (independent browser window)');
        }
        
        // Mark detection as complete
        this.detected = true;
        
        // Return results object
        const results = {
            mode: this.mode,
            isInIframe: this.isInIframe,
            isInConnect: this.isInConnect,
            useAutomaticDetection: this.mode === 'embedded',
            useManualLogin: this.mode === 'standalone'
        };
        
        console.log('=== Mode Detection Complete ===');
        console.log('Results:', results);
        
        return results;
    }

    /**
     * Get the current mode (must call detectMode() first).
     * 
     * @returns {string|null} 'embedded', 'standalone', or null if not detected yet
     */
    getMode() {
        if (!this.detected) {
            console.warn('Mode not detected yet. Call detectMode() first.');
            return null;
        }
        return this.mode;
    }

    /**
     * Check if automatic agent detection should be used.
     * 
     * Automatic detection uses the Amazon Connect Streams API to get
     * the agent's username without asking them to log in.
     * 
     * @returns {boolean} True if should use automatic detection
     */
    shouldUseAutomaticDetection() {
        return this.detected && this.mode === 'embedded';
    }

    /**
     * Check if manual login form should be shown.
     * 
     * Manual login requires the agent to type their username.
     * 
     * @returns {boolean} True if should show manual login form
     */
    shouldUseManualLogin() {
        return this.detected && this.mode === 'standalone';
    }
}

/**
 * Initialize the app based on detected mode.
 * 
 * This function is called after mode detection to set up the appropriate
 * user interface and behavior.
 * 
 * @param {Object} modeResults - Results from ModeDetector.detectMode()
 */
function initializeApp(modeResults) {
    console.log('=== Initializing App ===');
    console.log('Mode:', modeResults.mode);
    
    // Get UI elements (these will be defined in the HTML templates)
    const loginForm = document.getElementById('login-form');
    const ccpContainer = document.getElementById('ccp-container');
    const modeIndicator = document.getElementById('mode-indicator');
    
    if (modeResults.mode === 'embedded') {
        // EMBEDDED MODE: Hide login form, prepare for Streams API
        console.log('Setting up EMBEDDED mode...');
        
        if (loginForm) {
            loginForm.style.display = 'none';
            console.log('✓ Login form hidden');
        }
        
        if (ccpContainer) {
            // CCP container will be used by Streams API (Task 5)
            console.log('✓ CCP container ready for Streams API');
        }
        
        if (modeIndicator) {
            modeIndicator.textContent = 'Embedded Mode (Automatic Detection)';
            modeIndicator.className = 'mode-badge embedded';
        }
        
        // Note: Streams API initialization will happen in Task 5
        console.log('→ Next: Initialize Streams API (Task 5)');
        
    } else {
        // STANDALONE MODE: Show login form
        console.log('Setting up STANDALONE mode...');
        
        if (loginForm) {
            loginForm.style.display = 'block';
            console.log('✓ Login form visible');
        }
        
        if (ccpContainer) {
            // Hide CCP container in standalone mode
            ccpContainer.style.display = 'none';
            console.log('✓ CCP container hidden');
        }
        
        if (modeIndicator) {
            modeIndicator.textContent = 'Standalone Mode (Manual Login)';
            modeIndicator.className = 'mode-badge standalone';
        }
        
        console.log('→ User will enter username manually');
    }
    
    console.log('=== App Initialization Complete ===');
}

// Export for use in other modules
// This allows other JavaScript files to use ModeDetector
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment (for testing)
    module.exports = { ModeDetector, initializeApp };
}
