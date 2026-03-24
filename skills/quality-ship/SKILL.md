---
name: quality-ship
description: Shared atom for running quality checks, committing, pushing, and opening a PR. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# Quality Checks + Ship

## Quality Checks

Detect the project's tooling from config files at the repo root, then run each applicable check:

| Check | Detection signals | Typical command |
|-------|-------------------|-----------------|
| Format | `.prettierrc*`, `biome.json`, `dprint.json` | `npm run format` or equivalent |
| Lint fix | `eslint.config*`, `.eslintrc*`, `biome.json` | `npm run fix` or `npx eslint --fix` |
| Dead code | `knip.*`, `knip` in package.json scripts | `npm run knip` or `npx knip` |
| Type check | `tsconfig.json` | `npm run typecheck` or `npx tsc --noEmit` |
| Tests | `jest.config*`, `vitest.config*`, `pytest.ini` | Run relevant test subset for changed files |

- Check `package.json` scripts for canonical commands (`format`, `fix`, `lint`, `knip`, `test`, `typecheck`).
- Fix any issues found. Re-run until clean.

### Monorepo lint: use turbo, not direct invocation

In monorepos with `turbo.json`, **always** use `turbo run lint --filter=<package>` instead of running `npx eslint` directly. Direct invocation breaks on path aliases (`@/utils/...`) because ESLint doesn't resolve the project's `tsconfig` paths without turbo's workspace setup. The same applies to `typecheck` and `test`.

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

## Open PR

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
gh pr create \
  --base "$DEFAULT_BRANCH" \
  --title "<type>(<scope>): <description> (<TICKET-ID>)" \
  --body "<body>"
```

PR body structure:
- **Summary**: What changed and why.
- **Linear ticket**: Link (use `linear i link <ID>`).
- **Testing**: What was tested and how.
- **Screenshots / output**: If applicable.

Report the PR URL when done.
