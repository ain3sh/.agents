# Cleanup targets

## Profiles

`clean_home.py` defaults to the aggressive profile. Its base cache set is:

- `~/.cache` contents
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

Approved generated basenames:

```text
node_modules target dist build .next .turbo coverage .venv
.pytest_cache .ruff_cache
```

The scripts do not remove browser profiles, Wine prefixes, VM disks, project
source, Downloads, datasets, model files, `~/.factory/sessions`, or arbitrary
application state.

## Fast escalation order

1. Snapshot protected paths.
2. `clean_tmp.py --apply`
3. `clean_home.py --apply`
4. Add exact `--generated` paths already known to be reproducible.
5. Re-run `df`; inspect one bounded top-level directory only if still needed.

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
