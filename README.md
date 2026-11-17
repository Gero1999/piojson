# piojson: pharma & bio JSON standards

![piojson logo](docs/static/piojson-logo.png)

Read, edit, validate and write **CDISC Dataset-JSON 1.1.0** with pandas.
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
from piojson import read_datasetjson, write_datasetjson, validate_datasetjson

frame = pd.DataFrame({"SUBJID": ["MOCK-001", "MOCK-002"],
                      "AGE": pd.Series([35, None], dtype="Int64")})
frame.attrs["labels"] = {"SUBJID": "Synthetic subject", "AGE": "Age"}
write_datasetjson(frame, "dm.json", name="DM", label="Synthetic demographics",
                  studyOID="MOCK-STUDY", itemGroupOID="IG.DM")
dataset = read_datasetjson("dm.json", schema_validate=True)
dataset.df.loc[0, "AGE"] = 36
dataset.metadata["label"] = "Edited synthetic demographics"
validate_datasetjson(dataset)
write_datasetjson(dataset, "dm-edited.json")
```

Examples use generated demonstration data. They require no external service.

## Validation and round trips

- Readers check version, record count, row widths, unique columns and typed
  values. Invalid values raise an error naming the column and one-based row.
  `errors="coerce"` explicitly converts bad values to missing; schema checking
  can still reject the original invalid input when enabled.
- `schema_validate=True` opts into official schema checking on read; writers
  enable it by default. `validate_datasetjson()` runs schema and cell checks.
  The pinned schema and its MIT notice are bundled for offline use. See
  [schema provenance](docs/schema-provenance.md).
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

Schema checks are software checks, not CDISC certification. Only version 1.1.0
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
checkout to verify public imports, bundled schema access and a null round trip.

## Contributing and license

Report bugs and propose formats in the [issue tracker](https://github.com/Gero1999/piojson/issues).
Include a small synthetic example, expected behavior and package versions.
The project uses [Apache 2.0](LICENSE); bundled third-party schemas retain their
own accompanying notices.

## ODM-XML 2.0

```python
from piojson import read_odm, validate_odm, write_odm

document = read_odm("study.xml")
root_copy = document.to_element()  # detached copy for inspection
validate_odm(document)
write_odm(document, "study-copy.xml")
```

ODM support reads and writes XML trees, retaining clinical data, metadata,
child order, text, comments and extension elements. It does not flatten ODM
into pandas or invent an ODM-JSON representation. It supports the official
`http://www.cdisc.org/ns/odm/v2.0` namespace, not ODM 1.3.2.

Readers and writers validate against the bundled official ODM 2.0 XSDs by
default; `schema_validate=False` permits structurally checked partial documents.
DTDs, entities and external references are rejected. The default input bound is
64 MiB; change `max_bytes` explicitly for larger trusted inputs. XSD imports
resolve locally, never from document-provided remote locations. Output is atomic
UTF-8 XML. Namespace prefixes, whitespace formatting, XML declarations and
processing instructions are not promised byte-identical round trips.
XSD validity does not replace Schematron rules, reference reconciliation,
clinical consistency checks or regulatory review.
