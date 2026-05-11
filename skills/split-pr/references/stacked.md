# Stacked PRs

Stacked PRs form a linear chain: PR N's branch targets PR N-1's branch, not `$BASE`. They enforce merge order: PR 2 cannot land without PR 1 first. Use only when atomic is geometrically impossible.

## When to pick stacked

Any of:

- Concern groups share real logic -- same function, same schema, same migration, same type a child consumes.
- One group is a **prerequisite refactor** and the rest build on the refactored shape.
- You tried atomic and hit a cherry-pick conflict that could only be resolved by pulling sibling code.

**Hard cap: stack depth <= 3.** Past three, restacking churn and reviewer cognitive load dominate the benefit. If you genuinely need more, land the bottom half first and re-split the remainder as a fresh pass.

## Execution

### Branch chain

Branch PR K's working branch off **PR K-1's branch tip**, not off `$BASE`:

```bash
# PR 1 -- off base, as with atomic
git fetch origin
git checkout -b "<owner>/<prefix>-<num1>-<stub1>" "origin/$BASE"
# ... apply commits ...

# PR 2 -- off PR 1's local branch
git checkout -b "<owner>/<prefix>-<num2>-<stub2>" "<owner>/<prefix>-<num1>-<stub1>"
# ... apply commits ...

# PR 3 -- off PR 2's local branch
git checkout -b "<owner>/<prefix>-<num3>-<stub3>" "<owner>/<prefix>-<num2>-<stub2>"
```

Use incrementing numbers in the stub so order is obvious on the remote.

### Apply commits per-PR

Same primitives as atomic (cherry-pick, hunk stage, diff-apply -- see `atomic.md`). A cherry-pick into PR 2's branch that touches a file PR 1 already modified is **expected and fine** -- PR 1's changes are already present as committed history on PR 2's branch.

### Quality-ship and open, bottom-up

Process one PR at a time, in order (PR 1 -> PR 2 -> ...):

1. Load **quality-ship** on that branch; run detected validators; commit any fixups; push.
2. Load **pr-description**; tick section-0 checklist.
3. Open the PR targeting the **parent branch**, not `$BASE`:
   ```bash
   gh pr create \
     --base "<parent-branch-name>" \
     --title "<title>" \
     --body-file /tmp/pr-body.md
   ```
   For PR 1: `--base "$DEFAULT_BRANCH"`. For PR 2+: `--base "<previous-pr-branch>"`.

**Do not open a later PR before its parent is pushed** -- `gh pr create` fails with "base branch does not exist" otherwise.

### Body language for stacked PRs

Lead the `Description` with the stack context:

```markdown
## Description

<2-4 sentences on this PR's contribution.>

Stacked: part K of N. Depends on #<parent-pr-num>. Merges only after parent lands.

- #<PR1>: <short scope> <-- base of stack
- #<PR2>: <short scope> <-- this PR
- #<PR3>: <short scope>
```

Under `Risk & Impact`, list any risk that is cumulative-over-the-stack (e.g., a migration in PR 1 plus a consumer in PR 2 -- if PR 1 rolls back, PR 2 is broken in production).

## Restacking

When the parent moves -- new commits, a rebase, or merge into `$BASE` -- child PRs must be kept in sync. Three scenarios.

### Scenario A: Parent gained new commits (e.g., review feedback)

```bash
git checkout <child-branch>
git fetch origin
git rebase "origin/<parent-branch>"
# resolve any conflicts, then:
git push --force-with-lease
```

**Always `--force-with-lease`, never bare `--force`.** The lease prevents overwriting an unexpected remote update from a collaborator or a CI amendment.

For stack depth >=2, propagate bottom-up, rebasing each child on its updated parent:

```bash
git fetch origin
git checkout <pr1-branch> && git rebase "origin/$BASE"              && git push --force-with-lease
git checkout <pr2-branch> && git rebase "origin/<pr1-branch>"       && git push --force-with-lease
git checkout <pr3-branch> && git rebase "origin/<pr2-branch>"       && git push --force-with-lease
```

### Scenario B: Parent PR merged into `$BASE`

GitHub auto-retargets child PRs from the merged parent branch to `$BASE`. **Verify**, don't assume -- then rebase locally to drop the now-redundant parent commits:

```bash
gh pr view <child-pr> --json baseRefName --jq '.baseRefName'   # should now be $BASE
git checkout <child-branch>
git fetch origin
git rebase "origin/$BASE"                                      # drops commits already on $BASE via parent
git push --force-with-lease
```

