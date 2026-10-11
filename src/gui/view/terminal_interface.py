import html
import logging
import queue
import re

from PySide6.QtCore import QThread
from PySide6.QtGui import Qt, QColor
from PySide6.QtWidgets import QTextEdit, QVBoxLayout
from qfluentwidgets import SimpleCardWidget

from .gallery_interface import GalleryInterface
from ..common.globals import globalParam, globalSignal
from ..common.signal_bus import signalBus

logger = logging.getLogger(__name__)


class LogListener(QThread):

    def __init__(self, logQueue):
        super().__init__()
        self.logQueue = logQueue

    def run(self):
        try:
            while not self.isInterruptionRequested():
                try:
                    logText = self.logQueue.get(timeout=1)  # 设置超时，避免永久阻塞
                    if logText is None:
                        continue
                    # 异步必须用signal传递数据，再由槽函数往控件内添加文本，直接在这往控件添加文本QT会经常闪退
                    signalBus.logQueueSignal.emit(logText)
                except queue.Empty:
                    continue  # 超时继续循环，及时感知运行状态
                except Exception:
                    logger.exception("日志监听线程发生未知异常，停止运行")
                    break
        except Exception:
            pass

    def stop(self):
        self.requestInterruption()
        self.logQueue.put(None)
        self.logQueue.put(None)
        self.wait(1200)
        logger.info("日志监听已关闭")


class TerminalCard(SimpleCardWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.textEdit = QTextEdit()

        self.vBoxLayout = QVBoxLayout(self)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(10, 6, 10, 6)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.addWidget(self.textEdit)
        # self.vBoxLayout.addStretch(1)

        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName('textEdit')

    def append_log(self, emit_msg):
        # 获取当前的滚动条位置
        scrollbar = self.textEdit.verticalScrollBar()
        # 判断滚动条是否在最底部
        is_at_bottom = scrollbar.value() == scrollbar.maximum()

        level_name, msg = emit_msg
        if level_name in ["ERROR", "WARN", "WARNING", "DEBUG"]:
            if level_name == "ERROR":
                color = QColor(255, 100, 100)
                # 转义 HTML 特殊字符
                safe_msg = html.escape(msg)
                # 替换每一行开头的空格为 &nbsp;（缩进）
                safe_msg = re.sub(r'^(\s+)', lambda m: '&nbsp;' * len(m.group(1)), safe_msg, flags=re.MULTILINE)
                # 替换换行符为 <br>
                safe_msg = safe_msg.replace('\n', '<br>')
                formatted_msg = rf"<font color='{color.name()}'>{safe_msg}</font>"
            elif level_name == "WARNING" or level_name == "WARN":
                # color = QColor(200, 200, 0)
                color = QColor(184, 134, 11)
                formatted_msg = rf"<font color='{color.name()}'>{msg}</font>"
            else:  # level_name == "DEBUG":
                color = QColor(100, 255, 100)
                formatted_msg = rf"<font color='{color.name()}'>{msg}</font>"
            self.textEdit.append(formatted_msg)
        else:
            # 添加文本
            formatted_msg = rf"<span>{msg}</span>"  # 也用html，防止被染色
            self.textEdit.append(formatted_msg)

        # 如果原本在底部，添加文本后跳到最底部
        if is_at_bottom:
            scrollbar.setValue(scrollbar.maximum())


class TerminalInterface(GalleryInterface):
    """ Terminal interface """

    def __init__(self, parent=None):
        self.logFIle = globalParam.logFile or ""
        self.logQueue = globalParam.logQueue

        super().__init__(
            title=self.tr("Terminal"),
            subtitle=self.logFIle,
            parent=parent,
            needButtonLayout=False,
            subtitleSelectableByMouse=True,
        )
        self.setObjectName('terminalInterface')

        # self.textEdit = QTextEdit()
        self.terminalCard = TerminalCard(self)
        self.logListener = LogListener(self.logQueue)
        if self.logFIle is not None:
            self.logListener.start()
        else:
            logger.warning("日志队列未初始化")

        self.__initWidget()

    def __initWidget(self):
        # self.textEdit.setObjectName("textEdit")
        # self.textEdit.setReadOnly(True)
        # StyleSheet.TERMINAL_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        # self.vBoxLayout.addWidget(self.textEdit)
        self.vBoxLayout.addWidget(self.terminalCard)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        globalSignal.closeMainWindowSignal.connect(self.stopLogListener)
        signalBus.logQueueSignal.connect(self.terminalCard.append_log)

    def stopLogListener(self):
        self.logListener.stop()
