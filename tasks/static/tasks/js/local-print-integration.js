/**
 * Local Printer Integration for ADHD Print System
 * 
 * This module provides the complete integration layer that combines:
 * - ESC/POS command generation (text + server-side graphics)
 * - WebUSB/WebSerial printer communication
 * - Task-to-printer conversion with fallback strategies
 * - Error handling and user feedback
 * 
 * This serves as the main interface for printing tasks locally,
 * bridging the gap between task data and physical printer output.
 */

class LocalPrintManager {
    constructor() {
        // Initialize dependencies
        this.escposCommands = window.escposCommands || new ESCPOSCommands();
        this.printerManager = window.localPrinterManager || new LocalPrinterManager();
        
        // Print job tracking
        this.currentPrintJob = null;
        this.printQueue = [];
        this.isProcessingQueue = false;
        
        // Configuration
        this.config = {
            preferredMode: 'graphics',        // 'graphics' or 'text'
            allowFallback: true,              // Allow fallback to text mode
            retryAttempts: 2,                 // Number of retry attempts
            timeoutMs: 30000,                 // Print timeout in milliseconds
            queueProcessingDelay: 1000        // Delay between queued prints
        };
        
        // Event handlers
        this.eventHandlers = {
            printStart: [],
            printSuccess: [],
            printError: [],
            queueUpdate: []
        };
    }

    /**
     * Print a single task with comprehensive error handling
     * @param {Object} task - Task object or task ID
     * @param {Object} options - Print options
     * @returns {Promise<Object>} Print result with success status and details
     */
    async printTask(task, options = {}) {
        const startTime = Date.now();
        const printJob = {
            id: this.generateJobId(),
            type: 'single_task',
            task: task,
            options: { ...this.config, ...options },
            status: 'starting',
            startTime: startTime,
            attempts: 0
        };
        
        this.currentPrintJob = printJob;
        this.notifyEventHandlers('printStart', printJob);
        
        try {
            // Resolve task data if needed
            const taskData = await this.resolveTaskData(task);
            printJob.task = taskData;
            printJob.status = 'preparing';
            
            // Validate task data
            this.escposCommands.validateTask(taskData);
            
            // Ensure printer connection
            await this.ensurePrinterConnection(printJob.options);
            printJob.status = 'generating_commands';
            
            // Generate ESC/POS commands with fallback
            const escposData = await this.generateESCPOSWithRetry(taskData, printJob);
            printJob.status = 'sending_to_printer';
            
            // Send to printer
            await this.printerManager.sendData(escposData);
            
            // Success
            const duration = Date.now() - startTime;
            const result = {
                success: true,
                jobId: printJob.id,
                type: printJob.type,
                mode: printJob.finalMode || printJob.options.preferredMode,
                duration: duration,
                message: `Task "${taskData.title}" printed successfully`,
                details: {
                    taskId: taskData.id,
                    taskTitle: taskData.title,
                    commandBytes: escposData.length,
                    attempts: printJob.attempts + 1
                }
            };
            
            printJob.status = 'completed';
            printJob.result = result;
            this.currentPrintJob = null;
            
            this.notifyEventHandlers('printSuccess', result);
            return result;
            
        } catch (error) {
            // Handle error
            const duration = Date.now() - startTime;
            const result = {
                success: false,
                jobId: printJob.id,
                type: printJob.type,
                error: error.message,
                duration: duration,
                details: {
                    taskId: taskData?.id,
                    taskTitle: taskData?.title,
                    attempts: printJob.attempts + 1,
                    stage: printJob.status
                }
            };
            
            printJob.status = 'failed';
            printJob.result = result;
            printJob.error = error;
            this.currentPrintJob = null;
            
            this.notifyEventHandlers('printError', result);
            return result;
        }
    }

