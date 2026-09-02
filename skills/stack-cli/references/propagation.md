# Stack Propagation Judgment

Stack freshness is demand-driven. Preview after parent movement; propagate only
when fresh descendants buy evidence or unblock work now.

## Decide

```bash
stack status
stack sync <any-branch-in-the-stack> # dry run
```

Judge four facts:

| Fact | Propagate now | Defer descendants |
|---|---|---|
| Descendant demand | A child is being edited, tested, reviewed, or merged. | Children are dormant or draft. |
| Parent stability | The parent reached a review or merge candidate. | Another parent rewrite is likely before child work resumes. |
| Evidence value | Child CI/diffs must represent the current parent. | Only the active branch's CI or mergeability matters. |
| Replay cost | The repair is small or needed once. | A long/conflict-heavy stack would be replayed repeatedly. |

Also propagate when the user explicitly requests the whole stack or after a
parent merge/rewrite when child work resumes.

## Propagate

Summarize every branch and PR the preview will mutate. If that exceeds the
user's explicit request, ask before applying:

```bash
stack sync --apply <any-branch-in-the-stack>
```

Use the stack owner for the whole lifecycle: root and descendant replay,
retargeting, backups, exact pushes, failure restoration, and undo.

## Defer

Return to **sync-target** and sync only the active branch. Leave descendants
untouched.

Report:

- every intentionally stale descendant
- that descendant CI, diffs, and mergeability are not current
- the trigger for propagation: before descendant work/testing/review resumes,
  when the active branch stabilizes, or during the next stack merge

Never request descendant review or cite descendant CI while propagation is
deferred.

## Example: volatile stack root

The bottom PR is changing rapidly, only its CI needs unblocking, four
descendants are dormant, and prior replay required substantial conflict work.
Preview the stack, defer descendant propagation, sync only the root, and
restack once the root reaches a stable candidate.
