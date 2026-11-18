import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from defusedxml.common import DefusedXmlException
from piojson import read_odm,write_odm

XML='''<ODM xmlns="http://www.cdisc.org/ns/odm/v2.0" FileOID="MOCK" FileType="Snapshot" ODMVersion="2.0" CreationDateTime="2026-01-02T12:00:00Z"><!--synthetic--><ClinicalData StudyOID="MOCK" MetaDataVersionOID="MDV"><SubjectData SubjectKey="MOCK-001"/></ClinicalData></ODM>'''
class ODMTests(unittest.TestCase):
    def test_tree_roundtrip_and_detached_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a.xml';b=Path(folder)/'b.xml';a.write_text(XML)
            doc=read_odm(a);before=ET.tostring(doc.root)
            copy=doc.to_element();copy.set('FileOID','changed')
            write_odm(doc,b);after=read_odm(b)
            self.assertEqual(ET.tostring(after.root),before)
            self.assertEqual(doc.root.get('FileOID'),'MOCK')
    def test_entities_and_size_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.xml';p.write_text('<!DOCTYPE ODM [<!ENTITY x SYSTEM "file:///etc/passwd">]>'+XML)
            with self.assertRaises(DefusedXmlException):read_odm(p)
            p.write_text(XML)
            with self.assertRaisesRegex(ValueError,'max_bytes'):read_odm(p,max_bytes=10)
