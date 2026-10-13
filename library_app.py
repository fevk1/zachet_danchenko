# -*- coding: utf-8 -*-
"""
Лабораторная работа: настольное приложение на PyQt5 «Учёт изданий библиотеки».

Запуск:
    pip install PyQt5
    python library_app.py


"""

import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton, QSpinBox,
    QStatusBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


# ============================================================================
#                               СУЩНОСТИ
# ============================================================================

class BaseEntity(ABC):
    """Абстрактный корень иерархии. Каждая сущность обязана иметь ключ сортировки
    и реализовать __eq__, __repr__, __str__. Сравнение (<, <=, >, >=) общее для всех."""

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


class Book(LibraryItem):
    KIND = "Книга"
    MAX_PAGES = 10000

    def __init__(self, title, author, year, pages, price):
        self._author = ""
        self._pages = 1
        super().__init__(title, year, price)
        self.author = author
        self.pages = pages

    @property
    def kind(self):
        return Book.KIND

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("Укажите автора книги.")
        self._author = value

    @property
    def pages(self):
        return self._pages

    @pages.setter
    def pages(self, value):
        value = int(value)
        if not 1 <= value <= Book.MAX_PAGES:
            raise ValueError(f"Число страниц должно быть от 1 до {Book.MAX_PAGES}.")
        self._pages = value

    @property
    def creator(self):
        return self.author

    @creator.setter
    def creator(self, value):
        self.author = value

    @property
    def size(self):
        return self.pages

    @size.setter
    def size(self, value):
        self.pages = value

    def size_text(self):
        return f"{self.pages} стр."

    def __eq__(self, other):
        if not isinstance(other, Book):
            return NotImplemented
        return (self.title.lower(), self.author.lower(), self.year) == \
               (other.title.lower(), other.author.lower(), other.year)

    def __hash__(self):
        return hash((Book.KIND, self.title.lower(), self.author.lower(), self.year))

    def __len__(self):
        return self.pages

    def __contains__(self, text):
        needle = str(text).strip().lower()
        return needle in self.title.lower() or needle in self.author.lower() or needle == str(self.year)

    def __repr__(self):
        return (f"Book(id={self.id}, title={self.title!r}, author={self.author!r}, "
                f"year={self.year}, pages={self.pages}, price={self.price})")

    def __str__(self):
        return f"книга «{self.title}», {self.author}, {self.year}"


