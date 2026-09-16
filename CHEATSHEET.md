## Reference Skills (auto-loaded)

- **`linear-cli`** — linear-cli commands, agent output flags, chaining patterns
- **`slack-cli`** — slck commands, bot/user token guidance, search flags, Slack formatting/delivery, and the shared **voice** gate before sending or editing
- **`twitter-cli`** — bounded Twitter/X reads and user-approved account actions through the local `twitter` CLI; YAML default, JSON available with `--format json`
- **`dsx`** — session search/analytics plus durable `dsx papercut add|list|review`
- **`harness-optimization`** — reliability optimization for repeated agent/tool failures: trace policy → model → hooks → executor → process → evidence, then replace symptom patches with one lifecycle owner
- **`worktree-setup`** — source-selectable dependency mirrors (`repair|verify|setup --from <worktree>`); never install in a shared worktree
- **`design-doc`** — Factory-themed single-file RFCs and technical memos; adaptive document modes, proof-band/chart and claim-row callout patterns, full light/dark Playwright capture, hero-thumbnail crop for link sharing, secret-gist publishing
- **`vscode-workspace`** — on-demand headless VSCode instances for the `vscode:*` MCP tools (live LSP diagnostics/symbols/renames); zero-touch: auto-ensure hook spawns/canonicalizes/warms (workspace_path defaults to cwd), refcounted retirement at SessionEnd, idle reaper at SessionStart; manual: `vscode-ws ensure|retire|reap|list`

## Workflow Skills

Slash workflows live in `skills/<name>/SKILL.md`; there is no `commands/`
directory. `address-review`, `explain-diff`, `implement`, and `post-review` are
human-only (`disable-model-invocation: true`). `user-invocable` defaults to
`true`; `/zoom-out` also allows model invocation.

| Command | Replaces | Usage |
|---|---|---|
| `/show-me` | walls of prose for code shape, flow, state, ownership, dependencies, and before/after structure; also composed by design/review workflows | `/show-me`, `/show-me auth retry as sequence` |
| `/open-pr` | ticket + branch + verify + lint + ship mega-prompt (handles fresh + mid-fix) | `/open-pr FAC-456` |
| `/review-pr` | full review workflows, now a skill: first-pass (per-type verification, repro for bugs) / `deeper` (paired confirm-or-kill wave) / `follow-up` (three-lane re-review from worktree dossier `./.agents/review.md`); `/post-review` publishes + writes dossier | `/review-pr 123`, `deeper`, `re-review` |
| `/address-review` | read reviewer feedback → triage → fix → respond to threads | `/address-review 123` |
| `/post-review` | publish approved inline findings + review verdict | `/post-review 123` |
| `/explain-diff` | standalone HTML walkthrough with diagrams + interactive quiz | `/explain-diff 123` |
| `/zoom-out` | broader module and caller context in the project's vocabulary | `/zoom-out` |
| `/demo-pr` | tuistory before/after filming | `/demo-pr 123` |
| `/implement` | spec-first exploration + planning; waits for approval before coding | `/implement FAC-789` or `/implement "<description>"` |
| `/retrospective` | stranger-review your own diff for entropy (dead weight / junk / perf / drift / scope) | `/retrospective` |
| `/update-skill` | reflect → update skill → critique ×2 → PR | `/update-skill linear-cli` |
| `/split-pr` | split long branch into stacked or independent PRs via cherry-pick | `/split-pr feat/big-branch` |

## Git Workflow Skills

| Skill | Owns |
|---|---|
| **`sync-target`** | Sync one active PR branch without changing its review shape; inspect stack impact, defer dormant descendants during rapid iteration, otherwise merge ordinary branches or replay rewritten/split branches safely. |
| **`stack-cli`** | Squash-safe stack lifecycle: preview propagation, judge whether descendants need freshness now, apply root/descendant repair and retargeting, merge bottom-up, or undo mutations. |
| **`git-advanced`** | Rebase, cherry-pick, commit surgery, reflog recovery, and other history-editing primitives. |

## Background Atoms (composed by workflow skills)

