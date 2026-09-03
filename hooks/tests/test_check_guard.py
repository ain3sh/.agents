from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from hooks.pre_tool_use.check_guard import _validator_re, _violation


VALIDATORS = _validator_re(["pytest", "vitest", "eslint", "tsc"])
RUN_CHECK = Path(__file__).resolve().parents[2] / "scripts" / "run-check"
CHECK_GUARD = Path(__file__).resolve().parents[1] / "pre_tool_use" / "check_guard.py"


def _load_run_check():
    loader = importlib.machinery.SourceFileLoader("run_check_module", str(RUN_CHECK))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


class CheckGuardTest(unittest.TestCase):
    def analyze(self, command: str, *, background: bool = False):
        return _violation(
            command,
            fire_and_forget=background,
            validator_re=VALIDATORS,
        )

    def test_allows_only_the_canonical_shape(self) -> None:
        command = (
            "~/.agents/scripts/run-check e2e "
            '--cwd "/tmp/project with spaces" '
            '--env PATH="/opt/node/bin:$PATH" -- '
            "npm run test:e2e:run -- e2e-tests/chat-input.test.ts"
        )

        self.assertIsNone(self.analyze(command))

    def test_rejects_raw_validator(self) -> None:
        self.assertEqual(
            self.analyze("npm run test -- src/foo.test.ts"),
            "validator commands must use run-check",
        )

    def test_rejects_redirected_and_polled_validator(self) -> None:
        command = (
            "cd /tmp/project\n"
            '&& PATH="/opt/node/bin:$PATH" npm run test:e2e:run -- '
            "e2e-tests/cloud-sync-retain-flush.test.ts "
            '> /tmp/e2e.log 2>&1; echo "exit=$?"'
        )

        self.assertEqual(
            self.analyze(command),
            "validator commands must use run-check",
        )

    def test_rejects_filtered_validator(self) -> None:
        self.assertEqual(
            self.analyze(
                "npx vitest run src/foo.test.ts 2>&1 | tee /tmp/test.log | tail -30"
            ),
            "validator commands must use run-check",
        )

    def test_rejects_background_tool_call(self) -> None:
        self.assertEqual(
            self.analyze(
                "~/.agents/scripts/run-check test -- pytest tests/test_api.py",
                background=True,
            ),
            "checks must stay attached in the foreground",
        )

    def test_rejects_shell_composition_around_run_check(self) -> None:
        cases = (
            "~/.agents/scripts/run-check test -- pytest tests/test_api.py &",
            "~/.agents/scripts/run-check test -- pytest tests/test_api.py | tail",
            "~/.agents/scripts/run-check test -- pytest tests/test_api.py > x.log",
            "~/.agents/scripts/run-check test -- pytest tests/test_api.py; sleep 30",
            "cd /tmp && ~/.agents/scripts/run-check test -- pytest tests/test_api.py",
            "PATH=/opt/bin:$PATH ~/.agents/scripts/run-check test -- pytest",
        )

        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(
                    self.analyze(command),
                    "run-check must be the entire shell command",
                )

    def test_rejects_malformed_run_check_arguments(self) -> None:
        cases = (
            "~/.agents/scripts/run-check test pytest",
            "~/.agents/scripts/run-check --cwd /tmp -- pytest",
            "~/.agents/scripts/run-check test --cwd -- pytest",
            "~/.agents/scripts/run-check test --env PATH -- pytest",
        )

        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(
                    self.analyze(command),
                    "run-check arguments do not match the accepted grammar",
                )

    def test_rejects_noncanonical_run_check_path(self) -> None:
        self.assertEqual(
            self.analyze("/tmp/run-check test -- pytest"),
            "checks must invoke the canonical run-check path",
        )

    def test_ignores_non_validator_commands(self) -> None:
        self.assertIsNone(self.analyze("git log --oneline | tail -5"))
        self.assertIsNone(self.analyze("git diff -- scripts/run-check"))
        self.assertIsNone(self.analyze("make checklist"))
        self.assertIsNone(self.analyze('printf "npm run test && pytest"'))
        self.assertIsNone(self.analyze('echo "&&" pytest'))


class ExecutableModeTest(unittest.TestCase):
    def test_hook_and_runner_are_executable(self) -> None:
        self.assertTrue(os.access(CHECK_GUARD, os.X_OK))
        self.assertTrue(os.access(RUN_CHECK, os.X_OK))


