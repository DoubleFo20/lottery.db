/**
 * scripts/prep-3d-data.js
 * Reads database/predictions/pipeline_cache.json and generates hopper_3d_data.json
 * for the 3D Lucky Draw Hopper WebGL visualization.
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const PIPELINE_CACHE_PATH = path.join(ROOT_DIR, 'database', 'predictions', 'pipeline_cache.json');
const OUTPUT_DATA_PATH = path.join(ROOT_DIR, 'database', 'predictions', 'hopper_3d_data.json');
const DASHBOARD_OUTPUT_PATH = path.join(ROOT_DIR, 'dashboard', 'hopper_3d_data.json');

function main() {
  console.log('[1/3] Reading pipeline cache...');
  let pipelineData = {};
  if (fs.existsSync(PIPELINE_CACHE_PATH)) {
    try {
      const raw = fs.readFileSync(PIPELINE_CACHE_PATH, 'utf-8');
      pipelineData = JSON.parse(raw);
    } catch (err) {
      console.warn('Failed to parse pipeline_cache.json:', err.message);
    }
  } else {
    console.warn('pipeline_cache.json not found, using default template');
  }

  const candidates = pipelineData.candidates || [
    { number: '839386', confidence: 100.0 },
    { number: '539386', confidence: 87.15 },
    { number: '339386', confidence: 85.46 }
  ];

  const fullSpectrum = pipelineData.full_spectrum || {};
  const bankerDigits = (fullSpectrum.banker_digits || [{ digit: '3' }, { digit: '8' }]).map(b => String(b.digit));
  const top2Pairs = fullSpectrum.top2_pairs || [
    { direct: '86', reverse: '68' },
    { direct: '06', reverse: '60' },
    { direct: '83', reverse: '38' }
  ];
  const box3 = fullSpectrum.box_3 || [
    { direct: '386', permutations: ['368', '386', '638', '683', '836', '863'] },
    { direct: '306', permutations: ['036', '063', '306', '360', '603', '630'] }
  ];

  // Digits that appear in top candidate
  const top1Digits = (candidates[0]?.number || '839386').split('');
  
  console.log('[2/3] Constructing 3D hopper ball pool...');
  // Standard lottery draw machine contains 4-5 sets of digits 0-9 (40 balls)
  const balls = [];
  let ballIndex = 0;
  const copiesPerDigit = 4;

  // Ball color palette
  const COLOR_GOLD = '#f59e0b';      // Jackpot candidate digits
  const COLOR_CYAN = '#38bdf8';      // 2-digit upper
  const COLOR_EMERALD = '#10b981';   // Banker digits
  const COLOR_PURPLE = '#a855f7';    // 3-digit box
  const COLOR_STANDARD = '#475569';  // Neutral ball

  for (let digit = 0; digit <= 9; digit++) {
    const digitStr = String(digit);
    const isBanker = bankerDigits.includes(digitStr);
    const isTop1 = top1Digits.includes(digitStr);

    for (let c = 0; c < copiesPerDigit; c++) {
      let tier = 'standard';
      let color = COLOR_STANDARD;
      let glow = false;

      if (isBanker) {
        tier = 'banker';
        color = COLOR_EMERALD;
        glow = true;
      } else if (isTop1) {
        tier = 'jackpot';
        color = COLOR_GOLD;
        glow = true;
      } else if (digit % 2 === 0) {
        color = '#3b82f6'; // Blue accent
      } else {
        color = '#64748b'; // Slate accent
      }

      balls.push({
        id: `ball-${digit}-${c}`,
        digit: digit,
        tier: tier,
        color: color,
        glow: glow,
        weight: isBanker ? 1.5 : (isTop1 ? 1.3 : 1.0)
      });
      ballIndex++;
    }
  }

  const hopper3DConfig = {
    meta: {
      generated_at: new Date().toISOString(),
      version: '1.0',
      total_balls: balls.length,
      chamber_radius: 12.0
    },
    clusters: {
      jackpot_6: candidates.slice(0, 3),
      banker_digits: bankerDigits,
      top2_pairs: top2Pairs,
      box_3: box3
    },
    balls: balls
  };

  console.log(`[3/3] Writing config (${balls.length} balls) to ${OUTPUT_DATA_PATH}...`);
  fs.mkdirSync(path.dirname(OUTPUT_DATA_PATH), { recursive: true });
  fs.writeFileSync(OUTPUT_DATA_PATH, JSON.stringify(hopper3DConfig, null, 2), 'utf-8');

  // Also write to dashboard directory if exists
  if (fs.existsSync(path.join(ROOT_DIR, 'dashboard'))) {
    fs.writeFileSync(DASHBOARD_OUTPUT_PATH, JSON.stringify(hopper3DConfig, null, 2), 'utf-8');
    console.log(`[OK] Mirrored to ${DASHBOARD_OUTPUT_PATH}`);
  }

  console.log('✓ 3D Hopper data generated successfully!');
}

main();
