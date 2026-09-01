# Publishing through GitHub REST

Compose body files with Create/apply_patch, then publish through REST. Never use
`gh pr edit`: organizations with Projects (classic) can trigger its deprecated
GraphQL query and reject the operation.

The REST body command reads the completed file with `$(cat ...)`, preserving
multiline Markdown, backticks, and shell-significant characters.

## Resolve the PR

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
PR_NUM=$(gh pr view --json number --jq '.number')
```

## Operations

| Goal | Command |
|---|---|
| Update body | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-body.md)"` |
| Update title | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f title="<type(scope): description>"` |
| Request reviewer | `gh api "repos/$REPO/pulls/$PR_NUM/requested_reviewers" -X POST -f "reviewers[]=<login>"` |
| Add label | `gh api "repos/$REPO/issues/$PR_NUM/labels" -X POST -f "labels[]=<label>"` |
| Mark ready | `gh api graphql -f query='mutation{markPullRequestReadyForReview(input:{pullRequestId:"<node-id>"}){pullRequest{isDraft}}}'` |

`gh pr create` and `gh pr view` are unaffected.

## Rules

1. Never compose Markdown with a shell heredoc. Terminal-security guards scan
   command lines, external URLs can false-positive, and interruption loses the
   draft. Use a file tool; the shell only reads the finished file.
2. Never weaken or placeholder-substitute body content to satisfy a command
   scanner. Change the write mechanism.
3. Never commit screenshots, recordings, or diagrams. Upload through
   `gh-attach` per `artifacts.md`.
4. After publishing, fetch the live body and compare it byte-for-byte with the
   composed file.
