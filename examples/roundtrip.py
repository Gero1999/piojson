"""Run after installing piojson. All files are synthetic and temporary."""
from pathlib import Path
import tempfile
import pandas as pd
from piojson import read_datasetjson, write_datasetjson, read_odm, write_odm

with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    data = folder / 'demo.json'
    write_datasetjson(pd.DataFrame({'ID': ['MOCK-001']}), data, name='DEMO', label='Synthetic demo')
    assert read_datasetjson(data).df.iloc[0, 0] == 'MOCK-001'
    xml = folder / 'demo.xml'
    xml.write_text('<ODM xmlns="http://www.cdisc.org/ns/odm/v2.0" FileOID="MOCK" FileType="Snapshot" ODMVersion="2.0" CreationDateTime="2026-01-02T12:00:00Z"/>', encoding='utf-8')
    write_odm(read_odm(xml), folder / 'copy.xml')
print('Synthetic JSON and ODM XML round trips passed.')
