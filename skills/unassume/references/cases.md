# Cases

Each row is one finished sentence and what happened when it was tested. Read the rows nearest your case before step 3; they show the size of a good move, not answers to copy.

## Format

`symptom` is what a person said or would say. `cost` uses the six words. `assumption` is what the interface did. `move` is the smallest build without it. `verdict` is `picked` (a person chose the build), `rejected` (they chose the original), or `unjudged`.

| Symptom | Cost | Assumption | Move | Verdict |
|---|---|---|---|---|
| "No, I meant…" after an AI answer | repair: a whole turn, retyped and waited for, per misreading | The system shows its reading of the request only after the user sends it. | Show the plan the system would follow while the user is still typing ([Feedforward](https://demos.liubruce.me/intra-turn/)). | unjudged |
| An answer built on a detail the user never gave | guess by the system, then a turn of repair | The system must fill every part of its answer in its own turn. | Leave a blank in the answer for the user to fill, and continue ([Leaving Blanks](https://demos.liubruce.me/intra-turn/)). | unjudged |
| A dropdown "feels sluggish" | wait, during the first frames, which is when the user is watching | Motion should start gently. | Ease-out at the same duration (motion-polish). | picked |
| A popover "comes out of nowhere" | reorient: the eye jumps from the trigger to the popover's centre | An element scales around its own centre. | Scale from the trigger. A modal has no trigger, so its centre is the right origin. (motion-polish) | picked |
| A command palette "feels slow" though it opens in 200 ms | wait, paid a hundred times a day | Every state change deserves a transition. | No animation on keyboard-initiated actions (motion-polish). | picked |
| Scanning a toolbar's tooltips is tedious | wait, once per tooltip | Every hover is a first hover. | After one tooltip opens, the adjacent ones open at once (motion-polish). | picked |

## When a case changes the vocabulary

A person's pick that the count cannot explain means a cost is missing from the six. Name the cost in one word, add it to the table in `SKILL.md` with its unit, and re-file any earlier row it explains better. Two words no case distinguishes collapse into one.
