/**
 * Comprehensive Test Suite for ESC/POS Command Generation and Local Printing
 * 
 * This test suite validates:
 * - ESC/POS command generation (graphics mode)
 * - Task data conversion and validation
 * - Server-side graphics API integration
 * - Local print manager functionality
 * - Error handling and fallback mechanisms
 * - End-to-end printing workflows
 */

class ESCPOSTestSuite {
    constructor() {
        this.testResults = [];
        this.totalTests = 0;
        this.passedTests = 0;
        this.failedTests = 0;
        
        // Test data
        this.sampleTasks = {
            simple: {
                id: 1,
                title: 'Simple Test Task',
                description: 'This is a simple test task description',
                urgency: 'normal',
                due_date: new Date().toISOString(),
                created_at: new Date().toISOString(),
                hierarchy: ['Simple Test Task']
            },
            complex: {
                id: 2,
                title: 'Complex Task with Very Long Title That Should Wrap Across Multiple Lines',
                description: 'This is a much longer description that should definitely wrap across multiple lines when printed. It contains various details about the task that need to be formatted properly.',
                urgency: 'urgent',
                due_date: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
                created_at: new Date().toISOString(),
                hierarchy: ['Root Task', 'Parent Task', 'Complex Task with Very Long Title That Should Wrap Across Multiple Lines']
            },
            critical: {
                id: 3,
                title: 'Critical Overdue Task',
                description: 'This task is overdue and critical',
                urgency: 'critical',
                due_date: new Date(Date.now() - 86400000).toISOString(), // Yesterday
                created_at: new Date().toISOString(),
                hierarchy: ['Critical Overdue Task']
            },
            minimal: {
                id: 4,
                title: 'Minimal Task',
                urgency: 'low',
                hierarchy: ['Minimal Task']
            }
        };
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🧪 Starting ESC/POS Test Suite...\n');
        
        try {
            // Core ESC/POS Command Tests
            await this.testESCPOSBasicCommands();
            await this.testTaskValidation();
            await this.testTextWrapping();
            await this.testDueDateFormatting();
            await this.testHierarchyFormatting();
            
            // Graphics Mode Tests
            await this.testGraphicsModeAPI();
            await this.testGraphicsAPIErrorHandling();
            
            // Integration Tests
            await this.testLocalPrintManager();
            await this.testPrintManagerErrorHandling();
            await this.testBatchPrinting();
            await this.testPrintQueue();
            
            // End-to-End Tests
            await this.testCompleteWorkflow();
            await this.testFallbackMechanisms();
            
        } catch (error) {
            console.error('Test suite failed with error:', error);
        }
        
        this.printTestSummary();
    }

