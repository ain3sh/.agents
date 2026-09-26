// Renders every <section class="card" id="..."> in an HTML file to
// <out-dir>/<id>.png at exactly 1600x900 (1x, the size Slack shows inline).
//
// Usage:
//   node render-cards.js <cards.html> [out-dir]   (out-dir defaults to the html's directory)

const path = require('path');
const { loadModule, fileUrl } = require('./lib');

const { chromium } = loadModule('playwright');

(async () => {
  const [src, outArg] = process.argv.slice(2);
  if (!src) {
    console.error('Usage: node render-cards.js <cards.html> [out-dir]');
    process.exit(1);
  }
  const outDir = path.resolve(outArg || path.dirname(path.resolve(src)));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  await page.goto(fileUrl(src), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const ids = await page.$$eval('section.card[id]', (els) => els.map((e) => e.id));
  if (ids.length === 0) {
    console.error('no <section class="card" id="..."> found');
    process.exit(1);
  }
  for (const id of ids) {
    const card = page.locator(`#${id}`);
    const overflow = await card.evaluate((el) => el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth);
    await card.screenshot({ path: path.join(outDir, `${id}.png`) });
    console.log(`wrote ${path.join(outDir, `${id}.png`)}${overflow ? '  (warning: content overflows the card and is clipped)' : ''}`);
  }
  await browser.close();
})();
