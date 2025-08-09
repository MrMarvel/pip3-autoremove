from unittest import TestCase
from extra import importlib_utils


class TestImportUtils(TestCase):
    def test_import_implementation(self):
        util = importlib_utils.ImportUtilsFactory.create()
        self.assertIsInstance(util, importlib_utils.ImportUtils)
        self.assertIsInstance(util, importlib_utils.ImportUtilsImportlib)
