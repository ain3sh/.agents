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

After the branch chain and PR targets exist, **stack-cli owns stack-wide
propagation**. Preview the impact whenever a parent moves, but apply only when
fresh descendants are worth the replay cost.

Load **stack-cli**, then:

```bash
stack status
stack sync <any-branch-in-the-stack> # dry run
```

### Propagate or defer

Load **stack-cli**'s `references/propagation.md`. It owns the decision inputs,
apply gate, deferred-descendant contract, and restack triggers.

When propagating, `stack sync` covers:

- **Parent gained commits:** replay descendants onto the updated parent.
- **Parent squash-merged:** retarget children to the trunk and drop redundant
  parent history using persisted merge-base anchors.
- **Trunk moved:** replay the root, then descendants, bottom-up.

Apply the reviewed plan:

```bash
stack sync --apply <any-branch-in-the-stack>
```

If the dry run reaches unrelated roots or an unexpected PR, stop and inspect
with `stack status` or `stack doctor`. If the user requested one branch but the
preview writes descendants, summarize that expanded scope and ask before
applying it.
`stack sync --apply` creates backups and an undo journal; on replay failure it
restores the original branch and names the branch requiring manual conflict
resolution. Do not replace its exact pushes with bare `--force`.

## Review and merge discipline

- **Merge bottom-up, one at a time.** Preview with `stack merge`; use
  `stack merge --apply` for immediate squash-merge and descendant repair, or
  `stack merge --auto` to wait for protections before repair. A misconfigured
  merge queue can merge a child against the wrong diff; disable it for stacks.
- **Squash-merge each PR** unless project policy forbids it. Squash keeps `$BASE` linear and makes the restack-after-merge step deterministic.
- **Avoid mid-review rebases on the bottom PR.** Reviewers lose their comment anchors when commit SHAs change. Wait for the current review round to close, then rebase.
- **Close PRs that become empty after a rebase.** If a PR's diff collapses to zero because an earlier PR absorbed its changes, close it with a one-line explanation -- do not leave empty PRs open.
- **Do not invite code review on a PR whose parent hasn't received approval yet**, unless the review is explicitly scoped to the delta. Reviewers will otherwise try to review the cumulative diff and conflate feedback across PRs.

Do not substitute GitHub's `gh stack`; this workflow uses the local squash-safe
`stack` CLI documented by **stack-cli**.

## Pitfalls specific to stacked

| Pitfall | Cause | Mitigation |
|---|---|---|
| Child PR diff shows parent's changes too | Opened with `--base $DEFAULT_BRANCH` instead of parent branch | Preview and repair with `stack sync` |
| Stack rot -- many small rebases churning | Parent under active review, long stack depth | Pause the stack: mark top PRs as draft until the bottom lands |
| Reviewer comment on PR 2 actually applies to PR 1 | Stack context not clear in body | Lead every stacked PR body with the "part K of N, depends on #X" block |
| Merge queue rejects stacked PRs | Queue treats each PR as independently targeting `$BASE` | Disable the queue for the stacked series, or flatten to atomic first |
| CI passes on PR 1 but fails on PR 2 against `$BASE` | PR 2's target is parent, so CI runs against PR 1's state, not `$BASE` | Run `stack sync --apply` after the parent moves, then wait for child CI |
| Applied stack repair was wrong | Preview scope was not inspected | Run `stack undo`, inspect it, then `stack undo --apply` |
