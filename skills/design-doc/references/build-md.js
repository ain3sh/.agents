// Renders a markdown report into a design-doc page styled by template.html
// (one stylesheet, one script, one logo; nothing here defines a second look).
//
// Usage:
//   node build-md.js <source.md> <out.html>
//     [--eyebrow="AC-123 · Retrospective · 2026-01-01"]   " · " becomes the // separators
//     [--title="<claim>"]         the h1; the source # Title becomes its .subtitle and stays the <title>
//     [--hero=<fragment.html>]    lede / linkline / chat / metrics, placed after the title
//     [--front=<fragment.html>]   curated layer (headline, findings, story) as <section data-nav="Label">;
//                                 the source then renders verbatim inside a collapsed "Full report"
//     [--footer=<fragment.html>]  provenance; default names the source file
//     [--log-dir=<dir>]           <dir>/<section-id>.html, when present, is that section's rewritten body;
//                                 an optional first line <!-- title: <claim> --> becomes its title
//     [--source-url=<url>]        links the source of record from the report's "About this report" note
//     [--linked-images]           keep images as relative links instead of base64
//
// Mapping (prose passes through marked unchanged; only layout is added):
//   # Title                 -> header.hero h1 (+ <title>); with --title, the h1's .subtitle
//   text before first ##    -> header.hero .preamble (with --front: the report's "About this report" note)
//   ## 3. Heading           -> section.block, .slabel "03 / Heading", h2   (or .chap "03" with --front)
//   ## Heading (unnumbered) -> section.block, h2                            (or an unnumbered .chap)
//   --front: the full report is a tile index (.tiles) plus one collapsed details.chap per section
//   ### / ####              -> h3 / h4 with ids
//   ![alt](img) + next-line *caption*  -> figure.diagram with figcaption
//   tables                  -> .table-wrap table; |---:| columns get .num; a cell
//                              starting with ↓ ↑ = · gets the effect-glyph span;
//                              4+ columns or a cell over 60 chars -> table.stack
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
  console.error('Usage: node build-md.js <source.md> <out.html> [--eyebrow=..] [--title=..] [--hero=f.html] [--front=f.html] [--footer=f.html] [--log-dir=dir] [--source-url=url] [--linked-images]');
  process.exit(1);
}
if (options.title === true || options.title === '') {
  console.error('--title needs a value: --title="<claim>"');
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
// Nav labels must fit a top bar: the heading up to its first clause break ("TL;DR" is not one).
const navLabel = (s) => s.replace(/[`*_]/g, '').split(/[:,(—]|;\s/)[0].trim();

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

// Wide or prose-heavy tables crush to one word per line on phones; stack them into cards instead.
const STACK_COLS = 4;
const STACK_CELL_CHARS = 60;
const wrapTable = (table) => {
  const cols = (table.match(/<thead>[\s\S]*?<\/thead>/)?.[0].match(/<th[\s>]/g) || []).length;
  const longCell = [...table.matchAll(/<td[^>]*>([\s\S]*?)<\/td>/g)]
    .some(([, cell]) => cell.replace(/<[^>]+>/g, '').length > STACK_CELL_CHARS);
  const open = cols >= STACK_COLS || longCell ? '<table class="stack">' : '<table>';
  return `<div class="table-wrap">${table.replace(/^<table>/, open)}</div>`;
};

const layout = (html) =>
  html
    .replace(/<h4>(.*?)<\/h4>/g, (_, t) => `<h4 id="${slug(t)}">${t}</h4>`)
    .replace(/<h3>(.*?)<\/h3>/g, (_, t) => `<h3 id="${slug(t)}">${t}</h3>`)
    .replace(/<table>[\s\S]*?<\/table>/g, wrapTable)
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

// A rewritten chapter (--log-dir) replaces the section's body outright; the markdown body is
// never emitted beside it, so ids stay unique. Sections without one keep the markdown.
const TITLE_LINE = /^<!--\s*title:\s*([\s\S]*?)\s*-->\s*\n?/;
const readRewrite = (id) => {
  const file = options['log-dir'] && path.join(path.resolve(options['log-dir']), `${id}.html`);
  if (!file || !fs.existsSync(file)) return null;
  const html = fs.readFileSync(file, 'utf8');
  const title = html.match(TITLE_LINE);
  return { title: title ? title[1] : '', body: html.replace(TITLE_LINE, '').trim() };
};

const sections = chunks.map((chunk) => {
  const nl = chunk.indexOf('\n');
  const heading = chunk.slice(0, nl).trim();
  const numbered = heading.match(/^(\d+)\.\s+(.*)$/);
  const text = numbered ? numbered[2] : heading;
  const id = slug(heading);
  const rewrite = readRewrite(id);
  return {
    id,
    num: numbered ? pad2(numbered[1]) : '',
    text,
    rewritten: Boolean(rewrite),
    // A rewrite's claim title leads; the source heading stays as the secondary line.
    display: rewrite && rewrite.title ? rewrite.title : marked.parseInline(text),
    sourceHeading: rewrite && rewrite.title ? text : '',
    body: rewrite ? rewrite.body : layout(marked.parse(withFigures(chunk.slice(nl + 1)))),
  };
});
if (options['log-dir']) {
  const missing = sections.filter((s) => !s.rewritten).map((s) => s.id);
  console.log(`log-dir: ${sections.length - missing.length}/${sections.length} sections rewritten${missing.length ? `; markdown for ${missing.join(', ')}` : ''}`);
}

const front = readFragment(options.front);
const frontNav = [...front.matchAll(/<section[^>]*\bid="([^"]+)"[^>]*\bdata-nav="([^"]+)"|<section[^>]*\bdata-nav="([^"]+)"[^>]*\bid="([^"]+)"/g)]
  .map((m) => ({ id: m[1] || m[4], label: m[2] || m[3] }));

// ---------- full report (--front): a tile index, then one collapsed chapter per source section
const WORDS_PER_MINUTE = 230;
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const countOf = (html, re) => (html.match(re) || []).length;

// "6 min · 4 tables · 2 figures", counted from the body; zero counts are left out. Figure
// placeholders (<!-- viz-NN -->, <!-- chart-log:… -->) are filled after the build, so they count too.
const FIGURE_PLACEHOLDER = /<!--\s*(?:viz-\d+|chart-log:)/g;
const chapterMeta = (body) => {
  const words = body.replace(/<!--[\s\S]*?-->/g, ' ').replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;
  const tables = countOf(body, /<table[\s>]/g);
  const figures = countOf(body, /<figure[\s>]/g) + countOf(body, FIGURE_PLACEHOLDER);
  return [
    `${Math.max(1, Math.round(words / WORDS_PER_MINUTE))} min`,
    tables && plural(tables, 'table'),
    figures && plural(figures, 'figure'),
  ].filter(Boolean).join(' · ');
};
// Unnumbered sections get an empty slot (the template draws a neutral dot), never a positional
// number, so "§7" in the prose matches the page.
const chapterMark = (s) => (s.num ? `§${Number(s.num)}` : '');
const stripMarks = (s) => s.replace(/[`*_]/g, '');
// The marker line: "§3", or with a claim title, "§3 · The arc, block by block" (the source heading).
const markerLine = (s) => [chapterMark(s), escapeHtml(stripMarks(s.sourceHeading))].filter(Boolean).join(' · ');
// A tile's marker splits so phones can keep the number and drop the source heading.
const tileMarker = (s) => {
  const mark = chapterMark(s);
  const heading = s.sourceHeading ? `<span class="tile-h">${mark ? ' · ' : ''}${escapeHtml(stripMarks(s.sourceHeading))}</span>` : '';
  return `<span class="tile-s">${mark}</span>${heading}`;
};
const tileTitle = (s) => (s.sourceHeading ? s.display.replace(/<[^>]+>/g, '') : escapeHtml(stripMarks(s.text)));

const tileHtml = (s) =>
  `<a class="tile" href="#${s.id}"><span class="tile-n">${tileMarker(s)}</span><span class="tile-t">${tileTitle(s)}</span><span class="tile-m">${s.meta}</span></a>`;

const tileGroup = (group, label = '', note = '') => {
  if (group.length === 0) return '';
  const heading = label ? `<div class="tiles-label">${label}${note ? ` <span>${note}</span>` : ''}</div>\n  ` : '';
  return `  ${heading}<nav class="tiles" aria-label="${label || 'Report sections'}">${group.map(tileHtml).join('')}</nav>\n`;
};

const chapterHtml = (s) => `  <details class="chap" id="${s.id}">
    <summary><span class="chn">${markerLine(s)}</span><span class="cht">${s.display}</span><span class="chm">${s.meta}</span></summary>
    <div class="chb">
${s.body}
    </div>
  </details>`;

const reportLine = () => {
  const rewritten = sections.filter((s) => s.rewritten).length;
  const count = plural(sections.length, 'section');
  if (rewritten === sections.length) return `Every section of the source report, rewritten and checked against it: ${count}`;
  if (rewritten === 0) return `The source report, verbatim: ${count}`;
  return `The source report: ${count}, ${rewritten} rewritten and checked against it, the rest verbatim`;
};

const aboutHtml = () => {
  const link = options['source-url']
    ? `<p class="report-src"><a href="${escapeHtml(options['source-url'])}">Source of record</a></p>`
    : '';
  if (!preamble && !link) return '';
  return `  <aside class="report-about"><div class="lhead">About this report</div>${preamble ? layout(marked.parse(preamble)) : ''}${link}</aside>\n`;
};

const reportHtml = () => {
  for (const s of sections) s.meta = chapterMeta(s.body);
  const unnumbered = sections.filter((s) => !s.num);
  const numbered = sections.filter((s) => s.num);
  // "Curated above" holds only while unnumbered sections render verbatim under a front that
  // distils them; once every section is rewritten, one grid in source order tells no one to skip.
  const grouped = unnumbered.length > 0 && numbered.length > 0 && sections.some((s) => !s.rewritten);
  return `<section class="block report" id="log" data-nav="Full report">
  <div class="slabel">Source</div>
  <h2>The full report</h2>
  <div class="report-bar">
    <p>${reportLine()}</p>
    <button type="button" class="report-toggle">Expand all</button>
  </div>
${grouped ? tileGroup(unnumbered, 'Front matter', 'curated above') + tileGroup(numbered, 'Chapters') : tileGroup(sections)}${aboutHtml()}  <div class="chapters">
${sections.map(chapterHtml).join('\n')}
  </div>
</section>`;
};

const bodyHtml = front
  ? `${front}
${reportHtml()}`
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
${eyebrow}    <h1>${options.title
  ? `${marked.parseInline(options.title)}<span class="subtitle">${marked.parseInline(titleMatch[1])}</span>`
  : marked.parseInline(titleMatch[1])}</h1>
${readFragment(options.hero)}
${preamble && !front ? `    <div class="preamble">${layout(marked.parse(preamble))}</div>` : ''}
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
