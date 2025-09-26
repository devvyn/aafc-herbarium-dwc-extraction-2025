"""Progress tracking system for herbarium OCR processing."""

import asyncio
import json
from datetime import datetime
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class ProgressUpdate:
    """Progress update message."""
    type: str  # 'start', 'progress', 'complete', 'error'
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ProgressTracker:
    """Centralized progress tracking for all interfaces."""

    def __init__(self):
        self.callbacks: List[Callable[[ProgressUpdate], None]] = []
        self.async_callbacks: List[Callable[[ProgressUpdate], None]] = []
        self.current_stats = {
            'total_images': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'current_image': None,
            'start_time': None,
            'errors': [],
            'engine_stats': {}
        }

    def add_callback(self, callback: Callable[[ProgressUpdate], None], async_callback: bool = False):
        """Add a progress callback function."""
        if async_callback:
            self.async_callbacks.append(callback)
        else:
            self.callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ProgressUpdate], None]):
        """Remove a progress callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
        if callback in self.async_callbacks:
            self.async_callbacks.remove(callback)

    def update(self, update: ProgressUpdate):
        """Send progress update to all callbacks."""
        # Update internal stats based on the update
        self._update_stats(update)

        # Call sync callbacks
        for callback in self.callbacks:
            try:
                callback(update)
            except Exception as e:
                print(f"Progress callback error: {e}")

        # Call async callbacks
        if self.async_callbacks:
            asyncio.create_task(self._notify_async_callbacks(update))

    async def _notify_async_callbacks(self, update: ProgressUpdate):
        """Notify async callbacks."""
        for callback in self.async_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                print(f"Async progress callback error: {e}")

    def _update_stats(self, update: ProgressUpdate):
        """Update internal statistics based on progress update."""
        data = update.data

        if update.type == 'start':
            self.current_stats.update({
                'total_images': data.get('total_images', 0),
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'current_image': None,
                'start_time': update.timestamp,
                'errors': [],
                'engine_stats': {}
            })

        elif update.type == 'progress':
            if 'current_image' in data:
                self.current_stats['current_image'] = data['current_image']
            if 'processed' in data:
                self.current_stats['processed'] = data['processed']

        elif update.type == 'success':
            self.current_stats['successful'] += 1
            self.current_stats['processed'] = self.current_stats.get('processed', 0) + 1

            # Track engine usage
            engine = data.get('engine')
            if engine:
                self.current_stats['engine_stats'][engine] = \
                    self.current_stats['engine_stats'].get(engine, 0) + 1

        elif update.type == 'error':
            self.current_stats['failed'] += 1
            self.current_stats['processed'] = self.current_stats.get('processed', 0) + 1

            error_msg = data.get('error', update.message)
            self.current_stats['errors'].append(error_msg)

            # Keep only last 10 errors
            if len(self.current_stats['errors']) > 10:
                self.current_stats['errors'] = self.current_stats['errors'][-10:]

        elif update.type == 'skip':
            self.current_stats['skipped'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.current_stats.copy()

    def start_processing(self, total_images: int, config: Dict[str, Any] = None):
        """Signal start of processing."""
        update = ProgressUpdate(
            type='start',
            message=f'Starting processing of {total_images} images',
            data={
                'total_images': total_images,
                'config': config or {}
            }
        )
        self.update(update)

    def image_started(self, image_path: Path):
        """Signal start of processing a specific image."""
        update = ProgressUpdate(
            type='progress',
            message=f'Processing {image_path.name}',
            data={'current_image': image_path.name}
        )
        self.update(update)

    def image_completed(self, image_path: Path, engine: str, confidence: float = None):
        """Signal successful completion of image processing."""
        update = ProgressUpdate(
            type='success',
            message=f'Successfully processed {image_path.name}',
            data={
                'image': image_path.name,
                'engine': engine,
                'confidence': confidence
            }
        )
        self.update(update)

    def image_failed(self, image_path: Path, error: str):
        """Signal failed image processing."""
        update = ProgressUpdate(
            type='error',
            message=f'Failed to process {image_path.name}',
            data={
                'image': image_path.name,
                'error': error
            }
        )
        self.update(update)

    def image_skipped(self, image_path: Path, reason: str):
        """Signal skipped image processing."""
        update = ProgressUpdate(
            type='skip',
            message=f'Skipped {image_path.name}: {reason}',
            data={
                'image': image_path.name,
                'reason': reason
            }
        )
        self.update(update)

    def processing_complete(self):
        """Signal completion of all processing."""
        stats = self.get_stats()
        update = ProgressUpdate(
            type='complete',
            message=f'Processing complete: {stats["successful"]}/{stats["processed"]} successful',
            data=stats
        )
        self.update(update)


# Global progress tracker instance
global_tracker = ProgressTracker()


def create_tui_callback():
    """Create a TUI-compatible progress callback."""
    try:
        from rich.console import Console
        from rich.live import Live
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

        console = Console()

        def tui_callback(update: ProgressUpdate):
            if update.type == 'start':
                console.print(f"🚀 {update.message}")
            elif update.type == 'progress':
                console.print(f"🔄 {update.message}")
            elif update.type == 'success':
                console.print(f"✅ {update.message}")
            elif update.type == 'error':
                console.print(f"❌ {update.message}")
            elif update.type == 'complete':
                console.print(f"🎉 {update.message}")

        return tui_callback

    except ImportError:
        # Fallback to simple print
        def simple_callback(update: ProgressUpdate):
            print(f"[{update.type.upper()}] {update.message}")

        return simple_callback


def create_web_callback(websocket_manager=None):
    """Create a web dashboard compatible progress callback."""
    async def web_callback(update: ProgressUpdate):
        if websocket_manager:
            # Send update to all connected WebSocket clients
            await websocket_manager.broadcast({
                'type': 'progress_update',
                'update': asdict(update),
                'stats': global_tracker.get_stats()
            })

    return web_callback


def create_file_callback(log_path: Path):
    """Create a file-based progress callback for logging."""
    def file_callback(update: ProgressUpdate):
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps(asdict(update)) + '\n')
        except Exception as e:
            print(f"Failed to write progress log: {e}")

    return file_callback


class ProgressContextManager:
    """Context manager for automatic progress tracking."""

    def __init__(self, tracker: ProgressTracker, total_images: int, config: Dict[str, Any] = None):
        self.tracker = tracker
        self.total_images = total_images
        self.config = config

    def __enter__(self):
        self.tracker.start_processing(self.total_images, self.config)
        return self.tracker

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.tracker.processing_complete()
        else:
            update = ProgressUpdate(
                type='error',
                message=f'Processing failed: {exc_val}',
                data={'exception': str(exc_val)}
            )
            self.tracker.update(update)


# Convenience functions
def track_processing(total_images: int, config: Dict[str, Any] = None) -> ProgressContextManager:
    """Create a context manager for tracking processing progress."""
    return ProgressContextManager(global_tracker, total_images, config)


def setup_tui_tracking():
    """Setup progress tracking for TUI interface."""
    callback = create_tui_callback()
    global_tracker.add_callback(callback)
    return callback


def setup_web_tracking(websocket_manager=None):
    """Setup progress tracking for web dashboard."""
    callback = create_web_callback(websocket_manager)
    global_tracker.add_callback(callback, async_callback=True)
    return callback


def setup_file_tracking(log_path: Path):
    """Setup progress tracking to file."""
    callback = create_file_callback(log_path)
    global_tracker.add_callback(callback)
    return callback
