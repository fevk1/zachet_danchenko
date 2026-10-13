# -*- coding: utf-8 -*-
"""Точка входа приложения «Учёт изданий библиотеки».

Запуск:
    pip install -r requirements.txt
    python main.py
"""

import os
import sys

from PyQt5.QtWidgets import QApplication

from library import Library, LoginDialog, MainWindow, UserSession


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