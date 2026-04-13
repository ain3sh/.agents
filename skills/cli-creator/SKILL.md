---
name: cli-creator
description: Build a composable CLI from API docs, an OpenAPI spec, existing curl examples, an SDK, a web app, an admin tool, or a local script. Use when the user wants to create a command-line tool that can run from any repo, expose composable read/write commands, return stable JSON, manage auth, and pair with a companion skill.
---

# CLI Creator

Create a real CLI that future sessions can run by command name from any working directory.

This skill is for durable tools, not one-off scripts. If a short script in the current repo solves the task, write the script there instead.

## Start

Name the target tool, its source, and the first real jobs it should do:

- **Source**: API docs, OpenAPI JSON, SDK docs, curl examples, browser app, existing internal script, article, or working shell history.
- **Jobs**: literal reads/writes such as `list drafts`, `download failed job logs`, `search messages`, `upload media`, `read queue schedule`.
- **Install name**: a short binary name such as `ci-logs`, `slack-cli`, `sentry-cli`, or `buildkite-logs`.

Prefer `~/code/clis/<tool-name>` when the user wants a personal tool and has not named a repo.

Before scaffolding, check whether the proposed command already exists:

```bash
command -v <tool-name> || true
```

## Choose the runtime

Inspect the user's machine and source material:

```bash
command -v cargo rustc node pnpm npm python3 uv || true
```

Then choose the least surprising toolchain:

- Default to **Rust** for a durable CLI: one fast binary, strong argument parsing, good JSON handling, easy install into `~/.local/bin`.
- Use **TypeScript/Node** when the official SDK, auth helper, or existing repo tooling is the reason the CLI can be better.
- Use **Python** when the source is data science, local file transforms, notebooks, SQLite/CSV/JSON analysis, or Python-heavy admin tooling.

State the choice in one sentence before scaffolding.

## Command contract

Sketch the command surface before coding. Read [references/agent-cli-patterns.md](references/agent-cli-patterns.md) for the expected composable CLI shape.

Build toward this surface:

- `tool-name --help` shows every major capability.
- `tool-name --json doctor` verifies config, auth, version, endpoint reachability.
- `tool-name init ...` stores local config when env-only auth is painful.
- Discovery commands find accounts, projects, workspaces, teams, channels, repos, dashboards.
- Resolve commands turn names, URLs, slugs, permalinks into stable IDs.
- Read commands fetch exact objects and list/search collections. Paginated lists support a bounded `--limit`.
- Write commands do one named action each: create, update, delete, upload, schedule. They accept the narrowest stable ID, support `--dry-run` when the service allows it.
- `--json` returns stable machine-readable output.
- A raw escape hatch exists: `request`, `api`, or the nearest honest name.

Do not expose only a generic `request` command. Give high-level verbs for the repeated jobs.

## Auth and config

Support the boring paths first:

1. Environment variable using the service's standard name (`GITHUB_TOKEN`).
2. User config under `~/.<tool-name>/config.toml`.
3. `--api-key` flag only for explicit one-off tests.

Never print full tokens. `doctor --json` should say whether a token is available and what setup step is missing.

## Build workflow

1. Read the source just enough to inventory resources, auth, pagination, IDs, rate limits.
2. Sketch the command list. Keep names short and shell-friendly.
3. Scaffold the CLI with a README.
4. Implement `doctor`, discovery, resolve, read commands, one narrow write path if requested, and the raw escape hatch.
5. Install on PATH so `tool-name ...` works outside the source folder.
6. Smoke test from another directory or `/tmp`. Run `command -v <tool-name>`, `<tool-name> --help`, and `<tool-name> --json doctor`.
7. Run format, typecheck/build, unit tests.

## Runtime defaults

### Rust

- `clap` for commands, `reqwest` for HTTP, `serde`/`serde_json` for payloads, `toml` for config, `anyhow` for errors.
- Add `make install-local` that builds release and installs into `~/.local/bin`.

### TypeScript/Node

- `commander` or `cac` for commands, native `fetch` or the official SDK for API calls.
- `package.json` `bin` entry. Install via `pnpm link --global` or a Makefile wrapper.

### Python

- `argparse` or `typer` for commands, `requests`/`httpx`/stdlib for HTTP.
- `pyproject.toml` console script or executable wrapper. `make install-local` target.

## Companion skill

After the CLI works, create or update a companion skill at `~/.agents/skills/<tool-name>/SKILL.md`.

Write it in the order a future session should use the CLI:

1. How to verify the installed command exists.
2. Which command to run first.
3. How auth is configured.
4. The safe read path.
5. The intended draft/write path.
6. The raw escape hatch.
7. What not to do without explicit user approval.
8. Three copy-pasteable command examples.
