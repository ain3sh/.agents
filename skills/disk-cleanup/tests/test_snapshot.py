"""Active directory growth is allowed; lost entries and changed files are not."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "snapshot.py"
SPEC = importlib.util.spec_from_file_location("cleanup_snapshot", SCRIPT)
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class SnapshotProtectionTests(unittest.TestCase):
    def setUp(self):
        self.before = {
            "factory_sessions": {"exists": True, "entries": ["existing"]},
            "protected": [
                {"path": "/sessions", "exists": True, "kind": "dir", "size": 128, "inode": 7},
                {"path": "/model", "exists": True, "kind": "file", "size": 5, "inode": 8, "sha256": "original"},
            ],
        }
        self.after = deepcopy(self.before)

    def test_active_session_directory_growth_is_not_data_loss(self):
        self.after["factory_sessions"]["entries"].append("new")
        self.after["protected"][0]["size"] += 64
        self.assertEqual(snapshot.compare(self.before, self.after), [])

    def test_replaced_protected_directory_is_still_rejected(self):
        self.after["protected"][0]["inode"] = 99
        self.assertEqual(
            snapshot.compare(self.before, self.after),
            ["protected path changed inode: /sessions (7 -> 99)"],
        )

    def test_same_size_protected_file_change_is_still_rejected(self):
        self.after["protected"][1]["sha256"] = "changed"
        self.assertEqual(
            snapshot.compare(self.before, self.after),
            ["protected path changed sha256: /model (original -> changed)"],
        )

    def test_missing_existing_session_is_still_rejected(self):
        self.after["factory_sessions"]["entries"] = ["new"]
        self.assertEqual(
            snapshot.compare(self.before, self.after),
            ["1 Factory session entries disappeared: existing"],
        )


if __name__ == "__main__":
    unittest.main()
