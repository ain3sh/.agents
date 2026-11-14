# Behavioral replay

Run after editing this skill, as step 6 describes. A run here is a skill edit. Each arm gets a git copy of `skills/` that differs only in this skill's revision, and the same brief. The brief forbids subagents, so the run writes the replay request it would dispatch. Grade the commit and that request, not the report.

## Scenarios

| # | Brief | A run with step 6 is expected to |
|---|---|---|
| 1 | Update **pr-description** from a session report. `gh-attach` failed with a GitHub App token and no browser. The agent read "the repo's `upload-attachments.yml`" in `references/artifacts.md` as the PR's own repository, found no workflow there, and published a text tree in place of the image. The report gives the route that worked later: an `attachments/factory-plugins/<slug>` branch on Factory-AI/factory-mono. | Fix the sentence, write a replay request with a control arm, and leave the scenarios in pr-description's `references/replay.md`. |

Copy `skills/` from `793cf08`, where that sentence is unfixed.

## Grading

| Check | Pass |
|---|---|
| Fix lands | The commit names Factory-AI/factory-mono as the workflow's home and gives the branch for a PR outside the organization. |
| Replay asked | The report holds a request a parent could dispatch as written. |
| Control | The request runs the previous revision on the same brief. |
| Neutral names | No path or description in the request names its arm. |
| Friction | The request asks each run to quote the lines that were unclear, wrong, or in its way. |
| Actions graded | The pass condition reads the run's commands and Markdown, not its summary. |
| Second task | The request has a scenario the session report did not describe. |
| Kept | The commit adds the edited skill's `references/replay.md`. |
| Unproven | The report says the edit is unproven until the runs come back. |

## Baseline

One Opus run per arm.

| Arm | Result |
|---|---|
| Without step 6 | Fixed the sentence in three files. Asked for one run of the new text on two scenarios, because **harness-optimization** asks for a replay. Fails Control, Friction, and Kept. |
| With step 6 | Fixed the sentence in five files. Asked for both revisions on two scenarios, under `<neutral-path-1>` and `<neutral-path-2>`, with the friction list, and wrote `references/replay.md`. Passes every check. |

Both arms pass Fix lands, Replay asked, Actions graded, Second task, and Unproven, so step 6 is not what produced those.

Not yet run: an arm that can dispatch subagents, so no run has graded its own replay or edited from a friction list. The two clauses added after these runs, "without its `replay.md`" and "until it has run, report the edit as unproven", and the later sentences on what a replay is worth and that the user never waits on it. Any model other than Opus.

If an edit moves a check the wrong way, fix the skill text, not the output.
