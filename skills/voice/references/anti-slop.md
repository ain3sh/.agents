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
