# slack-cli Ops Reference

Full command surface for `slck` (aliased `slack`). Auth model: bot token (`xoxb-`) stored via config; search and DM-reads need a user token (`xoxp-`) via `slack config set-token` or `SLACK_USER_TOKEN`.

## Channels

```bash
slack ch list                                      # All channels
slack ch list --exclude-archived                   # Active only
slack ch list --type public                        # Public only
slack ch get C0123456789                           # Details (channel metadata + member count)
slack ch create "name" --public                    # Create
slack ch archive C0123456789                       # Archive
slack ch unarchive C0123456789                     # Unarchive (user token only)
slack ch rename C0123456789 "new-name"             # Rename
slack ch invite C0123456789 -u U0123456789         # Invite user
slack ch kick C0123456789 -u U0123456789           # Remove user
slack ch set-topic C0123456789 "topic"             # Set topic
slack ch set-purpose C0123456789 "purpose"         # Set purpose
```

## Messages

```bash
slack msg send C0123456789 "text"                  # Send
slack msg send C0123456789 "reply" --thread TS     # Thread reply (flag is --thread, NOT --thread-ts)
slack msg send C0123456789 --file ./doc.pdf        # Upload file
slack msg send --channel "#general" "text"         # By channel name
slack msg send C0123 --blocks-file ./blocks.json   # Block Kit payload
slack msg update C0123 TS "new text"               # Edit
slack msg delete C0123 TS                          # Delete
slack msg react C0123 TS thumbsup                  # React
slack msg unreact C0123 TS thumbsup                # Remove reaction
slack msg history C0123456789 --limit 50           # Channel history
slack msg thread C0123 THREAD_TS                   # Thread replies (parent + all replies)
slack msg thread C0123 THREAD_TS --limit 200       # Higher page size
```

### Long / multi-line message bodies

Shell-quoting long messages inline is fragile (backticks, quotes, parens). Write the body to a file, then:

```bash
slack msg send C0123456789 "$(cat /tmp/message.txt)" --thread 1700000000.000000
```

## Users

```bash
slack u list                                       # All users
slack u list --include-bots                        # Include bots
slack u list --include-deactivated                 # Include deactivated
slack u get U0123456789                            # User details
slack u presence U0123456789                       # Presence status
```

## Search (requires user token)

```bash
slack s messages "query"                           # Messages
slack s messages "query" --in "#general"           # In channel
slack s messages "query" --from "@alice"           # From user
slack s messages "query" --after 2025-01-01        # Date filter
slack s messages "query" --has-link                # With links
slack s files "query" --type pdf                   # Files, by type
slack s all "query"                                # Both
```

Flags: `--count N` (max 100), `--page N`, `--sort score|timestamp`, `--sort-dir asc|desc`, `--scope all|public|private|dm|mpim`, `--highlight`.

## Emoji, Files, Identity

```bash
slack emoji list --include-aliases                 # Custom emoji
slack files download FILE_ID --output ./file.pdf   # Download file
slack whoami                                       # Current identity
slack ws info                                      # Workspace info
```

## Output, Env, Aliases

- Output: text (default), `-o json`, `-o table`.
- Env: `SLACK_API_TOKEN` (bot override), `SLACK_USER_TOKEN` (search/DMs), `SLCK_AS_USER=true` (default to user token), `NO_COLOR`.
- Aliases: `channels`→`ch`, `messages`→`msg`/`m`, `users`→`u`, `search`→`s`, `emoji`→`e`, `workspace`→`ws`/`team`.

## Config

```bash
slack config set-token [xoxb-...]                  # Interactive or direct
slack config show                                  # Status
slack config test                                  # Test auth
slack config delete-token [--type bot]             # Delete
```

## Patterns

### Read a thread from its URL

URL shape: `https://<ws>.slack.com/archives/<CHANNEL_ID>/p<REPLY_TS>?thread_ts=<PARENT_TS>`.
Use `thread_ts` (the parent). The `p<ts>` in the path is a reply id — using it misses the parent and any replies above it. If there's no `?thread_ts=` query param, the `p<ts>` *is* the parent: convert `p1700000000000000` → `1700000000.000000` (insert a dot before the last 6 digits).

```bash
URL='https://example.slack.com/archives/CXXXXXXXXXX/p1700000000000000?thread_ts=1700000000.000000'
CH=${URL#*archives/}; CH=${CH%%/*}
TS=${URL#*thread_ts=}; TS=${TS%%&*}
slack msg thread "$CH" "$TS" -o json
```

