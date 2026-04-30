---
name: worktree-setup
description: "Repair git worktree dev environments before running tooling. Trigger when cwd is a worktree, dependencies are missing, module resolution points at main, generated artifacts are missing, installs fail, or a repo/worktree moved paths/hosts."
---

# Worktree Setup

## Always check first

Before any lint/test/build/typecheck/dev command:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
WORKTREE=$(git rev-parse --show-toplevel)
[ "$WORKTREE" != "$MAIN_REPO" ] && echo "WORKTREE DETECTED -- repair deps first"
```

If the path contains `worktree` (for example `factory-mono-worktrees/fac-123`), assume it needs setup.

## Rules

- Do **not** run `npm install`, `bun install`, `pnpm install`, or create a fresh venv in a worktree.
- Reuse main-repo dependencies.
- Make workspace packages resolve to the **current worktree**, not main.
- Prefer hardlink-tree mirrors: `cp -al`, not root `node_modules` symlinks and not `cp -as` absolute symlink mirrors.
- Use relative symlinks for rewritten workspace package links so worktrees also work via SSHFS/alternate mount paths.
- Discover workspace packages from the **worktree branch's** `package.json`, not main. Older branches may contain packages main no longer has, e.g. `@factory/models`.

## Canonical Factory repair script

Run from the main repo after main dependencies/generated artifacts are healthy (`npm install`, `npm run setup` as needed in main only):

```bash
cd /home/ain3sh/factory/factory-mono
python3 - <<'PY'
import json, os, shutil, subprocess
from pathlib import Path

MAIN = Path(subprocess.check_output(["git", "worktree", "list"], text=True).splitlines()[0].split()[0]).resolve()
raw = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=MAIN, text=True)
WORKTREES = [Path(l.split(" ", 1)[1]).resolve() for l in raw.splitlines() if l.startswith("worktree ")]
WORKTREES = [p for p in WORKTREES if p != MAIN]


def remove(path: Path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def mirror(src: Path, dst: Path):
    remove(dst)
    dst.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["cp", "-al", str(src) + "/.", str(dst) + "/"])


def workspaces(root: Path):
    try:
        patterns = json.loads((root / "package.json").read_text()).get("workspaces", [])
    except Exception:
        return {}
    found = {}
    for pattern in patterns:
        for pkg_json in sorted(root.glob(pattern + "/package.json")):
            try:
                name = json.loads(pkg_json.read_text()).get("name")
            except Exception:
                continue
            if isinstance(name, str) and name:
                found[name] = pkg_json.parent.relative_to(root)
    return found


def rel_link(link: Path, target: Path):
    if link.exists() or link.is_symlink():
        remove(link)
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(os.path.relpath(target, link.parent))


def rewire(nm: Path, wt: Path, pkgs: dict):
    if not nm.exists():
        return 0
    count = 0
    for name, rel in pkgs.items():
        target = wt / rel
        if not target.exists():
            continue
        if name.startswith("@"):
            scope, pkg = name.split("/", 1)
            scope_dir = nm / scope
            if scope_dir.is_symlink() or scope_dir.is_file():
                scope_dir.unlink()
            scope_dir.mkdir(parents=True, exist_ok=True)
            link = scope_dir / pkg
        else:
            link = nm / name
        rel_link(link, target)
        count += 1
    return count


MAIN_LOCAL_NODE_MODULES = sorted(
    p.relative_to(MAIN)
    for p in MAIN.glob("**/node_modules")
    if p.is_dir()
    and p != MAIN / "node_modules"
    and ".git" not in p.parts
    and "node_modules" not in p.relative_to(MAIN).parent.parts
)

