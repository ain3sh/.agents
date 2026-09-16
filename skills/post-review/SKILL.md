---
name: post-review
description: Publish approved PR findings as inline comments and a review verdict.
disable-model-invocation: true
---

# Post Review

## Act

Usage: `/post-review [<PR-number-or-URL>]`.

Default (`/post-review <PR>` alone): post the full approved review, every live
finding at its approved tier and gating stance plus a verdict naming every
blocker, reconciled against the whole ledger (`./.agents/review.md` and all of
`./.agents/review.notes.md`) before the first write. Use trailing text as
instructions or pasted findings; only explicit subset selection narrows the default.

Read `references/workflow.md` in full, then follow its steps in order.
