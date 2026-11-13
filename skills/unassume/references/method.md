# Method

## Slips

The clean path shows what a task costs when nothing goes wrong. Losses, guesses, and repairs only appear when something does, so run each slip the surface allows, once.

| Slip | The user |
|---|---|
| Overshoot | goes one past the target and has to come back. |
| Wrong key | hits the neighbouring key or the habit from another tool. |
| Change of mind | starts, then wants out with nothing changed. |
| Typing ahead | acts on the screen they expect instead of the one that is showing. |
| Return | looks away mid-task and comes back needing to know where they are. |

## Counting

Script each run as one input per line. For every version, script the same task and the same slips by the shortest path that version allows. Mechanics for driving and recording live in **droid-control**; this is what to read off the recording.

| Cost | Read it off the recording as |
|---|---|
| loss | Anything the user had before an input and cannot get back after it: typed text that vanished, work or state overwritten, an effect no later input reverses. Name the thing. |
| guess | Inputs whose result the previous frame did not show, and system actions the user did not ask for. List each. |
| repair | The script lines and waits that exist only to undo a guess. |
| step | Lines in the clean script. |
| wait | Time from an input to the first frame that answers it, when nothing else on screen was worth reading. |
| recall | Tokens the user typed or chose that no frame had displayed. |
| reorient | Frames where the focused element, or the text being read, moved without the user moving it. |

- Frequency: with no usage data, estimate from the product's own cues (a bound key, a default path, an onboarding hint) and write the estimate in the table, so a reader can dispute the number.
- Focus and selection often live in styling. A plain-text snapshot drops it; capture a styled frame when a row depends on where focus is.
- For motion, replay at a fifth of the speed or step frame by frame: a wait or a reorient that lasts 80 ms is invisible at full speed and still felt.

Report the count as a table with one row per cost and one column per version, deleted builds included. A change with no differing cell is not an improvement you can claim.

## Probes

An assumption worth naming is a default the interface inherited: from the medium before it, from the order it was built in, or from the way people talk. Ask each question of the costly moment. The first one with a concrete answer gives you the second blank.

| Ask | Default it exposes | Relaxed, it becomes |
|---|---|---|
| Who must finish before the other side shows anything? | Turn-taking: one party acts, then the other. | The system shows its reading while the user is still acting, or the user steers while the system is still working. |
| What does the system already know or intend that it shows late, or never? | Hidden state. | The interpretation, the next state, or the consequence is on screen before the commit. |
| What must be committed before its effect can be seen? | Commit, then see. | A preview, or a commit that one input reverses. |
| Whose keys are these? What does the surface in front do with input meant for the one behind? | A mode the user did not know they entered. | Input goes where the user was aiming, and the surface in front gives way. |
| After the slip, how many inputs get the user back? | One-way travel. | Back costs what forward costs. |
| What is shown once and then gone? | Transience. | It stays where the next action needs it. |
| What happens in sequence that could overlap? | A single thread. | A second channel carries it while the first continues. |
| What does the user decide that has a right default? What does the system decide that the user will undo? | A decision on the wrong side. | A default with a one-input override, or a blank left for the user where the system would have guessed. |
| What is here only because the last medium, or the implementation, needed it? | An inherited constraint. | Gone. |

A well-formed assumption passes three checks: the interface does it (not the user), its negation can be built this week, and the negation removes the cost you ranked first, not a neighbouring one.

When a build dies at step 5, the assumption it relaxed was protecting something. Name what, in the dead build's row: that protection is a constraint on the next build.
