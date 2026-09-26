// Renders a markdown report into a design-doc HTML file styled by
// template.html's stylesheet (one visual system, no second CSS).
//
// Usage:
//   node build-md.js <source.md> <out.html>
//     [--eyebrow="AC-123 · Retrospective · 2026-01-01"]
//     [--hero=<fragment.html>]     tagline / linkline / statband / panels, placed after the title
//     [--footer=<fragment.html>]   provenance; default names the source file
//     [--linked-images]            keep images as relative links instead of base64
//
// Mapping (prose passes through marked unchanged; only layout is added):
//   # Title                 -> header.doc h1.title (+ <title>)
//   text before first ##    -> header.doc .preamble
//   ## 3. Heading           -> section.block: h2 ".num §3" eyebrow + h3 display heading
//   ## Heading (unnumbered) -> section.block: h2 rule + h3 display heading
//   ### / ####              -> h4 / h5 with ids
//   ![alt](img) + next-line *caption*  -> figure.diagram with figcaption
//   tables                  -> table.kv in a scrolling .table-wrap; a cell that
//                              starts with ↓ ↑ = · gets the effect-glyph span
//   ul / ol                 -> ul.bullets / ol.numbered
//
// marked resolves like playwright (see lib.js); `npm i marked` in /tmp if absent.

const fs = require('fs');
const path = require('path');
const { loadModule, parseArgs } = require('./lib');

const { marked } = loadModule('marked');

const { positional, options } = parseArgs(process.argv.slice(2));
const [srcArg, outArg] = positional;
if (!srcArg || !outArg) {
  console.error('Usage: node build-md.js <source.md> <out.html> [--eyebrow=..] [--hero=f.html] [--footer=f.html] [--linked-images]');
  process.exit(1);
}
const src = path.resolve(srcArg);
const out = path.resolve(outArg);
const srcDir = path.dirname(src);

const template = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');
const style = template.match(/<style>[\s\S]*?<\/style>/)[0];
const fontLinks = template.match(/<link rel="preconnect"[\s\S]*?rel="stylesheet"\s*\/>/)[0];

const escapeHtml = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const slug = (s) => s.toLowerCase().replace(/<[^>]+>/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const readFragment = (f) => (f ? fs.readFileSync(path.resolve(f), 'utf8') : '');

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
    .replace(/<h4>(.*?)<\/h4>/g, (_, t) => `<h5 id="${slug(t)}">${t}</h5>`)
    .replace(/<h3>(.*?)<\/h3>/g, (_, t) => `<h4 id="${slug(t)}">${t}</h4>`)
    .replace(/<table>/g, '<div class="table-wrap"><table class="kv">')
    .replace(/<\/table>/g, '</table></div>')
    .replace(/<td([^>]*)>(↓|↑|=|·)/g, (_, attrs, g) => `<td${attrs}><span class="g g-${GLYPH[g]}">${g}</span>`)
    .replace(/<ul>/g, '<ul class="bullets">')
    .replace(/<ol>/g, '<ol class="numbered">');

const source = fs.readFileSync(src, 'utf8');
const [head, ...chunks] = source.split(/^## /m);
const titleMatch = head.match(/^# (.+)$/m);
if (!titleMatch) {
  console.error(`${srcArg}: no "# Title" line before the first "## " section`);
  process.exit(1);
}
const title = marked.parseInline(titleMatch[1]);
const preamble = head.replace(/^# .+$/m, '').trim();

const sections = chunks.map((chunk) => {
  const nl = chunk.indexOf('\n');
  const heading = chunk.slice(0, nl).trim();
  const numbered = heading.match(/^(\d+)\.\s+(.*)$/);
  return {
    id: slug(heading),
    heading,
    num: numbered ? `<span class="num">§${numbered[1]}</span>` : '',
    display: marked.parseInline(numbered ? numbered[2] : heading),
    body: layout(marked.parse(withFigures(chunk.slice(nl + 1)))),
  };
});

// The collapsed 68px rail fits roman numerals up to four characters (XVII).
if (sections.length > 17) console.warn(`warning: ${sections.length} sections; the TOC rail clips numerals past XVII`);

const footer =
  readFragment(options.footer) ||
  `<p>Source: <code>${escapeHtml(path.basename(src))}</code> · rendered ${new Date().toISOString().slice(0, 10)}</p>`;

const doc = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${titleMatch[1].replace(/[`*_]/g, '')}</title>
${fontLinks}
${style}
</head>
<body>
<div class="page">
<nav class="toc" aria-label="Table of contents">
  <p class="toc-label">Contents</p>
  <ol>
${sections.map((s) => `    <li><a href="#${s.id}">${marked.parseInline(s.heading)}</a></li>`).join('\n')}
  </ol>
</nav>
<main>
<header class="doc">
${options.eyebrow ? `  <p class="eyebrow">${escapeHtml(options.eyebrow)}</p>\n` : ''}  <h1 class="title">${title}</h1>
${readFragment(options.hero)}
${preamble ? `  <div class="preamble">${layout(marked.parse(preamble))}</div>` : ''}
</header>
${sections
  .map((s) => `<section class="block" id="${s.id}">
  <h2>${s.num}</h2>
  <h3>${s.display}</h3>
${s.body}
</section>`)
  .join('\n')}
<footer class="doc">
${footer}
</footer>
</main>
</div>
</body>
</html>
`;

fs.writeFileSync(out, doc);
const kb = Buffer.byteLength(doc) / 1024;
console.log(`wrote ${out} (${kb.toFixed(0)} KB, ${sections.length} sections)`);
if (kb > 1000) {
  console.warn(
    'warning: over ~1 MB; the gist API will truncate it. Shrink flat charts with\n' +
    "  magick in.png -resize '1400x>' -colors 128 out.png\n" +
    'or rebuild with --linked-images for local viewing.',
  );
}
