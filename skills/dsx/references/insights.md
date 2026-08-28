# Insights interpretation

Rules for interpreting `dsx insights` output.

## Insight signals

`dsx insights` emits findings with `kind`, `severity`, `session`, `detail`.
Severity is comparable across kinds and always in [0, 1]. Without `--kind`,
each kind is capped at 10 findings so no signal monopolizes the list; pass
`--kind <kind>` for the uncapped set of one signal.

| kind | fires when |
|---|---|
| `error_dense` | >=15% of tool calls failed (min 10 calls); severity = error rate |
| `retry_loops` | >=3 consecutive identical tool calls |
| `interrupted` | >=3 user cancellations; severity = cancels per user message |
| `abandoned` | unended session with <=2 user messages and at least one tool error |
| `compaction_churn` | >=4 context compactions |
| `expensive` | credits above max(p95, 3x median) of this user's credit-bearing sessions (min 20 samples); severity = log10(median ratio)/3 |
| `marathon` | >4h of assistant active time |

`expensive` is relative to the user's own distribution, never an absolute
threshold; details cite the median ratio and percentile (e.g. "44x your
median session (top 1%)"). Remember the fork-inflation rule from
`usage-semantics.md` when reading cost findings.

## Report-level rates

The `overall` block of `dsx insights --json` reports `toolErrorRate` (over
all tool calls), `interruptionRate` and `abandonRate` (over sessions), and
`medianCredits` (median over credit-bearing sessions only; zero-credit
sessions are typically empty shells and are excluded from the median).
