/**
 * assets/js/nav-component.js — Unified Responsive Navigation Component
 * Provides:
 * - Common accessible header & mobile drawer
 * - Active page link highlighting
 * - Language toggle integration with LotteryI18n
 * - Keyboard & ARIA support
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

    const base = getBasePath();
    const active = getActivePage();

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

            <button type="button" class="lang-toggle-btn" data-action="toggle-lang" aria-label="Toggle Language">
              🌐 <span class="lang-label">TH / EN</span>
            </button>

            <button type="button" class="mobile-menu-btn" id="btn-mobile-menu" aria-label="Open navigation menu" aria-expanded="false">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
      </header>

      <div class="mobile-drawer-overlay" id="mobile-overlay" aria-hidden="true"></div>
      <aside class="mobile-drawer" id="mobile-drawer" role="dialog" aria-modal="true" aria-label="Mobile Navigation">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <div style="font-weight:700; font-size:1.1rem; color:var(--text-primary);">LOTTERY.DB</div>
          <button type="button" id="btn-close-drawer" style="background:none; border:none; color:var(--text-secondary); cursor:pointer; font-size:1.3rem;" aria-label="Close menu">✕</button>
        </div>
        <nav style="display:flex; flex-direction:column; gap:0.5rem;">
          <a href="${base}strategy.html" class="nav-link ${active === 'strategy' ? 'active' : ''}" data-i18n="nav.strategy">📊 Strategy</a>
          <a href="${base}manager.html" class="nav-link ${active === 'manager' ? 'active' : ''}" data-i18n="nav.manager">⚙️ Manager</a>
          <a href="${base}performance.html" class="nav-link ${active === 'performance' ? 'active' : ''}" data-i18n="nav.performance">📈 Performance</a>
          <a href="${base}3d.html" class="nav-link ${active === '3d' ? 'active' : ''}" data-i18n="nav.showcase_3d">🌐 3D Showcase</a>
          <a href="${base}mobile-wallet.html" class="nav-link ${active === 'wallet' ? 'active' : ''}" data-i18n="nav.wallet">📱 Wallet</a>
        </nav>
        <div style="margin-top:auto; padding-top:1.5rem; border-top:1px solid var(--border-subtle); display:flex; flex-direction:column; gap:0.75rem;">
          <button type="button" class="btn-analytical btn-secondary lang-toggle-btn" data-action="toggle-lang" style="width:100%;">
            🌐 Switch Language (TH / EN)
          </button>
        </div>
      </aside>
    `;

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

    function openDrawer() {
      if (drawer && overlay) {
        drawer.classList.add('open');
        overlay.classList.add('show');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
      }
    }

    function closeDrawer() {
      if (drawer && overlay) {
        drawer.classList.remove('open');
        overlay.classList.remove('show');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      }
    }

    if (menuBtn) menuBtn.addEventListener('click', openDrawer);
    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (overlay) overlay.addEventListener('click', closeDrawer);

    window.addEventListener('keydown', e => {
      if (e.key === 'Escape' && drawer && drawer.classList.contains('open')) {
        closeDrawer();
      }
    });

    document.querySelectorAll('[data-action="toggle-lang"]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (window.LotteryI18n) {
          window.LotteryI18n.toggleLang();
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderHeader);
  } else {
    renderHeader();
  }
})();
