import copy
from typing import Union, List, Dict, Set, Any, TypeVar, Collection, Sequence

T = TypeVar('T')


def get_graph_leaves(graph: Dict[T, Collection[T]]) -> Set[T]:
    def is_leaf(node):
        return len(graph[node]) < 1

    result = set(filter(is_leaf, graph.keys()))
    return result


def remove_graph_nodes(graph, nodes):
    new_graph = copy.deepcopy(graph)
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


def find_cycle(graph: Dict[T, Collection[T]]) -> Sequence[T]:
    visited = set()
    stack = []
    on_stack = set()

    def dfs(node) -> Union[List[Any], None]:
        visited.add(node)
        stack.append(node)
        on_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                _cycle = dfs(neighbor)
                if _cycle:
                    return _cycle
            elif neighbor in on_stack:
                cycle_start_index = stack.index(neighbor)
                return stack[cycle_start_index:] + [neighbor]

        stack.pop()
        on_stack.remove(node)
        return None

    for start_node in graph:
        if start_node not in visited:
            cycle = dfs(start_node)
            if cycle:
                return tuple(cycle)

    return tuple()  # No cycle found


def main():
    pass


if __name__ == '__main__':
    main()
