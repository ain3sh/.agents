# PR review requests in Slack

One top-level post per PR, in the owning pod's channel, only when the PR is
finished. Everything after that lives in the post's thread. **voice** owns the
prose; this file owns readiness, channel, reviewer scope, shape, and delivery.

## Readiness gate (all true, or do not post)

```bash
gh pr view N --json isDraft,headRefOid,mergeStateStatus,reviewDecision,latestReviews
gh pr checks N | awk -F'\t' '{c[$2]++} END{for(k in c) printf "%s=%d ", k, c[k]}'   # fail=0 pending=0
gh api graphql -f query='query{repository(owner:"Factory-AI",name:"factory-mono"){pullRequest(number:N){reviewThreads(first:100){nodes{isResolved}}}}}' \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[]|select(.isResolved==false)]|length'   # 0
```

- Ready for review, not draft; CI fully green on the current head; no
  unaddressed review feedback: every thread, bot reviews included, is fixed or
  deflected with a reply and resolved; title and body current for this head
  (`pr-desc-base` marker equals the head); no further commits planned before
  merge.
- Skip the post when the PR already holds the approval it needs. Approvals
  survive new pushes; never ask an approver again.
- Also request the reviewers on GitHub so the PR shows them:
  `gh api repos/Factory-AI/factory-mono/pulls/N/requested_reviewers -X POST -f 'reviewers[]=<login>'`.

## Channel and reviewer scope

Post in the pod channel that owns the touched area; never open with a DM.
Scope reviewers from the diff paths (`gh pr diff N --name-only`), one tag per
reason, and say the reason in the post.

| Diff touches | Channel | Tag |
|---|---|---|
| `apps/cli/`, `packages/logging/`, `packages/droid-sdk-core/` only | `#pod-cli` `C08867C315E` | David Gu `<@U09F1267NEQ>`, Arman `<@U07JFQ3LD6Z>` |
| + agent core (`apps/cli/src/core/`, `AgentLoop`, exec runner) | same | + Luke `<@U07UL8E7JES>` |
| + backend (`apps/backend/`, `packages/server/`, `apps/prem/`) | same | + Austin (resolve: `slack u list \| rg -i austin`; search display names too) |

Resolve anything not in the table with `slack ch list | rg <pod>` and
`slack u list | rg -i <name>`; tag by user ID, never by name.

## Shape (mrkdwn, one short paragraph, under ~45 words)

Reviewers scan the channel to find what needs them; a long post hides that.
The team said so on 2026-10-07 (`#pod-cli` ts `1791410360.287579`): one line
per PR, title visible, and when several are ready, one message sorted by
priority. So:

```
Review request: <PR URL|#N title>. <state in one clause: green, N open threads, who approved>; needs <tag> (<reason>)[, <tag> (<reason>)]. Details in thread.
```

Everything else (what it does, scope cuts, base and head, areas touched)
is the first reply in the post's own thread, not the post. No headings, no
bullets, no second paragraph in the root.

When three or more PRs pass the gate in the same pass, post one digest
instead of one post each: an opening clause (`Three CLI PRs are green and
need review:`), then one line per PR in priority order (blocking someone
else first, then oldest first), each `• <PR URL|#N title> — <one clause>
(<tag>)`. Per-PR detail goes in the digest's thread, one reply per PR.

Reference posts: single `#pod-cli` ts `1791415296.907529`; digest `#pod-cli`
ts `1791404474.924979`.

## Delivery

```bash
slack msg send C08867C315E "$(cat /tmp/review-N.txt)"      # draft in a file first
slack msg history C08867C315E --limit 1                      # verify; keep the ts
slack msg send C08867C315E "<update>" --thread <TS>          # every follow-up
slack msg react C08867C315E <TS> merged                      # once the PR merges
```

New head after review feedback, answers to questions, and the merge notice are
thread replies on that ts. When the PR merges, also react `:merged:` on the
post itself, so anyone scanning the channel sees the request is closed without
opening the thread. A second top-level post for the same PR is noise; if the
first post is wrong, `msg update` it.
