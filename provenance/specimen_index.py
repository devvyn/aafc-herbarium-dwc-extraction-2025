"""
Specimen-Centric Provenance Index

Tracks specimens through image transformations, extraction runs, and human review.
See docs/specimen_provenance_architecture.md for full design.

Key features:
- Specimen identity tracking (camera filename → specimen ID)
- Image transformation provenance (original → derivatives)
- Extraction deduplication at (image, params) level
- Multi-extraction aggregation per specimen
- Data quality flagging
"""

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class OriginalFile:
    """Original camera file for a specimen."""

    sha256: str
    specimen_id: str
    file_path: str
    format: str
    dimensions: Optional[Tuple[int, int]] = None
    size_bytes: Optional[int] = None
    role: str = "original_photo"  # or 'original_raw'
    captured_at: Optional[datetime] = None


@dataclass
class ImageTransformation:
    """Content-addressed derivative image with provenance."""

    sha256: str
    specimen_id: str
    derived_from: str
    operation: str
    params: Dict[str, Any]
    timestamp: datetime
    tool: Optional[str] = None
    tool_version: Optional[str] = None
    stored_at: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of running extraction on an image with specific parameters."""

    extraction_id: str
    specimen_id: str
    image_sha256: str
    params_hash: str
    run_id: str
    status: str
    dwc_fields: Dict[str, Dict[str, Any]]
    raw_jsonl_offset: Optional[int] = None
    timestamp: Optional[datetime] = None


@dataclass
class DataQualityFlag:
    """Data quality issue flagged for a specimen."""

    specimen_id: str
    flag_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    resolved: bool = False


class SpecimenIndex:
    """
    Central index tracking specimens and their provenance.

    Maintains specimen identity, image transformations, extraction results,
    and data quality flags in a SQLite database.
    """

    def __init__(self, db_path: Path):
        """
        Initialize specimen index.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

        logger.info(f"Specimen index initialized: {self.db_path}")

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        with self.conn:
            # Specimens table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS specimens (
                    specimen_id TEXT PRIMARY KEY,
                    camera_filename TEXT UNIQUE,
                    expected_catalog_number TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Original files
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS original_files (
                    sha256 TEXT PRIMARY KEY,
                    specimen_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    format TEXT,
                    dimensions_json TEXT,
                    size_bytes INTEGER,
                    role TEXT,
                    captured_at TIMESTAMP,
                    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
                )
            """)

            # Image transformations
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS image_transformations (
                    sha256 TEXT PRIMARY KEY,
                    specimen_id TEXT NOT NULL,
                    derived_from TEXT NOT NULL,
                    operation TEXT,
                    params_json TEXT,
                    timestamp TIMESTAMP,
                    tool TEXT,
                    tool_version TEXT,
                    stored_at TEXT,
                    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id),
                    FOREIGN KEY (derived_from) REFERENCES original_files(sha256)
                )
            """)

            # Extractions
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS extractions (
                    extraction_id TEXT PRIMARY KEY,
                    specimen_id TEXT NOT NULL,
                    image_sha256 TEXT NOT NULL,
                    params_hash TEXT NOT NULL,
                    run_id TEXT,
                    status TEXT,
                    dwc_fields_json TEXT,
                    raw_jsonl_offset INTEGER,
                    timestamp TIMESTAMP,
                    UNIQUE(image_sha256, params_hash),
                    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
                )
            """)

            # Specimen aggregations
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS specimen_aggregations (
                    specimen_id TEXT PRIMARY KEY,
                    candidate_fields_json TEXT,
                    best_candidates_json TEXT,
                    review_status TEXT,
                    queued_for_review_at TIMESTAMP,
                    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
                )
            """)

            # Reviews
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    specimen_id TEXT PRIMARY KEY,
                    reviewed_by TEXT,
                    reviewed_at TIMESTAMP,
                    decisions_json TEXT,
                    final_dwc_json TEXT,
                    status TEXT,
                    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
                )
            """)

            # Data quality flags
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_flags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    specimen_id TEXT NOT NULL,
                    flag_type TEXT NOT NULL,
                    severity TEXT,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
                )
            """)

            # Indexes
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_specimen_catalog
                ON specimens(expected_catalog_number)
            """)

            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_extraction_image
                ON extractions(image_sha256, params_hash)
            """)

            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_flags_specimen
                ON data_quality_flags(specimen_id, resolved)
            """)

    def register_specimen(
        self,
        specimen_id: str,
        camera_filename: Optional[str] = None,
        expected_catalog_number: Optional[str] = None,
    ) -> bool:
        """
        Register a new specimen.

        Args:
            specimen_id: Unique identifier (usually camera filename base)
            camera_filename: Original camera filename
            expected_catalog_number: Expected catalog number

        Returns:
            True if created, False if already exists
        """
        try:
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO specimens (specimen_id, camera_filename, expected_catalog_number)
                    VALUES (?, ?, ?)
                    """,
                    (specimen_id, camera_filename, expected_catalog_number),
                )
            logger.debug(f"Registered specimen: {specimen_id}")
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"Specimen already exists: {specimen_id}")
            return False

    def register_original_file(self, original_file: OriginalFile):
        """Register an original camera file."""
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO original_files
                (sha256, specimen_id, file_path, format, dimensions_json,
                 size_bytes, role, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    original_file.sha256,
                    original_file.specimen_id,
                    original_file.file_path,
                    original_file.format,
                    json.dumps(original_file.dimensions) if original_file.dimensions else None,
                    original_file.size_bytes,
                    original_file.role,
                    original_file.captured_at.isoformat() if original_file.captured_at else None,
                ),
            )
        logger.debug(f"Registered original file: {original_file.sha256[:16]}...")

    def register_transformation(self, transformation: ImageTransformation):
        """Register an image transformation."""
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO image_transformations
                (sha256, specimen_id, derived_from, operation, params_json,
                 timestamp, tool, tool_version, stored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transformation.sha256,
                    transformation.specimen_id,
                    transformation.derived_from,
                    transformation.operation,
                    json.dumps(transformation.params),
                    transformation.timestamp.isoformat(),
                    transformation.tool,
                    transformation.tool_version,
                    transformation.stored_at,
                ),
            )
        logger.debug(f"Registered transformation: {transformation.sha256[:16]}...")

    def get_specimen_id_from_image(self, image_sha256: str) -> Optional[str]:
        """Get specimen ID associated with an image (original or derived)."""
        # Check original files
        row = self.conn.execute(
            "SELECT specimen_id FROM original_files WHERE sha256 = ?", (image_sha256,)
        ).fetchone()

        if row:
            return row["specimen_id"]

        # Check transformations
        row = self.conn.execute(
            "SELECT specimen_id FROM image_transformations WHERE sha256 = ?", (image_sha256,)
        ).fetchone()

        return row["specimen_id"] if row else None

    def should_extract(
        self, image_sha256: str, extraction_params: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if extraction should proceed (deduplication).

        Args:
            image_sha256: SHA256 of image to extract
            extraction_params: Extraction parameters

        Returns:
            (should_extract, existing_extraction_id)
        """
        params_hash = self._hash_params(extraction_params)

        row = self.conn.execute(
            """
            SELECT extraction_id, status FROM extractions
            WHERE image_sha256 = ? AND params_hash = ?
            """,
            (image_sha256, params_hash),
        ).fetchone()

        if row is None:
            return True, None

        # Re-extract if previous attempt failed
        if row["status"] == "failed":
            logger.info(
                f"Re-extracting {image_sha256[:16]}... (previous attempt failed: {row['extraction_id']})"
            )
            return True, row["extraction_id"]

        # Skip if already successfully extracted
        logger.debug(f"Skipping {image_sha256[:16]}... (already extracted: {row['extraction_id']})")
        return False, row["extraction_id"]

    def record_extraction(self, result: ExtractionResult):
        """Record an extraction result."""
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO extractions
                (extraction_id, specimen_id, image_sha256, params_hash,
                 run_id, status, dwc_fields_json, raw_jsonl_offset, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.extraction_id,
                    result.specimen_id,
                    result.image_sha256,
                    result.params_hash,
                    result.run_id,
                    result.status,
                    json.dumps(result.dwc_fields),
                    result.raw_jsonl_offset,
                    result.timestamp.isoformat() if result.timestamp else None,
                ),
            )
        logger.debug(f"Recorded extraction: {result.extraction_id}")

    def aggregate_specimen_extractions(self, specimen_id: str) -> Dict[str, Any]:
        """
        Aggregate multiple extraction results for a specimen.

        Returns:
            Dictionary with 'candidate_fields' and 'best_candidates'
        """
        # Get all completed extractions for this specimen
        rows = self.conn.execute(
            """
            SELECT extraction_id, dwc_fields_json FROM extractions
            WHERE specimen_id = ? AND status = 'completed'
            ORDER BY timestamp DESC
            """,
            (specimen_id,),
        ).fetchall()

        if not rows:
            logger.warning(f"No completed extractions for specimen: {specimen_id}")
            return {"candidate_fields": {}, "best_candidates": {}}

        # Group by field name, collect all candidates
        candidate_fields: Dict[str, List[Dict[str, Any]]] = {}

        for row in rows:
            dwc_fields = json.loads(row["dwc_fields_json"])

            for field_name, field_data in dwc_fields.items():
                if field_name not in candidate_fields:
                    candidate_fields[field_name] = []

                candidate_fields[field_name].append(
                    {
                        "value": field_data.get("value"),
                        "confidence": field_data.get("confidence", 0.0),
                        "source": row["extraction_id"],
                    }
                )

        # Select best candidate per field (highest confidence)
        best_candidates = {}
        for field_name, candidates in candidate_fields.items():
            # Filter out None/empty values
            valid_candidates = [c for c in candidates if c["value"]]
            if valid_candidates:
                best = max(valid_candidates, key=lambda c: c["confidence"])
                best_candidates[field_name] = best

        # Save aggregation
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO specimen_aggregations
                (specimen_id, candidate_fields_json, best_candidates_json,
                 review_status, queued_for_review_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    specimen_id,
                    json.dumps(candidate_fields),
                    json.dumps(best_candidates),
                    "pending",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        logger.info(
            f"Aggregated {len(rows)} extractions for specimen {specimen_id}: "
            f"{len(best_candidates)} fields"
        )

        return {"candidate_fields": candidate_fields, "best_candidates": best_candidates}

    def flag_specimen(
        self, specimen_id: str, flag_type: str, message: str, severity: str = "warning"
    ):
        """Add a data quality flag to a specimen."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO data_quality_flags
                (specimen_id, flag_type, severity, message)
                VALUES (?, ?, ?, ?)
                """,
                (specimen_id, flag_type, severity, message),
            )
        logger.warning(f"Flagged {specimen_id}: [{flag_type}] {message}")

    def get_specimen_flags(self, specimen_id: str, unresolved_only: bool = True) -> List[Dict]:
        """Get data quality flags for a specimen."""
        query = "SELECT * FROM data_quality_flags WHERE specimen_id = ?"
        params = [specimen_id]

        if unresolved_only:
            query += " AND resolved = FALSE"

        rows = self.conn.execute(query + " ORDER BY created_at DESC", params).fetchall()
        return [dict(row) for row in rows]

    def check_catalog_number_duplicates(self):
        """Check for catalog numbers appearing on multiple specimens."""
        rows = self.conn.execute("""
            SELECT
                json_extract(best_candidates_json, '$.catalogNumber.value') as cat_num,
                GROUP_CONCAT(specimen_id) as specimens,
                COUNT(*) as count
            FROM specimen_aggregations
            WHERE cat_num IS NOT NULL AND cat_num != ''
            GROUP BY cat_num
            HAVING count > 1
        """).fetchall()

        for row in rows:
            cat_num = row["cat_num"]
            specimens = row["specimens"].split(",")

            for specimen_id in specimens:
                self.flag_specimen(
                    specimen_id,
                    "DUPLICATE_CATALOG_NUMBER",
                    f"Catalog {cat_num} appears on {len(specimens)} specimens: {specimens}",
                    severity="error",
                )

        logger.info(f"Checked catalog duplicates: {len(rows)} duplicates found")
        return len(rows)

    def check_malformed_catalog_numbers(self, pattern: str = r"^AAFC-\d{5,6}$"):
        """Check for catalog numbers that don't match expected pattern."""
        import re

        rows = self.conn.execute("""
            SELECT
                specimen_id,
                json_extract(best_candidates_json, '$.catalogNumber.value') as cat_num
            FROM specimen_aggregations
            WHERE cat_num IS NOT NULL AND cat_num != ''
        """).fetchall()

        regex = re.compile(pattern)
        malformed_count = 0

        for row in rows:
            cat_num = row["cat_num"]
            if not regex.match(cat_num):
                self.flag_specimen(
                    row["specimen_id"],
                    "MALFORMED_CATALOG_NUMBER",
                    f"Catalog '{cat_num}' doesn't match pattern {pattern}",
                    severity="warning",
                )
                malformed_count += 1

        logger.info(f"Checked catalog patterns: {malformed_count} malformed found")
        return malformed_count

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_specimens": self.conn.execute("SELECT COUNT(*) FROM specimens").fetchone()[0],
            "original_files": self.conn.execute("SELECT COUNT(*) FROM original_files").fetchone()[
                0
            ],
            "transformations": self.conn.execute(
                "SELECT COUNT(*) FROM image_transformations"
            ).fetchone()[0],
            "extractions": self.conn.execute("SELECT COUNT(*) FROM extractions").fetchone()[0],
            "aggregations": self.conn.execute(
                "SELECT COUNT(*) FROM specimen_aggregations"
            ).fetchone()[0],
            "reviews": self.conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
            "unresolved_flags": self.conn.execute(
                "SELECT COUNT(*) FROM data_quality_flags WHERE resolved = FALSE"
            ).fetchone()[0],
        }

    @staticmethod
    def _hash_params(params: Dict[str, Any]) -> str:
        """Create deterministic hash of extraction parameters."""
        canonical = json.dumps(params, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
