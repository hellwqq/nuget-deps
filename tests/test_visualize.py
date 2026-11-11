"""Tests for the ASCII tree and Graphviz output."""

import unittest

from depgraph.graph import build_graph
from depgraph.testrepo import FileSource, parse_repository
from depgraph.visualize import ascii_tree, quote, to_dot


def make(text, root="A", depth=10):
    """Build a graph from a test repository text."""
    source = FileSource(parse_repository(text))
    return build_graph(source, root, depth)


class VisualizeTestCase(unittest.TestCase):
    """Checks the textual representations of a graph."""

    def test_ascii_tree(self):
        """The tree uses ASCII branches."""
        graph = make("A: B C\nB: D\nC:\nD:")
        expected = "A\n|-- B\n|   `-- D\n`-- C"
        self.assertEqual(ascii_tree(graph), expected)

    def test_tree_marks_cycle(self):
        """A back edge is marked and not expanded."""
        graph = make("A: B\nB: A")
        self.assertEqual(ascii_tree(graph), "A\n`-- B\n    `-- A (cycle)")

    def test_tree_marks_repeats(self):
        """A subtree that was already printed is not repeated."""
        graph = make("A: B C\nB: D\nC: D\nD: E\nE:")
        self.assertIn("D (*)", ascii_tree(graph))

    def test_single_package(self):
        """A single package gives a one-line tree."""
        self.assertEqual(ascii_tree(make("A:")), "A")

    def test_dot(self):
        """DOT text lists edges and isolated nodes."""
        dot = to_dot(make("A: B\nB:"))
        self.assertIn('digraph "A" {', dot)
        self.assertIn('"A" -> "B";', dot)
        self.assertIn('    "B";', dot)
        self.assertTrue(dot.rstrip().endswith("}"))

    def test_quote(self):
        """Quotes inside names are escaped."""
        self.assertEqual(quote('a"b'), '"a\\"b"')


if __name__ == "__main__":
    unittest.main()
