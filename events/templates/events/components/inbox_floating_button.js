/**
 * =======================================================
 * INBOX GTD - SISTEMA DE COMPONENTE FLOTANTE GLOBAL
 * =======================================================
 * Este archivo maneja toda la funcionalidad del componente
 * flotante del inbox GTD que está disponible en toda la
 * aplicación, enfatizando que el inbox es la semilla
 * del ecosistema de gestión de proyectos.
 */

class InboxGTDManager {
    constructor() {
        this.isPanelOpen = false;
        this.pendingCount = 0;
        this.todayCount = 0;
        this.processedCount = 0;
        this.notificationQueue = [];
        this.isLoading = false;

        this.init();
    }

    /**
     * Inicializar el componente
     */
    init() {
        this.bindEvents();
        this.loadInitialData();
        this.startPeriodicUpdates();
        this.showWelcomeMessage();
    }

    /**
     * Vincular eventos del DOM
     */
    bindEvents() {
        // Botón principal flotante
        const floatingButton = document.getElementById('inboxFloatingButton');
        const floatingPanel = document.getElementById('inboxFloatingPanel');
        const panelClose = document.getElementById('inboxPanelClose');

        if (floatingButton) {
            floatingButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePanel();
            });
        }

        if (panelClose) {
            panelClose.addEventListener('click', () => {
                this.closePanel();
            });
        }

        // Cerrar panel al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (this.isPanelOpen && floatingPanel &&
                !floatingPanel.contains(e.target) &&
                !floatingButton.contains(e.target)) {
                this.closePanel();
            }
        });

        // Formulario de captura rápida
        const quickForm = document.getElementById('inboxQuickCaptureForm');
        if (quickForm) {
            quickForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleQuickCapture();
            });
        }

        // Inputs del formulario
        const quickTitle = document.getElementById('inboxQuickTitle');
        const quickDescription = document.getElementById('inboxQuickDescription');

        if (quickTitle) {
            quickTitle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleQuickCapture();
                }
            });
        }

        // Manejo de teclas globales
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + I para abrir inbox
            if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
                e.preventDefault();
                this.togglePanel();
            }

            // Escape para cerrar panel
            if (e.key === 'Escape' && this.isPanelOpen) {
                this.closePanel();
            }
        });
    }

    /**
     * Alternar panel flotante
     */
    togglePanel() {
        const panel = document.getElementById('inboxFloatingPanel');
        if (!panel) return;

        if (this.isPanelOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }

    /**
     * Abrir panel flotante
     */
    openPanel() {
        const panel = document.getElementById('inboxFloatingPanel');
        const button = document.getElementById('inboxFloatingButton');

        if (!panel || !button) return;

        this.isPanelOpen = true;
        panel.classList.add('show');
        button.classList.add('active');

        // Actualizar datos al abrir
        this.refreshData();

        // Analytics
        this.trackEvent('inbox_panel_opened');
    }

    /**
     * Cerrar panel flotante
     */
    closePanel() {
        const panel = document.getElementById('inboxFloatingPanel');
        const button = document.getElementById('inboxFloatingButton');

        if (!panel || !button) return;

        this.isPanelOpen = false;
        panel.classList.remove('show');
        button.classList.remove('active');
    }

    /**
     * Manejar captura rápida
     */
    async handleQuickCapture() {
        const titleInput = document.getElementById('inboxQuickTitle');
        const descriptionInput = document.getElementById('inboxQuickDescription');

        if (!titleInput || !titleInput.value.trim()) {
            this.showNotification('Por favor ingresa un título para tu idea', 'warning');
            return;
        }

        const title = titleInput.value.trim();
        const description = descriptionInput ? descriptionInput.value.trim() : '';

        this.setLoading(true);

        try {
            const formData = new FormData();
            formData.append('title', title);
            formData.append('description', description);
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch('/events/inbox/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Limpiar formulario
                titleInput.value = '';
                if (descriptionInput) descriptionInput.value = '';

                // Actualizar datos
                await this.refreshData();

                // Mostrar notificación de éxito
                this.showNotification(`¡Idea capturada! "${title}" agregada al inbox`, 'success');

                // Analytics
                this.trackEvent('quick_capture_success', { title_length: title.length });

                // Cerrar panel después de capturar
                setTimeout(() => {
                    this.closePanel();
                }, 1500);

            } else {
                throw new Error(data.error || 'Error desconocido');
            }

        } catch (error) {
            console.error('Error en captura rápida:', error);
            this.showNotification('Error al capturar idea. Inténtalo de nuevo.', 'error');
            this.trackEvent('quick_capture_error', { error: error.message });
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Cargar datos iniciales
     */
    async loadInitialData() {
        await this.refreshData();
    }

    /**
     * Actualizar datos del inbox
     */
    async refreshData() {
        try {
            const response = await fetch('/events/inbox/api/stats/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.updateStats(data.stats);
                this.updateBadge(data.stats.pending);
            }

        } catch (error) {
            console.error('Error al cargar datos del inbox:', error);
        }
    }

    /**
     * Actualizar estadísticas en la UI
     */
    updateStats(stats) {
        // Actualizar contadores
        const pendingElement = document.getElementById('inboxPendingCount');
        const todayElement = document.getElementById('inboxTodayCount');
        const processedElement = document.getElementById('inboxProcessedCount');

        if (pendingElement) pendingElement.textContent = stats.pending || 0;
        if (todayElement) todayElement.textContent = stats.today || 0;
        if (processedElement) processedElement.textContent = stats.processed || 0;

        // Guardar valores
        this.pendingCount = stats.pending || 0;
        this.todayCount = stats.today || 0;
        this.processedCount = stats.processed || 0;
    }

    /**
     * Actualizar badge de notificación
     */
    updateBadge(count) {
        const badge = document.getElementById('inboxBadge');
        const button = document.getElementById('inboxFloatingButton');

        if (!badge || !button) return;

        badge.textContent = count;

        if (count > 0) {
            badge.classList.add('pulse');
            button.classList.add('new-items');
        } else {
            badge.classList.remove('pulse');
            button.classList.remove('new-items');
        }
    }

    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info') {
        const toast = document.getElementById('inboxToast');
        const toastBody = document.getElementById('inboxToastBody');

        if (!toast || !toastBody) return;

        toastBody.textContent = message;

        // Configurar clase según tipo
        toast.className = `toast align-items-center text-white bg-${type} border-0`;

        // Mostrar toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Agregar a cola de notificaciones
        this.notificationQueue.push({ message, type, timestamp: Date.now() });
    }

    /**
     * Mostrar mensaje de bienvenida
     */
    showWelcomeMessage() {
        // Solo mostrar si no hay items pendientes
        if (this.pendingCount === 0) {
            setTimeout(() => {
                this.showNotification(
                    '¡Bienvenido al Inbox GTD! Captura tus ideas rápidamente con Ctrl+I',
                    'info'
                );
            }, 2000);
        }
    }

    /**
     * Configurar estado de carga
     */
    setLoading(loading) {
        this.isLoading = loading;
        const panel = document.getElementById('inboxFloatingPanel');

        if (panel) {
            if (loading) {
                panel.classList.add('inbox-loading');
            } else {
                panel.classList.remove('inbox-loading');
            }
        }
    }

    /**
     * Obtener token CSRF
     */
    getCSRFToken() {
        const csrfForm = document.getElementById('csrf-form');
        const token = csrfForm ? csrfForm.querySelector('[name=csrfmiddlewaretoken]') : null;
        return token ? token.value : '';
    }

    /**
     * Iniciar actualizaciones periódicas
     */
    startPeriodicUpdates() {
        // Actualizar cada 30 segundos
        setInterval(() => {
            this.refreshData();
        }, 30000);

        // Verificar cambios más frecuentemente si el panel está abierto
        setInterval(() => {
            if (this.isPanelOpen) {
                this.refreshData();
            }
        }, 10000);
    }

    /**
     * Trackear evento para analytics
     */
    trackEvent(eventName, data = {}) {
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                event_category: 'inbox_gtd',
                event_label: eventName,
                ...data
            });
        }

        console.log('Inbox GTD Event:', eventName, data);
    }

    /**
     * API pública para uso externo
     */
    getStats() {
        return {
            pending: this.pendingCount,
            today: this.todayCount,
            processed: this.processedCount
        };
    }

    openInboxPanel() {
        this.openPanel();
    }

    closeInboxPanel() {
        this.closePanel();
    }

    refreshInboxData() {
        this.refreshData();
    }
}

