from __future__ import print_function

import optparse
import os
import subprocess
import sys

import pip
from pkg_resources import working_set, get_distribution, VersionConflict, DistributionNotFound

__version__ = '1.2.2'

from extra.extra_utils import optional_distributions_required, get_requirements_graph
from extra.graph_utils import get_graph_leafs, remove_graph_nodes

try:
    raw_input
except NameError:
    raw_input = input

try:
    ModuleNotFoundError
except NameError:
    ModuleNotFoundError = ImportError

try:
    # pip >= 10.0.0 hides main in pip._internal. We'll monkey patch what we need and hopefully this becomes available
    # at some point.
    from pip._internal import main, logger

    pip.main = main
    pip.logger = logger
except (ModuleNotFoundError, ImportError):
    pass

WHITELIST = ['pip', 'setuptools']


def autoremove(names, yes=False, remove_extra=False):
    names_to_remove = list(names)
    dead_base_distributions = list_dead(names)
    dead_extras = set()
    if remove_extra:
        dead_extras = list_dead_extras(dead_base_distributions)
    dead_distributions = dead_base_distributions | dead_extras
    names_to_remove = list(map(lambda d: d.project_name, dead_distributions))
    if dead_distributions and (yes or confirm("Uninstall (y/N)? ")):
        remove_dists(dead_distributions)


def list_dead(names, remove_extras=False):
    start = set()
    for name in names:
        try:
            start.add(get_distribution(name))
        except DistributionNotFound:
            print("%s is not an installed pip module, skipping" % name, file=sys.stderr)
        except VersionConflict:
            print("%s is not the currently installed version, skipping" % name, file=sys.stderr)
    graph = get_graph()
    dead = exclude_whitelist(find_all_dead(graph, start))
    if remove_extras:
        dead = exclude_whitelist(dead)
    for d in start:
        show_tree(d, dead, include_extras=True)
    return dead


def list_dead_extras(dead_base_distributions):
    graph = get_requirements_graph()
    dead_distribution_by_base = exclude_whitelist(find_all_dead(graph, dead_base_distributions))
    graph_without_base = remove_graph_nodes(graph, dead_distribution_by_base)
    leaf_nodes = get_graph_leafs(graph_without_base)
    leaf_extra_nodes = set()
    restricted_extras_like = ['dev', 'test', 'doc']
    for dist in dead_distribution_by_base:
        allowed_extras = list(filter(lambda e: not any([restricted in e for restricted in restricted_extras_like]),
                                     dist.extras))
        optional_distributions = exclude_whitelist(optional_distributions_required(dist, allowed_extras))
        for optional_dist in optional_distributions:
            if optional_dist in leaf_nodes:
                leaf_extra_nodes.add(optional_dist)
    if len(leaf_extra_nodes) > 0:
        return list_dead_extras(dead_base_distributions | leaf_extra_nodes)
    return dead_distribution_by_base


def exclude_whitelist(dists):
    return set(dist for dist in dists if dist.project_name not in WHITELIST)


def show_tree(dist, dead, indent=0, visited=None, include_extras=False):
    if visited is None:
        visited = set()
    if dist in visited:
        return
    visited.add(dist)
    print(' ' * 4 * indent, end='')
    show_dist(dist)
    for req in requires(dist):
        if req in dead:
            show_tree(req, dead, indent + 1, visited, include_extras=include_extras)


def find_all_dead(graph, start):
    return fixed_point(lambda d: find_dead(graph, d), start)


def find_dead(graph, dead):
    def is_killed_by_us(node):
        succ = graph[node]
        return succ and not (succ - dead)

    return dead | set(filter(is_killed_by_us, graph))


def fixed_point(f, x):
    while True:
        y = f(x)
        if y == x:
            return x
        x = y


def confirm(prompt):
    return raw_input(prompt) == 'y'


def show_dist(dist):
    print('%s %s (%s)' % (dist.project_name, dist.version, dist.location))


def show_freeze(dist):
    print(dist.as_requirement())


def remove_dists(dists):
    # if sys.executable and os.name != 'nt':
    #     # Not working good with windows when packages locks directories like pywin32
    #     pip_cmd = [sys.executable, '-m', 'pip']
    # else:
    #     pip_cmd = ['pip']
    pip_cmd = [sys.executable, '-m', 'pip']
    subprocess.check_call(pip_cmd + ["uninstall", "-y"] + [d.project_name for d in dists])


def get_graph():
    g = dict((dist, set()) for dist in working_set.by_key.values())
    for dist in g.keys():
        for req in requires(dist):
            g[req].add(dist)
    return g


def requires(dist):
    required = []
    for pkg in dist.requires():
        try:
            if pkg.marker is not None:
                if pkg.name not in working_set.by_key:
                    # print("Extra distribution %s not found in working_set, skipping" % str(pkg), file=sys.stderr)
                    continue
                if pkg.name == dist.project_name:
                    # Recursive
                    continue
            required.append(get_distribution(pkg))
        except VersionConflict as e:
            print(e.report(), file=sys.stderr)
            print("Redoing requirement with just package name...", file=sys.stderr)
            required.append(get_distribution(pkg.project_name))
        except DistributionNotFound as e:
            print(e.report(), file=sys.stderr)
            print("Skipping %s" % pkg.project_name, file=sys.stderr)
    return required


def main(argv=None):
    parser = create_parser()
    (opts, args) = parser.parse_args(argv)
    if opts.leaves or opts.freeze:
        list_leaves(opts.freeze, include_extras=opts.include_extras)
    elif opts.list:
        list_dead(args, remove_extras=opts.include_extras)
    elif len(args) == 0:
        parser.print_help()
    elif opts.read_file:
        filename = args[0]
        total_args = args[1:]
        file_args = []
        try:
            with open(filename, mode='r') as f:
                line = f.readline().rstrip('\n')
                while line:
                    if len(line) < 1:
                        break
                    file_args.append(line)
                    line = f.readline().rstrip('\n').strip()
            total_args += file_args
            autoremove(total_args, yes=opts.yes, remove_extra=opts.include_extras)
        except FileNotFoundError:
            print('File \'%s\' not found!' % filename)
    else:
        autoremove(args, yes=opts.yes, remove_extra=opts.include_extras)


def get_leaves(graph):
    def is_leaf(node):
        return not graph[node]

    return filter(is_leaf, graph)


def list_leaves(freeze=False, include_extras=False):
    graph = get_graph()
    if include_extras:
        graph = get_requirements_graph(include_extras)
    for node in get_leaves(graph):
        if freeze:
            show_freeze(node)
        else:
            show_dist(node)


def create_parser():
    parser = optparse.OptionParser(
        usage='usage: %prog [OPTION]... [NAME]...',
        version='%prog ' + __version__,
    )
    parser.add_option(
        '-l', '--list', action='store_true', default=False,
        help="list unused dependencies, but don't uninstall them.")
    parser.add_option(
        '-L', '--leaves', action='store_true', default=False,
        help="list leaves (packages which are not used by any others).")
    parser.add_option(
        '-y', '--yes', action='store_true', default=False,
        help="don't ask for confirmation of uninstall deletions.")
    parser.add_option(
        '-e', '--include-extras', action='store_true', default=False,
        help="include in search all extras (like jsonschema[format]).")
    parser.add_option(
        '-f', '--freeze', action='store_true', default=False,
        help="list leaves (packages which are not used by any others) in file_test.txt format")
    parser.add_option(
        '-r', '--read-file', action='store_true', default=False,
        help="read packages from file like file_test.txt")
    return parser


if __name__ == '__main__':
    main()
