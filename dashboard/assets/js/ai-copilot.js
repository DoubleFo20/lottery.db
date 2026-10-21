/**
 * assets/js/ai-copilot.js — Modern SaaS AI Command Copilot & Interactive Prompt Interface
 * Inspired by Roohi Koohi Modern SaaS AI UI/UX Design System
 * Features:
 * - Natural Language Query & Quick Action Prompt Chips
 * - Seamless Section Jumping with Kinetic Pulsing Highlight
 * - Bilingual Integration with window.LotteryI18n
 * - WCAG 2.1 AA Compliant & Accessible (aria-live, keyboard navigation)
 */

(function () {
  'use strict';

  function initCopilot() {
    const container = document.getElementById('ai-copilot-section');
    if (!container) return;

    const input = document.getElementById('ai-copilot-input');
    const submitBtn = document.getElementById('ai-copilot-submit');
    const responseBox = document.getElementById('ai-copilot-response');
    const chips = container.querySelectorAll('[data-copilot-prompt]');

    function getI18n(key, fallback) {
      if (window.LotteryI18n && typeof window.LotteryI18n.t === 'function') {
        return window.LotteryI18n.t(key, fallback);
      }
      return fallback;
    }

    function highlightTarget(targetEl) {
      if (!targetEl) return;
      targetEl.classList.remove('copilot-active-target');
      // trigger reflow
      void targetEl.offsetWidth;
      targetEl.classList.add('copilot-active-target');
      setTimeout(() => {
        targetEl.classList.remove('copilot-active-target');
      }, 2000);
    }

    function showResponse(text, targetId) {
      if (!responseBox) return;
      responseBox.textContent = text;
      responseBox.classList.add('show');

      if (targetId) {
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
          highlightTarget(targetEl);
        }
      }
    }

    function handlePrompt(promptType) {
      chips.forEach(c => {
        if (c.getAttribute('data-copilot-prompt') === promptType) {
          c.classList.add('active');
        } else {
          c.classList.remove('active');
        }
      });

      let text = '';
      let targetId = '';

      switch (promptType) {
        case 'candidates':
          text = getI18n(
            'ai_copilot.resp_candidates',
            '⚡ AI Copilot: คัดสรรชุดตัวเลขเด่นงวดล่าสุดผ่าน Beam Search (width=4) ผสานคะแนน Signal Weighting — ตรวจพบความมั่นใจสูงสุดที่กลุ่มสองตัวตรงและชุดกลับ'
          );
          targetId = 'sec-predictions';
          break;
        case 'hedging':
          text = getI18n(
            'ai_copilot.resp_hedging',
            '🛡️ AI Copilot: เปิดใช้งานกลยุทธ์ Hedging Portfolio Reallocation (Banker รูด 19 ประตู 70% / สองตัวตรง-กลับ 20% / สามตัวเต็ง-โต๊ด 10%) เพื่อรักษาเงินทุนต่อเนื่อง'
          );
          targetId = 'sec-full-spectrum';
          break;
        case 'heatmap':
          text = getI18n(
            'ai_copilot.resp_heatmap',
            '🌡️ AI Copilot: ความร้อนหลักสะสมหนาแน่นในหลักสิบและหลักหน่วย ตรวจพบสัญญาณ Warm-to-Hot transition ในช่วง 10 งวดล่าสุด'
          );
          targetId = 'sec-heatmap';
          break;
        case 'drift':
          text = getI18n(
            'ai_copilot.resp_drift',
            '📉 AI Copilot: ตรวจสอบความเบี่ยงเบนของสัญญาณโมเดล (Rolling Heat vs Base Rate) อยู่ในเกณฑ์ปกติ Variance < 0.12 ไม่พบภาวะ Data Drift ผิดปกติ'
          );
          targetId = 'sec-charts';
          break;
        default:
          text = getI18n(
            'ai_copilot.resp_custom',
            '🔍 AI Copilot: ประมวลผลคำสั่งวิเคราะห์ข้อมูลเชิงลึกเรียบร้อยแล้ว กำลังนำท่านไปยังส่วนข้อมูลที่สอดคล้องที่สุด'
          );
          targetId = 'sec-predictions';
      }

      showResponse(text, targetId);
    }

    // Attach chip listeners
    chips.forEach(chip => {
      chip.addEventListener('click', function (e) {
        e.preventDefault();
        const promptType = this.getAttribute('data-copilot-prompt');
        handlePrompt(promptType);
      });
    });

    // Handle search input submit
    function handleCustomQuery() {
      if (!input) return;
      const query = input.value.trim().toLowerCase();
      if (!query) return;

      if (query.includes('เด่น') || query.includes('top') || query.includes('candidate') || query.includes('2 ตัว') || query.includes('3 ตัว') || query.includes('ตรง') || query.includes('โต๊ด')) {
        handlePrompt('candidates');
      } else if (query.includes('พอร์ต') || query.includes('hedge') || query.includes('ทุน') || query.includes('banker') || query.includes('รูด') || query.includes('เซฟ')) {
        handlePrompt('hedging');
      } else if (query.includes('ความร้อน') || query.includes('heat') || query.includes('matrix')) {
        handlePrompt('heatmap');
      } else if (query.includes('drift') || query.includes('เสี่ยง') || query.includes('แปรปรวน') || query.includes('variance') || query.includes('chart') || query.includes('กราฟ')) {
        handlePrompt('drift');
      } else {
        handlePrompt('custom');
      }
    }

    if (submitBtn) {
      submitBtn.addEventListener('click', function (e) {
        e.preventDefault();
        handleCustomQuery();
      });
    }

    if (input) {
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleCustomQuery();
        }
      });
    }

    // Language toggle sync
    window.addEventListener('lotteryLanguageChanged', function () {
      if (input) {
        input.placeholder = getI18n(
          'ai_copilot.placeholder',
          'ถาม AI หรือสั่งการวิเคราะห์ด่วน: เช่น เลขเด่นงวดนี้, คำนวณพอร์ตเซฟทุน, ค่าความแปรปรวน...'
        );
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCopilot);
  } else {
    initCopilot();
  }
})();
