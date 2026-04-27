---
name: lolbin-audit
description: Audit projects, containers, sudoers/IaC, and shell-out call sites for dangerous Living-Off-the-Land binary exposure using GTFOBins data. Use when asked about GTFOBins, LOLBins, post-foothold blast radius, privilege escalation, SUID/capability risks, sudo allowlists, container hardening, or security auto-testing of Unix/Linux projects.
---

# LOLBin Audit

## Purpose

Use this skill to answer: **"If an attacker gets any local execution foothold, what abusable Unix binaries have we handed them?"**

This is a defensive blast-radius audit. It does **not** exploit systems, run GTFOBins payloads, or prove command injection. It maps project artifacts to known GTFOBins primitives so findings are concrete, reproducible, and easy to remediate.

## Threat model

Assume an attacker has one of:

- a low-privilege shell inside a container or VM,
- a vulnerable app path that can invoke a system command,
- access to a user that has sudo rules,
- influence over provisioning scripts or build artifacts.

Then audit for primitives that convert that foothold into:

- root or higher-integrity execution,
- shell escape,
- arbitrary file read/write,
- file transfer,
- library loading,
- container or host escape preconditions.

## Never do

- Do not execute GTFOBins exploit snippets.
- Do not add SUID bits, capabilities, sudoers rules, or reverse shells for testing.
- Do not scan hosts you do not own or lack explicit authorization to test.
- Do not treat "binary exists" as a finding by itself. Findings require an enabling primitive: SUID/SGID, file capability, sudo allowlist, provisioning action, or a shell-out path.

## Skill root

The skill is installed at the absolute path below; use it verbatim from any cwd. All copy-pasteable snippets in this file assume `$SKILL_DIR` is set.

```bash
SKILL_DIR=/home/ain3sh/.agents/skills/lolbin-audit
```

## Prerequisites

Required: a working `gtfobins-cli` install. The skill auto-discovers its bundled JSON data; you do not call `gtfo` directly.

```bash
command -v gtfo >/dev/null || uv tool install git+https://github.com/kasem545/gtfobins-cli
"$SKILL_DIR/scripts/gtfo-data-dir.sh"   # prints the discovered data directory; exits non-zero if missing
```

Override discovery if needed: `export GTFO_DATA_DIR=/path/to/gtfo/data`.

Optional but improves coverage:

- `getcap` (libcap2-bin): rootfs/Docker file-capability scanning.
- `docker`: required only when `image-audit.sh` is given an image *name* (not a directory).
- `shellcheck`: optional skill self-test (see Verification).

## Output schema

Every audit script emits the same row schema (in JSONL/TSV; text format pretty-prints the same fields). When triaging, decide whether a row is a finding by combining `surface` + `technique` against `references/categories.md`'s gating rules.

| Field | Meaning |
|---|---|
| `surface` | `image`, `sudoers`, `iac`, `shellout`, or `inventory` |
| `source` | file path, image name, or rootfs path |
| `line` | source line number (`""` when not applicable) |
| `binary` | binary name/path as it appeared in evidence |
| `gtfo_binary` | matching GTFOBins entry after alias normalization |
| `technique` | GTFOBins category (e.g. `sudo`, `suid`, `capabilities`, `shell`) |
| `severity` | `critical` / `high` / `medium` / `low` / `info` |
| `reason` | one-sentence justification |
| `evidence` | the matched line or metadata |
| `snippet` | minimal GTFOBins exploitation snippet (when small enough) |

## Severity rules (canonical)

This table is the single source of truth; `references/categories.md` defers to it.

| Severity | Condition |
|---|---|
| Critical | `NOPASSWD: ALL`; setuid-root GTFOBins binary; sudo NOPASSWD rule for a binary with `sudo` GTFOBins technique |
| High | file capability on a GTFOBins binary that has `capabilities`; provisioning that grants SUID/capability to a GTFOBins binary; sudo allowlist for a shell/file primitive |
| Medium | SGID or limited-SUID primitive; ambiguous IaC that appears to grant a primitive but needs owner/context confirmation; shell-out with string interpolation or `shell=True` to a GTFOBins binary |
| Low | shell-out call site using a GTFOBins binary without evidence of user-controlled input |
| Info | inventory rows from `bins-with.sh`, or manually triaged non-findings |

