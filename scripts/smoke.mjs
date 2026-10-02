// Röktest: öppnar den byggda sidan i Chromium och kontrollerar att tabellen
// renderas, att sök och popup fungerar och att inga skriptfel uppstår.
// Biblioteken från CDN hämtas ur node_modules så att testet inte beror på nätet.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), '..');
const SITE = path.join(ROOT, '_site');
const LIBS = {
  'js-yaml': 'node_modules/js-yaml/dist/js-yaml.min.js',
  'marked': 'node_modules/marked/marked.min.js',
  'dompurify': 'node_modules/dompurify/dist/purify.min.js',
};
const TYPES = { '.html': 'text/html; charset=utf-8', '.yaml': 'text/yaml; charset=utf-8', '.js': 'text/javascript' };

const server = http.createServer((req, res) => {
  const p = path.join(SITE, decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/\/$/, '/index.html'));
  if (!p.startsWith(SITE) || !fs.existsSync(p)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0);
const url = `http://localhost:${server.address().port}/`;

const fail = [];
const check = (ok, msg) => { if (!ok) fail.push(msg); console.log(`${ok ? '✓' : '✗'} ${msg}`); };

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('https://cdn.jsdelivr.net/npm/**', route => {
    const name = Object.keys(LIBS).find(k => route.request().url().includes(`/npm/${k}@`));
    return name ? route.fulfill({ path: path.join(ROOT, LIBS[name]), contentType: 'text/javascript' }) : route.abort();
  });
  await page.route(/fonts\.(googleapis|gstatic)\.com|wikipedia\.org/, r => r.abort());

  await page.goto(url);
  await page.waitForSelector('li.has', { timeout: 15000 });
  const n = await page.$$eval('li.has', x => x.length);
  check(n > 1000, `tabellen visar ${n} punkter`);
  check(!(await page.textContent('footer')).includes('ej byggd'), 'fotnoten visar byggdatum');

  await page.fill('#q', 'elektricitet');
  await page.waitForTimeout(400);
  const hits = await page.textContent('#hits');
  check(/^\d+ träffar/.test(hits), `sökning ger träffar (${hits})`);
  await page.fill('#q', '');
  await page.waitForTimeout(400);

  await page.click('li.has');
  await page.waitForSelector('#pop:not([hidden]) .md p');
  check(true, 'popup öppnas med artikeltext');
  const ref = await page.$('#pop a.ref');
  check(!!ref, 'artikeln har en intern länk');
  if (ref) {
    const before = await page.textContent('#pop h2');
    await ref.click();
    await page.waitForTimeout(300);
    check((await page.textContent('#pop h2')) !== before, 'intern länk öppnar en annan artikel');
    check(!!(await page.$('#pop .back')), 'tillbaka-knappen visas');
  }

  await page.goto(url + '?direkt#' + (await page.evaluate(() => Object.keys(NODES)[5])));
  await page.waitForSelector('#pop:not([hidden]) h2', { timeout: 5000 });
  check(true, 'direktlänk med #id öppnar artikeln');

  check(errors.length === 0, `inga skriptfel${errors.length ? ': ' + errors.join('; ') : ''}`);
} finally {
  await browser.close();
  server.close();
}
if (fail.length) { console.error(`${fail.length} test misslyckades`); process.exit(1); }
