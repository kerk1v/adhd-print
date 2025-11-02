/**
 * Local Printer Communication Layer
 * 
 * This module provides unified WebUSB and WebSerial printer communication
 * for direct local printing to thermal receipt printers.
 */

/**
 * Simple printer identification - treat all discovered printers as ESC/POS thermal printers
 */
function identifyPrinter(vendorId, productId, deviceName = null) {
    return {
        name: deviceName || 'Thermal Receipt Printer',
        type: 'ESC/POS Thermal Printer',
        vendor: 'Generic',
        isSupported: true
    };
}

/**
 * WebUSB Printer Communication Class
 */
class WebUSBPrinter {
    constructor() {
        this.device = null;
        this.connected = false;
        this.interfaceNumber = null;
        this.endpointNumber = null;
    }

    /**
     * Check if WebUSB is supported
     */
    static isSupported() {
        return 'usb' in navigator && 'requestDevice' in navigator.usb;
    }

    /**
     * Discover and request access to USB printers
     * @param {object} filters - USB device filters
     * @returns {Promise<Array>} Array of available devices
     */
    async discoverPrinters(filters = null) {
        console.log('🔌 WebUSB: Starting discovery...');
        
        if (!WebUSBPrinter.isSupported()) {
            console.error('❌ WebUSB: Not supported in this browser');
            throw new Error('WebUSB is not supported in this browser');
        }
        
        console.log('✅ WebUSB: Browser support confirmed');

        try {
            // Default filters for common thermal printer vendors
            const defaultFilters = [
                { vendorId: 0x04b8 }, // Epson
                { vendorId: 0x154f }, // Star Micronics
                { vendorId: 0x0519 }, // Citizen
                { vendorId: 0x0fe6 }, // ICS Advent (Bixolon)
                { vendorId: 0x20d1 }, // RONGTA
                { vendorId: 0x0416 }, // Winbond Electronics (thermal printers)
                // Generic USB printer class
                { classCode: 7 } // Printer class
            ];

            const requestFilters = filters || defaultFilters;
            
            console.log('🔍 WebUSB: Discovering printers with filters:', requestFilters);
            console.log('🔍 WebUSB: Starting device request dialog...');
            
            this.device = await navigator.usb.requestDevice({
                filters: requestFilters
            });

            console.log('✅ WebUSB: Device successfully selected:', this.device);
            console.log('📋 WebUSB: Device details:', {
                productName: this.device.productName,
                manufacturerName: this.device.manufacturerName,
                vendorId: '0x' + this.device.vendorId.toString(16),
                productId: '0x' + this.device.productId.toString(16),
                serialNumber: this.device.serialNumber
            });
            
            // Identify the printer
            const printerInfo = identifyPrinter(
                this.device.vendorId, 
                this.device.productId, 
                this.device.productName || this.device.manufacturerName
            );
            
            // Create enhanced printer object
            const printerObject = {
                device: this.device,
                name: printerInfo.name,
                type: printerInfo.type,
                vendor: printerInfo.vendor,
                vendorId: this.device.vendorId,
                productId: this.device.productId,
                connection: 'USB',
                isSupported: printerInfo.isSupported,
                printerClass: 'WebUSBPrinter'
            };
            
            console.log('🏷️ WebUSB: Identified printer:', printerObject);
            return [printerObject];

        } catch (error) {
            console.error('❌ WebUSB: Discovery error:', error);
            console.error('❌ WebUSB: Error type:', error.name);
            console.error('❌ WebUSB: Error message:', error.message);
            
            if (error.name === 'NotFoundError') {
                console.warn('⚠️ WebUSB: No device found - either no matching USB devices were found or user cancelled the selection dialog');
                console.info('💡 WebUSB: Suggestions:');
                console.info('   • Make sure your printer is connected via USB');
                console.info('   • Check if printer is powered on');
                console.info('   • Try a different USB port or cable');
                console.info('   • Some printers may not be compatible with WebUSB');
                throw new Error('No USB printer found or user cancelled selection');
            } else if (error.name === 'SecurityError') {
                console.warn('⚠️ WebUSB: Security error - this usually means the page is not served over HTTPS');
                console.info('💡 WebUSB: Security requirements:');
                console.info('   • Must be served over HTTPS (or localhost for development)');
                console.info('   • Must have user activation (button click)');
            } else if (error.name === 'NotAllowedError') {
                console.warn('⚠️ WebUSB: User denied permission or operation not allowed');
                console.info('💡 WebUSB: Permission suggestions:');
                console.info('   • User must grant permission when prompted');
                console.info('   • Try clicking the button again');
            }
            throw error;
        }
    }

