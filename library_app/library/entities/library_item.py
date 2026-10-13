"""Абстрактное издание: общие поля книги и журнала + фабрика."""

from abc import abstractmethod
from datetime import datetime

from .base import BaseEntity


class LibraryItem(BaseEntity):
    """Абстрактное издание: общие поля книги и журнала."""

    MIN_YEAR = 1450
    _next_id = 1

    def __init__(self, title, year, price):
        self._id = LibraryItem.next_id()
        self._title = ""
        self._year = LibraryItem.MIN_YEAR
        self._price = 0.0
        self.title = title
        self.year = year
        self.price = price

    @staticmethod
    def next_id():
        value = LibraryItem._next_id
        LibraryItem._next_id += 1
        return value

    @staticmethod
    def create(kind, title, creator, year, size, price):
        """Фабрика: создаёт книгу или журнал по названию типа."""
        # Импорт внутри метода — чтобы избежать циклической зависимости.
        from .book import Book
        from .magazine import Magazine

        if kind == Book.KIND:
            return Book(title, creator, year, size, price)
        if kind == Magazine.KIND:
            return Magazine(title, creator, year, size, price)
        raise ValueError(f"Неизвестный тип издания: {kind}")

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) or value < 1:
            raise ValueError("ID должен быть положительным целым числом.")
        self._id = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("Название не может быть пустым.")
        self._title = value

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        value = int(value)
        current = datetime.now().year
        if not LibraryItem.MIN_YEAR <= value <= current:
            raise ValueError(f"Год должен быть от {LibraryItem.MIN_YEAR} до {current}.")
        self._year = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        value = float(value)
        if value < 0:
            raise ValueError("Цена не может быть отрицательной.")
        self._price = round(value, 2)

    @property
    @abstractmethod
    def kind(self):
        """Название типа издания."""

    @property
    @abstractmethod
    def creator(self):
        """Автор книги или издатель журнала."""

    @property
    @abstractmethod
    def size(self):
        """Число страниц книги или номер выпуска журнала."""

    @abstractmethod
    def size_text(self):
        """Объём в виде строки для таблицы."""

    def to_row(self):
        return (str(self.id), self.kind, self.title, self.creator,
                str(self.year), self.size_text(), f"{self.price:.2f}")

    def snapshot(self):
        return (self.title, self.creator, self.year, self.size, self.price)

    def apply(self, title, creator, year, size, price):
        self.title = title
        self.creator = creator
        self.year = year
        self.size = size
        self.price = price

    def sort_key(self):
        return (self.kind, self.title.lower(), self.year, self.id)