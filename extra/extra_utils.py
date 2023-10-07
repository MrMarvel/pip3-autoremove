import sys
from typing import Union

from pkg_resources import EggInfoDistribution, get_distribution, VersionConflict, DistributionNotFound, working_set, \
    DistInfoDistribution, Requirement

restricted_extras_like = ['dev', 'test', 'doc']


def _is_restricted_extra(extra):
    return any([restricted in extra for restricted in restricted_extras_like])


def _get_dist(requirement):
    """Return the distribution matching the given requirement."""
    if requirement.name not in working_set.by_key:
        if requirement.key not in working_set.by_key:
            raise DistributionNotFound(requirement.name)
    required_dist = None
    try:
        required_dist = get_distribution(requirement)
    except (VersionConflict, DistributionNotFound) as _:
        pass

    if required_dist is None:
        try:
            required_dist = get_distribution(requirement.project_name)
        except VersionConflict as _:
            pass
        except DistributionNotFound as e:
            raise e

    return required_dist


def distributions_required(dist, extras=None):
    """Return a list of distributions required by the given distribution."""
    if extras is None:
        extras = list()
    required_distributions = set()
    for pkg in dist.requires(extras=extras):
        try:
            required_dist = _get_dist(pkg)
            required_distributions.add(required_dist)
        except DistributionNotFound as _:
            pass

    return required_distributions


def optional_distributions_required(
        dist,
        extras
):
    required_base_distributions = distributions_required(dist)
    required_base_with_extra_distributions = distributions_required(dist, extras)
    required_optional_distributions = set()
    for dist in required_base_with_extra_distributions:
        if dist not in required_base_distributions:
            required_optional_distributions.add(dist)
    return required_optional_distributions


def get_requirements_graph(extra_required=False):
    g = dict((dist, set()) for dist in working_set.by_key.values())
    for dist in g.keys():
        for req in distributions_required(dist):
            g[req].add(dist)
    for dist in g.keys():
        if extra_required:
            extras = list(filter(lambda e: not _is_restricted_extra(e), dist.extras))
            for req in optional_distributions_required(dist, extras):
                if len(g[req]) > 0:
                    continue
                g[req].add(dist)
    return g


def main():
    g = distributions_required(working_set.by_key['commitizen'])
    from pip_autoremove import requires
    g2 = requires(working_set.by_key['commitizen'])
    optional_distributions_required(working_set.by_key['jsonschema'], ["format"])


if __name__ == '__main__':
    main()
