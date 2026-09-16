---
name: slack-cli
description: Reference for using slck (aliased as `slack`) to manage Slack channels, messages, users, and search from the terminal. Use when the user mentions Slack messaging, channel management, or workspace communication.
---

# Slack CLI (`slack`)

Use `slck` (aliased `slack`) for Slack operations; **voice** owns how messages
read, and this skill owns how they are formatted and delivered.

## Act

| Goal | Action |
|---|---|
| Read, search, or manage Slack | Load [ops/cli.md](ops/cli.md) for commands, auth, threads, channels, files, and recovery. |
| Compose or edit a post, reply, or DM | Load **voice** and its [external-replies reference](../voice/references/external-replies.md) before drafting, including after an investigation. |
| Send or update an authorized message | Use the [Slack formatting](ops/cli.md#slack-message-formatting) and command recipes in ops; verify the resulting message in its thread or history. |

## Detect

For Slack URLs, messages, DMs, searches, or channel operations, load ops. For
writing to people, also load voice; do not duplicate its communication rules
here or restrict them to Slack.

## Rules

1. Never send or edit before applying voice's audience and substance-preservation
   checks. Natural phrasing does not justify dropping material details.
2. Never confuse thread-reply syntax with API field names: CLI replies use
   `--thread`, not `--thread-ts`.
3. Never interpolate a long message into shell syntax. Draft it in a file and
   pass its contents as one quoted argument; see ops.

## Failure map

| Symptom | Action |
|---|---|
| Thread context is missing | Use the parent `thread_ts`; see [thread URLs](ops/cli.md#read-a-thread-from-its-url). |
| `not_in_channel` | Follow [membership recovery](ops/cli.md#resolve-not_in_channel). |
| DM sends rate-limit or an upload is invisible | Follow [DMs and file sharing](ops/cli.md#dms-and-file-sharing-when-slck-hits-ratelimited). |
| Markdown renders incorrectly | Use [Slack message formatting](ops/cli.md#slack-message-formatting). |
| Reply is stiff or too terse to evaluate | Re-run [voice's reply checks](../voice/references/external-replies.md#preserve-substance-before-sending). |

## References

Load on demand; do not reabsorb into this file:

- [ops/cli.md](ops/cli.md): Slack command reference, auth, formatting, delivery,
  and error recovery.
- [../voice/SKILL.md](../voice/SKILL.md): canonical craft and judgment routing
  for human-facing prose across apps.
