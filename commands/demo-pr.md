---
description: Film a tuistory before/after demo for a PR
argument-hint: <PR-number-or-URL>
---

Load skill: **pr-context**.

## 1. Understand the PR

Follow the **pr-context** skill to gather full PR context from `$ARGUMENTS`.

Extract **all claimed features, enhancements, and fixes** from both the PR description and the linked ticket.

## 2. Plan the Demo

Design action flows that **stress-test every claimed change**. The before vs after comparison must be robust and informative.

For each claim, define:
- **Scenario name**: Short label (e.g., `tooltip-hover`, `error-message`).
- **Setup**: Any prerequisite state or data.
- **Steps**: Exact sequence of interactions -- commands to run, text to type, keys to press, expected visible output.
- **What to look for**: The specific behavior that should differ between before and after.

Present the full plan and **wait for user approval** before filming.

## 3. Film "Before" (Base Branch)

```bash
git checkout <base-branch> && git pull origin <base-branch>
```

- Start any required services or dev servers.
- For each scenario, record using `tuistory-rec`:
  ```bash
  tuistory-rec "before-<scenario>" "<start-command>" /tmp/tuistory-recordings/before-<scenario>.cast
  ```
- Execute the planned steps via tuistory commands (`type`, `press`, `wait`).
- Close each recording cleanly.

## 4. Film "After" (PR Branch)

```bash
git checkout <pr-branch>
```

- Ensure the same services/servers are running.
- Repeat the **identical scenarios** with `after-` prefix:
  ```bash
  tuistory-rec "after-<scenario>" "<start-command>" /tmp/tuistory-recordings/after-<scenario>.cast
  ```
- Execute the same steps. The differences should be visible.

## 5. Post-Process

- Review all recordings for clarity and completeness.
- If the `agg` or `svg-term` tools are available, render `.cast` files to GIF/SVG for easy sharing.
- Summarize findings:
  - Which scenarios show clear improvement?
  - Any regressions or unexpected differences?
  - Any claims that could not be demonstrated?
- Report output file paths and the summary.
