---
description: Post a reviewed PR's findings to GitHub -- threaded line comments + verdict.
argument-hint: [<PR-number-or-URL>]
---

Load skills: **pr-context**.

The posting half of the review workflow. Findings come from an upstream `/review-pr` (typical) or fresh paste.

## 1. Resolve PR Identity

Use `REPO` and `HEAD_SHA` from context if present (typical post-`/review-pr`); otherwise follow **pr-context** with `$ARGUMENTS`. Ask for the PR ref via `AskUser` if neither is available.

## 2. Source the Findings

In priority: the approved list from the current chat (`/review-pr` just completed) or pasted inline.

Each finding: severity (`critical|warning|suggestion|nit`), file path, line(s), body prose, optionally a replacement snippet. Use `AskUser` once if anything's missing or ambiguous.

## 3. Per-Finding: Plain Comment vs. Suggestion Block

Posting-time decision; `/review-pr` is silent on this so review judgment isn't biased toward apply-clickable issues.

Attach a `suggestion` block only when **all** hold:

- Fix is small (~1-5 lines), mechanical, unambiguous -- no naming/ordering/design judgment.
- Local: no ripple edits to imports, types, or other regions.
- Targeted lines lie inside the PR's diff hunks (GitHub only renders Apply on changed/adjacent regions).
- Indentation matches the file (tabs vs spaces).

Otherwise post the prose as a plain comment. Don't downgrade severity because a suggestion isn't attachable.

## 4. Posting Mechanics

Build JSON with `jq` and pipe to `--input -`; multi-line bodies with backticks/newlines aren't safe through `-f body=...`.

### Single-line

The suggestion fence (when present) replaces the targeted line verbatim, including leading whitespace.

````bash
BODY=$(cat <<'EOF'
**[warning]** Swallows the parse error. Surface it instead:

```suggestion
  throw new ParseError(result.error);
```
EOF
)
jq -n \
  --arg body "$BODY" \
  --arg commit_id "$HEAD_SHA" \
  --arg path "src/parser.ts" \
  --argjson line 42 \
  '{body:$body, commit_id:$commit_id, path:$path, line:$line, side:"RIGHT"}' \
| gh api "repos/$REPO/pulls/<number>/comments" --method POST --input -
````

For a plain comment, omit the suggestion fence from `BODY`.

### Multi-line range

Add `--argjson start_line <N>` and emit `start_line:$start_line, start_side:"RIGHT"` alongside `line:$line, side:"RIGHT"` in the JSON. `start_line < line`, range inclusive, both endpoints inside the PR's hunks.

### Format rules

- **Severity prefix always** -- begin `BODY` with `**[critical|warning|suggestion|nit]**`.
- **Indent matches the file** -- tabs vs spaces; mismatch commits as-is and breaks formatting.
- **Backtick collision** -- if the replacement contains triple backticks, escalate the suggestion fence to four (` ````suggestion `).
- **Empty fence deletes the targeted lines** -- use only when deletion is the recommendation.
- **Group related findings** into one comment where it helps; max one suggestion block per comment.

## 5. Submit the Verdict

```bash
gh api "repos/$REPO/pulls/<number>/reviews" \
  --method POST \
  -f event="<COMMENT|APPROVE>" \
  -f body="<summary>"
```

`COMMENT` if any line comments were posted; `APPROVE` only if `/review-pr` ended with zero findings.
