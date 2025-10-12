"""
Flask Web Application for Specimen Review

Provides browser-based interface for curators to review, validate,
and approve extracted specimen data.

Features:
- Review queue with prioritization
- Side-by-side image and data view
- GBIF validation indicators
- Field-level editing and corrections
- Approval/rejection workflow
- Keyboard navigation (j/k for next/prev)
"""

import logging
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .engine import ReviewEngine, ReviewStatus, ReviewPriority
from .validators import GBIFValidator

logger = logging.getLogger(__name__)


def create_review_app(
    extraction_dir: Path,
    image_base_url: str = "",
    enable_gbif: bool = True,
) -> Flask:
    """
    Create and configure Flask review application.

    Args:
        extraction_dir: Directory containing raw.jsonl
        image_base_url: Base URL for specimen images
        enable_gbif: Enable GBIF validation

    Returns:
        Configured Flask app
    """
    app = Flask(__name__, template_folder="../../templates")
    app.config["EXTRACTION_DIR"] = extraction_dir
    app.config["IMAGE_BASE_URL"] = image_base_url

    # Initialize review engine
    gbif_validator = GBIFValidator() if enable_gbif else None
    engine = ReviewEngine(gbif_validator=gbif_validator)

    # Load extraction results
    results_file = extraction_dir / "raw.jsonl"
    if results_file.exists():
        engine.load_extraction_results(results_file)
        logger.info(f"Loaded {len(engine.reviews)} specimens for review")
    else:
        logger.warning(f"Results file not found: {results_file}")

    @app.route("/")
    def index():
        """Render review dashboard."""
        return render_template("review_dashboard.html")

    @app.route("/api/queue")
    def get_queue():
        """Get review queue with filters.

        Query parameters:
            v: API version (1 or 2). Default: 1 (backward compatible)
            status: Filter by review status
            priority: Filter by priority level
            sort: Sort field (priority, quality, completeness)
            limit: Maximum number of results (default: 100)

        v=2 includes quality indicators and keyboard shortcuts for accessibility.
        """
        status_str = request.args.get("status")
        priority_str = request.args.get("priority")
        sort_by = request.args.get("sort", "priority")
        limit = int(request.args.get("limit", 100))
        api_version = request.args.get("v", "1")  # API versioning

        # Parse filters
        status = None
        if status_str:
            try:
                status = ReviewStatus[status_str.upper()]
            except KeyError:
                pass

        priority = None
        if priority_str:
            try:
                priority = ReviewPriority[priority_str.upper()]
            except KeyError:
                pass

        # Get filtered queue
        queue = engine.get_review_queue(status=status, priority=priority, sort_by=sort_by)

        # Limit results
        queue = queue[:limit]

        # v2 API includes quality indicators
        if api_version == "2":
            from src.accessibility import QualityIndicator

            queue_items = []
            for review in queue:
                quality_ind = QualityIndicator.from_score(
                    score=review.quality_score / 100, context="specimen"
                )

                queue_items.append(
                    {
                        "specimen_id": review.specimen_id,
                        "priority": review.priority.name,
                        "status": review.status.name,
                        "quality_score": review.quality_score,
                        "completeness": review.completeness_score,
                        "gbif_verified": review.gbif_taxonomy_verified,
                        "critical_issues": len(review.critical_issues),
                        "warnings": len(review.warnings),
                        "quality_indicator": quality_ind.to_dict(),  # NEW in v2
                    }
                )

            return jsonify(
                {
                    "queue": queue_items,
                    "total": len(engine.reviews),
                    "filtered": len(queue),
                    "api_version": "2",
                    "keyboard_shortcuts": {  # NEW in v2
                        "approve": "a",
                        "reject": "r",
                        "flag": "f",
                        "next": "j",
                        "previous": "k",
                    },
                }
            )

        # v1 API (existing code)
        return jsonify(
            {
                "queue": [
                    {
                        "specimen_id": review.specimen_id,
                        "priority": review.priority.name,
                        "status": review.status.name,
                        "quality_score": review.quality_score,
                        "completeness": review.completeness_score,
                        "gbif_verified": review.gbif_taxonomy_verified,
                        "critical_issues": len(review.critical_issues),
                        "warnings": len(review.warnings),
                    }
                    for review in queue
                ],
                "total": len(engine.reviews),
                "filtered": len(queue),
            }
        )

    @app.route("/api/specimen/<specimen_id>")
    def get_specimen(specimen_id: str):
        """Get full specimen review data.

        Query parameters:
            v: API version (1 or 2). Default: 1 (backward compatible)
               v=2 includes accessibility metadata for multi-modal interfaces
        """
        review = engine.get_review(specimen_id)

        if not review:
            return jsonify({"error": "Specimen not found"}), 404

        # Check API version
        api_version = request.args.get("v", "1")  # Default to v1 for backward compatibility

        # Construct image URL
        image_url = None
        if app.config["IMAGE_BASE_URL"]:
            image_url = f"{app.config['IMAGE_BASE_URL']}/{specimen_id}"

        # v2 API includes accessibility metadata
        if api_version == "2":
            return jsonify(
                {
                    "specimen": review.to_dict_with_accessibility(),
                    "image_url": image_url,
                    "api_version": "2",
                }
            )

        # v1 API (backward compatible)
        return jsonify(
            {
                "specimen": review.to_dict(),
                "image_url": image_url,
            }
        )

    @app.route("/api/specimen/<specimen_id>", methods=["PUT"])
    def update_specimen(specimen_id: str):
        """Update specimen review."""
        data = request.json

        corrections = data.get("corrections")
        status_str = data.get("status")
        reviewed_by = data.get("reviewed_by")
        notes = data.get("notes")

        # Parse status
        status = None
        if status_str:
            try:
                status = ReviewStatus[status_str.upper()]
            except KeyError:
                return jsonify({"error": f"Invalid status: {status_str}"}), 400

        # Update review
        engine.update_review(
            specimen_id=specimen_id,
            corrections=corrections,
            status=status,
            reviewed_by=reviewed_by,
            notes=notes,
        )

        return jsonify({"success": True, "specimen_id": specimen_id})

    @app.route("/api/specimen/<specimen_id>/approve", methods=["POST"])
    def approve_specimen(specimen_id: str):
        """Approve specimen."""
        data = request.json or {}
        reviewed_by = data.get("reviewed_by", "anonymous")

        engine.update_review(
            specimen_id=specimen_id, status=ReviewStatus.APPROVED, reviewed_by=reviewed_by
        )

        return jsonify({"success": True, "specimen_id": specimen_id, "status": "APPROVED"})

    @app.route("/api/specimen/<specimen_id>/reject", methods=["POST"])
    def reject_specimen(specimen_id: str):
        """Reject specimen."""
        data = request.json or {}
        reviewed_by = data.get("reviewed_by", "anonymous")
        notes = data.get("notes")

        engine.update_review(
            specimen_id=specimen_id,
            status=ReviewStatus.REJECTED,
            reviewed_by=reviewed_by,
            notes=notes,
        )

        return jsonify({"success": True, "specimen_id": specimen_id, "status": "REJECTED"})

    @app.route("/api/specimen/<specimen_id>/flag", methods=["POST"])
    def flag_specimen(specimen_id: str):
        """Flag specimen for expert review."""
        data = request.json or {}
        reviewed_by = data.get("reviewed_by", "anonymous")
        notes = data.get("notes")

        engine.update_review(
            specimen_id=specimen_id,
            status=ReviewStatus.FLAGGED,
            reviewed_by=reviewed_by,
            notes=notes,
        )

        return jsonify({"success": True, "specimen_id": specimen_id, "status": "FLAGGED"})

    @app.route("/api/gbif/taxonomy")
    def gbif_taxonomy_lookup():
        """Live GBIF taxonomy lookup."""
        if not gbif_validator:
            return jsonify({"error": "GBIF validation disabled"}), 503

        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing parameter: name"}), 400

        record = {"scientificName": name}
        updated_record, metadata = gbif_validator.verify_taxonomy(record)

        return jsonify({"record": updated_record, "validation": metadata})

    @app.route("/api/gbif/suggest")
    def gbif_suggest():
        """Get taxonomic name suggestions."""
        if not gbif_validator:
            return jsonify({"error": "GBIF validation disabled"}), 503

        query = request.args.get("q", "")
        limit = int(request.args.get("limit", 10))

        if not query or len(query) < 2:
            return jsonify({"suggestions": []})

        suggestions = gbif_validator.get_suggestions(query, limit=limit)
        return jsonify({"suggestions": suggestions})

    @app.route("/api/statistics")
    def get_statistics():
        """Get review statistics."""
        stats = engine.get_statistics()
        return jsonify(stats)

    @app.route("/api/export")
    def export_reviews():
        """Export all reviews to JSON."""
        output_path = app.config["EXTRACTION_DIR"] / "reviews_export.json"
        engine.export_reviews(output_path)

        return jsonify({"success": True, "file": str(output_path)})

    return app


# Standalone launcher
def main():
    """Launch review web application."""
    import argparse

    parser = argparse.ArgumentParser(description="Launch specimen review web interface")
    parser.add_argument(
        "--extraction-dir",
        type=Path,
        required=True,
        help="Directory containing raw.jsonl",
    )
    parser.add_argument("--port", type=int, default=5002, help="Port to run on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument(
        "--image-base-url",
        type=str,
        default="",
        help="Base URL for specimen images",
    )
    parser.add_argument(
        "--no-gbif",
        action="store_true",
        help="Disable GBIF validation",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print("=" * 70)
    print("SPECIMEN REVIEW WEB INTERFACE")
    print("=" * 70)
    print(f"Extraction directory: {args.extraction_dir}")
    print(f"GBIF validation: {'disabled' if args.no_gbif else 'enabled'}")
    print(f"Server: http://{args.host}:{args.port}")
    print()

    app = create_review_app(
        extraction_dir=args.extraction_dir,
        image_base_url=args.image_base_url,
        enable_gbif=not args.no_gbif,
    )

    print("✅ Review system ready")
    print(f"🌐 Open: http://{args.host}:{args.port}")
    print()

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
