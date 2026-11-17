# Behavioral replay

Run after editing the approval gate (`workflows/first-pass.md` §6), the draft layout (`systems/dossier.md`), or how **post-review** consumes the draft, as **update-skill** step 6 describes. Each arm gets a git copy of `skills/` that differs only in the revision under test, at a path that names neither arm. One fresh worker per arm and scenario reads `review-pr/SKILL.md` by path, never through the Skill tool and never this file. The brief is the dry run below; grade the files it writes, not its summary.

## Brief

> You are a Droid running the `review-pr` skill. The skills you have are at `<arm>/skills`: read them by path, starting from `review-pr/SKILL.md`. Situation: `<situation>`. The review is finished through the review-state summary, which is in `<fixture>`. You are now at the user approval gate: do exactly what the skills say at this step, and stop where they say to wait. Dry run: do not post, upload, or use the network. In `<out>`, write `actions.md` (every action in order, the full text of each message, how each file is attached or shown, and an outline instead of any HTML page you would build), every file you would create at its path mapped under `<out>`, and a `## Friction` section quoting each skill line that was unclear, wrong, or in your way.

## Scenarios

Fixtures are in `replay-fixtures/`. Their view paths point under `views/`; copy any rendered PNG to those names, since the workers never need to open them.

| # | Situation | Fixture | Expected |
|---|---|---|---|
| 1 | Delegated from a Slack thread; `/review-pr 32759 ground-up` | `pr-32759.md` (12 findings, 3 views, head moved since review) | Writes `./.agents/review.draft.md` with the verdict and one thread per anchored finding; attaches one HTML page ending in *Draft as posted* plus the draft file; sends one short closing message; uploads no PNG separately and makes no PDF |
| 2 | Droid TUI on the user's laptop; the TUI shows chat and any image a Script passes to `image()` | `pr-32759.md` | Writes the same draft; the chat message carries findings by file and the verdict body, each view goes through `image()`, the draft's path is given; no HTML page |
| 3 | Delegated from a Slack thread; `/review-pr 4410 follow-up` (held out: not the PR the edit was written from) | `pr-4410.md` (one prior thread resolved, one open nit, one new warning, 1 view) | Draft holds the verdict, the new inline thread, and a `# Thread replies` entry resolving 9001; same Slack delivery as scenario 1 |

## Grading

| Check | Pass |
|---|---|
| Draft written | `review.draft.md` exists, in the `systems/dossier.md` layout, with every anchored finding as its own thread and the verdict body in full |
| Replies (3) | The draft has a reply to comment 9001 marked resolve, and no duplicate thread for F2 |
| Slack delivery (1, 3) | Attachments are exactly the HTML page and the draft file; no PNG upload, no PDF; one closing message under ~1,200 characters ending with how to approve |
| Draft as posted (1, 3) | The HTML outline's last content section renders the draft itself, not a summary |
| Chat delivery (2) | Findings and verdict in the message, an `image()` per view, the draft's path, no HTML page |
| Stops | No `/post-review`, no GitHub write, waits for the user |

## Baseline

2026-11-17, one worker (`worker`, medium) per arm and scenario, at `eaedd0b` against `main` `0182682`.

| # | `main` | This edit |
|---|---|---|
| 1 | Uploaded all 3 PNGs separately, then 4 Slack messages with findings and the verdict; kept `verdict.md` locally, not attached; no inline thread bodies. Fails Draft written, Slack delivery, Draft as posted | Wrote the draft (verdict, 7 asks, 9 threads); outlined an HTML page ending in *Draft as posted*; attached the page and draft; one 809-character closing message ending "Reply *post*, or say what to change". Passes every check |
| 2 | Chat message with findings and the verdict, 3 `image()` calls; no draft file and no inline thread bodies. Fails Draft written | Wrote the draft; chat message with findings and verdict, `image()` per view, the draft's path. Passes every check |
| 3 | Uploaded the PNG, then one long Slack message with the verdict inline; no thread reply or inline body drafted. Fails Draft written, Replies, Slack delivery, Draft as posted | Draft with verdict, the F5 thread, and a resolving reply to 9001, F2 linked not duplicated; HTML page and draft attached; closing message. Passes every check |

Both arms used `image()` in scenario 2 because the situation names it; the edit is not what produced that.

Friction from the edit arms: **design-doc**'s RFC rules (commission an animated figure, argue against rivals, `--print` a PDF) pulled against a review report. A first fix listed those three as exclusions; rerun on scenarios 1 and 3, both arms honored it but read it as a ban list to reconcile against design-doc rule by rule. The Slack bullet now states the goal instead (judge the review without leaving the thread; the page reports a review, so nothing new is built for it) and lets the agent set aside what serves an RFC. Two frictions predate this edit and were left alone: the gate does not say what to do when the head has already moved (every run disclosed it and required a follow-up before posting), and post-review's "group related findings" sits beside "every finding gets its own thread" (every run kept one thread per finding).
