---
name: split-pr
description: Break a large branch into a series of small, reviewable PRs -- as atomic PRs (independent, any merge order) or stacked PRs (linear chain, strict order). Use when a branch has outgrown reviewability, mixes concerns, or a reviewer has asked to split it. Covers diff-level decomposition, branch mechanics, stack restacking, and per-PR quality-ship / pr-description hand-offs.
---

# Split PR

One large branch becomes N small PRs. The split is driven by the **diff**, not the commit graph -- commits are a storage artifact; a PR is a reviewable unit of intent. Pick **atomic** (independent branches off base, any merge order) whenever the diff allows it; fall back to **stacked** (chain of branches, strict merge order) only when file overlap or a logical dependency forces the chain.

## When to use

- A branch has outgrown reviewable size (~>400 lines changed or >15 files touched).
- A single branch carries multiple concerns (feature + refactor, two unrelated fixes, cross-package churn).
- A reviewer asked for the split, or you know the branch will land faster as a series.
- You're about to open a PR and the diff summary shows more than one story.

## When NOT to use

- Diff is already a single concern (one module, one bug, one feature slice). Ship as-is via `/open-pr`.
- The work is mid-flight and unverified -- finish and verify before splitting.
- The branch is a prototype or spike you won't merge -- split has no value.
- Exactly two commits, both trivial, same module -- just ship.

## Compose with

- **ticket-branch** -- creating a ticket + branch per PR in the series.
- **quality-ship** -- the per-PR validator and commit/push gate. Runs **once per PR**, not once at the end.
- **pr-description** -- the per-PR body writer. Mandatory hand-off at every `gh pr create`.
- **git-advanced** -- interactive rebase, cherry-pick, hunk-level commit splitting -- the movement primitives.
- **pr-context** -- REST replacements for every `gh pr edit` call. Every stacked-PR mutation (body, title, base retarget) goes through REST; `gh pr edit` is broken on any org with Projects (classic) enabled.

## 1. Analyze the diff

Do **not** look at commits first. The commit graph is a distraction -- most branches were not committed with future-split boundaries in mind.

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
BASE="${base:-$DEFAULT_BRANCH}"
git diff --stat "$BASE"...HEAD            # size per file
git diff --name-only "$BASE"...HEAD       # flat file list
git log --oneline --reverse "$BASE"..HEAD # commits, oldest first
git log --stat --reverse "$BASE"..HEAD    # commits + touched files
```

Build a **concern map**: group files by what they accomplish together (feature area, package, layer, concern type). A good concern map:

- Has 2-5 groups. More than that and the branch is incoherent -- fix the branch, don't PR-ize the mess.
- Puts type/schema/contract files in the lowest group -- they tend to block others.
- Flags any file that belongs to >1 group -- that file is the overlap your shape decision hinges on.

Then **classify every commit** against the concern map:

- **Clean** -- touches files in exactly one concern group. Cherry-pick as-is.
- **Grab-bag** -- touches files across >=2 groups. Needs hunk-level splitting, a pre-split `git rebase -i`, or decomposition via `git cherry-pick -n`.
- **Interdependent** -- commit B only makes sense after commit A in the same group (B modifies code A added). Same group, same PR, no split needed.

## 2. Propose the plan

Write it down before executing. Share with the user and wait for approval.

```
Split plan for <branch> -> <base>

Shape:   <atomic | stacked>   (reason: <file-overlap evidence>)

PR 1 -- <conventional-commit title>
  Concern:      <one sentence>
  Files:        <paths or globs>
  Commits:      <sha1 sha2 ...> or "hunks from <sha>"
  Depends on:   <none | PR K>
  Standalone?:  <yes -- reviewable without others | no -- needs PR K merged first>

PR 2 -- ...

Restructuring needed:
- <commit abc123>: split into <PR1-hunks> + <PR3-hunks>
- <commit def456>: reword message to "..."

Merge order:    <PR1 -> PR2 -> PR3> (stacked) | <any order> (atomic)
```

**The plan is gated.** Do not cherry-pick, rebase, or branch until the user approves. A wrong split costs more time than a well-planned one.

**Standalone-review test.** For every PR in the plan, write one sentence stating its standalone intent -- what a reviewer seeing only this PR would understand it to do. If the sentence requires "and also PR X does..." to make sense, the split is wrong: either merge with its sibling or stack it.

## 3. Pick the shape

Not a preference -- determined by the concern map and file overlap.

| Situation | Shape | Reason |
|---|---|---|
| Concern groups touch disjoint files | **Atomic** | Any merge order works; reviewers parallelize. |
| Groups share >=1 file, overlap is cosmetic (barrel exports, lockfile, unrelated formatting) | **Atomic** with last-merged rebase | Rebase the second-to-land PR at merge time; don't pre-emptively stack. |
| Groups share real logic (same function, same schema, same migration) | **Stacked** | Child depends on parent's code existing. |
| One group is a prerequisite refactor, the rest build on it | **Stacked** | Prerequisite ships first; children stack. |
| Stack depth would exceed 3 | **Refuse -- redesign the split** | Stacks rot. Land the base half first, then re-split the remainder. |

**Default: atomic whenever geometrically possible.** Stacks impose merge order on reviewers, invite restacking churn as parents move, and multiply the "empty PR after rebase" failure mode.

For execution details:
- **Atomic** -> `references/atomic.md`
- **Stacked** -> `references/stacked.md`

Both paths share:

- One branch per PR. Names follow `ticket-branch` conventions (`<owner>/<prefix>-<number>-<stub>`, <=32 chars).
- **Always move code via git operations** (cherry-pick, hunk stage, `git diff ... | git apply`) -- drift from manual re-typing is silent and costly. Fall back to manual edits only when no git primitive can produce the right result.
- `quality-ship` gate **per PR**, not once at the end.
- `pr-description` hand-off per PR -- re-load the skill and tick its section-0 checklist before every `gh pr create`.

## 4. Execute the split

### 4a. Pre-split commit surgery (often necessary, skip only if every commit is clean)

Grab-bag commits are the main blocker to a clean split. Fix them before branching:

```bash
git checkout -b split-staging HEAD           # scratch branch; discarded after
git rebase -i "$BASE"                         # mark grab-bag commits as `edit`

