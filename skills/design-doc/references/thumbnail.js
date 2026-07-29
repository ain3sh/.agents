// Hero-thumbnail capture for design-doc HTML files.
//
// Usage:
//   node thumbnail.js <abs-path-to-html> [out.png] [ratio]
//
// Produces a wide, dark-mode crop of the document hero (eyebrow → title →
// tagline → stat band) for pasting into chat/tickets alongside the doc link.
// Default 1.6:1 so chat clients don't letterbox it.
//
// The crop rules exist because naive full-page captures look wrong:
//   - the auto-hide TOC rail renders as a stray column of numerals
//   - whatever follows the hero (callout panels, demo card) bleeds a sliver
//     of accent color into the bottom edge
//   - the header is narrower than the stat band, so centering on the header
//     leaves the image visibly off-center
//
// Dependencies: same playwright resolution as screenshot.js.

const path = require('path');

// See screenshot.js: bare require() resolves from THIS FILE, not the CWD,
// so we walk up from the invocation directory to find playwright.
function loadPlaywright() {
  const candidates = ['playwright'];

  for (const envDir of [process.env.PLAYWRIGHT_NODE_MODULES, process.env.NODE_PATH]) {
    for (const entry of (envDir || '').split(path.delimiter).filter(Boolean)) {
      candidates.push(path.join(entry, 'playwright'));
    }
  }

  for (let dir = process.cwd(); ; dir = path.dirname(dir)) {
    candidates.push(path.join(dir, 'node_modules', 'playwright'));
    if (dir === path.dirname(dir)) break;
  }

  candidates.push(
    '/tmp/node_modules/playwright',
    '/usr/lib/node_modules/playwright',
    '/usr/local/lib/node_modules/playwright',
  );

  for (const c of candidates) {
    try { return require(c); } catch (_) { /* try next */ }
  }
  console.error(
    'playwright not found. Run from (or under) a project that has it installed,\n' +
    'or set PLAYWRIGHT_NODE_MODULES=/abs/path/to/node_modules,\n' +
    'or: cd /tmp && npm i playwright && npx playwright install chromium',
  );
  process.exit(1);
}
const { chromium } = loadPlaywright();

const VIEWPORT_W = 1800;
const VIEWPORT_H = 1700;
const PAD = 56;

(async () => {
  const src = process.argv[2];
  const out = process.argv[3] || '/tmp/doc-thumb.png';
  const ratio = Number(process.argv[4]) || 1.6;
  if (!src) {
    console.error('Usage: node thumbnail.js <abs-path-to-html> [out.png] [ratio]');
    process.exit(1);
  }

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    colorScheme: 'dark',
    viewport: { width: VIEWPORT_W, height: VIEWPORT_H },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  await page.goto(src.startsWith('file://') ? src : `file://${src}`);
  await page.waitForTimeout(2500);

  // The TOC rail is chrome, not content.
  await page.addStyleTag({ content: 'nav.toc{display:none!important}' });

  const box = await page.evaluate(({ pad, ratio, vw }) => {
    const header = document.querySelector('header.doc');
    if (!header) return null;

    // Bottom anchor: stat band in memo mode, else the tagline/meta strip.
    const anchor =
      header.querySelector('.statband') ||
      header.querySelector('.meta') ||
      header.querySelector('.tagline') ||
      header;

    // Hide everything after the anchor so no accent sliver bleeds in.
    let n = anchor.nextElementSibling;
    while (n) { n.style.display = 'none'; n = n.nextElementSibling; }

    const rh = header.getBoundingClientRect();
    const ra = anchor.getBoundingClientRect();
    const top = rh.top - pad;
    const h = ra.bottom + pad - top;

    // Center on the widest element, not the header — they differ.
    const wide = ra.width > rh.width ? ra : rh;
    const cx = (wide.left + wide.right) / 2;
    const w = Math.min(h * ratio, vw);

    return { x: Math.max(0, cx - w / 2), y: Math.max(0, top), w, h };
  }, { pad: PAD, ratio, vw: VIEWPORT_W });

  if (!box) {
    console.error('no <header class="doc"> found — is this a design-doc HTML file?');
    process.exit(1);
  }

  await page.screenshot({
    path: out,
    clip: { x: box.x, y: box.y, width: box.w, height: box.h },
  });
  await ctx.close();
  await browser.close();

  console.log(
    `wrote ${out} — ${Math.round(box.w * 2)}x${Math.round(box.h * 2)}px @2x, ratio ${(box.w / box.h).toFixed(2)}`,
  );
})();
