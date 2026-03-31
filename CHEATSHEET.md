## Reference Skills (auto-loaded by Droid)

- **`linear-cli`** -- linear-cli commands, agent output flags, chaining patterns
- **`slack`** -- slck commands, bot/user token guidance, search flags
- **`worktree-setup`** -- node_modules symlink rule, never npm install in a worktree

## Workflow Commands

| Command | Replaces | Usage |
|---|---|---|
| `/open-ticket` | "load linear skill and source .env.local to open ticket" | `/open-ticket Fix tooltip` |
| `/open-pr` | ticket + branch + verify + lint + ship mega-prompt | `/open-pr FAC-456` |
| `/review-pr` | review prompt + separate "post comments via gh api" prompt | `/review-pr 123` |
| `/address-review` | (new) read reviewer feedback, triage, fix, respond to threads | `/address-review 123` |
| `/demo-pr` | tuistory before/after filming prompt | `/demo-pr 123` |
| `/implement` | "exploration and planning, don't take ugly path" prompt | `/implement FAC-789` |
| `/update-skill` | "reflect + update skill + critique x2 + PR" prompt | `/update-skill linear-cli` |
| `/split-prs` | (new) break a long-running branch into clean separate PRs | `/split-prs feat/big-branch` |

`/open-pr` handles the full state matrix (fix already applied vs starting fresh, bug vs feature) and auto-detects project tooling.

`/review-pr` classifies the PR type (bug fix / feature / refactor / CI), runs type-specific verification (mandatory repro for bugs), then shared criteria. Posts threaded line comments; REQUEST_CHANGES only if issues found.

`/split-prs` analyzes commit groupings, proposes a split plan, auto-decides stacked vs independent based on file overlap, then executes via cherry-pick/diff-apply (never manual re-typing).

`/implement` presents a spec and waits for approval before writing code.

## Background Atoms (Droid-only, not in `/` menu)

| Atom | Purpose | Composed by |
|---|---|---|
| **ticket-branch** | Create/resolve Linear ticket (with description + parent search) + checkout branch | `/open-pr`, `/update-skill`, `/split-prs` |
| **quality-ship** | Run detected quality checks (lint, format, typecheck, tests), commit, push | `/open-pr`, `/update-skill`, `/split-prs`, `/address-review` |
| **pr-description** | Analyze diff, format conventional-commit title, write structured 4-section PR body | `/open-pr`, `/update-skill`, `/split-prs` |
| **pr-context** | Gather PR metadata, diff, conversation, linked Linear ticket | `/review-pr`, `/address-review`, `/demo-pr` |

### Atom responsibilities (separation of concerns)

- **quality-ship** owns: tooling detection, check execution, fix loops, commit (conventional format), push. Does *not* touch PR creation or description.
- **pr-description** owns: diff analysis, title formatting, PR body template (Description, Related Issue, Risk & Impact, Testing), contextual additions (stacked/split PR notes).
- **ticket-branch** owns: ticket resolution or creation (with meaningful description, parent linking), branch checkout with naming conventions.
- **pr-context** owns: fetching existing PR state (metadata, diff, comments, linked ticket) for review/response workflows.
