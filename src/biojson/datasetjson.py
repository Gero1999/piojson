from __future__ import annotations

import json
import math
import os
import stat
import tempfile
from pathlib import Path
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class DatasetJSON:
    df: pd.DataFrame
    metadata: dict
    columns_metadata: list[dict]

    def to_dict(self):
        data = deepcopy(self.metadata)
        data["datasetJSONCreationDateTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        data["records"] = len(self.df)
        data["columns"] = deepcopy(self.columns_metadata)
        names = [column["name"] for column in self.columns_metadata]
        if len(set(names)) != len(names) or not self.df.columns.is_unique:
            raise ValueError("Column names must be unique")
        if set(names) != set(self.df.columns):
            raise ValueError("DataFrame columns must match column metadata exactly")
        df_to_write = self.df.loc[:, names].copy()
        datatypes = {col["name"]: col.get("dataType", "string") for col in self.columns_metadata}
        for col, dtype in datatypes.items():
            if dtype == "date":
                df_to_write[col] = _temporal_values(df_to_write[col], "date")
            elif dtype == "datetime":
                df_to_write[col] = _temporal_values(df_to_write[col], "datetime")
        data["rows"] = _json_rows(df_to_write)
        return data

def read_datasetjson(file_path, *, errors="raise"):
    if errors not in {"raise", "coerce"}:
        raise ValueError("errors must be raise or coerce")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f, parse_constant=_reject_constant, object_pairs_hook=_unique_keys)
    _validate_structure(data)

    columns_metadata = data["columns"]
    columns = [col["name"] for col in columns_metadata]
    rows = data["rows"]
    labels = [col["label"] for col in columns_metadata]
    datatypes = {col["name"]: col.get("dataType", "string") for col in columns_metadata}

    df = pd.DataFrame(rows, columns=columns, dtype=object)

    for col, dtype in datatypes.items():
        df[col] = _convert_column(df[col], dtype, errors)

    df.attrs["labels"] = dict(zip(columns, labels))
    metadata = {k: v for k, v in data.items() if k not in ["columns", "rows", "records"]}
    return DatasetJSON(df=df, metadata=metadata, columns_metadata=columns_metadata)


