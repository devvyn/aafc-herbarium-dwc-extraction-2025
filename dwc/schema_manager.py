"""Schema management utilities for dynamic schema handling and version compatibility."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from .schema import (
    SchemaInfo,
    fetch_official_schemas,
    load_schema_terms_from_official_sources,
    validate_schema_compatibility,
)
from .mapper import (
    configure_dynamic_mappings,
    auto_generate_mappings_from_schemas,
    suggest_mapping_improvements,
)


class SchemaManager:
    """Manages schema loading, caching, and version compatibility."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        update_interval_days: int = 30,
        preferred_schemas: Optional[List[str]] = None,
    ):
        """Initialize the schema manager.

        Args:
            cache_dir: Directory for caching schemas
            update_interval_days: How often to check for schema updates
            preferred_schemas: Default schemas to use
        """
        self.cache_dir = cache_dir or Path("config/schemas/cache")
        self.update_interval = timedelta(days=update_interval_days)
        self.preferred_schemas = preferred_schemas or ["dwc_simple", "abcd_206"]
        self.logger = logging.getLogger(__name__)

        # Internal state
        self._schemas: Optional[Dict[str, SchemaInfo]] = None
        self._last_update: Optional[datetime] = None
        self._metadata_file = self.cache_dir / "schema_metadata.json"

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> Dict[str, Any]:
        """Load schema metadata from cache."""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load schema metadata: {e}")
        return {}

    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save schema metadata to cache."""
        try:
            with open(self._metadata_file, "w") as f:
                json.dump(metadata, f, indent=2, default=str)
        except IOError as e:
            self.logger.warning(f"Failed to save schema metadata: {e}")

    def _should_update_schemas(self) -> bool:
        """Check if schemas should be updated based on cache age."""
        metadata = self._load_metadata()
        last_update_str = metadata.get("last_update")

        if not last_update_str:
            return True

        try:
            last_update = datetime.fromisoformat(last_update_str)
            return datetime.now() - last_update > self.update_interval
        except ValueError:
            return True

    def get_schemas(self, force_update: bool = False) -> Dict[str, SchemaInfo]:
        """Get available schemas, updating if necessary.

        Args:
            force_update: Force an update regardless of cache age

        Returns:
            Dictionary of available schemas
        """
        if force_update or self._schemas is None or self._should_update_schemas():
            self.logger.info("Updating schemas from official sources")
            self._schemas = fetch_official_schemas(use_cache=True, cache_dir=self.cache_dir)

            if self._schemas:
                # Update metadata
                metadata = {
                    "last_update": datetime.now().isoformat(),
                    "schemas": {
                        name: {
                            "name": schema.name,
                            "version": schema.version,
                            "namespace": schema.namespace,
                            "term_count": len(schema.terms),
                            "schema_type": schema.schema_type.value,
                            "source_url": schema.source_url,
                        }
                        for name, schema in self._schemas.items()
                    },
                }
                self._save_metadata(metadata)
                self._last_update = datetime.now()

        return self._schemas or {}

    def get_schema_info(self, schema_name: str) -> Optional[SchemaInfo]:
        """Get information about a specific schema.

        Args:
            schema_name: Name of the schema to get info for

        Returns:
            SchemaInfo object or None if not found
        """
        schemas = self.get_schemas()
        return schemas.get(schema_name)

    def list_available_schemas(self) -> List[str]:
        """List names of all available schemas.

        Returns:
            List of schema names
        """
        schemas = self.get_schemas()
        return list(schemas.keys())

    def get_schema_terms(self, schema_names: Optional[List[str]] = None) -> List[str]:
        """Get terms from specified schemas.

        Args:
            schema_names: List of schema names to get terms from
                         If None, uses preferred schemas

        Returns:
            List of unique terms from the specified schemas
        """
        if schema_names is None:
            schema_names = self.preferred_schemas

        return load_schema_terms_from_official_sources(schema_names)

    def validate_terms(
        self, terms: List[str], target_schemas: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Validate terms against target schemas.

        Args:
            terms: List of terms to validate
            target_schemas: Schemas to validate against

        Returns:
            Validation results with valid, invalid, and deprecated terms
        """
        if target_schemas is None:
            target_schemas = self.preferred_schemas

        return validate_schema_compatibility(terms, target_schemas)

    def generate_mappings(
        self,
        schema_names: Optional[List[str]] = None,
        include_fuzzy: bool = True,
        similarity_threshold: float = 0.6,
    ) -> Dict[str, str]:
        """Generate automatic mappings from schemas.

        Args:
            schema_names: Schemas to generate mappings from
            include_fuzzy: Whether to include fuzzy matches
            similarity_threshold: Minimum similarity for fuzzy matches

        Returns:
            Dictionary of generated mappings
        """
        if schema_names is None:
            schema_names = self.preferred_schemas

        return auto_generate_mappings_from_schemas(
            schema_names, include_fuzzy, similarity_threshold
        )

    def configure_dynamic_mappings(
        self,
        schema_names: Optional[List[str]] = None,
        include_fuzzy: bool = True,
        similarity_threshold: float = 0.6,
    ) -> None:
        """Configure dynamic mappings based on schemas.

        Args:
            schema_names: Schemas to generate mappings from
            include_fuzzy: Whether to include fuzzy matches
            similarity_threshold: Minimum similarity for fuzzy matches
        """
        if schema_names is None:
            schema_names = self.preferred_schemas

        configure_dynamic_mappings(schema_names, include_fuzzy, similarity_threshold)
        self.logger.info(f"Configured dynamic mappings from schemas: {schema_names}")

    def suggest_mappings(
        self,
        unmapped_fields: List[str],
        target_schemas: Optional[List[str]] = None,
        similarity_threshold: float = 0.6,
    ) -> Dict[str, List[str]]:
        """Suggest mappings for unmapped fields.

        Args:
            unmapped_fields: Fields that need mapping suggestions
            target_schemas: Target schemas for suggestions
            similarity_threshold: Minimum similarity for suggestions

        Returns:
            Dictionary mapping fields to suggested terms
        """
        if target_schemas is None:
            target_schemas = self.preferred_schemas

        return suggest_mapping_improvements(unmapped_fields, target_schemas, similarity_threshold)

    def get_schema_compatibility_report(
        self, source_schema: str, target_schemas: List[str]
    ) -> Dict[str, Any]:
        """Generate a compatibility report between schemas.

        Args:
            source_schema: Source schema name
            target_schemas: List of target schema names

        Returns:
            Compatibility report with overlap statistics
        """
        schemas = self.get_schemas()

        if source_schema not in schemas:
            return {"error": f"Source schema '{source_schema}' not found"}

        source_terms = set(schemas[source_schema].terms)
        compatibility_report = {
            "source_schema": source_schema,
            "source_term_count": len(source_terms),
            "target_schemas": {},
            "overall_compatibility": 0.0,
        }

        total_overlap = 0
        valid_targets = 0

        for target_schema in target_schemas:
            if target_schema not in schemas:
                compatibility_report["target_schemas"][target_schema] = {
                    "error": f"Target schema '{target_schema}' not found"
                }
                continue

            target_terms = set(schemas[target_schema].terms)
            overlap = source_terms.intersection(target_terms)
            compatibility_score = len(overlap) / len(source_terms) if source_terms else 0.0

            compatibility_report["target_schemas"][target_schema] = {
                "target_term_count": len(target_terms),
                "overlapping_terms": len(overlap),
                "compatibility_score": compatibility_score,
                "unique_to_source": len(source_terms - target_terms),
                "unique_to_target": len(target_terms - source_terms),
                "overlapping_term_names": sorted(list(overlap)),
            }

            total_overlap += compatibility_score
            valid_targets += 1

        if valid_targets > 0:
            compatibility_report["overall_compatibility"] = total_overlap / valid_targets

        return compatibility_report

    def get_status(self) -> Dict[str, Any]:
        """Get status information about the schema manager.

        Returns:
            Dictionary with status information
        """
        metadata = self._load_metadata()
        schemas = self.get_schemas()

        return {
            "cache_dir": str(self.cache_dir),
            "update_interval_days": self.update_interval.days,
            "preferred_schemas": self.preferred_schemas,
            "last_update": metadata.get("last_update"),
            "available_schemas": list(schemas.keys()) if schemas else [],
            "schema_count": len(schemas) if schemas else 0,
            "cache_metadata_exists": self._metadata_file.exists(),
            "should_update": self._should_update_schemas(),
        }
