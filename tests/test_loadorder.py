"""Tests for the load order and cycle detection."""

import unittest

from depgraph.graph import build_graph
from depgraph.loadorder import find_cycle_edges, load_order
from depgraph.testrepo import FileSource, parse_repository


def make(text, root="A", depth=10):
    """Build a graph from a test repository text."""
    source = FileSource(parse_repository(text))
    return build_graph(source, root, depth)


class LoadOrderTestCase(unittest.TestCase):
    """Dependencies must be loaded before dependents."""

    def test_chain(self):
        """A chain is loaded from the leaf to the root."""
        self.assertEqual(load_order(make("A: B\nB: C\nC:")), ["C", "B", "A"])

    def test_shared(self):
        """A shared dependency is loaded once, before its users."""
        graph = make("A: B C\nB: D\nC: D\nD:")
        self.assertEqual(load_order(graph), ["D", "B", "C", "A"])

    def test_every_dependency_first(self):
        """For acyclic graphs each edge goes forward in the order."""
        graph = make("A: B C\nB: D\nC: D E\nD:\nE:")
        order = load_order(graph)
        for name, deps in graph.edges.items():
            for dep in deps:
                self.assertLess(order.index(dep), order.index(name))

    def test_cycle(self):
        """A cycle still gives every package exactly once."""
        graph = make("A: B\nB: C\nC: A")
        self.assertEqual(sorted(load_order(graph)), ["A", "B", "C"])
        self.assertEqual(find_cycle_edges(graph), [("C", "A")])

    def test_no_cycle(self):
        """An acyclic graph has no back edges."""
        self.assertEqual(find_cycle_edges(make("A: B\nB:")), [])


if __name__ == "__main__":
    unittest.main()
