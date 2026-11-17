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

    def test_invalid_values_require_explicit_coercion(self):
        data=deepcopy(BASE);data['rows']=[['bad']]
        with self.assertRaisesRegex(ValueError,"Column 'X', row 1"):self.read(data)
        import pandas as pd
        self.assertTrue(pd.isna(self.read(data,errors='coerce').df.iloc[0,0]))
    def test_fractional_integer_and_boolean_are_not_silently_numeric(self):
        for value in [1.2,True]:
            data=deepcopy(BASE);data['rows']=[[value]]
            with self.assertRaises(ValueError):self.read(data)
