# Model proxy

This directory is the canonical home for the local CLIProxyAPI configuration and lifecycle scripts.

- `config.yaml` exposes `gpt-6.1-sol-fast` and `gpt-6-luna-fast` as client aliases. Both resolve to their unsuffixed upstream models and add `service_tier: priority`.
- Codex OAuth only honors Fast scheduling over its Responses WebSocket transport. Because Droid sends HTTP/SSE requests, the updater applies a narrow bridge that sends only translated priority streams upstream by WebSocket. Standard requests retain CLIProxyAPI's normal HTTP path.
- Factory's plain `gpt-6.1-sol` entry is intentionally standard speed. The explicit `custom:openai://gpt-6.1-sol-fast` entry is intended for the main model. Luna has only a Fast Factory entry.
- The v8.0.4 release does not include `gpt-6.1-sol`. `gpt61-sol.patch` supplies the Team/Plus/Pro routing entry for releases missing it and is skipped when the release already includes the model. Upstream registered the model in commit `c8a2bfe8`, and the remote catalogs now include both its registry entry and client template, so startup and periodic remote catalog refresh are enabled.
- `update-cliproxyapi` reapplies the WebSocket bridge, strips the forced Claude redact-thinking beta, runs focused tests, builds, installs atomically, and keeps at most one rotating binary rollback file.

Use `model-proxy update`, `model-proxy restart`, and `model-proxy status`; the shell alias points to the controller in this directory.
