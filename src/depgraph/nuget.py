"""Collecting dependency data from a NuGet (.NET) repository.

Only the standard library is used: the NuGet V3 service index is read
to find the package content endpoint, then the ``.nuspec`` manifest of
the requested package version is downloaded and parsed.
"""

import json
import urllib.error
import urllib.request
from xml.etree import ElementTree

from .errors import RepositoryError

PACKAGE_BASE = "PackageBaseAddress"
TIMEOUT_SECONDS = 30
MIN_VERSION_PARTS = 3


def http_get(url):
    """Download ``url`` and return the response body as bytes."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as reply:
            return reply.read()
    except urllib.error.HTTPError as exc:
        raise RepositoryError(f"HTTP {exc.code} for {url}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RepositoryError(f"cannot reach {url}: {exc}") from exc


def find_package_base(index_url, fetch=http_get):
    """Return the package content URL from the V3 service index."""
    try:
        index = json.loads(fetch(index_url))
        resources = index["resources"]
    except (ValueError, KeyError, TypeError) as exc:
        raise RepositoryError(
            f"{index_url} is not a NuGet V3 service index"
        ) from exc
    for resource in resources:
        kind = str(resource.get("@type", ""))
        if kind.startswith(PACKAGE_BASE):
            return resource["@id"].rstrip("/")
    raise RepositoryError("service index has no PackageBaseAddress")


def normalize_version(version):
    """Convert a version to the normalized NuGet form (1.0 -> 1.0.0)."""
    core, dash, suffix = version.partition("-")
    core = core.split("+")[0]
    try:
        numbers = [int(part) for part in core.split(".")]
    except ValueError:
        raise RepositoryError(f"invalid version '{version}'") from None
    while len(numbers) < MIN_VERSION_PARTS:
        numbers.append(0)
    while len(numbers) > MIN_VERSION_PARTS and not numbers[-1]:
        numbers.pop()
    text = ".".join(str(number) for number in numbers)
    return text + dash + suffix.split("+")[0]


def lower_bound(version_range):
    """Return the minimal version of a NuGet version range."""
    cleaned = version_range.strip().strip("[]()")
    for part in cleaned.split(","):
        if part.strip():
            return part.strip()
    return ""


def local_name(tag):
    """Strip the XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1]


def parse_dependencies(data):
    """Return ``[(id, version_range)]`` found in a .nuspec document."""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise RepositoryError(f"invalid .nuspec document: {exc}") from exc
    found = {}
    for element in root.iter():
        dep_id = element.get("id")
        if local_name(element.tag) == "dependency" and dep_id:
            found.setdefault(dep_id, element.get("version", ""))
    return list(found.items())


class NuGetSource:
    """Dependency source that reads a real NuGet repository."""

    def __init__(self, index_url, root, version, fetch=http_get):
        """Connect to the repository and remember the root version."""
        self.fetch = fetch
        self.base = find_package_base(index_url, fetch)
        self.versions = {root: version}

    def nuspec_url(self, name):
        """Return the URL of the manifest of ``name``."""
        key = name.lower()
        version = normalize_version(self.versions[name]).lower()
        return f"{self.base}/{key}/{version}/{key}.nuspec"

    def dependencies(self, name):
        """Return the names of direct dependencies of ``name``."""
        try:
            data = self.fetch(self.nuspec_url(name))
        except RepositoryError as exc:
            raise RepositoryError(
                f"package {name} {self.versions[name]}: {exc}"
            ) from exc
        names = []
        for dep_id, dep_range in parse_dependencies(data):
            version = lower_bound(dep_range)
            if not version:
                raise RepositoryError(
                    f"dependency {dep_id} of {name} has no version"
                )
            self.versions.setdefault(dep_id, version)
            names.append(dep_id)
        return names
