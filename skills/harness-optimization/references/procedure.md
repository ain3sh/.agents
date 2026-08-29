# Harness Optimization Procedure

## 1. Freeze and collect

Capture before retrying:

- full transcript around the incident, including reasoning summaries when
  available
- exact tool input, tool options, and complete tool response
- every PreToolUse/PostToolUse decision, rewrite, timeout, and injected message
- the skill and instruction text loaded at that moment
- executor mode: interactive, headless/exec, background, detached task
- process tree, PIDs/process groups, exit status, and cancellation source
- complete output log plus what the model/operator actually saw live
- runtime registration and behavior config, not only committed source
- cache/sentinel state and the artifacts it claims are complete

If any referenced artifact is unavailable, state the gap. Do not promote a
theory to root cause.

## 2. State the invariant

Use one sentence that spans the control plane:

> Given the loaded policy, one owner starts the operation, exposes truthful
> progress, persists complete evidence, terminates all owned work on
> cancellation, and reports the real final state.

Narrow it for the incident without dropping ownership, observation, or
termination.

## 3. Walk the broken flow

Write explicit state at every transition:

| Step | Actor | Inputs/beliefs | Action | Owned state | Observable output |
|---|---|---|---|---|---|
| 1 | instruction/skill | loaded rules and examples | constrains or suggests | policy grammar | prose |
| 2 | model | policy + current evidence | chooses tool call | plan | tool input |
| 3 | hook | tool input + config + mode | allow/deny/rewrite | enforcement grammar | decision/message |
| 4 | executor | accepted input + timeout | starts/waits/cancels | parent process | tool response |
| 5 | child | argv/env/cwd/signals | runs/exits | child process group | stdout/stderr/status |
| 6 | output surface | stream/log limits | displays/persists | evidence | live view/log |
| 7 | model/operator | visible evidence | retries/cancels/diagnoses | recovery loop | next action |

Stop at the first transition where the invariant breaks. Later errors are
symptoms.

## 4. Classify the root

- **Policy-induced behavior**: the agent followed an example or rule that
  encoded the bad pattern.
- **Enforcement gap**: policy forbade the behavior, but the hook accepted it
  or excluded the relevant mode.
- **Runtime drift**: source changed, but active registration, config, cache, or
  generated wiring still selected the old mechanism.
- **Executor mismatch**: cancellation, updated input, timeout, streaming, or
  exit semantics differed from the assumed contract.
- **Observability distortion**: filtering, redirection, truncation, or
  detached execution changed what the model/operator could truthfully infer.
- **Split ownership**: setup, process lifetime, output, logs, cleanup, or
  status belonged to competing mechanisms.
- **Recovery-loop amplification**: the first failure hid evidence or taught a
  retry that created more failure.

Name the first locally rational wrong choice: what did the model do that made
sense under the control plane it actually saw?

## 5. Choose the fix by hierarchy

Apply the first sufficient move:

1. **Delete the bad affordance.** Remove examples and mechanisms that normalize
   the failure.
2. **Create one lifecycle owner.** Prefer a typed tool or argv protocol over
   shell composition.
3. **Constrain the accepted grammar.** Accept only the required shape; do not
   translate arbitrary old shapes.
4. **Enforce at entry.** Block before side effects; return the grammar, not a
   guessed reconstruction.
5. **Align prose with enforcement.** Every executable recipe uses the same
   primitive.
6. **Delete competitors.** Remove old hooks, post-hoc reminders, polling
   loops, fallback capture paths, and stale runtime registrations.

If the patch adds more exception branches than states it removes, redesign it.

## 6. Verify the lifecycle matrix

| Path | Proof required |
|---|---|
| Canonical success | truthful unfiltered live progress, complete persisted evidence, exit 0 |
| Canonical failure | complete evidence and exact nonzero status |
| Quiet/long run | attached wait without polling or synthetic sleeps |
| Interactive denial | side effect never starts; message states one grammar |
| Headless/exec denial | documented behavior matches real fail/pass semantics |
| User cancellation | whole process group terminates; result is interrupted |
| Ignored graceful signal | bounded escalation kills and reaps descendants |
| Concurrency | shared caches/logs/locks preserve their bound and completeness |
| Registration | runtime wiring invokes the new owner and no stale owner |
| Adversarial quoting | quoted operator text is data, not shell control |
| Detection limit | uncertain forms fail open or are explicitly out of scope |

Run the real registered lifecycle event for hook behavior. Unit tests prove
classification; they do not prove registration, mode semantics, or process
ownership.

## 7. Stop conditions

The optimization is complete only when:

- the incident replay reaches the intended state without retries
- the bad path is unrepresentable or rejected before side effects
- one primitive owns the full lifecycle
- policy, examples, guard, runner, and runtime registration speak one grammar
- cancellation and concurrency cannot leave hidden work or unbounded state
- remaining blind spots are explicit cooperation-guard limits, not covert
  fallback behavior

## 8. Report

Include:

- expected harness behavior and invariant
- evidence packet
- broken control-plane trace
- first locally rational wrong choice
- root classification and owning layer
- competing owners or grammars
- canonical replacement primitive
- mechanisms deleted
- verification matrix results
- residual detection limits, stated as limits rather than hidden fallbacks
