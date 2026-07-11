import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hooks.session_start import tool_wrappers


class CandidateFromNpmTest(unittest.TestCase):
    def test_uses_sibling_binary_without_invoking_npm(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            npm = bin_dir / "npm"
            target = bin_dir / "agent-browser"
            npm.touch(mode=0o755)
            target.touch(mode=0o755)

            with (
                patch.dict(os.environ, {"PATH": str(bin_dir)}),
                patch.object(
                    tool_wrappers.subprocess,
                    "run",
                    side_effect=AssertionError("npm should not run"),
                ),
            ):
                self.assertEqual(
                    tool_wrappers._candidate_from_npm("agent-browser"),
                    target,
                )


if __name__ == "__main__":
    unittest.main()
