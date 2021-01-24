import unittest
from unittest.mock import Mock
import sys
from os import path
from shutil import rmtree
'''
Mock all unnecessary modules that we don't use in testing environment.
This should happen before importing the module we are testing.
'''
sys.modules['model.enums.storage_provider'] = Mock()
sys.modules['logger.jsonLogger'] = Mock()
sys.modules['osgeo'] = Mock()
sys.modules['src.config'] = Mock()
import src.utilities as utilities

class TestUtilities(unittest.TestCase):

    def test_folder_creation(self):
        folder_test_name = "temp_test_folder"
        utilities.create_folder(folder_test_name)
        folder_created = path.exists(folder_test_name)
        # Remove folder
        if path.exists(folder_test_name):
            rmtree(folder_test_name)

        self.assertTrue(True, folder_created)

if __name__ == '__main__':
    unittest.main()
