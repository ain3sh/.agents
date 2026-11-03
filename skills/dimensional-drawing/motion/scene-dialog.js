const { seg, lerp, eo, eio, clamp01 } = kit;
const DW_NS = 'http://www.w3.org/2000/svg';
const DW_CAM = [
  { t: 0, cx: 798, cy: 272, z: 4.4 }, { t: 2.3, cx: 806, cy: 274, z: 4.22 },
  { t: 4.2, cx: 905, cy: 440, z: 1.72 }, { t: 5.3, cx: 906, cy: 442, z: 1.69 },
  { t: 7.2, cx: 600, cy: 468, z: 1.5 }, { t: 7.8, cx: 602, cy: 470, z: 1.48 },
  { t: 9.2, cx: 950, cy: 530, z: 0.998 }, { t: 13, cx: 950, cy: 530, z: 0.988 }];
kit.scene('drawing', {
  init(kit) {
    kit.css('.dw-svg .dt{font-size:11px;fill:var(--main);paint-order:stroke;stroke:var(--ground);stroke-width:4px;stroke-linejoin:round}' +
      '.dw-svg .dts{font-size:9.5px;fill:color-mix(in srgb,var(--second) 75%,var(--ground));letter-spacing:.06em;paint-order:stroke;stroke:var(--ground);stroke-width:3px}' +
      '.dw-svg .sl{font-size:9px;fill:color-mix(in srgb,var(--second) 75%,var(--ground));letter-spacing:.08em}' +
      '.dw-svg .nt{font-size:11.5px;fill:var(--main);letter-spacing:.06em}.dw-svg .nth{font-size:13px;font-weight:700;fill:var(--main);letter-spacing:.06em}' +
      '.dw-svg .vt{font-size:12px;fill:var(--main);letter-spacing:.1em}.dw-svg .nbt{font-size:9.5px;fill:var(--main)}' +
      '.dw-svg .th{font-size:10.5px;fill:var(--main);letter-spacing:.05em}.dw-svg .tc{font-size:10.5px;fill:var(--main);text-transform:none}');
    const root = kit.h('<div class="ground"><div class="dw-cam"></div></div>');
    kit.stage.append(root);
    const camEl = root.querySelector('.dw-cam');
    this.cam = camEl.style;
    const svg = document.createElementNS(DW_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 1900 1060'); svg.setAttribute('width', '1900'); svg.setAttribute('height', '1060'); svg.setAttribute('class', 'dw-svg');
    camEl.appendChild(svg);
    const REG = this.reg = []; let sv = svg, CUR = { a: 0, s: 0, d: .6, i: 0 }, noreg = 0;
    const at = (a, s, d) => { CUR = { a: a, s: s || 0, d: d || .6, i: 0 }; };
    const kind = (e, t) => { if (t === 'text') return 'f'; const c = ' ' + (e.getAttribute('class') || '') + ' ';
      if (/ (slot|ph|cl|env|hs) /.test(c) || (e.getAttribute('fill') || '').indexOf('url') === 0) return 'f'; return 'd'; };
    function mk(t, a, p) { const e = document.createElementNS(DW_NS, t); for (const k in a) if (a[k] != null) e.setAttribute(k, a[k]); (p || sv).appendChild(e);
      if (!noreg && t !== 'g') { const s = CUR.a + CUR.i * CUR.s; CUR.i++; const k = kind(e, t); if (k === 'd') e.setAttribute('pathLength', '1'); e.style.opacity = 0; REG.push({ e: e, a: s, b: s + CUR.d, k: k, last: -1 }); }
      return e; }
    function tx(x, y, s, c, a, p) { const t = mk('text', Object.assign({ x: x, y: y, class: c || 'dt' }, a || {}), p); t.textContent = s; return t; }
    noreg = 1; const d = mk('defs', {}); const m = mk('marker', { id: 'dwar', viewBox: '0 0 10 10', refX: 10, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse', markerUnits: 'userSpaceOnUse' }, d);
    mk('path', { d: 'M0,1.7 L10,5 L0,8.3 z', class: 'arrow' }, m);
    const pt = mk('pattern', { id: 'dwhat', width: 5, height: 5, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' }, d); mk('line', { x1: 0, y1: 0, x2: 0, y2: 5, class: 'hl' }, pt); noreg = 0;
    const A = 'url(#dwar)', HAT = 'url(#dwhat)';
    function dimH(x1, x2, y, e1, e2, l, o) { o = o || {}; [[x1, e1], [x2, e2]].forEach(([x, e]) => { if (e == null) return; const s = Math.sign(y - e) || 1; mk('line', { x1: x, y1: e + s * 3, x2: x, y2: y + s * 5, class: 'ext' }); });
      if (x2 - x1 >= 28) mk('line', { x1: x1, y1: y, x2: x2, y2: y, class: 'dl', 'marker-start': A, 'marker-end': A }); else { mk('line', { x1: x1 - 13, y1: y, x2: x1, y2: y, class: 'dl', 'marker-end': A }); mk('line', { x1: x2 + 13, y1: y, x2: x2, y2: y, class: 'dl', 'marker-end': A }); }
      tx((x1 + x2) / 2 + (o.dx || 0), (o.below ? y + 13 : y - 4) + (o.dy || 0), l, o.c || 'dt', { 'text-anchor': 'middle' }); }
    function dimV(y1, y2, x, e1, e2, l, o) { o = o || {}; [[y1, e1], [y2, e2]].forEach(([y, e]) => { if (e == null) return; const s = Math.sign(x - e) || 1; mk('line', { x1: e + s * 3, y1: y, x2: x + s * 5, y2: y, class: 'ext' }); });
      if (y2 - y1 >= 28) mk('line', { x1: x, y1: y1, x2: x, y2: y2, class: 'dl', 'marker-start': A, 'marker-end': A }); else { mk('line', { x1: x, y1: y1 - 13, x2: x, y2: y1, class: 'dl', 'marker-end': A }); mk('line', { x1: x, y1: y2 + 13, x2: x, y2: y2, class: 'dl', 'marker-end': A }); }
      const c = (y1 + y2) / 2; if (o.side) { const r = o.side === 'r'; tx(r ? x + 6 : x - 6, c + 4, l, o.c || 'dt', { 'text-anchor': r ? 'start' : 'end' }); } else tx(x - 5, c, l, o.c || 'dt', { 'text-anchor': 'middle', transform: 'rotate(-90 ' + (x - 5) + ' ' + c + ')' }); }
    function callout(px, py, ex, ey, l, dir, c) { const s = dir || (ex >= px ? 1 : -1); mk('circle', { cx: px, cy: py, r: 1.8, class: 'dot' }); mk('polyline', { points: px + ',' + py + ' ' + ex + ',' + ey + ' ' + (ex + s * 10) + ',' + ey, class: 'lead' }); tx(ex + s * 14, ey + 4, l, c || 'dt', { 'text-anchor': s > 0 ? 'start' : 'end' }); }
    function rad(cx, cy, r, c, l, L) { const sx = c.indexOf('l') > -1 ? -1 : 1, sy = c.indexOf('t') > -1 ? -1 : 1; const ox = cx - sx * r, oy = cy - sy * r; callout(ox + sx * r * Math.SQRT1_2, oy + sy * r * Math.SQRT1_2, ox + sx * r * Math.SQRT1_2 + sx * L, oy + sy * r * Math.SQRT1_2 + sy * L, l, sx); }
    function nb(x, y, n) { mk('rect', { x: x - 6, y: y - 6, width: 12, height: 12, class: 'nb' }); tx(x, y + 3.5, String(n), 'nbt', { 'text-anchor': 'middle' }); }
    function rr(x, y, w, h, r, c, p) { return mk('rect', { x: x, y: y, width: w, height: h, rx: r, class: c }, p); }
    function slotLabel(x, y, w, h, l, al, p) { tx(al === 'l' ? x + 6 : x + w / 2, y + h / 2 + 3.2, l, 'sl', { 'text-anchor': al === 'l' ? 'start' : 'middle' }, p); }
    function title(x, y, t, s) { tx(x, y, t, 'vt', { 'text-anchor': 'middle' }); if (s) tx(x, y + 14, s, 'dts', { 'text-anchor': 'middle' }); }
    function xbox(x, y, w, h, p) { mk('rect', { x: x, y: y, width: w, height: h, class: 'thin' }, p); mk('path', { d: 'M' + x + ',' + y + ' l' + w + ',' + h + ' M' + (x + w) + ',' + y + ' l' + (-w) + ',' + h, class: 'thin' }, p); }
    function detailRef(cx, cy, r, lbl, lx, ly) { mk('circle', { cx: cx, cy: cy, r: r, class: 'ph' }); const a = Math.atan2(ly - cy, lx - cx); mk('line', { x1: cx + r * Math.cos(a), y1: cy + r * Math.sin(a), x2: lx, y2: ly, class: 'lead' }); tx(lx + (lx < cx ? -4 : 4), ly + 4, lbl, 'dts', { 'text-anchor': lx < cx ? 'end' : 'start' }); }
    function table(x, y, ttl, rows) { const ws = [40, 88, 96], rh = 17; tx(x, y - 8, ttl, 'vt'); [['Code', 'Variable', 'Value']].concat(rows).forEach((r, i) => { let c2 = x; r.forEach((c, j) => { mk('rect', { x: c2, y: y + i * rh, width: ws[j], height: rh, class: 'thin' }); tx(c2 + (j ? ws[j] / 2 : 6), y + i * rh + 12, c, i ? 'tc' : 'th', { 'text-anchor': j ? 'middle' : 'start' }); c2 += ws[j]; }); }); return y + (rows.length + 1) * rh + 36; }
    function notes(list) { tx(50, 58, 'Notes:', 'nth'); tx(112, 58, '(unless otherwise specified)', 'nt'); list.forEach(([n, t], i) => { const y = 88 + i * 24; nb(56, y - 4, n); tx(72, y, t, 'nt'); }); }
    const W = 420, H = 448;
    /* ---------- plan view (draws first, camera starts on its header) ---------- */
    const k = .9, PX = 720, PY = 232, X = v => PX + v * k, Y = v => PY + v * k;
    const r = (x, y, w, h, rx, c, l, al) => { rr(X(x), Y(y), w * k, h * k, rx * k, c); if (l) slotLabel(X(x), Y(y), w * k, h * k, l, al); };
    at(-0.95, 0, 2.4); { const x0 = X(0), y0 = Y(0), w = W * k, h = H * k, q = 16 * k; mk('path', { d: 'M' + x0 + ',' + (y0 + h * .55) + ' V' + (y0 + q) + ' A' + q + ',' + q + ' 0 0 1 ' + (x0 + q) + ',' + y0 + ' H' + (x0 + w - q) + ' A' + q + ',' + q + ' 0 0 1 ' + (x0 + w) + ',' + (y0 + q) + ' V' + (y0 + h - q) + ' A' + q + ',' + q + ' 0 0 1 ' + (x0 + w - q) + ',' + (y0 + h) + ' H' + (x0 + q) + ' A' + q + ',' + q + ' 0 0 1 ' + x0 + ',' + (y0 + h - q) + ' Z', class: 'obj' }); }
    at(-0.7, 0, 1.0); mk('circle', { cx: X(31), cy: Y(33), r: 16 * k, class: 'hug' });
    at(-0.05, .12, .55); xbox(X(23), Y(25), 16 * k, 16 * k);
    at(0.6, .25, .5); r(57, 23, 304, 20, 2, 'slot', 'Title slot · flex', 'l');
    at(1.35, .1, .45); mk('line', { x1: X(1), y1: Y(65), x2: X(419), y2: Y(65), class: 'ph' });
    const ty = Y(-30);
    at(1.45, .07, .45); dimH(X(1), X(15), ty, Y(0), Y(17), 'S1', { dx: -9 }); dimH(X(15), X(47), ty, null, Y(17), 'Z1'); dimH(X(47), X(57), ty, null, Y(23), 'S5', { dx: 9 });
    at(1.85, .1, .5); dimV(Y(1), Y(65), X(-58), X(0), X(0), 'H1');
    at(2.45, .08, .5); r(373, 17, 32, 32, 10, 'slot'); xbox(X(381), Y(25), 16 * k, 16 * k);
    at(2.65, .1, .7); r(5, 65, 410, 318, 11, 'well'); mk('line', { x1: X(1), y1: Y(383), x2: X(419), y2: Y(383), class: 'ph' });
    at(2.9, .07, .5); r(20, 80, 380, 40, 2, 'slot', 'Content slot · fill'); r(20, 136, 380, 68, 2, 'slot', 'Content slot · fill');
    at(3.15, .06, .5); [[220, 246], [302, 328]].forEach(([l, i]) => { r(20, l, 380, 18, 2, 'slot', 'Label slot', 'l'); r(20, i, 380, 40, 10, 'hug'); r(32, i + 10, 356, 20, 2, 'slot', 'Value slot', 'l'); });
    at(3.5, .08, .55); r(197, 397, 90, 36, 18, 'hug', 'Secondary'); r(295, 397, 110, 36, 10, 'hug', 'Primary');
    at(3.7, .1, .6); mk('line', { x1: X(-16), y1: Y(33), x2: X(436), y2: Y(33), class: 'cl' }); mk('line', { x1: X(-16), y1: Y(415), x2: X(436), y2: Y(415), class: 'cl' });
    at(3.6, .05, .4); dimH(X(57), X(361), ty, null, Y(23), 'FLEX', { c: 'dts' }); dimH(X(361), X(373), ty, null, Y(17), 'S8'); dimH(X(373), X(405), ty, null, Y(17), 'Z2'); dimH(X(405), X(419), ty, null, Y(0), 'S1', { dx: 9 });
    at(3.85, .03, .4); dimH(X(0), X(420), Y(-62), Y(-34), Y(-34), 'W'); tx(X(210), Y(-80), 'W = 420 · fixed', 'dts', { 'text-anchor': 'middle' });
    const by = Y(H + 30);
    at(4.0, .03, .4); dimH(X(15), X(197), by, Y(H), Y(433), 'FLEX', { below: true, c: 'dts' }); dimH(X(197), X(287), by, null, Y(433), 'HUG', { below: true, c: 'dts' }); dimH(X(287), X(295), by, null, Y(433), 'S7', { below: true }); dimH(X(295), X(405), by, null, Y(433), 'HUG', { below: true, c: 'dts' }); dimH(X(405), X(419), by, null, Y(H), 'S1', { below: true, dx: 6 });
    at(4.1, .05, .45); dimV(Y(65), Y(383), X(-58), null, X(5), 'HUG', { c: 'dts' }); dimV(Y(383), Y(447), X(-58), null, X(0), 'H2'); dimV(Y(0), Y(H), X(-96), X(-62), X(-62), '(REF ' + H + ')');
    at(4.2, .012, .35); [[1, 15, 'S1'], [15, 51, 'H3'], [51, 65, 'S1'], [66, 80, 'S2'], [120, 136, 'S3'], [204, 220, 'S3'], [238, 246, 'S4'], [246, 286, 'H5'], [286, 302, 'S3'], [368, 382, 'S2'], [383, 397, 'S1'], [397, 433, 'H3'], [433, 447, 'S1']].forEach(([a, b, l]) => dimV(Y(a), Y(b), X(452), X(420), X(420), l, { side: 'r' }));
    at(4.55, .05, .45); rad(X(0), Y(H), 16 * k, 'bl', 'R1', 22); rad(X(5), Y(383), 11 * k, 'bl', 'R2', 20); rad(X(405), Y(433), 10 * k, 'br', 'R3', 22);
    at(4.75, .05, .4); nb(X(350), Y(33), 1); nb(X(389), Y(7), 3); nb(X(60), Y(415), 4); nb(X(342), Y(7), 7); nb(X(12), Y(-46), 5); nb(X(280), Y(-84), 8);
    at(4.9, .06, .45); detailRef(X(6), Y(66), 13, 'DETAIL C', X(42), Y(57)); detailRef(X(389), Y(33), 22, 'DETAIL D', X(330), Y(57)); detailRef(X(32), Y(266), 24, 'DETAIL E', X(108), Y(295)); detailRef(X(300), Y(415), 26, 'DETAIL F', X(168), Y(415));
    at(5.0, .1, .5); title(X(210), Y(H + 82), 'Plan view', 'Scale 0.9:1 · reference content');
    /* ---------- exploded view: static bottom layers + three layers that lift off the plan ---------- */
    const sc = .45, TX = 330, TY = 560, gap = 46, ia = .94 * sc, ib = .17 * sc, ic = -.34 * sc, id = .47 * sc;
    const P = (x, y, z) => [TX + ia * x + ic * y, TY + ib * x + id * y - z];
    const uIso = 1 / Math.sqrt(ia * id - ib * ic);
    const G = (z, reg) => { const g = mk('g', { transform: 'matrix(' + ia + ',' + ib + ',' + ic + ',' + id + ',' + TX + ',' + (TY - z) + ')' }); g.style.setProperty('--u', uIso); return g; };
    at(6.15, .12, .8); let g = G(0); rr(-60, -60, 540, 568, 0, 'thin', g);
    g = G(gap); const scrim = rr(-60, -60, 540, 568, 0, 'hs', g); scrim.setAttribute('fill', HAT); scrim.setAttribute('fill-opacity', '.35');
    g = G(gap * 2); const sh = rr(16, 48, 388, H - 32, 16, 'hs', g); sh.setAttribute('fill', HAT);
    noreg = 1; const MG = this.morph = [];
    const mg = (z, a0) => { const g2 = mk('g', {}); g2.style.opacity = 0; MG.push({ g: g2, z: z, a: a0 }); return g2; };
    let q = mg(gap * 3, 5.4); rr(0, 0, W, H, 16, 'obj', q); mk('line', { x1: 1, y1: 65, x2: 419, y2: 65, class: 'ph' }, q); mk('line', { x1: 1, y1: 383, x2: 419, y2: 383, class: 'ph' }, q);
    q = mg(gap * 4, 5.5); rr(5, 65, 410, 318, 11, 'well', q);
    q = mg(gap * 5, 5.6); mk('circle', { cx: 31, cy: 33, r: 16, class: 'hug' }, q); rr(57, 23, 304, 20, 2, 'slot', q); rr(373, 17, 32, 32, 10, 'slot', q); rr(20, 80, 380, 40, 2, 'slot', q); rr(20, 136, 380, 68, 2, 'slot', q);
    [[220, 246], [302, 328]].forEach(([l, i]) => { rr(20, l, 380, 18, 2, 'slot', q); rr(20, i, 380, 40, 10, 'hug', q); }); rr(197, 397, 90, 36, 18, 'hug', q); rr(295, 397, 110, 36, 10, 'hug', q);
    noreg = 0; this.iso = [ia, ib, ic, id, TX, TY]; this.flat = [k, 0, 0, k, PX, PY]; this.uIso = uIso; this.uFlat = 1 / k;
    at(6.85, .04, .45); [[0, 0], [W, 0], [W, H], [0, H]].forEach(([x, y]) => { const p1 = P(x, y, gap * 2), p2 = P(x, y, gap * 5); mk('line', { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1], class: 'ph' }); });
    at(7.0, .07, .45); const LX = 215;
    [[0, [-60, 508], 'L0 · Viewport', 'Reference 1280 × 800'], [gap, [-60, 508], 'L1 · Scrim', 'Full-bleed, below the dialog'], [gap * 2, [16, H + 16], 'L2 · Shadow', 'Footprint · Y · BL · SP'], [gap * 3, [0, H], 'L3 · Container', 'R1 · B · header / body / footer'], [gap * 4, [5, 383], 'L4 · Body', 'R2 · inset S6'], [gap * 5, [20, 368], 'L5 · Slots & controls', 'Lead · title · close · fields']].forEach(([z, [x, y], t, st]) => {
      const p1 = P(x, y, z); mk('circle', { cx: p1[0], cy: p1[1], r: 1.8, class: 'dot' }); mk('polyline', { points: p1[0] + ',' + p1[1] + ' ' + (LX + 10) + ',' + p1[1] + ' ' + LX + ',' + p1[1], class: 'lead' });
      tx(LX - 4, p1[1] - 2, t, 'vt', { 'text-anchor': 'end' }); tx(LX - 4, p1[1] + 11, st, 'dts', { 'text-anchor': 'end' }); });
    at(7.5, .1, .5); title(390, TY + 168, 'Exploded view', 'Axonometric · z gaps not to scale');
    /* ---------- the rest of the sheet, drawn after the pull-back ---------- */
    at(7.7, 0, 1.6); rr(20, 20, 1860, 1020, 16, 'border');
    at(8.55, .045, .4); notes([[1, 'Title slot flexes (min-width 0) and wraps. Header grows past H1.'], [2, 'Body inset S6 from container. Body radius R2 = R1 − B − S6 (derived).'], [3, 'Lead, close and footer actions hug their content and never shrink.'], [4, 'Footer actions align to the end: secondary, then primary, gap S7.'], [5, 'Dialog centers on both axes above a full-bleed scrim.'], [6, 'Max height MH = 100vh − 2·V1. Overflow behavior [TBD].'], [7, 'Close is Z2. Hit area 44 min on touch layouts.'], [8, 'W is fixed in source. Narrow-viewport behavior [TBD].']]);
    at(8.8, .006, .25); let yy = table(1606, 86, 'Spacing', [['S1', 'dialog-pad', '14'], ['S2', 'body-pad', '14'], ['S3', 'body-gap', '16'], ['S4', 'field-gap', '8'], ['S5', 'lead-gap', '10'], ['S6', 'body-inset', '4'], ['S7', 'action-gap', '8'], ['S8', 'gap-min', '12'], ['S9', 'input-pad-x', '12'], ['S10', 'primary-pad-x', '14'], ['S11', 'secondary-pad-x', '16']]);
    yy = table(1606, yy, 'Size', [['B', 'border', '1'], ['Z1', 'lead-size', '32'], ['Z2', 'close-size', '32'], ['I1', 'icon-size', '16'], ['H3', 'action-h', '36'], ['H5', 'input-h', '40'], ['H1', 'header-min', '2·S1+H3 = 64'], ['H2', 'footer-h', '2·S1+H3 = 64'], ['W', 'dialog-w', '420']]);
    yy = table(1606, yy, 'Radius', [['R1', 'r-dialog', '16'], ['R2', 'r-body', 'R1−B−S6 = 11'], ['R3', 'r-control', '10'], ['R4', 'r-pill', 'h ÷ 2']]);
    yy = table(1606, yy, 'Shadow', [['Y', 'shadow-y', '32'], ['BL', 'shadow-blur', '72'], ['SP', 'shadow-spread', '−16'], ['E1', 'env-top', 'BL+SP−Y = 24'], ['E2', 'env-side', 'BL+SP = 56'], ['E3', 'env-bottom', 'BL+SP+Y = 88']]);
    table(1606, yy, 'Viewport', [['V1', 'viewport-margin', '[TBD]'], ['MH', 'max-h', '100vh−2·V1']]);
    { const DX = 1300, DY = 250; at(9.0, .05, .45);
      mk('circle', { cx: DX + 32, cy: DY + 32, r: 32, class: 'hug' }); xbox(DX + 16, DY + 16, 32, 32);
      rr(DX + 120, DY, 64, 64, 20, 'slot'); xbox(DX + 136, DY + 16, 32, 32);
      dimH(DX, DX + 64, DY - 16, DY + 32, DY, 'Z1'); dimH(DX + 120, DX + 184, DY - 16, DY, DY, 'Z2');
      dimH(DX + 136, DX + 168, DY + 82, DY + 48, DY + 48, 'I1', { below: true }); dimH(DX + 120, DX + 136, DY + 82, DY + 64, null, '(Z2−I1)÷2', { below: true, dy: 14 });
      callout(DX + 32 - 22.6, DY + 32 + 22.6, DX - 6, DY + 86, 'R4', -1); rad(DX + 184, DY + 64, 20, 'br', 'R3', 16);
      tx(DX + 32, DY + 108, 'Lead', 'sl', { 'text-anchor': 'middle' }); tx(DX + 152, DY + 122, 'Close', 'sl', { 'text-anchor': 'middle' }); nb(DX + 196, DY + 8, 7);
      title(DX + 100, DY + 150, 'Detail D · header controls', 'Scale 2:1'); }
    { const FX = 1290, FY = 500; at(9.3, .05, .45);
      mk('line', { x1: FX + 222, y1: FY - 38, x2: FX + 222, y2: FY + 66, class: 'ph' }); tx(FX + 222, FY - 44, 'Container edge', 'dts', { 'text-anchor': 'middle' });
      rr(FX, FY, 90, 36, 18, 'hug'); rr(FX + 98, FY, 110, 36, 10, 'hug'); slotLabel(FX, FY, 90, 36, 'Secondary'); slotLabel(FX + 98, FY, 110, 36, 'Primary');
      const t2 = FY - 14; dimH(FX, FX + 90, t2, FY, FY, 'HUG', { c: 'dts' }); dimH(FX + 90, FX + 98, t2, null, FY, 'S7'); dimH(FX + 98, FX + 208, t2, null, FY, 'HUG', { c: 'dts' }); dimH(FX + 208, FX + 222, t2, null, null, 'S1', { dx: 8 });
      dimV(FY, FY + 36, FX - 14, FX, FX, 'H3', { side: 'l' }); dimH(FX, FX + 16, FY + 52, FY + 36, FY + 36, 'S11', { below: true, dx: -6 }); dimH(FX + 98, FX + 112, FY + 52, FY + 36, FY + 36, 'S10', { below: true, dx: -4 });
      tx(FX + 180, FY + 64, 'R4 · R3', 'dts'); nb(FX + 50, FY + 80, 4); title(FX + 111, FY + 108, 'Detail F · footer actions', 'Scale 1:1'); }
    { const s = .25, VX = 80, VY = 780, vw = 320, vh = 200, dw = W * s, dh = H * s, dx = VX + (vw - dw) / 2, dy = VY + (vh - dh) / 2, m2 = 10; at(9.6, .06, .5);
      const vr = rr(VX, VY, vw, vh, 0, 'hs'); vr.setAttribute('fill', HAT); vr.setAttribute('fill-opacity', '.35');
      rr(VX + vw / 2 - dw / 2, VY + m2, dw, vh - 2 * m2, 0, 'ph'); rr(dx - 14, dy - 6, dw + 28, dh + 28, 0, 'env'); rr(dx, dy, dw, dh, 4, 'obj');
      mk('line', { x1: VX - 8, y1: VY + vh / 2, x2: VX + vw + 8, y2: VY + vh / 2, class: 'cl' }); mk('line', { x1: VX + vw / 2, y1: VY - 8, x2: VX + vw / 2, y2: VY + vh + 8, class: 'cl' });
      dimH(VX, VX + vw, VY - 16, VY, VY, '100VW'); dimV(VY, VY + vh, VX - 16, VX, VX, '100VH');
      dimV(VY, VY + m2, VX + vw + 18, VX + vw / 2 + dw / 2, VX + vw / 2 + dw / 2, 'V1 [TBD]', { side: 'r' }); dimV(VY + vh - m2, VY + vh, VX + vw + 18, VX + vw / 2 + dw / 2, VX + vw / 2 + dw / 2, 'V1', { side: 'r' });
      dimV(VY + m2, VY + vh - m2, VX + vw + 60, VX + vw / 2 + dw / 2 + 4, VX + vw / 2 + dw / 2 + 4, 'MH', { side: 'r' });
      callout(dx + dw + 12, dy + dh + 6, VX + vw - 20, VY + vh - 24, 'E1 · E2 · E3', 1, 'dts'); callout(VX + 30, VY + 30, VX + 20, VY + vh + 16, 'Scrim', -1, 'dts');
      nb(VX + vw - 14, VY + m2 + 14, 6); nb(dx - 14, dy - 14, 5); title(VX + vw / 2, VY + vh + 34, 'Viewport placement', 'Scale 0.25:1 · reference 1280 × 800'); }
    { const K = 4, CX = 620, CY = 956, CP = (u, v) => [CX + u * K, CY - v * K]; at(10.0, .08, .55);
      const arc = (o, rr2) => { const a1 = CP(o, 36), a2 = CP(o, 16), a3 = CP(16, o), a4 = CP(36, o); return 'M' + a1 + ' L' + a2 + ' A' + rr2 * K + ' ' + rr2 * K + ' 0 0 0 ' + a3 + ' L' + a4; };
      mk('path', { d: arc(0, 16), class: 'obj', fill: 'none' }); mk('path', { d: arc(1, 15), class: 'thin' }); mk('path', { d: arc(5, 11), class: 'thin' });
      const cc = CP(16, 16); mk('path', { d: 'M' + (cc[0] - 6) + ',' + cc[1] + ' h12 M' + cc[0] + ',' + (cc[1] - 6) + ' v12', class: 'thin' });
      [[16, 'R1', 205], [11, 'R2', 250]].forEach(([rq, l, dg], i) => { const a = dg * Math.PI / 180, ex = cc[0] + rq * K * Math.cos(a), ey = cc[1] - rq * K * Math.sin(a); mk('line', { x1: cc[0], y1: cc[1], x2: ex, y2: ey, class: 'dl', 'marker-end': A }); tx(i ? (cc[0] + ex) / 2 + 8 : (cc[0] + ex) / 2 - 6, i ? (cc[1] + ey) / 2 + 2 : (cc[1] + ey) / 2 - 6, l, 'dt', { 'text-anchor': i ? 'start' : 'end' }); });
      dimH(CP(0, 0)[0], CP(1, 0)[0], CP(0, 32)[1], CP(0, 36)[1], CP(1, 36)[1], 'B', { dx: -10 }); dimH(CP(1, 0)[0], CP(5, 0)[0], CP(0, 32)[1], null, CP(5, 36)[1], 'S6', { dx: 12 });
      tx(CP(9, 30)[0], CP(9, 30)[1], 'R2 = R1 − B − S6', 'dt', { style: 'text-transform:none' }); title(CX + 72, CY + 38, 'Detail C · nested corner', 'Scale 4:1'); }
    { const EX = 880, EY = 860, FW = 260; at(10.25, .06, .5);
      rr(EX, EY, FW, 18, 2, 'slot'); slotLabel(EX, EY, FW, 18, 'Label slot', 'l'); rr(EX, EY + 26, FW, 40, 10, 'hug'); rr(EX + 12, EY + 36, FW - 24, 20, 2, 'slot'); slotLabel(EX + 12, EY + 36, FW - 24, 20, 'Value slot', 'l');
      dimV(EY, EY + 18, EX - 16, EX, EX, 'HUG', { side: 'l', c: 'dts' }); dimV(EY + 18, EY + 26, EX - 16, null, EX, 'S4', { side: 'l' }); dimV(EY + 26, EY + 66, EX - 16, null, EX, 'H5', { side: 'l' });
      const b2 = EY + 84; dimH(EX, EX + 12, b2, EY + 66, EY + 56, 'S9', { below: true, dx: -8 }); dimH(EX + 12, EX + FW - 12, b2, null, EY + 56, 'FILL', { below: true, c: 'dts' }); dimH(EX + FW - 12, EX + FW, b2, EY + 56, EY + 66, 'S9', { below: true, dx: 8 });
      rad(EX + FW, EY + 26, 10, 'tr', 'R3', 16); title(EX + FW / 2, EY + 134, 'Detail E · field', 'Scale 1:1 · label → input'); }
    { at(10.55, .07, .5); [['R1', 'Container', 16], ['R2', 'Body', 11], ['R3', 'Control', 10], ['R4', 'Pill (h = H3)', 18]].forEach(([c, n, rq], i) => { const x0 = 1250 + i * 92, y0 = 950, L = 30, q2 = 2, RP = (u, v) => [x0 + u * q2, y0 - v * q2];
        mk('path', { d: 'M' + RP(0, L) + ' L' + RP(0, rq) + ' A' + rq * q2 + ' ' + rq * q2 + ' 0 0 0 ' + RP(rq, 0) + ' L' + RP(L, 0), class: 'obj', fill: 'none' });
        const cc = RP(rq, rq), a = 225 * Math.PI / 180; mk('line', { x1: cc[0], y1: cc[1], x2: cc[0] + rq * q2 * Math.cos(a), y2: cc[1] - rq * q2 * Math.sin(a), class: 'dl', 'marker-end': A });
        tx(x0 + L * q2 / 2 + 4, y0 - L * q2 + 12, c, 'dt'); tx(x0, y0 + 16, n, 'dts'); });
      title(1420, 994, 'Radius details', 'Scale 2:1'); }
  },
  render(t) {
    t = t / 0.85;
    let i = 0; while (i < DW_CAM.length - 2 && t > DW_CAM[i + 1].t) i++;
    const c0 = DW_CAM[i], c1 = DW_CAM[i + 1], p = eio(seg(t, c0.t, c1.t));
    const z = Math.exp(lerp(Math.log(c0.z), Math.log(c1.z), p)), cx = lerp(c0.cx, c1.cx, p), cy = lerp(c0.cy, c1.cy, p);
    this.cam.transform = 'translate(' + (960 - cx * z) + 'px,' + (540 - cy * z) + 'px) scale(' + z + ')';
    for (const it of this.reg) {
      let v = clamp01((t - it.a) / (it.b - it.a)); v = Math.round(v * 400) / 400;
      if (v === it.last) continue; it.last = v; const s = it.e.style;
      if (it.k === 'f') { s.opacity = eo(v); continue; }
      const e = eio(v); s.opacity = Math.min(1, v * 6);
      if (v >= 1) { s.strokeDasharray = ''; s.strokeDashoffset = ''; } else { s.strokeDasharray = '1 2'; s.strokeDashoffset = 1 - e; }
      s.fillOpacity = eo(seg(v, .55, 1));
    }
    const F = this.flat, I = this.iso;
    this.morph.forEach((m, j) => {
      const v = eio(seg(t, m.a, m.a + 1.5)), M = F.map((f, n) => lerp(f, I[n], v));
      M[5] -= m.z * v;
      m.g.style.opacity = eo(seg(t, m.a + 0.05, m.a + 0.5));
      const fo = eo(seg(t, m.a + 0.55, m.a + 1.25)); if (fo !== m.fo) { m.fo = fo; m.fills = m.fills || m.g.querySelectorAll('.obj,.well,.hug'); m.fills.forEach(e => { e.style.fillOpacity = fo; }); }
      m.g.setAttribute('transform', 'matrix(' + M.join(',') + ')');
      m.g.style.setProperty('--u', 1 / Math.sqrt(Math.abs(M[0] * M[3] - M[1] * M[2])));
    });
  },
});
