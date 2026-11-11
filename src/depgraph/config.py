"""Reading and validating the INI configuration file."""

import configparser
import os
import re
from dataclasses import dataclass

from .errors import ConfigError

SECTION = "settings"
MIN_DEPTH = 1
TRUE_VALUES = {"true", "yes", "1", "on"}
FALSE_VALUES = {"false", "no", "0", "off"}
URL_PREFIXES = ("http://", "https://")
PNG_SUFFIX = ".png"
VERSION_RE = re.compile(r"^\d+(\.\d+){1,3}(-[0-9A-Za-z.-]+)?$")
PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TEST_PACKAGE_RE = re.compile(r"^[A-Z]+$")


@dataclass
class Config:
    """User-defined settings of the tool."""

    package_name: str
    repository: str
    test_mode: bool
    version: str
    output_file: str
    ascii_tree: bool
    max_depth: int


def read_ini(path):
    """Read the INI file and return its settings section."""
    if not os.path.isfile(path):
        raise ConfigError(f"config file not found: {path}")
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, UnicodeDecodeError) as exc:
        raise ConfigError(f"cannot parse config file: {exc}") from exc
    if not parser.has_section(SECTION):
        raise ConfigError(f"section [{SECTION}] is missing")
    return parser[SECTION]


def required(section, key):
    """Return a non-empty value of ``key`` or raise ConfigError."""
    value = section.get(key)
    if value is None or not value.strip():
        raise ConfigError(f"parameter '{key}' is missing or empty")
    return value.strip()


def parse_bool(key, raw):
    """Convert a textual value to bool."""
    value = raw.lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ConfigError(
        f"parameter '{key}' must be true or false, got '{raw}'"
    )


def parse_package_name(raw, test_mode):
    """Validate the package name for the selected mode."""
    pattern = TEST_PACKAGE_RE if test_mode else PACKAGE_RE
    if not pattern.match(raw):
        kind = "capital Latin letters" if test_mode else "a NuGet id"
        raise ConfigError(
            f"parameter 'package_name' must be {kind}, got '{raw}'"
        )
    return raw


def parse_repository(raw, test_mode):
    """Validate the repository URL or the test repository path."""
    if test_mode:
        if not os.path.isfile(raw):
            raise ConfigError(f"test repository file not found: {raw}")
    elif not raw.startswith(URL_PREFIXES):
        raise ConfigError(
            f"parameter 'repository' must be an http(s) URL, got '{raw}'"
        )
    return raw


def parse_version(raw, test_mode):
    """Validate the package version (free-form in test mode)."""
    if not test_mode and not VERSION_RE.match(raw):
        raise ConfigError(
            f"parameter 'version' is not a valid version: '{raw}'"
        )
    return raw


def parse_output_file(raw):
    """Validate the name of the image file."""
    if not raw.lower().endswith(PNG_SUFFIX) or raw.lower() == PNG_SUFFIX:
        raise ConfigError(
            f"parameter 'output_file' must be a *.png file name, got '{raw}'"
        )
    folder = os.path.dirname(raw)
    if folder and not os.path.isdir(folder):
        raise ConfigError(f"output directory does not exist: {folder}")
    return raw


def parse_max_depth(raw):
    """Validate the maximum analysis depth."""
    try:
        depth = int(raw)
    except ValueError:
        raise ConfigError(
            f"parameter 'max_depth' must be an integer, got '{raw}'"
        ) from None
    if depth < MIN_DEPTH:
        raise ConfigError(
            f"parameter 'max_depth' must be >= {MIN_DEPTH}, got {depth}"
        )
    return depth


def load_config(path):
    """Load and validate the configuration from an INI file."""
    section = read_ini(path)
    test_mode = parse_bool("test_mode", required(section, "test_mode"))
    return Config(
        package_name=parse_package_name(
            required(section, "package_name"), test_mode
        ),
        repository=parse_repository(
            required(section, "repository"), test_mode
        ),
        test_mode=test_mode,
        version=parse_version(required(section, "version"), test_mode),
        output_file=parse_output_file(required(section, "output_file")),
        ascii_tree=parse_bool("ascii_tree", required(section, "ascii_tree")),
        max_depth=parse_max_depth(required(section, "max_depth")),
    )


def format_config(config):
    """Return the settings as ``key = value`` lines."""
    return [f"{key} = {value}" for key, value in vars(config).items()]
