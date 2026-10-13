"""Пара «ключ — значение» для CustomMap."""

from .base import BaseEntity


class Pair(BaseEntity):
    """Пара «ключ — значение», элемент CustomMap."""

    def __init__(self, key, value):
        self._key = key
        self._value = value

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def sort_key(self):
        return (str(self._key),)

    def __eq__(self, other):
        if not isinstance(other, Pair):
            return NotImplemented
        return self._key == other.key and self._value == other.value

    def __hash__(self):
        return hash((Pair, self._key))

    def __iter__(self):
        yield self._key
        yield self._value

    def __getitem__(self, index):
        return (self._key, self._value)[index]

    def __len__(self):
        return 2

    def __repr__(self):
        return f"Pair(key={self._key!r}, value={self._value!r})"

    def __str__(self):
        return f"{self._key} → {self._value}"