# Cleanup targets

## Profiles

`clean_home.py` defaults to the aggressive profile. Its base cache set is:

- `~/.cache` contents except dsx cache/index paths (including configured overrides)
- Baloo index
- Factory, Factory DEV, VS Code, Electron, and gcloud caches/logs
- Factory logs, snapshots, and plugin cache — never Factory sessions
- Cargo registry/git caches
- Bun, NVM, and npm download caches
- user Trash

The default aggressive profile also deletes the pnpm content-addressed store,
prunes inactive toolchains, removes VS Code extensions except rust-analyzer,
and prunes unused Docker data including volumes. `--profile caches` opts out of
those four additions.

| Flag | Action |
|---|---|
| `--[no-]prune-toolchains` | Default on in aggressive mode. Keep the active NVM Node and rustup toolchains; remove other installed versions. If Rust's active toolchain cannot be determined, skip Rust. |
| `--[no-]prune-vscode-extensions` | Default on in aggressive mode. Remove extension directories except rust-analyzer and prefixes supplied with `--keep-vscode-extension`. Metadata files remain. |
| `--drop-all-vscode-extensions` | Remove rust-analyzer too. |
| `--[no-]prune-docker` | Default on in aggressive mode. Dry-run shows `docker system df`; apply runs `docker system prune -af --volumes`. This removes unused volumes too. |
| `--generated PATH` | Remove one exact generated directory after basename and protected-path validation. Repeat as needed. |

The entrypoint uses `--no-prune-docker`: unused volumes may contain persistent
data. Inspect Docker state and obtain authorization for its deletion scope
before enabling the script's default prune behavior.

Approved generated basenames:

```text
node_modules target dist build .next .turbo coverage .venv
.pytest_cache .ruff_cache
```

The home cleaner has no dedicated targets for browser profiles, Wine prefixes,
VM disks, project source, Downloads, datasets, models, or arbitrary application
state. That is not content detection: valuable files or active environments
inside cache/temporary targets still require explicit `--protect`. Factory
sessions and dsx paths are hard-protected independently of that inventory.

## Fast escalation order

1. Identify the pressured filesystem and snapshot actual protected paths.
   Include active test fixtures under `.cache`, not just models and sessions.
2. Preview and apply one bounded pass on that filesystem. `/tmp` on a separate
   tmpfs is not a candidate for reclaiming Btrfs device space.
3. Measure `df` and, on Btrfs, data/metadata usage and unallocated space.
4. If reclaim is inadequate, switch to bulk targets: unused dependency
   environments, generated build trees, or operator-selected stale worktrees.
   Do not chase repeated MB-scale cache wins against a multi-GiB deficit.
5. Preview one exact batch and obtain any unresolved scope approval, then apply
   and verify. Never silently defer authorized bulk cleanup into future work.

## Bulk worktree reclaim

Load `worktree-setup`. Use the repository's registered worktree list and trusted
workspace manifests to build an exact generated-target inventory; never
recursively discover dependency/build directories. Preserve the primary source,
current-task worktrees, active fixtures, recent sessions, and live process
references. Confirm inactivity and deletion scope with the operator when
uncertain, preferably in one batch rather than one directory at a time.

Root `node_modules`, package-local `node_modules`, `.turbo`, and generated build
trees are different targets. Root-only cleanup can leave local environments
behind; local-only cleanup can leave the root mirror holding most space.
Shared hardlinks/reflinks also make directory counts a poor reclaim estimate.
If measured reclaim is small, choose the next bulk class instead of assuming
hundreds of removed directories solved the problem.

Whole-worktree removal is distinct from generated-directory cleanup. Prefer
the owning worktree tool for an operator-approved stale-worktree batch; preserve
dirty/untracked source or obtain explicit disposition before removal. Do not
delete branches or valuable source merely because aggressive cleanup was
requested. Stop overlapping automation when the operator takes ownership.

For session recency, dsx lists default to 25 entries. Do not mistake the default
page for a complete active-worktree inventory. Query the latest session per
exact worktree (`dsx list --project /absolute/worktree --all --sort updated -n 1
--json`), check returned cwd/update times, and independently inspect live
process references.

## Extension retention

Retention uses directory-name prefixes:

```bash
--keep-vscode-extension rust-lang.rust-analyzer-
--keep-vscode-extension anthropic.claude-code-
```

Omit a prefix to delete that extension. Reinstallation remains the recovery
path; settings outside the extension directory are not targeted.

## Protected paths

Repeat `--protect` for every irreplaceable item:

```bash
--protect "$HOME/path/to/model.gguf" \
--protect "$HOME/path/to/vm.qcow2"
```

Apply refuses to proceed when a listed path is missing unless
`--allow-missing-protected` is explicit. That override only acknowledges prior
absence; it does not make the missing data recoverable.

`clean_tmp.py --protect /tmp/container/evidence.patch` retains the entire
`/tmp/container` direct child. A protected root/ancestor retains all children.
Missing explicitly protected paths stop both dry-run and apply. The automatic
dsx exclusions do not require an unused default cache path to exist.
