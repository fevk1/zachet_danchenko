"""Диалог входа в систему."""

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout,
)


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