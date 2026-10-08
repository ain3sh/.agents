from __future__ import annotations

import fcntl
import importlib.machinery
import importlib.util
import os
import select
import signal
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
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
            "~/.agents/scripts/run-check e2e --exclusive "
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

    def test_allows_env_file_and_unset_prefix(self) -> None:
        command = (
            "~/.agents/scripts/run-check record --unset-prefix FACTORY_ "
            "--env-file ~/factory/dev-env.json --env LLM_RECORD_MODE=true "
            "--cwd apps/cli -- npm run test:llm-integration:record mid-conversation"
        )

        self.assertIsNone(self.analyze(command))

    def test_rejects_malformed_run_check_arguments(self) -> None:
        cases = (
            "~/.agents/scripts/run-check test pytest",
            "~/.agents/scripts/run-check --cwd /tmp -- pytest",
            "~/.agents/scripts/run-check test --cwd -- pytest",
            "~/.agents/scripts/run-check test --env PATH -- pytest",
            "~/.agents/scripts/run-check test --env-file -- pytest",
            "~/.agents/scripts/run-check test --unset-prefix -- pytest",
            "~/.agents/scripts/run-check test --unset-prefix --exclusive -- pytest",
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
    def test_exclusive_queue_cancellation_and_failure_release_across_worktrees(
        self,
    ) -> None:
        # Removing the host-wide lock permits the second validator to start.
        with tempfile.TemporaryDirectory() as temp_dir, ExitStack() as cleanup:
            root = Path(temp_dir)
            first_cwd, second_cwd = root / "first", root / "second"
            first_cwd.mkdir()
            second_cwd.mkdir()
            marker = root / "cancelled-validator-started"

            def stop(process):
                if process.poll() is None:
                    process.terminate()
                process.communicate(timeout=5)

            def start(label, cwd, child):
                process = subprocess.Popen(
                    [
                        str(RUN_CHECK),
                        label,
                        "--exclusive",
                        "--cwd",
                        str(cwd),
                        "--",
                        sys.executable,
                        "-c",
                        child,
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=0,
                    env={**os.environ, "DROID_CHECK_LOG_DIR": str(cwd / "logs")},
                )
                cleanup.callback(stop, process)
                return process

            def line(process):
                self.assertTrue(select.select([process.stdout], [], [], 5)[0])
                result = process.stdout.readline().decode()
                self.assertTrue(result, "runner exited before the expected transition")
                return result

            owner = start(
                "owner",
                first_cwd,
                "import sys; print('owner-running', flush=True); "
                "sys.stdin.read(1); raise SystemExit(7)",
            )
            line(owner)
            self.assertIn("exclusive: waiting", line(owner))
            self.assertIn("exclusive: acquired", line(owner))
            self.assertEqual(line(owner), "owner-running\n")
            with Path(f"/tmp/droid-checks-{os.getuid()}.exclusive.lock").open(
                "a+b"
            ) as slot:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(slot, fcntl.LOCK_EX | fcntl.LOCK_NB)

            queued = start(
                "cancelled",
                second_cwd,
                f"from pathlib import Path; Path({str(marker)!r}).touch()",
            )
            queued_log = Path(line(queued).removeprefix("[run-check] log: ").strip())
            self.assertIn("exclusive: waiting", line(queued))
            queued.terminate()
            queued_output = queued.communicate(timeout=5)[0].decode()
            self.assertEqual(queued.returncode, 143)
            self.assertIn("[run-check] exit: 143", queued_output)
            self.assertIn("[run-check] exit: 143", queued_log.read_text())
            self.assertFalse(marker.exists())

            cheap = subprocess.run(
                [
                    str(RUN_CHECK),
                    "cheap",
                    "--cwd",
                    str(second_cwd),
                    "--",
                    sys.executable,
                    "-c",
                    "print('cheap-ran')",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
                env={**os.environ, "DROID_CHECK_LOG_DIR": str(second_cwd / "logs")},
            )
            self.assertEqual(cheap.returncode, 0)
            self.assertIn("cheap-ran", cheap.stdout)
            self.assertIsNone(owner.poll())

            next_check = start("next", second_cwd, "print('next-ran')")
            line(next_check)
            self.assertIn("exclusive: waiting", line(next_check))
            # A pipe gate makes overlap observable without timing sleeps.
            owner.stdin.write(b"x")
            owner.stdin.flush()
            owner_output = owner.communicate(timeout=5)[0].decode()
            self.assertEqual(owner.returncode, 7)
            self.assertIn("[run-check] exit: 7", owner_output)
            next_output = next_check.communicate(timeout=5)[0].decode()
            self.assertEqual(next_check.returncode, 0)
            self.assertIn("exclusive: acquired", next_output)
            self.assertIn("next-ran", next_output)

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

    def test_loads_env_files_and_drops_prefixed_inherited_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            dotenv = Path(temp_dir) / "probe.env"
            dotenv.write_text('A_PROBE=plain\n# comment\nexport B_PROBE="quoted"\n')
            json_file = Path(temp_dir) / "probe.json"
            json_file.write_text('{"C_PROBE": "json", "DROP_ME_BASE": "from-file"}')
            child = (
                "import os; "
                "print(os.environ['A_PROBE'], os.environ['B_PROBE'], os.environ['C_PROBE'], "
                "os.environ.get('DROP_ME_INHERITED', 'unset'), os.environ['DROP_ME_BASE'], "
                "flush=True)"
            )
            completed = subprocess.run(
                [
                    str(RUN_CHECK),
                    "test",
                    "--unset-prefix",
                    "DROP_ME_",
                    "--env-file",
                    str(dotenv),
                    "--env-file",
                    str(json_file),
                    "--",
                    sys.executable,
                    "-c",
                    child,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env={
                    **os.environ,
                    "DROID_CHECK_LOG_DIR": str(log_dir),
                    "DROP_ME_INHERITED": "leaked",
                },
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout)
            # Inherited DROP_ME_* is removed; a file entry with the same prefix is applied after.
            self.assertIn("plain quoted json unset from-file\n", completed.stdout)

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
        for nested in (False, True):
            with self.subTest(nested=nested), tempfile.TemporaryDirectory() as log_dir:
                self._assert_group_terminated(log_dir, nested)

    def _assert_group_terminated(self, log_dir: str, nested: bool) -> None:
        child = (
            "import os, signal, time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "print(os.getpid(), flush=True); "
            "time.sleep(60)"
        )
        if nested:
            child = (
                "import subprocess, sys; "
                f"subprocess.run([sys.executable, '-c', {child!r}])"
            )
        process = subprocess.Popen(
            [
                str(RUN_CHECK),
                "signal",
                "--exclusive",
                "--",
                sys.executable,
                "-c",
                child,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ, "DROID_CHECK_LOG_DIR": log_dir},
        )
        assert process.stdout is not None

        process.stdout.readline()
        process.stdout.readline()
        process.stdout.readline()
        child_pid = int(process.stdout.readline())
        process.terminate()
        try:
            remaining = process.communicate(timeout=5)[0]
        finally:
            if process.poll() is None:
                os.kill(child_pid, signal.SIGKILL)
                process.communicate(timeout=5)

        self.assertEqual(process.returncode, 143)
        self.assertIn("[run-check] exit: 143\n", remaining)
        state = subprocess.run(
            ["ps", "-p", str(child_pid), "-o", "stat="],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(state.returncode != 0 or state.stdout.strip().startswith("Z"))

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
