"""Building the dependency graph with a recursive BFS."""

from .errors import DepGraphError


class DependencyGraph:
    """Directed graph: package name -> list of direct dependencies."""

    def __init__(self, root):
        """Create a graph that contains only the root package."""
        self.root = root
        self.edges = {}
        self.depths = {root: 0}

    def nodes(self):
        """Return all package names in discovery (BFS) order."""
        return list(self.depths)


def bfs_level(source, graph, level, max_depth):
    """Expand one BFS level and recurse into the next one.

    ``level`` holds the packages found at depth ``depth``. A package is
    expanded only if its depth is below ``max_depth``. A package that is
    already known is never queued again, so cycles terminate.
    """
    if not level:
        return
    depth = graph.depths[level[0]]
    if depth >= max_depth:
        return
    next_level = []
    for name in level:
        deps = source.dependencies(name)
        graph.edges[name] = deps
        for dep in deps:
            if dep not in graph.depths:
                graph.depths[dep] = depth + 1
                next_level.append(dep)
    bfs_level(source, graph, next_level, max_depth)


def build_graph(source, root, max_depth):
    """Build the dependency graph of ``root`` up to ``max_depth``."""
    graph = DependencyGraph(root)
    try:
        bfs_level(source, graph, [root], max_depth)
    except RecursionError:
        raise DepGraphError("max_depth is too large") from None
    return graph


def format_edges(graph):
    """Return ``name -> deps`` lines for every package of the graph."""
    lines = []
    for name in graph.nodes():
        deps = " ".join(graph.edges.get(name, [])) or "-"
        lines.append(f"{name} -> {deps}")
    return lines
