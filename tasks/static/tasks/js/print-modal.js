/**
 * Print Modal JavaScript
 * Handles print confirmation and print operations
 */

// Store task ID for printing
let taskIdToPrint = null;

// Flag to track if we're in the middle of a print operation
let isPrinting = false;

function showPrintConfirmModal(taskId) {
    console.log(`showPrintConfirmModal called with task ID: ${taskId}`);
    console.log('Current taskIdToPrint before setting:', taskIdToPrint);
    taskIdToPrint = taskId;
    console.log('taskIdToPrint set to:', taskIdToPrint);
    console.log('Opening print modal...');
    
    // Check if modal exists
    const modalElement = document.getElementById('printConfirmModal');
    console.log('Modal element found:', modalElement);
    
    // Check if jQuery is available
    console.log('jQuery available:', typeof $ !== 'undefined');
    
    $('#printConfirmModal').modal('show');
    console.log('Modal show command executed');
}

// Handle print confirmation using event delegation
$(document).ready(function() {
    console.log('Print modal JavaScript loaded and ready');
    console.log('Setting up event delegation for #confirmPrintBtn');
    
    // Use event delegation to ensure handler is always available
    $(document).on('click', '#confirmPrintBtn', function() {
        console.log('Print confirmation button clicked via event delegation!');
        console.log('taskIdToPrint:', taskIdToPrint);
        
        if (taskIdToPrint) {
            console.log(`Sending print request for task ${taskIdToPrint}`);
            // Set printing flag to prevent duplicate reloads
            isPrinting = true;
            
            // Show loading state
            $(this).html('<i class="fas fa-spinner fa-spin"></i> Printing...').prop('disabled', true);
            
            // Send print request
            fetch(`/tasks/print/${taskIdToPrint}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else if (response.status === 302 || response.status === 401) {
                    // Redirect to login - user is not authenticated
                    showMessage('Please log in to print tasks.', 'warning');
                    setTimeout(() => {
                        window.location.href = '/admin/login/';
                    }, 2000);
                    return null;
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            })
            .then(data => {
                console.log('Print response received:', data);
                if (!data) return; // Handle authentication redirect case
                
                if (data.success) {
                    console.log('Print successful!');
                    // Show success message
                    if (typeof showMessage === 'function') {
                        showMessage(data.message || 'Task printed successfully!', 'success');
                    } else {
                        console.error('showMessage function not available');
                        alert(data.message || 'Task printed successfully!');
                    }
                } else {
                    console.log('Print failed:', data.message);
                    // Show error message
                    if (typeof showMessage === 'function') {
                        showMessage(data.message || 'Failed to print task.', 'danger');
                    } else {
                        console.error('showMessage function not available');
                        alert(data.message || 'Failed to print task.');
                    }
                }
                $('#printConfirmModal').modal('hide');
            })
            .catch(error => {
                console.error('Print error:', error);
                if (typeof showMessage === 'function') {
                    showMessage('An error occurred while printing the task.', 'danger');
                } else {
                    console.error('showMessage function not available');
                    alert('An error occurred while printing the task.');
                }
                $('#printConfirmModal').modal('hide');
            })
            .finally(() => {
                // Reset button state
                $('#confirmPrintBtn')
                    .html('<i class="fas fa-print"></i> Yes, Print')
                    .prop('disabled', false);
                
                // Clear task ID and printing flag
                taskIdToPrint = null;
                isPrinting = false;
                
                // Reload page to refresh task list
                console.log('Print operation completed - refreshing task list');
                window.location.reload();
            });
        } else {
            console.error('No task ID set for printing!');
        }
    });
    
    console.log('Print confirmation button handler bound successfully');

    // Handle modal being hidden (closed by any means) - this is the main refresh handler
    $('#printConfirmModal').on('hidden.bs.modal', function() {
        console.log('Print modal closed - ensuring task list refresh');
        
        // Clear task ID regardless of how modal was closed
        taskIdToPrint = null;
        
        // Always reload the page to refresh task list, unless we're in the middle of printing
        // (print operation handles its own reload in .finally())
        if (!isPrinting) {
            console.log('Refreshing task list after modal close');
            setTimeout(() => {
                window.location.reload();
            }, 100); // Minimal delay for smooth modal close
        } else {
            console.log('Print operation in progress - reload will be handled by print completion');
        }
    });
    
    // Handle ESC key and backdrop clicks - these will trigger hidden.bs.modal
    $('#printConfirmModal').on('hide.bs.modal', function(e) {
        console.log('Print modal hiding - source:', e.target === this ? 'backdrop/ESC' : 'button');
        // Clear task ID when modal starts hiding
        if (!isPrinting) {
            taskIdToPrint = null;
        }
    });
});

// Export functions for global use
window.showPrintConfirmModal = showPrintConfirmModal;