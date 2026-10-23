// Renders a markdown report into a design-doc page styled by template.html
// (one stylesheet, one script, one logo; nothing here defines a second look).
//
// Usage:
//   node build-md.js <source.md> <out.html>
//     [--eyebrow="AC-123 · Retrospective · 2026-01-01"]   " · " becomes the // separators
//     [--hero=<fragment.html>]    lede / linkline / chat / metrics, placed after the title
//     [--front=<fragment.html>]   curated layer (headline, findings, story) as <section data-nav="Label">;
//                                 the source then renders verbatim inside a collapsed "Full report"
//     [--footer=<fragment.html>]  provenance; default names the source file
//     [--linked-images]           keep images as relative links instead of base64
//
// Mapping (prose passes through marked unchanged; only layout is added):
//   # Title                 -> header.hero h1 (+ <title>)
//   text before first ##    -> header.hero .preamble
//   ## 3. Heading           -> section.block, .slabel "03 / Heading", h2   (or .chap "03" with --front)
//   ## Heading (unnumbered) -> section.block, h2
//   ### / ####              -> h3 / h4 with ids
//   ![alt](img) + next-line *caption*  -> figure.diagram with figcaption
//   tables                  -> .table-wrap table; |---:| columns get .num; a cell
//                              starting with ↓ ↑ = · gets the effect-glyph span
//   ul / ol / blockquote / fenced code -> ul.bullets / ol.steps / .callout / pre.code
//
// marked resolves like playwright (see lib.js): `npm i -g marked` if absent.

const fs = require('fs');
const path = require('path');
const { loadModule, parseArgs } = require('./lib');

const { marked } = loadModule('marked');

const { positional, options } = parseArgs(process.argv.slice(2));
const [srcArg, outArg] = positional;
if (!srcArg || !outArg) {
  console.error('Usage: node build-md.js <source.md> <out.html> [--eyebrow=..] [--hero=f.html] [--front=f.html] [--footer=f.html] [--linked-images]');
  process.exit(1);
}
const src = path.resolve(srcArg);
const out = path.resolve(outArg);
const srcDir = path.dirname(src);

const template = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');
const pick = (re, what) => {
  const m = template.match(re);
  if (!m) throw new Error(`template.html: ${what} not found`);
  return m[0];
};
const fontLinks = pick(/<link rel="preconnect"[\s\S]*?rel="stylesheet" \/>/, 'font links');
const style = pick(/<style>[\s\S]*?<\/style>/, '<style>');
const logo = pick(/<a href="#top">[\s\S]*?<\/a>/, 'logo link');
const script = pick(/<script>[\s\S]*?<\/script>/, '<script>');

