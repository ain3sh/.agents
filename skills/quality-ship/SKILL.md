---
name: quality-ship
description: Shared atom for running quality checks, committing, and pushing. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# Quality Checks + Ship

## Quality Checks

### Pre-check: worktree environment

Before running any checks, determine if you're in a git worktree:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
[ "$(git rev-parse --show-toplevel)" != "$MAIN_REPO" ] && echo "WORKTREE"
```

If in a worktree, follow the **worktree-setup** skill to symlink dependencies before proceeding. Never `npm install` or `pip install` in a worktree.

### Run all detected checks

Detect the project's tooling from config files at the repo root, then run each applicable check:

| Check | Detection signals | Typical command |
|-------|-------------------|-----------------|
| Format | `.prettierrc*`, `biome.json`, `dprint.json` | `npm run format --write` or `npx prettier --write` or equivalent |
| Lint fix | `eslint.config*`, `.eslintrc*`, `biome.json` | `npm run fix` or `npx eslint --fix` |
| Dead code | `knip.*`, `knip` in package.json scripts | `npm run knip` or `npx knip` |
| Type check | `tsconfig.json` | `npm run typecheck` or `npx tsc --noEmit` |
| Tests | `jest.config*`, `vitest.config*`, `pytest.ini` | Run relevant test subset for changed files |

- Check `package.json` scripts for canonical commands (`format`, `fix`, `lint`, `knip`, `test`, `typecheck`).
- Fix any issues found. Re-run until clean.

**Run every check with a detection signal present -- do not skip any.** A CI pipeline will typically gate on all of these; missing one here means a failed check after push.

### Monorepo scoping: use turbo, not direct invocation

In monorepos with `turbo.json`, **always** use `turbo run <task> --filter=<package>` instead of direct tool invocation for **all** checks: `format`, `lint`, `knip`, `typecheck`, and `test`. Direct invocation misses workspace-level configuration (path aliases, package-scoped configs) and runs against the entire repo unnecessarily.

In monorepos without turbo, scope validators to the changed packages. Use `git diff --name-only` against the base branch to identify affected packages, then run checks from within those package directories.

## Commit

```bash
git add -A
git commit -m "<type>(<scope>): <description> (<TICKET-ID>)"
```

- Conventional commit format. Infer type from changes: `fix`, `feat`, `refactor`, `docs`, `chore`, `test`, etc.
- Reference the Linear ticket ID in the message.

## Push

```bash
git push -u origin HEAD
```
