from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

from dwc.schema import DWC_TERMS
from io_utils.write import (
    write_dwc_csv,
    write_identification_history_csv,
    IDENT_HISTORY_COLUMNS,
)
from dwc.archive import write_meta_xml, build_dwca


def _write_csvs(out: Path) -> None:
    write_dwc_csv(out, [{"occurrenceID": "1"}])
    write_identification_history_csv(
        out,
        [
            {
                "occurrenceID": "1",
                "identificationID": "a",
                "identifiedBy": "x",
                "isCurrent": "TRUE",
            }
        ],
    )


def test_meta_xml_generation(tmp_path: Path) -> None:
    _write_csvs(tmp_path)
    meta_path = write_meta_xml(tmp_path)
    assert meta_path.exists()
    tree = ET.parse(meta_path)
    ns = {"dwc": "http://rs.tdwg.org/dwc/text/"}
    core_fields = tree.getroot().findall("dwc:core/dwc:field", ns)
    ext_fields = tree.getroot().findall("dwc:extension/dwc:field", ns)
    assert len(core_fields) == len(DWC_TERMS)
    assert len(ext_fields) == len(IDENT_HISTORY_COLUMNS)


def test_dwca_zip_contains_all_files(tmp_path: Path) -> None:
    _write_csvs(tmp_path)
    zip_path = build_dwca(tmp_path, compress=True)
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
    assert names == {"occurrence.csv", "identification_history.csv", "meta.xml"}
