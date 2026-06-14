---
description: Address reviewer feedback on your PR -- read comments, fix code, respond to threads
argument-hint: <PR-number-or-URL>
---

Load skills: **pr-context**, **quality-ship**.

## 1. Gather Feedback

Follow the **pr-context** skill to fetch full PR context from `$ARGUMENTS`.

Fetch all three PR-comment surfaces plus **GraphQL thread IDs** (needed for resolving review threads later):

```bash
# Line-level review threads (inline diff comments).
gh api "repos/$REPO/pulls/<number>/comments" | jq '.[] | {id, path, line, body, user: .user.login, in_reply_to_id}'

# Review summary bodies (REQUEST_CHANGES / APPROVE / COMMENT with body).
gh api "repos/$REPO/pulls/<number>/reviews" | jq '.[] | {id, state, body, user: .user.login}'

# Conversation comments -- drop bots; bot review threads above stay (their findings can be actionable).
gh api "repos/$REPO/issues/<number>/comments" \
  | jq '.[] | select(.user.type != "Bot" and (.user.login | endswith("[bot]") | not))
        | {id, body, user: .user.login}'

# Fetch thread node IDs upfront -- REST API cannot resolve threads.
gh api graphql -f query='
  query {
    repository(owner: "<owner>", name: "<repo>") {
      pullRequest(number: <number>) {
        reviewThreads(first: 100) {
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
- **GraphQL thread ID**: map each root review comment's `databaseId` to its thread `id` for step 8. Conversation comments have no thread and are closed by the reply itself.

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

If steps 1-3 produced **>=2 threads whose resolution requires editing code** (any bug-report, plus any nit / style / clarification thread that resolves into an edit), load the **patch-coherence** skill, run its audit, and emit the fix-locus map before step 4. Skip otherwise.

## 4. Triage

Produce two artifacts in this order.

### 4a. Triage Table

One row per thread. No prose, no rationale -- just the label. The `Locus` column references the step-3.5 map; non-Fix actions blank it; drop the column entirely if 3.5 was skipped.

| # | Thread | File:line | Class | Action | Locus |
|---|--------|-----------|-------|--------|-------|
| 1 | <short ref> | <path:line> | bug-report | Fix | L1 |
| 2 | <short ref> | <path:line> | clarification | Respond | -- |
| 3 | <short ref> | <path:line> | nit | Ack | -- |

Permitted actions: `Fix`, `Respond`, `Ack`, `Investigate`, `Resolved`, `Decline`.

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

For `Decline` rows, write a one-paragraph rationale citing the constraint or design decision that overrides the request. Declines are per-thread, not aggregated.

For `Fix` rows, draft the reply text inline under the table row alongside the locus's approach block: 1-3 sentences restating `Change` + `Why here` in the reviewer's frame, plus a pointer to where to look in the diff. The approach block is for the user; the reply is for the reviewer, whose context is only thread + diff -- not your locus blocks or this chat. Multi-thread loci produce one draft per thread, each in its reviewer's frame. **Bare `Fixed in <sha>.` is forbidden** -- it forces the reviewer to re-derive substance you produced upstream.

For `Respond`, `Ack`, `Resolved`, `Investigate` rows, draft the reply text inline under the table row (no block needed).

Write every reply draft with the **voice** skill: specifics and named actors, no slop, and treat declines and chosen-alternative rationale as `opinion`-grade pushback (state the position and the *why*).

**Hedging is forbidden in approach blocks.** Words like "likely", "probably", "should fix", "might be", "I think", "we may need to" indicate the RCA is incomplete. If you reach for them, demote the **locus** to `Investigate`; every thread it would have addressed becomes an `Investigate` row stating what's unknown and what you'd need to read or run to know it. The user cannot approve a fix you yourself are unsure of.

**A valid bug report does not validate the fix the reporter suggested.** The reviewer found a symptom; you did the RCA; you choose the patch. When **any thread under a locus** includes a specific fix proposal -- a `suggestion` block, an inline patch, "you should X", "what about Y", "wrap this in...", or any concrete code shape -- extend the locus's Approach block with three extra fields *before* `Verify`:

```
Reviewer proposed:    <one line per thread that proposed a fix, prefixed with the thread #>
Alternatives:         <at least one other credible fix: different layer, different fallback shape, different invariant ownership; one sentence each>
Chosen because:       <one sentence justifying the picked locus-level change against those alternatives, citing the invariant or layering, not the reviewer's authority>
```

If after consideration the reviewer's suggestion *is* the right fix, say so explicitly with the alternatives still listed and explicitly rejected. The point is audited reasoning, not contrarianism. Bot reviewers especially tend to pair a real finding with a locally-correct but architecturally-wrong patch (wrong layer, hides the bug elsewhere, breaks an invariant the bot can't see) -- treat their suggested fix as one hypothesis among several, never as ratified by the finding.

Present this in normal chat prose; **do not use `AskUser`** for the triage report. Addressing review feedback often needs nuanced back-and-forth, rewording, pushback, and partial acceptance that does not fit a constrained multiple-choice flow.

**Wait for user confirmation** before making changes.

## 5. Apply Fixes

Apply the change for **each locus** (or each `Fix` thread when 3.5 was skipped):

- Make the code change exactly as specified in the locus's approach block.
- Keep changes minimal and scoped to the locus -- multi-thread loci are still one change at one layer, not several stitched together.
- Do not refactor unrelated code in the same pass.

## 6. Quality + Push

Follow the **quality-ship** skill for quality checks, commit, and push:
- **Worktree pre-check first** -- if cwd is a git worktree, load **worktree-setup** and run its repair before any validator. Never `npm install` / `pip install` inside a worktree.
- Run detected quality checks. Fix issues until clean.
- Commit: `fix(<scope>): address review feedback (<TICKET-ID>)`
- Push to the existing PR branch.

## 7. Respond to Threads

Send the row's step-4 reply draft verbatim; append `Fixed in <sha>.` only when a commit landed against it. Do not improvise reply text at API time -- if a row has no draft, return to step 4.

Pick endpoint by surface.

**Inline thread** (from `pulls/<n>/comments`, anchor `#discussion_r...`) -- reply on the thread:
```bash
gh api "repos/$REPO/pulls/<n>/comments" --method POST \
  -f body="$(cat <<'EOF'
<reply draft #N>

Fixed in <sha>.
EOF
)" -F in_reply_to=<comment-id>
```

**Review body** (from `pulls/<n>/reviews`, anchor `#pullrequestreview-...`) -- no thread to attach to. Quote-reply via PR issue comment, one per distinct point, quoting only the span you address:
```bash
gh api "repos/$REPO/issues/<n>/comments" --method POST \
  -f body="$(cat <<'EOF'
> <quoted snippet>

<reply draft #N>

Fixed in <sha>.
EOF
)"
```

**Conversation comment** (from `issues/<n>/comments`, anchor `#issuecomment-...`) -- no thread, no `in_reply_to`. Use the review-body quote-reply pattern above.

## 8. Resolve Threads

Thread resolution is **GraphQL-only** and applies only to review threads -- REST has no endpoint, and conversation comments have no thread node.

For each addressed review thread, resolve it using the thread ID fetched in step 1:
```bash
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "<thread-node-id>"}) {
      thread { isResolved }
    }
  }'
```

## 9. Re-request Review

Use REST -- `gh pr edit --add-reviewer` currently fails on the Projects-classic GraphQL deprecation (see `pr-context` skill):

```bash
gh api "repos/$REPO/pulls/<number>/requested_reviewers" \
  --method POST \
  -f "reviewers[]=<reviewer-login>"
```
