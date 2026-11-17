"""Compatibility imports for applications using the previous package name."""
from .__about__ import __version__
from .datasetjson import DatasetJSON, read_datasetjson, write_datasetjson, validate_datasetjson

__all__ = ['DatasetJSON', 'read_datasetjson', 'write_datasetjson', 'validate_datasetjson', '__version__']