def write_datasetjson(
    df,
    file_path,
    name=None,
    label=None,
    datasetJSONVersion="1.1.0",
    dbLastModifiedDateTime=None,
    studyOID=None,
    metaDataVersionOID=None,
    metaDataRef=None,
    itemGroupOID=None,
):
    if isinstance(df, DatasetJSON):
        # Validate datasetJSONVersion from the DatasetJSON.metadata if present
        metadata_version = None
        try:
            if isinstance(df.metadata, dict):
                metadata_version = df.metadata.get("datasetJSONVersion")
        except AttributeError:
            metadata_version = None
        if metadata_version is not None and metadata_version != "1.1.0":
            raise ValueError("Only datasetJSON version 1.1.0 is supported.")
        _write_json(df.to_dict(), file_path)
        return

    if datasetJSONVersion != "1.1.0":
        raise ValueError("Only datasetJSON version 1.1.0 is supported.")

    data = {}
    data['datasetJSONCreationDateTime'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data['datasetJSONVersion'] = datasetJSONVersion
    data['fileOID'] = "generated.by.biojson"
    data['dbLastModifiedDateTime'] = dbLastModifiedDateTime if dbLastModifiedDateTime else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data['originator'] = "biojson"
    data['sourceSystem'] = {
        "name": "biojson",
        "version": "1.0.0"
    }
    data['studyOID'] = studyOID if studyOID else "unknown.study"
    data['metaDataVersionOID'] = metaDataVersionOID if metaDataVersionOID else "unknown.mdv"
    data['metaDataRef'] = metaDataRef if metaDataRef else "http://unknown.metadata.ref"
    data['itemGroupOID'] = itemGroupOID if itemGroupOID else "IG.UNKNOWN"
    data['records'] = len(df)
    data['name'] = name if name else "UNKNOWN"
    data['label'] = label if label else "Unknown Label"


    columns = []
    df_to_write = df.copy()
    for col in df.columns:
        # Determine dataType for JSON schema
        dtype = df[col].dtype
        if pd.api.types.is_datetime64_any_dtype(dtype):
            dataType = 'datetime'
            df_to_write[col] = _temporal_values(df_to_write[col], 'datetime')
        elif pd.api.types.is_integer_dtype(dtype):
            dataType = 'integer'
            # Ensure integers remain as int, not string
            df_to_write[col] = df_to_write[col].astype('Int64')
        elif pd.api.types.is_float_dtype(dtype):
            dataType = 'float'
        elif pd.api.types.is_bool_dtype(dtype):
            dataType = 'boolean'
        else:
            dataType = 'string'
            df_to_write[col] = df_to_write[col].astype('string')
        col_meta = {
            "itemOID": f"IT.{data['itemGroupOID']}.{col}",
            "name": col,
            "label": df.attrs.get('labels', {}).get(col, col),
            "dataType": dataType
        }
        columns.append(col_meta)
    data['columns'] = columns

    metadata = {key: value for key, value in data.items() if key not in {"columns", "rows", "records"}}
    document = DatasetJSON(df_to_write, metadata, columns)
    _write_json(document.to_dict(), file_path)


def _write_json(payload, file_path):
    destination = Path(file_path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                         prefix="." + destination.name + ".", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, indent=4, allow_nan=False, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        if destination.exists():
            os.chmod(temporary, stat.S_IMODE(destination.stat().st_mode))
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _json_rows(frame):
    def scalar(value):
        if pd.isna(value):
            return None
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Non-finite numeric value cannot be written as JSON")
        return value
    return [[scalar(value) for value in row] for row in frame.itertuples(index=False, name=None)]


def _temporal_values(series, kind):
    def format_value(value):
        if pd.isna(value):
            return None
        stamp = pd.Timestamp(value)
        return stamp.date().isoformat() if kind == "date" else stamp.isoformat()
    return series.map(format_value)


def _reject_constant(value):
    raise ValueError("Non-standard JSON constant: " + value)


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON property: " + key)
        result[key] = value
    return result


def _validate_structure(data):
    if not isinstance(data, dict):
        raise ValueError("Dataset-JSON must be an object")
    if data.get("datasetJSONVersion") != "1.1.0":
        raise ValueError("Only datasetJSON version 1.1.0 is supported.")
    columns, rows = data.get("columns"), data.get("rows")
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ValueError("columns and rows must be arrays")
    names = []
    allowed = {"string", "integer", "decimal", "float", "double", "number", "boolean", "date", "datetime", "time", "URI"}
    for index, column in enumerate(columns):
        if not isinstance(column, dict) or not isinstance(column.get("name"), str) or not column["name"]:
            raise ValueError("Invalid column name at position " + str(index))
        if not isinstance(column.get("label"), str):
            raise ValueError("Missing or invalid label for column " + column["name"])
        if column.get("dataType", "string") not in allowed:
            raise ValueError("Unknown dataType for column " + column["name"])
        names.append(column["name"])
    if len(set(names)) != len(names):
        raise ValueError("Column names must be unique")
    if any(not isinstance(row, list) or len(row) != len(columns) for row in rows):
        raise ValueError("Every row must match the declared column count")
    records = data.get("records")
    if isinstance(records, bool) or not isinstance(records, int) or records != len(rows):
        raise ValueError("records must equal the number of rows")


def _convert_column(series, dtype, errors):
    def convert(value):
        if value is None or value is pd.NA:
            return pd.NA
        if dtype in {"date", "datetime"}:
            return pd.Timestamp(value)
        if dtype == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str) and value.upper() in {"Y", "TRUE", "N", "FALSE"}:
                return value.upper() in {"Y", "TRUE"}
            raise ValueError("expected a boolean")
        if dtype in {"integer", "decimal", "float", "double", "number"}:
            if isinstance(value, bool):
                raise ValueError("boolean is not a numeric value")
            numeric = pd.to_numeric(value, errors="raise")
            if not math.isfinite(numeric) or (dtype == "integer" and numeric != int(numeric)):
                raise ValueError("invalid finite number")
            return int(numeric) if dtype == "integer" else numeric
        if not isinstance(value, str):
            raise ValueError("expected a string")
        return value
    values = []
    for row, value in enumerate(series):
        try:
            values.append(convert(value))
        except (ValueError, TypeError, OverflowError) as exc:
            if errors == "raise":
                raise ValueError(f"Column {series.name!r}, row {row + 1}: invalid {dtype} value") from exc
            values.append(pd.NA)
    if dtype == "integer":
        return pd.Series(values, index=series.index, dtype="Int64", name=series.name)
    if dtype == "boolean":
        return pd.Series(values, index=series.index, dtype="boolean", name=series.name)
    if dtype in {"decimal", "float", "double", "number"}:
        return pd.Series(values, index=series.index, dtype="Float64", name=series.name)
    if dtype in {"date", "datetime"}:
        # Preserve individual offsets if values cannot share one datetime dtype.
        clean = [pd.NaT if value is pd.NA else value for value in values]
        return pd.Series(clean, index=series.index, name=series.name)
    return pd.Series(values, index=series.index, dtype="string", name=series.name)
