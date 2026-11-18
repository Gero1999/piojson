"""Public package name; biojson imports remain available for compatibility."""
from biojson.__about__ import __version__
from biojson.datasetjson import DatasetJSON, read_datasetjson, write_datasetjson

__all__ = ['DatasetJSON', 'read_datasetjson', 'write_datasetjson', '__version__']
