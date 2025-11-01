/**
 * Task List Management JavaScript
 * Handles task creation, editing, deletion, and modal interactions
 */

// Global variables
let currentParentId = null;
let currentDeleteTaskId = null;
let currentEditTaskId = null;

// Task creation modal functionality
$(document).ready(function() {
    // Universal modal refresh handler
    let activeModals = new Set();
    
    $(document).on('show.bs.modal', '.modal', function(e) {
        const modalId = $(e.target).attr('id');
        activeModals.add(modalId);
    });
    
    $(document).on('hidden.bs.modal', '.modal', function(e) {
        const modalId = $(e.target).attr('id');
        activeModals.delete(modalId);
        
        // Skip refresh for print modal - it handles its own refresh
        if (modalId === 'printConfirmModal') {
            console.log('Print modal closed - skipping universal refresh handler');
            return;
        }
        
        // Check if there are other active modals
        if (activeModals.size > 0) {
            console.log('Another modal is active - skipping refresh');
            return;
        }
        
        // Only refresh if we're on the task list page and no other modals are active
        if (window.location.pathname === '/tasks/' || window.location.pathname.startsWith('/tasks/list/')) {
            console.log('Modal closed - refreshing task list');
            setTimeout(function() {
                window.location.reload();
            }, 100);
        }
    });

    // Handle task creation modal show event
    $('#taskModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        currentParentId = button.data('parent-id') || null;
        
        // Update modal title
        if (currentParentId) {
            $('#taskModalLabel').html('<i class="fas fa-plus"></i> Create New Subtask');
        } else {
            $('#taskModalLabel').html('<i class="fas fa-plus"></i> Create New Task');
        }
        
        // Load form content
        loadTaskForm();
    });
    
    // Handle task delete modal show event
    $('#deleteModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        currentDeleteTaskId = button.data('task-id');
        
        // Load task details for confirmation
        loadDeleteConfirmation();
    });
    
    // Handle task edit modal show event
    $('#editModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        currentEditTaskId = button.data('task-id');
        
        if (!currentEditTaskId) {
            return;
        }
        
        // Load edit form with existing data
        loadEditForm();
    });
    
    // Handle create task only button click
    $('#saveTaskOnlyBtn').click(function() {
        submitTaskForm(false); // false = don't print
    });
    
    // Handle create and print button click
    $('#saveAndPrintBtn').click(function() {
        submitTaskForm(true); // true = print after creation
    });
    
    // Handle edit save button click
    $('#saveEditBtn').click(function() {
        submitEditForm();
    });
    
    // Handle delete confirmation
    $('#confirmDeleteBtn').click(function() {
        confirmDelete();
    });
    
    // Handle form submission on Enter key for create form (defaults to Create and Print)
    $(document).on('keypress', '#taskModalForm', function(e) {
        if (e.which == 13) {
            e.preventDefault();
            submitTaskForm(true); // Default to create and print on Enter
        }
    });
    
    // Handle form submission on Enter key for edit form
    $(document).on('keypress', '#editModalForm', function(e) {
        if (e.which == 13) {
            e.preventDefault();
            submitEditForm();
        }
    });
    
    // Handle edit button clicks to prevent navigation
    $(document).on('click', 'button[data-bs-target="#editModal"]', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const taskId = $(this).data('task-id');
        if (taskId) {
            currentEditTaskId = taskId;
            $('#editModal').modal('show');
        }
    });
});

