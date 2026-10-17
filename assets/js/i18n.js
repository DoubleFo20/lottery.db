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

  const FALLBACK_TH = {
    app_title: "LOTTERY.DB — แพลตฟอร์มวิเคราะห์ยุทธศาสตร์และสถิติสลากขั้นสูง",
    app_subtitle: "ระบบปัญญาประดิษฐ์วิเคราะห์สถิติและการกระจายความเสี่ยงระดับองค์กร",
    meta: {
      version: "v1.2 Analytical Pro",
      status_connected: "เชื่อมต่อระบบปกติ (473 งวด)",
      status_syncing: "กำลังอัปเดตข้อมูล",
      dataset_draws: "งวดประวัติศาสตร์ในฐานข้อมูล",
      latest_draw: "ผลงวดล่าสุด",
      cache_age: "อายุข้อมูลแคช"
    },
    nav: {
      strategy: "📊 ยุทธศาสตร์หลัก",
      manager: "⚙️ ศูนย์ควบคุมผู้จัดการ",
      performance: "📈 ผลการประเมินย้อนหลัง",
      showcase_3d: "🌐 แบบจำลอง 3 มิติ",
      wallet: "📱 พอร์ตความเสี่ยง",
      lang_toggle: "TH / EN",
      menu: "เมนู"
    },
    manager: {
      title: "ศูนย์บัญชาการระบบ AI (Manager Control Center)",
      subtitle: "ตรวจวัดสถานะแบบจำลอง บริหารความเสี่ยง และปรับแต่งค่าน้ำหนัก",
      miss_advisory_title: "ระบบแจ้งเตือนช่วงเว้นว่างรางวัล (Dry Spell Advisory)",
      run_pipeline: "⚡ รันไพป์ไลน์โมเดล (Run Pipeline)",
      fetch_result: "📡 ดึงผลรางวัลล่าสุด (Fetch Result)",
      refresh: "⟳ รีเฟรชข้อมูล (Refresh)"
    },
    performance: {
      title: "รายงานประสิทธิภาพและการประเมินย้อนหลัง",
      subtitle: "การประเมินทางสถิติแบบ Out-of-Sample โดยปราศจาก Look-Ahead Data Leakage",
      evaluated_draws: "จำนวนงวดที่ประเมินผล",
      avg_positional_hits: "ค่าเฉลี่ยตำแหน่งที่ตรง / 6",
      avg_digit_hits: "ค่าเฉลี่ยตัวเลขที่ตรง / 6",
      exact_jackpot: "รางวัลที่ 1 ตรงเป๊ะ"
    },
    predictions: {
      top_candidates: "ตัวเลขเด่นที่ผ่านเกณฑ์คัดกรอง",
      full_spectrum: "ยุทธศาสตร์กระจายความเสี่ยงรอบด้าน (Hedging Portfolio)"
    },
    analytics: {
      title: "สถิติและสัญญาณแนวโน้มเชิงลึก",
      heatmap_title: "แผนที่ความร้อนรายตำแหน่ง (Positional Digit Heatmap)",
      historical_draws: "ประวัติการออกรางวัล",
      walk_forward_evaluation: "การประเมินแบบไม่มองข้อมูลอนาคต (Walk-Forward Out-of-Sample)"
    }
  };

  const FALLBACK_EN = {
    app_title: "LOTTERY.DB — Premium Analytical Strategy & Statistical Platform",
    app_subtitle: "Enterprise-Grade Statistical Analysis & Quantitative Risk Hedging System",
    meta: {
      version: "v1.2 Analytical Pro",
      status_connected: "Online (473 Draws)",
      status_syncing: "Synchronizing Data",
      dataset_draws: "Historical Draws in Dataset",
      latest_draw: "Latest Official Draw",
      cache_age: "Pipeline Cache Age"
    },
    nav: {
      strategy: "📊 Strategy",
      manager: "⚙️ Manager",
      performance: "📈 Performance",
      showcase_3d: "🌐 3D Showcase",
      wallet: "📱 Wallet",
      lang_toggle: "TH / EN",
      menu: "Menu"
    },
    manager: {
      title: "AI Manager Control Center",
      subtitle: "Model Health Monitoring, Staking Allocation & Dynamic Weight Calibration",
      miss_advisory_title: "Consecutive Draw Miss Advisory System",
      run_pipeline: "⚡ Run Pipeline",
      fetch_result: "📡 Fetch Result",
      refresh: "⟳ Refresh Data"
    },
    performance: {
      title: "Model Performance & Out-of-Sample Evaluation",
      subtitle: "Rigorous Statistical Backtesting Free of Look-Ahead Data Leakage",
      evaluated_draws: "Evaluated Draws",
      avg_positional_hits: "Mean Positional Hits / 6",
      avg_digit_hits: "Mean Digit Hits / 6",
      exact_jackpot: "Exact Jackpot Hits"
    },
    predictions: {
      top_candidates: "Top Filtered Candidates",
      full_spectrum: "Full-Spectrum Hedging Portfolio"
    },
    analytics: {
      title: "Deep Trend Signals & Statistical Analytics",
      heatmap_title: "Positional Digit Heatmap",
      historical_draws: "Historical Draws",
      walk_forward_evaluation: "Walk-Forward Out-of-Sample Evaluation"
    }
  };

  let dictionaries = {
    th: Object.assign({}, FALLBACK_TH),
    en: Object.assign({}, FALLBACK_EN)
  };

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
          dictionaries.th = Object.assign({}, dictionaries.th, resTh);
          dictionaries.en = Object.assign({}, dictionaries.en, resEn);
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
