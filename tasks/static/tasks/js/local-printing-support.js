/**
 * Local Printing Support Detection
 * 
 * This module provides functions to detect browser support for WebUSB and WebSerial APIs
 * and displays appropriate warnings for unsupported browsers.
 */

class LocalPrintingSupportDetector {
    constructor() {
        this.webUSBSupported = null;
        this.webSerialSupported = null;
        this.compatibilityChecked = false;
    }

    /**
     * Detect if the current browser supports WebUSB API
     * @returns {boolean} True if WebUSB is supported, false otherwise
     */
    detectWebUSBSupport() {
        if (this.webUSBSupported !== null) {
            return this.webUSBSupported;
        }

        try {
            // Check if the WebUSB API is available
            this.webUSBSupported = 'usb' in navigator && 'requestDevice' in navigator.usb;
            
            if (this.webUSBSupported) {
                console.log('✅ WebUSB API is supported in this browser');
            } else {
                console.warn('❌ WebUSB API is not supported in this browser');
            }
        } catch (error) {
            console.error('Error detecting WebUSB support:', error);
            this.webUSBSupported = false;
        }

        return this.webUSBSupported;
    }

    /**
     * Detect if the current browser supports WebSerial API
     * @returns {boolean} True if WebSerial is supported, false otherwise
     */
    detectWebSerialSupport() {
        if (this.webSerialSupported !== null) {
            return this.webSerialSupported;
        }

        try {
            // Check if the WebSerial API is available
            this.webSerialSupported = 'serial' in navigator && 'requestPort' in navigator.serial;
            
            if (this.webSerialSupported) {
                console.log('✅ WebSerial API is supported in this browser');
            } else {
                console.warn('❌ WebSerial API is not supported in this browser');
            }
        } catch (error) {
            console.error('Error detecting WebSerial support:', error);
            this.webSerialSupported = false;
        }

        return this.webSerialSupported;
    }

    /**
     * Check if local printing is supported (either WebUSB or WebSerial)
     * @returns {boolean} True if at least one local printing method is supported
     */
    supportsLocalPrinting() {
        const webUSBSupported = this.detectWebUSBSupport();
        const webSerialSupported = this.detectWebSerialSupport();
        
        return webUSBSupported || webSerialSupported;
    }

    /**
     * Get detailed browser compatibility information
     * @returns {object} Detailed compatibility info
     */
    getBrowserCompatibilityInfo() {
        const userAgent = navigator.userAgent;
        const isChrome = userAgent.indexOf('Chrome') !== -1;
        const isEdge = userAgent.indexOf('Edge') !== -1;
        const isFirefox = userAgent.indexOf('Firefox') !== -1;
        const isSafari = userAgent.indexOf('Safari') !== -1 && userAgent.indexOf('Chrome') === -1;
        
        return {
            browser: this.getBrowserName(),
            isChrome,
            isEdge,
            isFirefox,
            isSafari,
            webUSBSupported: this.detectWebUSBSupport(),
            webSerialSupported: this.detectWebSerialSupport(),
            supportsLocalPrinting: this.supportsLocalPrinting(),
            userAgent: userAgent
        };
    }

    /**
     * Get the browser name
     * @returns {string} Browser name
     */
    getBrowserName() {
        const userAgent = navigator.userAgent;
        
        if (userAgent.indexOf('Chrome') !== -1 && userAgent.indexOf('Edge') === -1) {
            return 'Chrome';
        } else if (userAgent.indexOf('Edge') !== -1) {
            return 'Edge';
        } else if (userAgent.indexOf('Firefox') !== -1) {
            return 'Firefox';
        } else if (userAgent.indexOf('Safari') !== -1) {
            return 'Safari';
        } else if (userAgent.indexOf('Opera') !== -1) {
            return 'Opera';
        } else {
            return 'Unknown';
        }
    }

    /**
     * Display browser compatibility warning if needed
     */
    showBrowserCompatibilityWarning() {
        const compatInfo = this.getBrowserCompatibilityInfo();
        
        if (!compatInfo.supportsLocalPrinting) {
            this.displayUnsupportedBrowserWarning(compatInfo);
        } else {
            // Show which APIs are supported
            this.displaySupportedAPIsInfo(compatInfo);
        }
    }

    /**
     * Display warning for unsupported browsers
     * @param {object} compatInfo Browser compatibility information
     */
    displayUnsupportedBrowserWarning(compatInfo) {
        const warningMessage = this.createUnsupportedBrowserMessage(compatInfo);
        
        // Try to find existing warning container, or create one
        let warningContainer = document.getElementById('local-printing-warning');
        
        if (!warningContainer) {
            warningContainer = document.createElement('div');
            warningContainer.id = 'local-printing-warning';
            warningContainer.className = 'alert alert-warning local-printing-warning';
            warningContainer.style.margin = '10px 0';
            
            // Insert at the top of the main content area
            const mainContent = document.querySelector('.container') || document.querySelector('main') || document.body;
            mainContent.insertBefore(warningContainer, mainContent.firstChild);
        }
        
        warningContainer.innerHTML = warningMessage;
        
        console.warn('Local printing not supported in this browser:', compatInfo);
    }

