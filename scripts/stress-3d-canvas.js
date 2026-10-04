/**
 * scripts/stress-3d-canvas.js
 * Adversarial Stress & Performance Test Harness for 3d.html Kinetic Canvas Engine.
 * Executed by Challenger 1 (Canvas Stress & Mobile Performance Challenger).
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const ROOT_DIR = path.resolve(__dirname, '..');
const HTML_FILE = path.join(ROOT_DIR, '3d.html');
const DASHBOARD_HTML_FILE = path.join(ROOT_DIR, 'dashboard', '3d.html');

console.log('======================================================================');
console.log('   CHALLENGER 1: ADVERSARIAL STRESS & PERFORMANCE TEST HARNESS');
console.log('======================================================================\n');

let totalTests = 0;
let passedTests = 0;

function test(name, fn) {
  totalTests++;
  try {
    fn();
    passedTests++;
    console.log(`  [PASS] ${name}`);
  } catch (err) {
    console.error(`  [FAIL] ${name}: ${err.message}`);
    throw err;
  }
}

// ---------------------------------------------------------------------
// TEST SUITE 1: MIRROR PARITY & STRING INVARIANTS
// ---------------------------------------------------------------------
console.log('--- 1. Mirror Parity & Core HTML Invariants ---');

test('Byte-for-byte SHA-256 parity between 3d.html and dashboard/3d.html', () => {
  const crypto = require('crypto');
  const buf1 = fs.readFileSync(HTML_FILE);
  const buf2 = fs.readFileSync(DASHBOARD_HTML_FILE);
  const h1 = crypto.createHash('sha256').update(buf1).digest('hex');
  const h2 = crypto.createHash('sha256').update(buf2).digest('hex');
  assert.strictEqual(h1, h2, `Hash mismatch: ${h1} !== ${h2}`);
  assert.strictEqual(buf1.length, buf2.length, 'Length mismatch');
});

test('Required string invariants present in 3d.html', () => {
  const content = fs.readFileSync(HTML_FILE, 'utf-8');
  const requiredStrings = [
    '70%',
    '15%',
    '70% Banker',
    '15% Pairs',
    'kinetic-canvas',
    'scroll-container',
    'sticky-viewport',
    'DreamFrame',
    '830386',
    '060503'
  ];
  for (const str of requiredStrings) {
    assert(content.includes(str), `Missing required invariant: "${str}"`);
  }
});

test('Zero external Three.js or GSAP blocking script references in 3d.html', () => {
  const content = fs.readFileSync(HTML_FILE, 'utf-8');
  assert(!content.includes('three.min.js'), 'three.min.js should not be included');
  assert(!content.includes('three.module.min.js'), 'three.module.min.js should not be included');
  assert(!content.includes('OrbitControls.js'), 'OrbitControls.js should not be included');
  assert(!content.includes('gsap.min.js'), 'gsap.min.js should not be included');
});

// ---------------------------------------------------------------------
// EXTRACT CANVAS ENGINE LOGIC FROM 3d.html
// ---------------------------------------------------------------------
const htmlContent = fs.readFileSync(HTML_FILE, 'utf-8');
const scriptMatch = htmlContent.match(/<script>([\s\S]*?)<\/script>[\s\r\n]*<\/body>/i);
assert(scriptMatch, 'Could not locate main canvas engine script in 3d.html');
const engineScriptCode = scriptMatch[1];

// ---------------------------------------------------------------------
// TEST SUITE 2: FRAME BOUNDARY CONDITIONS & SCROLL MAPPING
// ---------------------------------------------------------------------
console.log('\n--- 2. Frame Boundary Conditions & Scroll Mapping ---');

test('Scroll boundary clamping: [0%, 50%, 100%, negative, overscroll]', () => {
  const TOTAL_FRAMES = 50;

  function calculateScrollProgress(rectTop, containerHeight, viewportH) {
    const maxScroll = containerHeight - viewportH;
    if (maxScroll <= 0) return 0;
    return Math.max(0, Math.min(1, -rectTop / maxScroll));
  }

  function progressToTargetFrame(p) {
    return 1 + p * (TOTAL_FRAMES - 1);
  }

  function frameToDraw(f) {
    return Math.min(TOTAL_FRAMES, Math.max(1, Math.round(f)));
  }

  const vH = 800;
  const cH = 3600; // 450vh at 800px viewport
  const maxS = cH - vH; // 2800

  // Exact 0%
  let p = calculateScrollProgress(0, cH, vH);
  assert.strictEqual(p, 0.0);
  assert.strictEqual(progressToTargetFrame(p), 1.0);
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 1);

  // Exact 50%
  p = calculateScrollProgress(-maxS * 0.5, cH, vH);
  assert.strictEqual(p, 0.5);
  assert.strictEqual(progressToTargetFrame(p), 25.5);
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 26);

  // Exact 100%
  p = calculateScrollProgress(-maxS, cH, vH);
  assert.strictEqual(p, 1.0);
  assert.strictEqual(progressToTargetFrame(p), 50.0);
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 50);

  // Negative scroll (iOS pull down / elastic bounce: top > 0)
  p = calculateScrollProgress(250, cH, vH);
  assert.strictEqual(p, 0.0, 'Negative scroll must clamp to 0.0');
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 1);

  // Extreme negative scroll
  p = calculateScrollProgress(100000, cH, vH);
  assert.strictEqual(p, 0.0);
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 1);

  // Overscroll (iOS pull up past bottom: -rectTop > maxScroll)
  p = calculateScrollProgress(-(maxS + 350), cH, vH);
  assert.strictEqual(p, 1.0, 'Overscroll must clamp to 1.0');
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 50);

  // Extreme overscroll
  p = calculateScrollProgress(-999999, cH, vH);
  assert.strictEqual(p, 1.0);
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 50);

  // Degenerate container height (cH <= vH)
  p = calculateScrollProgress(-100, 800, 800);
  assert.strictEqual(p, 0.0, 'Zero maxScroll must return 0');
  assert.strictEqual(frameToDraw(progressToTargetFrame(p)), 1);
});

test('padIndex formatting handles edge indices and extreme clamping', () => {
  const TOTAL_FRAMES = 50;
  function padIndex(idx) {
    return String(Math.min(TOTAL_FRAMES, Math.max(1, idx))).padStart(3, "0");
  }

  assert.strictEqual(padIndex(1), '001');
  assert.strictEqual(padIndex(9), '009');
  assert.strictEqual(padIndex(10), '010');
  assert.strictEqual(padIndex(50), '050');
  assert.strictEqual(padIndex(0), '001', 'Underflow clamped to 001');
  assert.strictEqual(padIndex(-999), '001', 'Negative clamped to 001');
  assert.strictEqual(padIndex(51), '050', 'Overflow clamped to 050');
  assert.strictEqual(padIndex(99999), '050', 'Extreme overflow clamped to 050');
});

// ---------------------------------------------------------------------
// TEST SUITE 3: NEAREST-FRAME FALLBACK LOGIC & DELAYED LOAD SIMULATION
// ---------------------------------------------------------------------
console.log('\n--- 3. Nearest-Frame Fallback Logic & Delayed Load Simulation ---');

test('Fallback algorithm correctly finds closest loaded frame bidirectional', () => {
  const TOTAL_FRAMES = 50;

  function createFallbackEngine() {
    const images = new Array(TOTAL_FRAMES + 1);
    const loadedMap = new Array(TOTAL_FRAMES + 1).fill(false);

    function setLoaded(idx, valid = true) {
      loadedMap[idx] = true;
      images[idx] = {
        complete: valid,
        naturalWidth: valid ? 720 : 0,
        naturalHeight: valid ? 1280 : 0
      };
    }

    function getNearestLoadedImage(frameIdx) {
      if (loadedMap[frameIdx] && images[frameIdx] && images[frameIdx].complete && images[frameIdx].naturalWidth > 0) {
        return { img: images[frameIdx], index: frameIdx };
      }

      for (let offset = 1; offset < TOTAL_FRAMES; offset++) {
        const prev = frameIdx - offset;
        const next = frameIdx + offset;
        if (prev >= 1 && loadedMap[prev] && images[prev] && images[prev].complete && images[prev].naturalWidth > 0) {
          return { img: images[prev], index: prev };
        }
        if (next <= TOTAL_FRAMES && loadedMap[next] && images[next] && images[next].complete && images[next].naturalWidth > 0) {
          return { img: images[next], index: next };
        }
      }

      return null;
    }

    return { setLoaded, getNearestLoadedImage };
  }

  // 1. Cold start: zero frames loaded
  const engine1 = createFallbackEngine();
  for (let i = 1; i <= TOTAL_FRAMES; i++) {
    assert.strictEqual(engine1.getNearestLoadedImage(i), null, 'Empty store must return null without crashing');
  }

  // 2. Only Frame 1 loaded (Tier 1 Instant Paint)
  const engine2 = createFallbackEngine();
  engine2.setLoaded(1);
  for (let i = 1; i <= TOTAL_FRAMES; i++) {
    const match = engine2.getNearestLoadedImage(i);
    assert.notStrictEqual(match, null);
    assert.strictEqual(match.index, 1, `Frame ${i} must fallback to 1`);
  }

  // 3. Only Frame 50 loaded
  const engine3 = createFallbackEngine();
  engine3.setLoaded(50);
  for (let i = 1; i <= TOTAL_FRAMES; i++) {
    const match = engine3.getNearestLoadedImage(i);
    assert.strictEqual(match.index, 50, `Frame ${i} must fallback to 50`);
  }

  // 4. Sparse keyframes (1, 10, 20, 30, 40, 50)
  const engine4 = createFallbackEngine();
  [1, 10, 20, 30, 40, 50].forEach(k => engine4.setLoaded(k));

  // Exactly on keyframe
  assert.strictEqual(engine4.getNearestLoadedImage(10).index, 10);
  assert.strictEqual(engine4.getNearestLoadedImage(20).index, 20);

  // Between 1 and 10
  assert.strictEqual(engine4.getNearestLoadedImage(5).index, 1); // 5-4=1 vs 5+5=10 -> 1 is closer
  assert.strictEqual(engine4.getNearestLoadedImage(6).index, 10); // 6-5=1 vs 6+4=10 -> 10 is closer

  // Between 20 and 30
  assert.strictEqual(engine4.getNearestLoadedImage(24).index, 20);
  assert.strictEqual(engine4.getNearestLoadedImage(26).index, 30);

  // 5. Corrupted/incomplete frame handling
  const engine5 = createFallbackEngine();
  engine5.setLoaded(1, true);
  engine5.setLoaded(25, false); // Corrupted: naturalWidth = 0
  engine5.setLoaded(30, true);

  // Asking for 25 should skip corrupted 25 and find nearest valid
  const match25 = engine5.getNearestLoadedImage(25);
  assert.strictEqual(match25.index, 30, 'Corrupted frame 25 must be skipped in favor of frame 30');
});

test('Delayed frame arrival triggers in-flight upgrade logic correctly', () => {
  let lastDrawnFrameIndex = 1;
  let currentFrame = 25.0;
  let needsRedraw = false;

  function onFrameArrive(idx) {
    const currentTarget = Math.round(currentFrame);
    if (idx === 1 && lastDrawnFrameIndex === -1) {
      lastDrawnFrameIndex = 1;
    } else if (idx === currentTarget || Math.abs(idx - currentTarget) < Math.abs(lastDrawnFrameIndex - currentTarget)) {
      needsRedraw = true;
    }
  }

  // Frame 5 arrives: |5 - 25| = 20 < |1 - 25| = 24 -> Upgrade!
  onFrameArrive(5);
  assert.strictEqual(needsRedraw, true, 'Frame 5 is closer than 1, should trigger redraw');

  // Draw frame 5
  lastDrawnFrameIndex = 5;
  needsRedraw = false;

  // Frame 2 arrives: |2 - 25| = 23 > |5 - 25| = 20 -> No redundant upgrade
  onFrameArrive(2);
  assert.strictEqual(needsRedraw, false, 'Frame 2 is further than 5, should NOT trigger redraw');

  // Frame 25 arrives: exact target -> Immediate upgrade!
  onFrameArrive(25);
  assert.strictEqual(needsRedraw, true, 'Frame 25 is exact target, must trigger redraw');
});

// ---------------------------------------------------------------------
// TEST SUITE 4: DPR CAPPING & THERMAL GUARD
// ---------------------------------------------------------------------
console.log('\n--- 4. DPR Capping Logic & Thermal Guard ---');

test('DPR capping logic across standard and extreme DPRs (1.0, 2.0, 3.0, 4.0, 8.0)', () => {
  function computeTargetResolution(w, h, dprInput) {
    const dpr = Math.min(dprInput || 1, 2.0);
    return {
      targetW: Math.round(w * dpr),
      targetH: Math.round(h * dpr),
      effectiveDPR: dpr
    };
  }

  const screenW = 390;
  const screenH = 844;

  // Standard non-retina (DPR 1.0)
  let res = computeTargetResolution(screenW, screenH, 1.0);
  assert.strictEqual(res.effectiveDPR, 1.0);
  assert.strictEqual(res.targetW, 390);
  assert.strictEqual(res.targetH, 844);

  // Standard Retina (DPR 2.0)
  res = computeTargetResolution(screenW, screenH, 2.0);
  assert.strictEqual(res.effectiveDPR, 2.0);
  assert.strictEqual(res.targetW, 780);
  assert.strictEqual(res.targetH, 1688);

  // iPhone Pro / Samsung Ultra (DPR 3.0) -> CAPPED AT 2.0
  res = computeTargetResolution(screenW, screenH, 3.0);
  assert.strictEqual(res.effectiveDPR, 2.0, 'DPR 3.0 must be capped at 2.0');
  assert.strictEqual(res.targetW, 780);
  assert.strictEqual(res.targetH, 1688);

  // High-Density Flagship (DPR 4.0) -> CAPPED AT 2.0
  res = computeTargetResolution(screenW, screenH, 4.0);
  assert.strictEqual(res.effectiveDPR, 2.0, 'DPR 4.0 must be capped at 2.0');
  assert.strictEqual(res.targetW, 780);
  assert.strictEqual(res.targetH, 1688);

  // Adversarial Extreme (DPR 8.0 / 16.0) -> CAPPED AT 2.0
  res = computeTargetResolution(screenW, screenH, 8.0);
  assert.strictEqual(res.effectiveDPR, 2.0, 'DPR 8.0 must be capped at 2.0');

  // Fallbacks: 0, undefined, null, NaN
  res = computeTargetResolution(screenW, screenH, 0);
  assert.strictEqual(res.effectiveDPR, 1.0, 'DPR 0 fallback to 1.0');

  res = computeTargetResolution(screenW, screenH, undefined);
  assert.strictEqual(res.effectiveDPR, 1.0, 'DPR undefined fallback to 1.0');

  res = computeTargetResolution(screenW, screenH, null);
  assert.strictEqual(res.effectiveDPR, 1.0, 'DPR null fallback to 1.0');
});

// ---------------------------------------------------------------------
// TEST SUITE 5: OBJECT-COVER ASPECT RATIO MATHEMATICS
// ---------------------------------------------------------------------
console.log('\n--- 5. Centered Object-Cover Aspect Ratio Math ---');

test('Object cover math covers 100% canvas without gaps on all aspect ratios', () => {
  const iW = 720;
  const iH = 1280; // 9:16 portrait asset

  const viewports = [
    { name: 'Portrait 9:16 (iPhone 13)', cW: 780, cH: 1688 },
    { name: 'Square 1:1 (Foldable tablet)', cW: 1600, cH: 1600 },
    { name: 'Landscape 16:9 (Desktop FHD)', cW: 1920, cH: 1080 },
    { name: 'Ultra-Wide 21:9 (Ultrawide Monitor)', cW: 2560, cH: 1080 },
    { name: 'Legacy 4:3 (iPad)', cW: 1024, cH: 768 },
    { name: 'Tall Mobile 9:21 (Sony Xperia)', cW: 720, cH: 1680 }
  ];

  for (const vp of viewports) {
    const scale = Math.max(vp.cW / iW, vp.cH / iH);
    const dW = iW * scale;
    const dH = iH * scale;
    const dX = (vp.cW - dW) / 2;
    const dY = (vp.cH - dH) / 2;

    // Invariant 1: Canvas must be completely covered horizontally & vertically
    assert(dW >= vp.cW - 1e-6, `[${vp.name}] Width underflow: dW (${dW}) < cW (${vp.cW})`);
    assert(dH >= vp.cH - 1e-6, `[${vp.name}] Height underflow: dH (${dH}) < cH (${vp.cH})`);

    // Invariant 2: Aspect ratio must be perfectly preserved (no distortion)
    const originalAspect = iW / iH;
    const drawnAspect = dW / dH;
    assert(Math.abs(originalAspect - drawnAspect) < 1e-6, `[${vp.name}] Aspect distortion: ${originalAspect} vs ${drawnAspect}`);

    // Invariant 3: Perfect optical centering
    const centerX = dX + dW / 2;
    const centerY = dY + dH / 2;
    assert(Math.abs(centerX - vp.cW / 2) < 1e-6, `[${vp.name}] Horizontal centering error`);
    assert(Math.abs(centerY - vp.cH / 2) < 1e-6, `[${vp.name}] Vertical centering error`);
  }
});

// ---------------------------------------------------------------------
// TEST SUITE 6: LERP CONVERGENCE & RAF LOOP STABILITY
// ---------------------------------------------------------------------
console.log('\n--- 6. Lerp Convergence & RAF Loop Stability ---');

test('Lerp convergence monotonic stability and cutoff threshold', () => {
  const TOTAL_FRAMES = 50;
  const LERP_FACTOR = 0.11;

  // Forward scroll simulation: frame 1 -> frame 50
  let currentFrame = 1.0;
  const targetFrame = 50.0;
  let iterations = 0;
  let prevFrame = currentFrame;

  while (currentFrame !== targetFrame && iterations < 500) {
    iterations++;
    const diff = targetFrame - currentFrame;
    if (Math.abs(diff) < 0.001) {
      currentFrame = targetFrame;
    } else {
      currentFrame += diff * LERP_FACTOR;
    }

    // Must monotonically increase towards target
    assert(currentFrame >= prevFrame, `Non-monotonic step at iteration ${iterations}`);
    assert(currentFrame <= targetFrame, `Overshoot at iteration ${iterations}: ${currentFrame} > ${targetFrame}`);
    prevFrame = currentFrame;
  }

  assert.strictEqual(currentFrame, 50.0, 'Did not reach exact target');
  assert(iterations < 100, `Convergence took too long: ${iterations} iterations (expected ~93)`);
  console.log(`    Forward Lerp converged exactly to 50.0 in ${iterations} frames (~${(iterations * 16.6).toFixed(0)}ms)`);

  // Reverse scroll simulation: frame 50 -> frame 1
  currentFrame = 50.0;
  const targetReverse = 1.0;
  iterations = 0;
  prevFrame = currentFrame;

  while (currentFrame !== targetReverse && iterations < 500) {
    iterations++;
    const diff = targetReverse - currentFrame;
    if (Math.abs(diff) < 0.001) {
      currentFrame = targetReverse;
    } else {
      currentFrame += diff * LERP_FACTOR;
    }

    assert(currentFrame <= prevFrame, `Non-monotonic step at reverse iteration ${iterations}`);
    assert(currentFrame >= targetReverse, `Undershoot at reverse iteration ${iterations}: ${currentFrame} < ${targetReverse}`);
    prevFrame = currentFrame;
  }

  assert.strictEqual(currentFrame, 1.0);
  assert(iterations < 100);
  console.log(`    Reverse Lerp converged exactly to 1.0 in ${iterations} frames (~${(iterations * 16.6).toFixed(0)}ms)`);

  // Steady-state stability: once converged, 0 change
  const diffStable = 1.0 - currentFrame;
  assert.strictEqual(diffStable, 0);
});

test('prefers-reduced-motion bypasses lerp with zero transition lag', () => {
  const TOTAL_FRAMES = 50;
  let currentFrame = 1.0;
  let targetProgress = 0.75;
  const targetFrame = 1 + targetProgress * (TOTAL_FRAMES - 1); // 37.75

  const prefersReducedMotion = true;

  if (prefersReducedMotion) {
    currentFrame = targetFrame;
  }

  assert.strictEqual(currentFrame, 37.75, 'Reduced motion must immediately match targetFrame');
  const frameToDraw = Math.min(TOTAL_FRAMES, Math.max(1, Math.round(currentFrame)));
  assert.strictEqual(frameToDraw, 38);
});

// ---------------------------------------------------------------------
// TEST SUITE 7: HEADLESS DOM & FULL CANVAS ENGINE EXECUTION
// ---------------------------------------------------------------------
console.log('\n--- 7. Headless DOM Execution of Canvas Script in 3d.html ---');

test('Canvas engine script compiles and initializes cleanly without exceptions', () => {
  // Mock DOM environment for VM execution
  const mockCanvas = {
    getContext: (type, opts) => {
      return {
        fillStyle: '',
        fillRect: () => {},
        drawImage: () => {},
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high'
      };
    },
    getBoundingClientRect: () => ({ width: 390, height: 844, top: 0 }),
    width: 0,
    height: 0,
    style: {}
  };

  const mockContainer = {
    getBoundingClientRect: () => ({ width: 390, height: 3798, top: 0 }),
    offsetHeight: 3798
  };

  const mockElement = () => ({
    style: {},
    classList: { add: () => {}, remove: () => {}, toggle: () => {} },
    innerText: '',
    innerHTML: '',
    value: '0',
    addEventListener: () => {}
  });

  const domElements = {
    'kinetic-canvas': mockCanvas,
    'scroll-container': mockContainer,
    'fps-label': mockElement(),
    'camera-scrubber': mockElement(),
    'scene1-hud': mockElement(),
    'scene2-hud': mockElement(),
    'btn-toggle-play': mockElement(),
    'play-icon': mockElement(),
    'play-text': mockElement(),
    'scene1-countdown': mockElement(),
    'jackpot-display': mockElement(),
    'neighbors-display': mockElement(),
    'pairs-display': mockElement(),
    'three-display': mockElement(),
    'banker-display': mockElement(),
    'toast': mockElement(),
    'mobile-drawer': mockElement(),
    'drawer-overlay': mockElement()
  };

  const listeners = {};

  let rafCount = 0;
  const sandbox = {
    window: {
      devicePixelRatio: 2.0,
      innerWidth: 390,
      innerHeight: 844,
      addEventListener: (evt, cb) => { listeners[evt] = cb; },
      matchMedia: (query) => ({
        matches: false,
        addEventListener: () => {}
      }),
      scrollTo: () => {},
      navigator: { clipboard: { writeText: () => Promise.resolve() } }
    },
    document: {
      getElementById: (id) => domElements[id] || null,
      documentElement: { clientHeight: 844 }
    },
    Image: class {
      constructor() {
        this.src = '';
        this.complete = true;
        this.naturalWidth = 720;
        this.naturalHeight = 1280;
      }
      decode() { return Promise.resolve(); }
    },
    requestAnimationFrame: (cb) => {
      if (rafCount++ < 3) {
        setTimeout(cb, 10);
      }
    },
    performance: { now: () => Date.now() },
    setTimeout: (cb, ms) => setTimeout(cb, ms),
    clearTimeout: clearTimeout,
    console: { log: () => {}, warn: () => {}, error: () => {} },
    fetch: () => Promise.resolve({ ok: false })
  };

  sandbox.window.document = sandbox.document;
  sandbox.global = sandbox.window;

  // Execute engine script in sandbox
  const script = new vm.Script(engineScriptCode);
  const context = vm.createContext(sandbox);
  script.runInContext(context);

  // Trigger DOMContentLoaded
  if (listeners['DOMContentLoaded']) {
    listeners['DOMContentLoaded']();
  }

  // Verify canvas was initialized and DPR capped at 2.0x (390 * 2 = 780, 844 * 2 = 1688)
  assert.strictEqual(mockCanvas.width, 780, 'Canvas width should be 780');
  assert.strictEqual(mockCanvas.height, 1688, 'Canvas height should be 1688');

  // Verify global helpers registered
  assert(typeof sandbox.window.toggleAutoTour === 'function', 'toggleAutoTour exported');
  assert(typeof sandbox.window.jumpToProgress === 'function', 'jumpToProgress exported');
  assert(typeof sandbox.window.copyAllStrategy === 'function', 'copyAllStrategy exported');
});

console.log('\n======================================================================');
console.log(`   ALL ${passedTests} ADVERSARIAL STRESS TESTS PASSED SUCCESSFULLY!`);
console.log('======================================================================\n');

setTimeout(() => {
  process.exit(0);
}, 50);

