"""CLI protection invariants; every deletion uses an isolated temporary root."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLEANER = Path(__file__).resolve().parents[1] / "scripts" / "clean_tmp.py"


class TemporaryProtectionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(prefix="disk-cleanup-test-")
        self.addCleanup(self.fixture.cleanup)
        self.base = Path(self.fixture.name)
        self.root = self.base / "tmp"
        self.root.mkdir()
        self.home = self.base / "home"
        self.home.mkdir()
        self.env = dict(
            os.environ, HOME=str(self.home), XDG_CACHE_HOME=str(self.home / ".cache")
        )
        self.env.pop("DSX_CACHE_DIR", None)
        self.env.pop("DSX_DB_PATH", None)
        (self.root / "junk").write_text("regenerable")

    def run_cleaner(self, *args, env=None):
        return subprocess.run(
            [sys.executable, str(CLEANER), "--tmp-root", str(self.root), *args],
            cwd=self.home,
            env=env or self.env,
            capture_output=True,
            text=True,
        )

    def test_nested_protection_survives_preview_apply_and_repeat(self):
        """A protected file retains its container; unrelated junk is removed."""
        container = self.root / "evidence"
        container.mkdir()
        protected = container / "patch.diff"
        protected.write_text("irreplaceable")
        preview = self.run_cleaner("--protect", str(protected))
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertTrue((self.root / "junk").exists())
        for _ in range(2):
            result = self.run_cleaner("--protect", str(protected), "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(protected.read_text(), "irreplaceable")
            self.assertFalse((self.root / "junk").exists())

    def test_symlink_protection_retains_alias_and_target_container(self):
        """Both the lexical protected alias and its resolved target survive."""
        container = self.root / "evidence"
        container.mkdir()
        target = container / "artifact"
        target.write_text("irreplaceable")
        alias = self.root / "alias"
        alias.symlink_to(target)
        result = self.run_cleaner("--protect", str(alias), "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(alias.is_symlink())
        self.assertEqual(target.read_text(), "irreplaceable")
        self.assertFalse((self.root / "junk").exists())

    def test_missing_explicit_protection_stops_before_deletion(self):
        """Missing explicit paths fail in both modes without removing junk."""
        for mode in ([], ["--apply"]):
            result = self.run_cleaner("--protect", str(self.root / "missing"), *mode)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("protected path missing", result.stderr)
            self.assertTrue((self.root / "junk").exists())

    def test_protected_ancestor_retains_every_child(self):
        """Protecting the temporary root's ancestor excludes all candidates."""
        result = self.run_cleaner("--protect", str(self.base), "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "junk").exists())

    def test_dsx_environment_paths_are_retained_without_explicit_flags(self):
        """Configured dsx paths survive while an absent unused cache is allowed."""
        index = self.root / "dsx-state"
        index.mkdir()
        database = index / "index.sqlite"
        database.write_text("durable index")
        for overrides in (
            {"DSX_CACHE_DIR": str(index)},
            {"DSX_DB_PATH": str(database)},
            {"XDG_CACHE_HOME": str(index)},
        ):
            (self.root / "junk").write_text("regenerable")
            result = self.run_cleaner("--apply", env=dict(self.env, **overrides))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(database.read_text(), "durable index")
            self.assertFalse((self.root / "junk").exists())


if __name__ == "__main__":
    unittest.main()
