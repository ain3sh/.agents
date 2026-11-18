Load skills: **pr-context**, **quality-ship**, **voice**.

Treat **voice** as mandatory for reviewer-facing replies: load it before drafting responses, declines, or alternative-rationale text so the reply states a position with specifics instead of sounding generically agreeable.

## On a new thread

Read the conversation and the cited code on the **pushed PR head**. Post the answer on the thread within minutes, human reviewers first. This is the triage action, before editing code, assigning a builder or waiting for CI. A code hold leaves replies open; an explicit no-contact order stops them.

Tell the reviewer what you verified. For a change you own, explain what will change and why; use the repository's promise marker for unpushed work. If the cause or decision is still open, name the concrete observation and the question that remains. Don't promise an unapproved change or publish an unconfirmed decline. Use **Posting replies** below, including its pending-review check.

Resolve an answered thread when its answer stands on the pushed head and nothing is owed; don't post it again. An unshipped fix stays open. After an authorized push, explain the change on the thread, add `Fixed in <sha>.` on its own line, then resolve.

## 1. Gather Feedback

Follow the **pr-context** skill to fetch full PR context from the text supplied after the slash command.

Fetch all three PR-comment surfaces plus **GraphQL thread IDs** (needed for resolving review threads later):

```bash
# Line-level review threads (inline diff comments).
gh api --paginate "repos/$REPO/pulls/<number>/comments" | jq '.[] | {id, path, line, body, user: .user.login, in_reply_to_id}'

# Review summary bodies (REQUEST_CHANGES / APPROVE / COMMENT with body).
gh api --paginate "repos/$REPO/pulls/<number>/reviews" | jq '.[] | {id, state, body, user: .user.login}'

# Conversation comments, bots included: a bot's finding can be actionable. Skip status
# reports (deploy previews, CI and scan summaries); they need no reply.
gh api --paginate "repos/$REPO/issues/<number>/comments" | jq '.[] | {id, body, user: .user.login}'

# Fetch thread node IDs upfront -- REST API cannot resolve threads.
gh api graphql --paginate -f query='
  query($endCursor: String) {
    repository(owner: "<owner>", name: "<repo>") {
      pullRequest(number: <number>) {
        reviewThreads(first: 100, after: $endCursor) {
          pageInfo { hasNextPage endCursor }
          nodes { id isResolved comments(first: 1) { nodes { databaseId body } } }
        }
      }
    }
  }'
```

Group comments into threads. For each thread, capture:
- **What the reviewer is asking for**: code change, clarification, or acknowledgment.
- **File + line**: where the feedback targets (`--` for conversation comments).
- **Whether it's blocking**: `REQUEST_CHANGES` reviews vs `COMMENT` suggestions.
- **GraphQL thread ID**: map each root review comment's `databaseId` to its thread `id` for resolution. Conversation comments have no thread and are closed by the reply itself.

## 2. Classify

Tag each thread with exactly one class:

- **bug-report** -- reviewer reports broken behavior, missing data, regression, race, off-by-one, schema mismatch, or anything where the root cause is non-obvious from the comment alone.
- **nit** -- naming, formatting, stylistic micro-preference. No behavior change.
- **clarification** -- reviewer asks "why X?" or "should this also do Y?" -- a response is needed, not necessarily a code change.
- **style** -- code organization, file placement, idiom. Behavior-equivalent.
- **ack** -- typo, docstring polish, trivial agreement.

Already-resolved threads keep their class but get the action `Resolved` in step 4.

## 3. Root-Cause Analysis (bug-report items only)

Do not skip to a fix. For every thread classified as **bug-report**, load the **root-cause-analysis** skill and walk its workflow against the reviewer's report. If the bug involves multi-actor sequencing, async callbacks, background refreshes, recovery paths, retries, queues, or two pieces of state evolving together, additionally load the **step-through** skill and walk the broken flow before proposing anything.

Output for each bug-report item, verbatim shape:

```
Symptom:        <what the reviewer saw>
Trigger:        <action / sequence that reproduces it>
Root cause:     <first unintended side effect, named with file + function/line>
Correct layer:  <where to fix>
Minimal patch:  <concrete code change, not a description>
```

If you cannot name a real file + symbol for the root cause after walking the flow, the item's action becomes `Investigate` in step 4, not `Fix`. Do not guess. Do not infer a fix from the symptom alone.

## 3.5 Cross-Thread Coherence (before triage)

If steps 1-3 produced **>=2 threads whose resolution requires editing code** (any bug-report, plus any nit / style / clarification thread that resolves into an edit), or one such thread at a symbol this PR has already fixed twice (a **recurrence**, defined in **patch-coherence**), load the **patch-coherence** skill, run its audit, and emit the fix-locus map before step 4. Skip otherwise.

## 4. Triage

**Discovery gate for edits.** Read every file an approach block will touch, trace its symbols and check each `Change` and `Verify` against the code. A choice you cannot settle before applying a fix belongs here as `Investigate`.

Produce two artifacts in this order.

