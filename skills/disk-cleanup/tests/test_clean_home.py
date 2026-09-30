"""The home cache pass preserves sessions and every configured dsx location."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLEANER = Path(__file__).resolve().parents[1] / "scripts" / "clean_home.py"


class HomeProtectionTests(unittest.TestCase):
    def test_cache_pass_retains_sessions_and_dsx_overrides(self):
        for setting in (None, "DSX_CACHE_DIR", "DSX_DB_PATH", "XDG_CACHE_HOME"):
            with self.subTest(setting=setting), tempfile.TemporaryDirectory() as raw:
                home = Path(raw) / "home"
                sessions = home / ".factory/sessions"
                sessions.mkdir(parents=True)
                (sessions / "session.jsonl").write_text("source")
                cache = home / ".cache"
                default = cache / "dsx"
                default.mkdir(parents=True)
                (default / "index.sqlite").write_text("default")
                configured = cache / "configured"
                configured.mkdir()
                database = configured / "index.sqlite"
                database.write_text("configured")
                (cache / "junk").write_text("regenerable")
                env = dict(os.environ, HOME=str(home))
                for key in ("DSX_CACHE_DIR", "DSX_DB_PATH", "XDG_CACHE_HOME"):
                    env.pop(key, None)
                if setting:
                    env[setting] = str(
                        database if setting == "DSX_DB_PATH" else configured
                    )
                result = subprocess.run(
                    [
                        sys.executable, str(CLEANER), "--home", str(home),
                        "--profile", "caches", "--apply",
                    ],
                    cwd=home,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((sessions / "session.jsonl").read_text(), "source")
                self.assertEqual((default / "index.sqlite").read_text(), "default")
                if setting:
                    self.assertEqual(database.read_text(), "configured")
                self.assertFalse((cache / "junk").exists())


if __name__ == "__main__":
    unittest.main()
