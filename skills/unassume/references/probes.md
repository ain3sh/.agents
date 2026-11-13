# Probes and counting

## Probes

An assumption worth naming is a default the interface inherited: from the medium before it, from the order it was built in, or from the way people talk. Ask each question of the costly moment. The first one with a concrete answer gives you the second blank.

| Ask | Default it exposes | Relaxed, it becomes |
|---|---|---|
| Who must finish before the other side shows anything? | Turn-taking: one party acts, then the other. | The system shows its reading while the user is still acting, or the user steers while the system is still working. |
| What does the system already know or intend that it shows late, or never? | Hidden state. | The interpretation, the next state, or the consequence is on screen before the commit. |
| What must be committed before its effect can be seen? | Commit, then see. | A preview, or a commit that one input reverses. |
| After the ordinary slip, how many inputs get the user back? | One-way travel. | Back costs what forward costs. |
| What is shown once and then gone? | Transience. | It stays where the next action needs it. |
| What happens in sequence that could overlap? | A single thread. | A second channel carries it while the first continues. |
| What does the user decide that has a right default? What does the system decide that the user will undo? | A decision on the wrong side. | A default with a one-input override, or a blank left for the user where the system would have guessed. |
| What is here only because the last medium, or the implementation, needed it? | An inherited constraint. | Gone. |

A well-formed assumption passes three checks: the interface does it (not the user), its negation can be built this week, and the negation removes the cost you counted, not a neighbouring one.

## Counting

Script the task as one input per line, then replay that script unchanged against every version. Mechanics for driving and recording live in **droid-control**; this is what to read off the recording.

| Cost | Read it off the recording as |
|---|---|
| step | Lines in the script. |
| wait | Time from an input to the first frame that answers it, when nothing else on screen was worth reading. |
| guess | Inputs whose result the previous frame did not show, and system actions the user did not ask for. List each. |
| repair | The script lines and waits that exist only to undo a guess. Run the slip variant to find them. |
| recall | Tokens the user typed or chose that no frame had displayed. |
| reorient | Frames where the focused element, or the text being read, moved without the user moving it. |

For motion, record and replay at a fifth of the speed, or step frame by frame: a wait or a reorient that lasts 80 ms is invisible at full speed and still felt.

Report the count as a table with one row per cost and one column per version. A change with no differing cell is not an improvement you can claim.
