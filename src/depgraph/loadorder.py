"""Order in which packages have to be loaded.

A package can be loaded only after all of its dependencies, so the order
is a post-order depth-first traversal: dependencies first, the requested
package last. Edges that close a cycle are skipped.
"""


def visit(graph, name, seen, order):
    """Append ``name`` to ``order`` after all its dependencies."""
    if name in seen:
        return
    seen.add(name)
    for dep in graph.edges.get(name, []):
        visit(graph, dep, seen, order)
    order.append(name)


def load_order(graph):
    """Return package names in the order they must be loaded."""
    order = []
    visit(graph, graph.root, set(), order)
    return order


def find_cycle_edges(graph):
    """Return ``(a, b)`` edges that point back to a package on the path."""
    found = []
    done = set()
    path = []
    walk_cycles(graph, graph.root, path, done, found)
    return found


def walk_cycles(graph, name, path, done, found):
    """Depth-first search that records back edges."""
    path.append(name)
    for dep in graph.edges.get(name, []):
        if dep in path:
            found.append((name, dep))
        elif dep not in done:
            walk_cycles(graph, dep, path, done, found)
    path.pop()
    done.add(name)
