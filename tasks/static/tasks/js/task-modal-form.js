/**
 * Task Modal Form JavaScript
 * Handles periodic task form fields in modal context
 */

// Make functions globally available immediately
window.togglePeriodicFields = function() {
    try {
        // Find elements dynamically instead of relying on global variables
        const isPeriodicCheckbox = document.getElementById('id_is_periodic');
        const periodicFields = document.getElementById('modal-periodic-fields');
        const dueDateField = document.querySelector('label[for="id_due_date"]');
        const dueDateContainer = dueDateField ? dueDateField.closest('.col-md-6') : null;
        
        if (isPeriodicCheckbox && isPeriodicCheckbox.checked) {
            if (periodicFields) {
                periodicFields.style.display = 'block';
                periodicFields.style.visibility = 'visible';
            }
            // Hide due date for periodic tasks (they use start_date instead)
            if (dueDateContainer) dueDateContainer.style.display = 'none';
            // Check current periodicity selection
            toggleWeekdaySelection();
        } else {
            if (periodicFields) {
                periodicFields.style.display = 'none';
            }
            if (dueDateContainer) dueDateContainer.style.display = 'block';
        }
    } catch (error) {
        console.error('Error in togglePeriodicFields:', error);
    }
};

window.toggleWeekdaySelection = function() {
    try {
        // Find elements dynamically
        const periodicityType = document.getElementById('id_periodicity_type');
        const weekdaySelection = document.getElementById('modal-weekday-selection');
        
        // Hide all interval field containers first
        const intervalFieldContainers = document.querySelectorAll('div.interval-field[data-type]');
        intervalFieldContainers.forEach(field => {
            field.style.display = 'none';
        });
        
        if (periodicityType) {
            const selectedType = periodicityType.value;
            
            // Handle weekday selection
            if (weekdaySelection) {
                if (selectedType === 'weekly') {
                    weekdaySelection.style.display = 'block';
                } else {
                    weekdaySelection.style.display = 'none';
                }
            }
            
            // Show the appropriate interval field container
            if (selectedType === 'every_x_days') {
                const intervalDaysField = document.querySelector('div.interval-field[data-type="every_x_days"]');
                if (intervalDaysField) {
                    intervalDaysField.style.display = 'block';
                }
            } else if (selectedType === 'every_x_weeks') {
                const intervalWeeksField = document.querySelector('div.interval-field[data-type="every_x_weeks"]');
                if (intervalWeeksField) {
                    intervalWeeksField.style.display = 'block';
                }
            } else if (selectedType === 'every_x_months') {
                const intervalMonthsField = document.querySelector('div.interval-field[data-type="every_x_months"]');
                if (intervalMonthsField) {
                    intervalMonthsField.style.display = 'block';
                }
            }
        }
    } catch (error) {
        console.error('Error in toggleWeekdaySelection:', error);
    }
};

// Initialize when modal content is loaded
function initializeModalPeriodicFields() {
    // Initial state check
    togglePeriodicFields();
    
    // Add event listeners
    const isPeriodicCheckbox = document.getElementById('id_is_periodic');
    const periodicityType = document.getElementById('id_periodicity_type');
    
    if (isPeriodicCheckbox) {
        isPeriodicCheckbox.addEventListener('change', togglePeriodicFields);
    }
    
    if (periodicityType) {
        periodicityType.addEventListener('change', toggleWeekdaySelection);
    }
}

// Expose functions globally
window.initializeModalPeriodicFields = initializeModalPeriodicFields;
window.togglePeriodicFields = togglePeriodicFields;
window.toggleWeekdaySelection = toggleWeekdaySelection;