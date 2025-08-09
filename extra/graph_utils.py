def get_graph_leafs(graph):
    def is_leaf(node):
        return len(graph[node]) < 1

    result = set(filter(is_leaf, graph.keys()))
    return result


def remove_graph_nodes(graph, nodes):
    new_graph = graph.copy()
    for node in nodes:
        del new_graph[node]
    for node in new_graph.keys():
        new_graph[node] = new_graph[node] - nodes
    return new_graph


def test_graph_loops(graph):
    """
    Test if the graph has loops.
    """
    visited = set()
    stack = set()

    def visit(_node):
        if _node in stack:
            return True  # Loop detected
        if _node in visited:
            return False  # Already visited

        visited.add(_node)
        stack.add(_node)

        for neighbor in graph.get(_node, []):
            if visit(neighbor):
                return True

        stack.remove(_node)
        return False

    for node in graph.keys():
        if visit(node):
            return True  # Loop detected

    return False  # No loops found


def main():
    pass


if __name__ == '__main__':
    main()
