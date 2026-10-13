"""Ассоциативный массив на списке пар (замена dict)."""

from .base import BaseEntity
from .pair import Pair


class CustomMap(BaseEntity):
    """Ассоциативный массив на списке пар — используется вместо dict."""

    def __init__(self, items=()):
        self._pairs = []
        for key, value in items:
            self.put(key, value)

    @property
    def pairs(self):
        return tuple(self._pairs)

    @pairs.setter
    def pairs(self, value):
        self._pairs = []
        for pair in value:
            self.put(pair.key, pair.value)

    def _index_of(self, key):
        for index, pair in enumerate(self._pairs):
            if pair.key == key:
                return index
        return -1

    def put(self, key, value):
        index = self._index_of(key)
        if index >= 0:
            self._pairs[index].value = value
        else:
            self._pairs.append(Pair(key, value))

    def get(self, key, default=None):
        index = self._index_of(key)
        return self._pairs[index].value if index >= 0 else default

    def remove(self, key):
        index = self._index_of(key)
        if index < 0:
            raise KeyError(key)
        return self._pairs.pop(index).value

    def keys(self):
        return [pair.key for pair in self._pairs]

    def values(self):
        return [pair.value for pair in self._pairs]

    def items(self):
        return [(pair.key, pair.value) for pair in self._pairs]

    def sort_key(self):
        return (len(self._pairs),)

    def __getitem__(self, key):
        index = self._index_of(key)
        if index < 0:
            raise KeyError(key)
        return self._pairs[index].value

    def __setitem__(self, key, value):
        self.put(key, value)

    def __delitem__(self, key):
        self.remove(key)

    def __contains__(self, key):
        return self._index_of(key) >= 0

    def __len__(self):
        return len(self._pairs)

    def __iter__(self):
        return iter(self.keys())

    def __eq__(self, other):
        if not isinstance(other, CustomMap):
            return NotImplemented
        missing = object()
        return len(self) == len(other) and all(
            other.get(key, missing) == value for key, value in self.items()
        )

    def __repr__(self):
        return f"CustomMap({self.items()!r})"

    def __str__(self):
        return "{" + ", ".join(str(pair) for pair in self._pairs) + "}"