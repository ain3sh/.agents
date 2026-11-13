# Behavioral replay

Run after editing this skill, as **update-skill** step 6 describes. Each scenario is one open ask against a product the run can launch and drive, and every arm gets the same notes on how to launch it. Grade the build and the count table, not the report.

## Scenarios

Both ran against factory-mono at `efa6623ef05`, where neither cost is fixed.

| # | Prompt | A skill run is expected to |
|---|---|---|
| 1 | "Switching models in the Droid TUI. Make it better." | Run the typing-ahead slip, count the characters dropped while the Ctrl+N picker is open as a `loss`, rank it first, and remove it. Passing through a model stays free of effect. |
| 2 | "Finding and running a slash command in the Droid TUI. Make it better." | Run the own-words slip, find a query whose top row runs an unrelated command, and remove that guess for every query it measured, going round again while one stands. |

## Grading

| Check | Pass |
|---|---|
| Used it | The report cites recordings of the clean path and of each slip, made before any edit. |
| Counted | One table in the seven words, with a column per version, deleted builds included. |
| Top row taken | The build removes the highest-ranked row in the table, not a cheaper one. |
| One assumption | The diff changes the moment the cost is paid and nothing else. |
| Recount decides | A build whose row did not drop, or that raised a row of equal or higher rank, was deleted and its diff kept. |
| Price reported | Every lower row that rose is named. |
| Written back | One case row per build, kept or deleted. |
| Differs from the control | A run without the skill, on the same prompt, did not make the same change. |

## Baseline

One Opus run per line.

| Scenario | Skill | Result |
|---|---|---|
| 1 | none, twice | Both opened the picker on the next model and added a key hint. Both saw the dropped text and left it. |
| 1 | first draft: six costs, no `loss`, no ranking | The same change as the runs without the skill, after deleting one build on measured evidence. Fails "Top row taken" and "Differs from the control". |
| 1 | with `loss`, the ranking, the slips, and rule 6 | Removed the loss: 11 of 11 dropped characters became 0. Typing cancels the picker. |
| 1 | the same, with the picker's rows cut from `cases.md` | Removed the loss: 17 of 17 became 0. Typing switches to the highlighted model, and the run reported the guess that costs. |
| 2 | none | A new ranking tier that improved five queries. |
| 2 | with `loss`, the ranking, the slips, and rule 6 | Fixed one of four intent words and deleted one build. Fails "Differs from the control": the run without the skill fixed more. |

Not yet run: the line under the Act table that says to go again while the top row stands, which exists for scenario 2. A person's gut as the entry point. Any surface outside a terminal.

If an edit moves a check the wrong way, fix the skill text, not the output.
