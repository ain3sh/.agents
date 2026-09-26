// Shared helpers for the design-doc scripts.
//
// A bare require('playwright') resolves relative to THIS FILE, not the CWD,
// so running from a project that has playwright installed does not work on
// its own. loadModule walks $PLAYWRIGHT_NODE_MODULES / $NODE_PATH, then every
// node_modules above the invocation directory, then /tmp and global roots.

const path = require('path');

function loadModule(name) {
  const candidates = [name];
  for (const envDir of [process.env.PLAYWRIGHT_NODE_MODULES, process.env.NODE_PATH]) {
    for (const entry of (envDir || '').split(path.delimiter).filter(Boolean)) {
      candidates.push(path.join(entry, name));
    }
  }
  for (let dir = process.cwd(); ; dir = path.dirname(dir)) {
    candidates.push(path.join(dir, 'node_modules', name));
    if (dir === path.dirname(dir)) break;
  }
  candidates.push(
    path.join('/tmp/node_modules', name),
    path.join('/usr/lib/node_modules', name),
    path.join('/usr/local/lib/node_modules', name),
  );
  for (const c of candidates) {
    try { return require(c); } catch (_) { /* try next */ }
  }
  console.error(
    `${name} not found. Run from (or under) a project that has it installed,\n` +
    'or set PLAYWRIGHT_NODE_MODULES=/abs/path/to/node_modules,\n' +
    `or: cd /tmp && npm i ${name}` +
    (name === 'playwright' ? ' && npx playwright install chromium' : ''),
  );
  process.exit(1);
}

const fileUrl = (arg) => (arg.startsWith('file://') ? arg : `file://${path.resolve(arg)}`);

// Smooth scrolling makes scrollTo() return before the page moves, so every
// segment would capture the top of the document.
const CAPTURE_CSS = 'html{scroll-behavior:auto!important}';

// Splits argv into positionals and --key=value / --flag options.
function parseArgs(argv) {
  const positional = [];
  const options = {};
  for (const a of argv) {
    const m = a.match(/^--([^=]+)(?:=(.*))?$/);
    if (m) options[m[1]] = m[2] ?? true;
    else positional.push(a);
  }
  return { positional, options };
}

module.exports = { loadModule, fileUrl, parseArgs, CAPTURE_CSS };
