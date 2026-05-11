# Atomic (Independent) PRs

The default shape. Each PR branches off `$BASE`, carries one concern, and merges in any order without blocking the others.

## When to pick atomic

All of:

- Concern groups touch disjoint files (run the overlap check below).
- No logical dependency -- each PR compiles, tests, and reads as a complete change on its own.
- Each PR's Description can be written without referencing a sibling PR.

## Overlap check

Before committing to atomic, verify no file appears in two groups. Substitute real paths (space-separated) for each group, then run:

```bash
G1="src/auth/handlers.ts src/auth/types.ts"
G2="src/billing/invoices.ts src/billing/api.ts"
G3="src/notifications/email.ts"

{
  for f in $G1; do echo "g1 $f"; done
  for f in $G2; do echo "g2 $f"; done
  for f in $G3; do echo "g3 $f"; done
} | awk '{print $2}' | sort | uniq -d
```

Any file printed by the pipeline appears in more than one group -- that's the overlap. Interpret:

- **No output** -- groups are truly disjoint. Atomic is safe.
- **Cosmetic overlap** (one line in a barrel export, an unrelated `package.json` bump, a lockfile regeneration, a formatter sweep) -- tolerable. Address at merge time: the second-to-land PR does a one-commit rebase on the merged base.
- **Real overlap** (same function edited, shared type change, same schema migration, same test file asserting both behaviors) -- switch to stacked. See `stacked.md`.

## Execution

### Branch per PR, off `$BASE`

```bash
git fetch origin
git checkout -b "<owner>/<prefix>-<number>-<stub>" "origin/$BASE"
```

Run once per PR in the plan. Every PR's branch has the same parent (`origin/$BASE`) -- the fan-out, not a chain, is what makes this atomic.

### Apply commits

Per-concern commit lists were decided in the plan. Pick the right primitive:

- **Clean commits**:
  ```bash
  git cherry-pick <sha1> <sha2> ...
  ```
- **Hunks from a grab-bag commit** (rare after step 4a pre-split surgery, but not zero):
  ```bash
  git cherry-pick --no-commit <sha>
  git reset HEAD                        # unstage everything
  git add -p                            # stage only this PR's hunks
  git checkout -- .                     # discard the rest
  git commit -m "<subject>"
  ```
- **Specific files from a commit**:
  ```bash
  git diff <sha>~1..<sha> -- <paths> | git apply
  git add <paths>
  git commit -m "<subject>"
  ```

### Quality-ship and open

Load **quality-ship**, emit its checklist, run detected validators, commit any fixups, push. Then load **pr-description**, tick its section-0 checklist, write the body.

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
gh pr create --base "$DEFAULT_BRANCH" --title "<title>" --body-file /tmp/pr-body.md
```

### Body language for atomic PRs

Under `Description`, spell out the series context so reviewers don't assume a dependency that isn't there:

```markdown
## Description

<2-4 sentences on this PR's standalone contribution.>

Splits `<original-branch>` into N independent PRs (atomic -- any merge order):
- This PR: <concern>
- #<other>: <concern>
- #<other>: <concern>
```

## Pitfalls specific to atomic

| Pitfall | Cause | Mitigation |
|---|---|---|
| Merge-time conflict you didn't predict | A "neutral" file (barrel export, lockfile, snapshot) was touched by two PRs | The second PR does a one-commit rebase on the merged base. Cheap -- do not pre-emptively stack to avoid this. |
| Reviewer assumes merge order | Body didn't explicitly say "any order" | Always include the atomic series block (above) |
| Shared type edit hidden in one PR | Dropped during hunk staging | Re-run the overlap check after all PR branches are built but before any are pushed |
| Tests pass per PR but break on `$BASE` after the second lands | PR 1 changed a signature; PR 2 added a caller with the old signature -- you missed a dependency | Run the combined shape locally (`git merge --no-ff` both heads onto `$BASE` in a scratch) before pushing; if it breaks, one concern actually depends on the other -- switch to stacked |
| Cherry-pick conflict that needs sibling code | Real logical dependency disguised as disjoint files | See "Abandon atomic" below |

## Abandon atomic mid-split

If any of these hits after branching started:

- Cherry-pick conflict that can only be resolved by pulling code from a sibling PR.
- Tests only pass on PR K when PR K-1 is also applied.
- Reviewer feedback on PR 1 that forces a shape change in PR 2.

Stop. Delete the scratch branches. Rebuild the plan as stacked (see `stacked.md`). The atomic split was wrong about independence -- don't paper over it with workaround commits.
