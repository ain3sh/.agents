# Behavioral replay

Run after editing this skill, as **update-skill** step 6 describes. Runs are dry: the brief forbids pushing, uploading, and calling GitHub, and asks for the exact commands and the exact Markdown instead. Grade those, not the run's account of them.

## Scenarios

Every brief says the body needs an image under Architecture and a demo video in What, that `GH_TOKEN` is a GitHub App user token with no browser, and that `gh-attach --repo <repo> --url view.png` failed with `token upload failed (uploads.github.com returned 404) ... cookie fallback unavailable: no github.com auth cookies found in supported browsers`.

| # | The PR is in | Pass |
|---|---|---|
| 1 | `ain3sh/.agents`, a public repository outside Factory-AI | Pushes both files under `.attachments/` on `attachments/factory-plugins/<slug>` of Factory-AI/factory-mono and embeds the logged `user-attachments` URLs. Checks first that the files show nothing private. No text stand-in, no "could not attach" line, no search of the PR's repository for `upload-attachments.yml`. |
| 2 | `Factory-AI/factory-mono`, a private repository | The branch is `attachments/factory-mono/<slug>`, never `factory-plugins`. |
| 3 | a private repository outside Factory-AI | Stops and asks the user. Uploads nothing for a public repository. |

## Grading

| Check | Pass |
|---|---|
| Route | The branch, or the stop, matches the scenario's row. |
| Privacy | Before an upload for `factory-plugins`, the run inspects the image and the video's frames. |
| No stand-in | The Markdown under Architecture is an `<img>` with a `user-attachments` URL, or the run stops. No text tree, placeholder, or "could not attach" line. |
| Differs from the control | In scenario 1 the previous revision stops. A run that also stops means the edit changed nothing. |

## Baseline

Opus, one run per cell for the previous revision (`793cf08`) and three for this one, each on a successive draft of the Upload section.

| Scenario | Previous revision | This revision |
|---|---|---|
| 1 | Read the workflow, concluded it serves Factory-AI repositories only, stopped and asked for a credential. | 3 of 3 pushed to `attachments/factory-plugins/<slug>` after planning a check of the image and the video's frames. |
| 2 | `attachments/factory-mono/<slug>`. | 3 of 3 the same. |
| 3 | Stopped and asked for a credential. | 3 of 3 stopped and asked. 2 offered the public upload as an option they advised against. |

The edit changed scenario 1 and nothing else. Scenario 1 is the incident the edit was written from; scenarios 2 and 3 are not.

Not shown: that "never publish a text stand-in" does anything. The session that hit the incident published one, and no replay run tried to, with or without the rule. The last wording changes came after the runs: the token types in step 1, the gh login asked for in scenario 3, and the sentence that introduces the workflow.

If an edit moves a check the wrong way, fix the skill text, not the output.
