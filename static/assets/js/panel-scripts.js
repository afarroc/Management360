/**
 * PANEL MANAGEMENT SCRIPTS
 * Reusable JavaScript functions for Projects, Tasks & Events panels
 * Compatible with NiceAdmin theme and Bootstrap 5
 */

(function() {
    'use strict';

    // Panel Management Object
    window.PanelManager = {

        // Default Configuration
        defaultConfig: {
            searchInputId: 'searchInput',
            selectedCountId: 'selectedCount',
            selectAllId: 'selectAll',
            checkboxName: 'selected_items',
            tableSelector: '.datatable tbody tr',
            tabSelector: '.nav-tabs .nav-link'
        },

        // Current configuration
        config: {},

        // Initialize panel functionality
        init: function(options) {
            // Merge options with default config
            this.config = Object.assign({}, this.defaultConfig, options || {});

            this.bindEvents();
            this.initializeTooltips();
            this.updateSelectedCount();
        },

        // Bind all event listeners
        bindEvents: function() {
            const self = this;

            // Search functionality
            const searchInput = document.getElementById(this.config.searchInputId);
            if (searchInput) {
                searchInput.addEventListener('keyup', function() {
                    self.searchItems(this.value);
                });
            }

            // Select all functionality
            const selectAllCheckbox = document.getElementById(this.config.selectAllId);
            if (selectAllCheckbox) {
                selectAllCheckbox.addEventListener('change', function() {
                    self.toggleSelectAll(this.checked);
                });
            }

            // Individual checkbox changes
            const checkboxes = document.querySelectorAll(`input[name="${this.config.checkboxName}"]`);
            checkboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    self.toggleRowSelection(this);
                    self.updateSelectedCount();
                });
            });

            // Tab changes
            const tabButtons = document.querySelectorAll(this.config.tabSelector);
            tabButtons.forEach(button => {
                button.addEventListener('shown.bs.tab', function() {
                    self.updateSelectedCount();
                });
            });
        },

        // Initialize Bootstrap tooltips
        initializeTooltips: function() {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        },

        // Search functionality
        searchItems: function(query) {
            const filter = query.toUpperCase();
            const rows = document.querySelectorAll(this.config.tableSelector);

            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                let found = false;

                // Skip checkbox column for search
                for (let i = 1; i < cells.length - 1; i++) {
                    const cell = cells[i];
                    if (cell) {
                        const textValue = cell.textContent || cell.innerText;
                        if (textValue.toUpperCase().indexOf(filter) > -1) {
                            found = true;
                            break;
                        }
                    }
                }

                row.style.display = found ? '' : 'none';
            });
        },

        // Clear search
        clearSearch: function() {
            const searchInput = document.getElementById(this.config.searchInputId);
            if (searchInput) {
                searchInput.value = '';
                this.searchItems('');
            }
        },

        // Toggle select all
        toggleSelectAll: function(checked) {
            const checkboxes = document.querySelectorAll(`input[name="${this.config.checkboxName}"]`);
            checkboxes.forEach(checkbox => {
                checkbox.checked = checked;
                this.toggleRowSelection(checkbox);
            });
            this.updateSelectedCount();
        },

        // Toggle row selection visual feedback
        toggleRowSelection: function(checkbox) {
            const row = checkbox.closest('tr');
            if (row) {
                if (checkbox.checked) {
                    row.classList.add('table-active');
                } else {
                    row.classList.remove('table-active');
                }
            }
        },

        // Update selected count
        updateSelectedCount: function() {
            const checkboxes = document.querySelectorAll(`input[name="${this.config.checkboxName}"]:checked`);
            const count = checkboxes.length;
            const selectedCountElement = document.getElementById(this.config.selectedCountId);

            if (selectedCountElement) {
                if (count === 0) {
                    selectedCountElement.textContent = '0 selected';
                    selectedCountElement.className = 'badge bg-secondary';
                } else {
                    selectedCountElement.textContent = `${count} selected`;
                    selectedCountElement.className = 'badge bg-primary';
                }
            }
        },

        // Bulk actions
        bulkAction: function(action, confirmMessage) {
            const selectedItems = Array.from(document.querySelectorAll(`input[name="${this.config.checkboxName}"]:checked`))
                .map(checkbox => checkbox.value);

            if (selectedItems.length === 0) {
                this.showAlert('Please select at least one item.', 'warning');
                return;
            }

            if (confirmMessage && !confirm(confirmMessage.replace('{count}', selectedItems.length))) {
                return;
            }

            const form = document.createElement('form');
            form.method = 'POST';
            form.action = this.getBulkActionUrl(action);

            const csrfToken = document.createElement('input');
            csrfToken.type = 'hidden';
            csrfToken.name = 'csrfmiddlewaretoken';
            csrfToken.value = this.getCsrfToken();
            form.appendChild(csrfToken);

            const actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            actionInput.value = action;
            form.appendChild(actionInput);

            selectedItems.forEach(id => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'selected_items';
                input.value = id;
                form.appendChild(input);
            });

            document.body.appendChild(form);
            form.submit();
        },

        // Export functionality
        exportItems: function(exportUrl) {
            const selectedItems = Array.from(document.querySelectorAll(`input[name="${this.config.checkboxName}"]:checked`))
                .map(checkbox => checkbox.value);

            if (selectedItems.length === 0) {
                // Export all items
                window.location.href = exportUrl;
            } else {
                // Export selected items
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = exportUrl;

                const csrfToken = document.createElement('input');
                csrfToken.type = 'hidden';
                csrfToken.name = 'csrfmiddlewaretoken';
                csrfToken.value = this.getCsrfToken();
                form.appendChild(csrfToken);

                selectedItems.forEach(id => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'selected_items';
                    input.value = id;
                    form.appendChild(input);
                });

                document.body.appendChild(form);
                form.submit();
                document.body.removeChild(form);
            }
        },

        // Filter by status
        filterByStatus: function(statusId) {
            const rows = document.querySelectorAll(this.config.tableSelector);

            rows.forEach(row => {
                if (statusId === 'all' || row.dataset.statusId === statusId) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        },

        // Toggle view (table/cards)
        toggleView: function(viewType) {
            const tableView = document.getElementById('all-items');
            const cardViews = document.querySelectorAll('.tab-pane[id$="-items"]:not(#all-items)');

            if (viewType === 'cards') {
                if (tableView) tableView.style.display = 'none';
                cardViews.forEach(view => view.style.display = 'block');
            } else {
                if (tableView) tableView.style.display = 'block';
                cardViews.forEach(view => view.style.display = 'none');
            }
        },

        // Refresh data
        refreshData: function() {
            const refreshBtn = event.target.closest('button');
            if (!refreshBtn) return;

            const originalHtml = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spinning"></i> Refreshing...';
            refreshBtn.disabled = true;

            // Simulate refresh delay
            setTimeout(() => {
                location.reload();
            }, 1000);
        },

        // Utility functions
        getCsrfToken: function() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        },

        getBulkActionUrl: function(action) {
            // This should be overridden by specific panel implementations
            return window.location.href;
        },

        showAlert: function(message, type = 'info') {
            // Simple alert - can be enhanced with toast notifications
            alert(message);
        },

        // Confirm dialog
        confirmAction: function(message) {
            return confirm(message);
        }
    };

})();