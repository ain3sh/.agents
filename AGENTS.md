# AGENTS.md

Guidance for coding agents working in this repo.

## Project shape

Personal, runtime-agnostic **agent-config repo**: the single source of truth for
skills, slash commands, lifecycle hooks, prompts, and configs.

- `skills/<name>/SKILL.md` (+ optional `references/`, `templates/`, `agents/`,
  `data/`) — skill packages. Many are composable **atoms** (`pr-context`,
  `quality-ship`, `ticket-branch`, `pr-description`, `repo-conventions`) that
  workflow skills/commands pull in.
- `commands/*.md` — slash-command definitions; larger workflows live as skills
  (`open-pr`, `split-pr`, `update-skill`, ...).
- `hooks/` — Python lifecycle hooks grouped by event (`pre_tool_use/`,
  `session_start/`, `session_end/`, ...) over typed helpers in `hooks/utils/`.
  Start at `hooks/README.md`.
- `prompts/` — `SOUL.md`, `instructions/` (composed at SessionStart), and
  runtime `overrides/` (`CLAUDE.md`, `CODEX.md`).
- `configs/droid.toml` — all hook **behavior** lives here: tool policy, rtk,
  tirith, instruction-composition rules.
- `CHEATSHEET.md` — quick reference for commands, atoms, and installed tooling.

Local-only (gitignored): `.agents/`, `logs/`, `*.env`, `__pycache__/`,
`.ruff_cache/`. `hooks/session_end/store_artifacts.py` writes session tails and
todo snapshots to `.agents/{MM_DD_YYYY}/`. Skills install into each agent's own
location (for droid, as plugins), so `~/.factory/skills` stays empty.

## Verify before committing

- **Python hooks**: `ruff check hooks/ && ruff format --check hooks/`. Reuse the
  typed I/O in `hooks/utils` (`read_input_as`, `emit`, `exit`) instead of parsing
  stdin by hand.
- **Hook behavior**: lint can't catch it. Trigger the real lifecycle event and
  confirm the hook fails *open* (passes through) on the unhappy path.
  `hooks/session_start/debug.sh` dumps env/tool diagnostics.
- **`configs/droid.toml`**: keep it valid TOML; it drives all hook behavior, so a
  mistake here silently changes what runs.
- **Markdown** (skills/commands/prompts) has no build step; just keep `SKILL.md`
  frontmatter (`name`, `description`) intact, since `description` is the trigger.

## Pushing changes

No release/CI here; changes land directly on `main`.

**Auth:** this repo is `github.com/ain3sh/.agents` (personal account), but the
active gh account is usually `factory-ain3sh` (work), which can't push to it. If
you're operating as Ainesh, wrap every push: `gh auth switch --user ain3sh` →
push → `gh auth switch --user factory-ain3sh`.

- Commits: Conventional Commits scoped by component: the generic type
  (`feat(skill)`, `fix(hooks)`, `feat(command)`) or the specific name
  (`fix(worktree-setup)`).
- After editing a skill/command, re-sync to the agents in `.skill-lock.json` so
  the runtimes pick it up.

## Conventions

- **One concern per skill.** Keep `SKILL.md` a lean entrypoint and push depth
  into `references/*.md` loaded on demand. Atoms compose into commands; see
  `CHEATSHEET.md` for the map.
- **Hooks fail open.** Best-effort features (rtk, tirith) pass through on missing
  tools or errors instead of blocking; mirror that, and gate new behavior behind
  a `configs/droid.toml` toggle rather than hardcoding it.
- **Never commit secrets.** `*.env` and `~/.factory/.env` are loaded at
  SessionStart and stay out of git.
- **Keep the cheatsheet current.** When a skill/command's surface changes,
  update `CHEATSHEET.md` in the same commit so the reference doesn't drift.

## Next ideas

- 