class RunCheckTest(unittest.TestCase):
    def test_owns_cwd_env_stream_log_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            cwd = Path(temp_dir) / "cwd"
            cwd.mkdir()
            child = (
                "import os, pathlib, sys; "
                "print(pathlib.Path.cwd(), flush=True); "
                "print(os.environ['CHECK_PROBE'], file=sys.stderr, flush=True); "
                "sys.stdin.read(1); "
                "print('finished', flush=True); "
                "raise SystemExit(7)"
            )
            process = subprocess.Popen(
                [
                    str(RUN_CHECK),
                    "test",
                    "--cwd",
                    str(cwd),
                    "--env",
                    "CHECK_PROBE=stderr-live",
                    "--",
                    sys.executable,
                    "-c",
                    child,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env={**os.environ, "DROID_CHECK_LOG_DIR": str(log_dir)},
            )
            assert process.stdout is not None
            assert process.stdin is not None

            log_line = process.stdout.readline()
            first = process.stdout.readline()
            second = process.stdout.readline()

            self.assertRegex(log_line, r"^\[run-check\] log: .+\.log$")
            self.assertEqual(first, f"{cwd}\n")
            self.assertEqual(second, "stderr-live\n")
            self.assertIsNone(process.poll())

            process.stdin.write("x")
            process.stdin.flush()
            process.stdin.close()
            remaining = process.stdout.read()
            status = process.wait()
            process.stdout.close()

            self.assertEqual(status, 7)
            self.assertIn("finished\n", remaining)
            self.assertIn("[run-check] exit: 7\n", remaining)

            log_path = Path(log_line.removeprefix("[run-check] log: ").strip())
            self.assertEqual(
                log_path.read_text(),
                f"{log_line}{cwd}\nstderr-live\nfinished\n[run-check] exit: 7\n",
            )

    def test_uses_the_nearest_nvmrc_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            cwd = root / "packages" / "cli"
            nvm_dir = Path(temp_dir) / "nvm"
            cwd.mkdir(parents=True)
            nvm_dir.mkdir()
            (root / ".nvmrc").write_text("20\n")
            (root / "packages" / ".nvmrc").write_text("22.19\n")
            nvm_exec = nvm_dir / "nvm-exec"
            nvm_exec.write_text(
                '#!/bin/sh\nprintf "selector=%s\\n" "$NODE_VERSION"\nexec "$@"\n'
            )
            nvm_exec.chmod(0o755)

            result = subprocess.run(
                [
                    str(RUN_CHECK),
                    "node-version",
                    "--cwd",
                    str(cwd),
                    "--",
                    sys.executable,
                    "-c",
                    "import os; print('child=' + str(os.getenv('NODE_VERSION')))",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "DROID_CHECK_LOG_DIR": str(Path(temp_dir) / "logs"),
                    "NVM_DIR": str(nvm_dir),
                },
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn(
                f"[run-check] node: 22.19 ({root / 'packages' / '.nvmrc'})\n",
                result.stdout,
            )
            self.assertIn("selector=22.19\n", result.stdout)
            self.assertIn("child=None\n", result.stdout)

    def test_fails_before_starting_when_nvmrc_cannot_be_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            cwd = root / "packages" / "cli"
            cwd.mkdir(parents=True)
            (root / ".nvmrc").write_text("22.19\n")
            marker = Path(temp_dir) / "started"

            result = subprocess.run(
                [
                    str(RUN_CHECK),
                    "node-version",
                    "--cwd",
                    str(cwd),
                    "--",
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(marker)!r}).touch()",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "DROID_CHECK_LOG_DIR": str(Path(temp_dir) / "logs"),
                    "NVM_DIR": str(Path(temp_dir) / "missing-nvm"),
                },
            )

            self.assertEqual(result.returncode, 127)
            self.assertIn("requires NVM", result.stdout)
            self.assertFalse(marker.exists())

    def test_forwards_termination_to_the_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as log_dir:
            child = (
                "import os, signal, time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "print(os.getpid(), flush=True); "
                "time.sleep(60)"
            )
            process = subprocess.Popen(
                [str(RUN_CHECK), "signal", "--", sys.executable, "-c", child],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env={**os.environ, "DROID_CHECK_LOG_DIR": log_dir},
            )
            assert process.stdout is not None

            process.stdout.readline()
            child_pid = int(process.stdout.readline())
            process.terminate()
            remaining = process.stdout.read()
            status = process.wait(timeout=5)
            process.stdout.close()

            self.assertEqual(status, 143)
            self.assertIn("[run-check] exit: 143\n", remaining)
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    def test_bounds_retained_logs(self) -> None:
        with tempfile.TemporaryDirectory() as log_dir:
            directory = Path(log_dir)
            for index in range(55):
                path = directory / f"old-{index}.log"
                path.write_text("old")
                os.utime(path, (index, index))

            result = subprocess.run(
                [str(RUN_CHECK), "retention", "--", sys.executable, "-c", "pass"],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "DROID_CHECK_LOG_DIR": log_dir},
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(len(list(directory.glob("*.log"))), 50)

    def test_bounds_retained_logs_across_concurrent_creators(self) -> None:
        module = _load_run_check()
        with tempfile.TemporaryDirectory() as log_dir:
            directory = Path(log_dir)
            for index in range(49):
                path = directory / f"old-{index}.log"
                path.write_text("old")
                os.utime(path, (index, index))

            def create(index: int) -> None:
                _path, log = module._create_log(directory, f"concurrent-{index}")
                log.close()

            with ThreadPoolExecutor(max_workers=8) as executor:
                list(executor.map(create, range(8)))

            self.assertEqual(len(list(directory.glob("*.log"))), 50)


if __name__ == "__main__":
    unittest.main()
