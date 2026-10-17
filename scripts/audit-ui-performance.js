/**
 * scripts/audit-ui-performance.js
 * Measures baseline performance, Core Web Vitals, and DOM metrics across all dashboards.
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const puppeteer = require('puppeteer-core');

const ROOT = path.resolve(__dirname, '..');

const executablePath = process.env.CHROME_PATH || [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium',
].find(file => fs.existsSync(file));

if (!executablePath) {
  console.error('Chrome executable not found');
  process.exit(1);
}

const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname;
  let file = path.resolve(ROOT, '.' + pathname);
  if (!file.startsWith(ROOT + path.sep)) { res.writeHead(403).end(); return; }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404).end(); return; }

  const ext = path.extname(file);
  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml'
  };
  res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

async function measurePage(browser, url, label) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const metricsBefore = await page.metrics();
  const startTime = Date.now();
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 15000 });
  const loadDurationMs = Date.now() - startTime;
  const metricsAfter = await page.metrics();

  const timing = await page.evaluate(() => {
    const nav = performance.getEntriesByType('navigation')[0] || {};
    const paint = performance.getEntriesByType('paint') || [];
    const fp = paint.find(p => p.name === 'first-paint')?.startTime || 0;
    const fcp = paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0;
    const domNodes = document.querySelectorAll('*').length;
    return {
      domContentLoadedMs: Math.round(nav.domContentLoadedEventEnd || 0),
      loadEventEndMs: Math.round(nav.loadEventEnd || 0),
      firstPaintMs: Math.round(fp),
      firstContentfulPaintMs: Math.round(fcp),
      domNodes
    };
  });

  const heapUsedMb = ((metricsAfter.JSHeapUsedSize || 0) / (1024 * 1024)).toFixed(2);
  const layoutCount = (metricsAfter.LayoutCount || 0) - (metricsBefore.LayoutCount || 0);

  const result = {
    page: label,
    loadDurationMs,
    domContentLoadedMs: timing.domContentLoadedMs,
    firstContentfulPaintMs: timing.firstContentfulPaintMs,
    heapUsedMb: parseFloat(heapUsedMb),
    domNodes: timing.domNodes,
    layoutCount
  };

  await page.close();
  return result;
}

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const baseUrl = `http://127.0.0.1:${port}`;

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const pages = [
      { path: '/strategy.html', label: 'Strategy Dashboard' },
      { path: '/manager.html', label: 'Manager Control Center' },
      { path: '/performance.html', label: 'Performance Dashboard' },
      { path: '/3d.html', label: '3D Showcase' }
    ];

    console.log('--- UI PERFORMANCE BASELINE AUDIT ---');
    const results = [];
    for (const p of pages) {
      const res = await measurePage(browser, `${baseUrl}${p.path}`, p.label);
      results.push(res);
      console.log(`[${res.page}] Load: ${res.loadDurationMs}ms | FCP: ${res.firstContentfulPaintMs}ms | DOM Nodes: ${res.domNodes} | Heap: ${res.heapUsedMb}MB`);
    }

    const reportPath = path.join(ROOT, 'reports', 'ui_performance_baseline.json');
    fs.mkdirSync(path.dirname(reportPath), { recursive: true });
    fs.writeFileSync(reportPath, JSON.stringify({ timestamp: new Date().toISOString(), results }, null, 2));
    console.log(`Baseline recorded to ${reportPath}`);
  } finally {
    await browser.close();
    server.close();
  }
})().catch(err => {
  console.error('Audit failed:', err);
  process.exit(1);
});
