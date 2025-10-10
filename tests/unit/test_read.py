import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from io_utils.read import iter_images, compute_sha256


def test_iter_images_supported_extensions(tmp_path: Path) -> None:
    # create files with supported and unsupported extensions
    (tmp_path / "img1.jpg").write_text("a")
    (tmp_path / "img2.jpeg").write_text("b")
    (tmp_path / "img3.PNG").write_text("c")
    (tmp_path / "doc.txt").write_text("d")
    (tmp_path / "img.gif").write_text("e")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "img4.jpg").write_text("f")
    (sub / "note.md").write_text("g")
    images = list(iter_images(tmp_path))
    expected = sorted(
        [
            tmp_path / "img1.jpg",
            tmp_path / "img2.jpeg",
            tmp_path / "img3.PNG",
            sub / "img4.jpg",
        ],
        key=lambda p: str(p),
    )
    assert images == expected


def test_compute_sha256_hash(tmp_path: Path) -> None:
    data = b"hello"
    file_path = tmp_path / "file.txt"
    file_path.write_bytes(data)
    expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert compute_sha256(file_path) == expected


def test_iter_images_custom_extensions(tmp_path: Path) -> None:
    (tmp_path / "sheet.tif").write_text("a")
    (tmp_path / "slide.TIFF").write_text("b")
    (tmp_path / "photo.jpg").write_text("c")

    images = list(iter_images(tmp_path, extensions={"tif", ".tiff"}))

    assert images == sorted([tmp_path / "sheet.tif", tmp_path / "slide.TIFF"], key=lambda p: str(p))