### Resolve `not_in_channel`

Reading messages requires channel membership; `channels:history` alone is not enough.

- **Public** — bot self-joins via `conversations.join` (requires `channels:join` scope).
- **Private** — a human must `/invite @slackcli`; bots cannot self-join.
- **DM / MPIM** — use a user token (`SLACK_USER_TOKEN` / `--as-user`).

Self-join guard for public channels (`conversations.join` is idempotent):

```bash
TOKEN=${SLACK_API_TOKEN:-$(cut -d= -f2 ~/.config/slack-chat-api/credentials)}
curl -sS -H "Authorization: Bearer $TOKEN" -d "channel=$CH" \
  https://slack.com/api/conversations.join >/dev/null
slack msg thread "$CH" "$TS"
```

If `conversations.join` returns `missing_scope`, add `channels:join` at
https://api.slack.com/apps/A0AN5RUFSNB/oauth and Reinstall to Workspace.

### DMs and file sharing (when slck hits `ratelimited`)

`slack msg send <USER_ID>` resolves DMs by listing every channel, which trips
`conversations.list` rate limits that persist for minutes across both token
buckets (symptom: `failed to list channels: slack API error: ratelimited`).
Skip the resolution: find the DM channel ID once via the API, then post to the
D-id directly. Token scopes force the split below; `conversations.open` fails
with `missing_scope` on both, so you can only reuse an existing DM.

| Token | Has | Lacks |
| --- | --- | --- |
| bot (`xoxb-`) | `chat:write`, `files:write` | `im:read`, `im:write` |
| user (`xoxp-`) | `im:read` (list DMs), search | `im:write`, `files:write` |

Identify the parties: `slack whoami -o json` → the human's user ID (the user
token's identity); `auth.test` with the bot token → `user_id` (the bot's user
ID, distinct from its `B…` bot ID).

**Resolve the DM channel ID** (user token lists; the `user` field in each IM is
the other party):

```bash
TOKEN=$(rg -o 'xoxp-[A-Za-z0-9-]+' ~/.config/slack-chat-api/credentials | head -1)
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://slack.com/api/conversations.list?types=im&limit=200" \
  -o /tmp/slack-ims.json
# Match the D-id whose "user" equals the target user ID:
rg -o '"id":"(D[A-Z0-9]+)"[^}]*"user":"<TARGET_USER_ID>"' /tmp/slack-ims.json
```

**Post the message** (bot token, direct to the D-id — bypasses slck's listing):

```bash
BTOKEN=$(rg -o 'xoxb-[A-Za-z0-9-]+' ~/.config/slack-chat-api/credentials | head -1)
curl -sS -H "Authorization: Bearer $BTOKEN" -d "channel=D0XXXXXXX" \
  --data-urlencode "text@/tmp/msg.txt" https://slack.com/api/chat.postMessage
```

**Upload + share a file** — Files API v2; legacy `files.upload` is dead
(`method_deprecated`):

1. `files.getUploadURLExternal` (GET, `filename` + `length`) → `upload_url`.
   The JSON escapes slashes (`\/`) — unescape (`sed 's/\\\//\//g'`) before
   use, or curl rejects the URL.
2. `curl -X POST -F "file=@./file.patch" "$UPLOAD_URL"` → `OK - <bytes>`.
3. `files.completeUploadExternal` to share. **Pass the channel via the legacy
   `channels` param — `channel_ids` is silently ignored**: `ok:true`, the file
   never appears, and `files.info` shows `"ims":[]`.
4. Verify with `files.info` → `"ims"` must contain the channel.

A completed-but-unshared file ID is spent — completion cannot be re-run and
the share cannot be retro-fitted. If the share silently failed, do a fresh
upload with the `channels` param.

**Message + file as one unit**: a file cannot be attached to an existing
message. Share the file, read its message ts from
`"shares":{"private":{"<CHANNEL_ID>":[{"ts":"…"` in the completion response,
post the prose as a threaded reply (`thread_ts=<ts>`), then delete the
standalone text message if one exists.

## Known Limitations

- Bot tokens (`xoxb-`) cannot unarchive channels — bot is removed on archive. Use a user token or the Slack UI.
- `channels invite` idempotency is limited to single-user invites.
- Reading messages/threads requires channel membership — see "Resolve `not_in_channel`".
