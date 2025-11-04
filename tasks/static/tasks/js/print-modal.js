/**
 * Enhanced Print Modal JavaScript
 * Handles both local and server printing with comprehensive UI feedback
 */

// Store task data for printing
let currentPrintTask = null;
let isPrinting = false;
let printModal = null;

// Print modal management
class PrintModalManager {
    constructor() {
        this.modal = null;
        this.currentTask = null;
        this.isInitialized = false;
        
        this.bindEvents();
    }
    
    bindEvents() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        if (this.isInitialized) return;
        
        console.log('Initializing enhanced print modal...');
        
        // Get modal element
        const modalElement = document.getElementById('printConfirmModal');
        if (!modalElement) {
            console.error('Print modal element not found');
            return;
        }
        
        // Initialize Bootstrap modal
        this.modal = new bootstrap.Modal(modalElement);
        
        // Setup event listeners using event delegation
        this.setupEventListeners();
        
        this.isInitialized = true;
        console.log('Print modal initialized successfully');
    }
    
    setupEventListeners() {
        // Print confirmation button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'confirmPrintBtn' || e.target.closest('#confirmPrintBtn')) {
                console.log('🖨️ Print Task button clicked!');
                e.preventDefault();
                this.handlePrintConfirmation();
            }
        });
        
        // Print method change events
        document.addEventListener('change', (e) => {
            if (e.target.name === 'print_method') {
                const printOptions = document.getElementById('print-options');
                if (e.target.value === 'local') {
                    printOptions.style.display = 'block';
                } else {
                    printOptions.style.display = 'none';
                }
            }
        });
        
        // Modal events
        document.getElementById('printConfirmModal').addEventListener('hidden.bs.modal', () => {
            this.resetModal();
        });
    }
    
    async showPrintModal(taskId, taskTitle = null) {
        if (!this.isInitialized) {
            console.error('Print modal not initialized');
            return;
        }
        
        console.log(`Showing print modal for task ${taskId}`);
        
        // Store current task
        this.currentTask = { id: taskId, title: taskTitle };
        
        // Update modal title
        if (taskTitle) {
            document.getElementById('print-task-title').textContent = `Print "${taskTitle}"?`;
        }
        
        // Reset modal state (but preserve task)
        this.resetModalState();
        
        // Load user preferences and printer status
        await this.loadUserPreferences();
        
        // Show modal
        this.modal.show();
    }
    
    async loadUserPreferences() {
        try {
            // Load user preferences from the server
            const response = await fetch('/users/api/profile/');
            if (response.ok) {
                const profile = await response.json();
                
                // Set print method preference
                const printMethod = profile.printing_method || 'local';
                const localRadio = document.getElementById('local_print');
                const serverRadio = document.getElementById('server_print');
                
                // Hide server option if not enabled for user
                const serverOption = serverRadio?.closest('.form-check');
                if (!profile.server_printing_enabled) {
                    if (serverOption) {
                        serverOption.style.display = 'none';
                    }
                } else {
                    if (serverOption) {
                        serverOption.style.display = 'block';
                    }
                }
                
                if (printMethod === 'local' || !profile.server_printing_enabled) {
                    localRadio.checked = true;
                } else {
                    serverRadio.checked = true;
                }
                
                // Set printer width preference
                const printerWidth = profile.printer_settings?.width || '80mm';
                const widthSelect = document.getElementById('print-width-modal');
                if (widthSelect) {
                    widthSelect.value = printerWidth;
                }
                
                // Show/hide print options based on method
                const printOptions = document.getElementById('print-options');
                if (printMethod === 'local') {
                    printOptions.style.display = 'block';
                } else {
                    printOptions.style.display = 'none';
                }
                
            } else {
                // Fallback to defaults if API fails
                console.warn('Could not load user preferences, using defaults');
                this.setDefaultPreferences();
            }
            
        } catch (error) {
            console.error('Error loading user preferences:', error);
            this.setDefaultPreferences();
        }
    }
    
    setDefaultPreferences() {
        // Set default print method
        const localRadio = document.getElementById('local_print');
        const serverRadio = document.getElementById('server_print');
        
        localRadio.checked = true;
        
        // Hide server option by default (until we know if it's enabled)
        const serverOption = serverRadio?.closest('.form-check');
        if (serverOption) {
            serverOption.style.display = 'none';
        }
        
        // Show print options for local printing by default
        const printOptions = document.getElementById('print-options');
        printOptions.style.display = 'block';
        
        // Set default printer width
        const widthSelect = document.getElementById('print-width-modal');
        if (widthSelect) {
            widthSelect.value = '80mm';
        }
    }
    
    async handlePrintConfirmation() {
        console.log('🖨️ handlePrintConfirmation called, currentTask:', this.currentTask, 'isPrinting:', isPrinting);
        
        if (!this.currentTask || isPrinting) {
            console.log('🖨️ Aborting print confirmation - no task or already printing');
            return;
        }
        
        isPrinting = true;
        console.log('🖨️ Starting print process...');
        
        try {
            // Get selected print method
            const selectedMethod = document.querySelector('input[name="print_method"]:checked').value;
            
            // Show progress
            this.showProgress('Initializing print...');
            
            if (selectedMethod === 'local') {
                await this.handleLocalPrint();
            } else {
                await this.handleServerPrint();
            }
            
        } catch (error) {
            console.error('Print error:', error);
            this.showError(`Print failed: ${error.message}`);
        } finally {
            isPrinting = false;
            this.hideProgress();
        }
    }
    
    async handleLocalPrint() {
        try {
            // Check if local print manager is available
            if (typeof localPrintManager === 'undefined') {
                throw new Error('Local printing not available. Please refresh the page or use server printing.');
            }
            
            this.updateProgress(20, 'Preparing task data...');
            
            // Get print options - always use high quality graphics mode
            const width = document.getElementById('print-width-modal').value;
            
            // Fetch task data
            const taskData = await this.fetchTaskData(this.currentTask.id);
            
            this.updateProgress(40, 'Connecting to printer...');
            
            // Ensure printer connection
            const status = localPrintManager.getStatus();
            if (!status.connection.connected) {
                // Try to auto-connect to last used printer
                await this.autoConnectPrinter();
            }
            
            this.updateProgress(60, 'Generating print commands...');
            
            // Prepare print options
            const printOptions = {
                mode: 'graphics',  // Always use graphics mode
                allowFallback: false,  // No fallback needed
                taskId: this.currentTask.id,
                printerWidth: width
            };
            
            this.updateProgress(80, 'Sending to printer...');
            
            // Print the task
            const result = await localPrintManager.printTask(taskData, printOptions);
            
            this.updateProgress(100, 'Print completed!');
            
            if (result.success) {
                // Mark task as printed after successful local printing
                try {
                    await this.markTaskAsPrinted(this.currentTask.id);
                } catch (markError) {
                    console.warn('Failed to mark task as printed:', markError);
                    // Don't fail the whole operation if marking fails
                }
                
                this.showSuccess(result.message);
                setTimeout(() => {
                    this.modal.hide();
                }, 1500);
            } else {
                throw new Error(result.error || 'Local print failed');
            }
            
        } catch (error) {
            console.error('Local print error:', error);
            
            // Try fallback to server printing if enabled
            if (await this.shouldFallbackToServer()) {
                this.showWarning('Local printing failed. Falling back to server printing...');
                await this.handleServerPrint();
            } else {
                throw error;
            }
        }
    }
    
    async handleServerPrint() {
        try {
            this.updateProgress(30, 'Sending to server...');
            
            // Get printer width from the modal
            const width = document.getElementById('print-width-modal').value;
            
            // Use existing server printing endpoint with printer width data
            const response = await fetch(`/tasks/print/${this.currentTask.id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    printerWidth: width
                })
            });
            
            this.updateProgress(70, 'Processing on server...');
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    throw new Error('Please log in to print tasks.');
                }
                throw new Error(`Server error: HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            this.updateProgress(100, 'Print completed!');
            
            if (data.success) {
                this.showSuccess(data.message || 'Task printed successfully via server!');
                setTimeout(() => {
                    this.modal.hide();
                }, 1500);
            } else {
                throw new Error(data.message || 'Server printing failed');
            }
            
        } catch (error) {
            throw new Error(`Server printing failed: ${error.message}`);
        }
    }
    
    async fetchTaskData(taskId) {
        try {
            // Fetch full task data from the server
            const response = await fetch(`/tasks/api/task/${taskId}/`);
            if (!response.ok) {
                throw new Error(`Failed to fetch task data: HTTP ${response.status}`);
            }
            
            const taskData = await response.json();
            
            // Ensure all required fields are present
            return {
                id: taskData.id || taskId,
                title: taskData.title || this.currentTask.title || 'Task',
                description: taskData.description || '',
                urgency: taskData.urgency || 'normal',
                due_date: taskData.due_date || null,
                created_at: taskData.created_at || new Date().toISOString(),
                hierarchy: taskData.hierarchy || [taskData.title || this.currentTask.title || 'Task']
            };
        } catch (error) {
            // Fallback to minimal task data if API fails
            console.warn('Failed to fetch full task data, using minimal data:', error);
            return {
                id: taskId,
                title: this.currentTask.title || 'Task',
                description: '',
                urgency: 'normal',
                due_date: null,
                created_at: new Date().toISOString(),
                hierarchy: [this.currentTask.title || 'Task']
            };
        }
    }
    
    async autoConnectPrinter() {
        try {
            console.log('🔌 Connecting to printer via discovery...');
            
            // Try USB discovery first since most thermal printers are USB
            console.log('🔌 Trying USB discovery first...');
            let printers = await localPrintManager.printerManager.discoverPrinters('usb');
            
            // If no USB printers found, try serial as fallback
            if (printers.length === 0) {
                console.log('🔌 No USB printers found, trying serial...');
                printers = await localPrintManager.printerManager.discoverPrinters('serial');
            }
            
            if (printers.length > 0) {
                console.log('🔌 Found printer, connecting...', printers[0]);
                // Connect to first available printer
                await localPrintManager.printerManager.connectToPrinter(printers[0]);
                return true;
            }
            
            throw new Error('No printers found via USB or Serial');
            
        } catch (error) {
            console.error('🔌 Auto-connect failed:', error);
            throw new Error(`Printer connection failed: ${error.message}`);
        }
    }
    
    async shouldFallbackToServer() {
        // Check if server printing is enabled in user preferences
        // For now, return true to allow fallback
        return true;
    }
    
    showProgress(message) {
        const progressDiv = document.getElementById('print-progress');
        const printBtn = document.getElementById('confirmPrintBtn');
        const cancelBtn = document.getElementById('cancel-print-btn');
        
        progressDiv.style.display = 'block';
        printBtn.disabled = true;
        cancelBtn.disabled = true;
        
        this.updateProgress(10, message);
    }
    
    updateProgress(percent, message) {
        const progressBar = document.getElementById('print-progress-bar');
        const progressText = document.getElementById('print-progress-text');
        
        progressBar.style.width = `${percent}%`;
        progressText.textContent = message;
    }
    
    hideProgress() {
        const progressDiv = document.getElementById('print-progress');
        const printBtn = document.getElementById('confirmPrintBtn');
        const cancelBtn = document.getElementById('cancel-print-btn');
        
        progressDiv.style.display = 'none';
        printBtn.disabled = false;
        cancelBtn.disabled = false;
        
        // Reset progress
        this.updateProgress(0, 'Preparing...');
    }
    
    showSuccess(message) {
        this.showStatusMessage(message, 'success');
    }
    
    showError(message) {
        this.showStatusMessage(message, 'danger');
    }
    
    showWarning(message) {
        this.showStatusMessage(message, 'warning');
    }
    
    showStatusMessage(message, type) {
        const messagesDiv = document.getElementById('print-status-messages');
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        messagesDiv.appendChild(alertDiv);
        
        // Auto-dismiss success messages
        if (type === 'success') {
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 3000);
        }
    }
    
    resetModal() {
        // Clear status messages
        document.getElementById('print-status-messages').innerHTML = '';
        
        // Reset progress
        this.hideProgress();
        
        // Reset button states
        document.getElementById('confirmPrintBtn').disabled = false;
        document.getElementById('cancel-print-btn').disabled = false;
        
        // Reset task (only when not printing)
        if (!isPrinting) {
            this.currentTask = null;
        }
    }
    
    resetModalState() {
        // Clear status messages
        document.getElementById('print-status-messages').innerHTML = '';
        
        // Reset progress
        this.hideProgress();
        
        // Reset button states
        document.getElementById('confirmPrintBtn').disabled = false;
        document.getElementById('cancel-print-btn').disabled = false;
        
        // Don't clear the task - we want to keep it for printing
    }
    
    async markTaskAsPrinted(taskId) {
        const response = await fetch('/tasks/mark-printed/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task_ids: [taskId]
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to mark task as printed: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to mark task as printed');
        }
        
        console.log(`✅ Marked task ${taskId} as printed`);
    }
}

// Initialize print modal manager
let printModalManager = null;

// Initialize when DOM is ready  
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!printModalManager) {
            printModalManager = new PrintModalManager();
        }
    });
} else {
    if (!printModalManager) {
        printModalManager = new PrintModalManager();
    }
}

// Global function for backwards compatibility
function showPrintConfirmModal(taskId, taskTitle = null) {
    console.log(`showPrintConfirmModal called with task ID: ${taskId}, title: ${taskTitle}`);
    
    if (printModalManager) {
        printModalManager.showPrintModal(taskId, taskTitle);
    } else {
        console.error('Print modal manager not initialized');
        
        // Fallback to simple confirmation
        if (confirm(`Print task "${taskTitle || taskId}"?`)) {
            // Use old-style server printing as fallback
            fetch(`/tasks/print/${taskId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                }
            }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || 'Task printed successfully!');
                } else {
                    alert(data.message || 'Failed to print task.');
                }
                window.location.reload();
            }).catch(error => {
                console.error('Print error:', error);
                alert('An error occurred while printing the task.');
                window.location.reload();
            });
        }
    }
}

// Export for global use
window.showPrintConfirmModal = showPrintConfirmModal;
window.printModalManager = printModalManager;