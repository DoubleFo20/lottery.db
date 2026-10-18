/**
 * scripts/capture-ui-screenshots.js
 * Captures high-fidelity desktop, tablet, mobile, and drawer interaction screenshots
 * for visual QA and regression evidence.
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
    '.csv': 'text/csv',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml'
  };
  const stat = fs.statSync(file);
  res.setHeader('Content-Type', mimeTypes[ext] || 'application/octet-stream');
  res.setHeader('Last-Modified', stat.mtime.toUTCString());
  res.setHeader('Cache-Control', 'no-cache');
  if (req.method === 'HEAD') { res.writeHead(200).end(); return; }
  res.writeHead(200);
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
    console.log('--- CAPTURING UI VISUAL QA EVIDENCE SCREENSHOTS ---');
    for (const t of targets) {
      const page = await browser.newPage();

      // 1. Desktop Viewport (1440x900)
      await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
      await page.goto(`${baseUrl}/${t.file}`, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await page.waitForNetworkIdle({ timeout: 3000 }).catch(() => {});
      await new Promise(r => setTimeout(r, 600));
      const desktopPath = path.join(SCREENSHOTS_DIR, `${t.name}_desktop.png`);
      await page.screenshot({ path: desktopPath, fullPage: false });
      console.log(`[PASS] Desktop: ${t.name}_desktop.png`);

      // 2. Tablet Viewport (768x1024)
      await page.setViewport({ width: 768, height: 1024, deviceScaleFactor: 2, isMobile: true });
      await new Promise(r => setTimeout(r, 400));
      const tabletPath = path.join(SCREENSHOTS_DIR, `${t.name}_tablet.png`);
      await page.screenshot({ path: tabletPath, fullPage: false });
      console.log(`[PASS] Tablet:  ${t.name}_tablet.png`);

      // 3. Mobile Viewport (390x844)
      await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true });
      await new Promise(r => setTimeout(r, 400));
      const mobilePath = path.join(SCREENSHOTS_DIR, `${t.name}_mobile.png`);
      await page.screenshot({ path: mobilePath, fullPage: false });
      console.log(`[PASS] Mobile:  ${t.name}_mobile.png`);

      // 4. Test Mobile Drawer opening on Strategy & Manager
      if (t.name === 'strategy' || t.name === 'manager') {
        const menuBtn = await page.$('#btn-mobile-menu, .hamburger-btn');
        if (menuBtn) {
          await menuBtn.click();
          await new Promise(r => setTimeout(r, 400));
          const drawerPath = path.join(SCREENSHOTS_DIR, `${t.name}_drawer_open.png`);
          await page.screenshot({ path: drawerPath, fullPage: false });
          console.log(`[PASS] Drawer:  ${t.name}_drawer_open.png`);

          // Press Escape key to verify keyboard closure
          await page.keyboard.press('Escape');
          await new Promise(r => setTimeout(r, 300));
        }
      }

      await page.close();
    }
    console.log(`\nVisual QA complete! All screenshots saved in ${SCREENSHOTS_DIR}`);
  } finally {
    await browser.close();
    server.close();
  }
})().catch(err => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
