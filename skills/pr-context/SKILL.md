---
name: pr-context
description: Shared atom for gathering full PR context -- metadata, diff, conversation, linked Linear ticket. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# PR Context Gather

## Parse Input

Accept PR reference as: `#123`, `123`, or a full GitHub URL. Extract the number.

## Fetch PR Metadata

```bash
gh pr view <number> --json title,body,headRefName,baseRefName,additions,deletions,changedFiles,commits,labels,reviewRequests,headRefOid
```

## Fetch Conversation

```bash
gh pr view <number> --comments
```

## Fetch Diff

```bash
gh pr diff <number>
```

## Resolve Linked Linear Ticket

Scan the PR body for Linear ticket references (patterns like `TEAM-123`, or Linear URLs). If found:

```bash
linear i get <ID> --output json --comments
```

Extract from the ticket: problem statement, acceptance criteria, constraints, and discussion context.

## Derive Repo Identity

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
HEAD_SHA=$(gh pr view <number> --json headRefOid --jq '.headRefOid')
```

These values are needed by commands that post review comments or interact with the GitHub API.

## GitHub API Selection

Choose the right `gh` interface for each operation. **`gh pr edit` is currently broken** on orgs that still have Projects (classic) enabled -- it fails with a GraphQL deprecation error on every invocation, regardless of flags. Route every mutation through REST instead.

| Operation | Use | Why |
|-----------|-----|-----|
| View/list PRs, issues | `gh pr view`, `gh issue list` | CLI works for reads |
| Create PR | `gh pr create` | CLI handles all create options |
| Update PR title | `gh api repos/$REPO/pulls/<N> -X PATCH -f title="..."` | `gh pr edit --title` hits Projects-classic deprecation |
| Update PR body | `gh api repos/$REPO/pulls/<N> -X PATCH -f body="..."` | `gh pr edit --body` hits same deprecation |
| Add reviewer | `gh api repos/$REPO/pulls/<N>/requested_reviewers --method POST -f "reviewers[]=<login>"` | `gh pr edit --add-reviewer` hits same deprecation |
| Add label | `gh api repos/$REPO/issues/<N>/labels --method POST -f "labels[]=<label>"` | `gh pr edit --add-label` hits same deprecation |
| Post line-level review comments | `gh api repos/$REPO/pulls/<N>/comments --method POST -f ...` | CLI cannot target specific diff lines or sides |
| Code suggestion comments | REST API with ` ```suggestion` blocks in body | CLI has no code suggestion support |
| Resolve review threads | `gh api graphql` with `resolveReviewThread` mutation | No REST endpoint exists for thread resolution |
| Merge PR | `gh pr merge` | CLI handles merge strategies |

**Rule of thumb**: `gh pr`/`gh issue` CLI for reads and `gh pr create`/`gh pr merge` only. Every PR mutation (body, title, labels, reviewers) goes through `gh api` REST. `gh api graphql` is reserved for thread resolution and complex queries that need nested data.

**Do not retry `gh pr edit`** when it fails -- the error is deterministic, not transient. Switch to REST immediately.