    /**
     * Display information about supported APIs
     * @param {object} compatInfo Browser compatibility information
     */
    displaySupportedAPIsInfo(compatInfo) {
        console.log('Local printing support detected:', {
            WebUSB: compatInfo.webUSBSupported ? '✅' : '❌',
            WebSerial: compatInfo.webSerialSupported ? '✅' : '❌',
            Browser: compatInfo.browser
        });
    }

    /**
     * Create unsupported browser warning message
     * @param {object} compatInfo Browser compatibility information
     * @returns {string} HTML warning message
     */
    createUnsupportedBrowserMessage(compatInfo) {
        const browserName = compatInfo.browser;
        
        let message = `
            <div class="local-printing-warning-content">
                <h5><i class="fas fa-exclamation-triangle"></i> Local Printing Not Supported</h5>
                <p>Your browser (${browserName}) does not support local printing via WebUSB or WebSerial APIs.</p>
                <p><strong>You can still use server-based printing</strong>, but direct USB/Serial printer connection is not available.</p>
                <div class="supported-browsers">
                    <p><strong>Browsers that support local printing:</strong></p>
                    <ul>
                        <li><strong>Google Chrome 89+</strong> - Full WebSerial and WebUSB support</li>
                        <li><strong>Microsoft Edge 89+</strong> - Full WebSerial and WebUSB support</li>
                        <li><strong>Opera 75+</strong> - WebSerial support</li>
                    </ul>
                    <p><em>Note: Firefox and Safari do not currently support these APIs.</em></p>
                </div>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="this.parentElement.parentElement.style.display='none'">
                    Dismiss
                </button>
            </div>
        `;
        
        return message;
    }

    /**
     * Perform compatibility check on page load
     */
    performCompatibilityCheck() {
        if (this.compatibilityChecked) {
            return;
        }
        
        console.log('🔍 Checking browser compatibility for local printing...');
        
        const compatInfo = this.getBrowserCompatibilityInfo();
        
        console.log('Browser compatibility results:', compatInfo);
        
        // Show warning if needed
        this.showBrowserCompatibilityWarning();
        
        this.compatibilityChecked = true;
    }

    /**
     * Get recommended browsers for local printing
     * @returns {array} List of recommended browsers
     */
    getRecommendedBrowsers() {
        return [
            {
                name: 'Google Chrome',
                version: '89+',
                webUSB: true,
                webSerial: true,
                downloadUrl: 'https://www.google.com/chrome/'
            },
            {
                name: 'Microsoft Edge',
                version: '89+',
                webUSB: true,
                webSerial: true,
                downloadUrl: 'https://www.microsoft.com/edge'
            },
            {
                name: 'Opera',
                version: '75+',
                webUSB: false,
                webSerial: true,
                downloadUrl: 'https://www.opera.com/'
            }
        ];
    }
}

// Global instance
const localPrintingSupportDetector = new LocalPrintingSupportDetector();

// Convenience functions for global access
function detectWebUSBSupport() {
    return localPrintingSupportDetector.detectWebUSBSupport();
}

function detectWebSerialSupport() {
    return localPrintingSupportDetector.detectWebSerialSupport();
}

function supportsLocalPrinting() {
    return localPrintingSupportDetector.supportsLocalPrinting();
}

function getBrowserCompatibilityInfo() {
    return localPrintingSupportDetector.getBrowserCompatibilityInfo();
}

function performCompatibilityCheck() {
    return localPrintingSupportDetector.performCompatibilityCheck();
}

// Auto-run compatibility check when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Global flag to prevent multiple compatibility checks across all instances
    if (window.localPrintingCompatibilityChecked) {
        return;
    }
    
    // Only run on pages where local printing might be relevant
    if (document.querySelector('.print-button') || 
        document.querySelector('#print-modal') ||
        window.location.pathname.includes('tasks')) {
        
        window.localPrintingCompatibilityChecked = true;
        
        // Delay slightly to ensure page is fully loaded
        setTimeout(() => {
            performCompatibilityCheck();
        }, 500);
    }
});

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LocalPrintingSupportDetector,
        detectWebUSBSupport,
        detectWebSerialSupport,
        supportsLocalPrinting,
        getBrowserCompatibilityInfo,
        performCompatibilityCheck
    };
}