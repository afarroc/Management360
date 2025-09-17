/**
 * Optimized Dashboard JavaScript
 * Externalized for better performance and maintainability
 */

(function() {
  'use strict';

  // Performance monitoring
  const perfData = {
    startTime: performance.now(),
    domReady: false,
    fullyLoaded: false,
    components: {}
  };

  // DOM ready event
  document.addEventListener('DOMContentLoaded', function() {
    perfData.domReady = true;
    console.log('DOM ready in:', performance.now() - perfData.startTime, 'ms');

    // Initialize all dashboard components
    initDashboard();
  });

  // Window load event
  window.addEventListener('load', function() {
    perfData.fullyLoaded = true;
    console.log('Page fully loaded in:', performance.now() - perfData.startTime, 'ms');

    // Mark lazy images as loaded
    document.querySelectorAll('img.lazy').forEach(img => {
      img.classList.add('loaded');
    });
  });

  /**
   * Initialize all dashboard components
   */
  function initDashboard() {
    const startTime = performance.now();

    // Initialize components
    initTabs();
    initLazyLoading();
    initAnimatedCounters();
    initTooltips();
    initAlerts();

    perfData.components.dashboard = performance.now() - startTime;
    console.log('Dashboard initialized in:', perfData.components.dashboard, 'ms');
  }

  /**
   * Initialize tab functionality with lazy loading
   */
  function initTabs() {
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');

    tabEls.forEach(tabEl => {
      tabEl.addEventListener('shown.bs.tab', function (event) {
        const targetId = event.target.getAttribute('data-bs-target');

        // Lazy load tab content if needed
        loadTabContent(targetId);

        // Track tab switches for analytics
        if (window.gtag) {
          gtag('event', 'tab_switch', {
            tab_name: targetId.replace('#', '')
          });
        }
      });
    });
  }

  /**
   * Load tab content dynamically (can be extended for AJAX loading)
   */
  function loadTabContent(tabId) {
    console.log('Loading content for tab:', tabId);

    // Add loading state
    const tabContent = document.querySelector(tabId);
    if (tabContent) {
      tabContent.classList.add('loading');

      // Simulate content loading (replace with actual AJAX if needed)
      setTimeout(() => {
        tabContent.classList.remove('loading');
      }, 100);
    }
  }

  /**
   * Initialize lazy loading for images and content
   */
  function initLazyLoading() {
    // Image lazy loading
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.classList.add('loaded');
          }
          observer.unobserve(img);
        }
      });
    });

    // Observe all lazy images
    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });

    // Content lazy loading for below-the-fold sections
    const contentObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target;
          element.classList.add('visible');
          observer.unobserve(element);
        }
      });
    });

    // Observe sections that should be lazy loaded
    document.querySelectorAll('.lazy-section').forEach(section => {
      contentObserver.observe(section);
    });
  }

  /**
   * Initialize animated counters with optimized performance
   */
  function initAnimatedCounters() {
    const counters = document.querySelectorAll('.counter');
    if (counters.length === 0) return;

    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.5,
      rootMargin: '0px 0px -50px 0px'
    });

    counters.forEach(counter => counterObserver.observe(counter));
  }

  /**
   * Animate counter with smooth easing
   */
  function animateCounter(counter) {
    const target = parseInt(counter.getAttribute('data-target')) || 0;
    const duration = 1000; // 1 second
    const start = performance.now();
    const startValue = 0;

    // Use requestAnimationFrame for smooth animation
    function update(currentTime) {
      const elapsed = currentTime - start;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const currentValue = Math.floor(startValue + (target - startValue) * easeOutQuart);

      counter.textContent = currentValue.toLocaleString();

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        counter.textContent = target.toLocaleString();
      }
    }

    requestAnimationFrame(update);
  }

  /**
   * Initialize Bootstrap tooltips
   */
  function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  /**
   * Initialize alert auto-dismiss
   */
  function initAlerts() {
    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
    alerts.forEach(alert => {
      const delay = parseInt(alert.dataset.autoDismiss) || 5000;
      setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }, delay);
    });
  }

  /**
   * Utility function for debouncing
   */
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Utility function for throttling
   */
  function throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    }
  }

  // Expose performance data for debugging
  window.dashboardPerf = perfData;

  // Expose utility functions for global use
  window.DashboardUtils = {
    debounce,
    throttle,
    animateCounter
  };

})();