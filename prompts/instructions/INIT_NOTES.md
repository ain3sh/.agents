---

[Implementation Notes — running decisions log]

Scaffold a paired notes file alongside the approved spec to capture spec-time-unknown decisions as they emerge during implementation.

**Path**: `${filePath}` with `.md` → `.notes.md`. Skip if `${filePath}` is empty (save failed).

**Scaffold once** (if not already present):

```
# Implementation Notes — <basename>

Spec: <basename>.md
Approved: <ISO date>
User comment: <tool response `userComment`, or "none">

---
```

**Append per entry** (one block per decision, in the same turn it's made — not batched):

```
## <ISO timestamp> — <one-line title>
**Type**: decision | deviation | tradeoff | surprise | followup
**Context**: <2-3 lines>
**Resolution**: <what was done, why, what alternative was rejected>
```

Append when the spec didn't anticipate the decision, the implementation deviated from the planned file list or approach, a real tradeoff was chosen (alternative + reason), an unforeseen constraint bit, or followup work emerged.

---
