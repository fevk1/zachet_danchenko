"""Абстрактный корень иерархии сущностей."""

from abc import ABC, abstractmethod


class BaseEntity(ABC):
    """Каждая сущность обязана иметь ключ сортировки и реализовать
    __eq__, __repr__, __str__. Сравнения (<, <=, >, >=) — общие."""

    @abstractmethod
    def sort_key(self):
        """Кортеж, по которому сущности упорядочиваются."""

    @abstractmethod
    def __eq__(self, other):
        ...

    @abstractmethod
    def __repr__(self):
        ...

    @abstractmethod
    def __str__(self):
        ...

    def _compare(self, other):
        if not isinstance(other, BaseEntity):
            return NotImplemented
        mine, theirs = self.sort_key(), other.sort_key()
        try:
            return (mine > theirs) - (mine < theirs)
        except TypeError:
            return NotImplemented

    def __lt__(self, other):
        result = self._compare(other)
        return result if result is NotImplemented else result < 0

    def __le__(self, other):
        result = self._compare(other)
        return result if result is NotImplemented else result <= 0

    def __gt__(self, other):
        result = self._compare(other)
        return result if result is NotImplemented else result > 0

    def __ge__(self, other):
        result = self._compare(other)
        return result if result is NotImplemented else result >= 0