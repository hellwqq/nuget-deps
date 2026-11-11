"""End-to-end tests of the command line interface."""

import contextlib
import io
import os
import shutil
import unittest

from depgraph.cli import EXIT_ERROR, EXIT_OK, main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*args):
    """Run main() and return ``(exit_code, stdout, stderr)``."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


def example(name):
    """Return the path of an example config."""
    return os.path.join(ROOT, "examples", name)


HAS_DOT = shutil.which("dot") is not None


@unittest.skipUnless(HAS_DOT, "Graphviz is not installed")
class CliTestCase(unittest.TestCase):
    """Runs the tool on the example test repositories."""

    def use_repo_root(self):
        """Run from the repository root so example paths resolve."""
        previous = os.getcwd()
        os.chdir(ROOT)
        self.addCleanup(os.chdir, previous)

    def test_simple(self):
        """The simple example prints its edges."""
        self.use_repo_root()
        code, out, _ = run_cli("-c", example("simple.ini"), "--edges")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("C -> D E", out)
        self.assertIn("`-- C", out)

    def test_cycle(self):
        """The cyclic example finishes."""
        self.use_repo_root()
        code, out, _ = run_cli("-c", example("cycle.ini"), "--edges")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("C -> A D", out)
        self.assertIn("(cycle)", out)

    def test_direct(self):
        """--direct prints only direct dependencies."""
        self.use_repo_root()
        code, out, _ = run_cli("-c", example("simple.ini"), "--direct")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.split(), ["B", "C"])

    def test_load_order(self):
        """--load-order prints dependencies before dependents."""
        self.use_repo_root()
        code, out, _ = run_cli("-c", example("diamond.ini"), "--load-order")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(
            [line.split()[1] for line in out.splitlines()],
            ["F", "E", "D", "B", "C", "A"],
        )

    def test_png_created(self):
        """A PNG file is produced next to the DOT file."""
        self.use_repo_root()
        run_cli("-c", example("diamond.ini"))
        for suffix in (".png", ".dot"):
            self.assertTrue(os.path.isfile(example("diamond" + suffix)))

    def test_error_exit_code(self):
        """Errors give exit code 1 and a message on stderr."""
        self.use_repo_root()
        code, _, err = run_cli("-c", "missing.ini")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("error:", err)


if __name__ == "__main__":
    unittest.main()
