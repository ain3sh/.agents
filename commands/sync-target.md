---
description: Merge this branch's target (PR base or repo default) into HEAD; resolve conflicts in branch context
argument-hint: [--no-push] [<target-branch>]
---

Load skills: **pr-context**, **quality-ship**, **git-advanced**, **worktree-setup**.

## 1. Resolve target

Target is wherever this branch lands: PR base, parent of a stacked PR, or repo default. Never hardcode `dev`/`main`.

Precedence: explicit arg → open PR's `baseRefName` → repo default (`origin/HEAD`).

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
REMOTE=$(git remote | head -1)
git fetch "$REMOTE" --prune

TARGET=$(printf '%s\n' $ARGUMENTS | grep -v '^--' | head -1)
[ -z "$TARGET" ] && TARGET=$(gh pr view --json baseRefName --jq .baseRefName 2>/dev/null)
[ -z "$TARGET" ] && TARGET=$(git symbolic-ref refs/remotes/"$REMOTE"/HEAD 2>/dev/null | sed "s|refs/remotes/$REMOTE/||")
```

If `$TARGET` is empty or equals `$CURRENT`, ask. Surface `"$REMOTE/$TARGET" → "$CURRENT"` and confirm — stacked PRs miscall easily.

## 2. Branch context

```bash
gh pr view --json title,body,headRefName,baseRefName 2>/dev/null
git log --oneline "$REMOTE/$TARGET".."$CURRENT"
git diff --stat "$REMOTE/$TARGET".."$CURRENT"
```

Note which files this branch owns, what it changes, what it should preserve from upstream.

## 3. Merge

```bash
git merge "$REMOTE/$TARGET" --no-edit
```

Clean? Skip to §5. Else: `git diff --name-only --diff-filter=U`.

## 4. Resolve conflicts

For each conflicted file, read both sides and classify. Tag each resolution **High** (mechanical, clear intent) or **Low** (judgment call on business logic) — §6 gates on these tags.

| Type | Action |
|------|--------|
| **Non-overlapping** | Integrate both |
| **Superseding** | Keep ours; adopt new deps/imports/types from theirs |
| **Upstream improvement** | Take theirs |
| **Genuine collision** | Judge from branch context |

Stage resolutions, then `git commit --no-edit`.

## 5. Quality checks

Run **quality-ship**: detected checks → fix → re-run until clean. Separate commits for fixes.

## 6. Push gate

**Hold** if any:
- `$ARGUMENTS` contains `--no-push`
- User said hold off this session
- Any **Low**-confidence resolution

When holding: summarize each resolution + confidence; for Low ones, name the ambiguity and the choice; ask before pushing.

Otherwise:

```bash
git push -u origin HEAD
```
