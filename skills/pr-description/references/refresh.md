# Post-push refresh

Keep an existing PR's description accurate after new commits. Three phases: resolve the base the description was last reconciled against (0), find what drifted (1), make it coherent (2). Triggered by any push onto a branch with an open PR, and run on completion by `/open-pr`, `/split-pr`, `/address-review`, `quality-ship`.

## The synced-base marker (keystone)

Every body this skill writes ends with one invisible line — the commit the description was last reconciled against:

```markdown
<!-- pr-desc-base: <full-HEAD-sha> -->
```

An HTML comment: invisible when rendered, present in the raw body. It turns "what changed since I last touched this?" from a timestamp guess into `git log <base>..HEAD`. Every refresh resolves it, then **re-stamps it to current HEAD as its final act** (idempotent). Each stacked PR carries its own. It powers everything below: incremental focus (Phase 1), the revision log (Phase 2), verification staleness (Phase 1), the no-op throttle.

## Phase 0 — resolve the base

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
PR_NUM=$(gh pr view --json number --jq '.number')
gh pr view "$PR_NUM" --json title,body > /tmp/pr-current.json
jq -r '.body' /tmp/pr-current.json > /tmp/pr-current-body.md
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
git fetch -q origin "$DEFAULT_BRANCH"

# 1. Marker — deterministic, written by every prior refresh.
BASE=$(rg -o 'pr-desc-base: \K[0-9a-f]{7,40}' /tmp/pr-current-body.md | tail -1)

# 2. Fallback for marker-less PRs (predate this skill, or hand-authored): map the
#    body's last-edit time to the commit the branch was at then. Best-effort —
#    committer dates drift under rebase, which is why the marker supersedes it.
#    userContentEdits is empty when never edited, so := falls back to createdAt.
if [ -z "$BASE" ]; then
  NODE_ID=$(gh pr view "$PR_NUM" --json id --jq .id)
  EDITED_AT=$(gh api graphql -f query='query($id:ID!){node(id:$id){... on PullRequest{userContentEdits(last:1){nodes{editedAt}}}}}' -f id="$NODE_ID" --jq '.data.node.userContentEdits.nodes[0].editedAt // empty')
  : "${EDITED_AT:=$(gh pr view "$PR_NUM" --json createdAt --jq .createdAt)}"
  BASE=$(git rev-list -1 --before="$EDITED_AT" HEAD)
fi

# 3. Guard — rebase/force-push can orphan the stored SHA. If BASE is missing or no
#    longer an ancestor of HEAD, degrade to merge-base so incremental == full
#    (correctness over efficiency).
if [ -z "$BASE" ] || ! git merge-base --is-ancestor "$BASE" HEAD 2>/dev/null; then
  BASE=$(git merge-base "origin/$DEFAULT_BRANCH" HEAD)