# at each `edit` stop:
git reset HEAD^                               # unstage everything
git add -p <files-for-PR-1>
git commit -m "<PR-1 subject>"
git add -p <files-for-PR-2>
git commit -m "<PR-2 subject>"
git rebase --continue
```

This produces a linear series of atomic commits that map 1:1 to the planned PRs. Cherry-picking against this is trivial.

**After surgery, update the plan's commit SHAs.** The rebase rewrote history -- the original SHAs are gone. Cherry-pick from the new `split-staging` SHAs in 4b; picking the old grab-bag SHAs silently undoes the surgery. Delete `split-staging` once all PR branches are created and pushed.

See **git-advanced** for interactive-rebase mechanics and split-commit patterns.

### 4b. Per-PR loop

For each PR in dependency order (atomic = any order; stacked = parent first):

1. **Branch** -- per `references/atomic.md` (off `$BASE`) or `references/stacked.md` (off parent).
2. **Apply commits** via cherry-pick / hunk stage / diff-apply. Resolve any conflicts; if unresolvable, surface to the user -- do not force.
3. **Quality-ship** -- load the skill, emit its checklist, run detected validators, commit, push.
4. **Open PR** -- re-load `pr-description`, emit its section-0 checklist, then `gh pr create --base <target> --body-file /tmp/pr-body.md`. Include the series context in the body (shape, part K of N, dependencies, what it proves standalone).

### 4c. Conflict strategy during cherry-pick

If a cherry-pick conflict arises:

1. **Read the conflict.** Is it because the parent's changes are already staged (stacked path, expected), or because you're taking a later concern before its dependency (wrong split -- back up to step 3)?
2. **Resolve only within the scope of the current PR's concern.** Do not pull hunks that belong to a later PR to make the conflict go away.
3. `git cherry-pick --continue` when clean.
4. If the only possible resolution requires code from a PR not yet landed, your shape is wrong -- revisit the plan.

## 5. Report

At the end, output:

```
Shape:         <atomic | stacked>
PRs created:   <count>
  #<num> -- <title>
    URL:        <pr-url>
    Base:       <branch>
    Depends on: <none | #num>
    Size:       +<added> / -<removed> across <files> files

Merge order:   <any | #1 -> #2 -> #3>
Follow-up:     <staging branches to delete, deferred work, etc.>
```

If the original branch had an open PR, close it with a comment pointing to the new series (URLs + shape + merge order). Do not delete the source branch until every new PR is merged -- it's the only remaining reference to the pre-split work if a split PR needs to be rebuilt.

## Failure modes

| Failure | Signal | Fix |
|---|---|---|
| **Commit-first thinking** | Plan groups by commit ranges, not by concerns | Throw away the plan; rebuild from `git diff --stat` and the concern map |
| **Skipped approval gate** | Started branching before user saw the plan | Stop, reset, present plan, wait |
| **Over-stacking** | Stack >3 deep | Land the bottom half, then re-split the remainder as a fresh pass |
| **Silent drift** | Manually re-typing changes "to clean them up" | Use git operations only -- cherry-pick, hunk stage, diff-apply |
| **Latent overlap** | "Atomic" PRs conflict on merge because a shared file was missed | Re-run overlap check (see `references/atomic.md`) after plan, before push |
| **PRs that don't stand alone** | Reviewer can't understand PR K without PR K-1 context | Expand each PR's Description to state the standalone intent, or merge the two |
| **One quality-ship run at the end** | Only the tip branch was validated | `quality-ship` per PR branch -- each must ship clean |
| **Skipped pr-description hand-off** | `gh pr create` called without re-loading the skill | Re-load and re-emit the section-0 checklist every PR. No exceptions. |
| **Stack rot** | Child PR diverges from parent after parent moves | See `references/stacked.md` "Restacking" |
| **`gh pr edit` used on stacked PRs** | Command fails with Projects-classic GraphQL error | Use `gh api repos/$REPO/pulls/<n> -X PATCH ...` per `pr-context` |
