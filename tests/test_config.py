"""Tests for configuration loading and error handling."""

import os
import tempfile
import unittest

from depgraph.config import load_config
from depgraph.errors import ConfigError

BASE = {
    "package_name": "Newtonsoft.Json",
    "repository": "https://api.nuget.org/v3/index.json",
    "test_mode": "false",
    "version": "13.0.3",
    "output_file": "graph.png",
    "ascii_tree": "true",
    "max_depth": "3",
}


class ConfigTestCase(unittest.TestCase):
    """Checks every parameter of the INI file."""

    def setUp(self):
        """Create a temporary folder for config files."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, **changes):
        """Write an INI file with ``changes`` applied to the defaults."""
        values = dict(BASE, **changes)
        path = os.path.join(self.tmp.name, "config.ini")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("[settings]\n")
            for key, value in values.items():
                if value is not None:
                    handle.write(f"{key} = {value}\n")
        return path

    def test_valid_config(self):
        """A correct file is loaded without errors."""
        config = load_config(self.write())
        self.assertEqual(config.package_name, "Newtonsoft.Json")
        self.assertEqual(config.max_depth, 3)
        self.assertTrue(config.ascii_tree)
        self.assertFalse(config.test_mode)

    def test_missing_file(self):
        """A missing config file is reported."""
        with self.assertRaises(ConfigError):
            load_config(os.path.join(self.tmp.name, "nope.ini"))

    def test_missing_section(self):
        """A file without the [settings] section is rejected."""
        path = os.path.join(self.tmp.name, "bad.ini")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("package_name = x\n")
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_missing_parameters(self):
        """Each parameter is mandatory."""
        for key in BASE:
            with self.subTest(key=key):
                with self.assertRaises(ConfigError):
                    load_config(self.write(**{key: None}))

    def test_invalid_values(self):
        """Wrong values of every parameter are rejected."""
        bad = {
            "package_name": "bad name!",
            "repository": "ftp://example.org",
            "test_mode": "maybe",
            "version": "abc",
            "output_file": "graph.jpg",
            "ascii_tree": "2",
            "max_depth": "0",
        }
        for key, value in bad.items():
            with self.subTest(key=key):
                with self.assertRaises(ConfigError):
                    load_config(self.write(**{key: value}))

    def test_depth_not_integer(self):
        """A non-numeric depth is rejected."""
        with self.assertRaises(ConfigError):
            load_config(self.write(max_depth="deep"))

    def test_output_directory_missing(self):
        """The folder of the output file must exist."""
        with self.assertRaises(ConfigError):
            load_config(self.write(output_file="no/such/dir/g.png"))

    def test_test_mode_requires_file(self):
        """In test mode the repository must be an existing file."""
        with self.assertRaises(ConfigError):
            load_config(
                self.write(test_mode="true", package_name="A",
                           repository="missing.txt")
            )

    def test_test_mode_package_name(self):
        """In test mode package names are capital Latin letters."""
        path = os.path.join(self.tmp.name, "repo.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("A:\n")
        with self.assertRaises(ConfigError):
            load_config(
                self.write(test_mode="true", package_name="a",
                           repository=path)
            )


if __name__ == "__main__":
    unittest.main()