    /**
     * Get list of previously authorized devices
     */
    async getAuthorizedDevices() {
        if (!WebUSBPrinter.isSupported()) {
            return [];
        }

        try {
            const devices = await navigator.usb.getDevices();
            console.log('📱 Previously authorized USB devices:', devices);
            return devices;
        } catch (error) {
            console.error('❌ Error getting authorized devices:', error);
            return [];
        }
    }

    /**
     * Connect to a USB printer device
     * @param {USBDevice} device - USB device to connect to
     */
    async connect(device = null) {
        try {
            this.device = device || this.device;
            
            if (!this.device) {
                throw new Error('No USB device available to connect');
            }

            console.log('🔌 Connecting to USB device:', this.device.productName || 'Unknown Device');

            // Open the device
            await this.device.open();
            console.log('✅ USB device opened');

            // Select configuration (usually first one)
            if (this.device.configuration === null) {
                await this.device.selectConfiguration(1);
                console.log('✅ USB configuration selected');
            }

            // Find printer interface (usually interface 0)
            const interfaces = this.device.configuration.interfaces;
            this.interfaceNumber = 0; // Default to first interface
            
            // Look for printer class interface
            for (const iface of interfaces) {
                if (iface.alternate.interfaceClass === 7) { // Printer class
                    this.interfaceNumber = iface.interfaceNumber;
                    break;
                }
            }

            // Claim the interface
            await this.device.claimInterface(this.interfaceNumber);
            console.log(`✅ USB interface ${this.interfaceNumber} claimed`);

            // Find bulk out endpoint for sending data
            const iface = this.device.configuration.interfaces[this.interfaceNumber];
            const endpoints = iface.alternate.endpoints;
            
            for (const endpoint of endpoints) {
                if (endpoint.direction === 'out' && endpoint.type === 'bulk') {
                    this.endpointNumber = endpoint.endpointNumber;
                    break;
                }
            }

            if (!this.endpointNumber) {
                throw new Error('No suitable output endpoint found');
            }

            console.log(`✅ Using endpoint ${this.endpointNumber} for output`);

            this.connected = true;
            console.log('🎉 USB printer connected successfully');

        } catch (error) {
            console.error('❌ Error connecting to USB printer:', error);
            this.connected = false;
            throw error;
        }
    }

    /**
     * Send data to the connected USB printer
     * @param {Uint8Array|string} data - Data to send
     */
    async sendData(data) {
        if (!this.connected || !this.device) {
            throw new Error('USB printer not connected');
        }

        try {
            // Convert string to Uint8Array if needed
            let dataArray;
            if (typeof data === 'string') {
                dataArray = new TextEncoder().encode(data);
            } else {
                dataArray = data;
            }

            console.log(`📤 Sending ${dataArray.length} bytes to USB printer`);

            const result = await this.device.transferOut(this.endpointNumber, dataArray);
            
            if (result.status === 'ok') {
                console.log(`✅ Successfully sent ${result.bytesWritten} bytes`);
                return true;
            } else {
                throw new Error(`Transfer failed with status: ${result.status}`);
            }

        } catch (error) {
            console.error('❌ Error sending data to USB printer:', error);
            throw error;
        }
    }

    /**
     * Disconnect from the USB printer
     */
    async disconnect() {
        try {
            if (this.device && this.connected) {
                if (this.interfaceNumber !== null) {
                    await this.device.releaseInterface(this.interfaceNumber);
                    console.log(`✅ USB interface ${this.interfaceNumber} released`);
                }
                
                await this.device.close();
                console.log('✅ USB device closed');
            }

            this.connected = false;
            this.device = null;
            this.interfaceNumber = null;
            this.endpointNumber = null;

            console.log('👋 USB printer disconnected');

        } catch (error) {
            console.error('❌ Error disconnecting USB printer:', error);
            throw error;
        }
    }

