/**
 * Test file for local printer communication functionality
 * This can be run in the browser console to test printer discovery and connection
 */

/**
 * Test the complete printer communication workflow
 */
async function testLocalPrinterCommunication() {
    console.log('🧪 Testing Local Printer Communication...');
    
    try {
        // 1. Test support detection
        console.log('\n1. Testing Support Detection:');
        const supported = localPrinterManager.getSupportedMethods();
        console.table(supported);
        
        if (!supported.anySupported) {
            console.error('❌ No local printing methods supported in this browser');
            return false;
        }

        // 2. Test authorized devices retrieval
        console.log('\n2. Testing Authorized Devices:');
        const authorizedDevices = await localPrinterManager.getAuthorizedDevices();
        console.log(`📱 Found ${authorizedDevices.length} previously authorized devices:`, authorizedDevices);

        // 3. Test connection status (should be disconnected initially)
        console.log('\n3. Testing Initial Connection Status:');
        const initialStatus = localPrinterManager.getConnectionStatus();
        console.log('📊 Connection status:', initialStatus);

        console.log('\n✅ Basic printer communication tests completed!');
        console.log('\n🎯 Next steps:');
        console.log('   - Run testPrinterDiscovery() to discover new printers');
        console.log('   - Run testPrinterConnection() after discovering a printer');
        console.log('   - Run testPrintData() to send test data to connected printer');

        return true;

    } catch (error) {
        console.error('❌ Error during printer communication test:', error);
        return false;
    }
}

/**
 * Test printer discovery workflow
 * Note: This will show browser permission dialogs
 */
async function testPrinterDiscovery() {
    console.log('🔍 Testing Printer Discovery...');
    
    try {
        console.log('\n⚠️  This will show browser permission dialogs');
        console.log('   Please select a printer from the dialog or cancel to test error handling');

        const devices = await localPrinterManager.discoverPrinters('auto');
        
        if (devices.length > 0) {
            console.log(`✅ Discovered ${devices.length} printer(s):`);
            devices.forEach((device, index) => {
                console.log(`   ${index + 1}. ${device.type.toUpperCase()} device:`, device.device);
            });
            
            // Store first device for connection testing
            window.testPrinterDevice = devices[0];
            console.log('\n💾 First device stored in window.testPrinterDevice for connection testing');
            console.log('   Run testPrinterConnection() to connect to this device');
            
        } else {
            console.log('ℹ️  No devices discovered (user might have cancelled)');
        }

        return devices;

    } catch (error) {
        console.error('❌ Error during printer discovery:', error);
        return [];
    }
}

/**
 * Test printer connection using a discovered device
 * Requires window.testPrinterDevice to be set from discovery
 */
async function testPrinterConnection() {
    console.log('🔌 Testing Printer Connection...');
    
    if (!window.testPrinterDevice) {
        console.error('❌ No test device available. Run testPrinterDiscovery() first');
        return false;
    }

    try {
        const device = window.testPrinterDevice;
        console.log(`🎯 Connecting to ${device.type} device...`);

        await localPrinterManager.connectToPrinter(device);
        
        const status = localPrinterManager.getConnectionStatus();
        console.log('✅ Connection successful! Status:', status);

        console.log('\n🎯 Next steps:');
        console.log('   - Run testPrintData() to send test data');
        console.log('   - Run testDisconnect() to disconnect cleanly');

        return true;

    } catch (error) {
        console.error('❌ Error during printer connection:', error);
        return false;
    }
}

/**
 * Test sending data to connected printer
 */
async function testPrintData() {
    console.log('📤 Testing Print Data...');
    
    const status = localPrinterManager.getConnectionStatus();
    if (!status.connected) {
        console.error('❌ No printer connected. Run testPrinterConnection() first');
        return false;
    }

    try {
        console.log('📝 Sending test data to printer...');
        
        // Simple test message
        const testMessage = '\n--- Local Print Test ---\n' +
                           `Date: ${new Date().toISOString()}\n` +
                           'Local printing is working!\n' +
                           '✅ Communication successful\n\n';

        await localPrinterManager.sendData(testMessage);
        console.log('✅ Test data sent successfully!');

        console.log('\n🎯 Next step:');
        console.log('   - Check your printer for the test printout');
        console.log('   - Run testDisconnect() when done');

        return true;

    } catch (error) {
        console.error('❌ Error sending test data:', error);
        return false;
    }
}

/**
 * Test the built-in test print function
 */
async function testBuiltInTestPrint() {
    console.log('🖨️  Testing Built-in Test Print...');
    
    const status = localPrinterManager.getConnectionStatus();
    if (!status.connected) {
        console.error('❌ No printer connected. Run testPrinterConnection() first');
        return false;
    }

    try {
        await localPrinterManager.testPrint();
        console.log('✅ Built-in test print completed!');
        return true;

    } catch (error) {
        console.error('❌ Error during built-in test print:', error);
        return false;
    }
}

/**
 * Test disconnection
 */
async function testDisconnect() {
    console.log('👋 Testing Printer Disconnection...');
    
    try {
        await localPrinterManager.disconnect();
        
        const status = localPrinterManager.getConnectionStatus();
        console.log('✅ Disconnection successful! Status:', status);

        return true;

    } catch (error) {
        console.error('❌ Error during disconnection:', error);
        return false;
    }
}

/**
 * Run complete end-to-end test workflow
 * Note: This will show browser permission dialogs
 */
async function testCompleteWorkflow() {
    console.log('🚀 Running Complete Printer Communication Workflow Test...');
    console.log('⚠️  This will show browser permission dialogs');
    
    try {
        // Step 1: Basic tests
        const basicTestPassed = await testLocalPrinterCommunication();
        if (!basicTestPassed) return false;

        // Step 2: Discovery
        console.log('\n📍 Step 2: Discovering printers...');
        const devices = await testPrinterDiscovery();
        if (devices.length === 0) {
            console.log('ℹ️  No devices discovered. Workflow test ended.');
            return false;
        }

        // Step 3: Connection
        console.log('\n📍 Step 3: Connecting to printer...');
        const connectionSuccess = await testPrinterConnection();
        if (!connectionSuccess) return false;

        // Step 4: Send test data
        console.log('\n📍 Step 4: Sending test data...');
        await testPrintData();

        // Step 5: Built-in test print
        console.log('\n📍 Step 5: Built-in test print...');
        await testBuiltInTestPrint();

        // Step 6: Disconnect
        console.log('\n📍 Step 6: Disconnecting...');
        await testDisconnect();

        console.log('\n🎉 Complete workflow test finished successfully!');
        return true;

    } catch (error) {
        console.error('❌ Complete workflow test failed:', error);
        return false;
    }
}

// Auto-announce test functions when this file loads
if (typeof window !== 'undefined' && window.location) {
    console.log('🧪 Local Printer Communication test functions loaded');
    console.log('📋 Available test functions:');
    console.log('   • testLocalPrinterCommunication() - Basic functionality tests');
    console.log('   • testPrinterDiscovery() - Discover available printers');
    console.log('   • testPrinterConnection() - Connect to discovered printer');
    console.log('   • testPrintData() - Send test data to printer');
    console.log('   • testBuiltInTestPrint() - Use built-in test print');
    console.log('   • testDisconnect() - Disconnect from printer');
    console.log('   • testCompleteWorkflow() - Run full end-to-end test');
    console.log('\n🚀 Start with: testLocalPrinterCommunication()');
}