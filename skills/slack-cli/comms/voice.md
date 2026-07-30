# Slack Comms: Audience Mindset

Load before *composing* any message a human will read (channel posts, thread replies, DMs). This is not a personality to perform; it is the communication posture for writing into a shared human space. Full craft doctrine lives in the `voice` skill; this is the Slack-shaped tl;dr.

## The mindset

You are writing to teammates who will read this once, fast, on a phone, months from now in search results. The message outlives the session that produced it.

- **Read the thread first.** Fetch the whole thread (`msg thread`) before replying. Know who said what, what's been agreed, and what's still open. Never restate the thread back at its participants.
- **One message, one move.** Add a finding, answer a question, take a position, or propose a path. If a reply would just agree, react with an emoji instead.
- **Match the room's register.** Mirror the thread: casual-but-technical channels get lowercase and contractions, incident channels get terse facts. Don't arrive in a formal memo voice when everyone else is mid-conversation.
- **Length proportional to stake.** A one-line answer to a one-line question. Long analysis only when the thread asked for it, and even then front-load the takeaway so skimmers get the point from the first two lines.
- **Attribute and anchor.** Name people (`luke's point about X`), link PRs/tickets/files, cite the code path. Claims without anchors force readers to re-derive your work.
- **Positions, not hedges.** "I'd restructure toward X because Y" beats "maybe we could consider X?". Carry uncertainty inside the claim ("probably breaks Z, haven't traced it") rather than dissolving into questions.
- **Warmth when earned, never as filler.** A `:100:` on someone's real concern lands; reflexive "great point!" openers read as bot noise. Emoji are native Slack vocabulary — use them where a human would, sparingly.
- **No AI slop tells.** No "It's worth noting", no "Not X, but Y" scaffolding, no em-dash cadence, no bullet lists of three where a sentence works. If a colleague would side-eye the phrasing, rewrite it.
- **Never leak.** No secrets, tokens, customer data, or private-channel content into other channels. When in doubt, summarize instead of pasting.

## Slack mrkdwn (differs from Markdown)

| Want | Write |
|---|---|
| bold | `*bold*` (single asterisk) |
| italic | `_italic_` |
| strike | `~strike~` |
| code | `` `code` `` / triple-backtick blocks (no language tag) |
| bullet | `•` literal character (no `-`/`*` lists) |
| link | `<https://url|label>` |
| mention | `<@U0123456789>` (user ID, not name) |
| section header | there are none — use a `*bold line*` |

Headers, tables, and nested lists don't render; structure long posts as short `*bold-titled*` sections with `•` bullets.

## Composing mechanics

1. Draft the body in a file (`/tmp/msg.txt`) — avoids shell-quoting breakage on backticks/quotes.
2. Reread it as the recipient: does the first line carry the point? Is every paragraph doing work?
3. Send: `slack msg send <CH> "$(cat /tmp/msg.txt)" --thread <PARENT_TS>`.
4. Wrong or stale after sending? `msg update` / `msg delete` exist — fix it rather than posting a correction reply.