// =======================================================
// INICIALIZACIÓN GLOBAL
// =======================================================

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si el usuario está autenticado
    if (typeof userAuthenticated !== 'undefined' && userAuthenticated) {
        window.inboxGTD = new InboxGTDManager();

        // Hacer disponible globalmente
        window.InboxGTD = InboxGTDManager;
    }
});

// =======================================================
// INTEGRACIÓN CON EL SISTEMA EXISTENTE
// =======================================================

// Integrar con el sistema de notificaciones existente
document.addEventListener('DOMContentLoaded', function() {
    // Escuchar eventos personalizados del inbox
    document.addEventListener('inbox:item_added', function(e) {
        if (window.inboxGTD) {
            window.inboxGTD.refreshData();
            window.inboxGTD.showNotification(
                `Nueva idea capturada: "${e.detail.title}"`,
                'success'
            );
        }
    });

    document.addEventListener('inbox:item_processed', function(e) {
        if (window.inboxGTD) {
            window.inboxGTD.refreshData();
            window.inboxGTD.showNotification(
                `Item procesado: "${e.detail.title}"`,
                'info'
            );
        }
    });
});

// =======================================================
// SHORTCUTS GLOBALES
// =======================================================

// Ctrl/Cmd + I para abrir inbox desde cualquier lugar
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'i' && window.inboxGTD) {
        e.preventDefault();
        window.inboxGTD.togglePanel();
    }
});

// =======================================================
// MÉTODOS DE UTILIDAD GLOBALES
// =======================================================

// Función global para captura rápida desde cualquier lugar
window.quickInboxCapture = function(title, description = '') {
    if (window.inboxGTD) {
        // Abrir panel
        window.inboxGTD.openPanel();

        // Llenar formulario
        setTimeout(() => {
            const titleInput = document.getElementById('inboxQuickTitle');
            const descInput = document.getElementById('inboxQuickDescription');

            if (titleInput) titleInput.value = title;
            if (descInput) descInput.value = description;

            // Enfocar en el campo de título
            if (titleInput) titleInput.focus();
        }, 300);
    }
};

// Función global para mostrar notificación del inbox
window.showInboxNotification = function(message, type = 'info') {
    if (window.inboxGTD) {
        window.inboxGTD.showNotification(message, type);
    }
};