### 4a. Triage Table

One row per thread. No prose, no rationale -- just the label. The `Locus` column references the step-3.5 map; non-Fix actions blank it; drop the column entirely if 3.5 was skipped.

| # | Thread | File:line | Class | Action | Locus |
|---|--------|-----------|-------|--------|-------|
| 1 | <short ref> | <path:line> | bug-report | Fix | L1 |
| 2 | <short ref> | <path:line> | clarification | Respond | -- |
| 3 | <short ref> | <path:line> | nit | Ack | -- |

Permitted actions: `Fix`, `Respond`, `Ack`, `Investigate`, `Resolved`, `Decline`.

**Provenance is not a decline reason.** "Pre-existing", "inherited", or "worth a follow-up" never justifies `Decline` or a deferral note when the issue is real and lies within a locus this PR already touches: the action is `Fix`. A real issue is never declined as out of scope or deferred: it is `Fix`, or, when fixing it needs a product or design call, an open thread whose exact decision you name for the user at the confirmation gate.

**A reviewer's proposal clears the same evidence bar as your own change.** `Decline` a suggestion that is wrong, makes things worse, or reverses a settled decision (one the user, team, or repo already made), and cite the evidence: the decision, compatibility boundary, or failure it would cause. What counts as evidence for reopening a settled decision is owned by [voice external replies](../../voice/references/external-replies.md#reviewer-replies) (**Settled decisions**); when the reviewer brings it, keep the thread open and name the decision for the user at the confirmation gate.

### 4b. Approach (Fix loci and Decline rows)

**One approach block per locus** (or per `Fix` thread when 3.5 was skipped). Each block's `Threads:` field lists every thread it resolves; the locus ID isn't repeated -- the triage table already maps thread → locus.

```
Threads:     <#N, #M, ...>
File(s):     <real paths>
Symbols:     <function/component/class/test names>
Change:      <one paragraph or a short code snippet>
Why here:    <one sentence on why this layer subsumes every thread above>
Verify:      <test/check that proves the fix across every thread>
```

For `Decline` rows, write a one-paragraph rationale citing the constraint or design decision that overrides the request. Declines are per-thread, not aggregated. A real bug is never a `Decline` row: move it to `Fix`, or keep the thread open and name the exact decision for the user in the plan.

**Hedging is forbidden in approach blocks.** Words like "likely", "probably", "should fix", "might be", "I think", "we may need to" indicate the RCA is incomplete. If you reach for them, demote the **locus** to `Investigate`; every thread it would have addressed becomes an `Investigate` row stating what's unknown and what you'd need to read or run to know it. The user cannot approve a fix you yourself are unsure of.

**A valid bug report does not validate the fix the reporter suggested.** The reviewer found a symptom; you did the RCA; you choose the patch. When **any thread under a locus** includes a specific fix proposal -- a `suggestion` block, an inline patch, "you should X", "what about Y", "wrap this in...", or any concrete code shape -- extend the locus's Approach block with three extra fields *before* `Verify`:

```
Reviewer proposed:    <one line per thread that proposed a fix, prefixed with the thread #>
Alternatives:         <at least one other credible fix: different layer, different fallback shape, different invariant ownership; one sentence each>
Chosen because:       <one sentence justifying the picked locus-level change against those alternatives, citing the invariant or layering, not the reviewer's authority>
```

If after consideration the reviewer's suggestion *is* the right fix, say so explicitly with the alternatives still listed and explicitly rejected. The point is audited reasoning, not contrarianism. Bot reviewers especially tend to pair a real finding with a locally-correct but architecturally-wrong patch (wrong layer, hides the bug elsewhere, breaks an invariant the bot can't see) -- treat their suggested fix as one hypothesis among several, never as ratified by the finding.

Present this in normal chat prose; **do not use `AskUser`** for the triage report. Addressing review feedback often needs nuanced back-and-forth, rewording, pushback, and partial acceptance that does not fit a constrained multiple-choice flow.

**Wait for confirmation before changing code or posting a decline**, unless the invocation already authorizes that action.

## Posting replies

End every reply with `<!-- agent-reply -->` so the agent's thread replies and drafts are distinguishable on a shared account. Triage all top-level feedback before replying: GitHub does not pair conversation replies with individual items.

**Pending review first.** GitHub keeps at most one pending review per account per PR, and GraphQL review mutations (`addPullRequestReviewThreadReply` among them) file the account's comments into it, where only the account can read them: reviewers see no answer. Before the first reply, look for the account's pending review (only its author can see one, so any review printed here belongs to the account). The query pages through every comment and prints the review once per page of 100:

```bash
gh api graphql --paginate -F o="${REPO%/*}" -F r="${REPO#*/}" -F n=<n> -f query='
query($o:String!,$r:String!,$n:Int!,$endCursor:String){ repository(owner:$o,name:$r){ pullRequest(number:$n){
  reviews(states:PENDING, first:1){ nodes{ id url body
    comments(first:100, after:$endCursor){ pageInfo{ hasNextPage endCursor } nodes{ id path url body } } } } } } }' \
  --jq '.data.repository.pullRequest.reviews.nodes[0] // empty | {id, url, body, comments: .comments.nodes}'
```

