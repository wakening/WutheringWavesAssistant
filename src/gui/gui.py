import contextlib
import hashlib
import logging
import os
import sys
from pathlib import Path

with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
    from qfluentwidgets import qconfig  # noqa: F401

from qfluentwidgets import FluentTranslator
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtWidgets import QApplication
from src.gui.common.config import cfg
from src.gui.common.globals import globalSignal
from src.gui.view.main_window import MainWindow

logger = logging.getLogger(__name__)

SERVER_NAME = "WWA_" + hashlib.md5(str(Path(__file__).resolve().parent).encode()).hexdigest()
LOCAL_SERVER = None  # 声明在外面，保证生命周期


def is_exist():
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(100):
        socket.disconnectFromServer()
        globalSignal.guiExistSignal.emit()  # 连上了说明已存在，发送信号退出
        return True

    global LOCAL_SERVER
    LOCAL_SERVER = QLocalServer()  # 否则自己成为Server
    try:
        QLocalServer.removeServer(SERVER_NAME)  # 清理旧的 socket 文件
    except Exception:
        pass
    LOCAL_SERVER.listen(SERVER_NAME)
    return False


def show_traceback(is_debug: bool = False):
    """显示Qt异常信息，仅调试用"""
    if not is_debug:
        return

    from PySide6.QtCore import qInstallMessageHandler
    import traceback

    def qt_message_handler(mode, context, message):
        print("\n===== Qt Warning =====")
        print(message)

        if "QLayout" in message:
            print("".join(traceback.format_stack()))

    qInstallMessageHandler(qt_message_handler)


def wwa():
    is_exist()
    show_traceback()

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
