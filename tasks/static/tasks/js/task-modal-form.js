/**
 * Task Modal Form JavaScript
 * Handles periodic task form fields in modal context
 */

// Modal periodic fields functions - these are used by the form widget onchange handlers
function togglePeriodicFields() {
    const isPeriodicCheckbox = document.getElementById(modalIsPeriodicFieldId);
    const periodicFields = document.getElementById('modal-periodic-fields');
    const dueDateField = document.querySelector(`label[for="${modalDueDateFieldId}"]`);
    const dueDateContainer = dueDateField ? dueDateField.closest('.col-md-6') : null;
    
    if (isPeriodicCheckbox && isPeriodicCheckbox.checked) {
        if (periodicFields) periodicFields.style.display = 'block';
        // Hide due date for periodic tasks (they use start_date instead)
        if (dueDateContainer) dueDateContainer.style.display = 'none';
        // Check if weekly is already selected to show weekday options
        toggleWeekdaySelection();
    } else {
        if (periodicFields) periodicFields.style.display = 'none';
        if (dueDateContainer) dueDateContainer.style.display = 'block';
    }
}

function toggleWeekdaySelection() {
    const periodicityType = document.getElementById(modalPeriodicityTypeFieldId);
    const weekdaySelection = document.getElementById('modal-weekday-selection');
    
    if (periodicityType && weekdaySelection) {
        if (periodicityType.value === 'weekly') {
            weekdaySelection.style.display = 'block';
        } else {
            weekdaySelection.style.display = 'none';
        }
    }
}

// Initialize when modal content is loaded
function initializeModalPeriodicFields() {
    // Initial state
    togglePeriodicFields();
    
    // Note: Event listeners are already attached via the form widget onchange attributes
    // No need to manually add them here
}

// Handle both immediate DOM ready and modal load events
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(initializeModalPeriodicFields, 100);
    });
} else {
    setTimeout(initializeModalPeriodicFields, 100);
}

// Also expose function globally for manual initialization
window.initializeModalPeriodicFields = initializeModalPeriodicFields;