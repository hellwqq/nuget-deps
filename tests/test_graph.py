"""Tests for the BFS graph builder."""

import unittest

from depgraph.graph import build_graph, format_edges
from depgraph.testrepo import FileSource, parse_repository


def make(text, root, depth):
    """Build a graph from a test repository text."""
    source = FileSource(parse_repository(text))
    return build_graph(source, root, depth)


class GraphTestCase(unittest.TestCase):
    """Checks transitivity, depth limit and cycles."""

    def test_transitive(self):
        """Transitive dependencies are included."""
        graph = make("A: B\nB: C\nC:", "A", 5)
        self.assertEqual(graph.nodes(), ["A", "B", "C"])

    def test_depth_limit(self):
        """Packages deeper than max_depth are not expanded."""
        graph = make("A: B\nB: C\nC: D\nD:", "A", 2)
        self.assertEqual(graph.nodes(), ["A", "B", "C"])
        self.assertNotIn("C", graph.edges)

    def test_depth_one(self):
        """Depth 1 gives only direct dependencies."""
        graph = make("A: B C\nB: D\nC:\nD:", "A", 1)
        self.assertEqual(graph.nodes(), ["A", "B", "C"])

    def test_cycle(self):
        """A cycle does not hang and its edge is kept."""
        graph = make("A: B\nB: A", "A", 10)
        self.assertEqual(graph.nodes(), ["A", "B"])
        self.assertEqual(graph.edges["B"], ["A"])

    def test_self_dependency(self):
        """A package that depends on itself is handled."""
        graph = make("A: A", "A", 10)
        self.assertEqual(graph.edges["A"], ["A"])

    def test_shared_dependency(self):
        """A shared dependency is a single node."""
        graph = make("A: B C\nB: D\nC: D\nD:", "A", 5)
        self.assertEqual(graph.nodes(), ["A", "B", "C", "D"])

    def test_bfs_order(self):
        """Nodes are discovered level by level."""
        graph = make("A: B C\nB: D\nC: E\nD:\nE:", "A", 5)
        self.assertEqual(graph.nodes(), ["A", "B", "C", "D", "E"])

    def test_format_edges(self):
        """Edges are printed one package per line."""
        graph = make("A: B\nB:", "A", 5)
        self.assertEqual(format_edges(graph), ["A -> B", "B -> -"])


if __name__ == "__main__":
    unittest.main()
