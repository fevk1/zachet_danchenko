"""Переопределённые компоненты Qt."""

from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDoubleSpinBox, QGroupBox,
    QHeaderView, QLabel, QLineEdit, QListWidget, QPushButton, QSpinBox,
    QStatusBar, QTableWidget, QTableWidgetItem,
)

from ..entities import CustomMap, LibraryItem


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