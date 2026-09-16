Load skills: **pr-context**, **voice**.

**voice** is required here: use its severity taxonomy and craft rules for every posted body instead of rephrasing approved findings into generic review-speak.

The posting half of the review workflow. Findings come from an upstream `/review-pr` (typical) or fresh paste. Publish only in §5: §2-§4 reconcile, draft, and check the whole payload first.

## 1. Resolve PR Identity

Resolve the PR and `REPO` from the supplied ref or current review context via **pr-context**. Ask for the PR ref via `AskUser` if neither is available. Fetch the live PR head as `HEAD_SHA`, even when context already holds a SHA.

## 2. Reconcile the Findings

**Default scope.** `/post-review <PR>` publishes the full final review at its approved tiers and gating stances, plus the verdict. Invoking it after the final presentation is explicit confirmation; do not ask again. Trailing text supplies instructions or pasted findings; only an explicit subset narrows the default.

**Read the ledger whole, first.** Before drafting anything, read `./.agents/review.md` and every chunk of `./.agents/review.notes.md` start to end (layout in the **review-pr** skill's `references/dossier.md`) -- not the tail, not a search, not a summary. Verify both belong to the target repo and PR; a mismatched or missing ledger is a gap, not permission to use chat memory. Skip only for pasted findings with no upstream review session: use that list for the same per-finding coverage check without inventing a ledger.

**Build the coverage table** for every `F<id>` appearing in either file, including notes-only findings. It is a temporary view over existing state, never a new file, dossier field, or status:

| Column | Source |
|---|---|
| `F<id>`, current tier, status | reconcile the dossier with the full event history for that id |
| user decision | latest explicit approval, drop, rewording, retier, scope, or verdict choice |
| prior thread | comment id when an earlier pass already posted it |
| outgoing body | inline comment, grouped comment, or verdict passage carrying it; otherwise the exclusion reason |

Reconciliation rules:

- **Live** = `confirmed` and approved at the gate. `killed`, `folded→Fn`, user-dropped, and superseded findings stay out; a well-argued notes entry is not a reason to resurrect one.
- **Explicit user decisions win.** Apply the latest instruction, including this invocation, over earlier decisions; record new decisions using the existing `gate` / `retier` notes events. Chat memory is not a competing source.
- **Approved means presented.** The gate approved the findings shown to the user, never `candidate` entries that stayed in the notes. A `confirmed` finding the presentation omitted is a conflict (below), not a bonus post.
- **Already posted** (`posted` status / thread id) is never sent again. If it still gates, the verdict names it and links the thread.
- **Grouping keeps every claim.** One comment may carry several findings; each independent claim and ask survives the merge.
- **Tier and gating stance are separate, and both are fixed here.** No recasting a blocker as optional or fast-follow to soften or shorten; no turning a non-gating finding into a blocker.
- **Stale substance is not reposted as fresh.** A current head (§1) that differs from the dossier's `reviewed_head`, or materially new evidence, sends the finding back through `/review-pr` follow-up for revalidation and re-approval. This step never rewrites substance.
- **Gaps block publication.** Missing evidence, missing approval, or a genuine unresolved conflict requires one `AskUser` naming the gap. Resume only after resolution or explicit user scope reduction; never silently post a subset or ask again about settled approval.

Each live finding needs a **voice** severity (do not invent or remap tiers), body prose, and a destination. Inline comments need a file path and line(s), optionally a replacement snippet; a broader finding without a useful inline anchor goes in the verdict. Pasted findings need the same information; missing or ambiguous material follows the gap rule above.

**Full means final.** Post each finding whole: claim, mechanism and impact, the evidence that backs it, the required action, and any remaining uncertainty. Not the raw candidates, not the investigation diary behind them.

## 3. Draft Every Body

### Plain comment vs. suggestion block

Posting-time decision; `/review-pr` is silent on this so review judgment isn't biased toward apply-clickable issues.

Attach a `suggestion` block only when **all** hold:

- Fix is small (~1-5 lines), mechanical, unambiguous -- no naming/ordering/design judgment.
- Local: no ripple edits to imports, types, or other regions.
- Targeted lines lie inside the PR's diff hunks (GitHub only renders Apply on changed/adjacent regions).
- Indentation matches the file (tabs vs spaces).

Otherwise post the prose as a plain comment. Don't downgrade severity because a suggestion isn't attachable.

### Verdict body

The verdict body is the standalone judgment from the **review-pr** skill's first-pass §6 (disposition + root cause, blockers, headline opinion, evidence woven into the claims it backs) -- **not** a recap of the threads you post; GitHub renders those inline. If the upstream handoff omitted one, draft it against that structure -- don't fall back to "Posted N comments on X, Y, Z."

It names **every** still-gating finding, numbered, each with its concrete ask, including linked threads for already-posted blockers. There is no count limit. The GitHub event (§5) does not make these asks optional.

### Deslop pass -- mandatory, even on a user-approved body

Approval at the `/review-pr` gate covered the findings and disposition, not the prose; re-read every body against **voice** and cut wholesale:

- **Event-token prefix**: a verdict opening with "COMMENT." / "APPROVE." duplicates the badge GitHub renders from `event`; start with the *why* sentence instead.
- **Internal deliberation**: the approval-gate chat never leaks. Draft history, severity re-calibrations, "my earlier draft over-weighted X", what the user reworded or dropped -- the PR author sees none of that conversation and must not learn it existed. Post the final position as if it were the only one you ever held.
- **Persuasion on standard asks**: blockers that are ordinary due diligence (test coverage, ticket reference, meeting a CI gate) are flat imperative requirements with their concrete mechanism -- never hedged, argued for, or defended against imagined pushback ("worth satisfying rather than labeling away", "the gate is genuinely red"). The real-vs-flake triage call stays as a stated fact backing the disposition, not woven into the ask as a plea. Asking for standard protocol needs no apology; spend justification only on genuinely discretionary calls.
- **Command narration**: the CLI invocations, tool names, and worker dispatches behind a probe (`gh run view`, vitest flags, `slop-scan delta`, typechecker choice). Report the observed fact -- *"the new tests fail on base for the stated reason"* -- never the transcript that produced it. How you learned something is your business; what's true is the review.
- **Methodology paragraphs**: "Checks run:", "Also verified:", CI pass counts, sweep inventories. If a probe backs a claim, it's already inline in that claim; standalone it's an essay about your process.
- **Fast-follow / "worth a ticket" material**: pre-existing issues belong in a ticket or a PR conversation comment, not the verdict.

This applies to line-comment bodies too: findings state the defect and the fix, never the commands run to find it.

Deslop removes ceremony, not substance. It never changes a tier, a gating stance, or a claim; a body that reads shorter because a mechanism, caveat, or ask vanished fails §4.

Lead with the ruling and gate in the first two sentences; use the remaining space needed for the complete review.

## 4. Coverage Check Before the First Write

After the deslop pass and before any external write, walk the §2 coverage table against the final payload:

- Every live row maps to an outgoing comment or verdict passage preserving its claim, mechanism/impact, evidence, ask, uncertainty, tier, and gating stance.
- Every excluded row cites its recorded disposition or explicit user decision: unresolved candidate, killed, folded, dropped, superseded, already posted, or scoped out. Never "trimmed for length".
- Every published finding has a row; the verdict names every still-gating finding, including previously posted ones.
- Separately compare the verdict with the approved review state and first-pass §6: preserve the architecture ruling, acceptance states and waivers, and coverage limits. These are not invented findings merely to fit the table.
- Grouped comments still carry each claim they merged.

Restore what deslop dropped and run the check again. A gap the ledger cannot close is a §2 `AskUser`, not a silent omission.

## 5. Post

### Line comments

Build JSON with `jq` and pipe to `--input -`; multi-line bodies with backticks/newlines aren't safe through `-f body=...`.

#### Single-line

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

#### Multi-line range

Add `--argjson start_line <N>` and emit `start_line:$start_line, start_side:"RIGHT"` alongside `line:$line, side:"RIGHT"` in the JSON. `start_line < line`, range inclusive, both endpoints inside the PR's hunks.

#### Format rules

- **Severity prefix always** -- begin `BODY` with `**[critical|warning|opinion|suggestion|nit]**`.
- **Indent matches the file** -- tabs vs spaces; mismatch commits as-is and breaks formatting.
- **Backtick collision** -- if the replacement contains triple backticks, escalate the suggestion fence to four (` ````suggestion `).
- **Empty fence deletes the targeted lines** -- use only when deletion is the recommendation.
- **Group related findings** into one comment where it helps (each claim and ask retained, per §2); max one suggestion block per comment.

### Submit the verdict

```bash
gh api "repos/$REPO/pulls/<number>/reviews" \
  --method POST \
  -f event="<COMMENT|APPROVE|REQUEST_CHANGES>" \
  -f body="<verdict-body>"
```

The event is the verdict approved at the `/review-pr` gate -- don't recompute it here. Default to `COMMENT` when blockers gate or `APPROVE` otherwise; the number of blockers never changes the event. Use `REQUEST_CHANGES` only when the user explicitly requested that verdict type; never infer it from blocking findings. `APPROVE` with non-gating line comments (`opinion`/`nit`/`suggestion`) is legitimate per the skill's first-pass §6.

## 6. Close the Ledger

After submitting, close the ledger for this pass: append the `post` entry (review id, comment ids → anchors) to `./.agents/review.notes.md` and refresh `./.agents/review.md` per the **review-pr** skill's `references/dossier.md` (replace state sections, mark posted findings with their thread ids, append a history line). Skip only for pasted findings with no upstream review session (no ledger exists).
