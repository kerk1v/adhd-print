/**
 * Task Form JavaScript
 * Handles periodic task form fields and interactions
 */

function togglePeriodicFields() {
    const isPeriodicCheckbox = document.getElementById(isPeriodicFieldId);
    const periodicFields = document.getElementById('periodic-fields');
    const dueDateField = document.getElementById(dueDateFieldId);
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
    const periodicityType = document.getElementById(periodicityTypeFieldId);
    const weekdaySelection = document.getElementById('weekday-selection');
    
    if (periodicityType && weekdaySelection) {
        if (periodicityType.value === 'weekly') {
            weekdaySelection.style.display = 'block';
        } else {
            weekdaySelection.style.display = 'none';
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    togglePeriodicFields();
    
    // Set up event listeners
    const isPeriodicCheckbox = document.getElementById(isPeriodicFieldId);
    const periodicityTypeField = document.getElementById(periodicityTypeFieldId);
    
    if (isPeriodicCheckbox) {
        isPeriodicCheckbox.addEventListener('change', togglePeriodicFields);
    }
    
    if (periodicityTypeField) {
        periodicityTypeField.addEventListener('change', toggleWeekdaySelection);
    }
});