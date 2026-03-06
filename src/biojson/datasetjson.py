import json
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
        data["records"] = len(self.df)
        data["columns"] = self.columns_metadata
        df_to_write = self.df.copy()
        datatypes = {col["name"]: col.get("dataType", "string") for col in self.columns_metadata}
        for col, dtype in datatypes.items():
            if dtype == "date":
                df_to_write[col] = pd.to_datetime(df_to_write[col], errors="coerce").dt.strftime("%Y-%m-%d")
            def to_dict(self):
                data = deepcopy(self.metadata)
                data["datasetJSONCreationDateTime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                data["records"] = len(self.df)
                data["columns"] = self.columns_metadata
                df_to_write = self.df.copy()
                datatypes = {col["name"]: col.get("dataType", "string") for col in self.columns_metadata}
                for col, dtype in datatypes.items():
                    if dtype == "date":
                        df_to_write[col] = pd.to_datetime(df_to_write[col], errors="coerce").dt.strftime("%Y-%m-%d")
                    elif dtype == "datetime":
                        df_to_write[col] = pd.to_datetime(df_to_write[col], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")
                data["rows"] = df_to_write.where(pd.notnull(df_to_write), None).values.tolist()
                return data
                df_to_write[col] = pd.to_datetime(df_to_write[col], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")
        data["rows"] = df_to_write.where(pd.notnull(df_to_write), None).values.tolist()
        return data

def read_datasetjson(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    columns_metadata = data["columns"]
    columns = [col["name"] for col in columns_metadata]
    rows = data["rows"]
    labels = [col["label"] for col in columns_metadata]
    datatypes = {col["name"]: col.get("dataType", "string") for col in columns_metadata}

    df = pd.DataFrame(rows, columns=columns)

    # Convert columns to appropriate types
    for col, dtype in datatypes.items():
        if dtype == "date" or dtype == "datetime":
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif dtype == "integer":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif dtype == "float" or dtype == "double" or dtype == "number":
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif dtype == "boolean":
            df[col] = df[col].map(
                lambda x: True
                if x is True or x == "Y" or x == "TRUE"
                else (
                    False
                    if x is False or x == "N" or x == "FALSE"
                    else pd.NA
                )
            )
        else:
            df[col] = df[col].astype("string")

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
        with open(file_path, "w") as f:
            json.dump(df.to_dict(), f, indent=4)
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
            dataType = 'date'
            df_to_write[col] = df_to_write[col].dt.strftime("%Y-%m-%d")
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

    data['rows'] = df_to_write.where(pd.notnull(df_to_write), None).values.tolist()

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
