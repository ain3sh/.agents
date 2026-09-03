# Publishing through GitHub REST

Compose body files with Create/apply_patch, then publish through REST. Never use
`gh pr edit`: organizations with Projects (classic) can trigger its deprecated
GraphQL query and reject the operation.

`-F body=@/path` makes `gh api` read the finished file itself. The body never
touches the command line, so terminal-security scanners (lookalike TLDs, pipes,
URLs in the Markdown) cannot false-positive on it, and multiline Markdown,
backticks, and shell-significant characters survive untouched. Never
`-f body="$(cat …)"`: that puts the whole body on the command line.

## Resolve the PR

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
PR_NUM=$(gh pr view --json number --jq '.number')
```

## Operations

| Goal | Command |
|---|---|
| Stamp the marker (final line, every publish) | `printf '\n<!-- pr-desc-base: %s -->\n' "$(git rev-parse HEAD)" >> /tmp/pr-body.md` |
| Update body | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -F body=@/tmp/pr-body.md` |
| Update title | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f title='<type(scope): description>'` |
| Title and body in one call | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f title='…' -F body=@/tmp/pr-body.md` |
| Verify round-trip | `gh api "repos/$REPO/pulls/$PR_NUM" --jq .body \| sed 's/\r$//' > /tmp/pr-live.md && diff <(sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' /tmp/pr-live.md) <(sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' /tmp/pr-body.md)` |
| Request reviewer | `gh api "repos/$REPO/pulls/$PR_NUM/requested_reviewers" -X POST -f "reviewers[]=<login>"` |
| Add label | `gh api "repos/$REPO/issues/$PR_NUM/labels" -X POST -f "labels[]=<label>"` |
| Mark ready | `gh api graphql -f query='mutation{markPullRequestReadyForReview(input:{pullRequestId:"<node-id>"}){pullRequest{isDraft}}}'` |

GitHub returns the body with CRLF line endings and strips the final newline;
the round-trip command normalizes both. Any other difference means the publish
lost content: fix the write, never the comparison.

`gh pr create` and `gh pr view` are unaffected.

## Rules

1. Never compose Markdown with a shell heredoc. Terminal-security guards scan
   command lines, external URLs can false-positive, and interruption loses the
   draft. Use a file tool; `gh api -F body=@file` reads the finished file.
2. Never weaken or placeholder-substitute body content to satisfy a command
   scanner. Change the write mechanism.
3. Never commit screenshots, recordings, or diagrams. Upload through
   `gh-attach` per `artifacts.md`.
4. Never publish without the `pr-desc-base` marker as the final line; the
   refresh workflow (`refresh.md`) cannot resolve its base without it. Stamp it
   after the last generated block (for example the `stack:links` block).
5. After publishing, run the round-trip verification above.
