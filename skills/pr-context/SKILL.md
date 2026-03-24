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