## Tooling

### Audit scripts (produce findings)

| Script | Target | Surface tag | Output severity range |
|---|---|---|---|
| `project-audit.sh <repo>` | repo path; runs sudoers + iac + shellout sweeps | `sudoers`, `iac`, `shellout` (combined) | low → critical |
| `image-audit.sh <image\|rootfs-dir>` | Docker image name **or** unpacked rootfs directory | `image` | medium → critical |
| `sudoers-audit.sh <file\|dir>` | sudoers file, sudoers.d, Ansible, cloud-init | `sudoers` | high → critical |
| `iac-suid-audit.sh <repo>` | Dockerfiles, shell, Ansible, Packer, Makefiles | `iac` | medium → high |
| `shellout-grep.sh <repo>` | common source files (Python, JS/TS, Go, Ruby, shell, Java, PHP, Perl, Rust, C/C++, C#, etc.) | `shellout` | low → medium (hunt leads) |

### Database queries (no findings, just lookups)

| Script | Purpose |
|---|---|
| `bins-with.sh <technique>` | List GTFOBins entries that have a given technique. Output is `info` rows, not findings. |
| `has-technique.sh <binary> <technique>` | Predicate for chaining. Exit 0 = match, 1 = no match. `--quiet` suppresses output, `--snippet` prints the snippet on match. |
| `explain-bin.sh <binary> [technique]` | Print snippets for use in finding reports. |
| `gtfo-data-dir.sh` | Print the discovered GTFOBins data directory. |

### Common flags

All audit scripts accept:

```bash
--format text|tsv|jsonl     # default: text
--fail-on info|low|medium|high|critical   # exit 1 if any finding is at or above this severity (CI gate)
```

Pick `jsonl` when chaining or feeding another Droid; pick `text` for human summaries; pick `tsv` for spreadsheets or `cut`/`awk`.

### CI gate example

Drop-in script for a CI step (use `--fail-on high` to fail the pipeline only on real privilege issues, not on `shellout` hunt leads):

```bash
#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR=/home/ain3sh/.agents/skills/lolbin-audit
"$SKILL_DIR/scripts/sudoers-audit.sh"  ./infra --format jsonl --fail-on high
"$SKILL_DIR/scripts/iac-suid-audit.sh" .       --format jsonl --fail-on high
"$SKILL_DIR/scripts/image-audit.sh"    "$IMAGE_TAG" --format jsonl --fail-on high
```

Exit code 1 means a gate-blocking finding was emitted on stdout. Use `--format text` if a human will read the CI log.

### Binary alias normalization

The audit resolves observed names to canonical GTFOBins entries before lookup. Don't be surprised when a finding shows `gtfo_binary: python` for an evidence path of `/usr/bin/python3.11`.

| Observed | Resolves to |
|---|---|
| `python`, `python2`, `python3`, `python3.11`, `py` | `python` |
| `pip`, `pip3`, `pip3.11` | `pip` |
| `node`, `nodejs` | `node` |
| `ruby`, `ruby3.0`, `rb` | `ruby` |
| `php`, `php8.1` | `php` |
| `perl`, `perl5.36` | `perl` |
| `awk`, `gawk` | `awk` |
| `sh` | `dash` (not always correct on systems where `/bin/sh` is bash; treat as best-effort) |
| `vi` | `vim` |

If a binary doesn't resolve, no finding is emitted; rerun `has-technique.sh` to confirm.

## Default workflow

1. **Identify target type** and pick the matching script:

| If user mentions / scope is | Run |
|---|---|
| "Docker image", a `Dockerfile`, container hardening | `image-audit.sh <image>` first, then `iac-suid-audit.sh <repo>` |
| `/etc/sudoers`, sudoers.d, Ansible `become`, cloud-init | `sudoers-audit.sh <path>` |
| Terraform, Packer, shell provisioning, Makefile | `iac-suid-audit.sh <repo>` |
| App source code shelling out to commands | `shellout-grep.sh <repo>` (treat output as hunt leads) |
| Whole repo, no specific surface stated | `project-audit.sh <repo>` |
| "What can attackers do with binary X?" | `explain-bin.sh <bin>` |
| "Which binaries enable Y?" | `bins-with.sh <technique>` |

2. **Run with `--format jsonl`** so you can parse results, then triage by severity.
3. **Filter to true findings**: a row is a finding only when the GTFOBins primitive matches an enabling condition (SUID/SGID, file cap, sudo allowlist, IaC mutation, or shell-out where input control is plausible). `shellout` rows are hunt leads by default.
4. **For each finding**, run `explain-bin.sh <bin> <technique>` and include the snippet as attacker context.
5. **Report** using `references/findings-template.md`; recommend least-privilege remediation and a regression command (use `--fail-on` for CI).

## Worked example

Auditing a small repo that contains a sudoers fragment, a Dockerfile, and a Python file:

```bash
"$SKILL_DIR/scripts/project-audit.sh" /path/to/repo --format jsonl
```

Sample output (one JSON object per line; trimmed):

```json
{"surface":"sudoers","source":"infra/sudoers","line":1,"binary":"/usr/bin/vim","gtfo_binary":"vim","technique":"sudo","severity":"critical","reason":"sudo allowlist references a GTFOBins sudo primitive","evidence":"deploy ALL=(ALL) NOPASSWD: /usr/bin/vim","snippet":"sudo vim -c ':!/bin/sh'"}
{"surface":"iac","source":"Dockerfile","line":4,"binary":"/usr/bin/python3","gtfo_binary":"python","technique":"capabilities","severity":"high","reason":"provisioning appears to grant capabilities primitive to GTFOBins binary","evidence":"RUN setcap cap_setuid+ep /usr/bin/python3","snippet":"./python -c 'import os; os.setuid(0); os.system(\"/bin/sh\")'"}
{"surface":"shellout","source":"app.py","line":12,"binary":"tar","gtfo_binary":"tar","technique":"shell","severity":"medium","reason":"source code shells out to a GTFOBins binary; verify input control and privileges","evidence":"subprocess.run([\"tar\", \"xf\", user_file])"}
```

Triage:

- The first two are real findings (sudoers allowlist, file capability assignment).
- The third is a hunt lead: `tar xf user_file` is dangerous *if* `user_file` is attacker-controlled; confirm before reporting.

## Per-surface guidance

Use the gating rules in `references/categories.md` to decide whether each row is a finding, a hunt lead, or a non-finding.

### Container or rootfs audit (`image-audit.sh`)

```bash
"$SKILL_DIR/scripts/image-audit.sh" my-image:latest --format jsonl
"$SKILL_DIR/scripts/image-audit.sh" ./rootfs --format text
```

Highest-precision check; requires an actual SUID/SGID bit or file capability on a GTFOBins binary. False positive rate is near zero — every emitted row is a real finding.

Caveats:

- **Docker image input** runs `docker run --rm --entrypoint sh <image> -c "..."`. Distroless and `FROM scratch` images **lack `sh`** and will fail. For those, export the rootfs with `docker save | tar -x` (or `skopeo copy` + `umoci unpack`) and pass the directory.
- **Rootfs directory input** falls back to the host's `getcap`. Capability scanning is skipped with a warning if `getcap` is unavailable.
- **macOS targets** have no setuid GTFOBins exposure and no `getcap`; image-audit is Linux-only.

### Sudoers audit (`sudoers-audit.sh`)

```bash
"$SKILL_DIR/scripts/sudoers-audit.sh" ./infra --format jsonl
```

Searches sudoers/sudoers.d, plus Ansible/cloud-init/Terraform user-data files for `NOPASSWD` rules and Ansible `become` allowlists. Always flag `NOPASSWD: ALL` as critical even when no GTFOBins binary is named.

### IaC SUID/capability audit (`iac-suid-audit.sh`)

```bash
"$SKILL_DIR/scripts/iac-suid-audit.sh" . --format text
```

Looks for `chmod 4xxx` / `chmod u+s`, `install -m 4xxx`, and `setcap` lines that name a GTFOBins binary. Strong findings when the line spells out an absolute path; lines with `$(which ...)` or variables are hunt leads.

### Shell-out audit (`shellout-grep.sh`)

```bash
"$SKILL_DIR/scripts/shellout-grep.sh" . --format jsonl
```

Hunt-lead generator, not proof of exploitability. For each row, verify:

1. Does user/external input reach the argv? (look for `f"..."`, `% ...`, `${...}`, `+ var`, `shell=True`)
2. Does the process run with elevated privileges (sudo wrapper, root container user, suid/cap on the parent)?
3. Could the binary be replaced by a library call or a tightly argument-validated wrapper?

If 1 + (2 or 3) is true, promote to a finding. Otherwise list as a triaged non-finding in the report's hunt-lead table.

## Reporting format

Use `references/findings-template.md` verbatim for the report skeleton. It encodes: per-finding fields (severity rationale, evidence, primitive, impact, fix, validation, regression check) and a hunt-lead/non-finding triage table.

## Remediation patterns

- Remove SUID/SGID bits unless absolutely required.
- Replace file capabilities with narrower service design; if unavoidable, document why and assert exact capabilities in CI.
- Replace `NOPASSWD` allowlists with purpose-built wrappers that validate arguments and use absolute paths.
- Avoid allowing interactive tools (`vim`, `less`, `find`, `tar`, `python`, `bash`, `docker`, `kubectl`) in sudoers.
- In containers, use distroless/minimal images, drop package managers and shells when possible, and run as non-root.
- Replace app shell-outs with language-native APIs; if unavoidable, pass argv arrays, avoid shell expansion, and allowlist exact commands/arguments.

## Verification

### Before finishing a user audit

1. At least one audit script ran against the actual target (not just `bins-with.sh`).
2. Every emitted row was triaged into one of: real finding, hunt lead, or non-finding (with a reason).
3. Each real finding has: severity rationale, GTFOBins snippet from `explain-bin.sh`, fix, regression command (with `--fail-on`).
4. If a Docker image was in scope and Docker is available, `image-audit.sh` was run against the image, or the report states why it was skipped (e.g. distroless without exported rootfs).
5. Output lives in the report at `references/findings-template.md`'s shape, not raw script dumps.

### After editing the skill itself

Run all of these from any cwd; they should all succeed silently and leave no `__pycache__` behind:

```bash
SKILL_DIR=/home/ain3sh/.agents/skills/lolbin-audit
python3 -c "import sys; p='$SKILL_DIR/scripts/lolbin_audit.py'; compile(open(p).read(), p, 'exec')"
bash -n "$SKILL_DIR"/scripts/*.sh
"$SKILL_DIR/scripts/gtfo-data-dir.sh" >/dev/null
"$SKILL_DIR/scripts/has-technique.sh" python sudo --quiet
"$SKILL_DIR/scripts/has-technique.sh" python3.11 sudo --quiet   # alias resolution check
"$SKILL_DIR/scripts/bins-with.sh" sudo --format tsv >/dev/null
"$SKILL_DIR/scripts/explain-bin.sh" tar sudo >/dev/null
command -v shellcheck >/dev/null && shellcheck "$SKILL_DIR"/scripts/*.sh
test ! -d "$SKILL_DIR/scripts/__pycache__"
```

Optional functional smoke test (creates a temp dir, runs `project-audit.sh`, deletes the temp):

```bash
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf '%s\n' 'deploy ALL=(ALL) NOPASSWD: /usr/bin/vim' > "$tmp/sudoers"
printf '%s\n' 'RUN setcap cap_setuid+ep /usr/bin/python3' > "$tmp/Dockerfile"
"$SKILL_DIR/scripts/project-audit.sh" "$tmp" --format jsonl --fail-on critical || echo "expected exit 1: $?"
```
