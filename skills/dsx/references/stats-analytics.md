# Stats analytics

Rules for interpreting `dsx stats` cross-tabs, metrics, and histograms.

## Cross-tabs and pro-rating

`stats --by day-model` and `stats --by day-project` split session-level
tokens/credits across active days using assistant-message counts, then group
the pro-rated rows by model or project. This is the same approximation as
`stats --by day`; it is useful for trend attribution, not exact per-message
billing.

Tool cross-tabs (`day-tool`, `project-tool`, `model-tool`) use actual tool-use
timestamps for day grouping and joined tool results for error rates.

## Metric selection

Chart-oriented stats views honor `--metric`. Common metrics:

- `credits`
- `inputTokens`
- `outputTokens`
- `totalTokens`
- `messages`
- `sessions`
- `toolCalls`
- `toolErrors`
- `errorRate`
- `tokensPerMessage`

Normalized metrics are for comparison, not accounting. Use them to spot an
unusual model/project/tool mix, then inspect the underlying sessions.

## Distribution views

`stats --by dist` reports percentiles plus histogram buckets for session-level
metrics. Heavy-tailed usage makes medians and p90/p95 more useful than means.
