import pkg_resources
import subprocess

import pip_autoremove


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
        pip_autoremove.main(['-r', 'test/file_test.txt', '-y'])
    except Exception as e:
        assert not e
    for name in expected:
        assert not has_dist(name)


if __name__ == "__main__":
    test_main()
    test_find_all_dead()
    test_file()
