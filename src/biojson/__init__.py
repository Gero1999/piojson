"""Compatibility imports for applications using the previous package name."""
from .__about__ import __version__
from .datasetjson import DatasetJSON, read_datasetjson, write_datasetjson, validate_datasetjson

__all__ = ['DatasetJSON', 'read_datasetjson', 'write_datasetjson', 'validate_datasetjson', '__version__']

from biojson.odm import ODMDocument, read_odm, write_odm
__all__ += ["ODMDocument", "read_odm", "write_odm"]
