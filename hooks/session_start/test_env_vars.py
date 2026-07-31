import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hooks.session_start import env_vars


class PathConfigTest(unittest.TestCase):
    def test_expands_and_deduplicates_path_entries(self) -> None:
        with patch.dict(os.environ, {"HOME": "/home/example"}):
            self.assertEqual(
                env_vars._path_entries(
                    ["~/.local/bin", "/opt/tools/bin", "~/.local/bin", ""]
                ),
                ["/home/example/.local/bin", "/opt/tools/bin"],
            )

    def test_writes_prepend_and_append_to_session_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "session.env"
            local_bin = str(Path.home() / ".local" / "bin")
            with patch.dict(
                os.environ,
                {
                    "DROID_ENV_FILE": str(env_file),
                    "PATH": f"/usr/bin:{local_bin}",
                },
                clear=False,
            ):
                count = env_vars.apply_path_config(
                    {
                        "path_prepend": [local_bin, "/opt/tools/bin"],
                        "path_append": ["/opt/tail/bin"],
                    }
                )

            self.assertEqual(count, 1)
            self.assertEqual(
                env_file.read_text(),
                f"export PATH='{local_bin}:/opt/tools/bin:/usr/bin:/opt/tail/bin'\n",
            )

    def test_path_config_keys_are_not_exported_as_variables(self) -> None:
        self.assertEqual(
            env_vars._config_env_vars(
                {
                    "path_prepend": ["~/.local/bin"],
                    "path_append": "/opt/bin",
                    "EXAMPLE": "value",
                }
            ),
            {"EXAMPLE": "value"},
        )


if __name__ == "__main__":
    unittest.main()
