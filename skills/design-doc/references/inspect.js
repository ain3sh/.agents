// DOM probe for layout debugging.
//
// Usage:
//   node inspect.js <abs-path-to-html> "<css-selector>"
//
// Prints, for each match: bounding rect + computed styles for the
// properties most likely to be the bug (display, grid-column, position,
// width, color, background-color, font-family, font-style).
//
// Use when a Playwright screenshot shows a layout glitch and you can't
// see the cause in the CSS by reading. Common catches:
//   - dl > dd falling under dt because grid-column wasn't pinned
//   - decision card .num overlapping due to wrong padding-top
//   - dark-mode color falling back to inherited because variable wasn't
//     redefined in the @media (prefers-color-scheme: dark) block

const path = require('path');
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

(async () => {
  const arg = process.argv[2];
  const selector = process.argv[3];
  if (!arg || !selector) {
    console.error('Usage: node inspect.js <abs-path-to-html> "<css-selector>"');
    process.exit(1);
  }
  const fileUrl = arg.startsWith('file://') ? arg : `file://${path.resolve(arg)}`;

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1360, height: 1400 },
    deviceScaleFactor: 2,
    colorScheme: 'light',
  });
  const page = await ctx.newPage();
  await page.goto(fileUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  const results = await page.evaluate((sel) => {
    const props = [
      'display', 'position', 'grid-column', 'grid-row',
      'width', 'height', 'padding', 'margin',
      'color', 'background-color',
      'font-family', 'font-style', 'font-weight', 'font-size',
      'opacity', 'overflow',
    ];
    const els = Array.from(document.querySelectorAll(sel));
    return els.slice(0, 12).map((el) => {
      const rect = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const styles = Object.fromEntries(props.map((p) => [p, cs.getPropertyValue(p)]));
      return {
        tag: el.tagName.toLowerCase(),
        class: el.className || '(none)',
        id: el.id || '(none)',
        text: (el.textContent || '').slice(0, 60).replace(/\s+/g, ' '),
        rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
        styles,
      };
    });
  }, selector);

  console.log(`matches for "${selector}":`, results.length);
  for (const r of results) {
    console.log('---');
    console.log(`<${r.tag} id="${r.id}" class="${r.class}">`);
    console.log(`  text: "${r.text}"`);
    console.log(`  rect: x=${r.rect.x.toFixed(0)} y=${r.rect.y.toFixed(0)} w=${r.rect.w.toFixed(0)} h=${r.rect.h.toFixed(0)}`);
    for (const [k, v] of Object.entries(r.styles)) {
      console.log(`  ${k}: ${v}`);
    }
  }

  await browser.close();
})();
