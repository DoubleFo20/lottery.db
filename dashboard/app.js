/**
 * dashboard/app.js — Lottery Analytics Dashboard Application Controller
 * Professional, resilient, XSS-safe client for the Lottery Prediction Pipeline.
 */

const CANDIDATE_API_PATHS = [
    '../api/predict.php',
    'api/predict.php',
    '/Lottery/api/predict.php',
    '../database/predictions/pipeline_cache.json',
    'database/predictions/pipeline_cache.json',
    '/Lottery/database/predictions/pipeline_cache.json'
];

function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', () => {
    fetchInsights();
    setInterval(fetchInsights, 60 * 1000);
});

async function fetchInsights() {
    let data = null;
    let lastError = null;

    for (const path of CANDIDATE_API_PATHS) {
        try {
            const url = path + (path.includes('?') ? '&' : '?') + '_ts=' + Date.now();
            const response = await fetch(url);
            if (response.ok) {
                const parsed = await response.json();
                if (parsed && (parsed.status === 'ok' || parsed.candidates)) {
                    data = parsed;
                    break;
                }
            }
        } catch (err) {
            lastError = err;
        }
    }

    if (!data) {
        showError('Unable to load prediction cache. Ensure pipeline runner has executed.');
        if (lastError) console.error('Fetch error:', lastError);
        return;
    }

    renderDashboard(data);
}

