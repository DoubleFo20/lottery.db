/**
 * assets/live_countdown.js
 * 
 * Unified Real-Time Lottery Auto-Fetch & Dual Calendar Engine for Lottery.db
 * 
 * Features:
 * 1. Thai Official Lottery Calendar Engine (Auto-calculates next draw with holiday shifts: Dec 30, Jan 17, May 2).
 * 2. Smart Adaptive Poller (Normal: 5 mins, Draw Window 14:30-16:30 ICT: 30 secs).
 * 3. Live Broadcasting Mode (Replaces frozen countdown with pulsating live status badge during draw time).
 * 4. Real-time Ingestion & Auto-Rollover (Updates latest results in DOM and resets countdown immediately).
 * 5. Timestamp Cache-Busting (?_t=Date.now()) & Network Retry resilience.
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.LotteryLiveEngine = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {

  // ── 1. Thai Lottery Official Calendar Rules ──────────────────────
  const THAI_MONTH_NAMES = [
    '', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
  ];

  /**
   * Check if a given date is an official Thai Government lottery draw day.
   * Accounts for holiday shifts:
   * - Dec 30 (Official shift for New Year instead of Jan 1)
   * - Jan 17 (Official shift for Teacher's Day instead of Jan 16)
   * - May 2  (Official shift for Labour Day instead of May 1)
   */
  function isOfficialDrawDay(dateObj) {
    const day = dateObj.getDate();
    const month = dateObj.getMonth() + 1; // 1-12

    // Exception dates
    if (day === 30 && month === 12) return true;
    if (day === 17 && month === 1) return true;
    if (day === 2 && month === 5) return true;

    // Normal dates
    if (day === 1) {
      if (month === 1 || month === 5) return false; // Jan 1 & May 1 skipped
      return true;
    }
    if (day === 16) {
      if (month === 1) return false; // Jan 16 skipped
      return true;
    }

    return false;
  }

  /**
   * Calculate next upcoming official lottery draw date at 14:30 ICT (UTC+7).
   * @param {Date} [referenceDate] - Current date/time, default now
   * @returns {{ targetDate: Date, isoString: string, thaiFormatted: string, drawDayStr: string }}
   */
  function getNextDrawDate(referenceDate) {
    const now = referenceDate ? new Date(referenceDate) : new Date();
    
    // Look up to 45 days into future
    for (let dayOffset = 0; dayOffset <= 45; dayOffset++) {
      const candidate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + dayOffset, 14, 30, 0, 0);
      
      if (isOfficialDrawDay(candidate)) {
        // If candidate is today, check if 14:30 ICT has passed
        if (dayOffset === 0 && now.getTime() >= candidate.getTime() + (2 * 60 * 60 * 1000)) {
          // If today's draw window (14:30 - 16:30) is completely over, roll over to next draw
          continue;
        }

        const y = candidate.getFullYear();
        const m = candidate.getMonth() + 1;
        const d = candidate.getDate();
        const yTH = y + 543;
        const pad = (n) => String(n).padStart(2, '0');
        const drawDayStr = `${y}-${pad(m)}-${pad(d)}`;
        const isoString = `${drawDayStr}T14:30:00+07:00`;
        const thaiFormatted = `${d} ${THAI_MONTH_NAMES[m]} ${yTH}`;

        return {
          targetDate: candidate,
          isoString: isoString,
          thaiFormatted: thaiFormatted,
          drawDayStr: drawDayStr
        };
      }
    }

    // Fallback default
    return {
      targetDate: new Date(now.getTime() + 15 * 86400000),
      isoString: new Date(now.getTime() + 15 * 86400000).toISOString(),
      thaiFormatted: 'งวดถัดไป',
      drawDayStr: '2026-10-01'
    };
  }

  /**
   * Check if current time is within the active draw broadcasting window (14:30 - 16:30 ICT on draw days).
   */
  function isDrawWindow(referenceDate) {
    const now = referenceDate ? new Date(referenceDate) : new Date();
    if (!isOfficialDrawDay(now)) return false;

    const hours = now.getHours();
    const minutes = now.getMinutes();
    const timeInMins = hours * 60 + minutes;

    // 14:30 (870 mins) to 16:30 (990 mins)
    return timeInMins >= 870 && timeInMins <= 990;
  }

  // ── 2. Smart Adaptive Poller Engine ───────────────────────────────
  class LiveEngine {
    constructor(options = {}) {
      this.options = Object.assign({
        normalIntervalMs: 5 * 60 * 1000,   // 5 mins
        liveIntervalMs: 30 * 1000,         // 30 secs during draw window
        endpoints: [
          './database/predictions/pipeline_cache.json',
          './pipeline_cache.json',
          '../database/predictions/pipeline_cache.json',
          './dashboard/hopper_3d_data.json',
          './database/predictions/hopper_3d_data.json'
        ],
        onNewResult: null,
        onTick: null,
        onStatusChange: null
      }, options);

      this.currentDrawDate = null;
      this.currentFirstPrize = null;
      this.currentLast2 = null;
      this.timerInterval = null;
      this.pollInterval = null;
      this.currentTarget = getNextDrawDate();
      this.isPolling = false;
      this.lastFetchedHash = null;
    }

    init() {
      console.log('⚡ [LiveEngine] Initializing Real-time Lottery Engine...');
      this.updateTarget();
      this.startCountdownLoop();
      this.startAdaptivePolling();
      this.checkLatestResults(true); // Initial fetch with cache-busting
      return this;
    }

    updateTarget(explicitIso) {
      if (explicitIso) {
        try {
          const parsed = new Date(explicitIso);
          if (!isNaN(parsed.getTime()) && parsed.getTime() > Date.now()) {
            this.currentTarget = {
              targetDate: parsed,
              isoString: explicitIso,
              thaiFormatted: `${parsed.getDate()} ${THAI_MONTH_NAMES[parsed.getMonth()+1]} ${parsed.getFullYear()+543}`,
              drawDayStr: explicitIso.split('T')[0]
            };
            return;
          }
        } catch (e) {}
      }
      this.currentTarget = getNextDrawDate();
    }

    startCountdownLoop() {
      if (this.timerInterval) clearInterval(this.timerInterval);

      const tick = () => {
        const now = new Date();
        const target = this.currentTarget.targetDate;
        const diffMs = target.getTime() - now.getTime();
        const inWindow = isDrawWindow(now);

        // Notify status
        if (typeof this.options.onStatusChange === 'function') {
          this.options.onStatusChange({
            isDrawWindow: inWindow,
            target: this.currentTarget,
            now: now
          });
        }

        // Calculate Days, Hours, Minutes, Seconds
        let d = 0, h = 0, m = 0, s = 0;
        let isExpired = false;

        if (diffMs > 0) {
          d = Math.floor(diffMs / (1000 * 60 * 60 * 24));
          h = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          m = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
          s = Math.floor((diffMs % (1000 * 60)) / 1000);
        } else {
          isExpired = true;
          // If expired and not in draw window, auto-roll over immediately
          if (!inWindow && diffMs < -1000) {
            console.log('⚡ [LiveEngine] Target expired outside draw window. Auto-rolling over to next draw...');
            this.updateTarget();
          }
        }

        // Update DOM if IDs exist
        const pad = (n) => String(n).padStart(2, '0');
        const elDays = document.getElementById('cd-days');
        const elHours = document.getElementById('cd-hours');
        const elMins = document.getElementById('cd-mins');
        const elSecs = document.getElementById('cd-secs');

        if (elDays) elDays.textContent = pad(d);
        if (elHours) elHours.textContent = pad(h);
        if (elMins) elMins.textContent = pad(m);
        if (elSecs) elSecs.textContent = pad(s);

        // Update Target Date Display
        const elTarget = document.getElementById('target-date-display');
        if (elTarget && !inWindow) {
          elTarget.innerHTML = `${this.currentTarget.thaiFormatted} <span style="font-size:1.1rem;color:var(--text-muted);">(14:30 น.)</span> <span class="target-date-tag">งวดเป้าหมายหลัก</span>`;
        }

        // Update 3D Hero Countdown pill if exists
        const elHeroCountdown = document.getElementById('hero-countdown');
        if (elHeroCountdown) {
          if (inWindow) {
            elHeroCountdown.innerHTML = `<span style="color:#ef4444;animation:pulse 1.5s infinite">🔴 กำลังถ่ายทอดสด</span> (${pad(h)}:${pad(m)}:${pad(s)})`;
          } else {
            elHeroCountdown.innerHTML = `⏳ งวดถัดไป: ${this.currentTarget.thaiFormatted} (${d}วัน ${pad(h)}:${pad(m)}:${pad(s)})`;
          }
        }

        if (typeof this.options.onTick === 'function') {
          this.options.onTick({
            days: d, hours: h, minutes: m, seconds: s,
            diffMs: diffMs,
            isExpired: isExpired,
            isDrawWindow: inWindow,
            target: this.currentTarget
          });
        }
      };

      tick();
      this.timerInterval = setInterval(tick, 1000);
    }

    startAdaptivePolling() {
      if (this.pollInterval) clearInterval(this.pollInterval);

      const checkSchedule = () => {
        const inWindow = isDrawWindow();
        const interval = inWindow ? this.options.liveIntervalMs : this.options.normalIntervalMs;

        // Schedule next poll
        this.pollInterval = setTimeout(async () => {
          await this.checkLatestResults();
          checkSchedule(); // recurse with potentially updated interval
        }, interval);
      };

      checkSchedule();
    }

    async checkLatestResults(isInitial = false) {
      if (this.isPolling) return;
      this.isPolling = true;

      // Timestamp cache-busting
      const cacheBust = `_t=${Date.now()}`;

      for (const endpoint of this.options.endpoints) {
        try {
          const url = `${endpoint}?${cacheBust}`;
          const res = await fetch(url, { cache: 'no-store' });
          if (!res.ok) continue;

          const data = await res.json();
          this.processIngestedData(data, isInitial);
          this.isPolling = false;
          return data;
        } catch (err) {
          // try next endpoint fallback
        }
      }

      this.isPolling = false;
      return null;
    }

    processIngestedData(data, isInitial) {
      if (!data) return;

      const meta = data.meta || {};
      const dataset = meta.dataset || {};
      const latestDraw = meta.latest_draw || dataset.latest || dataset.latest_draw;
      const latestNum = dataset.latest_number || meta.latest_number || (data.candidates && data.candidates[0]?.number);
      const targetIso = data.target?.iso_target || meta.next_draw?.iso_target;

      if (targetIso) {
        this.updateTarget(targetIso);
      }

      // Check if this is a newly published draw result
      if (!isInitial && latestDraw && this.currentDrawDate && latestDraw !== this.currentDrawDate) {
        console.log(`🎉 [LiveEngine] NEW LOTTERY DRAW DETECTED: ${latestDraw} -> Number: ${latestNum}!`);
        
        // Trigger Toast and Callbacks
        if (typeof window.showToast === 'function') {
          window.showToast(`🎉 ผลรางวัลงวดใหม่ (${latestDraw}) เข้าสู่ระบบแล้ว!`);
        }

        // Auto roll over to next draw!
        this.updateTarget();

        if (typeof this.options.onNewResult === 'function') {
          this.options.onNewResult({
            latestDraw: latestDraw,
            latestNum: latestNum,
            fullData: data
          });
        }

        // Dispatch window event for any decoupled listeners
        window.dispatchEvent(new CustomEvent('lottery:new-results-detected', {
          detail: { latestDraw, latestNum, data }
        }));
      }

      this.currentDrawDate = latestDraw;
      this.currentFirstPrize = latestNum;
    }

    destroy() {
      if (this.timerInterval) clearInterval(this.timerInterval);
      if (this.pollInterval) clearTimeout(this.pollInterval);
    }
  }

  // Factory function
  return {
    isOfficialDrawDay,
    getNextDrawDate,
    isDrawWindow,
    createEngine: (options) => new LiveEngine(options)
  };
}));
