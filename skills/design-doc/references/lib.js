// Shared helpers for the design-doc scripts.
//
// A bare require('playwright') resolves relative to THIS FILE, not the CWD,
// and Node never searches the npm global root. loadModule walks
// $PLAYWRIGHT_NODE_MODULES / $NODE_PATH, every node_modules above the
// invocation directory, then `npm root -g` (the global install the skill expects).

const path = require('path');
const { execSync } = require('child_process');

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
  for (const c of candidates) {
    try { return require(c); } catch (_) { /* try next */ }
  }
  try {
    return require(path.join(execSync('npm root -g', { encoding: 'utf8' }).trim(), name));
  } catch (_) { /* fall through to the install hint */ }
  console.error(
    `${name} not found locally or in \`npm root -g\`. Install it globally once:\n` +
    `  npm i -g ${name}` + (name === 'playwright' ? ' && playwright install chromium' : ''),
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
