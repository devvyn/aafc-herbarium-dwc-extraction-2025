from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import json

from dwc.archive import create_archive
from dwc.schema import DWC_TERMS
from io_utils.write import (
    write_dwc_csv,
    write_identification_history_csv,
    IDENT_HISTORY_COLUMNS,
)


def _prepare_csvs(output_dir: Path) -> None:
    write_dwc_csv(output_dir, [])
    write_identification_history_csv(output_dir, [])


def test_meta_xml_written(tmp_path: Path) -> None:
    _prepare_csvs(tmp_path)
    create_archive(tmp_path, compress=False, filters={"basisOfRecord": "specimen"})
    meta_path = tmp_path / "meta.xml"
    assert meta_path.exists()

    tree = ET.parse(meta_path)
    ns = {"dwc": "http://rs.tdwg.org/dwc/text/"}
    core = tree.getroot().find("dwc:core", ns)
    assert core is not None
    fields = core.findall("dwc:field", ns)
    assert len(fields) == len(DWC_TERMS)

    ext = tree.getroot().find("dwc:extension", ns)
    assert ext is not None
    ext_fields = ext.findall("dwc:field", ns)
    assert len(ext_fields) == len(IDENT_HISTORY_COLUMNS)


def test_zip_archive_contains_required_files(tmp_path: Path) -> None:
    _prepare_csvs(tmp_path)
    archive_path = create_archive(
        tmp_path, compress=True, version="1.2.3", filters={"foo": "bar"}
    )
    assert archive_path.exists()
    assert archive_path.name == "dwca_v1.2.3.zip"

    with zipfile.ZipFile(archive_path) as zf:
        names = set(zf.namelist())
        assert {
            "occurrence.csv",
            "identification_history.csv",
            "meta.xml",
            "manifest.json",
        } <= names

        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["filters"] == {"foo": "bar"}
        assert "commit" in manifest
        assert "timestamp" in manifest


def test_manifest_written(tmp_path: Path) -> None:
    _prepare_csvs(tmp_path)
    create_archive(tmp_path, compress=False, filters={"basisOfRecord": "specimen"})
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["filters"] == {"basisOfRecord": "specimen"}
    assert "commit" in manifest
    assert "timestamp" in manifest
