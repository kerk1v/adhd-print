/**
 * Task Management Common Utilities
 * Shared JavaScript functionality across all task management pages
 */

// Add CSRF token to all AJAX requests
$(document).ready(function() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                xhr.setRequestHeader("X-CSRFToken", $('[name=csrfmiddlewaretoken]').val());
            }
        }
    });
    
    // Universal modal refresh handler - refresh task list when any modal is closed
    // This ensures the task list is always up-to-date after any modal interaction
    $('.modal').on('hidden.bs.modal', function(e) {
        const modalId = $(this).attr('id');
        console.log(`Modal ${modalId} closed - checking if page refresh needed`);
        
        // Skip refresh for print modal (it has its own refresh logic)
        if (modalId === 'printConfirmModal') {
            console.log('Print modal has its own refresh logic - skipping');
            return;
        }
        
        // For all other modals, check if another modal is about to open
        // This prevents page refresh when transitioning from one modal to another
        // (e.g., task creation → print confirmation)
        setTimeout(() => {
            // Check if any modal is currently being shown or is visible
            const activeModals = $('.modal.show, .modal.showing').length;
            
            if (activeModals > 0) {
                console.log(`Another modal is active - skipping refresh for ${modalId}`);
                return;
            }
            
            console.log(`Refreshing page after ${modalId} modal close`);
            window.location.reload();
        }, 200); // Increased delay to allow for modal transitions
    });
});

/**
 * Display a message to the user
 * @param {string} message - The message to display
 * @param {string} type - Bootstrap alert type (success, danger, warning, info)
 */
function showMessage(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container').prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
}

/**
 * Format date for display
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    if (!date) return '';
    
    const d = new Date(date);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return d.toLocaleDateString('en-US', options);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * Debounce function to limit the rate at which a function can fire
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @param {boolean} immediate - Whether to execute immediately
 * @returns {Function} Debounced function
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise} Promise that resolves when text is copied
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showMessage('Copied to clipboard!', 'success');
        return true;
    } catch (err) {
        console.error('Failed to copy text: ', err);
        showMessage('Failed to copy to clipboard', 'danger');
        return false;
    }
}

/**
 * Check if an element is in the viewport
 * @param {Element} element - Element to check
 * @returns {boolean} True if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Smooth scroll to element
 * @param {string|Element} target - CSS selector or element to scroll to
 * @param {number} offset - Offset from top in pixels
 */
function scrollToElement(target, offset = 0) {
    const element = typeof target === 'string' ? document.querySelector(target) : target;
    if (element) {
        const elementPosition = element.offsetTop;
        const offsetPosition = elementPosition - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize popovers
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Check if user prefers reduced motion
 * @returns {boolean} True if user prefers reduced motion
 */
function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Set up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new task
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newTaskBtn = document.querySelector('[data-bs-target="#taskModal"]');
            if (newTaskBtn) {
                newTaskBtn.click();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modalInstance = bootstrap.Modal.getInstance(openModal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        }
    });
}

// Initialize common functionality when DOM is ready
$(document).ready(function() {
    initializeTooltips();
    initializePopovers();
    setupKeyboardShortcuts();
    
    // Add loading states to buttons (except logout forms)
    $(document).on('click', '.btn[type="submit"]:not([form*="logout"]):not(form[action*="logout"] .btn)', function() {
        const btn = $(this);
        const form = btn.closest('form');
        
        // Skip if this is a logout form
        if (form.attr('action') && form.attr('action').includes('logout')) {
            return true; // Allow normal form submission
        }
        
        const originalText = btn.html();
        btn.html('<i class="fas fa-spinner fa-spin"></i> Loading...')
           .prop('disabled', true);
        
        // Re-enable button after 10 seconds as fallback
        setTimeout(() => {
            btn.html(originalText).prop('disabled', false);
        }, 10000);
    });
});

// Export utilities for use in other scripts
window.TaskUtils = {
    showMessage,
    formatDate,
    escapeHtml,
    debounce,
    copyToClipboard,
    isInViewport,
    scrollToElement,
    initializeTooltips,
    initializePopovers,
    prefersReducedMotion,
    setupKeyboardShortcuts
};