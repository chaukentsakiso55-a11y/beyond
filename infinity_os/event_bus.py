from collections import defaultdict
from threading import RLock

class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)
        self._lock = RLock()

    def on(self, event, callback):
        with self._lock:
            self._listeners[event].append(callback)
        return callback

    def off(self, event, callback):
        with self._lock:
            if callback in self._listeners.get(event, []):
                self._listeners[event].remove(callback)

    def emit(self, event, payload=None):
        with self._lock:
            callbacks = list(self._listeners.get(event, [])) + list(self._listeners.get("*", []))
        for callback in callbacks:
            try:
                callback(event, payload) if event != "*" and callback in self._listeners.get("*",[]) else callback(payload)
            except Exception:
                pass
