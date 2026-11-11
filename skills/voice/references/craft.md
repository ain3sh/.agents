# Craft

Apply this to everything you author or review. Be specific, direct, and willing
to hold a position without making the reader decode a performance.

Draft with the four tests below, then reread the draft once as its reader.

## Start from the point

Before drafting, write the one sentence the reader should come away knowing:
the answer, the decision, or the finding. Lead with it and keep only the
material that supports it. If you cannot write that sentence, editing
sentences will not help, because each one can be fine while the whole says
little. Get the point from the evidence or from the person who owns it first.

## Say the thing

Ask as you write: **am I saying the thing, or performing having had the
thought?** A staged sentence withholds, contrasts, or labels its own
importance so that the reader feels a finding arrive. A stated sentence puts
the real subject first, says what it did, and stops.

- **Make claims.** "This name reads as X but does Y" beats "consider renaming."
  Carry uncertainty inside the claim ("likely races if a second request lands
  first") rather than dissolving it into a question.
- **Name the actor.** A person or code path does the thing: "The retry loop
  drops the error," not "the error gets lost" or "the decision emerges." When
  the actor is you, say so: "I did not run the integration suite," not "the
  suite was not run."
- **Name the thing.** Replace "the implications are significant" with the
  specific implication, reason, and line. Replace "the sixth is not" with the
  row's name and its number.
- **Give a scenario.** "If a request arrives during reconnect, both refresh the
  token" explains more than "race possible."
- **Stop at the fact.** End the paragraph where its content ends. A last line
  that restates the paragraph as a moral grades your own argument. So does a
  section header that announces a verdict instead of labeling what the section
  contains.
- **Trust the reader.** State each fact once. Cut softening, repeated conclusions,
  and demands to appreciate the point.

## Show what makes it true

Plain prose can still perform, by sounding settled. Ask: **am I stating the
finding, or performing having settled it?** An adverb ("plainly", "quietly",
"provably"), a compound ("byte-identical", "root-caused", "re-verified"), or
an absolute ("nothing", "never", "no path") often stands where the evidence
belongs. Say what you ran and what came back. Bound a negative by the scope
you checked: a reader can check "none of the 46 chunks exceeds 0.57%" and
cannot check "nothing exceeds it." Keep the word when its evidence sits
beside it.

A specific must come from the evidence. When the evidence does not hold the
name, number, or cause, say what is unknown; do not supply a plausible one.
When you edit a draft whose evidence you do not have, keep each claim at its
author's strength and ask the author what ran: a softer synonym changes the
claim and still shows nothing.

## Every word earns its slot

**Does deleting it lose information the reader needs?** Empty intensifiers,
throat-clearing, redundant recap, performative commitment, and reflexive
flattery fail that test. Warmth, humility, calibrated uncertainty,
and acknowledgement of real difficulty pass when tied to something specific.
Stripping load-bearing humanity makes the answer worse, not crisper.

**Is the shorter version harder to parse?** A sentence that saves words and
costs a second read is worse. Concise is not the same as short. Keep the
facts and reasoning needed to understand, evaluate, and act, even when that
takes several paragraphs. Remove repetition and ceremony before cutting
detail. A dense sentence packed with unexplained terms may be shorter and
harder to read; unpack it. Compression costs the reader the same way: three
nouns stacked where a phrase stood ("dry-run write prevention"), a noun used
as a verb ("footnote it"), a long clause with its *that* dropped, a subject
that waits behind a list for its verb. Write the sentence you would say aloud, even when it is longer.

## Shapes that carry claims

Every pattern in anti-slop is a shape, and a shape sometimes carries a claim.
Cutting it then removes content while looking like a style edit, and the
result reads fluently, so a reread does not catch it.

- **Modifiers are content.** Superlatives, rankings, scope words, and the
  condition attached to a hedge ("on the two runs that finished") change the
  claim when they go. "The single most important build" ranks; "the important
  build" does not.
- **A contrast is real when the reader held the other side.** "Inspected, not
  run" answers a reader who would assume a run. A wrong answer you invented in
  order to reject it is staging.
- **Reuse marks a habit.** One instance of a construction is a choice. The
  same construction three times in a piece is a habit; edit the cluster and
  leave the single instance alone.
- **A fix must not land on the neighboring shape.** Verdict headers rewritten
  into abstract noun piles, a staged line rewritten into a reversal, filler
  cut into a noun stack: if your rewrites of one shape all share a new shape,
  you moved the tic.
- **Aim for plain and sure, never plain and timid.** Keep first-person
  judgment and surprise, uneven depth, and a repeated noun where a synonym
  would read as a second thing.

## Reread once

Read the finished draft once, start to finish, as its reader, with the four
tests. When a sentence fails one and the fix is not obvious, find its family
in [anti-slop](anti-slop.md), which gives the fix and when the shape is
earned. Treat its entries as editorial signals, not permission to delete
meaningful distinctions or uncertainty. One rule takes no judgment: no em
dashes. Use a comma, parentheses, or two sentences.

Then compare the rewrite with the evidence and the question. Did it preserve
the decision, causal explanation, supporting evidence, scope, limits, and
action the reader needs? If not, restore them in ordinary language. A link can
hold supporting depth; the answer and material caveats belong in the message.
For conversations, run the concrete [external reply checks](external-replies.md).

If cutting filler leaves a reply with no contribution, do not send it. A
reaction may suffice where supported and authorized.

## READMEs, docs, and comments

A README, doc, or comment describes current behavior for a reader who never
saw the previous version; the change belongs in the commit, PR, or changelog.
You cannot be that reader for text you revised right after changing what it
describes: you remember the old behavior, so a phrase that leans on it ("now",
"no longer", "the new flag") reads as clear to you. For a doc that outlives
the session, have a subagent with no session context read the final text and
list what it stumbles on.

## Scope

Voice owns craft and judgment. Verification and reproduction belong to
`review-pr` and the relevant investigation workflow; posting mechanics
(suggestion blocks, verdicts) to `post-review` or the app's workflow; PR-body
structure to `pr-description`. Do not use good phrasing as proof of a claim.
