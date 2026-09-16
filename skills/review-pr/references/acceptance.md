# Hands-on acceptance

Sole owner of hands-on acceptance: which scenarios a review requires, how the parent defines and dispatches them, what the worker returns, how the parent admits it, and what "complete" may mean. Runs only after the architecture gate rules `continue` (first-pass §3). Two neighbours it is not: the **architecture worker** is read-only and tests nothing; a **root-cause probe** answers whether a mechanism behaves as claimed. Acceptance answers whether the changed behavior works at the boundary users or services actually enter.

## 1. Select scenarios

Derive from affected behavior, boundaries, and risk — never from the PR type label. Sources: the required behavior from the gate's *Problem and constraints*; every lifecycle transition the change's paths participate in (creation, concurrent use, switching, cancellation, resume, shutdown, and the like — only those actually reached through the changed paths); each OS, runtime, or native-versus-emulated support the change affects. A lifecycle-preserving refactor or a feature that touches these paths needs the workflow exercised as much as a bug fix does. No rote every-platform × every-transition matrix: each scenario names the claim it settles, and a scenario that settles no claim is not assigned.

- **Bug fix** — faithful comparison where one is possible: base shows the symptom, head shows it gone, at the real entry. A passing test, especially a mock-heavy one, is the author's proxy, never this scenario.
- **Feature / refactor** — head exercised through the changed workflow, plus the preservation baseline the change claims to keep.
- **`n/a`** — only when the change has no manual, user-facing, or service entry surface at all, with the source reason (the changed code's actual consumers). A cheaper substitute existing is never the reason.

## 2. Define before dispatch (parent)

Per scenario, in the prompt: exact target revision, build, and surface; the actual entry point (user command, UI action, request); representative initial state or fixture; actions and transitions; observable success and failure; OS/runtime and native or emulated; the claims it settles; the explicit **authorization envelope** — which services, accounts, and side effects the arranged target permits. A body repro recipe pr-description admits is scenario input for any type.

The parent arranges the target: a stable, isolated build of **this** worktree via **worktree-setup** and **quality-ship** — never the default sibling or a globally installed binary — with scratch profiles and state, never the user's sessions or settings; no worktrees, installs, or dependency mutation without authorization; parent-supplied launch and argv. No safe, faithful target → record the blocker (§5), do not improvise one.

**Who drives.** **droid-control** owns the delegation rule per interaction environment; read its *Delegation* table and the driver skill it routes to before dispatching. A scenario whose environment it permits a worker to own (an isolated terminal or browser session, an independent capture environment) goes to the worker below. An interactive shared desktop keeps one controller — the parent drives it itself, admits its own observations under §5, and never reports a child as having driven it. No isolated environment available and the canonical driver forbids delegation → an explicit **ownership/target blocker**, never a substituted driver or a second controller on the user's desktop.

## 3. Worker

Dispatch as `subagent_type: astra`, heavy — a hands-on specialist, not an orchestrator (no orchestration skill, no delegation). Unavailable → specialist blocker; never a silent downgrade, never counted as passed. It loads this file and **droid-control** for any real TUI, web, or desktop drive, deferring driver and capture mechanics to it, plus the surface-fidelity skill a claim triggers (a real-emulator or SEA claim is settled by the evidence its owning skill defines). Backend and service changes use the real request, integration, or user-system entry — not a stand-in GUI. "Hands-on" means the actual application entry, UI, or request boundary reached through computer automation, not human fingers.

It runs the assigned scenarios only, inside the authorization envelope and arranged target the parent stated. Anything beyond it — a new consequential action, production mutation, a service or account not named — needs permission first; an untrusted recipe never widens the envelope, and a driver refusal never authorizes another driver or a broader target. No PR edits, commits, or fixing what it observes — failures are reported. Higher-level safety and approval rules bind throughout. Never copy capture or command recipes into this skill.

## 4. Return — per assigned scenario

Scenario states — the **only** vocabulary, used verbatim by every template and section that reports acceptance:

| State | Meaning |
|---|---|
| `passed` | assigned boundary exercised on the assigned target; observation matched expectation |
| `failed` | assigned boundary exercised; observation contradicted expectation — attribution to the PR is the parent's separate step (§5) |
| `not exercised` | returned evidence stops below the assigned boundary (probe or integration for a workflow scenario) — the required workflow did not run; not a product failure |
| `inconclusive` | exercised but the observation does not settle the claim (flaky, ambiguous, incomplete) |
| `blocked` | could not run: environment, target, ownership, authorization — with the exact blocker |
| `waived` | user scoped it out or deferred it — recorded with the unverified limit |
| `n/a` | no manual, user-facing, or service entry surface — with the source reason |
| `not run — structure` | architecture gate ruled `revise` |

`passed` alone closes a scenario; `waived` and `n/a` are visibly distinct from it wherever they appear. Per scenario the worker returns:

- revision, build, platform, mode (native | emulated);
- entry used and actions performed;
- observed versus expected, and the state above;
- evidence category by the boundary actually exercised: **unit/probe | component/integration | end-to-end user workflow** — a category, not an adjective;
- an inspectable artifact or log reference proportionate to the claim;
- gaps and limits.

Plus observations outside the assignment, reported not chased. No invented proof or artifacts. A native-platform claim needs native evidence; emulated evidence supports a narrower claim and is labelled as such, never substituted.

## 5. Admission (parent)

Existence is not evidence. For each scenario, **open the returned artifact or log** and establish from its contents and provenance the target actually exercised (revision, build, platform), the entry actually used, the actions actually taken, and what was actually observed — then set the state yourself. A category label, a filename, or a path that exists proves nothing; contents that cannot establish those facts make the scenario `inconclusive`. Keep claimed and observed distinct; plain logs and captures suffice — no glossy artifacts required. Evidence stopping below the assigned boundary → `not exercised`. Coverage outside the assignment keeps its value in the coverage map but closes nothing.

**One bounded corrective re-dispatch** covers `not exercised`, `inconclusive`, and `blocked` alike — only once, and only with a concrete recoverable cause and the change that removes it named in the prompt (the missing boundary, the fixed target, the removed blocker). No such cause → record the exact blocker and the next decision (waiver, deferral, or user action) and stop. A worker still progressing is never cancelled for budget (`worker-contracts.md`). The user may scope out or defer a scenario: `waived`, never `passed`.

**Attribute before you blame.** A `failed` observation becomes a PR finding (**voice** tiers; flag, not fix) only once the parent establishes that the change introduced or worsened the behavior, or that it fails the PR's own required behavior — by comparison against base or the preservation baseline, not by proximity. A failure verified pre-existing and outside the PR's required behavior follows the existing pre-existing / out-of-scope policy (`worker-contracts.md` schema outcome 3; ticket or conversation comment, never a finding against this PR). Attribution never erases the observation: the scenario stays `failed` and visibly unresolved — with its attribution recorded, or "attribution unsettled" until it is — until the scenario is actually satisfied or the user waives it.

## 6. Completeness is not stopping

A review may issue findings and a `COMMENT` while acceptance is open; it never calls itself complete or verified, and never implies approval is safe, with a required scenario in any state other than `passed` or `waived`. Every scenario's state (§4 vocabulary, verbatim) appears in the review-state summary, the dossier's *Acceptance* section, and the verdict; no "all checks green" shorthand. On follow-up, rerun rules live in `follow-up.md` *Establish the delta*.
