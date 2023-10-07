from pkg_resources import working_set


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


def main():
    pass


if __name__ == '__main__':
    main()
