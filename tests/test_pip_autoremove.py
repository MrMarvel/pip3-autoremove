import os
import subprocess
import sys
from io import StringIO

import pkg_resources

import pip_autoremove
from test_utils.std_wrapper import STDWrapper


def test_find_all_dead():
    graph = {
        'Flask': set([]),
        'Jinja2': set(['Flask']),
        'MarkupSafe': set(['Jinja2']),
        'Werkzeug': set(['Flask']),
        'itsdangerous': set(['Flask']),
        'pip': set([]),
        'setuptools': set([]),
    }
    start = set(["Flask"])
    expected = set(
        ["Flask", "Jinja2", "MarkupSafe", "Werkzeug", "itsdangerous"])
    dead = pip_autoremove.find_all_dead(graph, start)
    assert dead == expected


def install_dist(req):
    subprocess.check_call(["pip", "install", req])


def has_dist(req):
    req = pkg_resources.Requirement.parse(req)
    working_set = pkg_resources.WorkingSet()
    return working_set.find(req)


def test_main():
    expected = ["Flask", "Jinja2", "MarkupSafe", "Werkzeug", "itsdangerous"]

    for name in expected:
        install_dist(name)

    for name in expected:
        assert has_dist(name)

    for name in expected:
        pip_autoremove.main(['-y', name])
    for name in expected:
        assert not has_dist(name)


def test_file():
    expected = ["cowsay"]
    for name in expected:
        install_dist(name)
    try:
        pip_autoremove.main(['-r', 'tests/file_test.txt', '-y'])
    except Exception as e:
        assert not e
    for name in expected:
        assert not has_dist(name)


def test_locks_on_remove():
    if os.name != 'nt':
        print("Windows-specific test")
        return
    installing_packages = ["pywin32"]
    for name in installing_packages:
        install_dist(name)
    try:
        pip_autoremove.main(['-y'] + installing_packages)
    except Exception as e:
        assert not e
    for name in installing_packages:
        assert not has_dist(name)


def test_remove_extras():
    installing_packages = ["jsonschema[format]"]
    extra_installed = ["webcolors"]
    for name in installing_packages:
        install_dist(name)
    for name in installing_packages:
        assert has_dist(name)
    try:
        pip_autoremove.main(['-y', '-e'] + installing_packages)
    except Exception as e:
        assert not e
    for name in installing_packages:
        assert not has_dist(name)
    for name in extra_installed:
        assert not has_dist(name)
    pass

def test_show_extras():
    # check version of python
    if sys.version[0] < '3':
        # Console wrapper doesn't work well on python 2.7
        return
    installing_packages = ["jsonschema[format]"]
    extra_installed = ["webcolors"]
    for name in installing_packages:
        install_dist(name)
    for name in installing_packages:
        assert has_dist(name)

    console_output = StringIO()
    with STDWrapper(stdout=console_output):
        pip_autoremove.main(['-f', '-e'])
    for extra in extra_installed:
        assert extra not in console_output.getvalue()
    pip_autoremove.main(['-y', '-e'] + installing_packages)
    for name in installing_packages:
        assert not has_dist(name)
    for name in extra_installed:
        assert not has_dist(name)
    pass


def test_show_extras2():
    """
    Case: matplotlib install and does not show somehow with -ef
    """
    # check version of python
    if sys.version[0] < '3':
        # Console wrapper doesn't work well on python 2.7
        return
    installing_packages = ["matplotlib"]
    for name in installing_packages:
        install_dist(name)
    for name in installing_packages:
        assert has_dist(name)

    console_output_stream = StringIO()
    with STDWrapper(stdout=console_output_stream):
        pip_autoremove.main(['-ef'])
    console_output = console_output_stream.getvalue()
    for name in console_output:
        assert has_dist(name)
    pip_autoremove.main(['-y', '-e'] + installing_packages)
    pass


if __name__ == "__main__":
    test_main()
    test_find_all_dead()
    test_file()
    test_remove_extras()
