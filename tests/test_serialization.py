import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from src.biojson.datasetjson import write_datasetjson, read_datasetjson, DatasetJSON

class SerializationTests(unittest.TestCase):
    def test_nullable_scalars_are_standard_json(self):
        frame=pd.DataFrame({'i':pd.Series([1,None],dtype='Int64'),
          'b':pd.Series([True,None],dtype='boolean'),'f':[1.5,float('nan')]})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'data.json';write_datasetjson(frame,path)
            data=json.loads(path.read_text(),parse_constant=lambda x:self.fail(x))
        self.assertEqual(data['rows'],[[1,True,1.5],[None,None,None]])
        self.assertIsInstance(data['rows'][0][0],int)

    def test_infinity_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'Non-finite'):
                write_datasetjson(pd.DataFrame({'x':[float('inf')]}),Path(folder)/'data.json')
