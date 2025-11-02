/**
 * Enhanced Today's Tasks JavaScript
 * Handles printing today's tasks with both local and server printing support
 */

// Global variables
let todaysPrintModal = null;
let isPrintingTodays = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Initializing Today\'s Tasks page...');
    
    // Initialize the print modal
    initializeTodaysPrintModal();
    
    // Universal modal refresh handler
    let activeModals = new Set();
    
    document.addEventListener('show.bs.modal', function(e) {
        const modalId = e.target.id;
        activeModals.add(modalId);
    });
    
    document.addEventListener('hidden.bs.modal', function(e) {
        const modalId = e.target.id;
        activeModals.delete(modalId);
        
        // Check if there are other active modals
        if (activeModals.size > 0) {
            console.log('Another modal is active - skipping refresh');
            return;
        }
        
        // Only refresh if we're on the today's tasks page and no other modals are active
        if (window.location.pathname === '/tasks/today/') {
            console.log('Modal closed - refreshing today\'s tasks page');
            setTimeout(function() {
                window.location.reload();
            }, 100);
        }
    });
});

function initializeTodaysPrintModal() {
    const modalElement = document.getElementById('printTodaysTasksModal');
    if (!modalElement) {
        console.error('Print today\'s tasks modal element not found');
        return;
    }
    
    // Initialize Bootstrap modal
    todaysPrintModal = new bootstrap.Modal(modalElement);
    
    // Setup event listeners
    setupTodaysPrintEventListeners();
    
    console.log('✅ Today\'s Tasks print modal initialized');
}

function setupTodaysPrintEventListeners() {
    // Print confirmation button
    const confirmBtn = document.getElementById('confirmTodaysPrintBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', handleTodaysPrintConfirmation);
    }
    
    // Print method change events
    document.addEventListener('change', (e) => {
        if (e.target.name === 'todays_print_method') {
            const printOptions = document.getElementById('todays-print-options');
            if (e.target.value === 'local') {
                printOptions.style.display = 'block';
            } else {
                printOptions.style.display = 'none';
            }
        }
    });
    
    // Modal show event - load user preferences
    document.getElementById('printTodaysTasksModal').addEventListener('show.bs.modal', () => {
        loadTodaysUserPreferences();
    });
    
    // Modal hide event - reset state
    document.getElementById('printTodaysTasksModal').addEventListener('hidden.bs.modal', () => {
        resetTodaysModal();
    });
}

async function loadTodaysUserPreferences() {
    try {
        // Load user preferences from the server
        const response = await fetch('/users/api/profile/');
        if (response.ok) {
            const profile = await response.json();
            
            // Set print method preference
            const printMethod = profile.printing_method || 'local';
            const localRadio = document.getElementById('todays_local_print');
            const serverRadio = document.getElementById('todays_server_print');
            
            if (printMethod === 'local') {
                localRadio.checked = true;
            } else {
                serverRadio.checked = true;
            }
            
            // Hide server option if not enabled for user
            const serverOption = document.getElementById('server-print-option');
            if (!profile.server_printing_enabled) {
                serverOption.style.display = 'none';
            } else {
                serverOption.style.display = 'block';
            }
            
            // Set printer width preference
            const printerWidth = profile.printer_settings?.width || '80mm';
            const widthSelect = document.getElementById('todays-print-width');
            if (widthSelect) {
                widthSelect.value = printerWidth;
            }
            
            // Show/hide print options based on method
            const printOptions = document.getElementById('todays-print-options');
            if (printMethod === 'local') {
                printOptions.style.display = 'block';
            } else {
                printOptions.style.display = 'none';
            }
            
        } else {
            console.warn('Could not load user preferences, using defaults');
            setTodaysDefaultPreferences();
        }
        
    } catch (error) {
        console.error('Error loading user preferences:', error);
        setTodaysDefaultPreferences();
    }
}

function setTodaysDefaultPreferences() {
    // Set default print method
    const localRadio = document.getElementById('todays_local_print');
    const serverRadio = document.getElementById('todays_server_print');
    
    localRadio.checked = true;
    
    // Show print options for local printing by default
    const printOptions = document.getElementById('todays-print-options');
    printOptions.style.display = 'block';
    
    // Set default printer width
    const widthSelect = document.getElementById('todays-print-width');
    if (widthSelect) {
        widthSelect.value = '80mm';
    }
}

async function handleTodaysPrintConfirmation() {
    console.log('🖨️ handleTodaysPrintConfirmation called, isPrintingTodays:', isPrintingTodays);
    
    if (isPrintingTodays) {
        console.log('🖨️ Already printing today\'s tasks - aborting');
        return;
    }
    
    isPrintingTodays = true;
    console.log('🖨️ Starting today\'s tasks print process...');
    
    try {
        // Get selected print method
        const selectedMethod = document.querySelector('input[name="todays_print_method"]:checked').value;
        
        // Show progress
        showTodaysProgress('Initializing print...');
        
        if (selectedMethod === 'local') {
            await handleTodaysLocalPrint();
        } else {
            await handleTodaysServerPrint();
        }
        
    } catch (error) {
        console.error('Today\'s tasks print error:', error);
        showTodaysError(`Print failed: ${error.message}`);
    } finally {
        isPrintingTodays = false;
        hideTodaysProgress();
    }
}

