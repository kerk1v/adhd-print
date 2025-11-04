document.addEventListener('DOMContentLoaded', function() {
    const periodicityTypeField = document.getElementById('id_periodicity_type');
    const isPeriodicField = document.getElementById('id_is_periodic');
    
    // Hide all interval fields initially
    const intervalFields = document.querySelectorAll('.interval-field');
    const weekdaysField = document.querySelector('.field-weekdays');
    
    function toggleIntervalFields() {
        const isPeriodicChecked = isPeriodicField && isPeriodicField.checked;
        const periodicityType = periodicityTypeField ? periodicityTypeField.value : '';
        
        // Hide all interval fields first
        intervalFields.forEach(field => {
            const fieldWrapper = field.closest('.form-row') || field.closest('.field-interval_days, .field-interval_weeks, .field-interval_months');
            if (fieldWrapper) {
                fieldWrapper.style.display = 'none';
            }
        });
        
        // Hide weekdays field
        if (weekdaysField) {
            weekdaysField.style.display = 'none';
        }
        
        if (isPeriodicChecked && periodicityType) {
            // Show appropriate field based on periodicity type
            if (periodicityType === 'every_x_days') {
                const daysField = document.getElementById('id_interval_days');
                if (daysField) {
                    const fieldWrapper = daysField.closest('.form-row') || daysField.closest('.field-interval_days');
                    if (fieldWrapper) fieldWrapper.style.display = '';
                }
            } else if (periodicityType === 'every_x_weeks') {
                const weeksField = document.getElementById('id_interval_weeks');
                if (weeksField) {
                    const fieldWrapper = weeksField.closest('.form-row') || weeksField.closest('.field-interval_weeks');
                    if (fieldWrapper) fieldWrapper.style.display = '';
                }
            } else if (periodicityType === 'every_x_months') {
                const monthsField = document.getElementById('id_interval_months');
                if (monthsField) {
                    const fieldWrapper = monthsField.closest('.form-row') || monthsField.closest('.field-interval_months');
                    if (fieldWrapper) fieldWrapper.style.display = '';
                }
            } else if (periodicityType === 'weekly') {
                // Show weekdays field for regular weekly tasks
                if (weekdaysField) {
                    weekdaysField.style.display = '';
                }
            }
        }
    }
    
    // Add warning for 12-month interval
    const monthsField = document.getElementById('id_interval_months');
    if (monthsField) {
        monthsField.addEventListener('input', function() {
            const value = parseInt(this.value);
            const warningDiv = document.getElementById('months-warning');
            
            // Remove existing warning
            if (warningDiv) {
                warningDiv.remove();
            }
            
            if (value === 12) {
                const warning = document.createElement('div');
                warning.id = 'months-warning';
                warning.style.color = '#ffc107';
                warning.style.fontWeight = 'bold';
                warning.style.marginTop = '5px';
                warning.textContent = '⚠️ Consider using "Yearly" periodicity instead of "Every 12 Months" for better clarity.';
                this.parentNode.appendChild(warning);
            }
        });
    }
    
    // Bind events
    if (isPeriodicField) {
        isPeriodicField.addEventListener('change', toggleIntervalFields);
    }
    
    if (periodicityTypeField) {
        periodicityTypeField.addEventListener('change', toggleIntervalFields);
    }
    
    // Initial state
    toggleIntervalFields();
});