    /**
     * Get device information
     */
    getDeviceInfo() {
        if (!this.device) return null;

        return {
            type: 'USB',
            vendorId: this.device.vendorId,
            productId: this.device.productId,
            productName: this.device.productName || 'Unknown USB Printer',
            manufacturerName: this.device.manufacturerName || 'Unknown Manufacturer',
            serialNumber: this.device.serialNumber || 'Unknown',
            connected: this.connected
        };
    }
}

/**
 * WebSerial Printer Communication Class
 */
class WebSerialPrinter {
    constructor() {
        this.port = null;
        this.connected = false;
        this.writer = null;
        this.reader = null;
    }

    /**
     * Check if WebSerial is supported
     */
    static isSupported() {
        return 'serial' in navigator && 'requestPort' in navigator.serial;
    }

    /**
     * Discover and request access to serial ports
     * @param {object} filters - Serial port filters
     * @returns {Promise<Array>} Array of available ports
     */
    async discoverPrinters(filters = null) {
        console.log('🔍 === WEBSERIAL DISCOVERY START ===');
        
        if (!WebSerialPrinter.isSupported()) {
            console.error('🔍 ❌ WebSerial not supported');
            throw new Error('WebSerial is not supported in this browser');
        }

        console.log('🔍 ✅ WebSerial is supported');

        try {
            // Default filters for common thermal printer USB-to-Serial chips
            const defaultFilters = [
                { usbVendorId: 0x04b8 }, // Epson
                { usbVendorId: 0x154f }, // Star Micronics
                { usbVendorId: 0x0519 }, // Citizen
                { usbVendorId: 0x10C4 }, // Silicon Labs CP210x
                { usbVendorId: 0x0403 }, // FTDI
                { usbVendorId: 0x067B }, // Prolific PL2303
                { usbVendorId: 0x1A86 }, // QinHeng CH340
            ];

            const requestFilters = filters || defaultFilters;
            
            console.log('🔍 Discovering Serial printers with filters:', requestFilters);
            console.log('🔍 Calling navigator.serial.requestPort()...');
            
            this.port = await navigator.serial.requestPort({
                filters: requestFilters
            });

            console.log('✅ Serial port selected:', this.port);
            console.log('✅ Port info:', {
                connected: this.port.connected,
                readable: this.port.readable,
                writable: this.port.writable
            });
            
            // Create simplified printer object for serial connection
            const printerObject = {
                device: this.port,
                name: 'Thermal Receipt Printer',
                type: 'ESC/POS Thermal Printer',
                vendor: 'Generic',
                vendorId: null,
                productId: null,
                connection: 'Serial',
                isSupported: true,
                printerClass: 'WebSerialPrinter'
            };
            
            console.log('🏷️ WebSerial: Identified printer:', printerObject);
            console.log('🔍 === WEBSERIAL DISCOVERY END ===');
            return [printerObject];

        } catch (error) {
            console.error('❌ === WEBSERIAL DISCOVERY ERROR ===');
            console.error('❌ Error discovering serial printers:', error);
            console.error('❌ Error name:', error.name);
            console.error('❌ Error message:', error.message);
            if (error.name === 'NotFoundError') {
                throw new Error('No serial printer found or user cancelled selection');
            }
            throw error;
        }
    }

    /**
     * Get list of previously authorized ports
     */
    async getAuthorizedPorts() {
        if (!WebSerialPrinter.isSupported()) {
            return [];
        }

        try {
            const ports = await navigator.serial.getPorts();
            console.log('📱 Previously authorized serial ports:', ports);
            return ports;
        } catch (error) {
            console.error('❌ Error getting authorized ports:', error);
            return [];
        }
    }

