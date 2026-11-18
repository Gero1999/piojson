"""Dataset-JSON public API, shared with the legacy biojson implementation."""
from biojson.datasetjson import DatasetJSON, read_datasetjson, write_datasetjson

__all__ = ['DatasetJSON', 'read_datasetjson', 'write_datasetjson']
