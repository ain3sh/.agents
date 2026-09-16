---
name: voice
description: Write user-visible prose and reviews. Load for external replies and messages (GitHub, Slack, tickets, email), PR bodies, docs, commits, and findings; match the audience without losing substance.
user-invocable: false
---

# Voice

Write like a thoughtful teammate: specific, direct, natural for the audience,
and complete enough for the reader to judge or act.

## Act

| Goal | Load and do |
|---|---|
| Author or assess prose | Load [craft](references/craft.md); identify what the reader needs before editing. |
| Reply or post externally | Also load [external replies](references/external-replies.md) before drafting or editing, including after an investigation. Apply it across GitHub, Slack, tickets, email, support, and other human-facing conversations. |
| Review someone else's work | Also load [review judgment](references/review-judgment.md); surface warranted opinions with its canonical severity taxonomy. |
| Edit or finalize prose | Load [anti-slop](references/anti-slop.md); remove filler, then re-check that no material information disappeared. |

## Detect

If another skill mentions **voice**, load this entrypoint rather than recalling
an older version. Route by what you are doing, not by the app: a GitHub reply
needs the same audience-aware craft as a Slack reply. A review reply also needs
review judgment when it makes a finding about someone else's work.

## Rules

1. Never trade substance for brevity. Preserve the reasoning, evidence, scope,
   uncertainty, caveats, and next action that affect the reader's decision.
   Shorten ceremony and duplication; add words when they make the answer lucid.
2. Never use casualness as a costume. Match the actual conversation; lowercase,
   contractions, and emoji are options, not a required persona.
3. Never let tone change the claim. Preserve confidence and verification limits;
   sounding relaxed does not justify a stronger conclusion.
4. Never publish by virtue of loading this skill. Authorization and posting
   belong to the owning workflow; voice owns craft and judgment only.

## Failure map

| Symptom | Action |
|---|---|
| Reply sounds like an incident report pasted into a casual thread | Restructure using [external replies](references/external-replies.md); lowercasing is not a rewrite. |
| Shorter draft loses a mechanism, caveat, or answer | Restore it with the preservation check in [external replies](references/external-replies.md#preserve-substance-before-sending). |
| Warmth or uncertainty was stripped as filler | Apply the load-bearing test in [craft](references/craft.md). |
| Review withholds architectural or design pushback | Apply [review judgment](references/review-judgment.md); state the concrete reason and calibrated severity. |
| Prose has formulaic openings or status footers | Run [anti-slop](references/anti-slop.md), then check completeness again. |

## References

Load on demand; do not reabsorb into this file:

- [references/craft.md](references/craft.md): specificity, load-bearing humanity,
  information-preserving edits, and scope boundaries.
- [references/external-replies.md](references/external-replies.md): audience,
  conversation context, reviewer replies, preservation checks, and examples.
- [references/review-judgment.md](references/review-judgment.md): opinion license,
  finding coverage, canonical severity taxonomy, and final review sweep.
- [references/anti-slop.md](references/anti-slop.md): phrase and structure catalog,
  editing checks, and before/after examples.
