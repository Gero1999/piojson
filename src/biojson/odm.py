"""Safe, lossless-in-structure ODM 2.0 XML access (not an invented JSON mapping)."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import os
import stat
import tempfile
import xml.etree.ElementTree as ET
from defusedxml.ElementTree import DefusedXMLParser

ODM_NAMESPACE = 'http://www.cdisc.org/ns/odm/v2.0'

@dataclass
class ODMDocument:
    root: ET.Element

    def to_element(self):
        """Return a detached tree, retaining metadata, clinical data and extensions."""
        return deepcopy(self.root)


def _check_root(root):
    if root.tag != '{' + ODM_NAMESPACE + '}ODM':
        raise ValueError('Expected an ODM 2.0 namespaced XML root')
    if root.get('ODMVersion') not in {None, '2.0', '2.0.0'}:
        raise ValueError('Only ODM 2.0 is supported')
    if root.get('FileType') not in {'Snapshot', 'Transactional'}:
        raise ValueError('Unsupported ODM FileType')
    for key in ('FileOID', 'FileType', 'CreationDateTime'):
        if not root.get(key):
            raise ValueError('Missing ODM root attribute: ' + key)


def read_odm(file_path, *, max_bytes=64 * 1024 * 1024):
    """Read ODM XML with DTDs/entities disabled and no schema lookup.

    max_bytes bounds parser input (default 64 MiB). Namespace, attributes, child
    order, text, tails, comments and extension elements are retained. Prefixes
    and byte formatting are not guaranteed to be identical on write.
    """
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError('max_bytes must be a positive integer')
    with open(file_path, 'rb') as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError('ODM input exceeds max_bytes')
    parser = DefusedXMLParser(target=ET.TreeBuilder(insert_comments=True),
        forbid_dtd=True, forbid_entities=True, forbid_external=True)
    root = ET.fromstring(data, parser=parser)
    _check_root(root)
    return ODMDocument(root)


def write_odm(document, file_path):
    """Atomically write a detached ODMDocument as UTF-8 XML."""
    if not isinstance(document, ODMDocument):
        raise TypeError('Expected an ODMDocument')
    root = document.to_element()
    _check_root(root)
    destination = Path(file_path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=destination.parent,
                prefix='.' + destination.name + '.', delete=False) as stream:
            temporary = Path(stream.name)
            ET.ElementTree(root).write(stream, encoding='utf-8', xml_declaration=True)
            stream.flush()
            os.fsync(stream.fileno())
        if destination.exists():
            os.chmod(temporary, stat.S_IMODE(destination.stat().st_mode))
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
