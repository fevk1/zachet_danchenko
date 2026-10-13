"""Журнал."""

from .library_item import LibraryItem


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