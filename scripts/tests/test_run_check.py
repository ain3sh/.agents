import importlib.machinery
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RUN_CHECK = Path(__file__).resolve().parents[1] / "run-check"
loader = importlib.machinery.SourceFileLoader("run_check", str(RUN_CHECK))
spec = importlib.util.spec_from_loader("run_check", loader)
run_check = importlib.util.module_from_spec(spec)
sys.modules["run_check"] = run_check
loader.exec_module(run_check)

GIB = run_check.GIB
HOST = 8 * GIB


class CheckMemoryTest(unittest.TestCase):
    def memory(self, limits: dict[str, str]) -> int:
        def read_text(path: Path) -> str:
            if str(path) not in limits:
                raise FileNotFoundError(path)
            return limits[str(path)] + "\n"

        sysconf = {"SC_PAGE_SIZE": 4096, "SC_PHYS_PAGES": HOST // 4096}
        with (
            mock.patch.object(run_check.os, "sysconf", sysconf.__getitem__),
            mock.patch.object(Path, "read_text", read_text),
        ):
            return run_check._check_memory()

    def test_host_memory_without_a_cgroup(self) -> None:
        self.assertEqual(self.memory({}), HOST)

    def test_an_unset_cgroup_limit_leaves_host_memory(self) -> None:
        v1 = str(2**63 - 4096)
        self.assertEqual(
            self.memory(
                {
                    "/proc/self/cgroup": "0::/system.slice/tools",
                    "/sys/fs/cgroup/system.slice/tools/memory.max": "max",
                    "/sys/fs/cgroup/system.slice/memory.max": "max",
                }
            ),
            HOST,
        )
        self.assertEqual(
            self.memory(
                {
                    "/proc/self/cgroup": "4:memory:/",
                    "/sys/fs/cgroup/memory/memory.limit_in_bytes": v1,
                }
            ),
            HOST,
        )

    def test_the_root_cgroup_limit_binds(self) -> None:
        limit = str(4 * GIB)
        self.assertEqual(
            self.memory(
                {"/proc/self/cgroup": "0::/", "/sys/fs/cgroup/memory.max": limit}
            ),
            4 * GIB,
        )

    def test_the_nested_cgroup_of_this_process_binds(self) -> None:
        tools = str(6_554_804_224)
        self.assertEqual(
            self.memory(
                {
                    "/proc/self/cgroup": "0::/system.slice/factoryd.service/tools",
                    "/sys/fs/cgroup/system.slice/factoryd.service/tools/memory.max": tools,
                    "/sys/fs/cgroup/system.slice/factoryd.service/memory.max": "max",
                    "/sys/fs/cgroup/memory.max": "max",
                }
            ),
            int(tools),
        )

    def test_the_tightest_ancestor_binds(self) -> None:
        self.assertEqual(
            self.memory(
                {
                    "/proc/self/cgroup": "0::/a/b",
                    "/sys/fs/cgroup/a/b/memory.max": str(6 * GIB),
                    "/sys/fs/cgroup/a/memory.max": str(3 * GIB),
                }
            ),
            3 * GIB,
        )

    def test_a_v1_memory_hierarchy_binds(self) -> None:
        self.assertEqual(
            self.memory(
                {
                    "/proc/self/cgroup": "5:cpu,cpuacct:/x\n4:memory:/docker/abc",
                    "/sys/fs/cgroup/memory/docker/abc/memory.limit_in_bytes": str(
                        2 * GIB
                    ),
                }
            ),
            2 * GIB,
        )


class ChildEnvTest(unittest.TestCase):
    INHERITED = {
        "GH_TOKEN": "gh",
        "CONJURE_SERVER": "conjure",
        "JFROG_USERNAME": "jfrog",
        "OPENAI_API_KEY": "key",
        "aws_secret": "secret",
        "DB_PASSWORD": "password",
        "PGPASSWORD": "pg",
        "npm_config__authToken": "npm",
        "MONKEY": "not a credential",
        "PATH": "/bin",
        "FACTORY_ENV": "prod",
        "__ORIGINAL_FACTORY_API_KEY__": "original",
    }

    def child_env(self, *flags: str) -> tuple[dict[str, str], list[str]]:
        options = run_check._parse(["test", *flags, "--", "true"])
        return run_check._child_env(options, dict(self.INHERITED))

    def refusal(self, *flags: str) -> str:
        stderr = io.StringIO()
        with mock.patch.object(sys, "stderr", stderr), self.assertRaises(SystemExit) as exit_:
            run_check._parse(["test", *flags, "--", "true"])
        self.assertEqual(exit_.exception.code, 64)
        return stderr.getvalue()

    def test_strips_every_inherited_credential_by_default(self) -> None:
        env, stripped = self.child_env()
        self.assertEqual(env, {"MONKEY": "not a credential", "PATH": "/bin", "FACTORY_ENV": "prod"})
        self.assertEqual(
            stripped,
            [
                "CONJURE_SERVER",
                "DB_PASSWORD",
                "GH_TOKEN",
                "JFROG_USERNAME",
                "OPENAI_API_KEY",
                "PGPASSWORD",
                "__ORIGINAL_FACTORY_API_KEY__",
                "aws_secret",
                "npm_config__authToken",
            ],
        )

    def test_keep_env_keeps_one_inherited_credential(self) -> None:
        env, stripped = self.child_env("--keep-env", "GH_TOKEN")
        self.assertEqual(env["GH_TOKEN"], "gh")
        self.assertNotIn("GH_TOKEN", stripped)

    def test_explicit_env_replaces_the_inherited_value_and_is_not_listed(self) -> None:
        env, stripped = self.child_env("--env", "OPENAI_API_KEY=mock")
        self.assertEqual(env["OPENAI_API_KEY"], "mock")
        self.assertNotIn("OPENAI_API_KEY", stripped)

    def test_unset_prefix_still_drops_its_names(self) -> None:
        env, _stripped = self.child_env("--unset-prefix", "FACTORY_")
        self.assertNotIn("FACTORY_ENV", env)

    def test_keep_env_refuses_a_keep_that_keeps_nothing(self) -> None:
        for flags, reason in (
            (("--keep-env", "gh_token"), "not in the inherited environment"),
            (("--keep-env", "NPM_TOKEN"), "not in the inherited environment"),
            (("--unset-prefix", "GH_", "--keep-env", "GH_TOKEN"), "--unset-prefix also drops it"),
        ):
            with self.subTest(flags=flags), self.assertRaisesRegex(ValueError, reason):
                self.child_env(*flags)

    def test_keep_env_names_what_it_refuses(self) -> None:
        self.assertIn("--keep-env PATH: run-check never strips this name", self.refusal("--keep-env", "PATH"))
        self.assertIn("--keep-env takes one variable name", self.refusal("--keep-env", "BAD-NAME_TOKEN"))

    def test_names_that_are_not_identifiers_are_counted_not_printed(self) -> None:
        self.assertEqual(
            run_check._render_names(["GH_TOKEN", "CONJURE_\n[run-check] exit: 0", "ODD\udcff_TOKEN"]),
            "GH_TOKEN, and 2 names that are not shell identifiers",
        )
        self.assertEqual(
            run_check._render_names(["GH_TOKEN", "ODD\udcff_TOKEN"]),
            "GH_TOKEN, and 1 name that is not a shell identifier",
        )


class EnvFileErrorTest(unittest.TestCase):
    def test_errors_name_the_line_not_its_text(self) -> None:
        cases = (
            "A=1\nghp_FAKESENTINEL trailing\n",
            "A=1\nghp-FAKESENTINEL=value\n",
            '{"A": "1", "ghp-FAKESENTINEL": "value"}',
        )
        for text in cases:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "probe.env"
                path.write_text(text)
                with self.assertRaises(OSError) as error:
                    run_check._read_env_file(str(path))
                self.assertNotIn("FAKESENTINEL", str(error.exception))
                self.assertRegex(str(error.exception), r"(line|entry) 2")

    def test_a_value_the_environment_cannot_hold_names_its_line(self) -> None:
        for text, reason in (
            ("A=1\nB=FAKESENTINEL\0tail\n", "line 2: value holds a NUL byte"),
            ('{"A": "1", "B": "FAKESENTINEL\\u0000"}', "entry 2: value holds a NUL byte"),
            ('{"A": "1", "B": "FAKESENTINEL\\ud800"}', "entry 2: value is not encodable text"),
        ):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "probe.env"
                path.write_text(text)
                with self.assertRaises(OSError) as error:
                    run_check._read_env_file(str(path))
                self.assertIn(reason, str(error.exception))
                self.assertNotIn("FAKESENTINEL", str(error.exception))

@unittest.skipUnless(sys.platform == "linux", "user and mount namespaces are Linux's")
class HideTest(unittest.TestCase):
    def run_hidden(self, path: Path, script: str) -> str:
        return subprocess.run(
            ["sh", "-c", script],
            preexec_fn=run_check._hide((path,)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        ).stdout

    def test_the_child_reads_an_empty_file_as_itself(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment"
            path.write_text("GH_TOKEN=FAKESENTINEL\n")
            out = self.run_hidden(path, f"wc -c < {path}; id -u; id -g")
            self.assertEqual(out.split(), ["0", str(os.getuid()), str(os.getgid())])
            self.assertEqual(path.read_text(), "GH_TOKEN=FAKESENTINEL\n")

    def test_the_child_cannot_read_its_parents_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment"
            path.write_text("")
            out = self.run_hidden(path, "cat /proc/$PPID/environ >/dev/null 2>&1 && echo read || echo refused")
            self.assertEqual(out, "refused\n")

    def test_nothing_to_hide_adds_no_step(self) -> None:
        self.assertIsNone(run_check._hide(()))


class ExclusiveSlotsTest(unittest.TestCase):
    def test_one_heavy_check_under_12_gib(self) -> None:
        self.assertEqual(run_check._exclusive_slots(8 * GIB), 1)
        self.assertEqual(run_check._exclusive_slots(12 * GIB - 1), 1)

    def test_two_heavy_checks_from_12_gib(self) -> None:
        self.assertEqual(run_check._exclusive_slots(12 * GIB), 2)
        self.assertEqual(run_check._exclusive_slots(64 * GIB), 2)

    def test_one_lock_path_per_slot(self) -> None:
        self.assertEqual(len(run_check.EXCLUSIVE_LOCK_PATHS), run_check.EXCLUSIVE_SLOTS)


if __name__ == "__main__":
    unittest.main()
