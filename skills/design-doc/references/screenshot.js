// Playwright capture helper for design-doc HTML files.
//
// Usage:
//   node screenshot.js <abs-path-to-html> [out-dir] [--sample]
//
// Default (full sweep), to <out-dir> (default /tmp/doc-previews):
//   scroll-light-NN.png   full-width segments at 1360px viewport, 2x DPR
//   scroll-dark-NN.png    matching dark-mode segments
//   hero-dark-v2.png      alias for scroll-dark-00.png
//
// --sample: instead of the sweep, capture the hero viewport plus the first
// instance of each component type present (table, figure, code, statband,
// panels, decision card, callout, pull quote, numbered list), in both schemes:
//   sample-<scheme>-00-hero.png, sample-<scheme>-NN-<component>.png
// Each capture is capped at one segment height.
//
// Works on any HTML page; nothing here depends on the template's markup.

const path = require('path');
const fs = require('fs');
const { loadModule, fileUrl, parseArgs, CAPTURE_CSS } = require('./lib');

const { chromium } = loadModule('playwright');

const VIEWPORT_W = 1360;
const SEG_HEIGHT = 1400;
const SETTLE_MS = 1800;
const SCROLL_SETTLE_MS = 350;

const COMPONENTS = [
  ['statband', '.statband'],
  ['panels', '.two-col'],
  ['table', 'table'],
  ['figure', 'figure'],
  ['code', 'pre'],
  ['decision', '.decision'],
  ['callout', '.callout'],
  ['pullquote', '.pullquote'],
  ['list', 'ol.numbered'],
];

(async () => {
  const { positional, options } = parseArgs(process.argv.slice(2));
  const [arg, outDir = '/tmp/doc-previews'] = positional;
  if (!arg) {
    console.error('Usage: node screenshot.js <abs-path-to-html> [out-dir] [--sample]');
    process.exit(1);
  }
  fs.mkdirSync(outDir, { recursive: true });
  for (const name of fs.readdirSync(outDir)) {
    if (/^(scroll-(light|dark)-\d+|hero-dark-v2|sample-(light|dark)-.+)\.png$/.test(name)) {
      fs.unlinkSync(path.join(outDir, name));
    }
  }

  const browser = await chromium.launch();

  async function openPage(colorScheme) {
    const context = await browser.newContext({
      viewport: { width: VIEWPORT_W, height: SEG_HEIGHT },
      deviceScaleFactor: 2,
      colorScheme,
    });
    const page = await context.newPage();
    await page.goto(fileUrl(arg), { waitUntil: 'networkidle' });
    await page.addStyleTag({ content: CAPTURE_CSS });
    await page.waitForTimeout(SETTLE_MS);
    return { context, page };
  }

  async function sweep(colorScheme) {
    const { context, page } = await openPage(colorScheme);
    const totalHeight = await page.evaluate(() => document.documentElement.scrollHeight);
    let count = 0;
    for (let y = 0; y < totalHeight; y += SEG_HEIGHT, count++) {
      await page.evaluate((scrollY) => window.scrollTo(0, scrollY), y);
      await page.waitForTimeout(SCROLL_SETTLE_MS);
      const name = String(count).padStart(2, '0');
      await page.screenshot({ path: path.join(outDir, `scroll-${colorScheme}-${name}.png`) });
    }
    console.log(`${colorScheme}: scrollHeight ${totalHeight}, ${count} segments`);
    await context.close();
  }

  async function sample(colorScheme) {
    const { context, page } = await openPage(colorScheme);
    await page.screenshot({ path: path.join(outDir, `sample-${colorScheme}-00-hero.png`) });
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
        path: path.join(outDir, `sample-${colorScheme}-${String(i++).padStart(2, '0')}-${label}.png`),
        fullPage: true,
        clip: {
          x: 0,
          y: Math.max(0, box.y + scrollY - pad),
          width: VIEWPORT_W,
          height: Math.min(box.height + 2 * pad, SEG_HEIGHT),
        },
      });
      found.push(label);
    }
    console.log(`${colorScheme}: sampled ${found.join(', ')}`);
    await context.close();
  }

  for (const scheme of ['light', 'dark']) {
    await (options.sample ? sample(scheme) : sweep(scheme));
  }
  if (!options.sample) {
    fs.copyFileSync(path.join(outDir, 'scroll-dark-00.png'), path.join(outDir, 'hero-dark-v2.png'));
  }
  await browser.close();
  console.log('out:', outDir);
})();
