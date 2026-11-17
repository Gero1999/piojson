# Schema provenance

Dataset-JSON schema: cdisc-org/DataExchange-DatasetJson, tag v1.1,
commit f735969cdf3b6af87a0fcbd064c49e9274f69c5e, schema/dataset.schema.json.
Source: https://github.com/cdisc-org/DataExchange-DatasetJson/tree/v1.1/schema
The unmodified schema is bundled for offline validation under MIT; its complete
copyright and license notice is adjacent to it in schemas/LICENSE-DatasetJSON.txt.
SHA-256: dd7190ff3782edf31f7de42a3d68c2328e6194e62f9dfbdc2e776edfea2eb09c

Schema validation is supplemented with record counts, unique columns, row width,
column/cell types and complete ISO temporal values. This is a software validation
contract, not CDISC certification. Readers always check structure and values;
full schema checks are opt-in on read and enabled by default on write.

ODM 2.0 XSD files: cdisc-org/DataExchange-ODM, commit
6cb00a9cb38f245069758a7c5a6823cdf3ea48be, schema/*.xsd.
Source: https://github.com/cdisc-org/DataExchange-ODM/tree/6cb00a9cb38f245069758a7c5a6823cdf3ea48be/schema
The unmodified files and MIT notice are bundled under schemas/odm/.
Imports are resolved against this local bundle only. No online schema lookup
is performed. XSD checks do not cover separate Schematron rules or establish
clinical correctness, regulatory acceptance or certification.

The ODM XHTML file is explicitly derived from W3C via FHIR. All embedded
copyright/modification notices are retained. The bundle also includes W3C and
HL7/FHIR license texts and THIRD-PARTY-NOTICES.txt; the CDISC MIT notice does not
replace those upstream notices.
