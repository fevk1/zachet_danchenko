"""Сеанс работы пользователя и работа с отчётом."""

import os
from datetime import datetime

from .base import BaseEntity


class UserSession(BaseEntity):
    """Сеанс работы пользователя: логин, время входа и выхода."""

    TIME_FORMAT = "%d.%m.%y %H:%M:%S"
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
        return self._time_in <= moment <= (self._time_out or UserSession.now())

    def __iter__(self):
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