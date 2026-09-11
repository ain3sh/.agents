# Narrowing by bisection

Bisection is a search, not a theory. Each step runs one experiment whose result you cannot predict and discards the half of the region it rules out. If you can predict the result, it is not an experiment; take the next step of reading instead.

## The loop

1. **Write the boundary.** `good: <state where the invariant holds>`, `bad: <state where it breaks>`, `region: <everything between>`. If you cannot write `good`, you have no reference point: pick the layer or writers axis, where `good` is "the invariant holds at this probe."
2. **Pick the axis** whose split is cheapest to run and roughly halves the region. Change one axis at a time.
3. **Run the oracle once at the midpoint.** Record which side of the boundary moves.
4. **Repeat** until the region is one unit you can read whole, every candidate line on screen at once: one commit diff, one function, one writer, one field.
5. **Switch to read.** The narrowed unit is a location. Trace it to name the first unintended write, then prove that hypothesis against the repro (`SKILL.md` steps 6-10). A failed proof re-enters this loop at step 1 with the new boundary.

## The oracle

The oracle is the invariant from `SKILL.md` step 2 as a runnable check that returns pass/fail with no human judgment: a test, a script exit code, an assertion, a grep on a log line.

- Deterministic before you start. Run it three times at `good` and three at `bad`; any disagreement means fix the repro first.
- Checks the invariant, not the symptom. "Payload has field X at layer L" narrows; "the UI error is gone" is guess-and-check.
- Never encodes a candidate fix. Applying a fix and re-running is testing a theory, not narrowing.

## Axes

| Axis | `good` / `bad` | Split | Oracle |
|---|---|---|---|
| **History** | last known-good commit / HEAD | `git bisect start && git bisect bad HEAD && git bisect good <sha> && git bisect run <repro>` | repro exit code: 0 good, 125 skip (unbuildable), any other 1-127 bad |
| **Input** | passing input / failing input | halve the payload, fixture, or dataset; keep the half that still fails (delta debugging) | repro against the reduced input |
| **Layer** | invariant holds at probe / breaks at probe | assert the invariant at the midpoint of the candidate call path (log line, `assert`, breakpoint). Holds: cause is downstream. Breaks: cause is upstream. | the assertion |
| **Writers** | write absent / write present | disable or stub half the hidden-write suspects (hooks, subscribers, middleware, restore, jobs, startup code) | does the unexpected write still occur |
| **Environment** | env A / env B | diff env vars, flags, config, dependency versions; flip half of the differences | repro in the mutated env |
| **State** | fresh state / persisted state | run from a clean profile, seed, or empty store versus restored, hydrated, or cached state | repro from each |

Axes chain. History finds the commit; layer finds where inside that diff the invariant first breaks; writers finds which of several suspects in that layer performs the write.

## Pitfalls

| Symptom | Action |
|---|---|
| Results contradict (good after bad on the same axis) | Oracle is flaky or there are two bugs. Re-run the oracle three times at each boundary; if it holds, split the oracle into one check per invariant and bisect each. |
| Midpoint does not build or start | `git bisect skip`, or probe the adjacent point. Never mark an unbuildable point good or bad. |
| Instrumentation makes the bug disappear (races, timing) | The probe changed the schedule. Use a cheaper probe (timestamped log, not a breakpoint), or leave the layer axis for history or input. |
| Region stops shrinking on the current axis | Axis exhausted. Switch: history → layer → writers → state. |
| Narrowed to one unit, but it "looks fine" | The unit is where the invariant first breaks; reading it must explain why. If it cannot, the oracle checks the wrong invariant. Restate `SKILL.md` step 2 and re-narrow. |
