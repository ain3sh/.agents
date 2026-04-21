## Reference Skills (auto-loaded)

- **`linear-cli`** — linear-cli commands, agent output flags, chaining patterns
- **`slack`** — slck commands, bot/user token guidance, search flags
- **`worktree-setup`** — node_modules symlink rule; never `npm install` in a worktree

## Workflow Commands

| Command | Replaces | Usage |
|---|---|---|
| `/open-ticket` | linear skill load + `.env.local` source | `/open-ticket Fix tooltip` |
| `/open-pr` | ticket + branch + verify + lint + ship mega-prompt (handles fresh + mid-fix) | `/open-pr FAC-456` |
| `/review-pr` | per-type verification (repro for bugs), threaded line comments, verdict | `/review-pr 123` |
| `/address-review` | read reviewer feedback → triage → fix → respond to threads | `/address-review 123` |
| `/demo-pr` | tuistory before/after filming | `/demo-pr 123` |
| `/implement` | spec-first exploration + planning; waits for approval before coding | `/implement FAC-789` |
| `/retrospective` | stranger-review your own diff for entropy (dead weight / junk / perf / drift / scope) | `/retrospective` |
| `/update-skill` | reflect → update skill → critique ×2 → PR | `/update-skill linear-cli` |
| `/split-prs` | split long branch into stacked or independent PRs via cherry-pick | `/split-prs feat/big-branch` |

## Background Atoms (composed by commands, not in `/` menu)

| Atom | Owns | Composed by |
|---|---|---|
| **ticket-branch** | Ticket resolve/create (with parent search), branch checkout | `/open-pr`, `/update-skill`, `/split-prs` |
| **quality-ship** | Quality checks, commit, push. Not PR creation. | `/open-pr`, `/update-skill`, `/split-prs`, `/address-review` |
| **pr-description** | Diff analysis, conventional-commit title, 4-section PR body | `/open-pr`, `/update-skill`, `/split-prs` |
| **pr-context** | Fetch PR metadata + diff + conversation + linked ticket | `/review-pr`, `/address-review`, `/demo-pr` |

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
| `paperclip` MCP | HTTP MCP + `paperclip login` | Biomedical lit (`~/.factory/mcp.json`) |
| `paper-search` MCP | `npx -y paper-search-mcp-nodejs` | 14 academic platforms (`~/.factory/mcp.json`) |
