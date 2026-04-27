# LOLBin audit findings template

Fill this in after running the relevant audit scripts. Keep all severity assignments justified — never just write "high" without a rationale tied to `SKILL.md`'s severity table.

## Summary

- **Target:** `<repo path | image:tag | rootfs dir | sudoers file>`
- **Scope:** `<files / surfaces audited>`
- **Out of scope:** `<paths excluded, e.g. tests/, vendored deps>`
- **Scripts run:**
  - `project-audit.sh ./repo --format jsonl`
  - `image-audit.sh app:1.2.3 --format jsonl`
- **Environment notes:** `<docker available? getcap available? distroless?>`
- **Result counts:**
  - Critical: 0
  - High: 0
  - Medium: 0
  - Low: 0
  - Info: 0
- **Hunt leads triaged:** 0

## Audit metadata (reproducibility)

- **Audit timestamp (UTC):** `<YYYY-MM-DDThh:mm:ssZ>`
- **GTFOBins data dir:** `<output of scripts/gtfo-data-dir.sh>`
- **`gtfo` version:** `<output of: gtfo --version>`
- **Skill commit / mtime:** `<git rev-parse HEAD on the skill repo, or stat -c %y on SKILL.md>`

---

## Finding template

Copy this block once per finding. Delete unused fields rather than leaving placeholders.

### Finding F-NN: `<severity>` — `<gtfo_binary>` exposes `<technique>` via `<surface>`

- **Surface:** `image | sudoers | iac | shellout`
- **Source:** `<file or image>:<line>`
- **Observed binary:** `<as it appeared in evidence, e.g. /usr/bin/python3.11>`
- **GTFOBins entry:** `<resolved gtfo_binary, e.g. python>`

**Evidence**

```text
<exact line or metadata, copy/pasted from the audit output>
```

**GTFOBins primitive**

```text
<output of: scripts/explain-bin.sh <bin> <technique>, trimmed to the relevant snippet>
```

**Severity rationale**

This is `<severity>` because `<which row of the severity table applies and why>`. Cite the matching row from `SKILL.md` § Severity rules.

**Impact**

Assume an attacker with `<foothold: low-priv shell / web RCE / sudo as user X / image build influence>`. Using this primitive they can `<specific outcome: become root, read /etc/shadow, escape to host, ...>`. If the binary also exposes `<related impact-only category>`, the attacker can additionally `<...>`.

**Fix**

- `<smallest safe remediation, e.g. remove the NOPASSWD entry, use cap_net_bind_service instead of cap_setuid, switch shell-out to library API>`
- `<follow-up hardening>`

**Validation**

`<how you verified the finding manually, e.g. "ran has-technique.sh python sudo (exit 0)", "confirmed setuid bit with stat", "traced shell-out caller to user-controlled HTTP param">`.

**Regression check (CI gate)**

```bash
SKILL_DIR=/home/ain3sh/.agents/skills/lolbin-audit
"$SKILL_DIR/scripts/<script>.sh" <target> --format jsonl --fail-on <severity>
```

---

## Worked example (delete in real reports)

### Finding F-01: `critical` — `vim` exposes `sudo` via `sudoers`

- **Surface:** `sudoers`
- **Source:** `infra/sudoers.d/deploy:1`
- **Observed binary:** `/usr/bin/vim`
- **GTFOBins entry:** `vim`

**Evidence**

```text
deploy ALL=(ALL) NOPASSWD: /usr/bin/vim, /usr/bin/python3
```

**GTFOBins primitive**

```text
sudo vim -c ':!/bin/sh'
```

**Severity rationale**

Critical: matches "sudo NOPASSWD rule for a binary with `sudo` GTFOBins technique" in `SKILL.md` § Severity rules. The `deploy` user can become root with no password.

**Impact**

An attacker who compromises the `deploy` user (e.g. via a CI runner takeover, leaked SSH key, or supply-chain build script) can run `sudo vim -c ':!/bin/sh'` to obtain a root shell with no password prompt and no audit log of the actual command executed.

**Fix**

- Remove `vim` (and `python3`) from the NOPASSWD allowlist.
- If a deploy script truly needs root edits, replace with a narrowly-scoped wrapper that takes a fixed file path and validated content, owned by root and `chmod 0700`.

**Validation**

- `has-technique.sh vim sudo` exits 0.
- `getent passwd deploy` (run against a target image) confirms the user exists.
- Manually re-ran `sudoers-audit.sh infra/sudoers.d/deploy --format text` and got the same row.

**Regression check**

```bash
SKILL_DIR=/home/ain3sh/.agents/skills/lolbin-audit
"$SKILL_DIR/scripts/sudoers-audit.sh" infra/ --format jsonl --fail-on high
```

---

## Hunt leads / triaged non-findings

Document hunt leads (typically `shellout` rows or ambiguous IaC) and explicit non-findings here so the audit is reproducible. When a `TP` is escalated to a real finding, fill the `Promoted to` column so the cross-reference is explicit.

| Status | Surface | Source | Evidence | Reason | Promoted to |
|---|---|---|---|---|---|
| `FP` | shellout | `app/cli.py:42` | `subprocess.run(["python", "-c", LITERAL])` | argv fully literal, no input reaches it | — |
| `pending` | shellout | `worker/jobs.py:88` | `os.system(f"tar xf {path}")` | `path` traced to validated allowlist; revisit if validator weakens | — |
| `TP` | shellout | `api/users.py:201` | `os.system(f"vim {fname}")` | `fname` reaches from a request param; runs as web user but image has `setuid` `vim` | F-02 |
| `non-finding` | iac | `tests/fixtures/sudoers` | `NOPASSWD: ALL` | test fixture, never deployed | — |

Status legend: `FP` (false positive), `TP` (true positive — should already be a Finding above), `pending` (needs more investigation), `non-finding` (deliberate, e.g. test fixture).
