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
| Finalize (every publish, before `gh pr create` or PATCH) | `python3 ~/.agents/skills/pr-description/scripts/finalize-body.py /tmp/pr-body.md`: exits 1 without writing when `## Architecture` holds no view; otherwise replaces any old marker with the full HEAD sha as the final line |
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
4. Never publish a body `finalize-body.py` has not just passed. It is the only
   marker stamp, and refresh (`refresh.md`) cannot resolve its base without
   the marker. Rerun it after any edit, including a regenerated `stack:links`
   block.
5. After publishing, run the round-trip verification above.
