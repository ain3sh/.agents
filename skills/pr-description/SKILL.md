---
name: pr-description
description: Shared atom for analyzing a diff and writing a structured PR description. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# PR Description

Make the merge case legible from the title and first screen; later sections prove it, scope it, and price its risk.

## Act

| Goal | Action |
|---|---|
| Analyze and draft | Load `references/workflow.md`; use three-dot diff analysis, outcome-first title selection, `What / Why / How`, and the first-screen skim gate. |
| Large diff (roughly 1k+ lines or 20+ files) | Run `scripts/diff-composition.py BASE HEAD --core <behavior files> --tooling <prefixes>`; put the composition table and core breakdown under **What** (template in `references/conditional-sections.md`). |
| Add conditional sections | Load `references/conditional-sections.md` only when a catalog trigger fires. |
| Show a structural change | Load `show-me` to select one grounded shape; load `references/artifacts.md` only when inline evidence cannot carry it. |
| Show a visual change | Open the PR first, then load `references/visual-evidence.md` and capture live proof. |
| Refresh an existing PR | Load `references/refresh.md`; explicit title/body audits bypass the no-diff throttle. |
| Publish or PATCH | Load `references/publish.md`; compose with a file tool and use GitHub REST. |

Load this skill immediately before drafting, creating, or PATCHing the PR. Do not preload references; load each when its trigger fires.

## Detect

Use three-dot diff and two-dot log:

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
git fetch -q origin "$DEFAULT_BRANCH"
git log  --oneline "origin/$DEFAULT_BRANCH"..HEAD
git diff --stat    "origin/$DEFAULT_BRANCH"...HEAD
```

## Rules

1. Never title the mechanism when the diff proves a higher-level outcome,
   behavior, or invariant; the reviewer should not reverse-engineer value from
   implementation nouns.
2. Never replace `What / Why / How` with a second description schema; strengthen
   **What** with concrete impact and decisive evidence.
3. Never let section order bury a merge-defining fact; preview it in
   Description and keep methodology in its owning later section.
4. Never turn the body into a diff summary or changelog; file tours belong in
   Reviewer Guide/Implementation map, and patch history belongs only in the
   lean refresh revision log.
5. Never treat factual freshness as persuasive coherence; every explicit
   title/body audit reruns the first-screen skim gate.
6. Never fabricate magnitude, proof, mitigation, or rollout state. Preview
   only evidence the diff or live verification actually supports.
7. Never compose the body through shell heredocs or publish with `gh pr edit`;
   use a file tool and `gh api -F body=@file`, stamp the `pr-desc-base`
   marker last, then verify the live body byte-for-byte.
8. Never describe a large diff's size in prose or with estimated percentages;
   a reviewer prices the PR from the first screen, so the computed composition
   table with a per-row action goes there, before **Why**.
9. Never attach durations to review passes or to the review; name the commits,
   files, and the one thing to check per pass.

## Failure map

| Symptom | Action |
|---|---|
| Title is valid but says only how | Apply the abstraction ladder in `workflow.md`; choose the highest proven delta. |
| Impact is vague despite strong evidence | Preview the decisive fact in **What**; keep full proof in its conditional section. |
| Reviewer must scroll to know why to merge | Run the skim gate in `workflow.md` and rewrite the first screen. |
| Diff is large and the body explains the size in prose, or the composition sits in Reviewer Guide | Run `scripts/diff-composition.py`; move the table and core breakdown under **What** (`conditional-sections.md`, Diff composition). |
| Body cites SHAs after a rebase or force-push | Sweep with the stale-SHA step in `refresh.md`; rerun the composition script. |
| Refresh says no-op but the user asked for prose/title improvement | Use the explicit-audit bypass in `refresh.md`. |
| Repeated refreshes read like commit history | Replace the revision log with only changes since the last human review. |
| Diagram or recording adds no reviewer signal | Follow `artifacts.md` or `visual-evidence.md`; remove net-zero evidence. |
| GitHub body differs after PATCH | Follow the byte-compare verification in `publish.md`. |

## References

Load on demand; do not reabsorb into this file:

- `references/workflow.md` — diff analysis, title selection, first-screen gate,
  required sections, writing, and searchable markers.
- `references/conditional-sections.md` — optional section triggers, templates,
  repro recipes, scope maps, lineage, and implementation appendices.
- `references/artifacts.md` — architecture diagrams and artifact upload/caption
  discipline.
- `references/visual-evidence.md` — live visual proof decision tree and capture
  handoff.
- `references/refresh.md` — marker-based staleness, decision-hierarchy audit,
  revision log, and explicit-audit bypass.
- `references/publish.md` — GitHub REST operations, marker stamp, and
  round-trip verification.
- `scripts/diff-composition.py` — buckets a three-dot diff by review weight
  (generated / mechanical / tests / core / tooling / docs) from `git numstat`.
