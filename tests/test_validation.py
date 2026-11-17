import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from src.biojson.datasetjson import read_datasetjson

BASE={'datasetJSONVersion':'1.1.0','columns':[{'name':'X','label':'X','dataType':'integer'}],'records':1,'rows':[[1]]}
class ValidationTests(unittest.TestCase):
    def read(self,data,**kwargs):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'data.json';p.write_text(json.dumps(data),encoding='utf-8')
            return read_datasetjson(p,**kwargs)
    def test_invalid_structure(self):
        for updates in [{'records':99},{'datasetJSONVersion':'2.0.0'},{'rows':[[1,2]]},{'columns':[{'name':'X','label':'X','dataType':'bogus'}]}]:
            data=deepcopy(BASE);data.update(updates)
            with self.subTest(updates=updates),self.assertRaises(ValueError):self.read(data)
