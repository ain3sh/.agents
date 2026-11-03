#!/usr/bin/env node
// Screenshot a finished dimensional-drawing sheet (one self-contained HTML file)
// so the labels and sheet borders can be checked before delivery.
//
// Run from a work directory that has `playwright` installed (npm install playwright
// && npx playwright install chromium); the skill folder itself never holds node_modules.
//
// usage:
//   node ~/.agents/skills/dimensional-drawing/scripts/shot.mjs <sheet.html> [--out sheet.png] [--width 1800]

import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

function args() {
  const a = process.argv.slice(2), o = { _: [] };
  for (let i = 0; i < a.length; i++) {
    if (!a[i].startsWith('--')) { o._.push(a[i]); continue; }
    const k = a[i].slice(2), v = a[i + 1] && !a[i + 1].startsWith('--') ? a[++i] : true;
    o[k] = v;
  }
  return o;
}

const o = args();
if (!o._[0]) {
  console.error('usage: shot.mjs <sheet.html> [--out sheet.png] [--width 1800]');
  process.exit(1);
}
const IN = resolve(o._[0]);
const OUT = resolve(o.out || IN.replace(/\.html?$/, '') + '.png');
const W = +(o.width || 1800);

// Resolve playwright from the caller's cwd, not from this file, so the install lives in the work dir.
const require = createRequire(resolve(process.cwd(), 'package.json'));
let chromium;
try { ({ chromium } = require('playwright')); }
catch { console.error('playwright not found: run `npm install playwright` in the current directory'); process.exit(1); }

const launch = {};
if (process.env.CHROMIUM_PATH) launch.executablePath = process.env.CHROMIUM_PATH;
const browser = await chromium.launch(launch);
const page = await browser.newPage({ viewport: { width: W, height: 1000 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('[sheet error]', e.message));
await page.goto(pathToFileURL(IN).href, { waitUntil: 'load', timeout: 15000 }).catch(() => {});
await page.evaluate(() => document.fonts && document.fonts.ready);
mkdirSync(dirname(OUT), { recursive: true });
await page.screenshot({ path: OUT, fullPage: true });
await browser.close();
console.log('shot →', OUT);
