from typing import Set, Dict, List, Sequence

from extra import graph_utils
from extra.graph_utils import get_graph_leaves, test_graph_loops
from extra.importlib_utils import DistributionInfo, ImportUtils

restricted_extras_like = ['dev', 'test', 'doc']


def _is_restricted_extra(extra):
    return any([restricted in extra for restricted in restricted_extras_like])


def _get_dist(import_utils_lib: ImportUtils, requirement) -> DistributionInfo:
    """Return the distribution matching the given requirement."""
    dist = import_utils_lib.get_distribution(requirement.name_general)
    return dist


def distributions_required(import_utils_lib: ImportUtils, dist: DistributionInfo,
                           extras: List[str] = None):
    """Return a list of distributions required by the given distribution."""
    if extras is None:
        extras = list()
    required_distributions = set()
    for pkg in dist.requirements_filter(enabled_extras=extras):
        try:
            required_dist = _get_dist(import_utils_lib, pkg)
            required_distributions.add(required_dist)
        except import_utils_lib.InstalledDependencyNotFound as _:
            pass

    return required_distributions


def optional_distributions_required(
        import_utils_lib: ImportUtils,
        dist: DistributionInfo,
        extras: List[str] = None
):
    required_base_distributions = distributions_required(import_utils_lib, dist)
    required_base_with_extra_distributions = distributions_required(
        import_utils_lib, dist, extras)
    required_optional_distributions = set()
    for dist in required_base_with_extra_distributions:
        if dist not in required_base_distributions:
            required_optional_distributions.add(dist)
    return required_optional_distributions


def delete_cycles(graph: Dict[DistributionInfo, Set[DistributionInfo]]):
    """
    We are starting from the leaf nodes,
    and we detect cycles by removing deep connections.
    """
    leafs = get_graph_leaves(graph)
    visited = set()
    last_level = leafs
    while True:
        new_level = set()
        for node_num, node in enumerate(last_level.copy()):
            if node in visited:
                last_level.remove(node)
                continue
            visited.add(node)
            for child in graph[node]:
                if child not in visited:
                    new_level.add(child)
        if len(new_level) == 0:
            break
        for node in new_level:
            del graph[node]
        last_level = new_level


def get_requirements_graph(import_utils_lib: ImportUtils,
                           extra_required=False):
    installed_distributions = import_utils_lib.get_installed_distributions()
    dist_map = dict(
        (dist.name_general, dist) for dist in installed_distributions)
    g = dict(
        (dist, set([dist][:0])) for dist in dist_map.values())
    # set([dist][:0]) is used for typing help for 2.7. It marks as 'set' of 'dist type'
    for dist in g.keys():
        for req in distributions_required(import_utils_lib, dist):
            g[dist_map[req.name_general]].add(dist)
    # delete cycles
    while True:
        if remove_cycles(g):
            continue
        break
    #
    if extra_required:
        for dist in g.keys():
            extras = list(filter(
                lambda e: not _is_restricted_extra(e), dist.available_extras))
            for req in optional_distributions_required(import_utils_lib, dist, extras):
                if len(g[dist_map[req.name_general]]) > 0:
                    continue
                g[dist_map[req.name_general]].add(dist)
                if test_graph_loops(g):
                    g[dist_map[req.name_general]].remove(dist)
    # delete cycles

    return g


def requirements_total_count(graph: Dict[DistributionInfo, Set[DistributionInfo]],
                             node: DistributionInfo) -> int:
    total_requirements = 0
    visited = set()
    stack = [node]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        total_requirements += 1
        for child in graph.get(current, []):
            if child not in visited:
                stack.append(child)
    return total_requirements


def remove_cycles(graph: Dict[DistributionInfo, Set[DistributionInfo]]) \
        -> Sequence[DistributionInfo]:
    cycle = graph_utils.find_cycle(graph)
    if not cycle:
        return cycle
    requirements_per_node = [0 for _ in range(len(cycle) - 1)]
    for dist_cycle_num in range(len(cycle) - 1):
        dist_remove_connection = cycle[dist_cycle_num]
        if dist_remove_connection not in graph:
            continue
        connection = cycle[dist_cycle_num + 1]
        if connection not in graph[dist_remove_connection]:
            continue
        graph[dist_remove_connection].remove(connection)
        for dist_cycle_num2 in range(len(cycle) - 1):
            requirements_per_node[dist_cycle_num2] += requirements_total_count(
                graph, cycle[dist_cycle_num2])
        graph[dist_remove_connection].add(connection)
    # requirements_per_node = [requirements_total_count(graph, dist)
    # for dist in cycle[:-1]]
    min_index = requirements_per_node.index(min(requirements_per_node))
    node_to_remove_connection = cycle[min_index-1]
    connection = cycle[min_index]
    graph[node_to_remove_connection].remove(connection)
    return cycle


def main():
    # g = distributions_required(working_set.by_key['commitizen'])
    # from pip_autoremove import requires
    # g2 = requires(working_set.by_key['commitizen'])
    # optional_distributions_required(working_set.by_key['jsonschema'], ["format"])
    pass


if __name__ == '__main__':
    main()
