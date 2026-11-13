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
| 1. Use it | Pick the task a user came to do. Do it in the running product twice: once cleanly, once with the ordinary slip (overshoot, wrong key, change of mind). Record both. If a person's gut fired, the task is what they were doing; ask what they were doing, never why it felt off. | You hold a recording and an input-by-input trace. |
| 2. Count | Tally the trace in the six costs below. Multiply each by how often a user pays it. | One table: cost, where, count, frequency. |
| 3. Name | Take the largest cost and finish the sentence. When the second blank will not come, run the [probes](references/probes.md). | The assumption is something the interface does, and its negation is buildable. |
| 4. Build | Build the smallest version where that one assumption is false, in the real product. | One assumption relaxed, nothing else changed. |
| 5. Compare | Replay step 1's script, input for input, on both versions. Recount. Put the recordings side by side. | The count dropped and no other cost rose by more. Otherwise delete the build and return to step 3. |
| 6. Write back | When a person picks between the two, record the case in [cases](references/cases.md) through **update-skill**. | One row: symptom, cost, assumption, move, verdict. |

## The six costs

| Cost | The user pays it when they | Unit |
|---|---|---|
| step | press, click, or type to get where they were already going | inputs |
| wait | can neither act nor read anything useful | seconds |
| guess | act without seeing what the system will do, or the system acts without knowing what they meant | occurrences |
| repair | undo a wrong guess, theirs or the system's | steps and waits spent |
| recall | supply from memory what the screen could have shown | items |
| reorient | find their place again after the screen changed | occurrences |

Frequency sets the rank: a small cost paid a hundred times a day outranks a large one paid once. [probes](references/probes.md) says how to count each from a recording.

## Detect

- A person says a UI feels off, clunky, slow, or "could be better" and cannot say why.
- The ask is open: "make X better", "rethink X", "what would you change here".
- You are about to justify a UI change with an adjective.

Not this skill: setting visual direction is **frontend-design**; choosing an easing, duration, or gesture value is **motion-polish**, whose rules are cached answers to this loop for motion. When one of its rules does not fit the case in front of you, come back here.

## Rules

1. Never critique from source or screenshots alone: you find what is visible and miss what is paid.
2. Never give an adjective as the reason: "cleaner" and "more intuitive" cannot be recounted. Give a cost and a count.
3. Never name an assumption about the user ("assumes people read the hint"): it has no buildable negation.
4. Never relax two assumptions in one build: the recount cannot say which one paid.
5. Never keep a build the recount does not favour: a cost that only moved is a second interface to maintain.
6. Never add a surface (panel, option, setting, hint) where removing a guess would do: every addition is a step or a recall for someone.
7. Never overrule a person's pick with the count: a pick against the count means the six words missed a cost. Name it and record it.

## Failure map

| Symptom | Action |
|---|---|
| Every finding is about color, spacing, wording, or alignment | You reviewed the screen, not the task. Redo step 1 with a task and the slip. |
| The second blank will not come | Replay the costly moment one input at a time, then run the [probes](references/probes.md). |
| The cost belongs to the task itself (the user must choose something) | Leave it; take the next largest cost. |
| The build touches more than the moment the cost is paid | You are redesigning. Cut back to that moment. |
| Counts tie and one version still feels better | Show both to the person; record their pick and their words. |
| No person is available to pick | Deliver the recount and both recordings as the claim; file the case as `unjudged`. |
| A cached rule contradicts the recount | Check the rule's reason against this case's frequency; follow the recount and say which rule lost. |

## References

Load on demand; do not reabsorb into this file.

- [references/probes.md](references/probes.md): the defaults interfaces inherit, the question that exposes each, and how to count the six costs from a terminal or browser recording.
- [references/cases.md](references/cases.md): the casebook of symptom, cost, assumption, move, and verdict, and the rule for when a case changes the six words.
