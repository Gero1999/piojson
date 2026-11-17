import unittest
import piojson
from biojson.datasetjson import DatasetJSON

class PublicAPITests(unittest.TestCase):
    def test_new_import_shares_the_legacy_class(self):
        self.assertIs(piojson.DatasetJSON,DatasetJSON)
        self.assertTrue(callable(piojson.read_datasetjson))
        self.assertTrue(callable(piojson.validate_datasetjson))
