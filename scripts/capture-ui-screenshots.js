/**
 * scripts/capture-ui-screenshots.js
 * Captures high-fidelity desktop and mobile screenshots for visual QA evidence.
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const puppeteer = require('puppeteer-core');

const ROOT = path.resolve(__dirname, '..');
const SCREENSHOTS_DIR = path.join(ROOT, 'reports', 'screenshots');
fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

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

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const baseUrl = `http://127.0.0.1:${port}`;

  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const targets = [
    { file: 'strategy.html', name: 'strategy' },
    { file: 'manager.html', name: 'manager' },
    { file: 'performance.html', name: 'performance' },
    { file: '3d.html', name: '3d_showcase' },
    { file: 'mobile-wallet.html', name: 'mobile_wallet' }
  ];

  try {
    console.log('--- CAPTURING UI VISUAL QA SCREENSHOTS ---');
    for (const t of targets) {
      const page = await browser.newPage();
      
      // Desktop Viewport
      await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
      await page.goto(`${baseUrl}/${t.file}`, { waitUntil: 'networkidle2', timeout: 15000 });
      await new Promise(r => setTimeout(r, 800)); // wait for transitions
      const desktopPath = path.join(SCREENSHOTS_DIR, `${t.name}_desktop.png`);
      await page.screenshot({ path: desktopPath, fullPage: false });
      console.log(`[PASS] Desktop: ${desktopPath}`);

      // Mobile Viewport
      await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true });
      await new Promise(r => setTimeout(r, 500));
      const mobilePath = path.join(SCREENSHOTS_DIR, `${t.name}_mobile.png`);
      await page.screenshot({ path: mobilePath, fullPage: false });
      console.log(`[PASS] Mobile: ${mobilePath}`);

      await page.close();
    }
    console.log('All screenshots captured successfully in reports/screenshots/');
  } finally {
    await browser.close();
    server.close();
  }
})().catch(err => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
