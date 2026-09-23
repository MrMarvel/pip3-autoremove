import logging
import sys
import unittest
from unittest import TestCase, skipUnless

from extra import importlib_utils
from extra.importlib_utils import ImportUtilsPkgResources, ImportUtilsImportlib, \
    ImportUtils
from test_utils.install_utils import need_dists

logger = logging.getLogger(__name__)


class TestImportUtils(TestCase):
    logging.basicConfig(level=logging.INFO)

    @classmethod
    def setUpClass(cls):
        logger.info(
            "Python version: \"%s\"" % '.'.join(str(x) for x in sys.version_info[:3]))

    def test1_import_implementation(self):
        try:
            import importlib.metadata
        except ImportError:
            self.skipTest("importlib is not available in this Python version")
        util = importlib_utils.ImportUtilsFactory.create()
        self.assertIsInstance(util, ImportUtils)
        self.assertIsInstance(util, ImportUtilsImportlib)

    @skipUnless(sys.version_info < (3, 8), "This code is never used if importlib.metadata exists")
    @need_dists(['setuptools'], remove_after=True)
    def test2_setuptools(self):
        # This test is known to fail on Python 3.9 or higher, as that installs
        # setuptools 82.0.0 or higher, and that version removed the auxiliary
        # pkg_resources module that is required by ImportUtilsPkgResources.
        util1 = ImportUtilsPkgResources()
        try:
            util2 = ImportUtilsImportlib()
        except util1.ImportUtilsInitializationError:
            util2 = ImportUtilsPkgResources()
        utils = (util1, util2)
        dists = list(util.get_distribution('setuptools') for util in utils)[:2]
        requirements = list(d.requirements for d in dists)
        self.assertEqual(2, len(requirements))
        self.assertEqual(requirements[0][0], requirements[1][0])
        self.assertListEqual(requirements[0], requirements[1])
        pass


def main():
    logging.basicConfig(level=logging.INFO)
    selected_tests = [
        # "test1_import_implementation",
        # "test2_setuptools",
    ]
    if selected_tests:
        suite = unittest.TestSuite(TestImportUtils(name) for name in selected_tests)
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPipAutoremove)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    main()
