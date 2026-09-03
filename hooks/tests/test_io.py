import io
import json
import unittest
from unittest.mock import patch

from hooks.utils.io import HookInputError, read_input
from hooks.utils.types import SessionStartInput, StopInput


class ReadInputTest(unittest.TestCase):
    def read(self, payload: dict[str, object]):
        with patch("sys.stdin", io.StringIO(json.dumps(payload))):
            return read_input()

    def test_parses_current_session_start_contract(self) -> None:
        hook_input = self.read(
            {
                "session_id": "session",
                "transcript_path": "/tmp/session.jsonl",
                "cwd": "/tmp/project",
                "permission_mode": "auto-low",
                "hook_event_name": "SessionStart",
                "message_id": "message",
                "source": "startup",
            }
        )

        self.assertIsInstance(hook_input, SessionStartInput)
        self.assertEqual(hook_input.permission_mode, "auto-low")
        self.assertEqual(hook_input.message_id, "message")
        self.assertEqual(hook_input.source, "startup")

    def test_parses_current_stop_metadata(self) -> None:
        hook_input = self.read(
            {
                "hook_event_name": "Stop",
                "permission_mode": "off",
                "stop_hook_active": True,
                "tool_execution_count": 4,
                "elapsed_time": 1200,
            }
        )

        self.assertIsInstance(hook_input, StopInput)
        self.assertTrue(hook_input.stop_hook_active)
        self.assertEqual(hook_input.tool_execution_count, 4)
        self.assertEqual(hook_input.elapsed_time, 1200)

    def test_rejects_stale_camel_case_event_name(self) -> None:
        with self.assertRaisesRegex(HookInputError, "hook_event_name"):
            self.read({"hookEventName": "SessionStart", "source": "startup"})


if __name__ == "__main__":
    unittest.main()