function loadTaskForm() {
    $('#taskModalBody').html(`
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
    
    const url = taskCreateModalUrl; // This will be set in the template
    const params = currentParentId ? `?parent_id=${currentParentId}` : '';
    
    $.get(url + params)
        .done(function(response) {
            if (response.success) {
                $('#taskModalBody').html(response.form_html);
                // Focus on title field
                $('#id_title').focus();
                // Initialize periodic fields if available
                if (typeof window.initializeModalPeriodicFields === 'function') {
                    window.initializeModalPeriodicFields();
                }
            } else {
                showError(response.error);
            }
        })
        .fail(function(xhr, status, error) {
            console.log('Task form load failed:', xhr, status, error);
            if (xhr.status === 403 || xhr.status === 302) {
                showError('Please log in to create tasks.');
            } else {
                showError(`Failed to load form. Error: ${error} (Status: ${xhr.status})`);
            }
        });
}

function submitTaskForm(shouldPrint = false) {
    const form = $('#taskModalForm');
    const formData = new FormData(form[0]);
    
    // Clear previous errors
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').text('');
    
    // Determine which button was clicked and show appropriate loading state
    const activeBtn = shouldPrint ? $('#saveAndPrintBtn') : $('#saveTaskOnlyBtn');
    const inactiveBtn = shouldPrint ? $('#saveTaskOnlyBtn') : $('#saveAndPrintBtn');
    
    // Disable both buttons and show loading on the clicked one
    activeBtn.prop('disabled', true);
    inactiveBtn.prop('disabled', true);
    
    if (shouldPrint) {
        activeBtn.html('<i class="fas fa-spinner fa-spin"></i> Creating and Printing...');
    } else {
        activeBtn.html('<i class="fas fa-spinner fa-spin"></i> Creating...');
    }
    
    $.ajax({
        url: taskCreateModalUrl,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                if (shouldPrint) {
                    // Print the task directly
                    printTaskDirectly(response.task_id, response.message);
                } else {
                    // Close modal and show success message
                    $('#taskModal').modal('hide');
                    showMessage(response.message, 'success');
                    
                    // Refresh page to show new task
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                }
            } else {
                if (response.errors) {
                    // Display field errors
                    Object.keys(response.errors).forEach(field => {
                        const fieldElement = $(`#id_${field}`);
                        const errorElement = $(`#${field}-error`);
                        
                        fieldElement.addClass('is-invalid');
                        errorElement.text(response.errors[field].join(', '));
                    });
                } else {
                    showError(response.error);
                }
            }
        },
        error: function() {
            showError('Failed to create task. Please try again.');
        },
        complete: function() {
            // Reset button states
            $('#saveTaskOnlyBtn').prop('disabled', false).html('<i class="fas fa-save"></i> Create Task');
            $('#saveAndPrintBtn').prop('disabled', false).html('<i class="fas fa-print"></i> Create and Print');
        }
    });
}

function printTaskDirectly(taskId, creationMessage) {
    // Send print request immediately
    fetch(`/tasks/print/${taskId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        // Close the creation modal
        $('#taskModal').modal('hide');
        
        if (data.success) {
            // Show combined success message
            showMessage(`${creationMessage} Task printed successfully!`, 'success');
        } else {
            // Show creation success but print failure
            showMessage(`${creationMessage} However, printing failed: ${data.message}`, 'warning');
        }
    })
    .catch(error => {
        console.error('Print error:', error);
        // Close modal and show creation success but print error
        $('#taskModal').modal('hide');
        showMessage(`${creationMessage} However, an error occurred while printing.`, 'warning');
    })
    .finally(() => {
        // Refresh page to show the new task
        setTimeout(() => {
            window.location.reload();
        }, 2000); // Longer delay to let user read the message
    });
}

function showError(message) {
    $('#taskModalBody').html(`
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `);
}

function loadDeleteConfirmation() {
    $('#deleteModalBody').html(`
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
    
    $.get(`/tasks/delete/modal/${currentDeleteTaskId}/`)
        .done(function(response) {
            console.log('Delete modal response:', response); // Debug log
            
            if (response.success) {
                let warningHtml = '';
                let periodicWarningHtml = '';
                
                if (response.incomplete_subtasks) {
                    warningHtml = `
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong>Warning:</strong> This task has incomplete subtasks. 
                            Deleting this task will also delete all its subtasks.
                        </div>
                    `;
                } else if (response.subtask_count > 0) {
                    warningHtml = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            This task has ${response.subtask_count} completed subtask(s) that will also be deleted.
                        </div>
                    `;
                }
                
                // Add periodic warning if applicable
                console.log('Checking periodic subtask:', response.is_periodic_subtask, response.affected_instances); // Debug log
                
                if (response.is_periodic_subtask && response.affected_instances > 0) {
                    console.log('Adding periodic warning HTML'); // Debug log
                    periodicWarningHtml = `
                        <div class="alert alert-warning">
                            <i class="fas fa-repeat"></i>
                            <strong>Periodic Task Cleanup:</strong> This subtask is part of "${response.template_title}" periodic task.
                            <br><small><strong>This will remove the subtask from the template and ${response.affected_instances} existing instance(s).</strong></small>
                        </div>
                    `;
                } else if (response.is_periodic_subtask) {
                    console.log('Adding basic periodic warning HTML'); // Debug log
                    periodicWarningHtml = `
                        <div class="alert alert-info">
                            <i class="fas fa-repeat"></i>
                            <strong>Periodic Task:</strong> This subtask is part of a periodic task template.
                            <br><small>It will be removed from the template and all instances.</small>
                        </div>
                    `;
                }
                
                console.log('Final periodicWarningHtml:', periodicWarningHtml); // Debug log
                
                $('#deleteModalBody').html(`
                    <div class="mb-3">
                        <p>Are you sure you want to delete this task?</p>
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-title">${response.task_title}</h6>
                                ${response.task_description ? `<p class="card-text text-muted">${response.task_description}</p>` : ''}
                            </div>
                        </div>
                        ${periodicWarningHtml}
                        ${warningHtml}
                        <p class="text-danger"><strong>This action cannot be undone.</strong></p>
                    </div>
                `);
            } else {
                showDeleteError(response.error);
            }
        })
        .fail(function() {
            showDeleteError('Failed to load task details. Please try again.');
        });
}

function confirmDelete() {
    // Show loading state
    $('#confirmDeleteBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Deleting...');
    
    $.ajax({
        url: `/tasks/delete/modal/${currentDeleteTaskId}/`,
        type: 'DELETE',
        success: function(response) {
            if (response.success) {
                // Close modal
                $('#deleteModal').modal('hide');
                
                // Remove task from UI
                $(`#task-${currentDeleteTaskId}`).closest('.list-group-item').fadeOut(300, function() {
                    $(this).remove();
                });
                
                // Show success message
                showMessage(response.message, 'success');
            } else {
                showDeleteError(response.error);
            }
        },
        error: function() {
            showDeleteError('Failed to delete task. Please try again.');
        },
        complete: function() {
            // Reset button state
            $('#confirmDeleteBtn').prop('disabled', false).html('<i class="fas fa-trash"></i> Delete Task');
        }
    });
}

