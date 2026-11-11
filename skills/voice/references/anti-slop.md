# Anti-Slop Catalog

A lookup for prose that fails a [craft](craft.md) test. Each family names its shapes, the fix, and when a shape is earned. Load [external replies](external-replies.md) for conversation and completeness checks. These are editing signals, not a word-count target: never remove a meaningful distinction, caveat, or expression of uncertainty to satisfy a pattern.

## Find the family

Do not walk this file sentence by sentence. Reread the draft once with the craft tests, and when a sentence fails one, open its family:

| The sentence | Failed test | Family |
|---|---|---|
| makes the reader feel a finding arrive | Say the thing | [Staging](#staging) |
| sounds settled without showing why | Show what makes it true | [Flat certainty](#flat-certainty) |
| is shorter than the reader can parse | Every word earns its slot | [Compression](#compression) |
| stages nothing and runs on habit | Every word earns its slot | [Defaults](#defaults) |
| wraps a reply in ceremony | Every word earns its slot | [Reply ceremony](#reply-ceremony) |

Before cutting a shape, check its "earned when" and [the shapes that carry claims](craft.md#shapes-that-carry-claims). The families borrow from oaustegard's [declauding](https://github.com/oaustegard/claude-skills/tree/main/declauding) register; look there for more specimens before adding an entry here.

## Staging

The sentence withholds, contrasts, or labels its own importance. The fix is the same throughout: put the real subject in the subject slot, say what it did, and stop.

### Throat-clearing openers
State the content directly. "Here's the thing", "Here's what/why X", "The uncomfortable truth is", "It turns out", "Let me be clear", "The truth is", "I'll be honest". Any "here's what/this/that" is throat-clearing before the point.

### Emphasis crutches
They add no meaning. "Full stop.", "Period.", "Let that sink in.", "Make no mistake", "This matters because", "Here's why that matters".

### Meta-commentary
The prose should move, not announce its own structure. "Let me walk you through...", "In this section we'll...", "As we'll see...", "Plot twist:", "Spoiler:", "But that's another story", "X is a feature, not a bug".

### Vague declaratives
A sentence that announces importance without naming the thing. "The reasons are structural", "The implications are significant", "This is the deepest problem", "The stakes are high". Replace with the specific reason, implication, or stake.

### Binary contrasts
Cut false drama through telegraphed reversal. State the point directly. Preserve real technical contrasts, such as tested versus inspected or local versus remote; rephrase them without erasing the distinction.

| Pattern | Fix |
|---|---|
| "Not because X. Because Y." | "Y, because..." |
| "X isn't the problem. Y is." | "The problem is Y." |
| "The answer isn't X. It's Y." | "Y." |
| "It's not X, it's Y." | "It's Y." |
| "not just X but also Y" | "X and Y." |
| "stops being X and starts being Y" | name the change |

### Negative listing
Listing what something is *not* before saying what it *is* ("Not a X. Not a Y. A Z."). State Z; the reader doesn't need the runway.

### Dramatic fragmentation
Fragments-for-emphasis read as manufactured profundity. "[Noun]. That's it. That's the [thing].", "X. And Y. And Z." Use complete sentences and trust the content.

### Rhetorical setups
They announce insight instead of delivering it. "What if [reframe]?", "Here's what I mean:", "Think about it:", "And that's okay." Make the point; let the reader draw the conclusion.

### Labels, suspense, and closers

| Shape | Looks like | Fix | Earned when |
|---|---|---|---|
| Significance label | "the real fix", "the part that matters", "here's the catch", "that's the whole point", "that's why X mattered" | Delete the label and state the content | The rank is real over a named set: "the only one of the six runs that finished" |
| Deferred noun | "Five of those six rows are one cluster. The sixth is not." | Name it with its number: "fit-17g passes 62 and exhausts 21." | Never; the noun was available |
| Announcement | "One note, not fixed:", "Two things I did not do." | Start with the content | The count introduces a list the reader will scan |
| Suspense | A paragraph that ends on a colon before the culprit; "But here's where it gets interesting."; a lone line such as "It isn't." | State the finding where you have it; put the line back in its paragraph | The colon introduces a list, definition, or code block; the lone line is a real pivot (new actor, time jump) |
| Straw reader | "'It thinks twice as long' is the obvious reading, and it is wrong." | Give the correction directly | The thread or the draft proposed that reading |
| Aphoristic closer | "It is the kind of number that looks like evidence and is not." | Delete it; if the paragraph needs a landing, land on a fact | The line states a fact or consequence the paragraph has not: "Default retries are back to 3." |
| Welded maxim | "Entries the caller lacks are dropped, so a child never carries a grant its parent lacks." | Keep the clause that says what happens | Both clauses carry distinct facts the reader can act on |
| Stranded reversal | "The tool died; the data didn't." | Say what the second half claims: "The rows already written are still in the bucket." | Both halves are measured: "reads passed on all 12 shards, writes on none" |
| Self-grading | "earned, not asserted", "that is what the data shows", "this is rigorous because" | Make the point and stop | Never |
| Dressed metaphor | "information loss wearing the costume of a style fix", "the seam where", "rabbit hole", "under the hood" | Name the mechanism: "the edit removes content while looking like it removed only style" | The metaphor is the clearest description available and no plain noun fits |

### Section headers

A section header is navigation. Read it alone, as a table-of-contents entry: does it say what the section contains?

| Shape | Looks like | Fix | Earned when |
|---|---|---|---|
| Verdict or coy header | "The default was wrong", "What the data actually shows", "Why it matters", "X is dead" | Label the content with a concrete noun phrase: "The 2.876-bit gap" | The owning format asks for the claim there: a PR title, a finding card, a design-doc headline |
| Abstract-noun header | "Spawn availability", "GitHub authorship in a sourced child" | Name the concrete thing or the reader's question: "When create_session fails" | The noun is a term the document defines |
| Contents-list opener | "The parameter surface, plus the behavior the schema leaves out." | Say what the page contains, or drop the subtitle | Never |

### False agency
Inanimate things don't perform human actions. AI reaches for this because it dodges naming the actor.

| Pattern | Fix |
|---|---|
| "the decision emerges" | "the team decided" / "you decide" |
| "the complaint becomes a fix" | "someone fixed it" |
| "the data tells us" | "the logs show" |
| "the test guarantees X" | "the test asserts X" |
| "the abstraction wants to..." | name what the code does |
| "the docstring promises they're skipped" | "according to the docstring, they're skipped" |

If no specific person fits, use "you" or name the code path. A pairing the field already uses is earned: "the function expects an int".

### Passive voice
Passive hides the actor and drains energy: "X was created" becomes "the migration creates X"; "it is believed that" becomes "we assume"; "mistakes were made" becomes "we missed X". Find the actor; lead with it. A fragment with no subject hides the actor the same way: "Results are preserved automatically" becomes "the runner writes results to `out/` when the job exits".

## Flat certainty

Nothing is staged. An adverb, compound, or absolute asserts that the matter is closed, and the evidence that would close it is missing.

| Shape | Looks like | Fix | Earned when |
|---|---|---|---|
| Certainty adverb | "provably safe", "quietly dropped", "plainly", "genuinely", "outright" | Delete it, or replace it with what makes it true: "The retry is idempotent: the handler keys on the request id." | It names a contrast the reader can check: "silently" against a version that logs |
| Courtroom verb | "The guard refuses any caller without standing", "ruling", "carve-out", "honors" | Name the mechanism and its exit: "The guard returns 403 when the token has no `write` scope." | It is the system's own documented word: a policy engine whose API says `deny` |
| Verification compound | "byte-identical", "mutation-checked", "root-caused", "re-verified", "re-derived" | Say what ran and what came back: "`diff` reports no change. The mutation run killed 14 of 15." | The command or number sits beside it |
| Coined absence | "unguarded", "unwired", "vacuous", "inert" | Say what is missing and where: "Three paths have no length check before the index." | It is the field's own term: "unsatisfiable" |
| Absolute | "nothing in it does X", "no path reaches", "never", "nobody", "every", "always", "everyone" | State the scope you checked: "The fit has one parameter per cluster and none per week." | The set is bounded and named: "none of the 46 chunks", "the enum has three members and the switch covers all three" |
| Verdict adjective | "aggressive", "surprising", "brutal", "collapse" for a 15-point drop | Let the number be the adjective | Never |

## Compression

The sentence saves words and spends the reader's parse effort. The fix makes it longer.

| Shape | Looks like | Fix | Earned when |
|---|---|---|---|
| Noun stack | "dry-run write prevention", "Policy 1's class-time shutdown requirement" | Unstack with prepositions or a clause: "check that a dry run writes nothing" | An established term ("foreign key constraint"), or a name the document defines once |
| Verbed noun | "footnote it", "ticket that" | Use a plain verb with the noun as its object: "move it to a footnote" | The conversion is standard in the field: scope, gate, shard |
| Dropped *that* | "the others check behaviour the old code never reached" | Put *that* back when the clause is long or its subject is new | A short clause after a common verb: "I think the build is broken" |
| Distant verb | "All five expression shapes (attribute access, subscript, calls, nested calls, string literals) leave `current` on `b`" | Give the verb early and move the list after the main clause | The list is two or three short items |

## Defaults

Nothing is staged or compressed. The writer took the first available phrase.

### Empty intensifiers and hedges
Cut these when empty: really, just, literally, genuinely, honestly, simply, actually, basically, deeply, truly, fundamentally, inherently, inevitably, interestingly, importantly, crucially. Plus filler: "At its core", "It's worth noting", "At the end of the day", "When it comes to", "The reality is".

Keep adverbs that carry technical meaning: *explicitly*, *idempotently*, *atomically*, *synchronously*, and uncertainty that reflects the evidence ("likely", "not yet verified"). The test is whether deleting the word loses information. One hedge tied to its condition carries all the uncertainty that three stacked hedges do.

### Business jargon

| Avoid | Use |
|---|---|
| navigate (challenges) | handle, address |
| unpack | explain, examine |
| lean into | accept, commit to |
| landscape | situation, field |
| deep dive | analysis |
| take a step back | reconsider |
| circle back | revisit |
| moving forward | next, from now on |

The stock model vocabulary fails the same way: delve, tapestry, testament to, robust, seamless, leverage, utilize, crucial, pivotal, myriad, unlock, harness. Use the specific word.

### Sentence starters
Wh- openers become a crutch: "What makes this hard is..." becomes "The constraint is..." or, better, the named constraint. Drop leading "So," and "Look,".

### Rhythm
Vary sentence length; break up three consecutive sentences of the same length. Avoid em dashes. Don't stack staccato fragments. Use as many items as the distinct points need rather than forcing a stock triad. Don't end every paragraph on a punchy one-liner.

### Stock constructions

| Shape | Looks like | Fix | Earned when |
|---|---|---|---|
| Ceremonial verb | "serves as", "stands as", "boasts", "features" | Use "is" or "has" | The verb states a real purpose or role |
| Participle tail | "..., highlighting the team's commitment", "..., ensuring consistency" | Cut the tail | The tail holds a real claim; promote it to its own sentence |
| Renamed referent | "the model", "the system", "the network" for one thing | Pick the noun and repeat it | The second term names a different thing |
| False range | "from startups to enterprises" | List the items, or give the real endpoints | The scale exists: "from 2 to 8 bits" |
| Bold-label bullet | "- **Performance:** Performance has been improved" | Write the sentence, or drop the label | The label is a real index: a term, a flag, a case name |
| Scattered typography | Bold on phrases that are not terms, Title Case Headings, emoji as bullets | Bold a term on first use; sentence case | The destination's house style sets it |
| Doc written from the diff | "this function was added to replace", "we now use", "no longer" | Describe current behavior | The document is scoped to a version: changelog, release notes, migration guide |
| Chat wrapper in an artifact | "Certainly", "Here is an overview of", "I hope this helps" | Delete it | Never |

## Reply ceremony

### Reviewer-reply sycophancy
The warm-up before the actual reply. *Reflexive* warmth, when every reply opens with one ("Good catch", "Great point", "Great call", "Nice catch", "Fair", "Fair point", "You're right", "You're absolutely right", "Right,", "Yeah,", "Yep,", "Agreed.", "Apologies for the oversight", "Thanks for catching this"), is filler; cut on sight if the next sentence is just "I'll fix it." The fix is the agreement.

*Load-bearing* warmth is the same word doing work. "Yeah, missed this; the inflight guard from v1 didn't survive the rewrite" owns the regression, names the mechanism, and lets the reviewer trust the fix in one sentence. "Good catch, the second-tenant case slipped me" works when the catch was non-trivial. The test: does the reviewer learn something from the warm-up? If yes, keep it. If they could delete it and read the rest unchanged, cut it. Opening with "Fair" on a position you're about to dismantle three sentences later is worse than slop; it's dishonest.

### Reviewer-reply preamble
Restating the reviewer's comment back to them. "The e2e smoke covers X, but this unit test doesn't bind Y, so it would not fail on Z..." (when the reviewer just said exactly that). They wrote it; they remember it. Lead with the answer.

*Anchoring* is different: a one-fragment pointer ("On the `repoRoot()` thread:", "Re: the L47 null check:") disambiguates which thread or line you're answering when context could read either way. Anchor when needed; never recap.

### Performative future tense
"I'm going to fix the test with a `process.cwd()` spy" wraps the actual content (`process.cwd()` spy) in commitment ceremony. Drop the wrapper. "Replacing `process.chdir()` with a `process.cwd()` spy" carries the same information without the preamble.

*Real* future tense earns its slot when the work is genuinely future and scoped: "The soak suite takes 20 minutes; posting its result on this thread when it finishes." Deferring a real issue to a later PR is not future tense, it is a dropped fix: fix it here or name the decision. The test: is the future-tense clause describing work that lives outside this turn, or disguising "I'm about to type the fix" as commitment?

### Status footers
Status belongs in the agent loop, not in the reply body. "Waiting for your confirmation before I patch, run checks, push, reply, and...", "Let me know if you'd like me to proceed", "Will run tests and push once you confirm", "Standing by for your go-ahead". If the user wants a confirmation gate, it's a turn boundary; the reply carries technical content.

*Substantive proposals* aren't footers, even when they ask a question: "Should the retry cap apply to the auth path too, or only to uploads?", "Should I scope this to the auth path only, or land it everywhere?" That's content. The difference: a footer announces what the agent will do; a proposal asks the reviewer to choose between concrete paths.

## Before / after (our world)

**PR description**
- Before: "This PR fundamentally improves how we handle errors. It's worth noting the previous approach wasn't ideal; here's the thing, errors were being swallowed."
- After: "The retry loop swallowed parse errors, so failed syncs looked successful. `sync()` now throws `ParseError` instead of logging and continuing."

**Review comment**
- Before: "Consider maybe thinking about whether this might possibly race?"
- After: "**[warning]** If a second request arrives during reconnect, both call `refresh()` and you double-spend the token. Guard with the existing `inflight` promise."

**Ticket**
- Before: "Improve onboarding. The current experience is suboptimal and the implications are significant."
- After: "New users drop at the workspace-picker step (38% don't continue). Default to a personal workspace so first-run lands in the editor. Done when a fresh signup reaches the editor with no manual selection."

**Reviewer reply (filler-stack, all four anti-patterns firing)**
- Before: "Good catch. The e2e smoke covers the real startup path, but this unit test does not currently bind the fake repo to `process.cwd()`, so it would not fail on a future cwd-candidate regression. I'm going to fix the test with a `process.cwd()` spy instead of `process.chdir()`, because Vitest workers reject `chdir`; that exercises the same production lookup without changing the process working directory.\n\nWaiting for your confirmation before I patch, run checks, push, reply, and..."
- After: "The unit test wasn't binding the fake repo to `process.cwd()`, so a cwd-candidate regression slips past it. Swapping in a `process.cwd()` spy (Vitest workers reject `chdir`) so the test hits the production lookup."

Failure anatomy:
1. Sycophantic opener ("Good catch"). Cut: reflexive, didn't earn its slot.
2. Recap of what the reviewer just said about the e2e smoke and the unit test. Cut; the reviewer wrote it.
3. "I'm going to fix the test with..." performative wrapper around the actual content (`process.cwd()` spy). Unwrap.
4. Status footer ("Waiting for your confirmation before I patch, run checks, push, reply..."). Cut; status isn't reply content.

What's left after stripping the four is the diagnosis (test wasn't binding the fake repo) and the change-shape (cwd spy, because chdir is rejected). That's the reply.

**Reviewer reply (warmth performed; cut)**
- Reviewer: "Missing semicolon on L42."
- Before: "Great catch! Thanks for the careful review, I really appreciate it. I'll fix this right away. Apologies for the oversight."
- After: "Fixed in `<sha>`."

A one-line nit gets a one-line reply. The Before's gratitude is performed (reviewer ran a linter and pasted the result); the After respects their time.

**Reviewer reply (warmth load-bearing; keep)**
- Reviewer: "If a second request arrives during reconnect, both call `refresh()`. We hit this exact race in `auth-svc` last quarter; took two hours to repro."
- Reply: "Yeah, missed this; the inflight guard from v1 didn't survive the rewrite. Re-adding in `<sha>` and porting the auth-svc multi-request repro as a regression test here."

Why every word earns its slot: "Yeah, missed this" owns the regression instead of deflecting. "The inflight guard from v1 didn't survive the rewrite" tells the reviewer the *mechanism* of the miss, so they can trust the fix is at the right layer. "Porting the auth-svc repro" acknowledges their hard-won experience without flattering it. Strip the warmth and humility here and the reply gets shorter but worse: the reviewer can no longer tell whether you understood the failure mode or just patched the symptom.

**Reviewer reply (calibrated uncertainty; keep)**
- Reviewer: "Doesn't this race against the timeout path?"
- Reply: "Not sure yet; the lock is held across the refresh call, but I haven't traced what happens if the timeout fires mid-refresh. Adding a logging probe in `<sha>` and running the soak suite; will follow up with the trace."

The hedge ("not sure yet", "haven't traced") is calibration, not slop. It tells the reviewer exactly what's known, what isn't, and what you're doing to close the gap. The future tense at the end is load-bearing: the work is genuinely future (soak suite takes 20 minutes), and the commitment is scoped (one trace, one follow-up).
