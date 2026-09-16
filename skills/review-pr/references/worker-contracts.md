# Worker contracts

Rules for every `Task` dispatched from any review mode. Load before the first dispatch.

## Complexity follows responsibility

- **Heavy — mandatory** for: final correctness or architectural judgment, root-cause tracing, hands-on acceptance and faithful repro (`acceptance.md`), concurrency/state-machine analysis, security analysis, executed adversarial probes, the architecture-gate worker, and adjudication of any candidate finding.
- **Medium — allowed** for bounded static evidence work: caller/consumer enumeration, contract tracing, schema and locale/key parity audits, prior-art and parallel-PR search, convention mapping, test-gap analysis, line-by-line read-only audits of a bounded file set.
- **Medium output is evidence, not a finding.** Nothing a medium worker reports is retained as a finding until you (heavy main reviewer) or a heavy paired worker validates it.
- Genuinely trivial checks (one-file typo PR) run inline — no worker.

Do not downgrade heavy responsibilities to save tokens; do not pay heavy rates for mechanical enumeration.

## Dispatch admission

Two dispatch classes:

- **Standing dispatches** — mandated by a mode file (first-pass architecture worker at the gate, acceptance worker on `continue`). Scope comes from the mode file; no ledger entry needed. The architecture worker's subagent type, fallback rule, and prompt are the bounded assignment in `architecture-gate.md` ("Architecture worker") with the parent-selected current-source slice as its bounded file/call-path scope — it receives that file and **structural-review**, never `first-pass.md` or the whole diff as scope; it returns evidence and a proposed ruling and never owns the gate. The acceptance worker's subagent type, per-scenario assignment, scenario-state vocabulary, return, and admission are owned by `acceptance.md`; its scope is the parent-defined scenarios on a parent-arranged target within a stated authorization envelope, never "test the PR"; whether a given interaction environment may be delegated at all is **droid-control**'s rule, applied there.
- **Investigation dispatches** — everything else. The owning ledger entry must exist first (see mode files): proposition, path, evidence so far, remaining uncertainty, impact, bounded files. No named unresolved proposition → no worker. Workers never receive "review this area broadly" or the whole diff as scope.

Every investigation-worker prompt includes: the ledger entry verbatim; established facts (reconciled gate report, root-cause model — so it doesn't redo the main pass); bounded file/call-path list; the output schema below; hygiene rules; and neutral confirm-or-kill framing — never directional ("try to disprove first") instructions. Standing workers have no proposition and do not use the schema below: the architecture worker's prompt and return are the "Architecture worker" assignment and "Gate report" owned by `architecture-gate.md`, plus the read-only hygiene rules below; the acceptance worker's are the scenario assignment and per-scenario return owned by `acceptance.md`, plus the target-ownership rules below.

## Output schema (every proposition worker)

Each investigated proposition returns **exactly one** outcome:

1. **Confirmed** — PR-introduced defect or structural defect, each with owning locus and severity in **voice** tiers. Defect: violated invariant, mechanism, concrete trigger/reachability, evidence (probe output or quoted source chain). Structural defect: the design property violated — wrong boundary, duplicated or bypassed owner, needlessly broad state or contract, avoidable mechanism, unjustified coupling — shown in quoted source (both loci and the diverging callers when duplication is alleged), plus a direction that preserves the change's verified constraints and genuine contribution. Settled by source alone; a design proposition that needs an invented runtime failure to stand is not confirmed.
2. **Verified safe / killed** — the exact guard, invariant, or probe result that settles it.
3. **Pre-existing / out of scope** — real behavior, not introduced or worsened by the PR (evidence of pre-existence required).
4. **Duplicate / subsumed** — names the owning finding or upstream locus.
5. **Unresolved** — the one exact decisive next probe, not a shrug.

Plus, always: **scenarios attempted that did not break** (with evidence), and **newly discovered risks** outside the assigned propositions (reported, not chased — the parent decides).

"Checked, safe (evidence)" is a fully successful result. Worker success is validated coverage, never finding count — do not manufacture marginal findings to appear useful.

## Verification-target ownership & probe hygiene (probing workers)

The **parent owns verification targets**: it coordinates a stable revision and environment (builds, shared GUI state, scratch profiles and state for hands-on drives, dependency setup) and prepares disposable isolated snapshots for before/after source+test comparisons, preserving the real harness. Workers never replace tracked source in the active checkout and never change source under another worker. Workers never create worktrees without authorization, and a shared dependency mirror is never isolation: it does not separate mutable dependencies or build artifacts, so when the comparison requires it the parent arranges genuinely isolated state. Snapshot preparation is parent work; probing is worker work.

- Probes are **new untracked files only** (e.g. `__probe__.test.ts`) in the owning harness; reuse existing fixture builders. Delete when done; `git status` must show only pre-existing dirty entries. A probe is never a durable tracked edit.
- Never modify tracked files, never commit, never touch `.factory/settings.json`, `AGENTS.md`, `context/`.
- Scoped runs only, through the attached runner — the parent supplies the actual scoped argv, including how the workspace binary resolves (a local `node_modules/.bin` does not exist in every workspace): `~/.agents/scripts/run-check probe --cwd <pkg> -- flock -w 600 /tmp/droid-tests.lock ./node_modules/.bin/vitest run --no-file-parallelism --coverage.enabled=false <probe path>`.
- No safe, faithful verification target available? Do not improvise one — report exactly what remains unverified.
- A probe is optional: when the source contract is decisive, say so and cite the chain instead of executing.
- Read-only auditors: no file writes, no tests, no commits — state this in their prompt.

## Reconciliation gate

After each investigation dispatch returns, and **before any further dispatch in that category**: compare modalities, kill false positives, separate pre-existing, cluster by owning invariant (**patch-coherence**), record verified-safe, and name any remaining question. No remaining question → category closed. Details in `overcoverage.md` §3–4.

## Cancellation — evidence-based, never budget-based

If a worker is making progress (output/tool calls visible), let it finish. Never `TaskStop` over resource usage or token budget — review quality outranks both.

A worker **may** be stopped when:

- another result conclusively settled its identical proposition;
- a new PR head invalidated its scope;
- reconciliation proved its investigation redundant;
- its underlying hypothesis was withdrawn;
- it is genuinely stalled or off-task.

Record why it became redundant. That record goes in the dossier's worker log.
