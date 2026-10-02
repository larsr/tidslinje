// Bygger sajten till _site/: kopierar index.html och data/ och skriver in
// datumet för senaste commit som "Senast uppdaterad" i fotnoten.
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), '..');
const OUT = path.join(ROOT, '_site');

let when;
try { when = new Date(execSync('git log -1 --format=%cI', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()); }
catch { when = new Date(); }
if (isNaN(when)) when = new Date();
const stamp = new Intl.DateTimeFormat('sv-SE', {
  dateStyle: 'long', timeStyle: 'short', timeZone: 'Europe/Stockholm',
}).format(when);

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8')
  .replace(/<!--UPDATED-->[\s\S]*?<!--\/UPDATED-->/, `<time datetime="${when.toISOString()}">${stamp}</time>`);
fs.writeFileSync(path.join(OUT, 'index.html'), html);
fs.cpSync(path.join(ROOT, 'data'), path.join(OUT, 'data'), { recursive: true });
fs.writeFileSync(path.join(OUT, '.nojekyll'), '');
console.log(`Byggt till _site/ (senast uppdaterad ${stamp}).`);