    /**
     * Connect to a serial printer port
     * @param {SerialPort} port - Serial port to connect to
     * @param {object} options - Connection options
     */
    async connect(port = null, options = {}) {
        try {
            this.port = port || this.port;
            
            if (!this.port) {
                throw new Error('No serial port available to connect');
            }

            // Default serial options for thermal printers
            const defaultOptions = {
                baudRate: 9600,
                dataBits: 8,
                stopBits: 1,
                parity: 'none',
                flowControl: 'none'
            };

            const serialOptions = { ...defaultOptions, ...options };
            console.log('🔌 Connecting to serial port with options:', serialOptions);

            await this.port.open(serialOptions);
            console.log('✅ Serial port opened');

            // Get readable and writable streams
            this.writer = this.port.writable.getWriter();
            this.reader = this.port.readable.getReader();

            this.connected = true;
            console.log('🎉 Serial printer connected successfully');

        } catch (error) {
            console.error('❌ Error connecting to serial printer:', error);
            this.connected = false;
            throw error;
        }
    }

    /**
     * Send data to the connected serial printer
     * @param {Uint8Array|string} data - Data to send
     */
    async sendData(data) {
        if (!this.connected || !this.writer) {
            throw new Error('Serial printer not connected');
        }

        try {
            // Convert string to Uint8Array if needed
            let dataArray;
            if (typeof data === 'string') {
                dataArray = new TextEncoder().encode(data);
            } else {
                dataArray = data;
            }

            console.log(`📤 Sending ${dataArray.length} bytes to serial printer`);

            await this.writer.write(dataArray);
            console.log(`✅ Successfully sent ${dataArray.length} bytes`);
            return true;

        } catch (error) {
            console.error('❌ Error sending data to serial printer:', error);
            throw error;
        }
    }

    /**
     * Read data from the serial printer (if needed for status)
     * @param {number} timeout - Read timeout in milliseconds
     */
    async readData(timeout = 5000) {
        if (!this.connected || !this.reader) {
            throw new Error('Serial printer not connected');
        }

        try {
            console.log('📥 Reading data from serial printer');
            
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Read timeout')), timeout);
            });

            const readPromise = this.reader.read();
            const result = await Promise.race([readPromise, timeoutPromise]);

            if (result.done) {
                console.log('📥 Serial read completed (stream closed)');
                return null;
            }

            console.log(`📥 Received ${result.value.length} bytes from serial printer`);
            return result.value;

        } catch (error) {
            console.error('❌ Error reading from serial printer:', error);
            throw error;
        }
    }

    /**
     * Disconnect from the serial printer
     */
    async disconnect() {
        try {
            if (this.writer) {
                await this.writer.close();
                this.writer = null;
                console.log('✅ Serial writer closed');
            }

            if (this.reader) {
                await this.reader.cancel();
                this.reader = null;
                console.log('✅ Serial reader cancelled');
            }

            if (this.port && this.connected) {
                await this.port.close();
                console.log('✅ Serial port closed');
            }

            this.connected = false;
            this.port = null;

            console.log('👋 Serial printer disconnected');

        } catch (error) {
            console.error('❌ Error disconnecting serial printer:', error);
            throw error;
        }
    }

    /**
     * Get port information
     */
    getDeviceInfo() {
        if (!this.port) return null;

        const info = this.port.getInfo();
        return {
            type: 'Serial',
            usbVendorId: info.usbVendorId,
            usbProductId: info.usbProductId,
            productName: 'Serial Printer',
            manufacturerName: 'Unknown Manufacturer',
            serialNumber: 'Unknown',
            connected: this.connected
        };
    }
}

/**
 * Unified Local Printer Manager
 * Provides a common interface for both WebUSB and WebSerial printers
 */
class LocalPrinterManager {
    constructor() {
        this.currentPrinter = null;
        this.printerType = null; // 'usb' or 'serial'
        this.discoveredDevices = [];
        
        // Clean up any old saved device data
        this.clearOldDeviceData();
    }
    
    /**
     * Clear any old device persistence data
     */
    clearOldDeviceData() {
        try {
            localStorage.removeItem('adhd_print_saved_device');
            console.log('🧹 Cleared old device persistence data');
        } catch (error) {
            // Ignore localStorage errors
        }
    }

    /**
     * Check which local printing methods are supported
     */
    getSupportedMethods() {
        return {
            webUSB: WebUSBPrinter.isSupported(),
            webSerial: WebSerialPrinter.isSupported(),
            anySupported: WebUSBPrinter.isSupported() || WebSerialPrinter.isSupported()
        };
    }

