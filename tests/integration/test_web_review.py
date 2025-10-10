"""Integration tests for web review interface.

Tests the complete web review workflow including database integration.
"""

from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import requests
import pytest

from io_utils.candidates import Candidate, init_db, insert_candidate
from review_web import ReviewServer, ReviewHandler


def create_test_database(db_path: Path) -> None:
    """Create a test database with sample candidates."""
    session = init_db(db_path)

    # Add test candidates for multiple images
    test_data = [
        ("img1.jpg", Candidate(value="Species A", engine="vision", confidence=0.95)),
        ("img1.jpg", Candidate(value="Species B", engine="tesseract", confidence=0.80)),
        ("img2.jpg", Candidate(value="Location X", engine="vision", confidence=0.90)),
        ("img2.jpg", Candidate(value="Location Y", engine="gpt", confidence=0.75, error=True)),
    ]

    for image, candidate in test_data:
        insert_candidate(session, "test_run", image, candidate)

    session.close()


def create_test_images_dir(images_dir: Path) -> None:
    """Create test image files."""
    images_dir.mkdir(exist_ok=True)

    # Create dummy image files
    for i in [1, 2]:
        img_path = images_dir / f"img{i}.jpg"
        img_path.write_bytes(b"fake_jpeg_data")


@pytest.fixture
def web_server():
    """Start a test web server and return its URL."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test.db"
        images_dir = tmp_path / "images"

        # Setup test data
        create_test_database(db_path)
        create_test_images_dir(images_dir)

        # Start server in thread
        with sqlite3.connect(db_path, check_same_thread=False) as conn:
            server = ReviewServer(
                ("localhost", 0),  # Use any available port
                ReviewHandler,
                conn=conn,
                images_dir=images_dir,
                commit="test_commit",
                export="test_export",
            )

            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            # Wait for server to start
            time.sleep(0.1)

            base_url = f"http://localhost:{server.server_port}"

            yield base_url, tmp_path

            server.shutdown()
            server_thread.join(timeout=1)


def test_web_review_index_page(web_server):
    """Test that the index page lists available images."""
    base_url, tmp_path = web_server

    response = requests.get(base_url)
    assert response.status_code == 200

    content = response.text
    assert "Images" in content
    assert "img1.jpg" in content
    assert "img2.jpg" in content
    assert "/review/img1.jpg" in content


def test_web_review_image_page(web_server):
    """Test that individual image review pages work correctly."""
    base_url, tmp_path = web_server

    response = requests.get(f"{base_url}/review/img1.jpg")
    assert response.status_code == 200

    content = response.text
    assert "img1.jpg" in content
    assert "Species A" in content
    assert "Species B" in content
    assert "vision (0.95)" in content
    assert "tesseract (0.80)" in content
    assert '<form method="post"' in content


def test_web_review_candidates_ordering(web_server):
    """Test that candidates are ordered by confidence descending."""
    base_url, tmp_path = web_server

    response = requests.get(f"{base_url}/review/img2.jpg")
    assert response.status_code == 200

    content = response.text

    # Vision (0.90) should appear before GPT (0.75)
    vision_pos = content.find("vision (0.90)")
    gpt_pos = content.find("gpt (0.75)")

    assert vision_pos > 0
    assert gpt_pos > 0
    assert vision_pos < gpt_pos


def test_web_review_error_handling(web_server):
    """Test error handling for non-existent images."""
    base_url, tmp_path = web_server

    response = requests.get(f"{base_url}/review/nonexistent.jpg")
    # Should still return 200 but with empty candidate list
    assert response.status_code == 200


def test_web_review_database_compatibility():
    """Test that review_web.py can handle sqlite3 connections without errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test.db"

        # Create database and add test data
        create_test_database(db_path)

        # Test direct sqlite3 connection (what review_web.py uses)
        from io_utils.candidates import fetch_candidates_sqlite

        with sqlite3.connect(db_path) as conn:
            candidates = fetch_candidates_sqlite(conn, "img1.jpg")

        assert len(candidates) == 2
        assert candidates[0].confidence == 0.95  # Highest confidence first
        assert candidates[1].confidence == 0.80


def test_web_review_headers(web_server):
    """Test that response headers include version information."""
    base_url, tmp_path = web_server

    response = requests.get(base_url)

    assert response.headers.get("X-Commit-Hash") == "test_commit"
    assert response.headers.get("X-Export-Version") == "test_export"
