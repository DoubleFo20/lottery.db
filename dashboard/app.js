const API_URL = '/Lottery/api/predict.php';

document.addEventListener('DOMContentLoaded', () => {
    fetchInsights();
    setInterval(fetchInsights, 60 * 1000);
});

async function fetchInsights() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        
        if (data.status !== 'ok') {
            showError('API returned error status.');
            console.error(data);
            return;
        }

        renderDashboard(data);
    } catch (err) {
        showError('Failed to fetch data from AI Engine. Ensure XAMPP is running and cache exists.');
        console.error(err);
    }
}

function renderDashboard(data) {
    const loader = document.getElementById('loader');
    if (loader) loader.style.display = 'none';

    // Update Meta — support both run_pipeline.py and predict.php cache structures
    const totalDraws  = data.meta?.dataset?.total_draws  ?? data.meta?.total_draws  ?? '?';
    const latestDraw  = data.meta?.dataset?.latest       ?? data.meta?.latest_draw  ?? '?';
    const metaStr = `Analysis on ${totalDraws} draws | Latest: ${latestDraw}`;
    const metaEl = document.getElementById('meta-info');
    if (metaEl && metaEl.textContent.includes('Loading')) {
        metaEl.textContent = metaStr;
    }

    // Cache Banner
    if (data.cache) {
        const banner = document.getElementById('status-banner');
        const cacheTime = new Date(data.cache.cached_at);
        const timeStr = cacheTime.toLocaleTimeString('th-TH');
        
        function updateBannerTimer() {
            if (!banner) return;
            const diff = Math.floor((Date.now() - cacheTime.getTime()) / 1000);
            if (diff < 0) return;
            const h = Math.floor(diff / 3600);
            const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
            const s = (diff % 60).toString().padStart(2, '0');
            banner.textContent = `Using cached prediction from ${timeStr} ,Updated: ${new Date().toLocaleTimeString('th-TH')}`;
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
    data.candidates.forEach((cand, idx) => {
        predHtml += `
            <div class="prediction-item">
                <div class="prediction-header">
                    <span class="pred-number">${cand.number}</span>
                    <span class="pred-rank">#${idx + 1}</span>
                </div>
                <div class="confidence-label">
                    <span>Confidence Score</span>
                    <span>${cand.confidence.toFixed(1)}%</span>
                </div>
                <div class="confidence-wrapper">
                    <div class="confidence-bar" style="width: ${cand.confidence}%"></div>
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
            trendHtml += `<span class="trend-badge trend-streak">🔥 ${s.position}: ${s.digit} (${s.length} draws)</span>`;
        });
        trendHtml += `</div>`;
    }

    // Spikes (Up)
    const spikesUp = analytics.frequency_spikes || [];
    if (spikesUp.length > 0) {
        trendHtml += `<div class="trend-section"><h4>Frequency Spikes (Surging)</h4>`;
        spikesUp.forEach(s => {
            trendHtml += `<span class="trend-badge trend-spike">🔺 ${s.position} [${s.digit}] x${s.ratio}</span>`;
        });
        trendHtml += `</div>`;
    }

    // Drops (Down)
    const spikesDown = analytics.frequency_drops || [];
    if (spikesDown.length > 0) {
        trendHtml += `<div class="trend-section"><h4>Frequency Drops (Cooling)</h4>`;
        spikesDown.forEach(s => {
            trendHtml += `<span class="trend-badge trend-drop">🔻 ${s.position} [${s.digit}] x${s.ratio}</span>`;
        });
        trendHtml += `</div>`;
    }
    
    trendPanel.innerHTML += trendHtml || '<p style="color:var(--text-muted)">No significant trends detected.</p>';
    grid.appendChild(trendPanel);

    // 3. Explainable AI Panel (Why number #1?)
    const expData = Array.isArray(data.explanation) ? data.explanation[0] : data.explanation;
    if (expData && data.candidates.length > 0 && expData.positions) {
        const xaiPanel = createPanel(`🧠 Why ${data.candidates[0].number}? (XAI)`);
        let xaiHtml = `<p style="margin-bottom:1rem;color:var(--text-muted)">AI reasoning breakdown for the top candidate.</p>`;
        
        const exp = expData;
        
        let overview = `<div style="display:flex;gap:10px;margin-bottom:1rem;">
            <span class="trend-badge" style="background:rgba(59,130,246,0.2);color:#60a5fa">📊 Prob: ${exp.overall_factor_pct.probability_pct}%</span>
            <span class="trend-badge" style="background:rgba(239,68,68,0.2);color:#f87171">🌡 Heat: ${exp.overall_factor_pct.heatmap_pct}%</span>
            <span class="trend-badge" style="background:rgba(167,139,250,0.2);color:#c084fc">🔎 Patt: ${exp.overall_factor_pct.pattern_pct}%</span>
        </div>`;
        
        xaiHtml += overview;

        exp.positions.forEach(pos => {
            xaiHtml += `
                <div style="margin-bottom:1rem;background:rgba(255,255,255,0.03);padding:10px;border-radius:8px;">
                    <div style="font-weight:bold;margin-bottom:0.5rem;color:#cbd5e1;">🎯 ${pos.position} = <span style="font-size:1.2rem;color:white">${pos.digit}</span></div>
            `;
            // Take top 2 reasons per digit for brevity
            const topReasons = pos.reasons.slice(0, 2);
            topReasons.forEach(r => {
                xaiHtml += `<div class="xai-detail">${r}</div>`;
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
    if (loader) loader.innerHTML = `<div style="color:var(--danger)">❌ Error: ${msg}</div>`;
}