    /**
     * Discover all available printers (USB and Serial)
     * @param {string} preferredMethod - 'usb', 'serial', or 'auto'
     */
    async discoverPrinters(preferredMethod = 'auto') {
        console.log('🔍 === PRINTER MANAGER DISCOVERY START ===');
        console.log('🔍 Starting printer discovery with method:', preferredMethod);
        
        const supported = this.getSupportedMethods();
        console.log('🔍 Supported methods:', supported);
        this.discoveredDevices = [];

        if (!supported.anySupported) {
            console.error('🔍 ❌ No supported methods available');
            throw new Error('Neither WebUSB nor WebSerial is supported in this browser');
        }

        // Determine which method to use
        let methods = [];
        if (preferredMethod === 'usb' && supported.webUSB) {
            methods = ['usb'];
        } else if (preferredMethod === 'serial' && supported.webSerial) {
            methods = ['serial'];
        } else if (preferredMethod === 'auto') {
            // Prefer WebSerial over WebUSB (better compatibility)
            if (supported.webSerial) methods.push('serial');
            if (supported.webUSB) methods.push('usb');
        }

        console.log(`🎯 Using discovery methods: ${methods.join(', ')}`);

        // Try each method
        for (const method of methods) {
            try {
                console.log(`🔍 Attempting discovery via ${method}...`);
                
                if (method === 'serial' && supported.webSerial) {
                    console.log('🔍 Creating WebSerialPrinter instance...');
                    const serialPrinter = new WebSerialPrinter();
                    console.log('🔍 Calling serialPrinter.discoverPrinters()...');
                    const devices = await serialPrinter.discoverPrinters();
                    console.log(`🔍 WebSerial discovery returned:`, devices);
                    console.log(`🔍 Found ${devices.length} serial devices`);
                    
                    this.discoveredDevices.push(...devices.map(device => ({
                        device,
                        type: 'serial',
                        printer: serialPrinter
                    })));
                    
                    // If user selected a device, break (only one selection allowed per API call)
                    if (devices.length > 0) break;
                }

                if (method === 'usb' && supported.webUSB) {
                    console.log('🔍 Creating WebUSBPrinter instance...');
                    const usbPrinter = new WebUSBPrinter();
                    console.log('🔍 Calling usbPrinter.discoverPrinters()...');
                    const devices = await usbPrinter.discoverPrinters();
                    console.log(`🔍 WebUSB discovery returned:`, devices);
                    console.log(`🔍 Found ${devices.length} USB devices`);
                    
                    this.discoveredDevices.push(...devices.map(device => ({
                        device,
                        type: 'usb',
                        printer: usbPrinter
                    })));
                    
                    // If user selected a device, break (only one selection allowed per API call)
                    if (devices.length > 0) {
                        console.log('🔍 Breaking after USB discovery found devices');
                        break;
                    }
                }

            } catch (error) {
                console.warn(`⚠️ Discovery failed for ${method}:`, error);
                console.warn(`⚠️ Error name: ${error.name}`);
                console.warn(`⚠️ Error message: ${error.message}`);
                if (error.stack) console.warn(`⚠️ Error stack:`, error.stack);
                // Continue with other methods
            }
        }

        console.log(`✅ Discovery complete. Found ${this.discoveredDevices.length} device(s)`);
        console.log(`✅ Discovered devices:`, this.discoveredDevices);
        console.log('🔍 === PRINTER MANAGER DISCOVERY END ===');
        return this.discoveredDevices;
    }

    /**
     * Get previously authorized devices
     */
    async getAuthorizedDevices() {
        const supported = this.getSupportedMethods();
        const devices = [];

        try {
            if (supported.webSerial) {
                const serialPrinter = new WebSerialPrinter();
                const ports = await serialPrinter.getAuthorizedPorts();
                devices.push(...ports.map(port => ({
                    device: port,
                    type: 'serial',
                    printer: serialPrinter
                })));
            }

            if (supported.webUSB) {
                const usbPrinter = new WebUSBPrinter();
                const usbDevices = await usbPrinter.getAuthorizedDevices();
                devices.push(...usbDevices.map(device => ({
                    device,
                    type: 'usb',
                    printer: usbPrinter
                })));
            }

        } catch (error) {
            console.error('❌ Error getting authorized devices:', error);
        }

        return devices;
    }

