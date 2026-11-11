"""Test repository: packages are described in a plain text file.

Each line has the form ``A: B C`` meaning that package ``A`` directly
depends on ``B`` and ``C``. Package names are capital Latin letters.
Blank lines and lines starting with ``#`` are ignored.
"""

import re

from .errors import RepositoryError

NAME_RE = re.compile(r"^[A-Z]+$")
SEPARATOR = ":"
COMMENT = "#"


def check_name(name, number):
    """Make sure ``name`` is made of capital Latin letters."""
    if not NAME_RE.match(name):
        raise RepositoryError(
            f"line {number}: bad package name '{name}'"
        )


def parse_line(line, number):
    """Parse ``A: B C`` into ``("A", ["B", "C"])``."""
    name, separator, rest = line.partition(SEPARATOR)
    if not separator:
        raise RepositoryError(f"line {number}: expected '{SEPARATOR}'")
    name = name.strip()
    deps = rest.split()
    check_name(name, number)
    for dep in deps:
        check_name(dep, number)
    return name, deps


def parse_repository(text):
    """Parse the whole description into ``{package: [dependencies]}``."""
    packages = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT):
            continue
        name, deps = parse_line(line, number)
        if name in packages:
            raise RepositoryError(
                f"line {number}: package '{name}' is described twice"
            )
        packages[name] = deps
    return packages


def load_test_repository(path):
    """Read and parse a test repository file."""
    try:
        with open(path, encoding="utf-8") as handle:
            return parse_repository(handle.read())
    except (OSError, UnicodeDecodeError) as exc:
        raise RepositoryError(f"cannot read {path}: {exc}") from exc


class FileSource:
    """Dependency source backed by a test repository."""

    def __init__(self, packages):
        """Keep the parsed packages; the test mode has no versions."""
        self.packages = packages
        self.versions = {}

    def dependencies(self, name):
        """Return direct dependencies; unknown packages have none."""
        return list(self.packages.get(name, []))
