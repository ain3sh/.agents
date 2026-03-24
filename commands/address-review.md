---
description: Address reviewer feedback on your PR -- read comments, fix code, respond to threads
argument-hint: <PR-number-or-URL>
---

Load skills: **pr-context**, **quality-ship**.

## 1. Gather Feedback

Follow the **pr-context** skill to fetch full PR context from `$ARGUMENTS`.

Additionally, fetch all review comments and review threads:
```bash
gh api "repos/$REPO/pulls/<number>/comments" | jq '.[] | {id, path, line, body, user: .user.login, in_reply_to_id}'
gh api "repos/$REPO/pulls/<number>/reviews" | jq '.[] | {id, state, body, user: .user.login}'
```

Group comments into threads. For each thread, identify:
- **What the reviewer is asking for**: code change, clarification, or acknowledgment.
- **File + line**: Where the feedback targets.
- **Whether it's blocking**: `REQUEST_CHANGES` reviews vs `COMMENT` suggestions.

## 2. Triage

Present a summary of all feedback threads with a proposed action for each:
- **Fix**: code change needed -- describe what you'll change.
- **Respond**: clarification or pushback -- draft the reply.
- **Ack**: minor nit or style preference -- will fix or explain why not.

**Wait for user confirmation** before making changes.

## 3. Apply Fixes

For each thread marked "Fix":
- Make the code change.
- Keep changes minimal and scoped to what the reviewer asked for.
- Do not refactor unrelated code in the same pass.

## 4. Quality + Push

Follow the **quality-ship** skill for quality checks, commit, and push only (skip PR creation -- branch already has one):
- Run detected quality checks. Fix issues until clean.
- Commit: `fix(<scope>): address review feedback (<TICKET-ID>)`
- Push to the existing PR branch.

## 5. Respond to Threads

For each addressed thread, reply confirming the fix:
```bash
gh api "repos/$REPO/pulls/<number>/comments" \
  --method POST \
  -f body="Fixed in <commit-sha-short>." \
  -F in_reply_to=<comment-id>
```

For threads where the response is a clarification or disagreement, post the drafted reply from step 2.

## 6. Re-request Review

```bash
gh pr edit <number> --add-reviewer <reviewer-login>
```
