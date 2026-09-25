from __future__ import print_function

import optparse
import subprocess
import sys

from typing import List, Union

from extra import importlib_utils
from extra.extra_utils import optional_distributions_required, get_requirements_graph
from extra.graph_utils import get_graph_leaves, remove_graph_nodes
from extra.importlib_utils import DistributionInfo

from about_package import __version__

try:
    # noinspection PyShadowingBuiltins,PyUnresolvedReferences
    input = raw_input
except NameError:
    pass

import_utils_lib = importlib_utils.ImportUtilsFactory.create()

WHITELIST_GLOBAL = (['pip', 'packaging'] + ([] if sys.version_info >= (3, 8) else ['setuptools']) +
                    ['pip3-autoremove'])


def exclude_whitelist_from(dists: set[DistributionInfo], whitelist: list[str]):
    for package_name in whitelist:
        try:
            dist = import_utils_lib.get_distribution(package_name)
            dists.discard(dist)
        except import_utils_lib.InstalledDependencyNotFound:
            print("%s is not an installed pip module, skipping" % package_name,
                  file=sys.stderr)


def autoremove(names, yes=False, remove_extra=False, whitelist: Union[list[str], None] = None):
    dead_base_distributions: set[DistributionInfo] = list_dead(names, remove_extras=remove_extra)
    dead_extras: set[DistributionInfo] = set()
    dead_distributions = dead_base_distributions | dead_extras
    if whitelist:
        exclude_whitelist_from(dead_distributions, whitelist)
    if dead_distributions and (yes or confirm("Uninstall (y/N)? ")):
        remove_dists(dead_distributions)


def list_dead(names, remove_extras=False):
    start = set()
    for name in names:
        try:
            start.add(import_utils_lib.get_distribution(name))
        except import_utils_lib.InstalledDependencyNotFound:
            print("%s is not an installed pip module, skipping" % name,
                  file=sys.stderr)
    installed_distributions = import_utils_lib.get_installed_distributions()
    graph = get_requirements_graph(import_utils_lib, remove_extras)
    dead = exclude_whitelist(find_all_dead(graph, start))
    if remove_extras:
        dead = exclude_whitelist(dead)
    # b: importlib_utils.ImportUtils
    for d in start:
        show_tree(d, dead, installed_distributions, include_extras=True)
    return dead


def list_dead_extras(dead_base_distributions):
    installed_distributions = import_utils_lib.get_installed_distributions()
    graph = get_requirements_graph(import_utils_lib, installed_distributions)
    dead_distribution_by_base = exclude_whitelist(
        find_all_dead(graph, dead_base_distributions))
    graph_without_base = remove_graph_nodes(graph, dead_distribution_by_base)
    leaf_nodes = get_graph_leaves(graph_without_base)
    leaf_extra_nodes = set()
    restricted_extras_like = ['dev', 'test', 'doc']
    for dist in dead_distribution_by_base:
        allowed_extras = list(filter(
            lambda e: not any(
                [restricted in e for restricted in restricted_extras_like]
            ), dist.available_extras))
        optional_distributions = exclude_whitelist(optional_distributions_required(
            import_utils_lib, dist, allowed_extras))
        for optional_dist in optional_distributions:
            if optional_dist in leaf_nodes:
                leaf_extra_nodes.add(optional_dist)
    if len(leaf_extra_nodes) > 0:
        return list_dead_extras(dead_base_distributions | leaf_extra_nodes)
    return dead_distribution_by_base


def exclude_whitelist(dists):
    return set(dist for dist in dists if dist.name_general not in WHITELIST_GLOBAL)


def show_tree(dist, dead, installed_distributions, indent=0, visited=None,
              include_extras=False):
    if visited is None:
        visited = set()
    if dist in visited:
        return
    visited.add(dist)
    print(' ' * 4 * indent, end='')
    show_dist(dist)
    
    for req in requires(dist, installed_distributions):
        if req in dead:
            show_tree(req, dead, installed_distributions, indent + 1, visited,
                      include_extras=include_extras)


def find_all_dead(graph, start):
    return fixed_point(lambda d: find_dead(graph, d), start)


def find_dead(graph, dead):
    def has_children_and_all_child_nodes_dead(node):
        node_children = graph[node]
        if not node_children:
            return False
        return all(child in dead for child in node_children)
    
    return dead | set(filter(has_children_and_all_child_nodes_dead, graph))


def fixed_point(f, x):
    while True:
        y = f(x)
        if y == x:
            return x
        x = y


def confirm(prompt):
    return input(prompt) == 'y'


def show_dist(dist: DistributionInfo):
    print('%s %s (%s)' % (dist.name, dist.version, dist.lib_path_location))


def show_freeze(dist: DistributionInfo):
    print('%s==%s' % (dist.name, dist.version))