    /**
     * Connect to a specific printer device
     * @param {object} deviceInfo - Device info from discovery
     * @param {object} options - Connection options
     */
    async connectToPrinter(deviceInfo, options = {}) {
        try {
            console.log('🔌 Connecting to printer:', deviceInfo);

            // Handle both old format and new enhanced printer objects
            let connectionType, rawDevice;
            
            if (deviceInfo.printerClass) {
                // New enhanced printer object format
                connectionType = deviceInfo.connection.toLowerCase(); // 'USB' -> 'usb'
                rawDevice = deviceInfo.device;
                console.log('🔌 Using enhanced printer object format');
            } else if (deviceInfo.type && deviceInfo.device) {
                // Legacy format from print modal: {type: 'usb', device: enhancedPrinterObject}
                connectionType = deviceInfo.type;
                if (deviceInfo.device.device && deviceInfo.device.printerClass) {
                    // The device property contains an enhanced printer object, extract the raw device
                    rawDevice = deviceInfo.device.device;
                    console.log('🔌 Using legacy format with enhanced device, extracting raw USB device');
                } else {
                    // The device property is already a raw device
                    rawDevice = deviceInfo.device;
                    console.log('🔌 Using legacy format with raw device');
                }
            } else if (deviceInfo.device && deviceInfo.name) {
                // Discovery format: enhanced object with device nested inside
                connectionType = 'usb'; // Assume USB for now
                rawDevice = deviceInfo.device; // Extract the actual USB device
                console.log('🔌 Using discovery device format, extracting raw device');
            } else {
                console.error('🔌 ❌ Unknown device info format:', deviceInfo);
                throw new Error('Unknown device info format');
            }
            
            console.log('🔌 Connection type:', connectionType, 'Raw device type:', rawDevice?.constructor?.name, 'Device:', rawDevice);

            if (connectionType === 'serial') {
                this.currentPrinter = new WebSerialPrinter();
                await this.currentPrinter.connect(rawDevice, options);
            } else if (connectionType === 'usb') {
                this.currentPrinter = new WebUSBPrinter();
                await this.currentPrinter.connect(rawDevice);
            } else {
                throw new Error(`Unsupported printer type: ${connectionType}`);
            }

            this.printerType = connectionType;
            console.log('🎉 Printer connected successfully');

        } catch (error) {
            console.error('❌ Error connecting to printer:', error);
            this.currentPrinter = null;
            this.printerType = null;
            throw error;
        }
    }

    /**
     * Send data to the currently connected printer
     * @param {Uint8Array|string} data - Data to send
     */
    async sendData(data) {
        if (!this.currentPrinter) {
            throw new Error('No printer connected');
        }

        return await this.currentPrinter.sendData(data);
    }

    /**
     * Disconnect from the current printer
     */
    async disconnect() {
        if (this.currentPrinter) {
            await this.currentPrinter.disconnect();
            this.currentPrinter = null;
            this.printerType = null;
        }
    }

    /**
     * Get current printer connection status
     */
    getConnectionStatus() {
        if (!this.currentPrinter) {
            return {
                connected: false,
                type: null,
                device: null
            };
        }

        return {
            connected: this.currentPrinter.connected,
            type: this.printerType,
            device: this.currentPrinter.getDeviceInfo()
        };
    }

    /**
     * Test print functionality
     */
    async testPrint() {
        if (!this.currentPrinter) {
            throw new Error('No printer connected');
        }

        const testData = '\n\n--- Test Print ---\nLocal printing is working!\n\n\n\x1d\x56\x00'; // Cut paper
        await this.sendData(testData);
        console.log('✅ Test print sent');
    }

}

// Global instance for easy access
const localPrinterManager = new LocalPrinterManager();

// Make available on window for other modules
window.localPrinterManager = localPrinterManager;

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        WebUSBPrinter,
        WebSerialPrinter,
        LocalPrinterManager,
        localPrinterManager
    };
}