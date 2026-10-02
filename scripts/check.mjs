// Kontrollerar att datat i data/ är konsistent: giltig YAML, unika id:n,
// giltiga perioder, att same_as och alla [text](#id)-länkar pekar på noder som finns,
// och att Markdown-texten inte innehåller rå HTML.
import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';
import { marked } from 'marked';

const DATA = path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'data');
const errors = [];
const err = (f, id, msg) => errors.push(`${f}${id ? ` [${id}]` : ''}: ${msg}`);

const load = f => {
  try { return yaml.load(fs.readFileSync(path.join(DATA, f), 'utf8')); }
  catch (e) { err(f, '', `ogiltig YAML: ${e.message}`); return null; }
};

const index = load('index.yaml');
if (!index) { console.error(errors.join('\n')); process.exit(1); }
const { start, slut, steg } = index.perioder;
const periods = new Set();
for (let y = start; y <= slut; y += steg) periods.add(y);

const nodes = new Map();
const colIds = new Set();
for (const c of index.kolumner) {
  if (typeof c.id !== 'string' || !/^[a-z][a-z0-9-]*$/.test(c.id)) err('index.yaml', c.id, 'ogiltigt kolumn-id');
  if (colIds.has(c.id)) err('index.yaml', c.id, 'kolumnen finns två gånger');
  colIds.add(c.id);
  const f = `${c.id}.yaml`;
  if (!fs.existsSync(path.join(DATA, f))) { err(f, '', 'filen saknas'); continue; }
  const d = load(f) || {};
  for (const [id, n] of Object.entries(d)) {
    if (!/^[a-z][a-z0-9-]*$/.test(id)) err(f, id, 'id måste bestå av a-z, 0-9 och bindestreck och börja med en bokstav');
    if (nodes.has(id)) err(f, id, `id:t används redan i ${nodes.get(id).file}`);
    if (!n || typeof n !== 'object') { err(f, id, 'noden är tom'); continue; }
    if (!periods.has(n.period)) err(f, id, `ogiltig period ${n.period}`);
    if (typeof n.label !== 'string' || !n.label.trim()) err(f, id, 'label saknas');
    if (!n.same_as) {
      if (typeof n.title !== 'string') err(f, id, 'title saknas');
      if (typeof n.text !== 'string' || !n.text.trim()) err(f, id, 'text saknas');
      for (const w of n.wiki || []) if (!/^[a-z]{2,3}:.+/.test(w)) err(f, id, `ogiltig wiki-post "${w}" (ska vara språk:Artikel)`);
    }
    nodes.set(id, { ...n, file: f });
  }
}

let links = 0;
const linked = new Set();
for (const [id, n] of nodes) {
  if (n.same_as && !nodes.has(n.same_as)) err(n.file, id, `same_as pekar på okänd nod "${n.same_as}"`);
  if (!n.text) continue;
  const tokens = marked.lexer(n.text);
  marked.walkTokens(tokens, t => {
    if (t.type === 'html') err(n.file, id, `rå HTML i texten: ${t.raw.trim().slice(0, 40)}`);
    if (t.type === 'link' && t.href.startsWith('#')) {
      links++;
      const target = t.href.slice(1);
      if (!nodes.has(target)) err(n.file, id, `länk till okänd nod "#${target}"`);
      else if (target === id) err(n.file, id, 'noden länkar till sig själv');
      linked.add(target);
    }
  });
}

if (errors.length) {
  console.error(`${errors.length} fel:\n` + errors.join('\n'));
  process.exit(1);
}
console.log(`OK: ${colIds.size} kolumner, ${nodes.size} noder, ${links} interna länkar.`);
