"""Каталог изданий."""

from .base import BaseEntity
from .book import Book
from .custom_map import CustomMap
from .library_item import LibraryItem
from .magazine import Magazine


class Library(BaseEntity):
    """Каталог изданий: хранит объекты в списке и индекс id → издание в CustomMap."""

    KIND_COLORS = CustomMap([(Book.KIND, "#e6f0ff"), (Magazine.KIND, "#fff2df")])
    SORTERS = CustomMap([
        ("По умолчанию", None),
        ("По названию", lambda item: item.title.lower()),
        ("Сначала новые", lambda item: -item.year),
        ("Цена по возрастанию", lambda item: item.price),
        ("Цена по убыванию", lambda item: -item.price),
    ])

    def __init__(self, name, items=()):
        self._name = ""
        self._items = []
        self._index = CustomMap()
        self.name = name
        for item in items:
            self.add(item)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("Название библиотеки не может быть пустым.")
        self._name = value

    @property
    def items(self):
        return tuple(self._items)

    @items.setter
    def items(self, value):
        self._items = []
        self._index = CustomMap()
        for item in value:
            self.add(item)

    @property
    def total_price(self):
        return round(sum(item.price for item in self._items), 2)

    def add(self, item):
        if not isinstance(item, LibraryItem):
            raise TypeError("В библиотеку можно добавить только LibraryItem.")
        if item in self._items:
            return False
        self._items.append(item)
        self._index[item.id] = item
        return True

    def find(self, item_id):
        return self._index.get(item_id)

    def remove(self, item_id):
        item = self.find(item_id)
        if item is None:
            return None
        self._items = [other for other in self._items if other.id != item_id]
        del self._index[item_id]
        return item

    def update(self, item, title, creator, year, size, price):
        backup = item.snapshot()
        try:
            item.apply(title, creator, year, size, price)
        except ValueError:
            item.apply(*backup)
            raise
        if any(other is not item and other == item for other in self._items):
            item.apply(*backup)
            return False
        return True

    def search(self, text):
        needle = str(text).strip()
        return [item for item in self._items if not needle or needle in item]

    def stats(self):
        result = CustomMap()
        for item in self._items:
            result[item.kind] = result.get(item.kind, 0) + 1
        return result

    @staticmethod
    def sort_items(items, mode):
        key = Library.SORTERS.get(mode)
        return sorted(items) if key is None else sorted(items, key=key)

    @staticmethod
    def demo():
        return Library("Центральная", [
            Book("Мастер и Маргарита", "Михаил Булгаков", 1967, 480, 650),
            Book("Преступление и наказание", "Фёдор Достоевский", 1866, 608, 520),
            Book("Война и мир", "Лев Толстой", 1869, 1300, 1200),
            Book("Мёртвые души", "Николай Гоголь", 1842, 352, 410),
            Book("Отцы и дети", "Иван Тургенев", 1862, 288, 350),
            Book("Евгений Онегин", "Александр Пушкин", 1833, 224, 300),
            Book("Герой нашего времени", "Михаил Лермонтов", 1840, 256, 330),
            Book("Чистый код", "Роберт Мартин", 2008, 464, 1450),
            Magazine("Наука и жизнь", "АНО «Наука и жизнь»", 2026, 9, 450),
            Magazine("Вокруг света", "ООО «Вокруг света»", 2025, 12, 390),
            Magazine("Хакер", "ООО «Хакер»", 2024, 3, 290),
            Magazine("Популярная механика", "ООО «Фэшн Пресс»", 2025, 7, 350),
        ])

    def sort_key(self):
        return (self._name.lower(), len(self._items))

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __contains__(self, item):
        return item in self._items

    def __getitem__(self, index):
        return self._items[index]

    def __eq__(self, other):
        if not isinstance(other, Library):
            return NotImplemented
        return self._name == other.name and sorted(self._items) == sorted(other.items)

    def __repr__(self):
        return f"Library(name={self._name!r}, items={len(self._items)})"

    def __str__(self):
        return f"Библиотека «{self._name}»: {len(self._items)} изданий на {self.total_price:.2f} ₽"