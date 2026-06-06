# Conditional sections

Templates for the catalog's conditional rows (SKILL.md §3). Use only the ones whose trigger fired; each renders at its catalog position. `<details>`-wrapped sections sit at the body's bottom so it reads linearly.

## Inline to the Description

### Anti-goals — scope deliberately constrained

One-liner under Description; pre-empts drive-by "while you're here…" comments. Stack multiples as sub-bullets. If *every* PR has anti-goals, the scope was never honest.

```markdown
**Out of scope**: refactoring the legacy `auth/` module — tracked in TEAM-456.
```

### Scope map — large or multi-concern diffs

When a reviewer could ask "why are unrelated changes bundled?", append a scope map to the Description: one bullet per bucket (what it covers + why it must ship here), then an explicit Out-of-scope line. Bullets beat a table when each "why" is a sentence. Typical buckets: core change · plumbing it requires · deliberate behavior changes (cross-link the Reviewer Guide list) · tests/e2e · target-branch merge alignment ("no behavior of its own").

```markdown
### Scope map — what is bundled and why
- **<bucket>** — <files/areas>. <why the core change requires it.>
**Out of scope:** <excluded work + where it's tracked.>
```

## Between Risk & Impact and Verification

### Contract Delta — DB / API / type contract touched

Drop rows that don't apply; each states the change + its backward-compat consequence.

```markdown
## Contract Delta
**API**: <endpoint/method change; compat note>
**DB**: <table/column/index change; migration safety>
**Types/SDK**: <type/symbol change; consumer compat>
```

### Migration & Rollout — flag / migration / breaking change

```markdown
## Migration & Rollout
**Order**: deploy (dark) -> run `2026_05_18_add_redirected_to.sql` -> flag `cart.redirect_v2` 10%->100% staging -> verify -> 10->100% prod over 24h.
**Rollback**: flag flip suffices to 100%; migration is additive.
**Coordination**: frontend `pr-1234` merges first so the field is consumed before it's populated.
```

### Performance Evidence — perf-sensitive changes

Numbers without methodology are theatre. State workload, hardware, rerun command.

```markdown
## Performance Evidence
**Benchmark**: 10k `/checkout`, 100 concurrent, warm cart (~500 items).
**Before** (`main` @ abc1234): p50 42 / p95 81 / p99 134 ms.
**After** (this PR): p50 18 / p95 31 / p99 58 ms.
**Conditions**: c6a.2xlarge, Node 22.4. Rerun: `pnpm bench:checkout`.
```

### Telemetry & Observability — metric / log / trace changes

```markdown
## Telemetry & Observability
**New**: <metric + type (counter/histogram/gauge); what it measures>
**Changed**: <metric + tag; impact on dashboards/alerts that filter on it>
**Logs**: <field + level + when emitted>
**Alerts**: <existing-alert impact + new-alert candidate>
```

### Reverse Dependencies — >3 consumers of the changed surface

✓ = verified (reviewer can stop); ⚠ = owner to ping.

```markdown
## Reverse Dependencies
**Surface**: `@scope/sdk` `CheckoutClient.complete()` — added optional `onRedirect`.
**Consumers** (via `rg "CheckoutClient" -t ts`):
- ✓ `apps/web` — wired here
- ✓ `services/order-worker` — ignores callback (server context)
- ⚠ `apps/admin` — @bob, unverified; optional callback preserves compat by type
```

### Side Effects — acknowledged regression

Honest acknowledgment beats discovery six weeks later. No regression → omit; don't fabricate.

```markdown
## Side Effects
- Empty-cart users see a ~50ms flash before redirect (was an immediate 500). Acceptable per @alice (200ms threshold).
- `cart_events` grows ~1 row/checkout. Est. +0.5% table storage / 90d.
```

## After Verification

### Repro Recipe — new feature / fixed bug

Bar: a reviewer who's never touched the repo runs it as-is and sees the expected behavior. Use an indented (not fenced) command block so it nests cleanly inside the body.

```markdown
## Repro Recipe

    pnpm dev
    # /cart -> add 2 items -> checkout while logged out
    # Expect: 302 -> /login?return_to=%2Fcheckout

Or: `pnpm test apps/web/e2e/checkout-redirect.spec.ts`.
```

## Bottom of body (`<details>`)

### Implementation map — large multi-subsystem diff (~20+ files)

A reviewer-facing file tour — distinct from Implementation Notes, which records *decisions*. Group the diff into subsystems; per group, name the files and one line on what changed + why it's grouped there. Complements the Reviewer Guide's read-order (the critical path) by giving the *complete* inventory so any file is locatable. Lead with the live diffstat.

```markdown
<details><summary>Implementation map</summary>

Current diff: `52 files changed, +3418 / -1650`.
- **<subsystem>**: `path/a.ts`, `path/b.tsx` — <what changed + why grouped here>
- **<subsystem>**: `path/c.ts` — <…>

</details>
```

### Root Cause Analysis — bug fixes

```markdown
<details><summary>Root Cause Analysis</summary>

**Trace**: <repro, symptoms, investigation; cite Sentry IDs / log queries pulled>
**Root cause**: <first unintended side effect — not the downstream error; name the broken invariant>
**Fix path**: <why this addresses the cause not the symptom; the rejected symptom-level fix>
**Why this layer**: <if the fix isn't at the symptom's layer, justify; cite root-cause-analysis if it shaped the call>

</details>
```

### Implementation Notes — `.agents/specs/<spec>.notes.md` exists

The `/implement` hook scaffolds this on spec approval. Ingest, then thread entries back into the always-on sections so they're not siloed: `deviation` → Description, `tradeoff` → Risk & Impact, `surprise` → Verification (Behavior verified), `followup` → Verification (Not tested).

```bash
TICKET=$(linear context --output json 2>/dev/null | jq -r '.identifier // empty' | tr '[:upper:]' '[:lower:]')
NOTES=$(ls .agents/specs/*.notes.md 2>/dev/null | rg -i "$TICKET" | head -1); [ -n "$NOTES" ] && cat "$NOTES"
```

```markdown
<details><summary>Implementation Notes</summary>

Source: `.agents/specs/<basename>.notes.md`
**Deviations from spec**: <one per `Type: deviation`>
**Tradeoffs**: <one per `Type: tradeoff` — alternative rejected + reason>
**Discovered constraints**: <one per `Type: surprise`>
**Follow-ups not in this PR**: <one per `Type: followup` — link tickets>

</details>
```

## Lineage (renders with Related Issue, row 2)

### PR lineage — stacked / split chain

```markdown
**PR lineage**: Part 3 of 5. Prev #1234 · Next #1236. Epic FAC-100.
**Type**: stacked (merge in order) | split (atomic — any order)
```

---

Catalog row 15 (**Changes since last review**) is refresh-only — its template lives in `refresh.md` (Phase 2, the revision-log carve-out), not here.
