"""Tests for NuGet data collection with a fake HTTP layer."""

import json
import unittest

from depgraph.errors import RepositoryError
from depgraph.nuget import (
    NuGetSource,
    find_package_base,
    lower_bound,
    normalize_version,
    parse_dependencies,
)

INDEX = "https://example.org/v3/index.json"
BASE = "https://example.org/flat"
NUSPEC = b"""<?xml version="1.0"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Root.Pkg</id>
    <dependencies>
      <group targetFramework=".NETStandard2.0">
        <dependency id="Dep.One" version="[1.0, )" />
        <dependency id="Dep.Two" version="2.1" />
      </group>
      <group targetFramework="net6.0">
        <dependency id="Dep.One" version="1.0.0" />
      </group>
    </dependencies>
  </metadata>
</package>"""


def fake_fetch(url):
    """Return canned responses of a fake repository."""
    if url == INDEX:
        resources = [
            {"@id": "x", "@type": "SearchQueryService"},
            {"@id": BASE + "/", "@type": "PackageBaseAddress/3.0.0"},
        ]
        return json.dumps({"resources": resources}).encode()
    if url == f"{BASE}/root.pkg/1.2.3/root.pkg.nuspec":
        return NUSPEC
    raise RepositoryError(f"HTTP 404 for {url}")


class NuGetTestCase(unittest.TestCase):
    """Checks parsing helpers and the NuGet source."""

    def test_find_package_base(self):
        """The content endpoint is found in the service index."""
        self.assertEqual(find_package_base(INDEX, fake_fetch), BASE)

    def test_bad_index(self):
        """A non-JSON index is reported as a repository error."""
        with self.assertRaises(RepositoryError):
            find_package_base(INDEX, lambda url: b"<html/>")

    def test_normalize_version(self):
        """Versions are normalized like NuGet does."""
        self.assertEqual(normalize_version("1.0"), "1.0.0")
        self.assertEqual(normalize_version("1.2.3.0"), "1.2.3")
        self.assertEqual(normalize_version("1.0.0-Beta"), "1.0.0-Beta")
        with self.assertRaises(RepositoryError):
            normalize_version("x.y")

    def test_lower_bound(self):
        """The lower bound of a range is its minimal version."""
        self.assertEqual(lower_bound("[1.0, )"), "1.0")
        self.assertEqual(lower_bound("2.1"), "2.1")
        self.assertEqual(lower_bound("[1.0,2.0)"), "1.0")
        self.assertEqual(lower_bound(""), "")

    def test_parse_dependencies(self):
        """Dependencies of all groups are merged without duplicates."""
        deps = parse_dependencies(NUSPEC)
        self.assertEqual(
            deps, [("Dep.One", "[1.0, )"), ("Dep.Two", "2.1")]
        )

    def test_source_dependencies(self):
        """The source returns direct dependencies with versions."""
        source = NuGetSource(INDEX, "Root.Pkg", "1.2.3", fake_fetch)
        self.assertEqual(
            source.dependencies("Root.Pkg"), ["Dep.One", "Dep.Two"]
        )
        self.assertEqual(source.versions["Dep.One"], "1.0")

    def test_unknown_package(self):
        """A missing package gives a readable error."""
        source = NuGetSource(INDEX, "Root.Pkg", "9.9.9", fake_fetch)
        with self.assertRaises(RepositoryError):
            source.dependencies("Root.Pkg")


if __name__ == "__main__":
    unittest.main()
