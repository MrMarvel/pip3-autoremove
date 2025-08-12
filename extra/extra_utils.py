from typing import Set, Dict, List

from extra import importlib_utils
from extra.graph_utils import get_graph_leafs, test_graph_loops
from extra.importlib_utils import DistributionInfo

restricted_extras_like = ['dev', 'test', 'doc']

import_utils_lib = importlib_utils.ImportUtilsFactory.create()


def _is_restricted_extra(extra):
    return any([restricted in extra for restricted in restricted_extras_like])


def _get_dist(requirement) -> DistributionInfo:
    """Return the distribution matching the given requirement."""
    dist = import_utils_lib.get_distribution(requirement.name_general)
    return dist


def distributions_required(dist: DistributionInfo, extras: List[str] = None):
    """Return a list of distributions required by the given distribution."""
    if extras is None:
        extras = list()
    required_distributions = set()
    for pkg in dist.requirements_filter(enabled_extras=extras):
        try:
            required_dist = _get_dist(pkg)
            required_distributions.add(required_dist)
        except import_utils_lib.InstalledDependencyNotFound as _:
            pass

    return required_distributions


def optional_distributions_required(
        dist: DistributionInfo,
        extras: List[str] = None
):
    required_base_distributions = distributions_required(dist)
    required_base_with_extra_distributions = distributions_required(dist, extras)
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
    leafs = get_graph_leafs(graph)
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


def get_requirements_graph(installed_distributions, extra_required=False):
    dist_map = dict(
        (dist.name_general, dist) for dist in installed_distributions)
    g = dict(
        (dist, set()) for dist in dist_map.values())
    for dist in g.keys():
        for req in distributions_required(dist):
            g[dist_map[req.name_general]].add(dist)
    for dist in g.keys():
        if extra_required:
            extras = list(filter(
                lambda e: not _is_restricted_extra(e), dist.available_extras))
            for req in optional_distributions_required(dist, extras):
                if len(g[dist_map[req.name_general]]) > 0:
                    continue
                g[dist_map[req.name_general]].add(dist)
                if test_graph_loops(g):
                    g[dist_map[req.name_general]].remove(dist)
    # delete cycles

    return g


def main():
    # g = distributions_required(working_set.by_key['commitizen'])
    # from pip_autoremove import requires
    # g2 = requires(working_set.by_key['commitizen'])
    # optional_distributions_required(working_set.by_key['jsonschema'], ["format"])
    pass


if __name__ == '__main__':
    main()
