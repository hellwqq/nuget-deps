"""Tests for the test repository file format."""

import unittest

from depgraph.errors import RepositoryError
from depgraph.testrepo import FileSource, parse_repository


class TestRepositoryTestCase(unittest.TestCase):
    """Checks parsing of the test repository description."""

    def test_parse(self):
        """Lines, comments and blank lines are handled."""
        text = "# comment\nA: B C\n\nB:\nC: B\n"
        self.assertEqual(
            parse_repository(text), {"A": ["B", "C"], "B": [], "C": ["B"]}
        )

    def test_errors(self):
        """Malformed descriptions are rejected."""
        for text in ("A B", "a: B", "A: b", "A:\nA: B", ": B"):
            with self.subTest(text=text):
                with self.assertRaises(RepositoryError):
                    parse_repository(text)

    def test_source(self):
        """Unknown packages are leaves."""
        source = FileSource({"A": ["B"]})
        self.assertEqual(source.dependencies("A"), ["B"])
        self.assertEqual(source.dependencies("B"), [])


if __name__ == "__main__":
    unittest.main()
