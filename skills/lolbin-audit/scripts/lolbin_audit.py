#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".next",
    "coverage",
    "__pycache__",
    "target",
    ".terraform",
}
TEXT_EXTS = {
    ".bash",
    ".bats",
    ".c",
    ".cc",
    ".conf",
    ".cpp",
    ".cs",
    ".dockerfile",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".ksh",
    ".make",
    ".mk",
    ".php",
    ".pl",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".tf",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
    ".zsh",
}
SOURCE_EXTS = {
    ".bash",
    ".bats",
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".ksh",
    ".php",
    ".pl",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".ts",
    ".tsx",
    ".zsh",
}


def die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def valid_data_dir(path: Path) -> bool:
    return path.is_dir() and any(path.glob("*.json"))


def discover_data_dir() -> Path:
    env = os.environ.get("GTFO_DATA_DIR")
    if env and valid_data_dir(Path(env)):
        return Path(env)

    try:
        import gtfo  # type: ignore

        candidate = Path(gtfo.__file__).resolve().parent / "data"
        if valid_data_dir(candidate):
            return candidate
    except Exception:
        pass

    gtfo_exe = shutil.which("gtfo")
    if gtfo_exe:
        real = Path(gtfo_exe).resolve()
        try:
            first = real.read_text(errors="ignore").splitlines()[0]
            if first.startswith("#!"):
                py = first[2:].strip()
                proc = subprocess.run(
                    [
                        py,
                        "-c",
                        "import pathlib, gtfo; print(pathlib.Path(gtfo.__file__).resolve().parent / 'data')",
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                if proc.returncode == 0:
                    candidate = Path(proc.stdout.strip())
                    if valid_data_dir(candidate):
                        return candidate
        except Exception:
            pass

        venv = real.parent.parent
        for candidate in venv.glob("lib/python*/site-packages/gtfo/data"):
            if valid_data_dir(candidate):
                return candidate

    home = Path.home()
    for candidate in [
        *home.glob(".local/share/uv/tools/gtfobins-cli/lib/python*/site-packages/gtfo/data"),
        *home.glob(".local/pipx/venvs/gtfobins-cli/lib/python*/site-packages/gtfo/data"),
    ]:
        if valid_data_dir(candidate):
            return candidate

    die("could not locate GTFOBins data; set GTFO_DATA_DIR or install gtfobins-cli")


class GtfoDB:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._data: dict[str, dict[str, Any]] = {}
        for file in sorted(data_dir.glob("*.json")):
            try:
                self._data[file.stem] = json.loads(file.read_text())
            except Exception as exc:
                warn(f"skipping unreadable GTFOBins data file {file}: {exc}")

    @property
    def bins(self) -> set[str]:
        return set(self._data)

    def functions(self, gtfo_bin: str) -> dict[str, list[dict[str, str]]]:
        raw = self._data.get(gtfo_bin, {})
        funcs = raw.get("functions", {})
        return funcs if isinstance(funcs, dict) else {}

    def categories(self, gtfo_bin: str) -> list[str]:
        return sorted(self.functions(gtfo_bin))

    def has(self, binary: str, technique: str) -> bool:
        resolved = self.resolve(binary)
        return bool(resolved and technique in self.functions(resolved))

    def resolve(self, binary: str) -> str | None:
        base = clean_binary_name(binary)
        if not base:
            return None
        candidates = [base, base.lower()]

        alias_map = {
            "nodejs": "node",
            "sh": "dash",
            "rb": "ruby",
            "vi": "vim",
            "py": "python",
        }
        if base in alias_map:
            candidates.append(alias_map[base])

        regex_aliases = [
            (r"^python[0-9.]*$", "python"),
            (r"^pip[0-9.]*$", "pip"),
            (r"^ruby[0-9.]*$", "ruby"),
            (r"^php[0-9.]*$", "php"),
            (r"^perl[0-9.]*$", "perl"),
            (r"^node[0-9.]*$", "node"),
            (r"^g?awk$", "awk"),
        ]
        for pattern, alias in regex_aliases:
            if re.match(pattern, base):
                candidates.append(alias)

        for candidate in candidates:
            if candidate in self._data:
                return candidate
        return None

    def first_snippet(self, gtfo_bin: str, technique: str | None = None, max_lines: int = 6) -> str:
        funcs = self.functions(gtfo_bin)
        techniques = [technique] if technique else sorted(funcs)
        for tech in techniques:
            if not tech or tech not in funcs:
                continue
            for entry in funcs[tech]:
                code = (entry.get("code") or "").strip()
                if code:
                    lines = code.splitlines()
                    if len(lines) > max_lines:
                        lines = [*lines[:max_lines], "..."]
                    return "\n".join(lines)
        return ""

    def explain(self, binary: str, technique: str | None = None) -> str:
        gtfo_bin = self.resolve(binary)
        if not gtfo_bin:
            return f"No GTFOBins entry for {binary}"
        funcs = self.functions(gtfo_bin)
        techniques = [technique] if technique else sorted(funcs)
        chunks = [f"GTFOBins: {gtfo_bin}"]
        for tech in techniques:
            if not tech or tech not in funcs:
                continue
            chunks.append(f"\n--- {tech.upper()} ---")
            for idx, entry in enumerate(funcs[tech], start=1):
                desc = (entry.get("description") or "").strip()
                code = (entry.get("code") or "").rstrip()
                if desc:
                    chunks.append(desc)
                if code:
                    chunks.append(code)
                if idx >= 3:
                    remaining = len(funcs[tech]) - idx
                    if remaining:
                        chunks.append(f"... {remaining} more snippet(s) omitted")
                    break
        return "\n\n".join(chunks)


def clean_binary_name(value: str) -> str:
    value = value.strip().strip("\"'`")
    if not value or value in {"-", "--"}:
        return ""
    if "=" in value and not value.startswith("/") and value.split("=", 1)[0].isidentifier():
        return ""
    value = value.split()[0] if " " in value else value
    value = value.rstrip(",;:)]}")
    value = value.strip("\"'`")
    if value.startswith("./"):
        value = value[2:]
    return Path(value).name


def finding(
    *,
    surface: str,
    source: str,
    line: int | str = "",
    binary: str,
    gtfo_binary: str,
    technique: str,
    severity: str,
    reason: str,
    evidence: str,
    db: GtfoDB,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "source": source,
        "line": line,
        "binary": binary,
        "gtfo_binary": gtfo_binary,
        "technique": technique,
        "severity": severity,
        "reason": reason,
        "evidence": evidence.strip(),
        "snippet": db.first_snippet(gtfo_binary, technique),
    }


def output_findings(findings: list[dict[str, Any]], fmt: str) -> None:
    if fmt == "jsonl":
        for item in findings:
            print(json.dumps(item, sort_keys=True))
        return

    if fmt == "tsv":
        fields = [
            "surface",
            "source",
            "line",
            "binary",
            "gtfo_binary",
            "technique",
            "severity",
            "reason",
            "evidence",
        ]
        print("\t".join(fields))
        for item in findings:
            print("\t".join(str(item.get(field, "")).replace("\t", " ") for field in fields))
        return

    if not findings:
        print("No LOLBin findings.")
        return

    for idx, item in enumerate(findings, start=1):
        location = item["source"]
        if item.get("line"):
            location = f"{location}:{item['line']}"
        print(f"[{idx}] {item['severity'].upper()} {item['surface']} {item['gtfo_binary']} / {item['technique']}")
        print(f"    source:   {location}")
        print(f"    binary:   {item['binary']}")
        print(f"    reason:   {item['reason']}")
        print(f"    evidence: {item['evidence']}")
        snippet = item.get("snippet")
        if snippet:
            print("    snippet:")
            for line in str(snippet).splitlines():
                print(f"      {line}")
        print()


def fail_if_needed(findings: list[dict[str, Any]], fail_on: str | None) -> None:
    if not fail_on:
        return
    threshold = SEVERITY_ORDER[fail_on]
    if any(SEVERITY_ORDER.get(str(item.get("severity")), 0) >= threshold for item in findings):
        raise SystemExit(1)


def candidate_files(root: Path, *, source_only: bool = False, security_configs_only: bool = False) -> Iterable[Path]:
    if root.is_file():
        yield root
        return

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            lower = name.lower()
            suffix = path.suffix.lower()
            if path.stat().st_size > 2_000_000:
                continue
            if source_only and suffix not in SOURCE_EXTS and lower not in {"makefile", "dockerfile"}:
                continue
            if security_configs_only:
                interesting = (
                    "sudo" in lower
                    or "dockerfile" == lower
                    or "cloud" in lower
                    or "user-data" in lower
                    or suffix in {".sh", ".bash", ".zsh", ".yaml", ".yml", ".tf", ".tpl", ".conf"}
                    or lower in {"makefile", "packerfile"}
                )
                if not interesting:
                    continue
            elif suffix not in TEXT_EXTS and lower not in {"makefile", "dockerfile", "sudoers"}:
                continue
            yield path


def iter_text_lines(path: Path, **kwargs: Any) -> Iterable[tuple[Path, int, str]]:
    for file in candidate_files(path, **kwargs):
        try:
            raw = file.read_bytes()
        except OSError:
            continue
        if b"\0" in raw[:8192]:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            yield file, line_no, line


def extract_command_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    for match in re.finditer(r"(?:^|[\s:=,\[\('\"])(/[A-Za-z0-9_./+@%-]+)", text):
        candidates.append(match.group(1))
    for match in re.finditer(r"\bwhich\s+([A-Za-z0-9_.+@%-]+)", text):
        candidates.append(match.group(1))

    scrubbed = re.sub(r"['\"\[\]{}()]", " ", text)
    for segment in scrubbed.split(","):
        try:
            parts = shlex.split(segment)
        except ValueError:
            parts = segment.split()
        for token in parts:
            token = token.strip()
            if not token:
                continue
            upper = token.upper()
            if upper in {"ALL", "NOPASSWD", "PASSWD", "NOEXEC", "SETENV", "RUNAS"}:
                candidates.append(upper)
                continue
            if token.startswith("-") or token.startswith("cap_") or re.fullmatch(r"[0-7]{3,4}", token):
                continue
            if "/" in token or re.fullmatch(r"[A-Za-z][A-Za-z0-9_.+@%-]{1,40}", token):
                candidates.append(token)
            break

    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        normalized = candidate.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def cmd_data_dir(args: argparse.Namespace, db: GtfoDB) -> None:
    print(db.data_dir)


def cmd_bins_with(args: argparse.Namespace, db: GtfoDB) -> None:
    technique = args.technique
    rows = [
        {
            "surface": "inventory",
            "source": str(db.data_dir),
            "line": "",
            "binary": binary,
            "gtfo_binary": binary,
            "technique": technique,
            "severity": "info",
            "reason": f"GTFOBins has {technique} technique",
            "evidence": ",".join(db.categories(binary)),
            "snippet": db.first_snippet(binary, technique),
        }
        for binary in sorted(db.bins)
        if technique in db.functions(binary)
    ]
    output_findings(rows, args.format)


def cmd_has_technique(args: argparse.Namespace, db: GtfoDB) -> None:
    gtfo_bin = db.resolve(args.binary)
    if not gtfo_bin or args.technique not in db.functions(gtfo_bin):
        raise SystemExit(1)
    if args.quiet:
        return
    print(f"{args.binary}\t{gtfo_bin}\t{args.technique}")
    if args.snippet:
        snippet = db.first_snippet(gtfo_bin, args.technique)
        if snippet:
            print(snippet)


def cmd_explain_bin(args: argparse.Namespace, db: GtfoDB) -> None:
    print(db.explain(args.binary, args.technique))


def scan_rootfs_dir(root: Path, db: GtfoDB) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        if Path(dirpath) == Path("/"):
            dirnames[:] = [name for name in dirnames if name not in {"proc", "sys", "dev", "run"}]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = path.lstat()
            except OSError:
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            mode = st.st_mode
            setuid = bool(mode & stat.S_ISUID)
            setgid = bool(mode & stat.S_ISGID)
            if not (setuid or setgid):
                continue
            gtfo_bin = db.resolve(name)
            if not gtfo_bin:
                continue
            technique = ""
            if setuid and "suid" in db.functions(gtfo_bin):
                technique = "suid"
            elif (setuid or setgid) and "limited-suid" in db.functions(gtfo_bin):
                technique = "limited-suid"
            if not technique:
                continue
            rel = "/" + str(path.relative_to(root))
            severity = "critical" if setuid and st.st_uid == 0 and technique == "suid" else "high"
            if technique == "limited-suid":
                severity = "medium"
            findings.append(
                finding(
                    surface="image",
                    source=str(root),
                    line="",
                    binary=rel,
                    gtfo_binary=gtfo_bin,
                    technique=technique,
                    severity=severity,
                    reason=f"{'setuid' if setuid else 'setgid'} bit on GTFOBins binary",
                    evidence=f"mode={stat.filemode(mode)} uid={st.st_uid} gid={st.st_gid} path={rel}",
                    db=db,
                )
            )

    getcap = shutil.which("getcap")
    if getcap:
        proc = subprocess.run([getcap, "-r", str(root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        for line in proc.stdout.splitlines():
            if " = " not in line:
                continue
            path_str, caps = line.split(" = ", 1)
            gtfo_bin = db.resolve(path_str)
            if gtfo_bin and "capabilities" in db.functions(gtfo_bin):
                rel = "/" + str(Path(path_str).resolve().relative_to(root.resolve()))
                findings.append(
                    finding(
                        surface="image",
                        source=str(root),
                        binary=rel,
                        gtfo_binary=gtfo_bin,
                        technique="capabilities",
                        severity="high",
                        reason="Linux file capability on GTFOBins binary",
                        evidence=f"{rel} = {caps}",
                        db=db,
                    )
                )
    else:
        warn("getcap not found; skipping rootfs file capability scan")
    return findings


def docker_metadata(image: str) -> list[str]:
    docker = shutil.which("docker")
    if not docker:
        die("docker not found; pass an unpacked rootfs directory instead", 3)
    script = r"""
find / -xdev -type f \( -perm -4000 -o -perm -2000 \) -print 2>/dev/null | while IFS= read -r p; do
  mode=$(stat -c '%a' "$p" 2>/dev/null || echo '?')
  uid=$(stat -c '%u' "$p" 2>/dev/null || echo '?')
  gid=$(stat -c '%g' "$p" 2>/dev/null || echo '?')
  printf 'META\t%s\t%s\t%s\t%s\n' "$mode" "$uid" "$gid" "$p"
done
if command -v getcap >/dev/null 2>&1; then
  getcap -r / 2>/dev/null | sed 's/^/CAP\t/'
fi
"""
    proc = subprocess.run(
        [docker, "run", "--rm", "--entrypoint", "sh", image, "-c", script],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        die(f"docker inspection failed for {image}: {proc.stderr.strip() or proc.stdout.strip()}", 3)
    return proc.stdout.splitlines()


def scan_docker_image(image: str, db: GtfoDB) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line in docker_metadata(image):
        if line.startswith("META\t"):
            _, mode_s, uid_s, gid_s, path = line.split("\t", 4)
            gtfo_bin = db.resolve(path)
            if not gtfo_bin:
                continue
            try:
                mode = int(mode_s, 8)
            except ValueError:
                mode = 0
            setuid = bool(mode & 0o4000)
            setgid = bool(mode & 0o2000)
            technique = ""
            if setuid and "suid" in db.functions(gtfo_bin):
                technique = "suid"
            elif (setuid or setgid) and "limited-suid" in db.functions(gtfo_bin):
                technique = "limited-suid"
            if not technique:
                continue
            severity = "critical" if setuid and uid_s == "0" and technique == "suid" else "high"
            if technique == "limited-suid":
                severity = "medium"
            findings.append(
                finding(
                    surface="image",
                    source=image,
                    binary=path,
                    gtfo_binary=gtfo_bin,
                    technique=technique,
                    severity=severity,
                    reason=f"{'setuid' if setuid else 'setgid'} bit on GTFOBins binary in image",
                    evidence=f"mode={mode_s} uid={uid_s} gid={gid_s} path={path}",
                    db=db,
                )
            )
        elif line.startswith("CAP\t") and " = " in line:
            _, rest = line.split("\t", 1)
            path, caps = rest.split(" = ", 1)
            gtfo_bin = db.resolve(path)
            if gtfo_bin and "capabilities" in db.functions(gtfo_bin):
                findings.append(
                    finding(
                        surface="image",
                        source=image,
                        binary=path,
                        gtfo_binary=gtfo_bin,
                        technique="capabilities",
                        severity="high",
                        reason="Linux file capability on GTFOBins binary in image",
                        evidence=f"{path} = {caps}",
                        db=db,
                    )
                )
    return findings


def cmd_image_audit(args: argparse.Namespace, db: GtfoDB) -> None:
    target = Path(args.target)
    findings = scan_rootfs_dir(target, db) if target.is_dir() else scan_docker_image(args.target, db)
    output_findings(findings, args.format)
    fail_if_needed(findings, args.fail_on)


def scan_sudoers(target: Path, db: GtfoDB) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    file_cache: dict[Path, str] = {}

    for file, line_no, line in iter_text_lines(target, security_configs_only=True):
        upper = line.upper()
        lower = line.lower()
        if "NOPASSWD" not in upper and not ("commands" in lower and "sudo" in lower):
            if "commands:" not in lower:
                continue
            if file not in file_cache:
                try:
                    file_cache[file] = file.read_text(errors="ignore").lower()
                except OSError:
                    file_cache[file] = ""
            if "nopassword" not in file_cache[file]:
                continue

        rhs = line.split("NOPASSWD", 1)[-1] if "NOPASSWD" in upper else line
        candidates = extract_command_candidates(rhs)
        if "ALL" in candidates or re.search(r"(?:^|[:,\s])ALL(?:$|[,\s])", rhs.upper()):
            findings.append(
                {
                    "surface": "sudoers",
                    "source": str(file),
                    "line": line_no,
                    "binary": "ALL",
                    "gtfo_binary": "ALL",
                    "technique": "sudo",
                    "severity": "critical",
                    "reason": "sudoers grants NOPASSWD access to all commands",
                    "evidence": line.strip(),
                    "snippet": "",
                }
            )
            continue

        for candidate in candidates:
            gtfo_bin = db.resolve(candidate)
            if not gtfo_bin or "sudo" not in db.functions(gtfo_bin):
                continue
            findings.append(
                finding(
                    surface="sudoers",
                    source=str(file),
                    line=line_no,
                    binary=candidate,
                    gtfo_binary=gtfo_bin,
                    technique="sudo",
                    severity="critical" if "NOPASSWD" in upper else "high",
                    reason="sudo allowlist references a GTFOBins sudo primitive",
                    evidence=line.strip(),
                    db=db,
                )
            )
    return findings


def cmd_sudoers_audit(args: argparse.Namespace, db: GtfoDB) -> None:
    findings = scan_sudoers(Path(args.target), db)
    output_findings(findings, args.format)
    fail_if_needed(findings, args.fail_on)


CHMOD_RE = re.compile(r"\bchmod\b[^#\n]*(?:[ugoas]*\+s|[0-7]*[246][0-7]{3})", re.IGNORECASE)
INSTALL_MODE_RE = re.compile(r"\binstall\b[^#\n]*\s-m\s*[= ]?\s*['\"]?[0-7]*[246][0-7]{3}", re.IGNORECASE)
SETCAP_RE = re.compile(r"\bsetcap\b[^#\n]+", re.IGNORECASE)


def scan_iac(target: Path, db: GtfoDB) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for file, line_no, line in iter_text_lines(target, security_configs_only=True):
        if not (CHMOD_RE.search(line) or INSTALL_MODE_RE.search(line) or SETCAP_RE.search(line)):
            continue
        is_cap = bool(SETCAP_RE.search(line))
        technique = "capabilities" if is_cap else "suid"
        candidates = extract_command_candidates(line)
        for candidate in candidates:
            if candidate == "ALL":
                continue
            gtfo_bin = db.resolve(candidate)
            if not gtfo_bin or technique not in db.functions(gtfo_bin):
                continue
            severity = "high"
            if not is_cap and re.search(r"\b2[0-7]{3}\b", line) and not re.search(r"\b[46][0-7]{3}\b", line):
                severity = "medium"
            findings.append(
                finding(
                    surface="iac",
                    source=str(file),
                    line=line_no,
                    binary=candidate,
                    gtfo_binary=gtfo_bin,
                    technique=technique,
                    severity=severity,
                    reason=f"provisioning appears to grant {technique} primitive to GTFOBins binary",
                    evidence=line.strip(),
                    db=db,
                )
            )
    return findings


def cmd_iac_suid_audit(args: argparse.Namespace, db: GtfoDB) -> None:
    findings = scan_iac(Path(args.target), db)
    output_findings(findings, args.format)
    fail_if_needed(findings, args.fail_on)


STRING_RE = r"""(?:[rRuUbBfF]+)?(?P<quote>['"`])(?P<value>(?:\\.|(?!\1).)*?)(?P=quote)"""
SHELLOUT_PATTERNS = [
    re.compile(rf"\b(?:subprocess\.(?:run|Popen|call|check_call|check_output)|os\.(?:system|popen))\(\s*(?:\[)?\s*{STRING_RE}"),
    re.compile(rf"\b(?:exec|execFile|spawn|spawnSync)\(\s*{STRING_RE}"),
    re.compile(rf"\bexec\.Command(?:Context)?\(\s*{STRING_RE}"),
    re.compile(rf"\b(?:system|exec|spawn)\(\s*{STRING_RE}"),
    re.compile(rf"`(?P<value>[^`]+)`"),
]


def first_word(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    return parts[0] if parts else ""


def extract_shellout_command(line: str) -> str:
    for pattern in SHELLOUT_PATTERNS:
        match = pattern.search(line)
        if match:
            return first_word(match.group("value"))
    return ""


def preferred_shellout_technique(db: GtfoDB, gtfo_bin: str) -> str:
    for technique in ["shell", "command", "sudo", "file-read", "file-write", "file-upload", "file-download"]:
        if technique in db.functions(gtfo_bin):
            return technique
    categories = db.categories(gtfo_bin)
    return categories[0] if categories else "unknown"


def scan_shellout(target: Path, db: GtfoDB) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for file, line_no, line in iter_text_lines(target, source_only=True):
        command = extract_shellout_command(line)
        if not command:
            continue
        gtfo_bin = db.resolve(command)
        if not gtfo_bin:
            continue
        technique = preferred_shellout_technique(db, gtfo_bin)
        suspicious = any(marker in line for marker in ["shell=True", "${", "$(", "%", ".format(", "f'", 'f"'])
        severity = "medium" if suspicious else "low"
        findings.append(
            finding(
                surface="shellout",
                source=str(file),
                line=line_no,
                binary=command,
                gtfo_binary=gtfo_bin,
                technique=technique,
                severity=severity,
                reason="source code shells out to a GTFOBins binary; verify input control and privileges",
                evidence=line.strip(),
                db=db,
            )
        )
    return findings


def cmd_shellout_grep(args: argparse.Namespace, db: GtfoDB) -> None:
    findings = scan_shellout(Path(args.target), db)
    output_findings(findings, args.format)
    fail_if_needed(findings, args.fail_on)


def cmd_project_audit(args: argparse.Namespace, db: GtfoDB) -> None:
    root = Path(args.target)
    findings = [*scan_sudoers(root, db), *scan_iac(root, db), *scan_shellout(root, db)]
    findings.sort(key=lambda item: (-SEVERITY_ORDER.get(str(item["severity"]), 0), str(item["source"]), int(item["line"] or 0)))
    output_findings(findings, args.format)
    fail_if_needed(findings, args.fail_on)


def add_format_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["text", "tsv", "jsonl"], default="text")
    parser.add_argument("--fail-on", choices=list(SEVERITY_ORDER), help="exit 1 if any finding is at or above this severity")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Defensive LOLBin/GTFOBins audit helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("data-dir", help="print detected GTFOBins data directory")
    p.set_defaults(func=cmd_data_dir)

    p = sub.add_parser("bins-with", help="list GTFOBins entries with a technique")
    p.add_argument("technique")
    add_format_flags(p)
    p.set_defaults(func=cmd_bins_with)

    p = sub.add_parser("has-technique", help="exit 0 if binary has a GTFOBins technique")
    p.add_argument("binary")
    p.add_argument("technique")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--snippet", action="store_true")
    p.set_defaults(func=cmd_has_technique)

    p = sub.add_parser("explain-bin", help="print GTFOBins snippets for a binary")
    p.add_argument("binary")
    p.add_argument("technique", nargs="?")
    p.set_defaults(func=cmd_explain_bin)

    p = sub.add_parser("image-audit", help="audit Docker image or rootfs dir for privileged GTFOBins")
    p.add_argument("target")
    add_format_flags(p)
    p.set_defaults(func=cmd_image_audit)

    p = sub.add_parser("sudoers-audit", help="audit sudoers/provisioning files for risky allowlists")
    p.add_argument("target")
    add_format_flags(p)
    p.set_defaults(func=cmd_sudoers_audit)

    p = sub.add_parser("iac-suid-audit", help="audit IaC/provisioning files for chmod/setcap GTFOBins")
    p.add_argument("target")
    add_format_flags(p)
    p.set_defaults(func=cmd_iac_suid_audit)

    p = sub.add_parser("shellout-grep", help="hunt for source shell-outs to GTFOBins binaries")
    p.add_argument("target")
    add_format_flags(p)
    p.set_defaults(func=cmd_shellout_grep)

    p = sub.add_parser("project-audit", help="run sudoers, IaC, and shell-out audits against a repo")
    p.add_argument("target")
    add_format_flags(p)
    p.set_defaults(func=cmd_project_audit)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    db = GtfoDB(discover_data_dir())
    args.func(args, db)


if __name__ == "__main__":
    main()
