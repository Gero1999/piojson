"""Run outside the source checkout after installing the wheel."""
import json
import tempfile
from pathlib import Path
import pandas as pd
import piojson
import biojson

assert piojson.DatasetJSON is biojson.DatasetJSON
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / 'example.json'
    frame = pd.DataFrame({'AGE': pd.Series([35, None], dtype='Int64')})
    piojson.write_datasetjson(frame, path, name='DM', label='Synthetic demographics')
    result = piojson.read_datasetjson(path)
    assert result.df['AGE'].tolist()[0] == 35
    assert pd.isna(result.df['AGE'].iloc[1])

print('Installed public imports and nullable round trip passed.')
