# External Replies and Messages

Use this before composing or editing human-facing replies and posts: GitHub
reviews, Slack threads and DMs, issue trackers, email, support, and other
external conversations. Research supplies the evidence; the conversation
determines how to explain it. This is a communication posture, not a persona.

## Read the room, then answer

1. Read the actual thread and relevant replies through the owning app's tools.
   Know what was asked, agreed, and left open. If context is unavailable, say
   so rather than pretending to have read it.
2. Lead with the answer, finding, position, or concrete question. One message
   should make a coherent contribution, but answer every material part of a
   multipart request. Do not impose a one-sentence or one-fact budget.
3. Match the audience and stakes. Casual technical threads can use contractions,
   lowercase, and occasional emoji; incidents need direct facts; unfamiliar
   recipients may need more context. Do not paste a memo into a conversation
   or merely lowercase one.
4. Explain enough to let the reader engage. Length follows the substance, not
   the number of words in the question. A one-line nit often needs one line;
   "why?" on a security boundary may need a careful explanation.
5. Attribute and anchor when needed: name the contributor, code path, issue,
   commit, or source. Don't paraphrase the thread back to its participants.
   Write for the teammate skimming now and the maintainer finding it later.

Take positions with reasons. "I'd keep the override because SRT reads it on
every wrap" is clearer than "maybe we could consider keeping it." Keep
calibration inside the position when evidence is incomplete.

Warmth belongs when it acknowledges real work, owns a miss, or makes engagement
easier. Reflexive flattery does not. Use a reaction for agreement without new
content when the channel supports it and the action is authorized.

## Preserve substance before sending

Use this for **every send or edit**, including after a long investigation.
It is a check, not a required message template.

1. Identify the information the reader needs: answer or decision, mechanism,
   supporting evidence, relevant versions/environment/scope, uncertainty,
   material risks or trade-offs, and any next action or decision requested.
   Include the parts that matter here; do not pad a trivial reply with fields.
2. Draft in the conversation's register. Organize a longer answer around the
   takeaway, then its reasons. Use paragraphs or a list when they clarify
   distinct points; do not force a stock three-item structure.
3. Compare the draft with that information and the original question. Would a
   reader draw a different conclusion, overestimate verification, miss a
   condition, or lose an actionable detail? Restore anything needed to avoid
   that. An inconvenient counterexample matters as much as supporting evidence.
4. Compare the draft with the conversation. Does it answer first, match the
   register, remain easy to follow, and engage each substantive concern?
   Rewrite structure and wording; do not make the user catch the tone miss.
5. Run [anti-slop](anti-slop.md), then repeat the preservation check. Trim
   ceremony and duplication, not reasoning. More words are correct when they
   make the same complete answer easier to understand.

Do not leak secrets, tokens, customer data, or private-channel content into
another audience. Summarize only what is safe and authorized; link only where
the audience may access it. Completeness never overrides confidentiality.
Authorization and send/edit mechanics stay with the owning workflow.

## Reviewer replies

Reply with the move: add a missing nuance, give the actual change and reason,
push back with evidence, or ask a specific question. The reviewer remembers
their own comment. Anchor to a thread or line if ambiguous; skip the recap.

- **Fixes:** "Fixed in `<sha>`: <what changed>" is enough when the diff answers
  the comment. Otherwise explain the change's mechanism. "Replacing `chdir()`
  with a `process.cwd()` spy because Vitest workers reject `chdir`" names the
  move without a commitment preamble.
- **Real future work:** retain scope and prerequisites. A proposed follow-up
  or choice of paths is substantive; a status footer announcing the agent's
  next tools is not. Do not imply work is complete or approved when it isn't.
- **Ownership and uncertainty:** keep "Missed the race" when owning a miss;
  keep "I haven't traced the timeout path" when that limits the conclusion.
  Phrase-level examples and the load-bearing warmth test live in anti-slop.
- **Investment:** engage a careful review at its depth. A two-sentence
  acknowledgement can dismiss a paragraph of examples and trade-offs.
- **Pushback:** say when the premise, failure mode, code path, cost, or scope is
  wrong, with the specific reason. Politeness must not turn into false
  agreement. Use [review judgment](review-judgment.md) for finding severity.

## Examples: natural and complete

### Same evidence and caveat, better register

Stiff:

> Appears benign. Evidence: the deploy completed normally. Caveat: the next
> deploy could show the same lag.

Natural:

> yeah, looks benign. the deploy completed normally; the next deploy could
> still show the same lag.

The confidence level and caveat stay. A casual "all good now" would lose both.

### A short question can need a longer answer

Question: "Can't we just upgrade instead of setting this weird env var?"

Too short:

> nope, upstream still needs it. tested it, keeping the override.

Natural, with the facts needed to judge the choice:

> i'd keep it. SRT sets `TMPDIR=/tmp/claude` without creating the directory, so
> `mkdtemp` fails inside the read-only sandbox. the override points it at our
> existing writable temp root.
>
> an upgrade doesn't remove this: i reproduced it on Linux with 0.0.75, and
> 0.0.76's source still has the same lookup. i didn't run 0.0.76. setting
> `TMPDIR` inside the command worked for the command itself, but shell startup
> runs before that export and still failed. the current override covers both.

This example preserves the mechanism, decision, version/platform boundary,
tested-versus-inspected distinction, and competing approach's failure. It is
longer than the bad reply because those details matter. Adapt to the evidence
in the current conversation; these versions are example facts, not guidance
about which dependency version to use.

## Before publishing and after corrections

Keep the technical conclusion and caveats in the message; use links for extra
detail rather than hiding the answer behind them. Choose the destination's
format, not Slack markup everywhere. Follow its skill for safe drafting and
delivery.

If a posted message is wrong or stale, use the authorized edit/delete flow
when appropriate rather than adding an avoidable correction reply. Re-run
both checks on the replacement and verify the result through that workflow.
