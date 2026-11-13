import importlib.machinery
import importlib.util
import sys
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
        "PATH": "/bin",
        "FACTORY_ENV": "prod",
    }

    def child_env(self, *flags: str) -> tuple[dict[str, str], list[str]]:
        options = run_check._parse(["test", *flags, "--", "true"])
        return run_check._child_env(options, dict(self.INHERITED))

    def test_strips_every_inherited_credential_by_default(self) -> None:
        env, stripped = self.child_env()
        self.assertEqual(env, {"PATH": "/bin", "FACTORY_ENV": "prod"})
        self.assertEqual(
            stripped,
            [
                "CONJURE_SERVER",
                "DB_PASSWORD",
                "GH_TOKEN",
                "JFROG_USERNAME",
                "OPENAI_API_KEY",
                "aws_secret",
            ],
        )

    def test_keep_env_keeps_one_inherited_credential(self) -> None:
        env, stripped = self.child_env("--keep-env", "GH_TOKEN")
        self.assertEqual(env["GH_TOKEN"], "gh")
        self.assertNotIn("GH_TOKEN", stripped)

    def test_explicit_env_applies_after_the_strip(self) -> None:
        env, stripped = self.child_env("--env", "OPENAI_API_KEY=mock")
        self.assertEqual(env["OPENAI_API_KEY"], "mock")
        self.assertIn("OPENAI_API_KEY", stripped)

    def test_unset_prefix_still_drops_its_names(self) -> None:
        env, _stripped = self.child_env("--unset-prefix", "FACTORY_")
        self.assertNotIn("FACTORY_ENV", env)

    def test_keep_env_refuses_a_name_that_is_never_stripped(self) -> None:
        with mock.patch.object(sys, "stderr"), self.assertRaises(SystemExit) as exit_:
            run_check._parse(["test", "--keep-env", "PATH", "--", "true"])
        self.assertEqual(exit_.exception.code, 64)


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
