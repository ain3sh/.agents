#!/usr/bin/env node
// From https://github.com/enesozturk/dimensional-drawing.
//
// MIT License
//
// Copyright (c) 2026 Enes Ozturk
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//// Render a dimensional-drawing motion scene to MP4.
// Playwright (Chromium) draws each frame as a pure function of time,
// ffmpeg encodes the frames.
//
// Run from a work directory that has `playwright` installed (npm install playwright
// && npx playwright install chromium); the skill folder itself never holds node_modules.
//
// usage:
//   K=~/.agents/skills/dimensional-drawing/motion
//   node $K/render.mjs --scene $K/scene-dialog.js --css $K/base.css \
//                      --out dialog.mp4 [--duration 11] [--fps 60] [--width 1920] [--height 1080]
//                      [--bg #ffffff] [--id drawing] [--still 10.5 --out frame.png]

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const here = dirname(fileURLToPath(import.meta.url));
// Resolve playwright from the caller's cwd, not from this file, so the install lives in the work dir.
const require = createRequire(resolve(process.cwd(), 'package.json'));

function args() {
  const a = process.argv.slice(2), o = {};
  for (let i = 0; i < a.length; i++) {
    if (!a[i].startsWith('--')) continue;
    const k = a[i].slice(2), v = a[i + 1] && !a[i + 1].startsWith('--') ? a[++i] : true;
    o[k] = v;
  }
  return o;
}

const o = args();
if (!o.scene) {
  console.error('missing --scene <file.js>  (see README in this folder)');
  process.exit(1);
}
const W = +(o.width || 1920), H = +(o.height || 1080);
const FPS = +(o.fps || 60), DUR = +(o.duration || 11);
const BG = o.bg || '#ffffff';
const OUT = resolve(o.out || 'out.mp4');
const sceneJs = readFileSync(resolve(o.scene), 'utf8');
const sceneCss = o.css ? readFileSync(resolve(o.css), 'utf8') : '';

let html = readFileSync(resolve(here, 'player.html'), 'utf8');
html = html
  .replace('/*__CSS__*/', () => sceneCss)
  .replace('/*__JS__*/', () => sceneJs.replace(/<\/script/gi, '<\\/script'))
  .replace('<script>\n  const cfg', () =>
    `<script>window.__CFG__=${JSON.stringify({ w: W, h: H, bg: BG, scene: o.id || null })};</script>\n<script>\n  const cfg`);

let chromium;
try { ({ chromium } = require('playwright')); }
catch { console.error('playwright not found: run `npm install playwright` in the current directory'); process.exit(1); }

const launch = {};
if (process.env.CHROMIUM_PATH) launch.executablePath = process.env.CHROMIUM_PATH;
const browser = await chromium.launch(launch);
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('[scene error]', e.message));

// Fonts: the page asks Google Fonts for Arimo; offline it falls back to Helvetica/Arial (same metrics).
await page.setContent(html, { waitUntil: 'load', timeout: 15000 }).catch(() => {});
await page.waitForFunction(() => window.__READY__ === true, null, { timeout: 15000 });
await page.evaluate(() => document.fonts && document.fonts.ready);

const shot = () => page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: W, height: H } });

if (o.still !== undefined) {
  await page.evaluate(t => window.R(t), +o.still);
  const buf = await shot();
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, buf);
  console.log('still →', OUT);
  await browser.close();
  process.exit(0);
}

const ffmpeg = spawn(o.ffmpeg || 'ffmpeg', [
  '-y', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', String(o.crf || 16), '-preset', 'medium',
  '-movflags', '+faststart', OUT,
], { stdio: ['pipe', 'inherit', 'inherit'] });
ffmpeg.on('error', () => { console.error('ffmpeg not found on PATH (or pass --ffmpeg /path/to/ffmpeg)'); process.exit(1); });

const N = Math.round(DUR * FPS);
const t0 = Date.now();
for (let i = 0; i < N; i++) {
  await page.evaluate(t => window.R(t), i / FPS);
  const buf = await shot();
  if (!ffmpeg.stdin.write(buf)) await new Promise(r => ffmpeg.stdin.once('drain', r));
  if (i % FPS === 0) process.stdout.write(`\rframe ${i}/${N}`);
}
ffmpeg.stdin.end();
await new Promise(r => ffmpeg.on('close', r));
await browser.close();
console.log(`\r${N} frames → ${OUT}  (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
