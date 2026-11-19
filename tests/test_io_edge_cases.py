"""Original synthetic cases exercise IO behavior without external schemas."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from src.biojson.datasetjson import DatasetJSON,read_datasetjson,write_datasetjson

class IOEdgeTests(unittest.TestCase):
    def test_extra_metadata_and_unicode_are_retained_without_conformance_checks(self):
        doc=DatasetJSON(pd.DataFrame({'X':['synthetic ñ 汉字']}),
          {'datasetJSONVersion':'1.1.0','custom_note':'local extension'},
          [{'name':'X','label':'Example','dataType':'string'}])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'data.json';write_datasetjson(doc,path)
            result=read_datasetjson(path)
        self.assertEqual(result.metadata['custom_note'],'local extension')
        self.assertEqual(result.df.iloc[0,0],'synthetic ñ 汉字')

    def test_replace_failure_preserves_old_file_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'data.json';path.write_text('keep')
            with patch('src.biojson.datasetjson.os.replace',side_effect=OSError('synthetic failure')):
                with self.assertRaises(OSError):write_datasetjson(pd.DataFrame({'x':[1]}),path)
            self.assertEqual(path.read_text(),'keep')
            self.assertEqual(list(Path(folder).iterdir()),[path])

    def test_invalid_dates_raise_without_a_schema(self):
        for value in ['','NaT','2026-02-30','20260102']:
            data={'datasetJSONVersion':'1.1.0','records':1,
              'columns':[{'name':'X','label':'X','dataType':'date'}],'rows':[[value]]}
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'bad.json';path.write_text(json.dumps(data))
                with self.subTest(value=value),self.assertRaisesRegex(ValueError,'row 1'):
                    read_datasetjson(path)

    def test_empty_typed_frame_roundtrips(self):
        frame=pd.DataFrame({'i':pd.Series([],dtype='Int64'),'b':pd.Series([],dtype='boolean'),
          's':pd.Series([],dtype='string'),'d':pd.Series([],dtype='datetime64[ns]')})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'empty.json';write_datasetjson(frame,path)
            result=read_datasetjson(path)
        self.assertEqual(result.df.shape,(0,4))
        self.assertEqual(list(map(str,result.df.dtypes)),list(map(str,frame.dtypes)))

