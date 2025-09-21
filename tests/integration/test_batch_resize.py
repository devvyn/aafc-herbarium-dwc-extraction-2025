from pathlib import Path

from PIL import Image

from scripts.batch_resize import resize_directory


def _make_image(path: Path, size: tuple[int, int]) -> None:
    Image.new("RGB", size, color="white").save(path)


def test_resize_directory_resizes_and_copies(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    large = input_dir / "large.jpg"
    small = input_dir / "small.png"
    nested_dir = input_dir / "nested"
    nested_dir.mkdir()
    nested_large = nested_dir / "nested_large.jpg"

    _make_image(large, (5000, 3000))
    _make_image(small, (800, 600))
    _make_image(nested_large, (4500, 4500))

    summary = resize_directory(input_dir, output_dir, max_dim=3000, dry_run=False)

    assert summary == {"total": 3, "resized": 2, "skipped": 0, "copied": 1}

    with Image.open(output_dir / "large.jpg") as img:
        assert max(img.size) == 3000
        assert img.size[0] == 3000
    with Image.open(output_dir / "nested" / "nested_large.jpg") as img:
        assert max(img.size) == 3000
    with Image.open(output_dir / "small.png") as img:
        assert img.size == (800, 600)


def test_resize_directory_dry_run(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    large = input_dir / "large.jpg"
    _make_image(large, (4001, 3000))

    summary = resize_directory(input_dir, None, max_dim=3500, dry_run=True)

    assert summary == {"total": 1, "resized": 1, "skipped": 0, "copied": 0}
    assert list(input_dir.glob("*")) == [large]
