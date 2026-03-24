---
name: slack
description: Reference for using slck (aliased as `slack`) to manage Slack channels, messages, users, and search from the terminal. Use when the user mentions Slack messaging, channel management, or workspace communication.
---

# Slack CLI (`slack`)

slck uses a stored bot token (`xoxb-`). Verify with `slack config show`.
Search requires a user token (`xoxp-`). Set via `slack config set-token` or `SLACK_USER_TOKEN` env var.

## Channels

```bash
slack ch list                                      # All channels
slack ch list --exclude-archived                   # Active only
slack ch list --type public                        # Public only
slack ch info C0123456789                          # Details
slack ch create "name" --public                    # Create
slack ch archive C0123456789                       # Archive
slack ch unarchive C0123456789                     # Unarchive (user token only)
slack ch rename C0123456789 "new-name"             # Rename
slack ch invite C0123456789 -u U0123456789         # Invite user
slack ch kick C0123456789 -u U0123456789           # Remove user
slack ch set-topic C0123456789 "topic"             # Set topic
slack ch set-purpose C0123456789 "purpose"         # Set purpose
slack ch history C0123456789                       # Message history
slack ch history C0123456789 --count 50            # With count
slack ch history C0123456789 --oldest TS           # Since timestamp
```

## Messages

```bash
slack msg send C0123456789 "text"                  # Send
slack msg send C0123456789 "reply" --thread-ts TS  # Thread reply
slack msg send C0123456789 --file ./doc.pdf        # Upload file
slack msg send --channel "#general" "text"         # By channel name
slack msg update C0123 TS "new text"               # Edit
slack msg delete C0123 TS                          # Delete
slack msg react C0123 TS thumbsup                  # React
slack msg unreact C0123 TS thumbsup                # Remove reaction
slack msg pin C0123 TS                             # Pin
slack msg unpin C0123 TS                           # Unpin
slack msg permalink C0123 TS                       # Get permalink
slack msg schedule C0123 "text" --post-at UNIX     # Schedule
slack msg unschedule SCHEDULED_ID                  # Cancel scheduled
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
slack s files "query"                              # Files
slack s files "query" --type pdf                   # By type
slack s all "query"                                # Both
```

### Search Flags

| Flag | Description |
|------|-------------|
| `--count N` | Results per page (max 100) |
| `--page N` | Page number |
| `--sort score\|timestamp` | Sort order |
| `--sort-dir asc\|desc` | Direction |
| `--scope all\|public\|private\|dm\|mpim` | Scope |
| `--highlight` | Highlight matches |

## Emoji, Files, Identity

```bash
slack emoji list                                   # Custom emoji
slack emoji list --include-aliases                 # With aliases
slack files download FILE_ID                       # Download file
slack files download FILE_ID --output ./file.pdf   # To path
slack whoami                                       # Current identity
slack ws info                                      # Workspace info
```

## Output Formats

```bash
slack ch list                                      # Text (default)
slack ch list -o json                              # JSON
slack ch list -o table                             # Table
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SLACK_API_TOKEN` | Bot token override |
| `SLACK_USER_TOKEN` | User token for search |
| `SLCK_AS_USER` | `true` to default to user token |
| `NO_COLOR` | Disable colored output |

## Aliases

| Command | Aliases |
|---------|---------|
| `channels` | `ch` |
| `messages` | `msg`, `m` |
| `users` | `u` |
| `search` | `s` |
| `emoji` | `e` |
| `workspace` | `ws`, `team` |

## Config Management

```bash
slack config set-token                             # Interactive
slack config set-token xoxb-...                    # Direct
slack config show                                  # Status
slack config test                                  # Test auth
slack config delete-token                          # Delete all
slack config delete-token --type bot               # Delete bot only
```

## Shell Completions

```bash
slack completion zsh > "${fpath[1]}/_slck"
slack completion bash > /etc/bash_completion.d/slck
slack completion fish > ~/.config/fish/completions/slck.fish
```

## Known Limitations

- Bot tokens (`xoxb-`) cannot unarchive channels (Slack API limitation -- bot is removed on archive).
- Workaround: use a user token or unarchive via Slack UI.
- `channels invite` idempotency is limited to single-user invites.
