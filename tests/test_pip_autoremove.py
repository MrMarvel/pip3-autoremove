import logging
import os
import sys
import unittest
from io import StringIO
from typing import Sequence
from unittest import TestCase

from extra import importlib_utils

import pip_autoremove
from test_utils import install_utils
from test_utils.std_wrapper import STDWrapper

logger = logging.getLogger(__name__)


class TestPipAutoremove(TestCase):
    logging.basicConfig(level=logging.INFO)

    def __init__(self, methodName="runTest"):
        super(self.__class__, self).__init__(methodName)
        self._import_utils = importlib_utils.ImportUtilsFactory.create()

    def __has_dist(self, req):
        try:
            self._import_utils.get_requirement(req)
            # dist = self._import_utils.get_distribution(req.name)
        except importlib_utils.ImportUtils.InstalledDependencyNotFound:
            return False
        return True

    def __install_dist(self, req):
        logger.info("Installing distribution \"%s\"." % req)
        install_utils.install_dist(req)
        self.__clear_caches()

    @classmethod
    def setUpClass(cls):
        logger.info(
            "Python version: \"%s\"" % '.'.join(str(x) for x in sys.version_info[:3]))

    def setUp(self):
        logger.info("Test \"%s\"" % self._testMethodName)
        self.__clear_caches()

    def tearDown(self):
        logger.info("Tear down \"%s\"" % self._testMethodName)
        self.__clear_caches()

    def __clear_caches(self):
        self._import_utils.clear_known_distributions()
        pip_autoremove.import_utils_lib.clear_known_distributions()

    def __pip_autoremove_main(self, args: Sequence[str]):
        pip_autoremove.main(args)
        self.__clear_caches()

    def test1_find_all_dead(self):
        graph = {
            'Flask': {},
            'Jinja2': {'Flask'},
            'MarkupSafe': {'Jinja2'},
            'Werkzeug': {'Flask'},
            'itsdangerous': {'Flask'},
            'pip': {},
            'setuptools': {},
        }
        start = {"Flask"}
        expected = {"Flask", "Jinja2", "MarkupSafe", "Werkzeug", "itsdangerous"}
        dead = pip_autoremove.find_all_dead(graph, start)
        assert dead == expected

    def test2_main(self):
        expected = ["Flask", "Jinja2", "MarkupSafe", "Werkzeug", "itsdangerous"]

        for name in expected:
            self.__install_dist(name)

        for name in expected:
            assert self.__has_dist(name)

        for name in expected:
            self.__pip_autoremove_main(['-y', name])
        for name in expected:
            assert not self.__has_dist(name)

    def test3_file(self):
        expected = ["cowsay"]
        for name in expected:
            self.__install_dist(name)
        try:
            self.__pip_autoremove_main(['-r', 'tests/file_test.txt', '-y'])
        except Exception as e:
            assert not e
        for name in expected:
            assert not self.__has_dist(name)

    def test4_locks_on_remove(self):
        if os.name != 'nt':
            self.skipTest("Windows-specific test")
        if isinstance(self._import_utils, importlib_utils.ImportUtilsPkgResources):
            self.skipTest("Only for importlib implementation. "
                          "Pkg_resources not guaranteed")
        installing_packages = ["pywin32"]
        for name in installing_packages:
            self.__install_dist(name)
        try:
            self.__pip_autoremove_main(['-y'] + installing_packages)
        except Exception as e:
            assert not e
        for name in installing_packages:
            assert not self.__has_dist(name)

    def test5_remove_extras(self):
        installing_packages = ["jsonschema[format]"]
        extra_installed = ["webcolors"]
        for name in installing_packages:
            self.__install_dist(name)
        for name in installing_packages + extra_installed:
            assert self.__has_dist(name), "Package \"%s\" was not installed." % name
        try:
            self.__pip_autoremove_main(['-y', '-e'] + installing_packages)
        except Exception as e:
            assert not e, "Failed to remove extras: %s" % e
        for name in installing_packages:
            assert not self.__has_dist(name), "Package \"%s\" was not removed." % name
        for name in extra_installed:
            assert not self.__has_dist(name), ("Extra package \"%s\" was not removed."
                                               % name)
        pass

    def test6_show_extras(self):
        # check version of python
        if sys.version[0] < '3':
            # Console wrapper doesn't work well on python 2.7
            return
        installing_packages = ["jsonschema[format]"]
        extra_installed = ["webcolors"]
        for name in installing_packages:
            self.__install_dist(name)
        for name in installing_packages:
            assert self.__has_dist(name)

        console_output = StringIO()
        with STDWrapper(stdout=console_output):
            self.__pip_autoremove_main(['-f', '-e'])
        for extra in extra_installed:
            assert extra not in console_output.getvalue()
        self.__pip_autoremove_main(['-y', '-e'] + installing_packages)
        for name in installing_packages:
            assert not self.__has_dist(name)
        for name in extra_installed:
            assert not self.__has_dist(name)
        pass

    def test_show_extras2(self):
        """
        Case: matplotlib install and does not show somehow with -ef
        """
        # check version of python
        if sys.version[0] < '3':
            # Console wrapper doesn't work well on python 2.7
            self.skipTest("Console wrapper doesn't work well on python 2.7")
        installing_packages = ["matplotlib"]
        for name in installing_packages:
            self.__install_dist(name)
        for name in installing_packages:
            assert self.__has_dist(name)

        console_output_stream = StringIO()
        with STDWrapper(stdout=console_output_stream):
            self.__pip_autoremove_main(['-ef'])
        console_output = console_output_stream.getvalue()
        print(console_output)
        for package in installing_packages:
            assert package in console_output
        self.__pip_autoremove_main(['-y', '-e'] + installing_packages)
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tests = TestPipAutoremove()
    loader = unittest.TestLoader()
    all_tests_names = [t._testMethodName
                       for t in loader.loadTestsFromTestCase(TestPipAutoremove)][3:3 + 2]
    tests_to_run = all_tests_names
    for test in tests_to_run:
        logger.info("Running test: \"%s\"" % test)
        tests.setUp()
        getattr(tests, test)()
        tests.tearDown()
    # tests.setUp()
    # tests.test1_find_all_dead()
    # tests.setUp()
    # tests.test2_main()
    # tests.setUp()
    # tests.test3_file()
    # tests.setUp()
    # tests.test4_locks_on_remove()
    # tests.setUp()
    # tests.test5_remove_extras()
    # tests.setUp()
    # tests.test6_show_extras()
