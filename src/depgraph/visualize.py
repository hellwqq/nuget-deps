"""Graph visualization: ASCII tree, Graphviz text and PNG image."""

import os
import subprocess

from .errors import DepGraphError

BRANCH = "|-- "
LAST_BRANCH = "`-- "
PIPE = "|   "
BLANK = "    "
DOT_SUFFIX = ".dot"


def tree_lines(graph, name, prefix, path, shown):
    """Return ASCII-tree lines for the dependencies of ``name``."""
    children = graph.edges.get(name, [])
    is_last = [False] * len(children)
    if is_last:
        is_last[-1] = True
    lines = []
    for child, last in zip(children, is_last):
        mark = ""
        if child in path:
            mark = " (cycle)"
        elif child in shown and graph.edges.get(child):
            mark = " (*)"
        lines.append(prefix + (LAST_BRANCH if last else BRANCH) + child + mark)
        if mark:
            continue
        shown.add(child)
        extra = prefix + (BLANK if last else PIPE)
        lines.extend(tree_lines(graph, child, extra, path | {child}, shown))
    return lines


def ascii_tree(graph):
    """Return the dependencies as an ASCII tree (one string)."""
    root = graph.root
    lines = [root] + tree_lines(graph, root, "", {root}, {root})
    return "\n".join(lines)


def quote(name):
    """Quote a package name for the DOT language."""
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_dot(graph):
    """Return the Graphviz (DOT) description of the graph."""
    lines = [f"digraph {quote(graph.root)} {{", "    rankdir=LR;"]
    lines.append("    node [shape=box];")
    for name in graph.nodes():
        deps = graph.edges.get(name, [])
        if not deps and name != graph.root:
            lines.append(f"    {quote(name)};")
        for dep in deps:
            lines.append(f"    {quote(name)} -> {quote(dep)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_png(dot_text, output_file):
    """Render DOT text to a PNG file with the Graphviz ``dot`` tool."""
    try:
        subprocess.run(
            ["dot", "-Tpng", "-o", output_file],
            input=dot_text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        raise DepGraphError(
            "Graphviz 'dot' is not installed or not in PATH"
        ) from None
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode("utf-8", "replace").strip()
        raise DepGraphError(f"Graphviz failed: {message}") from exc


def dot_path(output_file):
    """Return the path of the .dot file next to the PNG file."""
    return os.path.splitext(output_file)[0] + DOT_SUFFIX


def save_visualization(graph, output_file):
    """Save the DOT text and the PNG image; return the DOT text."""
    dot_text = to_dot(graph)
    with open(dot_path(output_file), "w", encoding="utf-8") as handle:
        handle.write(dot_text)
    render_png(dot_text, output_file)
    return dot_text
