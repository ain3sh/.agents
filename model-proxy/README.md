# Model proxy

This directory is the canonical home for the local CLIProxyAPI configuration and lifecycle scripts.

- `config.yaml` exposes `gpt-5.6-sol-fast` and `gpt-5.6-luna-fast` as client aliases. Both resolve to their unsuffixed upstream models and add `service_tier: priority`.
- Codex OAuth only honors Fast scheduling over its Responses WebSocket transport. Because Droid sends HTTP/SSE requests, the updater applies a narrow bridge that sends only translated priority streams upstream by WebSocket. Standard requests retain CLIProxyAPI's normal HTTP path.
- Factory's plain `custom:openai://gpt-5-6-sol` entry is intentionally standard speed and is used by heavy and mission workers. The explicit `-fast` entry is intended for the main model. Luna has only a Fast Factory entry.
- `update-cliproxyapi` reapplies the WebSocket bridge, strips the forced Claude redact-thinking beta, runs focused tests, builds, installs atomically, and keeps at most one rotating binary rollback file.

Use `model-proxy update`, `model-proxy restart`, and `model-proxy status`; the shell alias points to the controller in this directory.