for i, wt in enumerate(WORKTREES, 1):
    pkgs = workspaces(wt)
    print(f"[{i}/{len(WORKTREES)}] {wt.name}")

    mirror(MAIN / "node_modules", wt / "node_modules")
    root_links = rewire(wt / "node_modules", wt, pkgs)

    local_mirrors = local_links = 0
    for rel_nm in MAIN_LOCAL_NODE_MODULES:
        if not (wt / rel_nm.parent).exists():
            continue
        mirror(MAIN / rel_nm, wt / rel_nm)
        local_mirrors += 1
        local_links += rewire(wt / rel_nm, wt, pkgs)

    generated = "skipped"
    if (MAIN / "apps/cli/src/generated").exists() and (wt / "apps/cli/src").exists():
        mirror(MAIN / "apps/cli/src/generated", wt / "apps/cli/src/generated")
        generated = "mirrored"

    for env_name in (".venv", "venv"):
        src, dst = MAIN / env_name, wt / env_name
        if src.exists():
            remove(dst)
            dst.symlink_to(os.path.relpath(src, dst.parent))

    print(f"  root_links={root_links}; local_mirrors={local_mirrors}; local_links={local_links}; generated={generated}")
PY
```

What this does:

- hardlink-mirrors root `node_modules`
- hardlink-mirrors package-local `node_modules` (`apps/cli/node_modules`, etc.)
- rewires workspace packages from each branch's own workspace list
- uses relative workspace symlinks
- mirrors Factory CLI generated artifacts (`apps/cli/src/generated`) for embedded `rg`, `keytar`, and agent-browser assets
- links `.venv`/`venv` from main when present

## Verification

For Factory CLI worktrees:

```bash
cd /home/ain3sh/factory/factory-mono
python3 - <<'PY'
import os, subprocess
from pathlib import Path
main = Path(subprocess.check_output(["git", "worktree", "list"], text=True).splitlines()[0].split()[0]).resolve()
raw = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=main, text=True)
fail = []
for line in raw.splitlines():
    if not line.startswith("worktree "):
        continue
    wt = Path(line.split(" ", 1)[1]).resolve()
    if wt == main or not (wt / "apps/cli/src/index.ts").exists():
        continue
    try:
        out = subprocess.check_output(["timeout", "20", str(wt / "node_modules/.bin/bun"), "src/index.ts", "--help"], cwd=wt / "apps/cli", text=True, stderr=subprocess.STDOUT, timeout=25)
        common = wt / "node_modules/@factory/common"
        ok = "Usage: droid" in out and common.is_symlink() and not os.readlink(common).startswith("/") and os.path.realpath(common) == str(wt / "packages/common")
    except Exception as e:
        ok = False
        print(f"{wt.name}: FAIL {e!r}")
    if ok:
        print(f"{wt.name}: ok")
    else:
        fail.append(wt.name)
print("failures", len(fail))
if fail:
    raise SystemExit(1)
PY

find /home/ain3sh/factory/factory-mono-worktrees -xtype l -lname '/mnt/dev/work/factory*' -print
find /home/ain3sh/factory/factory-mono-worktrees -xtype l -lname '/home/ain3sh/factory*' -print
```

Expected: all CLI smoke tests pass, and both `find` commands print nothing.

For general TS resolution, confirm workspace packages resolve under the worktree:

```bash
node -e 'console.log(require.resolve("@factory/common/package.json"))'
```

## Path migration warning

After moving a repo/worktrees between hosts or paths, fix `.git/worktrees/*/gitdir` and each worktree's `.git` pointer before `git worktree prune`.

`git worktree prune` will unregister valid worktrees if those pointers still reference the old path.

## Failure map

| Symptom | Fix |
|---|---|
| `Cannot find module X` | Run the canonical repair; ensure package-local mirrors and generated artifacts exist |
| Missing `@factory/models` on older branch | Discover/rewrite workspace links from the worktree branch, not main |
| Missing `@/generated/bin/keytar` or `@/generated/agent-browser/assets` | Mirror `apps/cli/src/generated` from main |
| Stale exports/impossible type errors | Rewire workspace links in every mirrored `node_modules`, including package-local dirs |
| Bin exists but fails relative imports | Use hardlink mirror; preserve `.bin` symlinks |
| Works locally but fails through SSHFS/alternate path | Remove absolute symlink mirrors; use `cp -al` + relative workspace symlinks |
| Install was run in worktree | Remove worktree deps and rebuild mirrors from main |
| Valid worktrees disappeared after prune | Restore/fix `.git/worktrees/*/gitdir` and worktree `.git` pointer files |
