# Model proxy

This directory is the canonical home for the local CLIProxyAPI configuration and lifecycle scripts.

- `config.yaml` exposes `gpt-6.1-sol-fast` and `gpt-6-luna-fast` as client aliases. Both resolve to their unsuffixed upstream models and add `service_tier: priority`. CLIProxyAPI sends the matching `X-Codex-Routing-Hint` header, so Codex OAuth honors Fast over plain HTTP/SSE.
- Factory's plain `gpt-6.1-sol` entry is intentionally standard speed. The explicit `custom:openai://gpt-6.1-sol-fast` entry is intended for the main model. Luna has only a Fast Factory entry.
- `update-cliproxyapi` strips the forced Claude redact-thinking beta, runs a focused regression test, builds outside tmpfs, installs atomically, and keeps one rollback binary.

Use `model-proxy update`, `model-proxy restart`, and `model-proxy status`; the shell alias points to the controller in this directory.
