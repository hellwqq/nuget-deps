"""Command line interface of the tool (stage 5)."""

import argparse
import sys

from .config import format_config, load_config
from .errors import DepGraphError, RepositoryError
from .graph import build_graph, format_edges
from .loadorder import find_cycle_edges, load_order
from .nuget import NuGetSource
from .testrepo import FileSource, load_test_repository
from .visualize import ascii_tree, dot_path, save_visualization

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
    parser.add_argument(
        "--load-order", action="store_true",
        help="print the order in which dependencies are loaded",
    )
    parser.add_argument(
        "--edges", action="store_true",
        help="print the graph as 'package -> dependencies' lines",
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


def print_load_order(graph):
    """Print the load order and warn about dependency cycles."""
    for position, name in enumerate(load_order(graph), start=1):
        print(f"{position}. {name}")
    for source_name, target in find_cycle_edges(graph):
        print(f"warning: cycle {source_name} -> {target}", file=sys.stderr)


def visualize(graph, config):
    """Print the ASCII tree if enabled and save DOT and PNG files."""
    if config.ascii_tree:
        print(ascii_tree(graph))
    save_visualization(graph, config.output_file)
    print(f"graph saved: {config.output_file}, {dot_path(config.output_file)}")


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
    if args.load_order:
        print_load_order(graph)
        return
    if args.edges:
        print("\n".join(format_edges(graph)))
    visualize(graph, config)


def main(argv=None):
    """Program entry point; returns the process exit code."""
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except DepGraphError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