If it prints a review, read its body and every comment on every page: nobody else has seen them. The account is shared with the user, so a pending draft is yours only when it carries `<!-- agent-reply -->`. Act on the first case that fits:

- **Empty**: the body is empty and there are 0 comments. Delete the review (`deletePullRequestReview(input:{pullRequestReviewId:"<review-id>"})`).
- **All yours**: the body, if non-empty, and every comment carry the mark. Delete each comment a reply you are about to send supersedes (`deletePullRequestReviewComment(input:{id:"<comment-id>"})`). If that leaves the review empty, delete it; otherwise submit it as a comment and read back `COMMENTED` before replying.
- **Any unmarked content**: it may be the user's unsent feedback. Do not submit, edit, or delete any of it. Report it as an open decision with the review URL and each unmarked comment's URL, and send no reply on this PR until the user settles it.

```bash
gh api graphql -F id=<review-id> -f query='
mutation($id:ID!){ submitPullRequestReview(input:{pullRequestReviewId:$id, event:COMMENT}){ pullRequestReview{ state url } } }'
```

The REST reply below fails with HTTP 422 `user_id can only have one pending review per pull request` while one exists. That error means run this check; never route around it through GraphQL `addPullRequestReviewThreadReply`, which files the reply into the pending review without a word.

Pick endpoint by surface.

**Inline thread** (from `pulls/<n>/comments`, anchor `#discussion_r...`) -- reply on the thread. `<comment-id>` must be the thread's top-level comment (the one with no `in_reply_to_id`): GitHub does not support replies to replies.
```bash
gh api "repos/$REPO/pulls/<n>/comments/<comment-id>/replies" --method POST \
  -f body="$(cat <<'EOF'
<answer to this thread>

<!-- agent-reply -->
EOF
)"
```

**Review body** (from `pulls/<n>/reviews`, anchor `#pullrequestreview-...`) -- no thread to attach to. Quote-reply via PR issue comment, one per distinct point, quoting only the span you address:
```bash
gh api "repos/$REPO/issues/<n>/comments" --method POST \
  -f body="$(cat <<'EOF'
> <quoted snippet>

<answer to this point>

<!-- agent-reply -->
EOF
)"
```

**Conversation comment** (from `issues/<n>/comments`, anchor `#issuecomment-...`) -- no thread to reply on. Use the review-body quote-reply pattern above.

## Resolve what stands

Thread resolution is **GraphQL-only** and applies only to review threads -- REST has no endpoint, and conversation comments have no thread node.

Leave unverified reports, decisions and requested reviewer follow-up open. Use the repository’s head-pinned resolver when present; otherwise use the thread ID fetched in step 1, after checking the PR head and latest response:
```bash
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "<thread-node-id>"}) {
      thread { isResolved }
    }
  }'
```

## 5. Apply Confirmed Fixes

Once the invocation or user confirms the proposed fixes, proceed **fully** — every confirmed `Fix` row lands in this pass; do not quietly re-punt during application. If applying a fix forces a choice its approach block didn't confirm, stop: that is a step-4 discovery failure — return to triage with the new question rather than deciding it silently.

Apply the change for **each locus** (or each `Fix` thread when 3.5 was skipped):

- Make the code change exactly as specified in the locus's approach block.
- Keep changes minimal and scoped to the locus -- multi-thread loci are still one change at one layer, not several stitched together.
- Do not refactor unrelated code in the same pass.

## 6. Quality + Push

Follow the **quality-ship** skill for quality checks, commit, and push:
- **Worktree pre-check first** -- if cwd is a git worktree, load **worktree-setup** and run its repair before any validator. Never `npm install` / `pip install` inside a worktree.
- Run detected quality checks. Fix issues until clean.
- Commit: `fix(<scope>): address review feedback (<TICKET-ID>)`
- Push to the existing PR branch. Revisit the threads this push changes.

## 7. Re-request Review

**Never re-request anyone who has approved this PR.** An `APPROVED` review at any point disqualifies that login for good, even if they later commented, requested changes, or had the approval dismissed. No exceptions and no user-confirmation path: the user re-requests approvers manually when a special case calls for it.

Candidates are only the reviewers whose threads this pass addressed. Subtract every approver, then re-request whoever remains. If nobody remains, skip this step.

```bash
APPROVERS=$(gh api --paginate "repos/$REPO/pulls/<number>/reviews" \
  --jq '.[] | select(.state == "APPROVED") | .user.login' | sort -u)
# Drop every login in $APPROVERS from the candidate list before the POST below.
```

Use REST -- `gh pr edit --add-reviewer` currently fails on the Projects-classic GraphQL deprecation (see `pr-context` skill):

```bash
gh api "repos/$REPO/pulls/<number>/requested_reviewers" \
  --method POST \
  -f "reviewers[]=<non-approver-login>"
```
