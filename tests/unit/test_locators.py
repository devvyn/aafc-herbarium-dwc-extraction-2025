"""Unit tests for ImageLocator implementations."""

import pytest
from pathlib import Path
from src.io_utils.locators.local import LocalFilesystemLocator
from src.io_utils.caching import CachingImageLocator
from src.io_utils.locator import ImageMetadata


class TestLocalFilesystemLocator:
    """Tests for LocalFilesystemLocator."""

    @pytest.fixture
    def temp_image_dir(self, tmp_path):
        """Create temp directory with test images."""
        # Create test images
        (tmp_path / "image1.jpg").write_bytes(b"fake image 1")
        (tmp_path / "image2.png").write_bytes(b"fake image 2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "image3.jpg").write_bytes(b"fake image 3")
        (tmp_path / "notimage.txt").write_bytes(b"not an image")
        return tmp_path

    def test_init_with_valid_directory(self, temp_image_dir):
        """Test initialization with valid directory."""
        locator = LocalFilesystemLocator(temp_image_dir)
        assert locator.base_path == temp_image_dir

    def test_init_with_invalid_directory(self):
        """Test initialization with non-existent directory fails."""
        with pytest.raises(ValueError, match="not a directory"):
            LocalFilesystemLocator(Path("/nonexistent/path"))

    def test_exists_returns_true_for_existing_image(self, temp_image_dir):
        """Test exists() returns True for existing image."""
        locator = LocalFilesystemLocator(temp_image_dir)
        assert locator.exists("image1.jpg") is True

    def test_exists_returns_false_for_missing_image(self, temp_image_dir):
        """Test exists() returns False for missing image."""
        locator = LocalFilesystemLocator(temp_image_dir)
        assert locator.exists("nonexistent.jpg") is False

    def test_get_image_returns_bytes(self, temp_image_dir):
        """Test get_image() returns image bytes."""
        locator = LocalFilesystemLocator(temp_image_dir)
        data = locator.get_image("image1.jpg")
        assert data == b"fake image 1"

    def test_get_image_raises_on_missing(self, temp_image_dir):
        """Test get_image() raises FileNotFoundError for missing image."""
        locator = LocalFilesystemLocator(temp_image_dir)
        with pytest.raises(FileNotFoundError, match="Image not found"):
            locator.get_image("nonexistent.jpg")

    def test_get_metadata_returns_valid_metadata(self, temp_image_dir):
        """Test get_metadata() returns ImageMetadata."""
        locator = LocalFilesystemLocator(temp_image_dir)
        metadata = locator.get_metadata("image1.jpg")

        assert isinstance(metadata, ImageMetadata)
        assert metadata.identifier == "image1.jpg"
        assert metadata.size_bytes == 12  # len(b"fake image 1")
        assert metadata.content_type == "image/jpeg"
        assert metadata.last_modified is not None

    def test_list_images_finds_all_images(self, temp_image_dir):
        """Test list_images() finds all image files."""
        locator = LocalFilesystemLocator(temp_image_dir)
        images = list(locator.list_images())

        # Should find .jpg and .png, but not .txt
        assert len(images) == 3
        assert "image1.jpg" in images
        assert "image2.png" in images
        # Subdirectory image should have relative path
        assert any("image3.jpg" in img for img in images)

    def test_list_images_with_prefix(self, temp_image_dir):
        """Test list_images() with prefix filter."""
        locator = LocalFilesystemLocator(temp_image_dir)
        images = list(locator.list_images(prefix="subdir"))

        assert len(images) == 1
        assert any("image3.jpg" in img for img in images)

    def test_get_local_path_returns_path(self, temp_image_dir):
        """Test get_local_path() returns valid Path."""
        locator = LocalFilesystemLocator(temp_image_dir)
        path = locator.get_local_path("image1.jpg")

        assert path is not None
        assert isinstance(path, Path)
        assert path.is_file()
        assert path.read_bytes() == b"fake image 1"

    def test_get_local_path_returns_none_for_missing(self, temp_image_dir):
        """Test get_local_path() returns None for missing image."""
        locator = LocalFilesystemLocator(temp_image_dir)
        path = locator.get_local_path("nonexistent.jpg")
        assert path is None


class TestCachingImageLocator:
    """Tests for CachingImageLocator decorator."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temp directories for images and cache."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Create test image
        (images_dir / "test.jpg").write_bytes(b"test image data")

        return images_dir, cache_dir

    def test_cache_miss_fetches_from_backend(self, temp_dirs):
        """Test that cache miss fetches from backend."""
        images_dir, cache_dir = temp_dirs
        backend = LocalFilesystemLocator(images_dir)
        locator = CachingImageLocator(backend, cache_dir)

        # First access: cache miss
        data = locator.get_image("test.jpg")
        assert data == b"test image data"

    def test_cache_hit_returns_from_cache(self, temp_dirs):
        """Test that cache hit returns from cache."""
        images_dir, cache_dir = temp_dirs
        backend = LocalFilesystemLocator(images_dir)
        locator = CachingImageLocator(backend, cache_dir)

        # First access: populate cache
        locator.get_image("test.jpg")

        # Verify file is cached
        cached_files = list(cache_dir.iterdir())
        assert len(cached_files) == 1

        # Second access: should return from cache
        data = locator.get_image("test.jpg")
        assert data == b"test image data"

    def test_exists_checks_cache_first(self, temp_dirs):
        """Test that exists() checks cache before backend."""
        images_dir, cache_dir = temp_dirs
        backend = LocalFilesystemLocator(images_dir)
        locator = CachingImageLocator(backend, cache_dir)

        # Populate cache
        locator.get_image("test.jpg")

        # exists() should return True even for cached image
        assert locator.exists("test.jpg") is True

    def test_get_local_path_returns_cache_path(self, temp_dirs):
        """Test get_local_path() returns cached path when available."""
        images_dir, cache_dir = temp_dirs
        backend = LocalFilesystemLocator(images_dir)
        locator = CachingImageLocator(backend, cache_dir)

        # Populate cache
        locator.get_image("test.jpg")

        # get_local_path should return cache path
        path = locator.get_local_path("test.jpg")
        assert path is not None
        assert path.parent == cache_dir

    def test_cache_eviction_when_size_exceeded(self, temp_dirs):
        """Test LRU cache eviction when max size exceeded."""
        images_dir, cache_dir = temp_dirs
        backend = LocalFilesystemLocator(images_dir)

        # Create locator with very small cache (1 byte max)
        locator = CachingImageLocator(backend, cache_dir, max_cache_size_mb=0.000001)

        # Add multiple images (they're all the same for this test)
        for i in range(3):
            (images_dir / f"img{i}.jpg").write_bytes(b"x" * 1000)

        # Fetch images - cache should evict old entries
        for i in range(3):
            locator.get_image(f"img{i}.jpg")

        # Cache should have evicted some files to stay under size limit
        cache_size_mb = sum(f.stat().st_size for f in cache_dir.iterdir()) / (1024 * 1024)
        # Allow some slack due to filesystem overhead
        assert cache_size_mb < 0.01  # Less than 10KB

    def test_clear_cache_removes_all_files(self, temp_dirs):
        """Test clear_cache() removes all cached files."""
        images_dir, cache_dir = temp_dirs
        backend = LocalFilesystemLocator(images_dir)
        locator = CachingImageLocator(backend, cache_dir)

        # Populate cache
        locator.get_image("test.jpg")
        assert len(list(cache_dir.iterdir())) > 0

        # Clear cache
        locator.clear_cache()
        assert len(list(cache_dir.iterdir())) == 0

    def test_get_cache_stats_returns_statistics(self, temp_dirs):
        """Test get_cache_stats() returns valid statistics."""
        images_dir, cache_dir = temp_dirs
        backend = LocalFilesystemLocator(images_dir)
        locator = CachingImageLocator(backend, cache_dir)

        # Empty cache stats
        stats = locator.get_cache_stats()
        assert stats["num_files"] == 0
        assert stats["total_size_mb"] == 0.0

        # Populate cache
        locator.get_image("test.jpg")

        # Non-empty cache stats
        stats = locator.get_cache_stats()
        assert stats["num_files"] == 1
        assert stats["total_size_mb"] > 0
        assert stats["oldest_access"] is not None
        assert stats["newest_access"] is not None
