/**
 * assets/js/nav-component.js — Unified Responsive Navigation Component
 * Provides:
 * - Common accessible header & mobile drawer (Single Source of Truth)
 * - Active page link highlighting
 * - Contextual mobile quick-actions and section jumps
 * - Keyboard controls (Escape to close, Tab trapping) & ARIA dialog support
 * - Language toggle integration with LotteryI18n
 */

(function () {
  'use strict';

  function getBasePath() {
    const p = window.location.pathname;
    return p.includes('/dashboard/') ? '../' : './';
  }

  function getActivePage() {
    const p = window.location.pathname.toLowerCase();
    if (p.includes('manager')) return 'manager';
    if (p.includes('performance')) return 'performance';
    if (p.includes('3d')) return '3d';
    if (p.includes('wallet')) return 'wallet';
    return 'strategy';
  }

  function renderHeader() {
    const headerContainer = document.getElementById('unified-app-header');
    if (!headerContainer) return;

    if (!headerContainer.querySelector('.app-header')) {
      const base = getBasePath();
      const active = getActivePage();

      let contextualSectionHtml = '';
      if (active === 'strategy') {
        contextualSectionHtml = `
          <div style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid var(--border-subtle);">
            <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; color:var(--text-muted); margin-bottom:0.4rem; letter-spacing:0.05em;" data-i18n="nav.strategy">Section Jumper</div>
            <div style="display:flex; flex-direction:column; gap:0.35rem;">
              <button type="button" class="btn-analytical btn-secondary drawer-link-action" data-jump="sec-predictions" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">🎯 <span data-i18n="predictions.top_candidates">Top Candidates</span></button>
              <button type="button" class="btn-analytical btn-secondary drawer-link-action" data-jump="sec-full-spectrum" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">👑 <span data-i18n="predictions.full_spectrum">Full Spectrum</span></button>
              <button type="button" class="btn-analytical btn-secondary drawer-link-action" data-jump="sec-heatmap" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">🌡 <span data-i18n="analytics.heatmap_title">Heatmap</span></button>
              <button type="button" class="btn-analytical btn-secondary drawer-link-action" data-jump="sec-charts" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">📊 <span data-i18n="analytics.title">Statistics</span></button>
              <button type="button" class="btn-analytical btn-secondary drawer-link-action" data-jump="sec-history" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">📜 <span data-i18n="analytics.historical_draws">Archive</span></button>
            </div>
          </div>
        `;
      } else if (active === 'manager') {
        contextualSectionHtml = `
          <div style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid var(--border-subtle);">
            <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; color:var(--text-muted); margin-bottom:0.4rem; letter-spacing:0.05em;" data-i18n="manager.title">Manager Quick Actions</div>
            <div style="display:flex; flex-direction:column; gap:0.35rem;">
              <button type="button" class="btn-analytical btn-primary drawer-link-action" data-action="run-pipeline" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">⚡ Run Pipeline</button>
              <button type="button" class="btn-analytical btn-secondary drawer-link-action" data-action="fetch-result" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">📡 Fetch Result</button>
              <button type="button" class="btn-analytical btn-secondary drawer-link-action" data-action="refresh-manager" style="text-align:left; font-size:0.8rem; padding:0.45rem 0.75rem;">⟳ Refresh Data</button>
            </div>
          </div>
        `;
      }

      headerContainer.innerHTML = `
        <header class="app-header" role="banner">
          <div class="header-inner">
            <a href="${base}strategy.html" class="brand-group" aria-label="LOTTERY.DB Home">
              <div class="brand-badge" aria-hidden="true">⚡</div>
              <div class="brand-meta">
                <div class="brand-title">
                  LOTTERY.DB
                  <span class="brand-version-pill" data-i18n="meta.version">v1.2 Analytical Pro</span>
                </div>
                <div class="brand-subtitle" data-i18n="app_subtitle">Enterprise Statistical Analysis & Quantitative Risk Hedging</div>
              </div>
            </a>

            <nav class="nav-links" role="navigation" aria-label="Main Navigation">
              <a href="${base}strategy.html" class="nav-link ${active === 'strategy' ? 'active' : ''}" data-i18n="nav.strategy">📊 Strategy</a>
              <a href="${base}manager.html" class="nav-link ${active === 'manager' ? 'active' : ''}" data-i18n="nav.manager">⚙️ Manager</a>
              <a href="${base}performance.html" class="nav-link ${active === 'performance' ? 'active' : ''}" data-i18n="nav.performance">📈 Performance</a>
              <a href="${base}3d.html" class="nav-link ${active === '3d' ? 'active' : ''}" data-i18n="nav.showcase_3d">🌐 3D Showcase</a>
              <a href="${base}mobile-wallet.html" class="nav-link ${active === 'wallet' ? 'active' : ''}" data-i18n="nav.wallet">📱 Wallet</a>
            </nav>

            <div class="header-actions">
              <div class="status-indicator" title="473 draws indexed">
                <span class="status-dot" aria-hidden="true"></span>
                <span data-i18n="meta.status_connected">Online (473 Draws)</span>
              </div>

              <button type="button" class="lang-toggle-btn" data-action="toggle-lang" aria-label="Toggle Language" title="Toggle Language">
                🌐 <span class="lang-label">TH / EN</span>
              </button>

              <button type="button" class="mobile-menu-btn" id="btn-mobile-menu" aria-label="Open navigation menu" aria-expanded="false" aria-controls="mobile-drawer">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <line x1="3" y1="12" x2="21" y2="12"></line>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
        </header>

        <div class="mobile-drawer-overlay" id="mobile-overlay" aria-hidden="true"></div>
        <aside class="mobile-drawer" id="mobile-drawer" role="dialog" aria-modal="true" aria-label="Mobile Navigation" tabindex="-1">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; padding-bottom:0.75rem; border-bottom:1px solid var(--border-subtle);">
            <div style="font-weight:700; font-size:1.05rem; color:var(--text-primary); display:flex; align-items:center; gap:0.4rem;">
              <span>⚡</span> LOTTERY.DB
            </div>
            <button type="button" id="btn-close-drawer" style="background:none; border:none; color:var(--text-secondary); cursor:pointer; font-size:1.3rem; padding:4px 8px; border-radius:4px;" aria-label="Close navigation menu">✕</button>
          </div>

          <nav style="display:flex; flex-direction:column; gap:0.45rem;" aria-label="Mobile Main Navigation">
            <a href="${base}strategy.html" class="nav-link ${active === 'strategy' ? 'active' : ''}" data-i18n="nav.strategy">📊 Strategy</a>
            <a href="${base}manager.html" class="nav-link ${active === 'manager' ? 'active' : ''}" data-i18n="nav.manager">⚙️ Manager</a>
            <a href="${base}performance.html" class="nav-link ${active === 'performance' ? 'active' : ''}" data-i18n="nav.performance">📈 Performance</a>
            <a href="${base}3d.html" class="nav-link ${active === '3d' ? 'active' : ''}" data-i18n="nav.showcase_3d">🌐 3D Showcase</a>
            <a href="${base}mobile-wallet.html" class="nav-link ${active === 'wallet' ? 'active' : ''}" data-i18n="nav.wallet">📱 Wallet</a>
          </nav>

          ${contextualSectionHtml}

          <div style="margin-top:auto; padding-top:1.25rem; border-top:1px solid var(--border-subtle); display:flex; flex-direction:column; gap:0.75rem;">
            <button type="button" class="btn-analytical btn-secondary lang-toggle-btn" data-action="toggle-lang" style="width:100%; justify-content:center;">
              🌐 <span data-i18n="nav.lang_toggle">Switch Language (TH / EN)</span>
            </button>
          </div>
        </aside>
      `;
    }

    bindEvents();
    if (window.LotteryI18n) {
      window.LotteryI18n.applyToDOM(headerContainer);
    }
  }

  function bindEvents() {
    const menuBtn = document.getElementById('btn-mobile-menu');
    const closeBtn = document.getElementById('btn-close-drawer');
    const drawer = document.getElementById('mobile-drawer');
    const overlay = document.getElementById('mobile-overlay');

    if (!drawer || !overlay) return;

    let previousActiveElement = null;

    function openDrawer() {
      previousActiveElement = document.activeElement;
      drawer.classList.add('open');
      overlay.classList.add('show');
      overlay.setAttribute('aria-hidden', 'false');
      if (menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
      
      // Focus first interactive element inside drawer
      const focusable = drawer.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusable.length > 0) {
        focusable[0].focus();
      }
    }

    function closeDrawer() {
      drawer.classList.remove('open');
      overlay.classList.remove('show');
      overlay.setAttribute('aria-hidden', 'true');
      if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      if (previousActiveElement && typeof previousActiveElement.focus === 'function') {
        previousActiveElement.focus();
      }
    }

    // Expose close/open on window for any legacy or helper caller
    window.LotteryNav = {
      openDrawer,
      closeDrawer
    };

    if (menuBtn) menuBtn.addEventListener('click', openDrawer);
    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (overlay) overlay.addEventListener('click', closeDrawer);

    // Keyboard support: Escape closes, Tab traps
    window.addEventListener('keydown', e => {
      if (!drawer.classList.contains('open')) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        closeDrawer();
        return;
      }

      if (e.key === 'Tab') {
        const focusable = Array.from(drawer.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'));
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    });

    // Close on navigation click inside drawer
    drawer.querySelectorAll('a.nav-link').forEach(link => {
      link.addEventListener('click', () => closeDrawer());
    });

    // Contextual button actions inside drawer
    drawer.querySelectorAll('.drawer-link-action').forEach(btn => {
      btn.addEventListener('click', () => {
        const jumpId = btn.getAttribute('data-jump');
        const act = btn.getAttribute('data-action');
        closeDrawer();

        if (jumpId && typeof window.scrollToSection === 'function') {
          window.scrollToSection(jumpId);
        } else if (act === 'run-pipeline' && typeof window.triggerAction === 'function') {
          window.triggerAction('pipeline');
        } else if (act === 'fetch-result' && typeof window.triggerAction === 'function') {
          window.triggerAction('fetch');
        } else if (act === 'refresh-manager' && typeof window.loadAll === 'function') {
          window.loadAll();
        }
      });
    });

    // Language toggle buttons
    document.querySelectorAll('[data-action="toggle-lang"]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (window.LotteryI18n) {
          window.LotteryI18n.toggleLang();
        }
      });
    });

    // Re-apply translations if language changes
    window.addEventListener('lotteryLanguageChanged', () => {
      const container = document.getElementById('unified-app-header');
      if (container && window.LotteryI18n) {
        window.LotteryI18n.applyToDOM(container);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderHeader);
  } else {
    renderHeader();
  }
})();

