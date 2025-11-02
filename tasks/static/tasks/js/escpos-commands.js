/**
 * ESC/POS Command Generation for Local Thermal Printer Support
 * 
 * This module provides comprehensive ESC/POS command generation for thermal receipt printers,
 * porting functionality from the existing print_utils.py while adding client-side capabilities.
 * 
 * Features:
 * - Text mode ESC/POS command generation
 * - Graphics mode support via server-side generation
 * - Task-to-ESC/POS conversion functions
 * - Error handling and fallback mechanisms
 * - Integration with WebUSB/WebSerial communication layer
 * 
 * Tested with: Thermal receipt printers supporting ESC/POS standard
 * Compatible with: Epson, Star, Citizen, Bixolon thermal printers
 */

class ESCPOSCommands {
    constructor() {
        // ESC/POS command constants
        this.commands = {
            // Initialization
            INIT: new Uint8Array([0x1B, 0x40]),  // ESC @ (Initialize printer)
            
            // Character commands
            CHAR_SET: new Uint8Array([0x1B, 0x74, 0x00]),  // ESC t 0 (Character code table 0)
            FONT_A: new Uint8Array([0x1B, 0x4D, 0x00]),    // ESC M 0 (Font A - default)
            FONT_B: new Uint8Array([0x1B, 0x4D, 0x01]),    // ESC M 1 (Font B - smaller)
            
            // Text formatting
            BOLD_ON: new Uint8Array([0x1B, 0x45, 0x01]),   // ESC E 1 (Bold on)
            BOLD_OFF: new Uint8Array([0x1B, 0x45, 0x00]),  // ESC E 0 (Bold off)
            UNDERLINE_ON: new Uint8Array([0x1B, 0x2D, 0x01]), // ESC - 1 (Underline on)
            UNDERLINE_OFF: new Uint8Array([0x1B, 0x2D, 0x00]), // ESC - 0 (Underline off)
            
            // Alignment
            ALIGN_LEFT: new Uint8Array([0x1B, 0x61, 0x00]),   // ESC a 0 (Left align)
            ALIGN_CENTER: new Uint8Array([0x1B, 0x61, 0x01]), // ESC a 1 (Center align)
            ALIGN_RIGHT: new Uint8Array([0x1B, 0x61, 0x02]),  // ESC a 2 (Right align)
            
            // Line feeds
            LF: new Uint8Array([0x0A]),          // LF (Line feed)
            CR: new Uint8Array([0x0D]),          // CR (Carriage return)
            CRLF: new Uint8Array([0x0D, 0x0A]),  // CR+LF
            
            // Paper control
            FEED_LINES: (n) => new Uint8Array([0x1B, 0x64, n]),  // ESC d n (Feed n lines)
            FULL_CUT: new Uint8Array([0x1D, 0x56, 0x00]),        // GS V 0 (Full cut)
            PARTIAL_CUT: new Uint8Array([0x1D, 0x56, 0x01]),     // GS V 1 (Partial cut)
            
            // Graphics commands
            BITMAP_MODE: new Uint8Array([0x1D, 0x76, 0x30, 0x00]) // GS v 0 0 (Normal bitmap)
        };
        
        // Printer capabilities
        this.capabilities = {
            paperWidth: 72,        // 72mm thermal paper (standard)
            printWidth: 576,       // 576 dots at 203 DPI
            charsPerLine: 42,      // Characters per line for text mode
            maxGraphicsWidth: 576  // Maximum graphics width in pixels
        };
        
        // Task formatting configuration
        this.formatting = {
            borderChar: '=',
            separatorChar: '-',
            maxTitleChars: 40,
            maxDescChars: 39,
            urgencySymbols: {
                'critical': '[!!!]',
                'urgent': '[!!] ',
                'normal': '[!]  ',
                'low': '[ ]  '
            }
        };
    }

    /**
     * Initialize printer and prepare for printing
     * @returns {Uint8Array} ESC/POS initialization commands
     */
    initializePrinter() {
        const commands = [];
        
        // Initialize printer
        commands.push(this.commands.INIT);
        
        // Set character code table
        commands.push(this.commands.CHAR_SET);
        
        // Set default font
        commands.push(this.commands.FONT_A);
        
        // Set left alignment
        commands.push(this.commands.ALIGN_LEFT);
        
        return this.combineCommands(commands);
    }


    /**
     * Generate ESC/POS commands for graphics mode using server-side generation
    /**
     * Wrap text to specified character width
     * @param {string} text - Text to wrap
     * @param {number} maxChars - Maximum characters per line
     * @returns {Array<string>} Array of wrapped lines
     */
    wrapText(text, maxChars) {
        if (!text || text.length <= maxChars) {
            return [text || ''];
        }
        
        const words = text.split(/\s+/);
        const lines = [];
        let currentLine = '';
        
        words.forEach(word => {
            const testLine = currentLine + (currentLine ? ' ' : '') + word;
            if (testLine.length <= maxChars) {
                currentLine = testLine;
            } else {
                if (currentLine) {
                    lines.push(currentLine);
                }
                currentLine = word;
            }
        });
        
        if (currentLine) {
            lines.push(currentLine);
        }
        
        return lines.length > 0 ? lines : [''];
    }

    /**
     * Convert string to UTF-8 byte array
     * @param {string} str - String to convert
     * @returns {Uint8Array} UTF-8 encoded bytes
     */
    stringToBytes(str) {
        return new TextEncoder().encode(str);
    }

