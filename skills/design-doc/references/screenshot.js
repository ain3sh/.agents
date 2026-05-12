// Playwright capture helper for design-doc HTML files.
//
// Usage:
//   node screenshot.js <abs-path-to-html> [out-dir]
//
// Outputs to <out-dir> (default /tmp/doc-previews):
//   scroll-light-NN.png   — full-width segments at 1400px viewport, 2x DPR, light mode
//   hero-dark-v2.png      — first viewport in dark mode (catches contrast bugs)
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
// anywhere without install ceremony. Tries CWD then /tmp then global.
function loadPlaywright() {
  const candidates = [
    'playwright',
    '/tmp/node_modules/playwright',
    '/usr/lib/node_modules/playwright',
    '/usr/local/lib/node_modules/playwright',
  ];
  for (const c of candidates) {
    try { return require(c); } catch (_) { /* try next */ }
  }
  console.error('playwright not found. Install with: cd /tmp && npm i playwright && npx playwright install chromium');
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

  const browser = await chromium.launch();

  // Light mode — full-page scroll capture
  const ctxLight = await browser.newContext({
    viewport: { width: VIEWPORT_W, height: SEG_HEIGHT },
    deviceScaleFactor: 2,
    colorScheme: 'light',
  });
  const pageLight = await ctxLight.newPage();
  await pageLight.goto(fileUrl, { waitUntil: 'networkidle' });
  await pageLight.waitForTimeout(SETTLE_MS);

  const totalHeight = await pageLight.evaluate(
    () => document.documentElement.scrollHeight,
  );
  console.log('total height:', totalHeight);

  const segments = [];
  for (let y = 0, i = 0; y < totalHeight; y += SEG_HEIGHT, i++) {
    segments.push([i, y]);
  }
  for (const [i, y] of segments) {
    await pageLight.evaluate((y) => window.scrollTo(0, y), y);
    await pageLight.waitForTimeout(SCROLL_SETTLE_MS);
    const name = String(i).padStart(2, '0');
    await pageLight.screenshot({
      path: path.join(outDir, `scroll-light-${name}.png`),
      fullPage: false,
    });
    console.log('captured at y=', y);
  }

  // Dark mode — first viewport (hero + first body segment)
  const ctxDark = await browser.newContext({
    viewport: { width: VIEWPORT_W, height: SEG_HEIGHT },
    deviceScaleFactor: 2,
    colorScheme: 'dark',
  });
  const pageDark = await ctxDark.newPage();
  await pageDark.goto(fileUrl, { waitUntil: 'networkidle' });
  await pageDark.waitForTimeout(SETTLE_MS);
  await pageDark.screenshot({
    path: path.join(outDir, 'hero-dark-v2.png'),
    fullPage: false,
  });

  await browser.close();
  console.log('done — segments:', segments.length, '· out:', outDir);
})();
