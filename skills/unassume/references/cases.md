# Cases

Each row is one finished sentence and what happened when it was tested. Read the rows nearest your case before step 3; they show the size of a good move, not answers to copy.

A row records a build and its test, not what any product ships today; check the product before you count.

`symptom` is what a person said or would say. `cost` uses the seven words. `assumption` is what the interface did. `move` is the smallest build without it. `verdict` is `picked` (a person chose the build), `rejected` (they chose the original), or `unjudged`.

## Kept builds

| Symptom | Cost | Assumption | Move | Verdict |
|---|---|---|---|---|
| "No, I meant…" after an AI answer | repair: a whole turn, retyped and waited for, per misreading | The system shows its reading of the request only after the user sends it. | Show the plan the system would follow while the user is still typing ([Feedforward](https://demos.liubruce.me/intra-turn/)). | unjudged |
| An answer built on a detail the user never gave | guess by the system, then a turn of repair | The system must fill every part of its answer in its own turn. | Leave a blank in the answer for the user to fill, and continue ([Leaving Blanks](https://demos.liubruce.me/intra-turn/)). | unjudged |
| A dropdown "feels sluggish" | wait, during the first frames, which is when the user is watching | Motion should start gently. | Ease-out at the same duration (motion-polish). | picked |
| A popover "comes out of nowhere" | reorient: the eye jumps from the trigger to the popover's centre | An element scales around its own centre. | Scale from the trigger. A modal has no trigger, so its centre is the right origin. (motion-polish) | picked |
| A command palette "feels slow" though it opens in 200 ms | wait, paid a hundred times a day | Every state change deserves a transition. | No animation on keyboard-initiated actions (motion-polish). | picked |
| Scanning a toolbar's tooltips is tedious | wait, once per tooltip | Every hover is a first hover. | After one tooltip opens, the adjacent ones open at once (motion-polish). | picked |
| A model-cycle key in a terminal agent: "the first press does nothing" | step: one extra input on every switch | The picker opens with the model you already have selected. | The press that opens the picker counts as the first step of the cycle. | unjudged |
| The same picker: "what I typed disappeared" | loss: every character typed while the picker shows (11 of 11), then repair: Esc and retype, 12 inputs | The picker owns every key while it is shown. | A typed character closes the picker with no switch, and the same press lands in the prompt. | unjudged |
| A command menu: typing your own word for a command and pressing Enter runs an unrelated one | guess on Enter or Tab, then 10 to 17 inputs of repair and a lost query | Commands that matched only by description are ordered by menu group before match strength. | Order description-only matches by match strength first; leave name matches alone. | unjudged |

## Deleted builds

A build the recount killed. `lesson` says why: what the assumption was protecting, which constrains the next build on that surface, or that it was not the assumption causing the row.

| Assumption relaxed | What the build bought | What the recount found | Lesson |
|---|---|---|---|
| A model-cycle key must be confirmed with Enter before the switch takes effect. | step: 4 inputs became 2; typing ahead was no longer dropped. | loss: cycling past a model from another provider rewrote the conversation history, with no way back. guess: a burst of three presses landed on one model. | Protects: the confirm is the only point where the user says which model they meant. A build on this surface must keep passing through models free of effect. |
| A command menu searches each command's source description, not the text its row displays. | step: the wanted command rose from off screen to row 2 for one query. | The top row did not change for any of four queries, so every guess remained. | Not the cause of the row taken. It is a separate cost on the same surface. |

## When a case changes the vocabulary

A person's pick, or a recount, that the words cannot express means a cost is missing. Name it in one word, add it to the table in `SKILL.md` with its unit, and re-file any earlier row it explains better. Two words no case distinguishes collapse into one.

`loss` entered this way. The first trial counted typed keys that vanished and a conversation that could not be restored, and filed both under `repair`, which they are not: nothing the user does afterwards buys them back.
