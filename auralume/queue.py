"""Playback order, isolated from the audio engine and widgets."""
import random


class PlayQueue:
    def __init__(self, rng=None):
        self.items: list[str] = []
        self.index = -1
        self.repeat = 'off'
        self.shuffle = False
        self._rng = rng or random.Random()
        self._visited: list[str] = []

    @property
    def current(self) -> str | None:
        return self.items[self.index] if 0 <= self.index < len(self.items) else None

    def set(self, ids: list[str], start_id: str | None = None):
        self.items = list(dict.fromkeys(ids))
        self.index = self.items.index(start_id) if start_id in self.items else (0 if self.items else -1)
        self._visited = [self.current] if self.current else []

    def enqueue(self, track_id: str):
        if track_id not in self.items:
            self.items.append(track_id)
        if self.index == -1:
            self.index = 0
            self._visited = [self.current]

    def next(self, automatic: bool = False) -> str | None:
        if not self.items:
            return None
        if automatic and self.repeat == 'one':
            return self.current
        if self.shuffle:
            available = [item for item in self.items if item not in self._visited]
            if not available:
                if self.repeat != 'all':
                    return None
                available = [item for item in self.items if item != self.current] or self.items
                self._visited = [self.current]
            self.index = self.items.index(self._rng.choice(available))
        else:
            index = self.index + 1
            if index == len(self.items):
                if self.repeat != 'all':
                    return None
                index = 0
            self.index = index
        self._visited.append(self.current)
        return self.current

    def previous(self) -> str | None:
        if not self.items:
            return None
        if self.shuffle and len(self._visited) > 1:
            self._visited.pop()
            self.index = self.items.index(self._visited[-1])
        else:
            self.index = max(0, self.index - 1)
            self._visited = [self.current]
        return self.current
