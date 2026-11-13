---
name: unassume
description: "Use when UI or UX feels off, or an ask to improve or rethink an interaction comes with no spec: count what it costs the user, name the assumption behind the cost, build the smallest version without it."
---

# Unassume

Taste detects cost. "This feels off" means someone is paying for an assumption the interface never had to make. Find the payment, name the assumption, build the smallest version where it is false, and let the recount decide.

Finish this sentence before proposing anything: **"This costs ___ because the interface assumes ___."**

## Act

| Step | Do | Done when |
|---|---|---|
| 1. Use it | Pick the task a user came to do; when the ask names a whole surface, take the path the product advertises first. Do it in the running product: once cleanly, then once for each ordinary [slip](references/method.md#slips). Record every run. If a person's gut fired, the task is what they were doing; ask what they were doing, never why it felt off. | You hold a recording and an input-by-input trace of every run. |
| 2. Count | Tally every run in the seven costs below: one row per cost found, with where it is paid, the count, and how often a user pays it. | One table, kept through the loop. |
| 3. Name | Rank the rows, take the top one, and finish the sentence. Read the [cases](references/cases.md) nearest yours first; when the second blank will not come, run the [probes](references/method.md#probes). | The assumption is something the interface does, and its negation is buildable. |
| 4. Build | Build the smallest version where that one assumption is false, in the real product. | One assumption relaxed, nothing else changed. |
| 5. Compare | Redo step 1's task and slips on both versions, by the shortest path each allows, and add a count column per version. Compare a row only with itself. Put the recordings side by side. | The row you took dropped and no row of its rank or higher rose. A lower row that rose is the build's price: report it. Otherwise delete the build, keep its diff, write down why it died, and return to step 3. |
| 6. Write back | Record each build, kept or deleted, in [cases](references/cases.md) through **update-skill**. The verdict comes from the person who picks between the versions. | One row per build. |

One pass removes one assumption. While the top row still stands and time remains, start again at step 3 with the same table.

## The seven costs

| Cost | The user pays it when they | Unit |
|---|---|---|
| loss | lose something they had: typed text, finished work, a state they cannot restore | what was lost |
| guess | act without seeing what the system will do, or the system acts without knowing what they meant | occurrences |
| repair | undo a wrong guess, theirs or the system's | steps and waits spent |
| step | press, click, or type to get where they were already going | inputs |
| wait | can neither act nor read anything useful | seconds |
| recall | supply from memory what the screen could have shown | items |
| reorient | find their place again after the screen changed | occurrences |

Rank by what the user can do about the cost. A loss comes first, because they cannot get it back. A guess and the repair it forces come next, because they are paid by surprise. Step, wait, recall, and reorient are paid knowingly on the clean path and come last, unless one is paid hundreds of times a day.

## Detect

- A person says a UI feels off, clunky, slow, or "could be better" and cannot say why.
- The ask is open: "make X better", "rethink X", "what would you change here".
- You are about to justify a UI change with an adjective.

Not this skill: setting visual direction is **frontend-design**; choosing an easing, duration, or gesture value is **motion-polish**, whose rules are cached answers to this loop for motion. When one of its rules does not fit the case in front of you, come back here.

## Rules

1. Never critique from source or screenshots alone: you find what is visible and miss what is paid.
2. Never give an adjective as the reason: "cleaner" and "more intuitive" cannot be recounted. Give a cost and a count.
3. Never name an assumption about the user ("assumes people read the hint"): it has no buildable negation.
4. Never relax two assumptions in one build: the recount cannot say which one paid. Fixing a defect the build introduced is not a second assumption.
5. Never keep a build the recount does not favour: a cost that only moved is a second interface to maintain.
6. Never answer a deleted build by taking a cheaper row: the ranking has not changed. Take the top row again with a different assumption.
7. Never add a surface (panel, option, setting, hint) where removing a guess would do: every addition is a step or a recall for someone.
8. Never overrule a person's pick with the count: a pick against the count means the seven words missed a cost. Name it and record it.

## Failure map

| Symptom | Action |
|---|---|
| Every finding is about color, spacing, wording, or alignment | You reviewed the screen, not the task. Redo step 1 with a task and its slips. |
| Every row is a step or a wait | You ran only the clean path. Run the [slips](references/method.md#slips). |
| The second blank will not come | Replay the costly moment one input at a time, then run the [probes](references/method.md#probes). |
| The cost belongs to the task itself (the user must choose something) | Leave it; take the next row. |
| The build touches more than the moment the cost is paid | You are redesigning. Cut back to that moment. |
| Two builds have died on the same row | Stop building. Deliver the counts, both builds, and why each died. |
| Counts tie and one version still feels better | Show both to the person; record their pick and their words. |
| No person is available to pick | Deliver the recount and both recordings as the claim; file the case as `unjudged`. |
| A cached rule contradicts the recount | Check the rule's reason against this case's frequency; follow the recount and say which rule lost. |
| The product cannot be run | This skill has no first step. Say so; a source review is not a substitute. |

## References

Load on demand; do not reabsorb into this file.

- [references/method.md](references/method.md): the slips to run at step 1, how to count the seven costs from a recording, and the probes that expose an inherited assumption.
- [references/cases.md](references/cases.md): the casebook of kept and deleted builds, and the rule for when a case changes the seven words.
