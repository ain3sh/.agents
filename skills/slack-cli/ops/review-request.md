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

## Shape (a numbered list, nothing else)

Reviewers scan the channel to find what needs them; a long post hides that.
The team said so on 2026-10-07 (`#pod-cli` ts `1791410360.287579`): one line
per PR, title visible, sorted by priority. The root is a numbered list, one
PR per line, PR title then the bare URL, in priority order (blocking someone
else first, then oldest first), and a last line with the tags and the ask:

```
Review request(s), green and ready:
1. perf(cli): own the connector catalog per scope and avoid redundant cold catalog requests - https://github.com/Factory-AI/factory-mono/pull/23051
2. perf(cli): open one startup bootstrap before the run module loads and share it between daemon and exec - https://github.com/Factory-AI/factory-mono/pull/23054
<@U09F1267NEQ> <@U07UL8E7JES> (agent core in 2) could one of you take these?
```

A single ready PR is the same list with one item. Every PR that passes the
gate in the same pass goes in the same list, never one post each. State
(approvals so far, threads, head), what it does, and scope cuts are thread
replies, one per PR, not the root. No headings, no bullets, no prose
paragraph in the root.

Reference post: `#pod-cli` ts `1791404474.924979`.

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
