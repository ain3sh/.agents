---
name: slack-cli
description: Reference for using slck (aliased as `slack`) to manage Slack channels, messages, users, and search from the terminal. Use when the user mentions Slack messaging, channel management, or workspace communication.
---

# Slack CLI (`slack`)

`slck` (aliased `slack`) drives the workspace from the terminal. Bot token (`xoxb-`) is stored via config — verify with `slack config show`. Search and DM-reads need a user token (`xoxp-`) via `slack config set-token` or `SLACK_USER_TOKEN`.

## Route by task

- **`ops/`** — operating Slack. [`ops/cli.md`](ops/cli.md) is the full command reference: reading threads, channel admin, search, files, auth, `not_in_channel` fixes, flag surface.
- **`comms/`** — writing to humans. Read [`comms/voice.md`](comms/voice.md) *before composing* any channel post, thread reply, or DM: the audience/communication mindset plus Slack mrkdwn rules, not a personality script. Future workflow docs (e.g. reply-to-thread) land here.

Doing both (the common case: read a thread, then reply)? Load both.

## Quick reference

```bash
slack msg thread C0123 THREAD_TS -o json           # Read a thread (parent + replies)
slack msg send C0123 "text" --thread THREAD_TS     # Reply (flag is --thread, NOT --thread-ts)
slack msg send C0123 "$(cat /tmp/msg.txt)" --thread TS  # Long bodies: draft in a file first
slack msg history C0123 --limit 50                 # Channel history
slack s messages "query" --in "#general"           # Search (user token)
slack whoami                                       # Current identity
```

Thread URLs: use the `thread_ts` query param (the parent), not the `p<ts>` path segment — details and edge cases in `ops/cli.md`.

## Gotchas that bite

- `--thread-ts` is not a flag; it's `--thread`. The mistake only surfaces as a failed send after you've drafted the whole message.
- `msg send <USER_ID>` resolves DMs by listing every channel → `ratelimited` for minutes, both token buckets. Resolve the D-id once via the API and post to it directly — see "DMs and file sharing" in `ops/cli.md`.
- `files.completeUploadExternal` **silently ignores `channel_ids`** — file uploads but nobody sees it; the legacy `channels` param is what shares. Details in `ops/cli.md`.
- Inline shell quoting of long messages breaks on backticks/quotes; draft in a file and pass `"$(cat file)"`.
- Slack mrkdwn ≠ Markdown: `*bold*` single-asterisk, `•` bullets, no headers/tables — see `comms/voice.md`.
- Reading requires channel membership even with `channels:history`; see "Resolve `not_in_channel`" in `ops/cli.md`.
