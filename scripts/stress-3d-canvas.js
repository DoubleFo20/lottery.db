/**
 * Browser regressions for scroll-sequence demos. Requires a production Next
 * server via NEXT_BASE_URL when Next routes are present, and an installed Chrome.
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const puppeteer = require('puppeteer-core');

const ROOT = path.resolve(__dirname, '..');
const MARKER = 'data-canvas-benchmark';
const SKIP = new Set(['.git', '.next', '.agents', '.codex', '.venv', 'node_modules', 'public', 'assets', 'dist']);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!SKIP.has(entry.name)) yield* walk(file);
    } else yield file;
  }
}

function discover(staticBase) {
  const targets = new Map();
  for (const file of walk(ROOT)) {
    if (!file.endsWith('.html')) continue;
    const source = fs.readFileSync(file, 'utf8');
    // Discover both explicitly registered and existing frame-sequence demos.
    if (!source.includes(MARKER) &&
        !(source.includes('hero-scroll-container') && /<canvas\b/.test(source))) continue;
    const url = new URL(path.relative(ROOT, file).replaceAll('\\', '/'), staticBase).href;
    targets.set(url, { url, required: true });
  }
  for (const app of ['next-app/src/app', 'next-app/app']) {
    const dir = path.join(ROOT, app);
    if (!fs.existsSync(dir)) continue;
    assert(process.env.NEXT_BASE_URL, 'Set NEXT_BASE_URL to a running production Next server');
    for (const file of walk(dir)) {
      if (!/^page\.(tsx?|jsx?)$/.test(path.basename(file))) continue;
      const parts = path.relative(dir, path.dirname(file)).split(path.sep).filter(Boolean);
      assert(!parts.some(p => p.includes('[') || p.startsWith('@') || /^\(\.\.?/.test(p)),
        'Provide concrete benchmark routes for dynamic/parallel/intercepted route: ' + file);
      const route = parts.filter(p => !/^\(.*\)$/.test(p)).join('/');
      const url = new URL(route, process.env.NEXT_BASE_URL).href;
      const source = fs.readFileSync(file, 'utf8');
      targets.set(url, { url, required: source.includes('StickyScrollCanvas') || source.includes(MARKER) });
    }
  }
  assert(targets.size > 0, 'No demo paths discovered');
  return [...targets.values()];
}

function installProbe() {
  const request = window.requestAnimationFrame.bind(window);
  const cancel = window.cancelAnimationFrame.bind(window);
  const pending = new Set();
  let ticks = 0;
  let draws = 0;
  let displayed = null;
  window.requestAnimationFrame = callback => {
    const id = request(time => {
      pending.delete(id);
      ticks++;
      callback(time);
    });
    pending.add(id);
    return id;
  };
  window.cancelAnimationFrame = id => {
    pending.delete(id);
    cancel(id);
  };
  for (const name of ['drawImage', 'fillRect', 'clearRect']) {
    const original = CanvasRenderingContext2D.prototype[name];
    CanvasRenderingContext2D.prototype[name] = function (...args) {
      if (this.canvas.closest('[data-canvas-benchmark]')) {
        draws++;
        if (name === 'drawImage') {
          const match = String(args[0].src).match(/frame-(\d+)/);
          displayed = match ? Number(match[1]) : null;
        } else displayed = 0;
      }
      return original.apply(this, args);
    };
  }
  window.__canvasProbe = () => ({
    ticks, draws, displayed, pending: pending.size,
    visible: document.visibilityState === 'visible',
  });
}

const snapshot = page => page.evaluate(() => window.__canvasProbe());

async function idle(page, label) {
  await page.waitForFunction(() => window.__canvasProbe().pending === 0,
    { polling: 100, timeout: 8000 });
  const before = await snapshot(page);
  const a = await page.metrics();
  await sleep(600);
  const b = await page.metrics();
  const after = await snapshot(page);
  assert(before.visible && after.visible, label + ': document hidden');
  assert.equal(after.pending, 0, label + ': pending rAF');
  assert.equal(after.ticks, before.ticks, label + ': idle rAF activity');
  assert.equal(after.draws, before.draws, label + ': idle canvas draws');
  const duration = b.Timestamp - a.Timestamp;
  console.log('[IDLE]', label, {
    ticks: after.ticks - before.ticks,
    draws: after.draws - before.draws,
    taskTimePercent: Number((100 * (b.TaskDuration - a.TaskDuration) / duration).toFixed(2)),
    heapBytes: b.JSHeapUsedSize,
  });
}

async function scroll(page, progress) {
  await page.evaluate(progress => {
    const section = document.querySelector('[data-canvas-benchmark]');
    if (!section) throw new Error('Canvas demo missing benchmark marker');
    const rect = section.getBoundingClientRect();
    scrollTo({ top: scrollY + rect.top + progress * (rect.height - innerHeight), behavior: 'instant' });
  }, progress);
}

async function scenario(browser, target, mode, reduced) {
  const page = await browser.newPage();
  const held = [];
  const errors = [];
  let injected = 0;
  let failed = 0;
  let released = false;
  const fixture = request => request.respond({
    status: 200, contentType: 'image/svg+xml',
    body: '<svg xmlns="http://www.w3.org/2000/svg" width="72" height="128"><rect width="72" height="128" fill="#583a12"/></svg>',
  });
  try {
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
    await page.bringToFront();
    await page.setCacheEnabled(false);
    await page.setBypassServiceWorker(true);
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: reduced ? 'reduce' : 'no-preference' }]);
    await page.evaluateOnNewDocument(installProbe);
    page.on('pageerror', error => errors.push(error.message));
    await page.setRequestInterception(true);
    page.on('request', request => {
      const frame = new URL(request.url()).pathname.match(/(?:ezgif-)?frame-(\d+)\.(?:webp|png|jpe?g)$/);
      if (!frame) {
        // Static demos use a CDN for styles; keep CI independent of it.
        if (new URL(request.url()).origin !== new URL(target.url).origin) {
          void request.respond({ status: 200, contentType: 'text/javascript', body: '' });
        } else void request.continue();
        return;
      }
      injected++;
      const index = Number(frame[1]);
      if (mode === 'all-missing' || (mode === 'target-missing' && index === 26)) {
        failed++;
        void request.abort('failed');
      } else if (mode === 'delayed' && index === 26 && !released) {
        held.push(request);
      } else void fixture(request);
    });
    const response = await page.goto(target.url, { waitUntil: 'domcontentloaded' });
    assert(response && response.ok(), target.url + ': failed navigation');
    if (!target.required) {
      // Wait for hydration before deciding whether a route is a canvas demo.
      await sleep(500);
      if (!(await page.$('[data-canvas-benchmark]'))) {
        assert(!(await page.$('canvas')), 'Unregistered canvas route: ' + target.url);
        console.log('[SKIP non-canvas]', target.url);
        return false;
      }
    }
    await page.waitForSelector('[data-canvas-benchmark] canvas');
    await page.waitForFunction(() => window.__canvasProbe().draws > 0,
      { polling: 100, timeout: 10000 });
    if (mode === 'delayed') {
      await page.waitForFunction(() => window.__canvasProbe().displayed > 0, { polling: 100 });
      const deadline = Date.now() + 10000;
      while (!held.length && Date.now() < deadline) await sleep(50);
      assert(held.length > 0, 'Delayed image request was not exercised');
    } else {
      await page.waitForNetworkIdle({ idleTime: 300, timeout: 20000 });
    }
    assert(injected > 0, 'Image injection was not exercised');
    if (mode.includes('missing')) assert(failed > 0, 'Failures were not injected');
    await idle(page, target.url + ' ' + mode + ' initial');
    for (const progress of [0.5, 1, 0]) {
      const before = await snapshot(page);
      await scroll(page, progress);
      await page.waitForFunction(ticks => window.__canvasProbe().ticks > ticks,
        { polling: 100, timeout: 5000 }, before.ticks);
      await idle(page, target.url + ' ' + mode + ' scroll=' + progress);
      if (mode === 'healthy') {
        const after = await snapshot(page);
        assert(after.draws > before.draws, 'Scroll did not render a new frame');
        assert.equal(after.displayed, progress === 0.5 ? 26 : progress === 1 ? 50 : 1);
      }
      if (mode === 'target-missing' && progress === 0.5) {
        const after = await snapshot(page);
        assert(after.displayed > 0 && after.displayed !== 26, 'No loaded fallback displayed');
      }
      if (mode === 'all-missing') assert.equal((await snapshot(page)).displayed, 0);
      if (mode === 'delayed' && progress === 0.5) {
        assert.notEqual((await snapshot(page)).displayed, 26);
        released = true;
        await Promise.all(held.splice(0).map(fixture));
        await page.waitForFunction(() => window.__canvasProbe().displayed === 26, { polling: 100 });
        await page.waitForNetworkIdle({ idleTime: 300, timeout: 20000 });
        await idle(page, target.url + ' late frame recovered');
      }
    }
    const before = await snapshot(page);
    await page.setViewport({ width: 430, height: 900, deviceScaleFactor: 2 });
    await page.waitForFunction(draws => window.__canvasProbe().draws > draws,
      { polling: 100, timeout: 5000 }, before.draws);
    await idle(page, target.url + ' resized');
    assert.equal(errors.length, 0, errors.join('\n'));
    return true;
  } finally {
    await page.close();
  }
}

async function serve() {
  const server = http.createServer((request, response) => {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    let file = path.resolve(ROOT, '.' + pathname);
    if (!file.startsWith(ROOT + path.sep)) { response.writeHead(403).end(); return; }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };
    if (!fs.existsSync(file)) { response.writeHead(404).end(); return; }
    response.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
    fs.createReadStream(file).pipe(response);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return { server, base: 'http://127.0.0.1:' + server.address().port + '/' };
}

async function main() {
  const { server, base } = await serve();
  let browser;
  try {
    const executablePath = process.env.CHROME_PATH || [
      'C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    ].find(file => fs.existsSync(file));
    assert(executablePath, 'Set CHROME_PATH to your installed Chrome/Chromium');
    browser = await puppeteer.launch({ executablePath, headless: true });
    let passed = 0;
    for (const target of discover(base)) {
      for (const mode of ['healthy', 'target-missing', 'all-missing', 'delayed']) {
        for (const reduced of [false, true]) {
          if (await scenario(browser, target, mode, reduced)) passed++;
        }
      }
    }
    assert(passed > 0, 'No canvas scenarios executed');
    console.log('PASS: ' + passed + ' browser scenarios');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