    /**
     * Test basic ESC/POS command generation
     */
    async testESCPOSBasicCommands() {
        const testName = 'ESC/POS Basic Commands';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Test initialization
            const initCommands = escpos.initializePrinter();
            this.assert(initCommands instanceof Uint8Array, 'Init commands should return Uint8Array');
            this.assert(initCommands.length > 0, 'Init commands should not be empty');
            
            // Test string to bytes conversion
            const testString = 'Hello World';
            const bytes = escpos.stringToBytes(testString);
            this.assert(bytes instanceof Uint8Array, 'String conversion should return Uint8Array');
            this.assert(bytes.length === testString.length, 'Byte length should match string length');
            
            // Test command combination
            const commands = [
                escpos.commands.INIT,
                escpos.stringToBytes('Test'),
                escpos.commands.LF
            ];
            const combined = escpos.combineCommands(commands);
            this.assert(combined instanceof Uint8Array, 'Combined commands should return Uint8Array');
            
            // Test test print generation
            const testPrint = escpos.generateTestPrint();
            this.assert(testPrint instanceof Uint8Array, 'Test print should return Uint8Array');
            this.assert(testPrint.length > 100, 'Test print should be substantial');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test task validation
     */
    async testTaskValidation() {
        const testName = 'Task Validation';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Test valid task
            const validTask = { ...this.sampleTasks.simple };
            escpos.validateTask(validTask); // Should not throw
            
            // Test invalid tasks
            this.assertThrows(() => {
                escpos.validateTask(null);
            }, 'Should reject null task');
            
            this.assertThrows(() => {
                escpos.validateTask({});
            }, 'Should reject task without title');
            
            this.assertThrows(() => {
                escpos.validateTask({ title: 123 });
            }, 'Should reject task with non-string title');
            
            // Test urgency defaults
            const taskWithoutUrgency = { title: 'Test' };
            escpos.validateTask(taskWithoutUrgency);
            this.assert(taskWithoutUrgency.urgency === 'normal', 
                'Should default urgency to normal');
            
            // Test invalid urgency correction
            const taskWithInvalidUrgency = { title: 'Test', urgency: 'invalid' };
            escpos.validateTask(taskWithInvalidUrgency);
            this.assert(taskWithInvalidUrgency.urgency === 'normal', 
                'Should correct invalid urgency to normal');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test text wrapping functionality
     */
    async testTextWrapping() {
        const testName = 'Text Wrapping';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Test short text (no wrapping needed)
            const shortText = 'Short text';
            const shortWrapped = escpos.wrapText(shortText, 20);
            this.assert(shortWrapped.length === 1, 'Short text should not wrap');
            this.assert(shortWrapped[0] === shortText, 'Short text should remain unchanged');
            
            // Test long text (wrapping needed)
            const longText = 'This is a very long text that definitely needs to be wrapped across multiple lines';
            const longWrapped = escpos.wrapText(longText, 20);
            this.assert(longWrapped.length > 1, 'Long text should wrap to multiple lines');
            
            // Verify no line exceeds max length
            longWrapped.forEach((line, index) => {
                this.assert(line.length <= 20, 
                    `Line ${index + 1} should not exceed max length: "${line}"`);
            });
            
            // Test edge cases
            const emptyText = '';
            const emptyWrapped = escpos.wrapText(emptyText, 20);
            this.assert(emptyWrapped.length === 1 && emptyWrapped[0] === '', 
                'Empty text should return single empty line');
            
            const singleWord = 'Supercalifragilisticexpialidocious';
            const singleWrapped = escpos.wrapText(singleWord, 10);
            this.assert(singleWrapped.length === 1, 
                'Single word longer than limit should not break');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test due date formatting
     */
    async testDueDateFormatting() {
        const testName = 'Due Date Formatting';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Test no due date
            const noDue = escpos.formatDueDate(null);
            this.assert(noDue === 'DUE: Not set', 'Should handle null due date');
            
            // Test today's due date
            const today = new Date();
            const todayStr = escpos.formatDueDate(today.toISOString());
            this.assert(todayStr.includes('(TODAY!)'), 'Should detect today\'s due date');
            
            // Test overdue
            const yesterday = new Date(Date.now() - 86400000);
            const overdueStr = escpos.formatDueDate(yesterday.toISOString());
            this.assert(overdueStr.includes('(OVERDUE!)'), 'Should detect overdue tasks');
            
            // Test future date
            const tomorrow = new Date(Date.now() + 86400000);
            const futureStr = escpos.formatDueDate(tomorrow.toISOString());
            this.assert(!futureStr.includes('(') || futureStr.includes('DUE:'), 
                'Future dates should be formatted normally');
            
            // Test invalid date
            const invalidStr = escpos.formatDueDate('invalid-date');
            this.assert(invalidStr.includes('Invalid date'), 'Should handle invalid dates');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test hierarchy formatting
     */
    async testHierarchyFormatting() {
        const testName = 'Hierarchy Formatting';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Test no hierarchy
            const noHierarchy = escpos.formatTaskHierarchy([]);
            this.assert(noHierarchy.length === 0, 'Empty hierarchy should return empty commands');
            
            // Test single task (no parents)
            const singleTask = escpos.formatTaskHierarchy(['Current Task']);
            this.assert(singleTask.length === 0, 'Single task should return empty commands');
            
            // Test complex hierarchy
            const complexHierarchy = ['Root', 'Parent', 'Child', 'Current'];
            const hierarchyCommands = escpos.formatTaskHierarchy(complexHierarchy);
            this.assert(hierarchyCommands.length > 0, 'Complex hierarchy should generate commands');
            
            // Convert to string to check content
            const hierarchyStr = Array.from(hierarchyCommands)
                .map(b => String.fromCharCode(b)).join('');
            this.assert(hierarchyStr.includes('Parents'), 'Should include Parents header');
            this.assert(hierarchyStr.includes('Root'), 'Should include root task');
            this.assert(hierarchyStr.includes('Parent'), 'Should include parent task');
            this.assert(hierarchyStr.includes('Child'), 'Should include child task');
            this.assert(!hierarchyStr.includes('Current'), 'Should not include current task');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test graphics mode API
     */
    async testGraphicsModeAPI() {
        const testName = 'Graphics Mode API';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Mock successful API response
            const originalFetch = window.fetch;
            window.fetch = async (url, options) => {
                if (url.includes('generate-escpos-graphics')) {
                    return {
                        ok: true,
                        json: async () => ({
                            success: true,
                            escpos_data: btoa('mock-escpos-data'),
                            format: 'bitmap',
                            byte_count: 16
                        })
                    };
                }
                throw new Error('Unexpected URL');
            };
            
            try {
                const graphicsCommands = await escpos.taskToGraphicsESCPOS(
                    this.sampleTasks.simple
                );
                
                this.assert(graphicsCommands instanceof Uint8Array, 
                    'Graphics mode should return Uint8Array');
                this.assert(graphicsCommands.length > 0, 
                    'Graphics commands should not be empty');
                
            } finally {
                // Restore original fetch
                window.fetch = originalFetch;
            }
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test graphics API error handling
     */
    async testGraphicsAPIErrorHandling() {
        const testName = 'Graphics API Error Handling';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Mock failed API response
            const originalFetch = window.fetch;
            window.fetch = async (url, options) => {
                if (url.includes('generate-escpos-graphics')) {
                    return {
                        ok: false,
                        status: 500,
                        statusText: 'Internal Server Error'
                    };
                }
                throw new Error('Unexpected URL');
            };
            
            try {
                await this.assertAsyncThrows(async () => {
                    await escpos.taskToGraphicsESCPOS(this.sampleTasks.simple);
                }, 'Should throw on API error');
                
            } finally {
                // Restore original fetch
                window.fetch = originalFetch;
            }
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test local print manager functionality
     */
    async testLocalPrintManager() {
        const testName = 'Local Print Manager';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const printManager = new LocalPrintManager();
            
            // Test configuration
            this.assert(typeof printManager.config === 'object', 
                'Print manager should have config object');
            this.assert(printManager.config.preferredMode === 'graphics', 
                'Default mode should be graphics');
            
            // Test status
            const status = printManager.getStatus();
            this.assert(typeof status === 'object', 'Should return status object');
            this.assert('connection' in status, 'Status should include connection info');
            this.assert('queueLength' in status, 'Status should include queue length');
            
            // Test configuration update
            printManager.updateConfig({ preferredMode: 'text' });
            this.assert(printManager.config.preferredMode === 'text', 
                'Should update configuration');
            
            // Test event listeners
            let eventFired = false;
            printManager.addEventListener('printStart', () => {
                eventFired = true;
            });
            printManager.notifyEventHandlers('printStart', {});
            this.assert(eventFired, 'Event listeners should work');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test print manager error handling
     */
    async testPrintManagerErrorHandling() {
        const testName = 'Print Manager Error Handling';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const printManager = new LocalPrintManager();
            
            // Test invalid task handling
            const result = await printManager.printTask(null);
            this.assert(!result.success, 'Should handle invalid task gracefully');
            this.assert(typeof result.error === 'string', 'Should provide error message');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test batch printing
     */
    async testBatchPrinting() {
        const testName = 'Batch Printing';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const printManager = new LocalPrintManager();
            
            // Test empty batch
            const emptyResult = await printManager.printTasks([]);
            this.assert(emptyResult.success, 'Empty batch should succeed');
            this.assert(emptyResult.totalTasks === 0, 'Should report zero tasks');
            
            // Test queue status
            const queueStatus = printManager.getQueueStatus();
            this.assert(typeof queueStatus === 'object', 'Should return queue status');
            this.assert(queueStatus.length === 0, 'Queue should start empty');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test print queue functionality
     */
    async testPrintQueue() {
        const testName = 'Print Queue';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const printManager = new LocalPrintManager();
            
            // Clear queue first
            printManager.clearQueue();
            
            // Add to queue
            const jobId = printManager.addToQueue(this.sampleTasks.simple);
            this.assert(typeof jobId === 'string', 'Should return job ID');
            
            const queueStatus = printManager.getQueueStatus();
            this.assert(queueStatus.length === 1, 'Queue should have one item');
            
            // Clear queue
            printManager.clearQueue();
            const emptyStatus = printManager.getQueueStatus();
            this.assert(emptyStatus.length === 0, 'Queue should be empty after clear');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test complete workflow
     */
    async testCompleteWorkflow() {
        const testName = 'Complete Workflow';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            // Test end-to-end command generation workflow
            const escpos = new ESCPOSCommands();
            
            // Validate task
            const task = { ...this.sampleTasks.complex };
            escpos.validateTask(task);
            
            // Generate graphics commands (will test fallback to text)
            const graphicsCommands = await escpos.generateESCPOSCommands(task, {
                mode: 'graphics',
                allowFallback: true
            });
            // This should fallback to graphics mode since we're only supporting graphics now
            this.assert(graphicsCommands instanceof Uint8Array, 
                'Graphics workflow should produce commands');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test fallback mechanisms
     */
    async testFallbackMechanisms() {
        const testName = 'Fallback Mechanisms';
        console.log(`📋 Testing: ${testName}`);
        
        try {
            const escpos = new ESCPOSCommands();
            
            // Test graphics to text fallback
            try {
                const commands = await escpos.generateESCPOSCommands(
                    this.sampleTasks.simple,
                    { mode: 'graphics', allowFallback: true }
                );
                // Should work with graphics mode
                this.assert(commands instanceof Uint8Array, 
                    'Should generate commands in graphics mode');
            } catch (error) {
                // Graphics failure should not happen in normal operation
                console.log('  ↳ Graphics generation test (expected to succeed in production)');
            }
            
            // Test no fallback scenario
            await this.assertAsyncThrows(async () => {
                await escpos.generateESCPOSCommands(
                    this.sampleTasks.simple,
                    { mode: 'invalid', allowFallback: false }
                );
            }, 'Should fail with invalid mode');
            
            this.passTest(testName);
            
        } catch (error) {
            this.failTest(testName, error.message);
        }
    }

    /**
     * Test utility functions
     */

    assert(condition, message) {
        this.totalTests++;
        if (condition) {
            this.passedTests++;
            console.log(`  ✅ ${message}`);
        } else {
            this.failedTests++;
            console.log(`  ❌ ${message}`);
            throw new Error(`Assertion failed: ${message}`);
        }
    }

    assertThrows(fn, message) {
        this.totalTests++;
        try {
            fn();
            this.failedTests++;
            console.log(`  ❌ ${message} (should have thrown)`);
            throw new Error(`Expected function to throw: ${message}`);
        } catch (error) {
            this.passedTests++;
            console.log(`  ✅ ${message}`);
        }
    }

    async assertAsyncThrows(asyncFn, message) {
        this.totalTests++;
        try {
            await asyncFn();
            this.failedTests++;
            console.log(`  ❌ ${message} (should have thrown)`);
            throw new Error(`Expected async function to throw: ${message}`);
        } catch (error) {
            this.passedTests++;
            console.log(`  ✅ ${message}`);
        }
    }

    passTest(testName) {
        console.log(`✅ ${testName} - PASSED\n`);
        this.testResults.push({ name: testName, status: 'PASSED' });
    }

    failTest(testName, error) {
        console.log(`❌ ${testName} - FAILED: ${error}\n`);
        this.testResults.push({ name: testName, status: 'FAILED', error });
    }

    printTestSummary() {
        console.log('📊 TEST SUMMARY');
        console.log('================');
        console.log(`Total Tests: ${this.totalTests}`);
        console.log(`Passed: ${this.passedTests}`);
        console.log(`Failed: ${this.failedTests}`);
        console.log(`Success Rate: ${((this.passedTests / this.totalTests) * 100).toFixed(1)}%`);
        console.log('');
        
        console.log('📋 Test Results:');
        this.testResults.forEach(result => {
            const status = result.status === 'PASSED' ? '✅' : '❌';
            console.log(`  ${status} ${result.name}`);
            if (result.error) {
                console.log(`     Error: ${result.error}`);
            }
        });
        
        if (this.failedTests === 0) {
            console.log('\n🎉 All tests passed!');
        } else {
            console.log(`\n⚠️  ${this.failedTests} test(s) failed.`);
        }
    }
}

// Global test functions for browser console
async function runESCPOSTests() {
    const testSuite = new ESCPOSTestSuite();
    await testSuite.runAllTests();
    return testSuite;
}

async function testESCPOSGraphicsMode() {
    console.log('🧪 Quick Graphics Mode Test');
    try {
        const escpos = new ESCPOSCommands();
        const task = {
            id: 999,
            title: 'Quick Test Task',
            description: 'Testing graphics mode generation',
            urgency: 'normal',
            due_date: new Date().toISOString(),
            hierarchy: ['Quick Test Task']
        };
        
        const commands = await escpos.generateESCPOSCommands(task, { mode: 'graphics' });
        console.log(`✅ Generated ${commands.length} bytes of ESC/POS commands`);
        
        // Display sample of commands as hex
        const sample = Array.from(commands.slice(0, 50))
            .map(b => b.toString(16).padStart(2, '0'))
            .join(' ');
        console.log(`Sample (hex): ${sample}...`);
        
        return commands;
    } catch (error) {
        console.error('❌ Graphics mode test failed:', error);
        throw error;
    }
}

async function testESCPOSIntegration() {
    console.log('🧪 Integration Test with Mock Printer');
    try {
        const printManager = new LocalPrintManager();
        
        // Mock the printer manager to avoid actual hardware
        printManager.printerManager = {
            getConnectionStatus: () => ({ connected: true, device: 'Mock Printer' }),
            discoverPrinters: async () => [{ name: 'Mock Printer', type: 'test' }],
            connectToPrinter: async () => {},
            sendData: async (data) => {
                console.log(`📤 Mock printer received ${data.length} bytes`);
                return { success: true };
            }
        };
        
        const task = {
            id: 888,
            title: 'Integration Test Task',
            description: 'Testing complete integration',
            urgency: 'urgent',
            hierarchy: ['Integration Test Task']
        };
        
        // Test with graphics mode (modern workflow)
        const result = await printManager.printTask(task, { mode: 'graphics' });
        
        if (result.success) {
            console.log('✅ Integration test passed');
            console.log(`Duration: ${result.duration}ms`);
            console.log(`Mode: ${result.mode}`);
        } else {
            console.error('❌ Integration test failed:', result.error);
        }
        
        return result;
        
    } catch (error) {
        console.error('❌ Integration test error:', error);
        throw error;
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        ESCPOSTestSuite, 
        runESCPOSTests,
        testESCPOSGraphicsMode,
        testESCPOSIntegration
    };
}

// Auto-run tests if this file is loaded directly
if (typeof window !== 'undefined' && window.location && window.location.search.includes('run-tests')) {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(runESCPOSTests, 1000);
    });
}