| Atom | Owns | Composed by |
|---|---|---|
| **ticket-branch** | Ticket resolve/create, direct parent/child context, branch checkout | `/open-pr`, `/update-skill`, `/split-pr` |
| **quality-ship** | Quality checks (foreground live + logged evidence), commit, push. Not PR creation. | `/open-pr`, `/update-skill`, `/split-pr`, `/address-review` |
| **pr-description** | Diff analysis, outcome-first title, first-screen skim gate, structured PR body, computed diff-composition table for large diffs (`scripts/diff-composition.py`), live visual evidence (post-open) | `/open-pr`, `/update-skill`, `/split-pr` |
| **pr-context** | Fetch PR metadata + diff + conversation + linked ticket | `/review-pr`, `/address-review`, `/demo-pr` |
| **voice** | Lean router to craft, external replies, review judgment, and anti-slop references. Audience-aware prose across apps; cut ceremony while preserving reasoning, evidence, scope, caveats, and action. Owns load-bearing warmth/humility and the canonical review severity taxonomy. | `/review-pr`, `/post-review`, `/address-review`, pr-description, linear-cli, slack-cli, external messages/replies |
| **structural-review** | Code-judo simplification hunt + structural tripwires (1k-line crossings, spaghetti growth, boundary leaks, contract muddying, orchestration smells); defers severity to voice | `/review-pr` (heavy-worker sweep) |
| **orchestrate** | Coordination reference: four-droid staffing, one writer per change, stable prerequisites/QA, resume vs fresh, restaff-or-block. Readability gate: inspect the diff, clarify with its author or reject avoidable complexity; obfuscated code is not mergeable. Three seats: Astra main, explicitly assigned Astra child, or top-level Fable told "be an orchestrator". | orchestrator seats (background) |

## Droids (model-pinned)

Definitions live in `~/.agents/droids/<name>.md` (canonical); `~/.factory/droids`
is a symlink to that directory, so the runtime discovers them with no copy step.
All four pin an exact custom model id at `reasoningEffort: high` and omit
`tools`/`mcpServers`: the definitions restrict nothing, though runtime policy
may still withhold tools (children currently lack Task). Factory-generated mission
droids land in the same directory and are gitignored. Staffing policy is the
**orchestrate** atom; ordinary workers never load it.

| Droid | Model | Prefer for |
|---|---|---|
| `glm` | `custom:factory://glm-5-3-flash` | bounded implementation, evidence gathering, writing |
| `sol` | `custom:openai://gpt-5-6-sol-fast` | persistent implementation, research, adversarial review |
| `fable` | `custom:factory://fable-5-1` | approach design, coupled or taste-sensitive code, UI, structural review |
| `astra` | `custom:openai://gpt-6` | diagnosis, QA, computer use; no durable code |

## Installed Tooling

| Tool | Install | Wired into |
|---|---|---|
| `rtk` | `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh \| sh` | `hooks/pre_tool_use/rtk_rewrite.py` — transparent `Execute` rewriter. Per-surface toggles in `configs/droid.toml`. |
| check runner + guard | built-in (`scripts/run-check`, `hooks/pre_tool_use/check_guard.py`) | One no-shell grammar: `run-check <label> [--cwd ...] [--env ...] -- <argv...>`. The Python runner applies the nearest `.nvmrc` through NVM, forwards cancellation signals, and keeps 50 logs; the guard denies recognized raw validators and composition around the canonical runner. Toggle/`tools` vocabulary in `configs/droid.toml`. |
| `slop-scan` | `npm install -g slop-scan` | `/retrospective`, `/review-pr`, `quality-ship` |
| `react-doctor` | `npm install -g react-doctor` (Node >=22) | `quality-ship` (React branch), `react-doctor` skill |
| `vulture` | `uv tool install vulture` | `quality-ship` (Python branch) |
| `arxiv2md` | `uv tool install arxiv2md` | Ad-hoc: pipe arXiv papers into context |
| `tirith` | [release tarball](https://github.com/sheeki03/tirith/releases/latest) | Shell hook only (activated in `~/.zshrc`); not wired into droids |
| `witr` | `go install github.com/pranshuparmar/witr/cmd/witr@latest` | Standalone "why is this running?" tracer |
| `nlsh` | `go install github.com/abakermi/nlsh@latest` | Wrapper + inlined config in `~/.zshrc` (materializes `~/.nlshrc` on call); uses OpenRouter via `OPENROUTER_API_KEY` |
| `excalirender` | At `~/.local/bin/`; if missing: `curl -fsSL https://raw.githubusercontent.com/JonRC/excalirender/main/install.sh \| PREFIX=$HOME/.local sh` | Renders `.excalidraw` → PNG/SVG/PDF, no browser. Excalidraw is a *format*, not an app. `pr-description` (artifacts.md), `excalidraw` skill |
| `gh-attach` | At `~/.local/bin/` | Uploads images/clips to GitHub's CDN for PR bodies. `pr-description` (artifacts.md, visual-evidence.md), `excalidraw` skill |
| `paperclip` MCP | HTTP MCP + `paperclip login` | Biomedical lit (`~/.factory/mcp.json`) |
| `paper-search` MCP | `npx -y paper-search-mcp-nodejs` | 14 academic platforms (`~/.factory/mcp.json`) |

## Session Environment

`hooks/session_start/env_vars.py` persists environment settings from
`[hooks.session_start.environment]` in `configs/droid.toml`. Use
`path_prepend` or `path_append` for ordered, deduplicated PATH additions:

```toml
[hooks.session_start.environment]
path_prepend = ["~/.local/bin"]
```

Set `export_session_id = true` in the same section to persist the session id as
`DROID_SESSION_ID` (used by `vscode-workspace` for per-session cleanup).
