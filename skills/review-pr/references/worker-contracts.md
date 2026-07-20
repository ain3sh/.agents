# Worker contracts

Rules for every `Task` dispatched from any review mode. Load before the first dispatch.

## Complexity follows responsibility

- **Heavy — mandatory** for: final correctness or architectural judgment, root-cause tracing, faithful repro (**droid-control**), concurrency/state-machine analysis, security analysis, executed adversarial probes, structural-review sweeps, and adjudication of any candidate finding.
- **Medium — allowed** for bounded static evidence work: caller/consumer enumeration, contract tracing, schema and locale/key parity audits, prior-art and parallel-PR search, convention mapping, test-gap analysis, line-by-line read-only audits of a bounded file set.
- **Medium output is evidence, not a finding.** Nothing a medium worker reports is retained as a finding until you (heavy main reviewer) or a heavy paired worker validates it.
- Genuinely trivial checks (one-file typo PR) run inline — no worker.

Do not downgrade heavy responsibilities to save tokens; do not pay heavy rates for mechanical enumeration.

## Dispatch admission

Two dispatch classes:

- **Standing dispatches** — mandated by a mode file (first-pass faithful repro, structural sweep). Scope comes from the mode file; no ledger entry needed.
- **Investigation dispatches** — everything else. The owning ledger entry must exist first (see mode files): proposition, path, evidence so far, remaining uncertainty, impact, bounded files. No named unresolved proposition → no worker. Workers never receive "review this area broadly" or the whole diff as scope.

Every worker prompt includes: the ledger entry verbatim; established facts (so it doesn't redo the main pass); bounded file/call-path list; the output schema below; hygiene rules; and neutral confirm-or-kill framing — never directional ("try to disprove first") instructions.

## Output schema (every worker)

Each investigated proposition returns **exactly one** outcome:

1. **Confirmed** — PR-introduced defect: violated invariant, mechanism, concrete trigger/reachability, evidence (probe output or quoted source chain), owning locus, severity in **voice** tiers.
2. **Verified safe / killed** — the exact guard, invariant, or probe result that settles it.
3. **Pre-existing / out of scope** — real behavior, not introduced or worsened by the PR (evidence of pre-existence required).
4. **Duplicate / subsumed** — names the owning finding or upstream locus.
5. **Unresolved** — the one exact decisive next probe, not a shrug.

Plus, always: **scenarios attempted that did not break** (with evidence), and **newly discovered risks** outside the assigned propositions (reported, not chased — the parent decides).

"Checked, safe (evidence)" is a fully successful result. Worker success is validated coverage, never finding count — do not manufacture marginal findings to appear useful.

## Probe & worktree hygiene (probing workers)

- Probes are **new untracked files only** (e.g. `__probe__.test.ts`); reuse existing fixture builders. Delete when done; `git status` must show only pre-existing dirty entries.
- Never modify tracked files, never commit, never touch `.factory/settings.json`, `AGENTS.md`, `context/`.
- Scoped runs only: `cd <pkg> && flock -w 600 /tmp/droid-tests.lock ./node_modules/.bin/vitest run --no-file-parallelism --coverage.enabled=false <probe path>`.
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
