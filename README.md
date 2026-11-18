# piojson: pharma & bio JSON standards

![piojson logo](docs/static/piojson-logo.png)

Read, edit and write **CDISC Dataset-JSON 1.1.0** with pandas.
This is a development package; install from this checkout rather than assuming
that a public package-index release is available.

## Installation

```sh
python -m pip install .
```

The distribution and preferred import are `piojson`. Existing `biojson` imports
remain compatible and use the same implementation and DatasetJSON class.
Python 3.8+ is declared; dependency versions are selected for the Python version.

## Quick start

```python
import pandas as pd
from piojson import read_datasetjson, write_datasetjson

frame = pd.DataFrame({"SUBJID": ["MOCK-001", "MOCK-002"],
                      "AGE": pd.Series([35, None], dtype="Int64")})
frame.attrs["labels"] = {"SUBJID": "Synthetic subject", "AGE": "Age"}
write_datasetjson(frame, "dm.json", name="DM", label="Synthetic demographics",
                  studyOID="MOCK-STUDY", itemGroupOID="IG.DM")
dataset = read_datasetjson("dm.json")
dataset.df.loc[0, "AGE"] = 36
dataset.metadata["label"] = "Edited synthetic demographics"
write_datasetjson(dataset, "dm-edited.json")
```

Examples use generated demonstration data. They require no external service.

## Reliable round trips

- Readers check version, record count, row widths, unique columns and typed
  values. Invalid values raise an error naming the column and one-based row.
  `errors="coerce"` explicitly converts bad values to missing.
- No schema files, schema validators or automatic standards-conformance checks
  are included. Original synthetic edge-case tests exercise input and IO behavior.
- `DatasetJSON` retains dataset and column metadata. Values are written in the
  column-metadata order; missing, extra and duplicate columns are rejected.
  Copies of output metadata do not share mutable lists with the document.
- Nulls use JSON `null`. Nullable integers and booleans are supported. Integers
  use pandas Int64; floating/decimal columns use pandas nullable floating point,
  not arbitrary-precision decimal arithmetic.
- Datetime columns retain time, offsets and fractional seconds. Explicit date
  metadata produces dates. Mixed timezones can produce object-dtype columns.
  ISO date/datetime/time strings are checked rather than guessed from numbers.
- Writes are UTF-8 and atomic on the destination filesystem. Failures leave an
  existing file intact. Creation timestamps are UTC; imported metadata is
  preserved apart from regenerated creation time and record counts. Optional
  study identifiers and metadata references are not fabricated when omitted.

The package does not certify standards compliance. Only version 1.1.0
is supported by the public read/write API. Other formats and large-file streaming
need separate support.

## Development checks

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

After installing the wheel, run `tools/check_installed.py` from outside the
checkout to verify public imports and a null round trip.

## Contributing and license

Report bugs and propose formats in the [issue tracker](https://github.com/Gero1999/piojson/issues).
Include a small synthetic example, expected behavior and package versions.
The project uses [Apache 2.0](LICENSE). No third-party schemas are bundled.
Normal Python dependencies retain their own licenses.

## ODM-XML 2.0

```python
from piojson import read_odm, write_odm

document = read_odm("study.xml")
root_copy = document.to_element()  # detached copy for inspection
write_odm(document, "study-copy.xml")
```

ODM support reads and writes XML trees, retaining clinical data, metadata,
child order, text, comments and extension elements. It does not flatten ODM
into pandas or invent an ODM-JSON representation. It supports the official
`http://www.cdisc.org/ns/odm/v2.0` namespace, not ODM 1.3.2.

Readers and writers perform basic format checks without XSD validation.
DTDs, entities and external references are rejected. The default input bound is
64 MiB; change `max_bytes` explicitly for larger trusted inputs. Document-provided schema locations are never fetched. Output is atomic
UTF-8 XML. Namespace prefixes, whitespace formatting, XML declarations and
processing instructions are not promised byte-identical round trips.
The package does not perform standards certification, reference reconciliation,
clinical consistency checks or regulatory review.