    /**
     * Combine multiple command arrays into single Uint8Array
     * @param {Array<Uint8Array>} commands - Array of command byte arrays
     * @returns {Uint8Array} Combined command sequence
     */
    combineCommands(commands) {
        // Calculate total length
        const totalLength = commands.reduce((sum, cmd) => sum + cmd.length, 0);
        
        // Create combined array
        const combined = new Uint8Array(totalLength);
        let offset = 0;
        
        commands.forEach(cmd => {
            combined.set(cmd, offset);
            offset += cmd.length;
        });
        
        return combined;
    }

    /**
     * Generate ESC/POS commands for graphics mode using server-side generation
     * @param {Object} task - Task object
     * @param {Object} options - Options including endpoint URL
     * @returns {Promise<Uint8Array>} ESC/POS graphics commands from server
     */
    async taskToGraphicsESCPOS(task, options = {}) {
        try {
            const endpoint = options.endpoint || '/tasks/generate-escpos-graphics/';
            
            // Prepare request data
            const requestData = {
                task: {
                    id: task.id,
                    title: task.title,
                    description: task.description,
                    urgency: task.urgency,
                    due_date: task.due_date,
                    created_at: task.created_at,
                    hierarchy: task.hierarchy
                },
                options: {
                    use_graphics: true,
                    format: 'bitmap',  // or 'simple' for 8-dot graphics
                    ...options
                }
            };
            
            // Make request to server
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`Server graphics generation failed: ${response.status} ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(`Graphics generation error: ${result.error}`);
            }
            
            // Convert base64 encoded ESC/POS data back to Uint8Array
            const binaryString = atob(result.escpos_data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            return bytes;
            
        } catch (error) {
            console.error('Error generating graphics ESC/POS commands:', error);
            throw new Error(`ESC/POS graphics generation failed: ${error.message}`);
        }
    }

    /**
     * Generate ESC/POS commands with fallback strategy
     * @param {Object} task - Task object
     * @param {Object} options - Options including preferred mode
     * @returns {Promise<Uint8Array>} ESC/POS commands
     */
    async generateESCPOSCommands(task, options = {}) {
        // Always use graphics mode - no fallback to text mode
        try {
            return await this.taskToGraphicsESCPOS(task, options);
        } catch (error) {
            console.error('Graphics mode ESC/POS generation failed:', error);
            throw error;
        }
    }

    /**
     * Get CSRF token for Django requests
     * @returns {string} CSRF token
     */
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Try to get from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Try to get from hidden input
        const hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (hiddenInput) {
            return hiddenInput.value;
        }
        
        console.warn('CSRF token not found');
        return '';
    }

    /**
     * Validate task object structure
     * @param {Object} task - Task object to validate
     * @throws {Error} If task structure is invalid
     */
    validateTask(task) {
        if (!task || typeof task !== 'object') {
            throw new Error('Task must be a valid object');
        }
        
        if (!task.title || typeof task.title !== 'string') {
            throw new Error('Task must have a valid title');
        }
        
        if (task.urgency && !['low', 'normal', 'urgent', 'critical'].includes(task.urgency)) {
            console.warn(`Unknown urgency level: ${task.urgency}, defaulting to 'normal'`);
            task.urgency = 'normal';
        }
        
        // Set defaults for missing fields
        if (!task.urgency) task.urgency = 'normal';
        if (!task.description) task.description = '';
        if (!task.hierarchy) task.hierarchy = [task.title];
        if (!task.created_at) task.created_at = new Date().toISOString();
    }

    /**
     * Generate test ESC/POS commands for printer validation
     * @returns {Uint8Array} Test print commands
     */
    generateTestPrint() {
        const commands = [];
        
        // Initialize printer
        commands.push(this.initializePrinter());
        
        // Test header
        commands.push(this.commands.ALIGN_CENTER);
        commands.push(this.commands.BOLD_ON);
        commands.push(this.stringToBytes('ADHD Print System'));
        commands.push(this.commands.BOLD_OFF);
        commands.push(this.commands.LF);
        commands.push(this.stringToBytes('Printer Test'));
        commands.push(this.commands.LF);
        commands.push(this.commands.ALIGN_LEFT);
        
        // Test content
        const testLine = this.formatting.borderChar.repeat(this.capabilities.charsPerLine);
        commands.push(this.stringToBytes(testLine));
        commands.push(this.commands.LF);
        
        commands.push(this.stringToBytes('Test Task Title'));
        commands.push(this.commands.LF);
        commands.push(this.stringToBytes('This is a test description to verify printing'));
        commands.push(this.commands.LF);
        commands.push(this.stringToBytes(`Urgency: [!] normal`));
        commands.push(this.commands.LF);
        commands.push(this.stringToBytes(`Date: ${new Date().toLocaleDateString()}`));
        commands.push(this.commands.LF);
        
        commands.push(this.stringToBytes(testLine));
        commands.push(this.commands.LF);
        
        // Test complete
        commands.push(this.commands.ALIGN_CENTER);
        commands.push(this.stringToBytes('Test Complete'));
        commands.push(this.commands.LF);
        commands.push(this.commands.ALIGN_LEFT);
        
        // Feed and cut
        commands.push(this.commands.LF);
        commands.push(this.commands.LF);
        commands.push(this.commands.FULL_CUT);
        
        return this.combineCommands(commands);
    }
}

// Create global instance
const escposCommands = new ESCPOSCommands();

// Make available on window for other modules
window.escposCommands = escposCommands;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ESCPOSCommands, escposCommands };
}