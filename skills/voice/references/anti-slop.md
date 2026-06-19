# Anti-Slop Catalog

The full catalog of AI writing tells, tuned for technical writing. `SKILL.md` carries the high-frequency subset; open this when editing or reviewing prose.

## Quick checks (run before delivering prose)

- Empty intensifier or hedge (really, just, simply, genuinely, basically)? Cut it.
- Passive voice? Name the actor and put it in front.
- Inanimate thing doing a human verb ("the decision emerges", "the data tells us")? Name the person or code path.
- Sentence starts with a Wh- word ("What makes this hard is...")? Restructure to lead with the subject.
- Throat-clearing opener ("Here's the thing", "It's worth noting")? Cut to the point.
- Binary contrast ("Not X, but Y")? State Y directly.
- Vague declarative ("the implications are significant")? Name the specific implication.
- Lazy extreme (every, always, never, everyone, nobody)? Use the specific scope.
- Em dash anywhere? Replace with a comma, parentheses, or two sentences.
- Three consecutive sentences of the same length? Break one.
- Reviewer reply opens with an acknowledgement ("Good catch", "You're right", "Agreed.", "Fair")? Apply the load-bearing test: did the catch take unusual work, or are you owning a position you held? Keep one beat when earned; cut when reflexive.
- Reviewer reply paraphrases the comment back before answering? Cut the recap (the reviewer wrote it) unless you're anchoring a specific thread or line.
- Reply contains "I'm going to fix..." / "I'll address..." without the change-shape? Drop the wrapper and lead with the diff shape. Keep future tense only when the work is genuinely future and scoped.
- Reply ends with a status footer ("Waiting for your confirmation", "Will run tests then push")? Cut, unless it's a substantive proposal that asks the reviewer to choose a path ("Want to land as-is and file a follow-up?").

## Phrases to cut

### Throat-clearing openers
State the content directly. "Here's the thing", "Here's what/why X", "The uncomfortable truth is", "It turns out", "Let me be clear", "The truth is", "I'll be honest". Any "here's what/this/that" is throat-clearing before the point.

### Emphasis crutches
They add no meaning. "Full stop.", "Period.", "Let that sink in.", "Make no mistake", "This matters because", "Here's why that matters".

### Empty intensifiers and hedges
Delete. really, just, literally, genuinely, honestly, simply, actually, basically, deeply, truly, fundamentally, inherently, inevitably, interestingly, importantly, crucially. Plus filler: "At its core", "It's worth noting", "At the end of the day", "When it comes to", "The reality is".

Keep adverbs that carry technical meaning: *explicitly*, *idempotently*, *atomically*, *synchronously*. The test is whether deleting the word loses information.

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

### Meta-commentary
The prose should move, not announce its own structure. "Let me walk you through...", "In this section we'll...", "As we'll see...", "Plot twist:", "Spoiler:", "But that's another story", "X is a feature, not a bug".

### Vague declaratives
A sentence that announces importance without naming the thing. "The reasons are structural", "The implications are significant", "This is the deepest problem", "The stakes are high". Replace with the specific reason, implication, or stake.

### Reviewer-reply sycophancy
The warm-up before the actual reply. *Reflexive* warmth, when every reply opens with one ("Good catch", "Great point", "Great call", "Nice catch", "Fair", "Fair point", "You're right", "You're absolutely right", "Right,", "Yeah,", "Yep,", "Agreed.", "Apologies for the oversight", "Thanks for catching this"), is filler; cut on sight if the next sentence is just "I'll fix it." The fix is the agreement.

*Load-bearing* warmth is the same word doing work. "Yeah, missed this; the inflight guard from v1 didn't survive the rewrite" owns the regression, names the mechanism, and lets the reviewer trust the fix in one sentence. "Good catch, the second-tenant case slipped me" works when the catch was non-trivial. The test: does the reviewer learn something from the warm-up? If yes, keep it. If they could delete it and read the rest unchanged, cut it. Opening with "Fair" on a position you're about to dismantle three sentences later is worse than slop; it's dishonest.

### Reviewer-reply preamble
Restating the reviewer's comment back to them. "The e2e smoke covers X, but this unit test doesn't bind Y, so it would not fail on Z..." (when the reviewer just said exactly that). They wrote it; they remember it. Lead with the answer.

*Anchoring* is different: a one-fragment pointer ("On the `repoRoot()` thread:", "Re: the L47 null check:") disambiguates which thread or line you're answering when context could read either way. Anchor when needed; never recap.

### Performative future tense
"I'm going to fix the test with a `process.cwd()` spy" wraps the actual content (`process.cwd()` spy) in commitment ceremony. Drop the wrapper. "Replacing `process.chdir()` with a `process.cwd()` spy" carries the same information without the preamble.

*Real* future tense earns its slot when the work is genuinely future and scoped: "Adding the stress test in a follow-up; this PR is already 800 lines, and the test infra needs a refactor first." The test: is the future-tense clause describing work that lives outside this turn, or disguising "I'm about to type the fix" as commitment?

### Status footers
Status belongs in the agent loop, not in the reply body. "Waiting for your confirmation before I patch, run checks, push, reply, and...", "Let me know if you'd like me to proceed", "Will run tests and push once you confirm", "Standing by for your go-ahead". If the user wants a confirmation gate, it's a turn boundary; the reply carries technical content.

*Substantive proposals* aren't footers, even when they ask a question: "Want to land as-is and file a follow-up?", "Should I scope this to the auth path only, or land it everywhere?" That's content. The difference: a footer announces what the agent will do; a proposal asks the reviewer to choose between concrete paths.

## Structures to break

### Binary contrasts
False drama through telegraphed reversal. State the point directly.

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

### False agency
Inanimate things don't perform human actions. AI reaches for this because it dodges naming the actor.

| Pattern | Fix |
|---|---|
| "the decision emerges" | "the team decided" / "you decide" |
| "the complaint becomes a fix" | "someone fixed it" |
| "the data tells us" | "the logs show" |
| "the test guarantees X" | "the test asserts X" |
| "the abstraction wants to..." | name what the code does |

If no specific person fits, use "you" or name the code path.

### Passive voice
Passive hides the actor and drains energy: "X was created" becomes "the migration creates X"; "it is believed that" becomes "we assume"; "mistakes were made" becomes "we missed X". Find the actor; lead with it.

### Sentence starters
Wh- openers become a crutch: "What makes this hard is..." becomes "The constraint is..." or, better, the named constraint. Drop leading "So," and "Look,".

### Rhythm
Vary sentence length. Avoid em dashes. Don't stack staccato fragments. Two items often beat three. Don't end every paragraph on a punchy one-liner.

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
