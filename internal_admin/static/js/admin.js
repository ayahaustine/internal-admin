/**
 * Internal Admin JavaScript
 * Provides interactive functionality for the admin interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('a[href*="/delete/"]');
    deleteButtons.forEach(function(button) {
        if (!button.closest('.confirm-delete-form')) {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to delete this item?')) {
                    e.preventDefault();
                }
            });
        }
    });

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Search input enhancements
    var searchInputs = document.querySelectorAll('input[type="search"]');
    searchInputs.forEach(function(input) {
        // Add clear button functionality
        var clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'btn btn-outline-secondary btn-sm position-absolute';
        clearButton.style.right = '5px';
        clearButton.style.top = '50%';
        clearButton.style.transform = 'translateY(-50%)';
        clearButton.innerHTML = '<i class="bi bi-x"></i>';
        
        // Only add clear button if input has value
        if (input.value) {
            input.parentNode.style.position = 'relative';
            input.parentNode.appendChild(clearButton);
            input.style.paddingRight = '40px';
            
            clearButton.addEventListener('click', function() {
                input.value = '';
                clearButton.remove();
                input.focus();
            });
        }
    });

    // Table row click handlers
    var clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(function(row) {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(e) {
            if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
                window.location.href = row.getAttribute('data-href');
            }
        });
    });

    // Loading states for forms
    var submitButtons = document.querySelectorAll('form button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.form.addEventListener('submit', function() {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Saving...';
        });
    });

    // Auto-resize textareas
    var textareas = document.querySelectorAll('textarea');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });

    // Sidebar navigation state
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Filter dropdown enhancements
    var filterDropdowns = document.querySelectorAll('.dropdown-menu a[href*="?"]');
    filterDropdowns.forEach(function(link) {
        link.addEventListener('click', function(e) {
            // Add loading state
            var dropdown = link.closest('.dropdown');
            var toggle = dropdown.querySelector('.dropdown-toggle');
            toggle.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Filtering...';
        });
    });
});

/**
 * Utility functions
 */
window.AdminUtils = {
    // Show confirmation dialog
    confirm: function(message, onConfirm, onCancel) {
        if (confirm(message)) {
            if (onConfirm) onConfirm();
        } else {
            if (onCancel) onCancel();
        }
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        var toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        var container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }

        container.appendChild(toast);
        var bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    },

    // Format timestamp
    formatDate: function(dateString, format = 'short') {
        var date = new Date(dateString);
        var options = {};
        
        if (format === 'short') {
            options = { year: 'numeric', month: 'short', day: 'numeric' };
        } else if (format === 'long') {
            options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        }
        
        return date.toLocaleDateString(undefined, options);
    },

    // Copy text to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(function() {
            AdminUtils.showToast('Copied to clipboard', 'success');
        }).catch(function() {
            AdminUtils.showToast('Failed to copy', 'danger');
        });
    }
};