fi
```

The fallback self-heals: once this refresh writes its marker, every later one takes the deterministic path.

**Throttle**: if `git diff --quiet "$BASE"..HEAD` (nothing new since last reconcile), skip Phases 1-2 and go straight to the no-op re-stamp (Phase 2 step 4).

## Phase 1 — staleness check

Two diffs, two jobs:

```bash
git log  --oneline "$BASE"..HEAD                    # (a) INCREMENTAL — changes since last reconcile;
git diff --stat    "$BASE"..HEAD                    #     BASE is an ancestor, so two-dot is exact.
git diff --stat    "origin/$DEFAULT_BRANCH"...HEAD  # (b) FULL — what the branch introduces (three-dot).
```

(a) is where new drift hides — read it first. But it only *focuses* the audit: a claim that went wrong three weeks ago won't appear in it. (b) is ground truth for "does the body still cover everything?" Prioritize with (a), stay complete with (b).

Check the description against both:

- **Title drift** — no longer matches the full diff, breaks `type(scope):`, or exceeds 72 chars. On squash repos it's the permanent commit subject — weight heavily on long PRs.
- **Missing scope** — new files/modules (look in the incremental diff first) unmentioned.
- **Changed intent** — "fix X" but the diff now also refactors Y. If the *approach itself* was replaced (the mechanism the Description narrates is gone), that's a pivot → Phase 2 rewrite, not a patch.
- **Stale claims** — search absolute wording first (`only`, `exact`, `complete`, `always`, `unchanged`, `lossless`); these decay fastest after follow-up commits.
- **Verification staleness** — intersect the incremental diff with paths cited in **Behavior verified** / `Sentinel test:`. A verified path touched since its `verified @ <sha>` anchor is unproven: re-verify or downgrade.
- **Evidence drift** — recordings/fixtures/pasted output still described as proving current behavior after their source changed. Revalidate or narrow to what they still prove.
- **Generated-appendix drift** — regenerate machine blocks (`<!-- *_START --> … *_END -->`, the `stack` CLI's `<!-- stack:links:start … :end -->` chain block, semantic-diff `<details>`, embedded snippets, diagrams, file lists); don't update only the human summary. The stack block is refreshed by `stack sync`, never by hand (conditional-sections.md, Lineage).
- **Verification gaps** — new code paths with no repro, no regression test, or a stale **Not tested** note.

**Size advisory (non-gating)**: if the full `--stat` shows the PR has outgrown reviewability — mixed concerns, sprawling file count, a diff a reviewer can't hold in their head — surface `split-pr` (decompose) or `retrospective` (scrub).

Nothing stale → re-stamp the marker (step 4) and stop. Don't rewrite for phrasing.

## Phase 2 — coherence pass

The body proper reads as one authored piece, not a log of patches — with **one sanctioned exception**, the revision log.

1. **Patch or rewrite?** Localized staleness (a few claims, a missing scope line) → patch in place. Approach pivot, or the incremental diff invalidated most specific claims → **rewrite ground-up from the full diff**; patching a pivoted narrative makes Frankenstein prose. ("Don't rewrite for marginal phrasing" guards *style* — a pivot is the opposite case.)
2. Before writing, verify:
   - Single narrative; Description still 2-4 sentences even on scope growth (added flows go in **Verification > Behavior verified**, not paragraph-per-commit).
   - **Revision log** (the carve-out): under active review a seamless body hides what moved since a reviewer last looked. Keep a `<details><summary>Changes since last review</summary>` trail fed from the incremental diff — the one place a patch-log belongs. Lean: entries since the last human review; drop older ones. Omit pre-review / on first push.
   - Risk & Impact reflects current full scope, not just the delta.
   - **Conditional sections re-evaluated both ways** — add newly-triggered (>3 consumers → Reverse Dependencies; new metric → Telemetry) **and remove** newly-untriggered (risky migration extracted to its own PR → drop Migration & Rollout / RCA). An orphaned section describing absent work is staleness too.
   - Every evidence claim revalidated or narrowed; every generated appendix regenerated (or replaced with a tighter Reviewer Guide if it adds bulk without aiding review).
3. Apply via REST (SKILL.md §5 — `gh pr edit` is broken), re-stamping the marker as the final line. Draft the body marker-free, then:
   ```bash
   printf '\n<!-- pr-desc-base: %s -->\n' "$(git rev-parse HEAD)" >> /tmp/pr-updated-body.md
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-updated-body.md)"
   # title drift, same pass:
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f title="<type(scope): description>"
   ```
4. **No-op re-stamp** (Phase 1 found nothing / throttle hit): replace the marker, leave prose untouched.
   ```bash
   sed '/<!-- pr-desc-base: /d' /tmp/pr-current-body.md > /tmp/pr-body-nomark.md
   printf '<!-- pr-desc-base: %s -->\n' "$(git rev-parse HEAD)" >> /tmp/pr-body-nomark.md
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-body-nomark.md)"
   ```

**Squash-merge note**: the marker is inert if it lands in a squash commit message; strip it in the final pre-merge refresh if your repo mirrors body→commit and you want a clean message.

**Bar**: would a reviewer reading the current description get a wrong or incomplete picture? Fix that; don't chase marginal phrasing.
