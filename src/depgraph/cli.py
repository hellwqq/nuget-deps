"""Command line interface of the tool (stage 1)."""

import argparse
import sys

from .config import format_config, load_config
from .errors import DepGraphError

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
    return parser


def run(args):
    """Execute the tool for already parsed arguments."""
    config = load_config(args.config)
    for line in format_config(config):
        print(line)


def main(argv=None):
    """Program entry point; returns the process exit code."""
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
