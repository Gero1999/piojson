import json
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
import pandas as pd
from src.biojson.datasetjson import validate_datasetjson, write_datasetjson, read_datasetjson

class SchemaTests(unittest.TestCase):
    def document(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'data.json';write_datasetjson(pd.DataFrame({'x':[1]}),path)
            return json.loads(path.read_text())
    def test_required_metadata_and_cell_types(self):
        good=self.document();validate_datasetjson(good)
        bad=deepcopy(good);del bad['itemGroupOID']
        with self.assertRaisesRegex(ValueError,'schema violation'):validate_datasetjson(bad)
        bad=deepcopy(good);bad['rows']=[['wrong']]
        with self.assertRaisesRegex(ValueError,'does not match integer'):validate_datasetjson(bad)
    def test_temporal_invalid_strings_are_not_missing_by_default(self):
        for value in ['','NaT','2026-02-30','20260102']:
            data=self.document();data['columns'][0]['dataType']='date';data['rows']=[[value]]
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'data.json';path.write_text(json.dumps(data))
                with self.subTest(value=value),self.assertRaisesRegex(ValueError,'row 1'):
                    read_datasetjson(path)