function renderDashboard(data) {
    const loader = document.getElementById('loader');
    if (loader) loader.style.display = 'none';

    // Update Meta — support both run_pipeline.py and predict.php cache structures
    const totalDraws = data.meta?.dataset?.total_draws ?? data.meta?.total_draws ?? '?';
    const latestDraw = data.meta?.dataset?.latest ?? data.meta?.latest_draw ?? '?';
    const metaStr = `Analysis on ${escapeHtml(totalDraws)} draws | Latest: ${escapeHtml(latestDraw)}`;
    const metaEl = document.getElementById('meta-info');
    if (metaEl && metaEl.textContent.includes('Loading')) {
        metaEl.textContent = metaStr;
    }

    // Cache Banner
    if (data.cache || data.meta?.processing_at) {
        const banner = document.getElementById('status-banner');
        const rawTime = data.cache?.cached_at || data.meta?.processing_at;
        const cacheTime = new Date(rawTime);
        const timeStr = isNaN(cacheTime.getTime()) ? 'Just now' : cacheTime.toLocaleTimeString('th-TH');

        function updateBannerTimer() {
            if (!banner) return;
            const diff = Math.floor((Date.now() - cacheTime.getTime()) / 1000);
            if (diff < 0) return;
            banner.textContent = `Pipeline Cache (${timeStr}) | Updated: ${new Date().toLocaleTimeString('th-TH')}`;
        }
        if (banner) {
            banner.style.display = 'block';
            updateBannerTimer();
            if (window._bannerTimer) clearInterval(window._bannerTimer);
            window._bannerTimer = setInterval(updateBannerTimer, 1000);
        }
    }

    const grid = document.getElementById('main-grid');
    if (!grid) return;
    grid.innerHTML = '';

    // 1. Top Predictions Panel
    const predPanel = createPanel('🏆 Top AI Predictions');
    let predHtml = '';
    const candidates = Array.isArray(data.candidates) ? data.candidates : [];
    candidates.forEach((cand, idx) => {
        const num = escapeHtml(cand.number);
        const conf = typeof cand.confidence === 'number' ? cand.confidence : 0;
        predHtml += `
            <div class="prediction-item">
                <div class="prediction-header">
                    <span class="pred-number">${num}</span>
                    <span class="pred-rank">#${idx + 1}</span>
                </div>
                <div class="confidence-label">
                    <span>Relative Score Rank (Uncalibrated)</span>
                    <span>${conf.toFixed(1)}%</span>
                </div>
                <div class="confidence-wrapper">
                    <div class="confidence-bar" style="width: ${Math.min(100, Math.max(0, conf))}%"></div>
                </div>
            </div>
        `;
    });
    predPanel.innerHTML += predHtml;
    grid.appendChild(predPanel);

    // 2. Trend Indicators Panel
    const trendPanel = createPanel('📈 Real-time Trend Scanner');
    let trendHtml = '';
    const analytics = data.analytics || {};

    // Streaks
    const activeStreaks = analytics.active_streaks || [];
    if (activeStreaks.length > 0) {
        trendHtml += `<div class="trend-section"><h4>Active Streaks</h4>`;
        activeStreaks.forEach(s => {
            trendHtml += `<span class="trend-badge trend-streak">🔥 ${escapeHtml(s.position)}: ${escapeHtml(s.digit)} (${escapeHtml(s.length)} draws)</span>`;
        });
        trendHtml += `</div>`;
    }

    // Spikes (Up)
    const spikesUp = analytics.frequency_spikes || [];
    if (spikesUp.length > 0) {
        trendHtml += `<div class="trend-section"><h4>Frequency Spikes (Surging)</h4>`;
        spikesUp.forEach(s => {
            trendHtml += `<span class="trend-badge trend-spike">🔺 ${escapeHtml(s.position)} [${escapeHtml(s.digit)}] x${escapeHtml(s.ratio)}</span>`;
        });
        trendHtml += `</div>`;
    }

    // Drops (Down)
    const spikesDown = analytics.frequency_drops || [];
    if (spikesDown.length > 0) {
        trendHtml += `<div class="trend-section"><h4>Frequency Drops (Cooling)</h4>`;
        spikesDown.forEach(s => {
            trendHtml += `<span class="trend-badge trend-drop">🔻 ${escapeHtml(s.position)} [${escapeHtml(s.digit)}] x${escapeHtml(s.ratio)}</span>`;
        });
        trendHtml += `</div>`;
    }

    trendPanel.innerHTML += trendHtml || '<p style="color:var(--text-muted)">No significant trends detected.</p>';
    grid.appendChild(trendPanel);

    // 3. Explainable AI Panel (Why number #1?)
    const expData = Array.isArray(data.explanation) ? data.explanation[0] : data.explanation;
    if (expData && candidates.length > 0 && Array.isArray(expData.positions)) {
        const topNum = escapeHtml(candidates[0].number);
        const xaiPanel = createPanel(`🧠 Why ${topNum}? (XAI Attribution)`);
        let xaiHtml = `<p style="margin-bottom:1rem;color:var(--text-muted)">Statistical signal breakdown for top candidate.</p>`;

        const factors = expData.overall_factor_pct || {};
        const probPct = factors.probability_pct ?? 0;
        const heatPct = factors.heatmap_pct ?? 0;
        const pattPct = factors.pattern_pct ?? 0;

        let overview = `<div style="display:flex;gap:10px;margin-bottom:1rem;flex-wrap:wrap;">
            <span class="trend-badge" style="background:rgba(59,130,246,0.2);color:#60a5fa">📊 Prob: ${escapeHtml(probPct)}%</span>
            <span class="trend-badge" style="background:rgba(239,68,68,0.2);color:#f87171">🌡 Heat: ${escapeHtml(heatPct)}%</span>
            <span class="trend-badge" style="background:rgba(167,139,250,0.2);color:#c084fc">🔎 Patt: ${escapeHtml(pattPct)}%</span>
        </div>`;

        xaiHtml += overview;

        expData.positions.forEach(pos => {
            xaiHtml += `
                <div style="margin-bottom:1rem;background:rgba(255,255,255,0.03);padding:10px;border-radius:8px;">
                    <div style="font-weight:bold;margin-bottom:0.5rem;color:#cbd5e1;">🎯 ${escapeHtml(pos.position)} = <span style="font-size:1.2rem;color:white">${escapeHtml(pos.digit)}</span></div>
            `;

            // Support both reasons object {th: [], en: []} and legacy array
            let reasonsList = [];
            if (Array.isArray(pos.reasons)) {
                reasonsList = pos.reasons;
            } else if (pos.reasons && typeof pos.reasons === 'object') {
                const lang = (document.documentElement.lang === 'th') ? 'th' : 'en';
                reasonsList = pos.reasons[lang] || pos.reasons.en || pos.reasons.th || [];
            }

            const topReasons = reasonsList.slice(0, 2);
            topReasons.forEach(r => {
                const text = typeof r === 'string' ? r : (r.text || JSON.stringify(r));
                xaiHtml += `<div class="xai-detail">${escapeHtml(text)}</div>`;
            });
            xaiHtml += `</div>`;
        });

        xaiPanel.innerHTML += xaiHtml;
        grid.appendChild(xaiPanel);
    }

    // Fade in panels
    document.querySelectorAll('.panel').forEach((p, i) => {
        p.style.opacity = '0';
        p.style.transform = 'translateY(20px)';
        setTimeout(() => {
            p.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            p.style.opacity = '1';
            p.style.transform = 'translateY(0)';
        }, i * 150);
    });
}

function createPanel(titleText) {
    const panel = document.createElement('div');
    panel.className = 'panel';
    const title = document.createElement('div');
    title.className = 'panel-title';
    title.textContent = titleText;
    panel.appendChild(title);
    return panel;
}

function showError(msg) {
    const loader = document.getElementById('loader');
    if (loader) loader.innerHTML = `<div style="color:var(--danger);padding:1rem;">❌ ${escapeHtml(msg)}</div>`;
}
