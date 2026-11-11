"""Command line interface of the tool (stage 2)."""

import argparse
import sys

from .config import format_config, load_config
from .errors import DepGraphError
from .nuget import NuGetSource

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
    return parser


def print_direct(source, name):
    """Print the direct dependencies of ``name``."""
    for dep in source.dependencies(name):
        print(f"{dep} {source.versions[dep]}")


def run(args):
    """Execute the tool for already parsed arguments."""
    config = load_config(args.config)
    if args.show_config:
        print("\n".join(format_config(config)))
    source = NuGetSource(
        config.repository, config.package_name, config.version
    )
    print_direct(source, config.package_name)


def main(argv=None):
    """Program entry point; returns the process exit code."""
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