    /**
     * Print multiple tasks in sequence
     * @param {Array} tasks - Array of task objects or task IDs
     * @param {Object} options - Print options
     * @returns {Promise<Object>} Batch print results
     */
    async printTasks(tasks, options = {}) {
        const startTime = Date.now();
        const batchJob = {
            id: this.generateJobId(),
            type: 'batch_print',
            tasks: tasks,
            options: { ...this.config, ...options },
            status: 'starting',
            startTime: startTime,
            results: []
        };
        
        this.notifyEventHandlers('printStart', batchJob);
        
        try {
            const results = [];
            let successCount = 0;
            let failureCount = 0;
            
            // Process each task
            for (let i = 0; i < tasks.length; i++) {
                const task = tasks[i];
                batchJob.status = `printing_${i + 1}_of_${tasks.length}`;
                
                try {
                    const result = await this.printTask(task, {
                        ...options,
                        skipQueueNotification: true
                    });
                    
                    results.push(result);
                    if (result.success) {
                        successCount++;
                    } else {
                        failureCount++;
                    }
                    
                    // Delay between prints to avoid overwhelming the printer
                    if (i < tasks.length - 1) {
                        await this.delay(this.config.queueProcessingDelay);
                    }
                    
                } catch (error) {
                    failureCount++;
                    results.push({
                        success: false,
                        error: error.message,
                        taskId: task.id || task,
                        taskTitle: task.title || 'Unknown'
                    });
                }
            }
            
            // Compile batch results
            const duration = Date.now() - startTime;
            const batchResult = {
                success: successCount > 0,
                jobId: batchJob.id,
                type: 'batch_print',
                duration: duration,
                totalTasks: tasks.length,
                successCount: successCount,
                failureCount: failureCount,
                results: results,
                message: `Batch print completed: ${successCount} successful, ${failureCount} failed`
            };
            
            batchJob.status = 'completed';
            batchJob.result = batchResult;
            
            this.notifyEventHandlers('printSuccess', batchResult);
            return batchResult;
            
        } catch (error) {
            const duration = Date.now() - startTime;
            const batchResult = {
                success: false,
                jobId: batchJob.id,
                type: 'batch_print',
                error: error.message,
                duration: duration,
                message: 'Batch print failed'
            };
            
            batchJob.status = 'failed';
            batchJob.result = batchResult;
            
            this.notifyEventHandlers('printError', batchResult);
            return batchResult;
        }
    }

    /**
     * Add task to print queue for background processing
     * @param {Object} task - Task object or task ID
     * @param {Object} options - Print options
     * @returns {string} Queue job ID
     */
    addToQueue(task, options = {}) {
        const queueJob = {
            id: this.generateJobId(),
            task: task,
            options: { ...this.config, ...options },
            addedAt: Date.now(),
            status: 'queued'
        };
        
        this.printQueue.push(queueJob);
        this.notifyEventHandlers('queueUpdate', {
            action: 'added',
            job: queueJob,
            queueLength: this.printQueue.length
        });
        
        // Start processing if not already running
        if (!this.isProcessingQueue) {
            this.processQueue();
        }
        
        return queueJob.id;
    }

    /**
     * Process the print queue in background
     */
    async processQueue() {
        if (this.isProcessingQueue || this.printQueue.length === 0) {
            return;
        }
        
        this.isProcessingQueue = true;
        
        while (this.printQueue.length > 0) {
            const queueJob = this.printQueue.shift();
            queueJob.status = 'processing';
            
            this.notifyEventHandlers('queueUpdate', {
                action: 'processing',
                job: queueJob,
                queueLength: this.printQueue.length
            });
            
            try {
                const result = await this.printTask(queueJob.task, queueJob.options);
                queueJob.status = result.success ? 'completed' : 'failed';
                queueJob.result = result;
                
            } catch (error) {
                queueJob.status = 'failed';
                queueJob.error = error;
            }
            
            this.notifyEventHandlers('queueUpdate', {
                action: 'completed',
                job: queueJob,
                queueLength: this.printQueue.length
            });
            
            // Delay between queue items
            if (this.printQueue.length > 0) {
                await this.delay(this.config.queueProcessingDelay);
            }
        }
        
        this.isProcessingQueue = false;
    }

    /**
     * Test printer connection and print a test page
     * @returns {Promise<Object>} Test result
     */
    async testPrinter() {
        try {
            // Ensure printer connection
            await this.ensurePrinterConnection();
            
            // Generate test print commands
            const testCommands = this.escposCommands.generateTestPrint();
            
            // Send to printer
            await this.printerManager.sendData(testCommands);
            
            return {
                success: true,
                message: 'Test print completed successfully',
                commandBytes: testCommands.length
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                message: 'Test print failed'
            };
        }
    }

    /**
     * Get current printer status and connection info
     * @returns {Object} Status information
     */
    getStatus() {
        return {
            connection: this.printerManager.getConnectionStatus(),
            currentJob: this.currentPrintJob,
            queueLength: this.printQueue.length,
            isProcessingQueue: this.isProcessingQueue,
            supportedMethods: this.printerManager.getSupportedMethods(),
            config: { ...this.config }
        };
    }