class Magazine(LibraryItem):
    KIND = "Журнал"
    MAX_ISSUE = 999

    def __init__(self, title, publisher, year, issue, price):
        self._publisher = ""
        self._issue = 1
        super().__init__(title, year, price)
        self.publisher = publisher
        self.issue = issue

    @property
    def kind(self):
        return Magazine.KIND

    @property
    def publisher(self):
        return self._publisher

    @publisher.setter
    def publisher(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("Укажите издателя журнала.")
        self._publisher = value

    @property
    def issue(self):
        return self._issue

    @issue.setter
    def issue(self, value):
        value = int(value)
        if not 1 <= value <= Magazine.MAX_ISSUE:
            raise ValueError(f"Номер выпуска должен быть от 1 до {Magazine.MAX_ISSUE}.")
        self._issue = value

    @property
    def creator(self):
        return self.publisher

    @creator.setter
    def creator(self, value):
        self.publisher = value

    @property
    def size(self):
        return self.issue

    @size.setter
    def size(self, value):
        self.issue = value

    def size_text(self):
        return f"№ {self.issue}"

    def __eq__(self, other):
        if not isinstance(other, Magazine):
            return NotImplemented
        return (self.title.lower(), self.year, self.issue) == \
               (other.title.lower(), other.year, other.issue)

    def __hash__(self):
        return hash((Magazine.KIND, self.title.lower(), self.year, self.issue))

    def __int__(self):
        return self.issue

    def __contains__(self, text):
        needle = str(text).strip().lower()
        return needle in self.title.lower() or needle in self.publisher.lower() or needle == str(self.year)

    def __repr__(self):
        return (f"Magazine(id={self.id}, title={self.title!r}, publisher={self.publisher!r}, "
                f"year={self.year}, issue={self.issue}, price={self.price})")

    def __str__(self):
        return f"журнал «{self.title}» № {self.issue}, {self.year}"


class UserSession(BaseEntity):
    """Сеанс работы пользователя: логин, время входа и выхода."""

    TIME_FORMAT = "%d.%m.%y %H:%M:%S"          # dd.MM.yy HH:MM:SS
    HEADERS = ("login", "time_in", "time_out")

    def __init__(self, login, time_in=None, time_out=None):
        self._login = ""
        self._time_in = None
        self._time_out = None
        self.login = login
        self.time_in = time_in if time_in is not None else UserSession.now()
        self.time_out = time_out

    @staticmethod
    def now():
        return datetime.now().replace(microsecond=0)

    @staticmethod
    def format_time(moment):
        return moment.strftime(UserSession.TIME_FORMAT) if moment else "-"

    @staticmethod
    def parse_time(text):
        return datetime.strptime(text.strip(), UserSession.TIME_FORMAT)

    @property
    def login(self):
        return self._login

    @login.setter
    def login(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("Логин не может быть пустым.")
        self._login = value

    @property
    def time_in(self):
        return self._time_in

    @time_in.setter
    def time_in(self, value):
        if not isinstance(value, datetime):
            raise ValueError("time_in должен быть datetime.")
        self._time_in = value

    @property
    def time_out(self):
        return self._time_out

    @time_out.setter
    def time_out(self, value):
        if value is not None:
            if not isinstance(value, datetime):
                raise ValueError("time_out должен быть datetime.")
            if value < self._time_in:
                raise ValueError("time_out не может быть раньше time_in.")
        self._time_out = value

    @property
    def is_active(self):
        return self._time_out is None

    @property
    def duration(self):
        return (self._time_out or UserSession.now()) - self._time_in

    def close(self):
        if self.is_active:
            self.time_out = UserSession.now()

    def sort_key(self):
        return (self._time_in, self._login)

    def __eq__(self, other):
        if not isinstance(other, UserSession):
            return NotImplemented
        return (self._login, self._time_in, self._time_out) == \
               (other.login, other.time_in, other.time_out)

    def __hash__(self):
        return hash((UserSession, self._login, self._time_in))

    def __contains__(self, moment):
        """Попадает ли момент времени в сеанс: `moment in session`."""
        return self._time_in <= moment <= (self._time_out or UserSession.now())

    def __iter__(self):
        """Ячейки строки отчёта: tuple(session) -> (login, time_in, time_out)."""
        yield self._login
        yield UserSession.format_time(self._time_in)
        yield UserSession.format_time(self._time_out)

    def __repr__(self):
        return (f"UserSession(login={self._login!r}, time_in={self._time_in!r}, "
                f"time_out={self._time_out!r})")

    def __str__(self):
        return (f"{self._login}: {UserSession.format_time(self._time_in)} → "
                f"{UserSession.format_time(self._time_out) if self._time_out else 'сейчас'}")

    @staticmethod
    def build_table(sessions):
        rows = [tuple(session) for session in sessions]
        widths = [len(header) for header in UserSession.HEADERS]
        for row in rows:
            widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
        border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
        header = "|" + "|".join(
            f" {title.center(width)} " for title, width in zip(UserSession.HEADERS, widths)) + "|"
        lines = [border, header, border]
        for row in rows:
            lines.append("|" + "|".join(f" {cell.ljust(width)} " for cell, width in zip(row, widths)) + "|")
        lines.append(border)
        return "\n".join(lines) + "\n"

    @staticmethod
    def save_report(sessions, path):
        with open(path, "w", encoding="utf-8") as file:
            file.write(UserSession.build_table(sessions))

    @staticmethod
    def load_report(path):
        """Читает прошлые сеансы из отчёта, чтобы история не терялась."""
        sessions = []
        if not os.path.exists(path):
            return sessions
        try:
            with open(path, encoding="utf-8") as file:
                lines = file.readlines()
        except (OSError, UnicodeDecodeError):
            return sessions
        for line in lines:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) != 3 or tuple(cells) == UserSession.HEADERS:
                continue
            try:
                sessions.append(UserSession(cells[0], UserSession.parse_time(cells[1]),
                                            UserSession.parse_time(cells[2])))
            except ValueError:
                continue
        return sessions


class Library(BaseEntity):
    """Каталог изданий: хранит объекты в списке и индекс id → издание в CustomMap."""

    KIND_COLORS = CustomMap([(Book.KIND, "#e6f0ff"), (Magazine.KIND, "#fff2df")])
    SORTERS = CustomMap([
        ("По умолчанию", None),                       # sorted() через __lt__
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
        """Меняет поля издания. False — если получился дубликат другой записи."""
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


# ============================================================================
#                   ПЕРЕОПРЕДЕЛЁННЫЕ КОМПОНЕНТЫ ОКНА (Qt)
# ============================================================================

class AppButton(QPushButton):
    """Кнопка с цветом по роли и подсветкой при наведении."""

    PALETTE = CustomMap([
        ("primary", ("#2563eb", "#1d4ed8")),
        ("danger", ("#dc2626", "#b91c1c")),
        ("neutral", ("#64748b", "#475569")),
    ])

    def __init__(self, text, role="neutral", parent=None):
        super().__init__(text, parent)
        self._role = "neutral"
        self.role = role
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(34)

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        if value not in AppButton.PALETTE:
            raise ValueError(f"Неизвестная роль кнопки: {value}")
        self._role = value
        self._paint(False)

    def _paint(self, hovered):
        normal, hover = AppButton.PALETTE[self._role]
        color = hover if hovered else normal
        self.setStyleSheet(
            f"QPushButton {{ background: {color}; color: white; border: none; "
            f"border-radius: 6px; padding: 6px 12px; font-weight: 600; }}"
            f"QPushButton:disabled {{ background: #cbd5e1; }}")

    def enterEvent(self, event):
        self._paint(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._paint(False)
        super().leaveEvent(event)


class SearchLineEdit(QLineEdit):
    """Поле поиска: Esc очищает, при фокусе текст выделяется."""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setMinimumHeight(30)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clear()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)


class TitleLabel(QLabel):
    """Заголовок, который подстраивает размер шрифта под ширину окна."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = self.font()
        font.setBold(True)
        font.setPointSize(14)
        self.setFont(font)

    def resizeEvent(self, event):
        font = self.font()
        size = max(12, min(20, self.width() // 55))
        if font.pointSize() != size:
            font.setPointSize(size)
            self.setFont(font)
        super().resizeEvent(event)


class ItemTable(QTableWidget):
    """Таблица изданий: Delete отправляет запрос на удаление."""

    deleteRequested = pyqtSignal()
    HEADERS = ("ID", "Тип", "Название", "Автор / издатель", "Год", "Объём", "Цена, ₽")
    TEXT_COLUMNS = (2, 3)

    def __init__(self, parent=None):
        super().__init__(0, len(ItemTable.HEADERS), parent)
        self.setHorizontalHeaderLabels(ItemTable.HEADERS)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.selected_id() is not None:
            self.deleteRequested.emit()
            return
        super().keyPressEvent(event)

    def fill(self, items, colors):
        self.blockSignals(True)
        self.setRowCount(0)
        for row, item in enumerate(items):
            self.insertRow(row)
            background = QColor(colors.get(item.kind, "#ffffff"))
            for column, text in enumerate(item.to_row()):
                cell = QTableWidgetItem(text)
                cell.setBackground(background)
                cell.setForeground(QColor("#1f2933"))
                if column in ItemTable.TEXT_COLUMNS:
                    cell.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    cell.setTextAlignment(Qt.AlignCenter)
                self.setItem(row, column, cell)
        self.blockSignals(False)

    def selected_id(self):
        rows = self.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self.item(rows[0].row(), 0).text())

    def select_id(self, item_id):
        self.blockSignals(True)
        for row in range(self.rowCount()):
            if self.item(row, 0).text() == str(item_id):
                self.selectRow(row)
                break
        self.blockSignals(False)


class SafeComboBox(QComboBox):
    """Выпадающий список, который не меняет значение от случайной прокрутки колесом."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(30)

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class YearSpinBox(QSpinBox):
    """Поле года: Home подставляет текущий год, колесо работает только в фокусе."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(LibraryItem.MIN_YEAR, datetime.now().year)
        self.setValue(datetime.now().year)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(30)

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Home:
            self.setValue(self.maximum())
            return
        super().keyPressEvent(event)


class PriceSpinBox(QDoubleSpinBox):
    """Поле цены: с зажатым Shift шаг увеличивается в 10 раз."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 1_000_000)
        self.setDecimals(2)
        self.setSingleStep(10)
        self.setSuffix(" ₽")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(30)

    def stepBy(self, steps):
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            steps *= 10
        super().stepBy(steps)

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class InfoStatusBar(QStatusBar):
    """Строка состояния, которая подписывает каждое сообщение временем."""

    def showMessage(self, message, timeout=6000):
        stamp = datetime.now().strftime("%H:%M:%S")
        super().showMessage(f"[{stamp}] {message}", timeout)


class FormGroupBox(QGroupBox):
    """Группа с единым оформлением и заголовком в верхнем регистре."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setTitle(title)
        self.setStyleSheet(
            "QGroupBox { font-weight: 600; border: 1px solid #cbd5e1; border-radius: 8px; "
            "margin-top: 14px; padding: 14px 10px 10px 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")

    def setTitle(self, title):
        super().setTitle(str(title).upper())


class SessionList(QListWidget):
    """Список сеансов: двойной клик показывает сеанс в строке состояния."""

    sessionActivated = pyqtSignal(str)

    def fill(self, sessions, current=None):
        self.clear()
        for session in sorted(sessions, reverse=True):
            text = str(session)
            if session is current:
                text += "   ← текущий"
            self.addItem(text)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if item is not None:
            self.sessionActivated.emit(item.text())
        super().mouseDoubleClickEvent(event)


class LoginDialog(QDialog):
    """Окно входа: не закрывается, пока не введён корректный логин."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._login = ""
        self.setWindowTitle("Вход в систему")
        self.setModal(True)
        self.setMinimumWidth(340)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText("3–20 символов: буквы, цифры или _")
        self._edit.setMinimumHeight(30)
        self._error = QLabel("")
        self._error.setStyleSheet("color: #dc2626;")
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Войти")
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.addWidget(QLabel("Введите логин пользователя:"))
        layout.addWidget(self._edit)
        layout.addWidget(self._error)
        layout.addWidget(buttons)

    @property
    def login(self):
        return self._login

    @login.setter
    def login(self, value):
        self._login = str(value).strip()
        self._edit.setText(self._login)

    @staticmethod
    def is_valid_login(text):
        return 3 <= len(text) <= 20 and text.replace("_", "").isalnum()

    def accept(self):
        text = self._edit.text().strip()
        if not LoginDialog.is_valid_login(text):
            self._error.setText("Логин: 3–20 символов, только буквы, цифры и _.")
            self._edit.setFocus()
            return
        self._login = text
        super().accept()

    @staticmethod
    def ask(parent=None):
        dialog = LoginDialog(parent)
        return dialog.login if dialog.exec_() == QDialog.Accepted else None


class MainWindow(QMainWindow):
    """Главное окно: карточка издания, таблица, сеансы, отчёт при закрытии."""

    FORM_MODES = CustomMap([
        (Book.KIND, ("Автор:", "Страниц:", Book.MAX_PAGES)),
        (Magazine.KIND, ("Издатель:", "Номер выпуска:", Magazine.MAX_ISSUE)),
    ])

    def __init__(self, library, session, history=(), report_path="report.txt"):
        super().__init__()
        self._library = library
        self._session = session
        self._history = list(history)
        self._report_path = report_path
        self._editing_id = None
        self._centered = False
        self.setWindowTitle("Учёт изданий библиотеки")
        self.setMinimumSize(980, 600)
        self.resize(1180, 700)
        self._build_ui()
        self._connect_signals()
        self._on_kind_changed(self._kind.currentText())
        self._update_title()
        self._refresh_table()
        self._refresh_sessions()

    # --- геттеры / сеттеры -------------------------------------------------
    @property
    def library(self):
        return self._library

    @library.setter
    def library(self, value):
        self._library = value
        self._update_title()
        self._refresh_table()

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value
        self._update_title()
        self._refresh_sessions()

    @property
    def history(self):
        return tuple(self._history)

    @history.setter
    def history(self, value):
        self._history = list(value)
        self._refresh_sessions()

    @property
    def report_path(self):
        return self._report_path

    @report_path.setter
    def report_path(self, value):
        self._report_path = str(value)

    # --- построение интерфейса ---------------------------------------------
    def _build_ui(self):
        self._title = TitleLabel()
        self._status = InfoStatusBar()
        self.setStatusBar(self._status)

        self._kind = SafeComboBox()
        self._kind.addItems(MainWindow.FORM_MODES.keys())
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Например: Война и мир")
        self._creator_label = QLabel()
        self._creator_edit = QLineEdit()
        self._year = YearSpinBox()
        self._size_label = QLabel()
        self._size = QSpinBox()
        self._size.setMinimum(1)
        self._size.setFocusPolicy(Qt.StrongFocus)
        self._price = PriceSpinBox()
        for field in (self._name_edit, self._creator_edit, self._size):
            field.setMinimumHeight(30)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.addRow("Тип:", self._kind)
        form.addRow("Название:", self._name_edit)
        form.addRow(self._creator_label, self._creator_edit)
        form.addRow("Год:", self._year)
        form.addRow(self._size_label, self._size)
        form.addRow("Цена:", self._price)

        self._add_btn = AppButton("Добавить", "primary")
        self._save_btn = AppButton("Сохранить", "primary")
        self._delete_btn = AppButton("Удалить", "danger")
        self._clear_btn = AppButton("Очистить", "neutral")
        buttons = QGridLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self._add_btn, 0, 0)
        buttons.addWidget(self._save_btn, 0, 1)
        buttons.addWidget(self._delete_btn, 1, 0)
        buttons.addWidget(self._clear_btn, 1, 1)

        card = FormGroupBox("Карточка издания")
        card_layout = QVBoxLayout(card)
        card_layout.addLayout(form)
        card_layout.addSpacing(6)
        card_layout.addLayout(buttons)

        self._sessions = SessionList()
        self._switch_btn = AppButton("Сменить пользователя", "neutral")
        sessions_box = FormGroupBox("Сеансы работы")
        sessions_layout = QVBoxLayout(sessions_box)
        sessions_layout.addWidget(self._sessions)
        sessions_layout.addWidget(self._switch_btn)

        left = QWidget()
        left.setFixedWidth(370)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(card)
        left_layout.addWidget(sessions_box, 1)

        self._search = SearchLineEdit("Поиск по названию, автору или году (Ctrl+F)")
        self._sort = SafeComboBox()
        self._sort.addItems(Library.SORTERS.keys())
        self._sort.setMinimumWidth(190)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self._search, 1)
        toolbar.addWidget(QLabel("Сортировка:"))
        toolbar.addWidget(self._sort)

        self._table = ItemTable()
        self._stats = QLabel()
        self._stats.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._stats.setStyleSheet("color: #475569;")

        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)
        right_layout.addLayout(toolbar)
        right_layout.addWidget(self._table, 1)
        right_layout.addWidget(self._stats)

        body = QHBoxLayout()
        body.setSpacing(14)
        body.addWidget(left)
        body.addLayout(right_layout, 1)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)
        root.addWidget(self._title)
        root.addLayout(body, 1)
        self.setCentralWidget(central)

    def _connect_signals(self):
        self._kind.currentTextChanged.connect(self._on_kind_changed)
        self._search.textChanged.connect(self._refresh_table)
        self._sort.currentTextChanged.connect(self._refresh_table)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.deleteRequested.connect(self._delete_item)
        self._add_btn.clicked.connect(self._add_item)
        self._save_btn.clicked.connect(self._save_item)
        self._delete_btn.clicked.connect(self._delete_item)
        self._clear_btn.clicked.connect(self._clear_form)
        self._switch_btn.clicked.connect(self._switch_user)
        self._sessions.sessionActivated.connect(self._on_session_activated)

    # --- обработчики -------------------------------------------------------
    def _update_title(self):
        self._title.setText(f"Библиотека «{self._library.name}»   ·   пользователь: {self._session.login}")

    def _on_kind_changed(self, kind):
        creator_text, size_text, size_max = MainWindow.FORM_MODES.get(kind, MainWindow.FORM_MODES[Book.KIND])
        self._creator_label.setText(creator_text)
        self._size_label.setText(size_text)
        self._size.setMaximum(size_max)

    def _form_values(self):
        return (self._name_edit.text(), self._creator_edit.text(),
                self._year.value(), self._size.value(), self._price.value())

    def _fill_form(self, item):
        self._kind.setCurrentText(item.kind)
        self._name_edit.setText(item.title)
        self._creator_edit.setText(item.creator)
        self._year.setValue(item.year)
        self._size.setValue(item.size)
        self._price.setValue(item.price)

    def _refresh_table(self, *_):
        items = Library.sort_items(self._library.search(self._search.text()), self._sort.currentText())
        self._table.fill(items, Library.KIND_COLORS)
        if self._editing_id is not None:
            self._table.select_id(self._editing_id)
        kinds = "  ·  ".join(f"{kind}: {count}" for kind, count in self._library.stats().items())
        total = f"{self._library.total_price:,.2f}".replace(",", " ")
        self._stats.setText(f"Показано {len(items)} из {len(self._library)}  ·  {kinds}  ·  Сумма: {total} ₽")

    def _refresh_sessions(self):
        self._sessions.fill(self._history + [self._session], self._session)

    def _on_selection_changed(self):
        item_id = self._table.selected_id()
        item = self._library.find(item_id) if item_id is not None else None
        if item is None:
            return
        self._editing_id = item_id
        self._fill_form(item)
        self._kind.setEnabled(False)
        self._status.showMessage(f"Выбрано: {item}")

    def _on_session_activated(self, text):
        self._status.showMessage(f"Сеанс {text}")

    def _warn(self, text):
        QMessageBox.warning(self, "Внимание", text)

    def _add_item(self, *_):
        try:
            item = LibraryItem.create(self._kind.currentText(), *self._form_values())
        except ValueError as error:
            self._warn(str(error))
            return
        if not self._library.add(item):
            self._warn("Такое издание уже есть в каталоге.")
            return
        self._editing_id = item.id
        self._kind.setEnabled(False)
        self._refresh_table()
        self._status.showMessage(f"Добавлено: {item}")

    def _save_item(self, *_):
        item = self._library.find(self._editing_id) if self._editing_id is not None else None
        if item is None:
            self._warn("Сначала выберите запись в таблице.")
            return
        try:
            saved = self._library.update(item, *self._form_values())
        except ValueError as error:
            self._warn(str(error))
            return
        if not saved:
            self._warn("После изменений запись совпала бы с уже существующей.")
            return
        self._refresh_table()
        self._status.showMessage(f"Сохранено: {item}")

    def _delete_item(self, *_):
        item_id = self._table.selected_id() or self._editing_id
        item = self._library.find(item_id) if item_id is not None else None
        if item is None:
            self._warn("Выберите запись для удаления.")
            return
        answer = QMessageBox.question(self, "Удаление", f"Удалить {item}?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self._library.remove(item.id)
        self._clear_form()
        self._refresh_table()
        self._status.showMessage(f"Удалено: {item}")

    def _clear_form(self, *_):
        self._editing_id = None
        self._table.clearSelection()
        self._kind.setEnabled(True)
        self._name_edit.clear()
        self._creator_edit.clear()
        self._year.setValue(self._year.maximum())
        self._size.setValue(1)
        self._price.setValue(0)
        self._name_edit.setFocus()

    def _switch_user(self, *_):
        login = LoginDialog.ask(self)
        if login is None:
            return
        self._session.close()
        self._history.append(self._session)
        self.session = UserSession(login)
        self._status.showMessage(f"Вошёл пользователь {login}")

    # --- переопределённые события окна ---------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        if not self._centered:
            self._centered = True
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(screen.center() - self.rect().center())
            self._status.showMessage(f"Добро пожаловать, {self._session.login}!")

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Find):
            self._search.setFocus()
            return
        if event.matches(QKeySequence.New):
            self._clear_form()
            return
        if event.key() == Qt.Key_F5:
            self._refresh_table()
            self._status.showMessage("Таблица обновлена")
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._session.close()
        try:
            UserSession.save_report(sorted(self._history + [self._session]), self._report_path)
        except OSError as error:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт:\n{error}")
        event.accept()


# ============================================================================
#                                ЗАПУСК
# ============================================================================

class Application:
    REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.txt")
    STYLE = (
        "QTableWidget { gridline-color: #e2e8f0; selection-background-color: #93c5fd; "
        "selection-color: #0f172a; }"
        "QListWidget { border: 1px solid #e2e8f0; border-radius: 4px; }"
    )

    @staticmethod
    def run():
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setStyleSheet(Application.STYLE)
        font = app.font()
        font.setPointSize(10)
        app.setFont(font)

        login = LoginDialog.ask()
        if login is None:
            return 0
        window = MainWindow(
            library=Library.demo(),
            session=UserSession(login),
            history=UserSession.load_report(Application.REPORT_FILE),
            report_path=Application.REPORT_FILE,
        )
        window.show()
        return app.exec_()


if __name__ == "__main__":
    sys.exit(Application.run())