def remove_dists(dists):
    # if sys.executable and os.name != 'nt':
    #     # Not working good with windows when packages locks directories like pywin32
    #     pip_cmd = [sys.executable, '-m', 'pip']
    # else:
    #     pip_cmd = ['pip']
    pip_cmd = [sys.executable, '-m', 'pip']
    subprocess.check_call(pip_cmd + ["uninstall", "-y"] + [d.name_general for d in dists])


def get_graph(installed_distributions):
    dist_map = dict(
        (dist.name, dist) for dist in installed_distributions)
    g = dict(
        (dist, set()) for dist in dist_map.values())
    for dist in g.keys():
        for req in requires(dist, installed_distributions):
            g[dist_map[req.name]].add(dist)
    return g


def requires(dist: DistributionInfo, installed_dists: List[DistributionInfo]):
    required = []
    installed_dependencies_names = list(
        x.name.lower() for x in installed_dists)
    requirements = dist.requirements_filter()
    for pkg in requirements:
        try:
            if pkg.name.lower() not in installed_dependencies_names:
                # print("Extra distribution %s not found in working_set,
                # skipping" % str(pkg), file=sys.stderr)
                continue
            if pkg.name.lower() == dist.name.lower():
                # Recursive
                continue
            required.append(import_utils_lib.get_distribution(pkg.name_general))
        # except pkg_resources.VersionConflict as e:
        #     print(e.report(), file=sys.stderr)
        #     print("Redoing requirement with just package name...", file=sys.stderr)
        #     required.append(pkg_resources.get_distribution(pkg.project_name))
        except import_utils_lib.InstalledDependencyNotFound as e:
            print(e, file=sys.stderr)
            print("Skipping %s" % pkg.name, file=sys.stderr)
    return required


def collect_packages_from_file(filename):
    packages_name = []
    try:
        with open(filename, mode='r') as f:
            line = f.readline().rstrip('\n')
            while line:
                if len(line) < 1:
                    break
                packages_name.append(line)
                line = str(f.readline()).rstrip('\n').strip()
    except FileNotFoundError:
        print('File \'%s\' not found!' % filename)
    return packages_name


def main(argv=None):
    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]
    (opts, args) = parser.parse_args(argv)
    if opts.leaves or opts.freeze:
        list_leaves(opts.freeze, include_extras=opts.include_extras)
    elif opts.list:
        list_dead(args, remove_extras=opts.include_extras)
    elif len(argv) < 1:
        parser.print_help()
    else:
        packages_name_to_remove = args
        packages_whitelist: list[str] = []
        if opts.read_file:
            filename = opts.read_file
            for package in collect_packages_from_file(filename):
                if package in packages_name_to_remove:
                    continue
                packages_name_to_remove.append(package)
        if opts.keep:
            packages_whitelist += opts.keep.split(',')
        if opts.keep_file:
            filename = opts.keep_file
            packages_whitelist += collect_packages_from_file(filename)
        autoremove(
            packages_name_to_remove, yes=opts.yes, remove_extra=opts.include_extras, whitelist=packages_whitelist)


def get_leaves(graph):
    def is_leaf(node):
        return not graph[node]
    
    return filter(is_leaf, graph)


def list_leaves(freeze=False, include_extras=False):
    # installed_distributions = import_utils_lib.get_installed_distributions()
    graph = get_requirements_graph(
        import_utils_lib, include_extras)
    
    leaves = get_graph_leaves(graph)
    for node in leaves:
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
        help="list leaves (packages, which are not used by any others).")
    parser.add_option(
        '-y', '--yes', action='store_true', default=False,
        help="don't ask for confirmation of uninstall deletions.")
    parser.add_option(
        '-e', '--include-extras', action='store_true', default=False,
        help="include in search all extras (like jsonschema[format]).")
    parser.add_option(
        '-f', '--freeze', action='store_true', default=False,
        help="list leaves (packages, which are not used by any others) in "
             "file_test.txt format")
    parser.add_option(
        '-r', '--read-file', action='store', default=False, dest='read_file', metavar='<FILE>',
        help="read packages from file like file_test.txt")
    parser.add_option(
        '-k', '--keep-file', action='store', default=None, dest='keep_file', metavar='<FILE>',
        help="read whitelist packages from file like keep_requirements.txt"
    )
    parser.add_option(
        '--keep', action='store', default=None, dest='keep', metavar='<PACKAGE>,...',
        help="keep package(s) from uninstalling"
    )
    return parser


if __name__ == '__main__':
    # profiling_test.make_all_profiling_in_module(globals())
    # profiling_test.make_all_profiling_in_module(vars(importlib_utils))
    # profiling_test.make_all_profiling_in_module(vars(extra_utils))
    main()
