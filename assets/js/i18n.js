/**
 * assets/js/i18n.js — Enterprise Bilingual Localization Engine (TH / EN)
 * Features:
 * - Zero external dependencies.
 * - Local fallback dictionary for instant paint & offline/file-protocol resilience.
 * - Deep key resolution (e.g., 'nav.strategy', 'results.first_prize').
 * - Preserves user choice in localStorage ('lottery_lang').
 * - Dispatches 'lotteryLanguageChanged' custom event for dynamic components.
 */

(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.LotteryI18n = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const STORAGE_KEY = 'lottery_lang';
  let currentLang = 'th';
  let dictionaries = { th: {}, en: {} };

  function getNestedValue(obj, path) {
    if (!obj || !path) return undefined;
    const parts = path.split('.');
    let curr = obj;
    for (const p of parts) {
      if (curr == null || typeof curr !== 'object') return undefined;
      curr = curr[p];
    }
    return curr;
  }

  function t(key, fallback) {
    const dict = dictionaries[currentLang] || {};
    const val = getNestedValue(dict, key);
    if (val !== undefined && val !== null) return String(val);

    // Fallback to English if currently Thai, or vice versa
    const otherLang = currentLang === 'th' ? 'en' : 'th';
    const alt = getNestedValue(dictionaries[otherLang] || {}, key);
    if (alt !== undefined && alt !== null) return String(alt);

    return fallback !== undefined ? fallback : key;
  }

  function applyToDOM(container = document) {
    if (!container || !container.querySelectorAll) return;

    // 1. Text elements: data-i18n="key"
    const textEls = container.querySelectorAll('[data-i18n]');
    textEls.forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (!key) return;
      const text = t(key);
      if (text && text !== key) {
        el.textContent = text;
      }
    });

    // 2. Attribute elements: data-i18n-attr="title:key,placeholder:key"
    const attrEls = container.querySelectorAll('[data-i18n-attr]');
    attrEls.forEach(el => {
      const spec = el.getAttribute('data-i18n-attr');
      if (!spec) return;
      spec.split(',').forEach(pair => {
        const [attr, key] = pair.split(':').map(s => s.trim());
        if (attr && key) {
          const val = t(key);
          if (val && val !== key) {
            el.setAttribute(attr, val);
          }
        }
      });
    });

    // 3. Update all language toggle buttons
    const toggles = container.querySelectorAll('.lang-toggle-btn, [data-action="toggle-lang"]');
    toggles.forEach(btn => {
      const label = currentLang === 'th' ? 'EN' : 'TH';
      const fullLabel = currentLang === 'th' ? 'Switch to English' : 'เปลี่ยนเป็นภาษาไทย';
      btn.setAttribute('aria-label', fullLabel);
      btn.setAttribute('title', fullLabel);
      const span = btn.querySelector('.lang-label') || btn;
      if (span === btn) {
        btn.textContent = label;
      } else {
        span.textContent = label;
      }
    });

    document.documentElement.lang = currentLang;
  }

  function setLang(lang) {
    if (lang !== 'th' && lang !== 'en') lang = 'th';
    currentLang = lang;
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (_) {}

    applyToDOM(document);

    try {
      window.dispatchEvent(new CustomEvent('lotteryLanguageChanged', { detail: { lang } }));
    } catch (_) {}
  }

  function toggleLang() {
    setLang(currentLang === 'th' ? 'en' : 'th');
  }

  function getLang() {
    return currentLang;
  }

  async function loadDictionaries() {
    // Attempt to load from JSON files if available
    const bases = ['./i18n/', '../i18n/', '/Lottery/i18n/'];
    let loaded = false;

    for (const base of bases) {
      try {
        const [resTh, resEn] = await Promise.all([
          fetch(base + 'th.json').then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(base + 'en.json').then(r => r.ok ? r.json() : null).catch(() => null)
        ]);
        if (resTh && resEn) {
          dictionaries.th = resTh;
          dictionaries.en = resEn;
          loaded = true;
          break;
        }
      } catch (_) {}
    }

    return loaded;
  }

  function init() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'en' || stored === 'th') {
        currentLang = stored;
      } else {
        currentLang = (navigator.language && navigator.language.startsWith('en')) ? 'en' : 'th';
      }
    } catch (_) {
      currentLang = 'th';
    }

    loadDictionaries().then(() => {
      applyToDOM(document);
    });

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => applyToDOM(document));
    } else {
      applyToDOM(document);
    }
  }

  // Auto-initialize in browser
  if (typeof window !== 'undefined') {
    init();
  }

  return {
    t,
    setLang,
    toggleLang,
    getLang,
    applyToDOM,
    init,
    dictionaries
  };
});
