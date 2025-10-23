#!/usr/bin/env python3
"""
Migrate Existing Extraction Runs to Specimen Index

Analyzes raw.jsonl files from existing extraction runs and populates
the specimen index with:
- Specimen records (derived from image hashes)
- Extraction results
- Aggregated candidates per specimen
- Data quality flags for duplicates

Usage:
    python scripts/migrate_to_specimen_index.py \\
        --run-dir full_dataset_processing/run_20250930_181456 \\
        --index specimen_index.db \\
        --analyze-duplicates

    # Or migrate multiple runs:
    python scripts/migrate_to_specimen_index.py \\
        --run-dir full_dataset_processing/* \\
        --index specimen_index.db
"""

import argparse
import json
import logging
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.provenance.specimen_index import (
    ExtractionResult,
    SpecimenIndex,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ExtractionRunMigrator:
    """Migrates existing extraction runs to specimen index."""

    def __init__(self, index: SpecimenIndex):
        self.index = index
        self.stats = {
            "specimens_created": 0,
            "extractions_recorded": 0,
            "duplicates_found": 0,
            "errors": 0,
        }

    def migrate_run(self, run_dir: Path, dry_run: bool = False):
        """
        Migrate a single extraction run.

        Args:
            run_dir: Path to extraction run directory
            dry_run: If True, don't write to database
        """
        logger.info(f"Migrating run: {run_dir}")

        raw_jsonl = run_dir / "raw.jsonl"
        if not raw_jsonl.exists():
            logger.error(f"No raw.jsonl found in {run_dir}")
            self.stats["errors"] += 1
            return

        manifest = run_dir / "manifest.json"
        run_config = {}
        if manifest.exists():
            with open(manifest) as f:
                manifest_data = json.load(f)
                run_config = manifest_data.get("config", {})

        # Read all extractions
        extractions: List[Dict] = []
        with open(raw_jsonl) as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line)
                        data["_line_num"] = line_num
                        extractions.append(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse line {line_num}: {e}")
                        self.stats["errors"] += 1

        logger.info(f"Found {len(extractions)} extraction results")

        # Group by image (specimen ID = image hash without extension)
        specimens: Dict[str, List[Dict]] = defaultdict(list)

        for extraction in extractions:
            image = extraction.get("image", "")
            sha256 = extraction.get("sha256", "")

            # Use SHA256 as specimen ID (content-addressed)
            if sha256:
                specimen_id = sha256
            elif image:
                # Extract hash from filename
                specimen_id = image.rsplit(".", 1)[0]
            else:
                logger.warning(f"No image/sha256 in extraction at line {extraction['_line_num']}")
                self.stats["errors"] += 1
                continue

            specimens[specimen_id].append(extraction)

        logger.info(f"Grouped into {len(specimens)} unique specimens")

        # Find duplicates (same specimen extracted multiple times)
        duplicates = {
            spec_id: results for spec_id, results in specimens.items() if len(results) > 1
        }

        if duplicates:
            logger.warning(f"Found {len(duplicates)} specimens with duplicate extractions:")
            for spec_id, results in list(duplicates.items())[:5]:
                logger.warning(f"  {spec_id[:16]}... extracted {len(results)} times")
            self.stats["duplicates_found"] += len(duplicates)

        if dry_run:
            logger.info("DRY RUN: Would create specimen records and extractions")
            return

        # Create specimen records and extraction results
        run_id = manifest_data.get("run_id", run_dir.name) if manifest.exists() else run_dir.name

        for specimen_id, results in specimens.items():
            # Register specimen
            created = self.index.register_specimen(specimen_id=specimen_id, camera_filename=None)
            if created:
                self.stats["specimens_created"] += 1

            # Register each extraction
            for result_data in results:
                extraction_result = self._parse_extraction(
                    specimen_id, result_data, run_id, run_config
                )

                if extraction_result:
                    self.index.record_extraction(extraction_result)
                    self.stats["extractions_recorded"] += 1

            # Aggregate extractions for this specimen
            if len(results) > 0:
                self.index.aggregate_specimen_extractions(specimen_id)

        logger.info(
            f"Migration complete: "
            f"{self.stats['specimens_created']} specimens, "
            f"{self.stats['extractions_recorded']} extractions"
        )

    def _parse_extraction(
        self, specimen_id: str, result_data: Dict, run_id: str, run_config: Dict
    ) -> ExtractionResult:
        """Parse extraction result from raw.jsonl entry."""
        # Generate extraction ID
        extraction_id = str(uuid.uuid4())

        # Extract DwC fields
        dwc_fields = result_data.get("dwc", {})

        # Determine status
        if result_data.get("errors"):
            status = "failed"
        elif dwc_fields:
            status = "completed"
        else:
            status = "failed"

        # Extract parameters for deduplication
        extraction_params = {
            "engine": result_data.get("engine"),
            "engine_version": result_data.get("engine_version"),
            "model": run_config.get("gpt4o", {}).get("model"),
            "prompt_dir": run_config.get("gpt4o", {}).get("prompt_dir"),
        }

        params_hash = SpecimenIndex._hash_params(extraction_params)

        return ExtractionResult(
            extraction_id=extraction_id,
            specimen_id=specimen_id,
            image_sha256=result_data.get("sha256", specimen_id),
            params_hash=params_hash,
            run_id=run_id,
            status=status,
            dwc_fields=dwc_fields,
            raw_jsonl_offset=result_data.get("_line_num"),
            timestamp=None,
        )

    def analyze_duplicates(self):
        """Analyze and report on duplicate extractions."""
        logger.info("Analyzing duplicate extractions...")

        # Find specimens with multiple extractions
        rows = self.index.conn.execute("""
            SELECT
                specimen_id,
                COUNT(*) as extraction_count,
                GROUP_CONCAT(extraction_id) as extraction_ids
            FROM extractions
            GROUP BY specimen_id
            HAVING extraction_count > 1
            ORDER BY extraction_count DESC
        """).fetchall()

        if not rows:
            logger.info("No duplicate extractions found")
            return

        logger.warning(f"Found {len(rows)} specimens with duplicate extractions:")

        for i, row in enumerate(rows[:10], 1):
            logger.warning(
                f"  {i}. Specimen {row['specimen_id'][:16]}... "
                f"extracted {row['extraction_count']} times"
            )

        # Check if duplicates are identical (same params)
        identical_count = 0
        different_count = 0

        for row in rows:
            extraction_ids = row["extraction_ids"].split(",")

            # Get params hashes for this specimen's extractions
            params_hashes = set()
            for ext_id in extraction_ids:
                params_row = self.index.conn.execute(
                    "SELECT params_hash FROM extractions WHERE extraction_id = ?", (ext_id,)
                ).fetchone()
                if params_row:
                    params_hashes.add(params_row["params_hash"])

            if len(params_hashes) == 1:
                identical_count += 1
            else:
                different_count += 1

        logger.info(
            f"Duplicate analysis:\n"
            f"  - {identical_count} specimens extracted multiple times with IDENTICAL params\n"
            f"  - {different_count} specimens extracted multiple times with DIFFERENT params"
        )

        if identical_count > 0:
            logger.warning(
                f"⚠️  {identical_count} specimens have redundant extractions (identical params)"
            )
            logger.warning(
                "   These could have been avoided with deduplication at (image, params) level"
            )

    def check_data_quality(self):
        """Run all data quality checks."""
        logger.info("Running data quality checks...")

        # Check catalog number duplicates
        dup_count = self.index.check_catalog_number_duplicates()
        logger.info(f"  - Catalog number duplicates: {dup_count}")

        # Check malformed catalog numbers
        malformed_count = self.index.check_malformed_catalog_numbers()
        logger.info(f"  - Malformed catalog numbers: {malformed_count}")

        # Get all flags
        all_flags = self.index.conn.execute("""
            SELECT flag_type, severity, COUNT(*) as count
            FROM data_quality_flags
            WHERE resolved = FALSE
            GROUP BY flag_type, severity
            ORDER BY severity, count DESC
        """).fetchall()

        logger.info(f"Data quality flags: {len(all_flags)} types")
        for flag in all_flags:
            logger.info(f"  - {flag['flag_type']} ({flag['severity']}): {flag['count']}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate existing extraction runs to specimen index"
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Extraction run directory (or glob pattern for multiple)",
    )
    parser.add_argument(
        "--index", type=Path, default="specimen_index.db", help="Specimen index database path"
    )
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument(
        "--analyze-duplicates", action="store_true", help="Analyze duplicate extractions"
    )
    parser.add_argument(
        "--check-quality", action="store_true", help="Run data quality checks after migration"
    )

    args = parser.parse_args()

    # Initialize index
    index = SpecimenIndex(args.index)

    # Print initial stats
    logger.info("Specimen index stats (before migration):")
    for key, value in index.get_stats().items():
        logger.info(f"  {key}: {value}")

    # Migrate run(s)
    migrator = ExtractionRunMigrator(index)

    # Handle glob patterns
    run_dirs = []
    if "*" in str(args.run_dir):
        run_dirs = list(args.run_dir.parent.glob(args.run_dir.name))
    else:
        run_dirs = [args.run_dir]

    logger.info(f"Migrating {len(run_dirs)} run(s)...")

    for run_dir in run_dirs:
        if run_dir.is_dir():
            migrator.migrate_run(run_dir, dry_run=args.dry_run)
        else:
            logger.warning(f"Skipping non-directory: {run_dir}")

    # Print final stats
    logger.info("\nSpecimen index stats (after migration):")
    for key, value in index.get_stats().items():
        logger.info(f"  {key}: {value}")

    # Analyze duplicates if requested
    if args.analyze_duplicates:
        migrator.analyze_duplicates()

    # Check data quality if requested
    if args.check_quality:
        migrator.check_data_quality()

    # Print migration stats
    logger.info("\nMigration stats:")
    for key, value in migrator.stats.items():
        logger.info(f"  {key}: {value}")

    index.close()


if __name__ == "__main__":
    main()
