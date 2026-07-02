## Reference Skills (auto-loaded)

- **`linear-cli`** — linear-cli commands, agent output flags, chaining patterns
- **`slack`** — slck commands, bot/user token guidance, search flags
- **`worktree-setup`** — node_modules symlink rule; never `npm install` in a worktree

## Workflow Commands

| Command | Replaces | Usage |
|---|---|---|
| `/open-pr` | ticket + branch + verify + lint + ship mega-prompt (handles fresh + mid-fix) | `/open-pr FAC-456` |
| `/review-pr` | per-type verification (repro for bugs), threaded line comments, verdict | `/review-pr 123` |
| `/address-review` | read reviewer feedback → triage → fix → respond to threads | `/address-review 123` |
| `/demo-pr` | tuistory before/after filming | `/demo-pr 123` |
| `/implement` | spec-first exploration + planning; waits for approval before coding | `/implement FAC-789` |
| `/retrospective` | stranger-review your own diff for entropy (dead weight / junk / perf / drift / scope) | `/retrospective` |
| `/update-skill` | reflect → update skill → critique ×2 → PR | `/update-skill linear-cli` |
| `/split-pr` | split long branch into stacked or independent PRs via cherry-pick | `/split-pr feat/big-branch` |

## Background Atoms (composed by commands, not in `/` menu)

| Atom | Owns | Composed by |
|---|---|---|
| **ticket-branch** | Ticket resolve/create, direct parent/child context, branch checkout | `/open-pr`, `/update-skill`, `/split-pr` |
| **quality-ship** | Quality checks, commit, push. Not PR creation. | `/open-pr`, `/update-skill`, `/split-pr`, `/address-review` |
| **pr-description** | Diff analysis, conventional-commit title, 5-section PR body, live visual evidence (post-open) | `/open-pr`, `/update-skill`, `/split-pr` |
| **pr-context** | Fetch PR metadata + diff + conversation + linked ticket | `/review-pr`, `/address-review`, `/demo-pr` |
| **voice** | Craft (every-word-earns-its-slot: specifics, named actors, calibrated warmth/humility, anti-slop) for any authored/reviewed content + reviewer-reply load-bearing test (cut reflexive sycophancy/recap/performative future tense/status footers; keep them when they own a miss, anchor a thread, scope deferred work, or propose a path) + the canonical review severity taxonomy | `/review-pr`, `/post-review`, `/address-review`, pr-description, linear-cli |
| **structural-review** | Code-judo simplification hunt + structural tripwires (1k-line crossings, spaghetti growth, boundary leaks, contract muddying, orchestration smells); defers severity to voice | `/review-pr` (heavy-worker sweep) |

## Installed Tooling

| Tool | Install | Wired into |
|---|---|---|
| `rtk` | `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh \| sh` | `hooks/pre_tool_use/rtk_rewrite.py` — transparent `Execute` rewriter. Per-surface toggles in `configs/droid.toml`. |
| `slop-scan` | `npm install -g slop-scan` | `/retrospective`, `/review-pr`, `quality-ship` |
| `vulture` | `uv tool install vulture` | `quality-ship` (Python branch) |
| `arxiv2md` | `uv tool install arxiv2md` | Ad-hoc: pipe arXiv papers into context |
| `tirith` | [release tarball](https://github.com/sheeki03/tirith/releases/latest) | Shell hook only (activated in `~/.zshrc`); not wired into droids |
| `witr` | `go install github.com/pranshuparmar/witr/cmd/witr@latest` | Standalone "why is this running?" tracer |
| `nlsh` | `go install github.com/abakermi/nlsh@latest` | Wrapper + inlined config in `~/.zshrc` (materializes `~/.nlshrc` on call); uses OpenRouter via `OPENROUTER_API_KEY` |
| `excalirender` | At `~/.local/bin/`; if missing: `curl -fsSL https://raw.githubusercontent.com/JonRC/excalirender/main/install.sh \| PREFIX=$HOME/.local sh` | Renders `.excalidraw` → PNG/SVG/PDF, no browser. Excalidraw is a *format*, not an app. `pr-description` (artifacts.md), `excalidraw` skill |
| `gh-attach` | At `~/.local/bin/` | Uploads images/clips to GitHub's CDN for PR bodies. `pr-description` (artifacts.md, visual-evidence.md), `excalidraw` skill |
| `paperclip` MCP | HTTP MCP + `paperclip login` | Biomedical lit (`~/.factory/mcp.json`) |
| `paper-search` MCP | `npx -y paper-search-mcp-nodejs` | 14 academic platforms (`~/.factory/mcp.json`) |
