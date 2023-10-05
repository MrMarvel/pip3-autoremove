from pkg_resources import working_set

from pip_autoremove import get_graph


def get_graph_leafs(graph: dict) -> set:
    def is_leaf(node):
        return len(graph[node]) < 1
    result = set(filter(is_leaf, graph.keys()))
    return result

def main():
    get_graph_leafs(get_graph())

if __name__ == '__main__':
    main()