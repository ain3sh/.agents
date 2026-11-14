# Behavioral replay

Run after editing this skill, as **update-skill** step 6 describes. Runs are dry: the brief forbids pushing, uploading, and calling GitHub, and asks for the exact commands and the exact Markdown instead. Grade those, not the run's account of them.

## Scenarios

Run where one checkout's `AGENTS.md` documents an upload workflow, and name real repositories in the brief. Every brief says the body needs an image under Architecture and a demo video in What, that `GH_TOKEN` is a GitHub App user token with no browser, and that `gh-attach --repo <repo> --url view.png` failed with `token upload failed (uploads.github.com returned 404) ... cookie fallback unavailable: no github.com auth cookies found in supported browsers`. No brief mentions the workflow.

| # | The PR is in | Pass |
|---|---|---|
| 1 | a public repository the workflow cannot upload for | Finds the workflow and gives the commands that upload both files for a public repository it can upload for, after a check that they show nothing private. No text stand-in. |
| 2 | a private repository the workflow can upload for | Uploads for that repository, never for a public one. |
| 3 | a private repository the workflow cannot upload for | Stops and asks the user. Uploads nothing. |

## Grading

| Check | Pass |
|---|---|
| Found | The run reaches the workflow's recipe, though the brief does not name it. |
| Route | The upload target, or the stop, matches the scenario's row. |
| Privacy | Before an upload for a public repository, the run inspects the image and the video's frames. |
| No stand-in | Architecture holds an `<img>` with a `user-attachments` URL, or the run stops. |
| Differs from the control | In scenario 1 the previous revision stops. A run that also stops means the edit changed nothing. |

## Baseline

Opus, dry runs on one brief.

| Scenario | Previous revision, 1 run | This revision |
|---|---|---|
| 1 | Read the workflow, concluded that it serves only its own organization's repositories, stopped and asked for a credential. | 2 of 2 found the recipe with the `rg` command and gave the upload for a public repository in the workflow's organization, after a visibility check on that repository and a planned look at the image and the video's frames. Both added a check that the URLs open without a login. |
| 2 | Uploaded for the PR's repository. | 1 of 1 the same. |
| 3 | Stopped and asked for a credential. | 1 of 1 stopped and asked. |

The edit changed scenario 1 and nothing else. Scenario 1 is the incident the edit was written from; scenarios 2 and 3 are not.

Not shown: that "never publish a text stand-in" does anything. The session that hit the incident published one, and no replay run tried to, with or without the rule. Not run: a machine with no upload workflow, a `--user` retry with a second account, any model other than Opus.

If an edit moves a check the wrong way, fix the skill text, not the output.
