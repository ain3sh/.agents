// Hero-thumbnail capture for design-doc HTML files.
//
// Usage:
//   node thumbnail.js <abs-path-to-html> [out.png] [ratio] [--hero=<selector>]
//
// Produces a wide, dark-mode 2x crop of the document hero (eyebrow -> title
// -> tagline -> stat band) for posting next to the doc link. Default ratio
// 1.6:1 so chat clients don't letterbox it.
//
// Contract: the hero is --hero if given, else `header.doc`, else the first
// <header> that contains an <h1>, else the parent of the first <h1>. The crop
// ends at the first of .statband / .meta / .linkline / .tagline inside the
// hero, or the hero itself.
//
// The crop rules exist because naive captures look wrong:
//   - a fixed or sticky contents nav renders as a stray column, so every
//     <nav> is made invisible (layout kept)
//   - whatever follows the anchor (panels, preamble, demo card) bleeds a
//     sliver of accent colour into the bottom edge, so it is hidden
//   - the header is often narrower than the stat band, so the crop centres
//     on the wider of the two

const { loadModule, fileUrl, parseArgs } = require('./lib');

const { chromium } = loadModule('playwright');

const VIEWPORT_W = 1800;
const VIEWPORT_H = 1700;
const PAD = 56;

(async () => {
  const { positional, options } = parseArgs(process.argv.slice(2));
  const [src, out = '/tmp/doc-thumb.png', ratioArg] = positional;
  const ratio = Number(ratioArg) || 1.6;
  if (!src) {
    console.error('Usage: node thumbnail.js <abs-path-to-html> [out.png] [ratio] [--hero=<selector>]');
    process.exit(1);
  }

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    colorScheme: 'dark',
    viewport: { width: VIEWPORT_W, height: VIEWPORT_H },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  await page.goto(fileUrl(src), { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  // visibility, not display: removing a grid-column nav reflows the hero into its column.
  await page.addStyleTag({ content: 'nav{visibility:hidden!important}' });

  const box = await page.evaluate(({ pad, ratio, vw, heroSelector }) => {
    const firstH1 = document.querySelector('h1');
    const hero =
      (heroSelector && document.querySelector(heroSelector)) ||
      document.querySelector('header.doc') ||
      [...document.querySelectorAll('header')].find((h) => h.querySelector('h1')) ||
      (firstH1 && firstH1.parentElement);
    if (!hero) return null;

    const anchor =
      hero.querySelector('.statband') ||
      hero.querySelector('.meta') ||
      hero.querySelector('.linkline') ||
      hero.querySelector('.tagline') ||
      hero;

    // Hide everything after the anchor, walking up to the hero, so no
    // accent sliver bleeds in from a later sibling at any depth.
    for (let el = anchor; el && el !== hero.parentElement; el = el.parentElement) {
      for (let n = el.nextElementSibling; n; n = n.nextElementSibling) n.style.display = 'none';
      if (el === hero) break;
    }

    const rh = hero.getBoundingClientRect();
    const ra = anchor.getBoundingClientRect();
    const top = rh.top - pad;
    const h = ra.bottom + pad - top;
    const wide = ra.width > rh.width ? ra : rh;
    const cx = (wide.left + wide.right) / 2;
    const w = Math.min(h * ratio, vw);
    return { x: Math.max(0, cx - w / 2), y: Math.max(0, top), w, h };
  }, { pad: PAD, ratio, vw: VIEWPORT_W, heroSelector: options.hero || null });

  if (!box) {
    console.error('no hero found: pass --hero=<selector>, or give the page an <h1>');
    process.exit(1);
  }

  await page.screenshot({ path: out, clip: { x: box.x, y: box.y, width: box.w, height: box.h } });
  await browser.close();
  console.log(`wrote ${out} (${Math.round(box.w * 2)}x${Math.round(box.h * 2)}px @2x, ratio ${(box.w / box.h).toFixed(2)})`);
})();