async function handleTodaysLocalPrint() {
    try {
        // Check if local print manager is available
        if (typeof localPrintManager === 'undefined') {
            throw new Error('Local printing not available. Please refresh the page or use server printing.');
        }
        
        updateTodaysProgress(20, 'Preparing today\'s tasks data...');
        
        // Get print options - always use high quality graphics mode
        const width = document.getElementById('todays-print-width').value;
        
        // Fetch today's tasks data from server
        updateTodaysProgress(30, 'Fetching tasks data...');
        const tasksData = await fetchTodaysTasksDataForLocalPrint();
        
        updateTodaysProgress(40, 'Connecting to printer...');
        
        // Ensure printer connection
        const status = localPrintManager.getStatus();
        if (!status.connection.connected) {
            // Try to auto-connect to last used printer
            await autoConnectPrinter();
        }
        
        updateTodaysProgress(60, 'Generating print commands...');
        
        // Prepare print options
        const printOptions = {
            mode: 'graphics',  // Always use graphics mode
            allowFallback: false,  // No fallback needed
            printerWidth: width,
            taskType: 'todays_tasks'
        };
        
        updateTodaysProgress(80, 'Sending to printer...');
        
        // Print today's tasks using the printTasks method
        const result = await localPrintManager.printTasks(tasksData, printOptions);
        
        updateTodaysProgress(100, 'Print completed!');
        
        if (result.success) {
            showTodaysSuccess(result.message);
            setTimeout(() => {
                todaysPrintModal.hide();
            }, 1500);
        } else {
            throw new Error(result.error || 'Local print of today\'s tasks failed');
        }
        
    } catch (error) {
        console.error('Today\'s tasks local print error:', error);
        
        // Try fallback to server printing if enabled
        if (await shouldFallbackToServer()) {
            showTodaysWarning('Local printing failed. Falling back to server printing...');
            await handleTodaysServerPrint();
        } else {
            throw error;
        }
    }
}

async function handleTodaysServerPrint() {
    try {
        updateTodaysProgress(30, 'Sending to server...');
        
        // Use existing server printing endpoint
        const response = await fetch(printTodaysTasksUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        });
        
        updateTodaysProgress(70, 'Processing on server...');
        
        if (!response.ok) {
            if (response.status === 302 || response.status === 401) {
                throw new Error('Please log in to print tasks.');
            }
            throw new Error(`Server error: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        updateTodaysProgress(100, 'Print completed!');
        
        if (data.success) {
            showTodaysSuccess(data.message || 'Today\'s tasks printed successfully via server!');
            setTimeout(() => {
                todaysPrintModal.hide();
            }, 1500);
        } else {
            throw new Error(data.message || 'Server printing of today\'s tasks failed');
        }
        
    } catch (error) {
        console.error('Today\'s tasks server print error:', error);
        throw error;
    }
}

async function fetchTodaysTasksDataForLocalPrint() {
    // Call the server endpoint with local printing method to get task data
    const response = await fetch(printTodaysTasksUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            print_method: 'local'
        })
    });
    
    if (!response.ok) {
        throw new Error(`Failed to fetch tasks data: HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
        throw new Error(data.message || 'Failed to fetch tasks data');
    }
    
    if (!data.task_data) {
        throw new Error('No task data received from server');
    }
    
    return data.task_data;
}

async function fetchTodaysTasksData() {
    // This would typically fetch the tasks data from the server
    // For now, we'll use placeholder data structure
    return {
        date: new Date().toISOString().split('T')[0],
        tasks: [] // Would contain the actual task data
    };
}

async function shouldFallbackToServer() {
    try {
        const response = await fetch('/users/api/profile/');
        if (response.ok) {
            const profile = await response.json();
            return profile.server_printing_enabled;
        }
    } catch (error) {
        console.error('Error checking server printing availability:', error);
    }
    return false;
}

async function autoConnectPrinter() {
    if (typeof localPrintManager !== 'undefined') {
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
                await localPrintManager.printerManager.connectToPrinter(printers[0]);
                console.log('🔌 Printer connected successfully');
            } else {
                console.warn('🔌 No compatible printers found');
                throw new Error('No compatible printers found. Please ensure your printer is connected and try again.');
            }
        } catch (error) {
            console.error('Auto-connect failed:', error);
            throw error; // Re-throw to let calling code handle it
        }
    } else {
        throw new Error('Local print manager not available');
    }
}

// Progress and status functions
function showTodaysProgress(message) {
    const progressDiv = document.getElementById('todays-print-progress');
    const progressText = document.getElementById('todays-print-progress-text');
    const progressBar = document.getElementById('todays-print-progress-bar');
    
    progressText.textContent = message;
    progressBar.style.width = '0%';
    progressDiv.style.display = 'block';
}

function updateTodaysProgress(percent, message) {
    const progressText = document.getElementById('todays-print-progress-text');
    const progressBar = document.getElementById('todays-print-progress-bar');
    
    progressText.textContent = message;
    progressBar.style.width = percent + '%';
}

function hideTodaysProgress() {
    const progressDiv = document.getElementById('todays-print-progress');
    progressDiv.style.display = 'none';
}

function showTodaysSuccess(message) {
    const statusDiv = document.getElementById('todays-print-status-messages');
    statusDiv.innerHTML = `
        <div class="alert alert-success">
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        </div>
    `;
}

function showTodaysError(message) {
    const statusDiv = document.getElementById('todays-print-status-messages');
    statusDiv.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        </div>
    `;
}

function showTodaysWarning(message) {
    const statusDiv = document.getElementById('todays-print-status-messages');
    statusDiv.innerHTML = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        </div>
    `;
}

function resetTodaysModal() {
    // Clear status messages
    const statusDiv = document.getElementById('todays-print-status-messages');
    statusDiv.innerHTML = '';
    
    // Hide progress
    hideTodaysProgress();
    
    // Reset printing flag
    isPrintingTodays = false;
}