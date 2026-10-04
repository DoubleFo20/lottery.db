const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const puppeteer = require('puppeteer-core');
const ROOT = path.resolve(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');
const realCsv = read('database/dataset/lottery_history.csv');
const realHistory = JSON.parse(read('database/predictions/prediction_history.json'));
const realCache = JSON.parse(read('database/predictions/pipeline_cache.json'));
const dates = ['2026-10-16', '2026-11-01', '2026-11-16', '2026-12-01', '2026-12-16', '2027-01-01'];
const sampleCsv = 'draw_date,first_prize\n2026-10-01,402701\n' +
  dates.map(date => date + ',123456').join('\n');
const sampleHistory = dates.map(date => ({
  target_date: date, draw_date_used: '2026-10-01',
  logged_at: date + 'T12:00:00', actual_result: '123456',
  candidates: [{ number: '000000' }],
}));

(async () => {
  let csv = realCsv;
  let history = realHistory;
  let cache = structuredClone(realCache);
  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    const fixtures = {
      '/database/dataset/lottery_history.csv': csv,
      '/database/predictions/prediction_history.json': JSON.stringify(history),
      '/database/predictions/pipeline_cache.json': JSON.stringify(cache),
    };
    if (Object.hasOwn(fixtures, pathname)) {
      response.setHeader('Cache-Control', 'no-store');
      response.writeHead(200, { 'Content-Type': 'text/plain' }).end(fixtures[pathname]);
      return;
    }
    const file = path.resolve(ROOT, '.' + pathname);
    if (!file.startsWith(ROOT + path.sep) || pathname.endsWith('.php') ||
        !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      response.writeHead(404).end();
      return;
    }
    response.setHeader('Content-Type', pathname.endsWith('.js') ? 'text/javascript' :
      pathname.endsWith('.html') ? 'text/html' : 'application/json');
    fs.createReadStream(file).pipe(response);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    const executablePath = process.env.CHROME_PATH || [
      'C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      '/usr/bin/google-chrome', '/usr/bin/chromium',
    ].find(file => fs.existsSync(file));
    assert(executablePath, 'Set CHROME_PATH');
    browser = await puppeteer.launch({ executablePath, headless: true });
    for (const route of ['manager.html', 'dashboard/manager.html']) {
      csv = realCsv; history = realHistory; cache = structuredClone(realCache);
      const context = await browser.createBrowserContext();
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.evaluateOnNewDocument(() => {
        Date.now = () => Date.parse('2027-02-01T00:00:00Z');
      });
      await page.goto('http://127.0.0.1:' + server.address().port + '/' + route);
      await page.waitForFunction(() => currentMissState.status === 'waiting');
      let text = await page.$eval('#consecutive-miss-alert-box', el => el.innerText);
      assert(text.includes('เริ่มรอบติดตามใหม่'));
      assert(!text.includes('Consecutive Draw Miss Advisory'));
      assert(!text.includes('เข้าเป้า 4 จาก 6'));

      csv = sampleCsv; history = structuredClone(sampleHistory);
      await page.evaluate(() => loadAll());
      assert.equal(await page.evaluate(() => currentMissState.misses), 6);
      text = await page.$eval('#consecutive-miss-alert-box', el => el.innerText);
      assert(text.includes('Consecutive Draw Miss Advisory'));
      history.at(-1).candidates = [{ number: '123456' }];
      await page.evaluate(() => loadAll());
      assert.equal(await page.evaluate(() => currentMissState.misses), 0);
      text = await page.$eval('#consecutive-miss-alert-box', el => el.innerText);
      assert(!text.includes('Consecutive Draw Miss Advisory'));

      cache.ensemble_weights.rolling_heat += 0.01;
      await page.evaluate(() => loadAll());
      assert.equal(await page.evaluate(() => currentMissState.status), 'waiting');
      assert.equal(await page.evaluate(() => currentMissState.afterDraw), '2027-01-01');
      await page.reload();
      await page.waitForFunction(() => currentMissState.afterDraw === '2027-01-01');
      assert.equal(await page.evaluate(() => currentMissState.status), 'waiting');
      assert.equal(errors.length, 0, errors.join('\n'));
      console.log('PASS:', route, 'reset, real streak, win, model change, persistence');
      await context.close();
    }
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
