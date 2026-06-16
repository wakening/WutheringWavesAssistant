import logging
import re
from typing import Callable

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import Qt
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from qfluentwidgets import InfoBar, InfoBarPosition

from src.gui.common.signal_bus import signalBus
from src.gui.common.config import ZH_SUPPORT_URL, EN_SUPPORT_URL, cfg, VERSION, VERSION_URLS

logger = logging.getLogger(__name__)


class RemoteVersion(QObject):

    def __init__(self, urls: list[str], callback: Callable, parent=None):
        super().__init__(parent)
        self.urls = urls
        self.callback = callback
        # 创建 QNetworkAccessManager 实例
        self.networkManager = QNetworkAccessManager(self)
        self.networkManager.finished.connect(self._onRequestFinished)

        self._index = 0
        self.version: str | None = None

    def request(self):
        self._index = 0
        self._tryNextUrl()

    def _tryNextUrl(self):
        if self._index >= len(self.urls):
            logger.warning("All update URLs failed.")
            return
        url_str = self.urls[self._index]
        url = QUrl(url_str)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.UserAgentHeader,
                          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/123.0.0.0 Safari/537.36")
        self.networkManager.get(request)

    def _onRequestFinished(self, reply):
        try:
            url = reply.url().toString()
            logger.debug(f"Finished request to: {url}")

            error = reply.error()
            if error != QNetworkReply.NoError:
                logger.debug(f"Error: {reply.errorString()} (Code: {error})")
                self._index += 1
                self._tryNextUrl()
                return

            data_bytes = reply.readAll()
            if data_bytes.isEmpty():
                logger.debug("Error: Empty reply received (but NoError reported)")
                self._index += 1
                self._tryNextUrl()
                return

            data = data_bytes.data().decode('utf-8', errors='ignore')
            logger.debug(f"Response: {data}")

            match = re.search(r"__version__\s*=\s*['\"](.+?)['\"]", data)
            if not match:
                logger.debug("Could not extract version from response.")
                self._index += 1
                self._tryNextUrl()
                return

            version = match.group(1)
            logger.debug(f"Remote version: {version}")
            self.version = version

            if self.callback:
                self.callback()
        except Exception as e:
            logger.error(e)
            self._index += 1
            self._tryNextUrl()
        finally:
            reply.deleteLater()

    def checkVersion(self):
        remoteVersion = self.version
        if not remoteVersion:
            return None
        if remoteVersion == VERSION:
            return False
        try:
            remoteVers = re.split(r"\s+", remoteVersion.strip())[0].split(".")
            curVers = re.split(r"\s+", VERSION.strip())[0].split(".")
            len = 3
            for i in range(len):  # 检查版本号的数值大小
                if int(remoteVers[i]) < int(curVers[i]):
                    return False
                if int(remoteVers[i]) > int(curVers[i]):
                    break
                if i == len - 1:
                    return False
            return True
        except Exception as e:
            logger.error(f"检查版本号时异常: {e}")
            return None

    def showInfoBar(self, msg, duration, parent):
        InfoBar.info(
            title=self.tr('Update'),
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=parent
        )

    def showSuccessBar(self, msg, duration, parent):
        InfoBar.success(
            title=self.tr('Update'),
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=parent
        )

    def showErrorBar(self, msg, duration, parent):
        InfoBar.error(
            title=self.tr('Update'),
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=parent
        )


