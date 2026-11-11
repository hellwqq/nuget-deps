"""Exceptions used by the dependency graph tool."""


class DepGraphError(Exception):
    """Base class for all expected errors of the tool."""


class ConfigError(DepGraphError):
    """Raised when the configuration file is missing or invalid."""


class RepositoryError(DepGraphError):
    """Raised when package data cannot be fetched or parsed."""
