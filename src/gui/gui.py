import contextlib
import os
import sys

with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
    from qfluentwidgets import FluentTranslator

from PySide6.QtCore import Qt, QTranslator, QObject, Signal
from PySide6.QtWidgets import QApplication
from src.gui.common.config import cfg
from src.gui.view.main_window import MainWindow

class GuiController(QObject):
    task_run_requested = Signal(str, str)

    def __init__(self):
        super().__init__()

    def on_run_clicked(self, task_name: str, task_ops: str):
        self.task_run_requested.emit(task_name, task_ops)


def wwa():
    # enable dpi scale
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    # internationalization
    locale = cfg.get(cfg.language).value
    translator = FluentTranslator(locale)
    galleryTranslator = QTranslator()
    galleryTranslator.load(locale, "gallery", ".", ":/gallery/i18n")

    app.installTranslator(translator)
    app.installTranslator(galleryTranslator)

    # create main window
    w = MainWindow()
    w.show()

    app.exec()


if __name__ == '__main__':
    wwa()
