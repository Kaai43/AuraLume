"""Bounded background work delivering results only on the Qt thread."""
from threading import Thread, BoundedSemaphore
from uuid import uuid4

from PySide6.QtCore import QObject, Qt, Signal, Slot


class BackgroundTasks(QObject):
    finished = Signal(str, object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._callbacks = {}
        self._closed = False
        self._slots = BoundedSemaphore(3)
        self.finished.connect(self._deliver, Qt.ConnectionType.QueuedConnection)

    def submit(self, operation, on_success, on_error):
        if self._closed:
            return
        key = uuid4().hex
        self._callbacks[key] = (on_success, on_error)

        def run():
            with self._slots:
                if self._closed:
                    return
                result, error = None, None
                try:
                    result = operation()
                except Exception as caught:
                    error = caught
                if not self._closed:
                    self.finished.emit(key, result, error)

        # Network code cannot delay application shutdown; workers never own DB/UI.
        Thread(target=run, name=f'auralume-{key[:8]}', daemon=True).start()

    @Slot(str, object, object)
    def _deliver(self, key, result, error):
        callbacks = self._callbacks.pop(key, None)
        if callbacks and not self._closed:
            if error is not None:
                callbacks[1](error)
            else:
                callbacks[0](result)

    def close(self):
        self._closed = True
        self._callbacks.clear()
