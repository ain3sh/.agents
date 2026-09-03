from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"


class SourceWorktreeIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.primary = self.root / "primary"
        self.source = self.root / "source"
        self.target = self.root / "target"

        self.exec("git", "init", "-b", "main", str(self.primary))
        self.exec("git", "-C", str(self.primary), "config", "user.name", "Test")
        self.exec(
            "git",
            "-C",
            str(self.primary),
            "config",
            "user.email",
            "test@example.com",
        )
        (self.primary / ".gitignore").write_text("node_modules/\ndist/\n.venv/\n")
        (self.primary / "packages/pkg").mkdir(parents=True)
        (self.primary / "package.json").write_text(
            '{"private":true,"workspaces":["packages/*"]}\n'
        )
        (self.primary / "packages/pkg/package.json").write_text(
            '{"name":"@test/pkg","exports":"./dist/index.js"}\n'
        )
        self.exec("git", "-C", str(self.primary), "add", ".")
        self.exec("git", "-C", str(self.primary), "commit", "-m", "fixture")
        self.exec(
            "git",
            "-C",
            str(self.primary),
            "worktree",
            "add",
            "-b",
            "source-branch",
            str(self.source),
        )
        self.exec(
            "git",
            "-C",
            str(self.primary),
            "worktree",
            "add",
            "-b",
            "target-branch",
            str(self.target),
        )

        (self.source / "node_modules/dep").mkdir(parents=True)
        (self.source / "node_modules/dep/index.js").write_text("source dependency\n")
        (self.source / "packages/pkg/dist").mkdir(parents=True)
        (self.source / "packages/pkg/dist/index.js").write_text("source build\n")
        (self.source / ".venv").mkdir()
        (self.source / ".venv/marker").write_text("source venv\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def exec(
        self,
        *args: str,
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
        )

    def script(
        self, name: str, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        result = self.exec(
            sys.executable,
            str(SCRIPTS / f"{name}.py"),
            *args,
            cwd=self.target,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(
                f"{name}.py exited {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def test_explicit_source_controls_repair_verify_and_break(self) -> None:
        before = self.script("verify", "--from", "source-branch", check=False)
        self.assertEqual(before.returncode, 1, before.stdout + before.stderr)
        self.assertIn("although source has", before.stdout)

        repaired = self.script("repair", "--from", "source-branch")
        self.assertIn("target <- source", repaired.stdout)
        self.assertEqual(
            (self.target / "node_modules/dep/index.js").read_text(),
            "source dependency\n",
        )
        self.assertEqual(
            (self.target / "packages/pkg/dist/index.js").read_text(),
            "source build\n",
        )
        self.assertEqual(
            os.stat(self.source / "node_modules/dep/index.js").st_ino,
            os.stat(self.target / "node_modules/dep/index.js").st_ino,
        )
        self.assertTrue((self.target / ".venv").is_symlink())

        verified = self.script("verify", "--from", f"../{self.source.name}")
        self.assertIn("target: ok", verified.stdout)

        broken = self.script("break")
        self.assertIn("source_symlinks=1", broken.stdout)
        self.assertFalse((self.target / "node_modules").exists())
        self.assertFalse((self.target / "packages/pkg/dist").exists())
        self.assertFalse((self.target / ".venv").exists())

    def test_source_must_differ_from_target(self) -> None:
        result = self.script("repair", "--from", "target-branch", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source and target are the same worktree", result.stderr)

    def test_primary_remains_the_default_source(self) -> None:
        (self.primary / "node_modules/primary-dep").mkdir(parents=True)
        (self.primary / "node_modules/primary-dep/index.js").write_text(
            "primary dependency\n"
        )

        repaired = self.script("repair")

        self.assertIn("target <- primary", repaired.stdout)
        self.assertEqual(
            (self.target / "node_modules/primary-dep/index.js").read_text(),
            "primary dependency\n",
        )


if __name__ == "__main__":
    unittest.main()
