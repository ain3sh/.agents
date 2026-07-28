// Playwright capture helper for design-doc HTML files.
//
// Usage:
//   node screenshot.js <abs-path-to-html> [out-dir]
//
// Outputs to <out-dir> (default /tmp/doc-previews):
//   scroll-light-NN.png   — full-width segments at 1400px viewport, 2x DPR, light mode
//   scroll-dark-NN.png    — matching full-page dark-mode segments
//   hero-dark-v2.png      — compatibility alias for scroll-dark-00.png
//
// Dependencies: requires `playwright` resolvable. The script searches
// node_modules in CWD, then /tmp/node_modules, then global. If missing:
//   cd /tmp && npm i playwright && npx playwright install chromium
//
// Then read each PNG with the Read tool at image_quality="high" and fix
// layout / contrast / overflow bugs visually before tightening prose.

const path = require('path');
const fs = require('fs');

// Resolve playwright from common locations so this script can run from
// anywhere without install ceremony.
//
// NOTE: bare require('playwright') resolves relative to THIS FILE, not the
// CWD — so simply running from a project that has playwright installed does
// NOT work. We walk up from CWD (and $PLAYWRIGHT_NODE_MODULES / $NODE_PATH)
// to find a real node_modules/playwright anywhere above the invocation dir.
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

const VIEWPORT_W = 1360;
const SEG_HEIGHT = 1400;
const SETTLE_MS = 1800;
const SCROLL_SETTLE_MS = 350;

(async () => {
  const arg = process.argv[2];
  const outDir = process.argv[3] || '/tmp/doc-previews';
  if (!arg) {
    console.error('Usage: node screenshot.js <abs-path-to-html> [out-dir]');
    process.exit(1);
  }
  const fileUrl = arg.startsWith('file://') ? arg : `file://${path.resolve(arg)}`;
  fs.mkdirSync(outDir, { recursive: true });
  for (const name of fs.readdirSync(outDir)) {
    if (/^(scroll-(light|dark)-\d+|hero-dark-v2)\.png$/.test(name)) {
      fs.unlinkSync(path.join(outDir, name));
    }
  }

  const browser = await chromium.launch();

  async function captureTheme(colorScheme) {
    const context = await browser.newContext({
      viewport: { width: VIEWPORT_W, height: SEG_HEIGHT },
      deviceScaleFactor: 2,
      colorScheme,
    });
    const page = await context.newPage();
    await page.goto(fileUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(SETTLE_MS);

    const totalHeight = await page.evaluate(
      () => document.documentElement.scrollHeight,
    );
    const segments = [];
    for (let y = 0, i = 0; y < totalHeight; y += SEG_HEIGHT, i++) {
      segments.push([i, y]);
    }
    console.log(`${colorScheme} total height:`, totalHeight);

    for (const [i, y] of segments) {
      await page.evaluate((scrollY) => window.scrollTo(0, scrollY), y);
      await page.waitForTimeout(SCROLL_SETTLE_MS);
      const name = String(i).padStart(2, '0');
      await page.screenshot({
        path: path.join(outDir, `scroll-${colorScheme}-${name}.png`),
        fullPage: false,
      });
      console.log(`${colorScheme} captured at y=`, y);
    }

    await context.close();
    return segments;
  }

  const lightSegments = await captureTheme('light');
  const darkSegments = await captureTheme('dark');
  fs.copyFileSync(
    path.join(outDir, 'scroll-dark-00.png'),
    path.join(outDir, 'hero-dark-v2.png'),
  );

  await browser.close();
  console.log(
    'done — light segments:', lightSegments.length,
    '· dark segments:', darkSegments.length,
    '· out:', outDir,
  );
})();