const escapeHtml = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const slug = (s) => s.toLowerCase().replace(/<[^>]+>/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const readFragment = (f) => (f ? fs.readFileSync(path.resolve(f), 'utf8') : '');
const pad2 = (n) => String(n).padStart(2, '0');
// Nav labels must fit a top bar: the heading up to its first clause break.
const navLabel = (s) => s.replace(/[`*_]/g, '').split(/[:,;(—]/)[0].trim();

const imageSrc = (ref) => {
  const abs = path.resolve(srcDir, ref);
  if (options['linked-images']) return path.relative(path.dirname(out), abs);
  const ext = path.extname(abs).slice(1).toLowerCase();
  const mime = { svg: 'image/svg+xml', jpg: 'image/jpeg', jpeg: 'image/jpeg' }[ext] || `image/${ext}`;
  return `data:${mime};base64,${fs.readFileSync(abs).toString('base64')}`;
};

const withFigures = (md) =>
  md.replace(/^!\[([^\]]*)\]\(([^)]+)\)\n\*(.+?)\*$/gm, (_, alt, ref, caption) =>
    `<figure class="diagram"><img src="${imageSrc(ref)}" alt="${escapeHtml(alt)}" /><figcaption>${marked.parseInline(caption)}</figcaption></figure>\n`);

const GLYPH = { '↓': 'down', '↑': 'up', '=': 'flat', '·': 'na' };

const layout = (html) =>
  html
    .replace(/<h4>(.*?)<\/h4>/g, (_, t) => `<h4 id="${slug(t)}">${t}</h4>`)
    .replace(/<h3>(.*?)<\/h3>/g, (_, t) => `<h3 id="${slug(t)}">${t}</h3>`)
    .replace(/<table>/g, '<div class="table-wrap"><table>')
    .replace(/<\/table>/g, '</table></div>')
    .replace(/<(td|th) align="right">/g, '<$1 class="num">')
    .replace(/<(td|th) align="(left|center)">/g, '<$1>')
    .replace(/<td([^>]*)>(↓|↑|=|·)/g, (_, attrs, g) => `<td${attrs}><span class="g g-${GLYPH[g]}">${g}</span>`)
    .replace(/<ul>/g, '<ul class="bullets">')
    .replace(/<ol>/g, '<ol class="steps">')
    .replace(/<blockquote>/g, '<div class="callout">')
    .replace(/<\/blockquote>/g, '</div>')
    .replace(/<pre><code[^>]*>/g, '<pre class="code"><code>');

const source = fs.readFileSync(src, 'utf8');
const [head, ...chunks] = source.split(/^## /m);
const titleMatch = head.match(/^# (.+)$/m);
if (!titleMatch) {
  console.error(`${srcArg}: no "# Title" line before the first "## " section`);
  process.exit(1);
}
const preamble = head.replace(/^# .+$/m, '').trim();

const sections = chunks.map((chunk, i) => {
  const nl = chunk.indexOf('\n');
  const heading = chunk.slice(0, nl).trim();
  const numbered = heading.match(/^(\d+)\.\s+(.*)$/);
  const text = numbered ? numbered[2] : heading;
  return {
    id: slug(heading),
    num: numbered ? pad2(numbered[1]) : null,
    index: pad2(i + 1),
    text,
    display: marked.parseInline(text),
    body: layout(marked.parse(withFigures(chunk.slice(nl + 1)))),
  };
});

const front = readFragment(options.front);
const frontNav = [...front.matchAll(/<section[^>]*\bid="([^"]+)"[^>]*\bdata-nav="([^"]+)"|<section[^>]*\bdata-nav="([^"]+)"[^>]*\bid="([^"]+)"/g)]
  .map((m) => ({ id: m[1] || m[4], label: m[2] || m[3] }));

const bodyHtml = front
  ? `${front}
<section class="block" id="log" data-nav="Full report">
  <div class="slabel">Source</div>
  <h2>The full report</h2>
  <details class="log">
    <summary>Show all ${sections.length} sections, verbatim</summary>
${sections.map((s) => `    <section class="chap" id="${s.id}"><div class="chn">${s.num || s.index}</div><div class="chb"><h2>${s.display}</h2>
${s.body}
    </div></section>`).join('\n')}
  </details>
</section>`
  : sections.map((s) => `<section class="block" id="${s.id}">
  ${s.num ? `<div class="slabel">${s.num} / ${escapeHtml(navLabel(s.text))}</div>\n  ` : ''}<h2>${s.display}</h2>
${s.body}
</section>`).join('\n');

const nav = front
  ? [...frontNav, { id: 'log', label: 'Full report' }]
  : sections.map((s) => ({ id: s.id, label: navLabel(s.text) }));
if (front && frontNav.length === 0) console.warn('warning: --front has no <section id=".." data-nav=".."> elements; the nav lists only "Full report"');

const eyebrow = options.eyebrow
  ? `    <p class="eyebrow">${options.eyebrow.split(' · ').map(escapeHtml).join('<span class="sep">//</span>')}</p>\n`
  : '';
const footer =
  readFragment(options.footer) ||
  `Source: <code>${escapeHtml(path.basename(src))}</code>. Rendered ${new Date().toISOString().slice(0, 10)}.`;

const doc = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(titleMatch[1].replace(/[`*_]/g, ''))}</title>
${fontLinks}
${style}
</head>
<body class="nojs">
<header class="top">
  <div class="wrap toprow">
    ${logo}
    <nav aria-label="Sections">${nav.map((n) => `<a href="#${n.id}">${escapeHtml(n.label)}</a>`).join('')}</nav>
  </div>
</header>
<header class="hero" id="top">
  <div class="hero-art" aria-hidden="true"></div>
  <div class="wrap">
${eyebrow}    <h1>${marked.parseInline(titleMatch[1])}</h1>
${readFragment(options.hero)}
${preamble ? `    <div class="preamble">${layout(marked.parse(preamble))}</div>` : ''}
  </div>
</header>
<main class="wrap">
${bodyHtml}
<footer class="doc"><span class="frotor" aria-hidden="true"></span><div>${footer}</div></footer>
</main>
${script}
</body>
</html>
`;

fs.writeFileSync(out, doc);
const kb = Buffer.byteLength(doc) / 1024;
console.log(`wrote ${out} (${kb.toFixed(0)} KB, ${sections.length} sections${front ? ', collapsed under a curated front' : ''})`);
if (kb > 1000) {
  console.warn(
    'warning: over ~1 MB; a gist would truncate it (conjure does not). Redraw charts as in-page SVG, or shrink rasters with\n' +
    "  magick in.png -resize '1400x>' -colors 128 out.png",
  );
}
