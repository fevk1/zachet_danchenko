"""Главное окно приложения."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QFormLayout, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QSpinBox, QVBoxLayout, QWidget,
)

from ..entities import (
    Book, CustomMap, Library, LibraryItem, Magazine, UserSession,
)
from .login_dialog import LoginDialog
from .widgets import (
    AppButton, FormGroupBox, InfoStatusBar, ItemTable, PriceSpinBox,
    SafeComboBox, SearchLineEdit, SessionList, TitleLabel, YearSpinBox,
)


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