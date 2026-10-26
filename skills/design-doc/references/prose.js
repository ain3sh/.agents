// Prose run probe: the longest stretch a reader must read with nothing to look at.
//
// Usage:
//   node prose.js <abs-path-to-html> [--run=150] [--para=45]
//
// A run is the running text (p, li, dd, blockquote, .callout) between two
// visual breaks: a figure, table, card, metric, code block, embedded figure
// (.iso, [data-loopsim]), or collapsed chapter. Headings do not break a run;
// a wall with subheads is still a wall. Prints the longest runs and every
// paragraph over --para words as hints. Exits 1 when any run passes --run.

const { loadModule, fileUrl, parseArgs } = require('./lib');

const { chromium } = loadModule('playwright');

(async () => {
  const { positional, options } = parseArgs(process.argv.slice(2));
  const arg = positional[0];
  if (!arg) {
    console.error('Usage: node prose.js <abs-path-to-html> [--run=150] [--para=45]');
    process.exit(1);
  }
  const cap = Number(options.run ?? 150);
  const para = Number(options.para ?? 45);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1360, height: 1000 } });
  await page.goto(fileUrl(arg), { waitUntil: 'networkidle' });
  const r = await page.evaluate((para) => {
    const prose = 'p, li, dd, blockquote, .callout';
    const visual = 'figure, table, pre, .finding, .metric, .iso, [data-loopsim], details';
    const chrome = 'nav, header.top, footer';
    const words = (el) => (el.textContent || '').trim().split(/\s+/).filter(Boolean).length;
    const head = (el) => el.textContent.trim().split(/\s+/).slice(0, 8).join(' ');
    const runs = [];
    const long = [];
    let run = null;
    for (const el of document.querySelectorAll(`${prose}, ${visual}`)) {
      if (el.closest(chrome)) continue;
      if (el.matches(visual)) {
        if (run && !el.parentElement.closest(visual)) runs.push(run);
        run = null;
        continue;
      }
      if (el.closest(visual) || el.parentElement.closest(prose)) continue;
      const n = words(el);
      const id = el.closest('[id]')?.id || '(top)';
      run ??= { n: 0, id, head: head(el) };
      run.n += n;
      if (n > para) long.push({ n, id, head: head(el) });
    }
    if (run) runs.push(run);
    return { runs, long, visible: document.body.innerText.split(/\s+/).filter(Boolean).length };
  }, para);
  await browser.close();
  const runs = r.runs.sort((a, b) => b.n - a.n);
  const total = runs.reduce((a, b) => a + b.n, 0);
  for (const x of runs.slice(0, 5)) console.log(`${String(x.n).padStart(5)}w run  #${x.id}: ${x.head}…`);
  for (const x of r.long.sort((a, b) => b.n - a.n)) console.log(`  long paragraph ${x.n}w #${x.id}: ${x.head}…`);
  const over = runs.filter((x) => x.n > cap).length;
  console.log(`longest run ${runs[0]?.n ?? 0}w (cap ${cap}) · ${over} over · ${runs.length} runs · prose ${total}w · visible ${r.visible}`);
  process.exit(over ? 1 : 0);
})();
