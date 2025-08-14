import logging
import sys
from unittest import TestCase

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

    @need_dists(['setuptools'], remove_after=True)
    def test2_setuptools(self):
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
    tests = TestImportUtils()
    tests.test2_setuptools()


if __name__ == '__main__':
    main()
