# GTFOBins categories for defensive auditing

This file is reference material for the `lolbin-audit` skill. The canonical severity table lives in `SKILL.md`; do not duplicate it here. Use this file to decide *whether* a row is a finding and *what evidence to look for*.

## Triage rule, in one line

A row is a finding only when **`gtfo_binary` has a primitive category** AND **the surface provides an enabling condition** for that primitive. Presence of the binary alone is never a finding.

## Categories that gate a finding

These categories, when present in the GTFOBins entry for the matched binary, can promote a row to a finding *if* the surface supplies the right evidence.

| Category | Enabling condition (what makes it a finding) | Evidence pattern to look for |
|---|---|---|
| `sudo` | sudoers/Ansible-become/cloud-init grants this binary via NOPASSWD or a fixed allowlist | `NOPASSWD:.*<bin>`, Ansible `become_method: sudo` + `commands:` allowlist |
| `suid` | the binary file has the setuid bit (mode `4xxx`) | `find -perm -4000`, `chmod 4755`, `chmod u+s`, `install -m 4755` |
| `limited-suid` | as above, but only some functions of the binary work under suid (e.g. setuid-root but argv-restricted) | same patterns; treat as one severity tier lower than `suid` unless the binary's GTFOBins entry confirms the restricted form still yields shell |
| `capabilities` | the binary file has any privilege-conferring file capability | `setcap` lines, `getcap` output containing `cap_setuid`, `cap_dac_read_search`, `cap_chown`, `cap_sys_admin`, etc. with `+ep` |
| `library-load` | sudoers/service config preserves `LD_PRELOAD` / `LD_LIBRARY_PATH`, or runs the binary with attacker-writable plugin/module dirs | `Defaults env_keep += "LD_*"`, `Defaults !env_reset`, systemd unit with `Environment=LD_PRELOAD=...`, plugin dirs writable by app user |
| `shell` | sudoers allows it, or a shell-out reaches it with attacker-controlled argv | sudoers rule + this category; or `shell=True` / f-string / `${var}` interpolation in source |
| `command` | same as `shell` but for arbitrary single-command execution rather than interactive shell | same patterns |

## Categories that describe *impact only*

These categories, alone, are never sufficient for a finding. They describe what an attacker does *after* one of the gating categories above is triggered. Cite them in the impact paragraph of a finding, never as the trigger.

- `reverse-shell`, `non-interactive-reverse-shell`
- `bind-shell`, `non-interactive-bind-shell`
- `file-upload`, `file-download`
- `file-write`, `file-read`

Example: a row like "`sudo NOPASSWD: /usr/bin/tar`" is a finding because `tar` has `sudo`; the *impact* is "arbitrary file read/write as root" because `tar` also has `file-read` and `file-write`. Cite both in the report.

## Distinguishing `suid` from `limited-suid`

- `suid`: the GTFOBins entry confirms a working shell-spawning or arbitrary-write primitive when the binary is setuid-root.
- `limited-suid`: the binary needs special invocation (e.g. `bash -p` to keep effective UID, or environment tweaks) and may only yield a partial primitive.

When in doubt, flag `limited-suid` one tier lower than `suid`. If `has-technique.sh <bin> suid` exits 0, prefer that over `limited-suid` for severity reasoning.

## `library-load` — concrete patterns to flag

This category is easy to miss because the enabling evidence is rarely on the same line as the binary. The audit scripts do not detect these directly; treat them as a manual checklist when reviewing sudoers, systemd, and plugin systems.

Flag any of:

- `Defaults env_keep += "LD_PRELOAD"` / `LD_LIBRARY_PATH` / `LD_AUDIT` in sudoers.
- `Defaults !env_reset` in sudoers (allows env vars through by default).
- `Defaults secure_path` containing a directory writable by a non-root user.
- `Defaults !env_check` (skips the env_check filter that normally drops `LD_*`).
- Systemd unit, supervisor config, or shell wrapper that exports `LD_PRELOAD=` / `LD_LIBRARY_PATH=` before invoking a sudoers/suid binary.
- Plugin or module directory referenced by the binary that is writable by a less-privileged user (e.g. `/usr/lib/python3/dist-packages/<pkg>` with a non-root group write, or a Polkit/PAM/NSS module path on a writable mount).

Pair with the matched binary's `library-load` snippet from `explain-bin.sh` for impact.

## Noise control — when to demote to non-finding

Almost every Unix system ships these binaries; their *presence* is not a finding. They become findings only when the surface evidence above is also present.

- shells: `bash`, `dash`, `zsh`, `busybox`, `ash`, `ksh`
- interpreters: `python` (any minor), `perl`, `ruby`, `node`/`nodejs`, `php`, `lua`
- archives & file tools: `tar`, `cpio`, `find`, `xargs`, `awk`/`gawk`, `sed`, `cp`, `mv`, `dd`
- network & download: `curl`, `wget`, `nc`, `socat`, `ssh`, `scp`, `rsync`
- orchestration: `docker`, `podman`, `kubectl`, `helm`, `ansible`, `ansible-playbook`
- editors & pagers: `vi`/`vim`/`nvim`, `nano`, `less`, `more`, `ed`, `man`

If `shellout-grep.sh` reports one of these without a privilege escalation surface (no sudo wrapper, container runs as non-root, no setuid/setcap on the parent process), classify as a triaged non-finding in the hunt-lead table.

## Common false-positive patterns

| Pattern | Why it's not a finding |
|---|---|
| `subprocess.run(["python", "-c", literal_string])` | argv is fully literal; no input control |
| `chmod 755` (no setuid bit) | `755` does not include `4xxx`; ignore |
| `RUN apt-get install -y python3` in Dockerfile | install is not the same as setuid/setcap |
| Sudoers entry whose RHS is a wrapper script with strict argv validation | the wrapper is the real allowlisted command; mark as info if you've verified the wrapper |
| Test files / fixtures that contain bait (`tests/fixtures/sudoers`) | scope the audit away from test directories or annotate as test artifact |
