// Playwright capture helper for design-doc HTML files.
//
// Usage:
//   node screenshot.js <abs-path-to-html> [out-dir] [--sample] [--print]
//
// Default (full sweep), to <out-dir> (default /tmp/doc-previews):
//   scroll-NN.png   full-width segments at a 1360px viewport, 2x DPR
// --sample: the hero viewport plus the first instance of each component
//   present, each capped at one segment: sample-00-hero.png, sample-NN-<component>.png
// --print: also writes doc.pdf with print media (A4) for a pagination check.
//
// Captures run with reduced motion, so scroll-reveal and typed text are
// already settled, and with every <details> opened, so collapsed content is
// checked too. Works on any HTML page; nothing depends on the template.

const path = require('path');
const fs = require('fs');
const { loadModule, fileUrl, parseArgs, CAPTURE_CSS } = require('./lib');

const { chromium } = loadModule('playwright');

const VIEWPORT_W = 1360;
const SEG_HEIGHT = 1400;
const SETTLE_MS = 1500;
const SCROLL_SETTLE_MS = 250;

const COMPONENTS = [
  ['metrics', '.metrics'],
  ['headline', '.headline'],
  ['entries', '.entries'],
  ['findings', '.findings'],
  ['panels', '.two-col'],
  ['timeline', '.timeline'],
  ['stages', '.stages'],
  ['table', '.table-wrap, table'],
  ['chart', 'figure.chart'],
  ['bars', '.bars'],
  ['diagram', 'figure.diagram'],
  ['figure', '.iso-figure'],
  ['decision', '.decision'],
  ['code', 'pre'],
  ['callout', '.callout'],
  ['questions', 'ol.numbered'],
  ['log', 'details'],
];

(async () => {
  const { positional, options } = parseArgs(process.argv.slice(2));
  const [arg, outDir = '/tmp/doc-previews'] = positional;
  if (!arg) {
    console.error('Usage: node screenshot.js <abs-path-to-html> [out-dir] [--sample] [--print]');
    process.exit(1);
  }
  fs.mkdirSync(outDir, { recursive: true });
  for (const name of fs.readdirSync(outDir)) {
    if (/^(scroll-\d+|sample-.+)\.png$|^doc\.pdf$/.test(name)) fs.unlinkSync(path.join(outDir, name));
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: VIEWPORT_W, height: SEG_HEIGHT },
    deviceScaleFactor: 2,
    colorScheme: 'dark',
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  await page.goto(fileUrl(arg), { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: CAPTURE_CSS });
  await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(SETTLE_MS);

  if (options.sample) {
    await page.screenshot({ path: path.join(outDir, 'sample-00-hero.png') });
    const found = ['hero'];
    let i = 1;
    for (const [label, selector] of COMPONENTS) {
      const el = page.locator(selector).first();
      if ((await el.count()) === 0) continue;
      await el.scrollIntoViewIfNeeded();
      const box = await el.boundingBox();
      const scrollY = await page.evaluate(() => window.scrollY);
      const pad = 24;
      await page.screenshot({
        path: path.join(outDir, `sample-${String(i++).padStart(2, '0')}-${label}.png`),
        fullPage: true,
        clip: { x: 0, y: Math.max(0, box.y + scrollY - pad), width: VIEWPORT_W, height: Math.min(box.height + 2 * pad, SEG_HEIGHT) },
      });
      found.push(label);
    }
    console.log(`sampled ${found.join(', ')}`);
  } else {
    const totalHeight = await page.evaluate(() => document.documentElement.scrollHeight);
    let count = 0;
    for (let y = 0; y < totalHeight; y += SEG_HEIGHT, count++) {
      await page.evaluate((scrollY) => window.scrollTo(0, scrollY), y);
      await page.waitForTimeout(SCROLL_SETTLE_MS);
      await page.screenshot({ path: path.join(outDir, `scroll-${String(count).padStart(2, '0')}.png`) });
    }
    console.log(`scrollHeight ${totalHeight}, ${count} segments`);
  }

  if (options.print) {
    await page.emulateMedia({ media: 'print' });
    await page.pdf({ path: path.join(outDir, 'doc.pdf'), format: 'A4', printBackground: true, preferCSSPageSize: true });
    console.log('wrote doc.pdf');
  }
  await browser.close();
  console.log('out:', outDir);
})();