    /**
     * Resolve task data from task object or ID
     * @private
     */
    async resolveTaskData(task) {
        if (typeof task === 'object' && task.title) {
            // Already a task object
            return task;
        }
        
        if (typeof task === 'number' || typeof task === 'string') {
            // Task ID - fetch from server
            try {
                const response = await fetch(`/tasks/api/task/${task}/`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch task ${task}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                throw new Error(`Unable to load task data: ${error.message}`);
            }
        }
        
        throw new Error('Invalid task data provided');
    }

    /**
     * Ensure printer connection is established
     * @private
     */
    async ensurePrinterConnection(options = {}) {
        const status = this.printerManager.getConnectionStatus();
        
        if (status.connected) {
            return; // Already connected
        }
        
        // Try to connect
        const preferredMethod = options.connectionMethod || 'auto';
        const devices = await this.printerManager.discoverPrinters(preferredMethod);
        
        if (devices.length === 0) {
            throw new Error('No compatible printers found. Please connect a thermal printer and try again.');
        }
        
        // Use first available device (could be made configurable)
        const device = devices[0];
        await this.printerManager.connectToPrinter(device);
    }

    /**
     * Generate ESC/POS commands with retry and fallback
     * @private
     */
    async generateESCPOSWithRetry(taskData, printJob) {
        const maxAttempts = printJob.options.retryAttempts + 1;
        let lastError = null;
        
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            printJob.attempts = attempt;
            
            try {
                // Try preferred mode first, then fallback
                const mode = attempt === 0 ? printJob.options.preferredMode : 'text';
                printJob.finalMode = mode;
                
                const escposData = await this.escposCommands.generateESCPOSCommands(taskData, {
                    mode: mode,
                    allowFallback: printJob.options.allowFallback && attempt === 0
                });
                
                return escposData;
                
            } catch (error) {
                lastError = error;
                console.warn(`ESC/POS generation attempt ${attempt + 1} failed:`, error.message);
                
                // If this was the last attempt, or fallback is disabled, throw the error
                if (attempt === maxAttempts - 1 || !printJob.options.allowFallback) {
                    break;
                }
                
                // Wait before retry
                await this.delay(500 * (attempt + 1));
            }
        }
        
        throw lastError || new Error('ESC/POS generation failed after all attempts');
    }

    /**
     * Utility function for delays
     * @private
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Generate unique job ID
     * @private
     */
    generateJobId() {
        return `print_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Event handler management
     */
    addEventListener(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].push(handler);
        }
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers[event]) {
            const index = this.eventHandlers[event].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[event].splice(index, 1);
            }
        }
    }

    notifyEventHandlers(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${event} event handler:`, error);
                }
            });
        }
    }

    /**
     * Update configuration
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }

    /**
     * Clear print queue
     */
    clearQueue() {
        this.printQueue = [];
        this.notifyEventHandlers('queueUpdate', {
            action: 'cleared',
            queueLength: 0
        });
    }

    /**
     * Get print queue status
     */
    getQueueStatus() {
        return {
            length: this.printQueue.length,
            isProcessing: this.isProcessingQueue,
            jobs: this.printQueue.map(job => ({
                id: job.id,
                taskTitle: job.task?.title || 'Unknown',
                status: job.status,
                addedAt: job.addedAt
            }))
        };
    }
}

// Integration helper functions for existing UI

/**
 * Print task from existing task list UI
 * @param {number} taskId - Task ID
 * @param {Object} options - Print options
 * @returns {Promise<void>}
 */
async function printTaskFromUI(taskId, options = {}) {
    try {
        // Show loading state
        showPrintSpinner(taskId);
        
        const result = await localPrintManager.printTask(taskId, options);
        
        if (result.success) {
            showPrintSuccess(taskId, result.message);
        } else {
            showPrintError(taskId, result.error || 'Print failed');
        }
        
    } catch (error) {
        showPrintError(taskId, error.message);
    } finally {
        hidePrintSpinner(taskId);
    }
}

/**
 * Print today's tasks from UI
 * @returns {Promise<void>}
 */
async function printTodaysTasksFromUI() {
    try {
        // Show loading state
        showPrintSpinner('todays-tasks');
        
        // Get today's tasks from existing function or API
        const todaysTasks = await getTodaysTasks();
        
        if (todaysTasks.length === 0) {
            showPrintError('todays-tasks', 'No tasks found for today');
            return;
        }
        
        const result = await localPrintManager.printTasks(todaysTasks);
        
        if (result.success) {
            showPrintSuccess('todays-tasks', result.message);
        } else {
            showPrintError('todays-tasks', result.error || 'Batch print failed');
        }
        
    } catch (error) {
        showPrintError('todays-tasks', error.message);
    } finally {
        hidePrintSpinner('todays-tasks');
    }
}

/**
 * Get today's tasks (placeholder - should match existing implementation)
 */
async function getTodaysTasks() {
    try {
        const response = await fetch('/tasks/today/api/');
        if (!response.ok) {
            throw new Error('Failed to fetch today\'s tasks');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching today\'s tasks:', error);
        return [];
    }
}

/**
 * UI helper functions (to be adapted to existing UI)
 */
function showPrintSpinner(elementId) {
    // Implementation depends on existing UI framework
    console.log(`Showing print spinner for ${elementId}`);
}

function hidePrintSpinner(elementId) {
    // Implementation depends on existing UI framework
    console.log(`Hiding print spinner for ${elementId}`);
}

function showPrintSuccess(elementId, message) {
    // Implementation depends on existing UI framework
    console.log(`Print success for ${elementId}: ${message}`);
}

function showPrintError(elementId, error) {
    // Implementation depends on existing UI framework
    console.error(`Print error for ${elementId}: ${error}`);
}

// Create global instance
const localPrintManager = new LocalPrintManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        LocalPrintManager, 
        localPrintManager,
        printTaskFromUI,
        printTodaysTasksFromUI
    };
}