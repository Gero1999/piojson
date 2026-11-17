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
    for key in ('FileOID', 'FileType', 'CreationDateTime'):
        if not root.get(key):
            raise ValueError('Missing ODM root attribute: ' + key)


def read_odm(file_path, *, max_bytes=64 * 1024 * 1024, schema_validate=True):
    """Read ODM XML without DTDs/entities; full XSD validation is separate.

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
    document = ODMDocument(root)
    if schema_validate:
        validate_odm(document)
    return document


def write_odm(document, file_path, *, schema_validate=True):
    """Atomically write a detached ODMDocument as UTF-8 XML."""
    if not isinstance(document, ODMDocument):
        raise TypeError('Expected an ODMDocument')
    root = document.to_element()
    _check_root(root)
    # Check well-formedness even when full schema validation is disabled.
    parser = DefusedXMLParser(forbid_dtd=True, forbid_entities=True, forbid_external=True)
    ET.fromstring(ET.tostring(root, encoding="utf-8"), parser=parser)
    if schema_validate:
        validate_odm(document)
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


def validate_odm(document):
    """Validate an ODMDocument against the pinned official ODM 2.0 XSD bundle.

    All schema imports resolve only inside the bundled directory; validation
    never fetches remote resources. XSD validation is not Schematron checking
    or a clinical/business-rule certification.
    """
    from lxml import etree
    from urllib.parse import urlsplit, unquote
    if not isinstance(document, ODMDocument):
        raise TypeError("Expected an ODMDocument")
    _check_root(document.root)
    directory = Path(__file__).parent / "schemas" / "odm"
    allowed = {path.name for path in directory.glob("*.xsd")}
    class LocalSchemas(etree.Resolver):
        def resolve(self, url, public_id, context):
            name = Path(unquote(urlsplit(url).path)).name
            if name not in allowed:
                raise ValueError("Schema resource is not in the offline bundle")
            return self.resolve_filename(str(directory / name), context)
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    parser.resolvers.add(LocalSchemas())
    schema = etree.XMLSchema(etree.parse(str(directory / "ODM.xsd"), parser))
    try:
        root = etree.fromstring(ET.tostring(document.root, encoding="utf-8"),
            etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True))
    except etree.XMLSyntaxError:
        raise ValueError("ODM document is not well-formed XML") from None
    if not schema.validate(root):
        error = schema.error_log.last_error
        raise ValueError("ODM schema validation failed at " + (error.path or "/ODM"))
