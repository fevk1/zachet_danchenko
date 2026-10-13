"""Книга."""

from .library_item import LibraryItem


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