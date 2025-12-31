"""
Thread workers for non-blocking database operations.

This module provides a Worker pattern using QRunnable/QThreadPool to move
database operations off the main UI thread, preventing UI freezes.

Usage:
    from .workers import run_in_background
    
    def on_result(data):
        # Update UI with data
        pass
    
    def on_error(exception):
        # Handle error
        pass
    
    run_in_background(
        lambda: services.list_tasks(),
        on_result=on_result,
        on_error=on_error
    )
"""

from __future__ import annotations

import sys
import traceback
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class WorkerSignals(QObject):
    """Signals for worker thread communication.
    
    Attributes:
        finished: Emitted when the worker completes (with or without error)
        result: Emitted with the result of the operation on success
        error: Emitted with exception info on failure
        progress: Emitted with progress percentage (0-100)
    """
    finished = Signal()
    result = Signal(object)
    error = Signal(tuple)  # (exc_type, exc_value, traceback_str)
    progress = Signal(int)


class DatabaseWorker(QRunnable):
    """Worker for executing database operations in a background thread.
    
    This prevents the UI from freezing during database operations.
    Uses QThreadPool for efficient thread management.
    
    Example:
        worker = DatabaseWorker(lambda: services.list_tasks())
        worker.signals.result.connect(self._on_tasks_loaded)
        worker.signals.error.connect(self._on_load_error)
        QThreadPool.globalInstance().start(worker)
    """
    
    def __init__(self, fn: Callable[[], Any], *args, **kwargs):
        """Initialize worker with a callable.
        
        Args:
            fn: The function to execute in the background thread.
                Should return the result or raise an exception.
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        # Enable auto-delete after completion
        self.setAutoDelete(True)
    
    @Slot()
    def run(self) -> None:
        """Execute the function in the background thread."""
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            self.signals.error.emit((exc_type, exc_value, tb_str))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


def run_in_background(
    fn: Callable[[], Any],
    on_result: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    on_finished: Optional[Callable[[], None]] = None,
) -> DatabaseWorker:
    """Run a function in a background thread.
    
    This is a convenience function for running database operations
    without blocking the UI.
    
    Args:
        fn: The function to execute (typically a services.* call)
        on_result: Callback with the result on success
        on_error: Callback with the exception on failure
        on_finished: Callback when complete (success or failure)
    
    Returns:
        The DatabaseWorker instance (for reference if needed)
    
    Example:
        run_in_background(
            lambda: services.list_phases(),
            on_result=lambda phases: self.table.setRowCount(len(phases)),
            on_error=lambda e: QMessageBox.critical(self, "Error", str(e))
        )
    """
    from PySide6.QtCore import Qt
    
    worker = DatabaseWorker(fn)
    
    # Use QueuedConnection to ensure callbacks run on the main thread
    if on_result is not None:
        worker.signals.result.connect(on_result, Qt.QueuedConnection)
    
    if on_error is not None:
        def handle_error(error_tuple):
            exc_type, exc_value, tb_str = error_tuple
            on_error(exc_value)
        worker.signals.error.connect(handle_error, Qt.QueuedConnection)
    
    if on_finished is not None:
        worker.signals.finished.connect(on_finished, Qt.QueuedConnection)
    
    # Start the worker
    QThreadPool.globalInstance().start(worker)
    
    return worker


class LoadingState:
    """Simple state tracker for loading operations.
    
    Helps prevent multiple simultaneous loads and track loading state.
    """
    
    def __init__(self):
        self._loading = False
        self._pending_refresh = False
    
    @property
    def is_loading(self) -> bool:
        return self._loading
    
    def start_loading(self) -> bool:
        """Start a loading operation. Returns False if already loading."""
        if self._loading:
            self._pending_refresh = True
            return False
        self._loading = True
        return True
    
    def finish_loading(self) -> bool:
        """Finish loading. Returns True if a refresh was requested during load."""
        self._loading = False
        pending = self._pending_refresh
        self._pending_refresh = False
        return pending
