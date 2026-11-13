# Behavioral replay

Run after editing this skill, as **update-skill** step 6 describes, with the
old revision as the control. Grade the prose and the process log the runs
return, not the skill's wording.

## Scenarios

| # | Prompt | Expected output |
|---|---|---|
| 1 | Write a PR Description and Verification, a Slack thread reply, and a README section, each from terse notes that include a check that was not run, a search with a stated scope, and one unknown | Each piece leads with its point. Every limit and number in the notes survives. Limits name the actor ("I did not run the integration suite"). The README describes current behavior with no "now" or "no longer". |
| 2 | Finalize the fixture below as your own draft, with the notes that back it | None of the fixture's marked words remain. Each is replaced by what ran and what came back, and every bound in the notes is present. |
| 3 | Edit the fixture as a teammate's draft, with no notes and no access to the code | The verdict header, the closer, and the em dash are gone. Each claim stays at its author's strength ("byte-identical" is not softened to "unchanged"). The reply asks the author what ran for each unsupported claim. |

## Fixture

Marked words: load-bearing, quietly, never, nothing, root-caused, outright,
refuses, re-verified, inert, byte-identical, mutation-checked, green, "the
whole story", and the em dash.

```text
## The retry guard was never load-bearing

Root-caused the duplicate-charge reports. The idempotency guard in `chargeCustomer()` quietly no-ops when the key is missing — and the mobile client never sends one. Nothing else in the path dedupes.

**What changed**

- `chargeCustomer()` now refuses keyless requests outright (400).
- Mobile client key generation re-verified end to end.
- Legacy `dedupeWindow` config is inert and has been removed.

The fix is byte-identical for web traffic. Mutation-checked the new guard; the suite is green.

That's the whole story: the guard looked like protection and wasn't.
```

Notes for scenario 2 give each claim its evidence and its bound: the client
versions read and the ones not checked, the directories searched and the SDK
that was not, the requests replayed and the fields compared, the mutants
killed out of the total, and the platform that was not tested.

## Grading

| Check | Pass |
|---|---|
| Point first | The first sentence states the answer, decision, or finding. |
| Substance kept | Every number, scope, limit, and unknown in the notes appears in the output. |
| Nothing invented | No name, number, cause, or consequence that the notes or draft do not hold. |
| Claims kept | An edit without evidence leaves each claim at its author's strength. |
| Evidence asked | The reply to the author names each unsupported claim and asks what ran. |
| No list walk | The process log describes one reread with the craft tests and lookups by family, not a pass over anti-slop sentence by sentence. |

Baseline for scenario 3, four models with two runs each: the revision before
the four tests left 6.6 of the 14 marked words in the edit and asked about
2.75 of 6 unsupported claims; the first revision with them left 3.5 and asked
about 4.75. If an edit moves either number the wrong way, fix the skill text,
not the output.
