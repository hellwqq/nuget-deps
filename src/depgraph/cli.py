"""Command line interface of the tool (stage 3)."""

import argparse
import sys

from .config import format_config, load_config
from .errors import DepGraphError, RepositoryError
from .graph import build_graph, format_edges
from .nuget import NuGetSource
from .testrepo import FileSource, load_test_repository

EXIT_OK = 0
EXIT_ERROR = 1


def build_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="NuGet dependency graph visualizer.",
    )
    parser.add_argument(
        "-c", "--config", default="config.ini",
        help="path to the INI configuration file (default: config.ini)",
    )
    parser.add_argument(
        "--show-config", action="store_true",
        help="print all user parameters as key = value",
    )
    parser.add_argument(
        "--direct", action="store_true",
        help="print only direct dependencies of the package",
    )
    return parser


def make_source(config):
    """Create the dependency source for the selected mode."""
    if config.test_mode:
        packages = load_test_repository(config.repository)
        if config.package_name not in packages:
            raise RepositoryError(
                f"package {config.package_name} is not in the test repository"
            )
        return FileSource(packages)
    return NuGetSource(
        config.repository, config.package_name, config.version
    )


def print_direct(source, name):
    """Print the direct dependencies of ``name``."""
    for dep in source.dependencies(name):
        print(f"{dep} {source.versions.get(dep, '')}".strip())


def run(args):
    """Execute the tool for already parsed arguments."""
    config = load_config(args.config)
    if args.show_config:
        print("\n".join(format_config(config)))
    source = make_source(config)
    if args.direct:
        print_direct(source, config.package_name)
        return
    graph = build_graph(source, config.package_name, config.max_depth)
    print("\n".join(format_edges(graph)))


def main(argv=None):
    """Program entry point; returns the process exit code."""
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
