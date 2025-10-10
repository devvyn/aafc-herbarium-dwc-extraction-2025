"""Batch resize helper for preprocessing herbarium images.

The script limits the longest edge for every image in an input directory to
reduce OCR latency.  It can operate in-place or mirror the resized files to an
output directory so the original images remain untouched.  By default the
maximum dimension is read from the repository's ``config.default.toml`` and can
be overridden on the command line.
"""

from __future__ import annotations

import argparse
import shutil
from importlib import resources
from pathlib import Path
import sys
from typing import Dict, Optional

from PIL import Image, ImageOps

from io_utils.read import iter_images
from preprocess import resize

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


def _deep_update(base: Dict[str, object], override: Dict[str, object]) -> Dict[str, object]:
    """Recursively merge ``override`` into ``base`` and return ``base``."""

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)  # type: ignore[arg-type]
        else:
            base[key] = value
    return base


def _load_preprocess_config(path: Optional[Path]) -> Dict[str, object]:
    """Return the merged configuration for the ``[preprocess]`` section."""

    cfg_path = resources.files("config").joinpath("config.default.toml")
    with cfg_path.open("rb") as handle:
        config = tomllib.load(handle)
    if path:
        with path.open("rb") as handle:
            user_cfg = tomllib.load(handle)
        _deep_update(config, user_cfg)
    return config.get("preprocess", {})  # type: ignore[return-value]


def _destination_path(source: Path, input_dir: Path, output_dir: Optional[Path]) -> Path:
    if output_dir is None:
        return source
    return output_dir / source.relative_to(input_dir)


def _save_image(img: Image.Image, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {"format": img.format} if img.format else {}
    img.save(destination, **save_kwargs)


def resize_directory(
    input_dir: Path,
    output_dir: Optional[Path],
    max_dim: int,
    dry_run: bool = False,
) -> Dict[str, int]:
    """Resize every image in ``input_dir`` and return a summary map."""

    if max_dim <= 0:
        raise ValueError("max_dim must be greater than zero")

    summary = {"total": 0, "resized": 0, "skipped": 0, "copied": 0}
    images = list(iter_images(input_dir))
    summary["total"] = len(images)

    for image_path in images:
        destination = _destination_path(image_path, input_dir, output_dir)

        with Image.open(image_path) as img:
            oriented = ImageOps.exif_transpose(img)
            longest_edge = max(oriented.size)

            if longest_edge <= max_dim:
                if output_dir is not None:
                    if not dry_run:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(image_path, destination)
                    summary["copied"] += 1
                else:
                    summary["skipped"] += 1
                continue

            if dry_run:
                summary["resized"] += 1
                continue

            resized = resize(oriented, max_dim)
            _save_image(resized, destination)
            summary["resized"] += 1

    return summary


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch resize herbarium images")
    parser.add_argument(
        "--input", type=Path, required=True, help="Directory containing source images"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional directory to mirror resized files; defaults to in-place updates",
    )
    parser.add_argument(
        "--config", type=Path, help="Optional configuration file merged over config.default.toml"
    )
    parser.add_argument("--max-dim", type=int, help="Maximum length of the longest edge in pixels")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    pre_cfg = _load_preprocess_config(args.config)
    default_max = int(pre_cfg.get("max_dim_px", 3072))
    max_dim = args.max_dim or default_max

    output_dir = args.output
    if output_dir and not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    summary = resize_directory(args.input, output_dir, max_dim, dry_run=args.dry_run)

    print(
        f"Processed {summary['total']} images: "
        f"{summary['resized']} resized, {summary['copied']} copied, {summary['skipped']} skipped"
    )

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
