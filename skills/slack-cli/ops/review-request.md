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

## Shape (mrkdwn, under ~150 words)

1. `Review request: <PR URL|#N title> (ticket or program)`.
2. `*What it does*`: 3-5 `•` bullets in reader terms, including any deliberate
   scope cut so nobody reviews for it.
3. `*State*`: commits and base, CI, threads, body; areas touched and whether
   backend is in it.
4. Last line: the tags, each with its reason, and the explicit ask
   ("could one of you take the approval?").

Reference post (CLI + agent core): `#pod-cli` ts `1791365435.282049`.

## Delivery

```bash
slack msg send C08867C315E "$(cat /tmp/review-N.txt)"      # draft in a file first
slack msg history C08867C315E --limit 1                      # verify; keep the ts
slack msg send C08867C315E "<update>" --thread <TS>          # every follow-up
```

New head after review feedback, answers to questions, and the merge notice are
thread replies on that ts. A second top-level post for the same PR is noise;
if the first post is wrong, `msg update` it.
