
import json
from pathlib import Path
import unittest
import pandas as pd
import os

from src.biojson import datasetjson

TEST_DIR = Path(__file__).parent
DM_PATH = TEST_DIR / "data/datasetjson_dm.json"

# --- Convert date columns to datetime (optional) ---
class TestDatasetJSON(unittest.TestCase):
    def setUp(self):
        self.dm_path = DM_PATH
        self.ds = datasetjson.read_datasetjson(self.dm_path)
        self.df = self.ds.df

    def test_read_datasetjson_types(self):
        # Check columns exist
        expected_columns = ["STUDYID", "USUBJID", "SUBJID", "RFSTDTC", "BRTHDTC", "AGE", "SEX", "COUNTRY"]
        self.assertListEqual(list(self.df.columns), expected_columns)
        # Check types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["RFSTDTC"]))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["BRTHDTC"]))
        self.assertTrue(pd.api.types.is_integer_dtype(self.df["AGE"]))
        self.assertTrue(pd.api.types.is_string_dtype(self.df["STUDYID"]))
        self.assertTrue(pd.api.types.is_string_dtype(self.df["SEX"]))
        self.assertTrue(pd.api.types.is_string_dtype(self.df["COUNTRY"]))

    def test_read_datasetjson_values(self):
        # Check some values
        self.assertEqual(self.df.iloc[0]["STUDYID"], "STUDYMOCK01")
        self.assertEqual(self.df.iloc[1]["COUNTRY"], "CAN")
        self.assertEqual(self.df.iloc[2]["AGE"], 47)

    def test_read_datasetjson_metadata(self):
        self.assertIsInstance(self.ds, datasetjson.DatasetJSON)
        self.assertEqual(self.ds.metadata["name"], "DM")
        self.assertEqual(self.ds.metadata["label"], "Demographics")
        self.assertEqual(self.ds.metadata["studyOID"], "example.org/STUDYMOCK01")

    def test_write_and_read_roundtrip(self):
        # Write to a temp file and read back
        tmp_path = TEST_DIR / "data/tmp_datasetjson_dm.json"
        datasetjson.write_datasetjson(self.ds, tmp_path)
        ds2 = datasetjson.read_datasetjson(tmp_path)
        df2 = ds2.df
        # Check shape and columns
        self.assertListEqual(list(df2.columns), list(self.df.columns))
        self.assertEqual(df2.shape, self.df.shape)
        # Check values
        self.assertEqual(df2.iloc[0]["STUDYID"], self.df.iloc[0]["STUDYID"])
        self.assertEqual(df2.iloc[1]["COUNTRY"], self.df.iloc[1]["COUNTRY"])
        self.assertEqual(df2.iloc[2]["AGE"], self.df.iloc[2]["AGE"])
        self.assertEqual(ds2.metadata["studyOID"], self.ds.metadata["studyOID"])
        self.assertEqual(ds2.metadata["label"], self.ds.metadata["label"])
        # Clean up
        os.remove(tmp_path)

    def test_write_datasetjson_rejects_unsupported_metadata_version(self):
        tmp_path = TEST_DIR / "data/tmp_invalid_version_datasetjson_dm.json"
        ds_invalid = datasetjson.DatasetJSON(
            df=self.ds.df,
            metadata={**self.ds.metadata, "datasetJSONVersion": "2.0.0"},
            columns_metadata=self.ds.columns_metadata,
        )

        with self.assertRaises(ValueError):
            datasetjson.write_datasetjson(ds_invalid, tmp_path)

if __name__ == "__main__":
    unittest.main()
