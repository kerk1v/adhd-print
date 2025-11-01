/**
 * Today's Tasks Page JavaScript
 * Handles printing today's tasks and modal interactions
 */

document.addEventListener('DOMContentLoaded', function() {
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

    const printBtn = document.getElementById('printTodaysTasksBtn');
    const statusMessage = document.getElementById('printStatusMessage');
    let statusModal;
    
    // Initialize status modal if it exists
    const statusModalElement = document.getElementById('printStatusModal');
    if (statusModalElement) {
        statusModal = new bootstrap.Modal(statusModalElement);
    }
    
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            printBtn.disabled = true;
            printBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Printing...';
            
            fetch(printTodaysTasksUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusMessage.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle me-2"></i>
                            ${data.message}
                        </div>
                    `;
                } else {
                    statusMessage.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            ${data.message}
                        </div>
                    `;
                }
                if (statusModal) {
                    statusModal.show();
                }
            })
            .catch(error => {
                statusMessage.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error: ${error.message}
                    </div>
                `;
                if (statusModal) {
                    statusModal.show();
                }
            })
            .finally(() => {
                printBtn.disabled = false;
                printBtn.innerHTML = '<i class="fas fa-print me-2"></i>Print All Today\'s Tasks';
            });
        });
    }
    
    // Universal modal refresh handler - refresh page when modal is closed
    $('.modal').on('hidden.bs.modal', function(e) {
        const modalId = $(this).attr('id');
        console.log(`Modal ${modalId} closed on todays_tasks page - checking if page refresh needed`);
        
        // Check if another modal is about to open to prevent refresh during modal transitions
        setTimeout(() => {
            // Check if any modal is currently being shown or is visible
            const activeModals = $('.modal.show, .modal.showing').length;
            
            if (activeModals > 0) {
                console.log(`Another modal is active - skipping refresh for ${modalId}`);
                return;
            }
            
            console.log(`Refreshing page after ${modalId} modal close to ensure data is current`);
            window.location.reload();
        }, 200); // Delay to allow for modal transitions
    });
});