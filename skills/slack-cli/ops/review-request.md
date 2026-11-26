# PR review requests in Slack

One top-level post per PR, in the owning pod's channel, only when the PR is
finished. Everything after that lives in the post's thread. **voice** owns the
prose; this file owns readiness, channel, reviewer scope, shape, and delivery.

## Readiness gate (all true, or do not post)

Run from the PR's checkout; `gh` fills `{owner}` and `{repo}` from it.

```bash
gh pr view N --json isDraft,headRefOid,mergeStateStatus,reviewDecision,latestReviews
gh pr checks N | awk -F'\t' '{c[$2]++} END{for(k in c) printf "%s=%d ", k, c[k]}'   # fail=0 pending=0
gh api graphql -F owner='{owner}' -F name='{repo}' -F pr=N -f query='query($owner:String!,$name:String!,$pr:Int!){repository(owner:$owner,name:$name){pullRequest(number:$pr){reviewThreads(first:100){nodes{isResolved}}}}}' \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[]|select(.isResolved==false)]|length'   # 0
```

- Ready for review, not draft; CI fully green on the current head; no
  unaddressed review feedback: every thread, bot reviews included, is fixed or
  deflected with a reply and resolved; title and body current for this head
  (`pr-desc-base` marker equals the head); no further commits planned before
  merge.
- Skip the post when the PR already holds the approval it needs. Approvals
  survive new pushes; never ask an approver again. An approved PR with green
  checks gets no post of any kind: merge it, or leave it to the merge
  automation where one owns the merge. Never post asking someone else to merge.
- Also request the reviewers on GitHub so the PR shows them:
  `gh api 'repos/{owner}/{repo}/pulls/N/requested_reviewers' -X POST -f 'reviewers[]=<login>'`.

## Channel and reviewer scope

Post in the pod channel that owns the touched area; never open with a DM.
Scope reviewers from the diff paths (`gh pr diff N --name-only`), one tag per
reason, and say the reason in the post.

Which channel and which people own a path is the workspace's knowledge, so it
is not written here. If you are working for ainesh, use the software-factory
repo for the mappings. Otherwise read the owners from the repository: its
`CODEOWNERS` entries for the diff paths, then whoever approved the latest
merged PRs that changed the same files. Find the channel with
`slack ch list | rg <pod>` and each person with `slack u list | rg -i <name>`
(search display names too); tag by user ID, never by name.

## Shape (a numbered list, nothing else)

Reviewers scan the channel to find what needs them; a long post hides that.
The root is a numbered list, one PR per line, PR title then the bare URL, in
priority order (blocking someone else first, then oldest first), and a last
line with the tags and the ask:

```
Review request(s), green and ready:
1. perf(cli): avoid redundant requests at startup - https://github.com/<owner>/<repo>/pull/101
2. perf(cli): share startup setup across entry points - https://github.com/<owner>/<repo>/pull/102
<@U0123456789> <@U0987654321> (agent core in 2) could one of you take these?
```

A single ready PR is the same list with one item. Every PR that passes the
gate in the same pass goes in the same list, never one post each. State
(approvals so far, threads, head), what it does, and scope cuts are thread
replies, one per PR, not the root. No headings, no bullets, no prose
paragraph in the root.

## Delivery

```bash
slack msg send <channel-id> "$(cat /tmp/review-N.txt)"      # draft in a file first
slack msg history <channel-id> --limit 1                      # verify; keep the ts
slack msg send <channel-id> "<update>" --thread <TS>          # every follow-up
slack msg react <channel-id> <TS> merged                      # once the PR merges
```

Answers to questions, steps that move the review (a nudge, a new reviewer's
request), and the merge notice are thread replies on that ts. A new head posts
nothing: a reply per sync is noise that teaches reviewers to skip the thread.
When the PR merges, also react `:merged:` on the post itself, so anyone
scanning the channel sees the request is closed without opening the thread. A second top-level post for the same PR is noise; if the
first post is wrong, `msg update` it.