If auto-retarget didn't happen, retarget via REST (`gh pr edit --base` is broken -- see `pr-context`):

```bash
gh api "repos/$REPO/pulls/<child-pr>" -X PATCH -f base="$DEFAULT_BRANCH"
```

**Merge-strategy implications:**

- **Squash-merge** (typical) -- parent's individual commits are replaced by a single squashed commit on `$BASE`. Your rebase onto `$BASE` drops the individual commits as duplicates when hunks match exactly; if the squash introduced editorial changes, expect one round of conflict resolution. Resolve by keeping the squashed form -- that's the canonical history now.
- **Merge commit** -- parent's commits exist verbatim on `$BASE` already. Rebase is usually a clean no-op.
- **Rebase-and-merge** -- similar to squash but preserving per-commit granularity; treat like merge commit for restack purposes.

### Scenario C: `$BASE` moved while the stack was open

Other PRs landed on `$BASE` during your stack's review. Rebase the bottom of the stack onto the new `$BASE` first, then walk up:

```bash
git fetch origin
git checkout <pr1-branch> && git rebase "origin/$BASE"          && git push --force-with-lease
git checkout <pr2-branch> && git rebase "origin/<pr1-branch>"   && git push --force-with-lease
git checkout <pr3-branch> && git rebase "origin/<pr2-branch>"   && git push --force-with-lease
```

If the rebase produces conflicts you can't resolve inside the current PR's scope, your split is bleeding concerns -- revisit the plan.

## Review and merge discipline

- **Merge bottom-up, one at a time.** A top-of-stack PR targets its parent, not `$BASE` -- merging it lands the top commits into the parent's branch, which is almost never what you want. Land the bottom PR, let GitHub auto-retarget children to `$BASE`, rebase, then merge the next. A misconfigured merge queue can bypass this check and merge a stacked child against the wrong diff; disable the queue for stacked series.
- **Squash-merge each PR** unless project policy forbids it. Squash keeps `$BASE` linear and makes the restack-after-merge step deterministic.
- **Avoid mid-review rebases on the bottom PR.** Reviewers lose their comment anchors when commit SHAs change. Wait for the current review round to close, then rebase.
- **Close PRs that become empty after a rebase.** If a PR's diff collapses to zero because an earlier PR absorbed its changes, close it with a one-line explanation -- do not leave empty PRs open.
- **Do not invite code review on a PR whose parent hasn't received approval yet**, unless the review is explicitly scoped to the delta. Reviewers will otherwise try to review the cumulative diff and conflate feedback across PRs.

## Tooling alternatives (advisory)

Manual stacking is fine for depth <= 3. For deeper or frequent stacking, external tooling automates the restack-and-retarget dance:

- **Graphite (`gt`)** -- hosted + CLI, strong restack automation, visual stack viewer.
- **ghstack** -- Meta-originated, one-PR-per-commit model, best for monorepos with strict commit hygiene.
- **git-spice (`gs`) / spr** -- lightweight local CLIs, no hosted service.

This skill does not depend on any of them. Reach for tooling only if you're spending >10% of your time on restacking -- manual is faster otherwise.

## Pitfalls specific to stacked

| Pitfall | Cause | Mitigation |
|---|---|---|
| `gh pr edit --base` fails | Projects-classic GraphQL deprecation | `gh api "repos/$REPO/pulls/<n>" -X PATCH -f base="<branch>"` |
| Child PR diff shows parent's changes too | Opened with `--base $DEFAULT_BRANCH` instead of parent branch | Retarget via `gh api ... -X PATCH -f base="<parent-branch>"` |
| Stack rot -- many small rebases churning | Parent under active review, long stack depth | Pause the stack: mark top PRs as draft until the bottom lands |
| Reviewer comment on PR 2 actually applies to PR 1 | Stack context not clear in body | Lead every stacked PR body with the "part K of N, depends on #X" block |
| Merge queue rejects stacked PRs | Queue treats each PR as independently targeting `$BASE` | Disable the queue for the stacked series, or flatten to atomic first |
| CI passes on PR 1 but fails on PR 2 against `$BASE` | PR 2's target is parent, so CI runs against PR 1's state, not `$BASE` | After every parent rebase, push child and let CI re-run before re-requesting review |
| Force-push clobbered a collaborator's amendment | Used `--force` instead of `--force-with-lease` | Always `--force-with-lease`; if clobber happened, recover from the reflog (see **git-advanced**) |