function showDeleteError(message) {
    $('#deleteModalBody').html(`
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `);
}

function loadEditForm() {
    $('#editModalBody').html(`
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
    
    const url = `/tasks/edit/modal/${currentEditTaskId}/`;
    
    $.get(url)
        .done(function(response) {
            if (response.success) {
                $('#editModalBody').html(response.form_html);
                $('#editModalLabel').html(`<i class="fas fa-edit"></i> Edit: ${response.task_title}`);
                // Focus on title field
                $('#id_title').focus();
                // Initialize periodic fields if available
                if (typeof window.initializeModalPeriodicFields === 'function') {
                    window.initializeModalPeriodicFields();
                }
            } else {
                showEditError(response.error);
            }
        })
        .fail(function(xhr, status, error) {
            console.log('Edit form load failed:', xhr, status, error);
            if (xhr.status === 403 || xhr.status === 302) {
                showEditError('Please log in to edit tasks.');
            } else {
                showEditError(`Failed to load edit form. Error: ${error} (Status: ${xhr.status})`);
            }
        });
}

function submitEditForm() {
    const form = $('#editModalForm');
    const formData = new FormData(form[0]);
    
    // Clear previous errors
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').text('');
    
    // Show loading state
    $('#saveEditBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Updating...');
    
    $.ajax({
        url: `/tasks/edit/modal/${currentEditTaskId}/`,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                // Close modal
                $('#editModal').modal('hide');
                
                // Show success message
                showMessage(response.message, 'success');
                
                // Universal modal handler will refresh the page when modal closes
            } else {
                if (response.errors) {
                    // Display field errors
                    Object.keys(response.errors).forEach(field => {
                        const fieldElement = $(`#id_${field}`);
                        const errorElement = $(`#${field}-error`);
                        
                        fieldElement.addClass('is-invalid');
                        errorElement.text(response.errors[field].join(', '));
                    });
                } else {
                    showEditError(response.error);
                }
            }
        },
        error: function() {
            showEditError('Failed to update task. Please try again.');
        },
        complete: function() {
            // Reset button state
            $('#saveEditBtn').prop('disabled', false).html('<i class="fas fa-save"></i> Update Task');
        }
    });
}

function showEditError(message) {
    $('#editModalBody').html(`
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `);
}

// Existing toggle function
function toggleTaskDone(taskId) {
    $.ajax({
        url: taskToggleDoneUrl.replace('0', taskId), // This will be set in the template
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                const taskElement = $('#task-' + taskId);
                if (response.done) {
                    taskElement.addClass('task-done');
                    taskElement.find('.task-checkbox').prop('checked', true);
                } else {
                    taskElement.removeClass('task-done');
                    taskElement.find('.task-checkbox').prop('checked', false);
                }
                
                // Show success message
                showMessage(response.message, 'success');
            }
        },
        error: function() {
            showMessage('Error updating task status', 'danger');
        }
    });
}

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