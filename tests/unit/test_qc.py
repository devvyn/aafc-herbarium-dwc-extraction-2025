import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import qc


def test_detect_duplicates_hash_collision():
    catalog = {}
    sha = "a" * 64
    assert qc.detect_duplicates(catalog, sha, 10) == []
    assert qc.detect_duplicates(catalog, sha, 10) == ["duplicate:sha256"]


def test_detect_duplicates_phash_collision():
    catalog = {}
    sha1 = "0" * 64
    sha2 = "0" * 63 + "1"
    qc.detect_duplicates(catalog, sha1, 10)
    assert qc.detect_duplicates(catalog, sha2, 10) == ["duplicate:phash"]


def test_flag_low_confidence():
    assert qc.flag_low_confidence(0.5, 0.7) == ["low_confidence"]
    assert qc.flag_low_confidence(0.9, 0.7) == []


def test_flag_top_fifth():
    qc.TOP_FIFTH_PCT = 20
    assert qc.flag_top_fifth(80) == ["top_fifth_scan"]
    assert qc.flag_top_fifth(50) == []
