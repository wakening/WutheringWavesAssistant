# coding: utf-8
import logging
import re
from typing import List
from PySide6.QtCore import Qt, Signal, QEasingCurve, QUrl, QSize, QTimer, QObject
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import QApplication, QHBoxLayout, QFrame, QWidget

from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen, SystemThemeListener, isDarkTheme, InfoBarPosition, InfoBar,
                            FluentIcon as FIF)

from src.gui.view.notice_interface import NoticeInterface
from src.gui.view.gallery_interface import GalleryInterface
from src.gui.view.home_interface import HomeV2Interface
from src.gui.view.param_interface import ParamInterface
from src.gui.view.setting_interface import SettingInterface
from src.gui.view.terminal_interface import TerminalInterface
from src.gui.common.config import ZH_SUPPORT_URL, EN_SUPPORT_URL, cfg, VERSION, VERSION_URLS
from src.gui.common.globals import globalSignal
from src.gui.common.icon import Icon
from src.gui.common.signal_bus import signalBus
from src.gui.common.translator import Translator
from src.gui.common import resource  # noqa: F401
from src.gui.common.version_control import RemoteVersion

logger = logging.getLogger(__name__)


class MainWindow(FluentWindow):

    remoteVersionFinishedSignal = Signal()

    def __init__(self):
        super().__init__()
        self.initWindow()

        # create system theme listener
        self.themeListener = SystemThemeListener(self)

        # self.setStyleSheet("border: 2px solid red;")

        # create sub interface
        self.homeInterface = HomeV2Interface(self)
        self.paramInterface = ParamInterface(self)
        self.noticeInterface = NoticeInterface(self)
        self.terminalInterface = TerminalInterface(self)

        self.settingInterface = SettingInterface(self)

        # enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()
        self.splashScreen.finish()

        # start theme listener
        self.themeListener.start()

        self.remoteVersion = RemoteVersion(VERSION_URLS, self.remoteVersionFinishedSignal.emit, self)
        if cfg.checkUpdateAtStartUpV2.value is True:
            self.remoteVersion.request()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSampleCard.connect(self.switchToSample)
        signalBus.supportSignal.connect(self.onSupport)
        signalBus.windowSizeChanged.connect(self.windowResize)
        self.remoteVersionFinishedSignal.connect(self.showUpdateVersion)
        globalSignal.taskInfoBarSignal.connect(self.showTaskInfoBar)

    def initNavigation(self):
        # add navigation items
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))
        self.addSubInterface(self.paramInterface, Icon.PARAM, self.tr('Param'))
        self.navigationInterface.addSeparator()
        self.addSubInterface(self.noticeInterface, FIF.MEGAPHONE, self.tr('Notice'))
        self.addSubInterface(self.terminalInterface, Icon.TERMINAL, self.tr('Terminal'))

        self.addSubInterface(
            self.settingInterface, FIF.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.windowResize()
        # self.resize(1280, 800)
        # self.resize(720, 720)
        # self.resize(960, 780)
        self.setMinimumWidth(700)
        self.setWindowIcon(QIcon(':/gallery/images/logo.ico'))
        self.setWindowTitle(f'Wuthering Waves Assistant {VERSION}')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        self.alignWindowToCenter()
        self.show()
        QApplication.processEvents()

    def alignWindowToCenter(self):
        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def onSupport(self):
        language = cfg.get(cfg.language).value
        if language.name() == "zh_CN":
            QDesktopServices.openUrl(QUrl(ZH_SUPPORT_URL))
        else:
            QDesktopServices.openUrl(QUrl(EN_SUPPORT_URL))

    def windowResize(self):
        windowSize = cfg.get(cfg.windowSize)
        if windowSize == "Default":
            windowSize = (1280, 800)
            # windowSize = (1080, 760)
        else:
            window_wh = windowSize.split("x")
            windowSize = (int(window_wh[0]), int(window_wh[1]))
        self.resize(*windowSize)
        self.alignWindowToCenter()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def closeEvent(self, e):
        globalSignal.closeMainWindowSignal.emit()
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        super().closeEvent(e)

    def _onThemeChangedFinished(self):
        super()._onThemeChangedFinished()

        # retry
        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))

    def switchToSample(self, routeKey, index):
        """ switch to sample """
        interfaces = self.findChildren(GalleryInterface)
        for w in interfaces:
            if w.objectName() == routeKey:
                self.stackedWidget.setCurrentWidget(w, False)
                w.scrollToCard(index)

    def showUpdateVersion(self):
        result = self.remoteVersion.checkVersion()
        if result is None:
            msg = self.tr(" *检查更新失败")
            signalBus.homeMessageSignal.emit(msg)
            self.setWindowTitle(self.windowTitle() + msg)
            return
        if result is False:
            logger.debug("无新版本需要更新")
            return
        if result is True:
            msg = self.tr(" *有新版本 {version}").format(version=self.remoteVersion.version)
            signalBus.homeMessageSignal.emit(msg)
            self.setWindowTitle(self.windowTitle() + msg)
            self.remoteVersion.showInfoBar(msg, 5000, self.homeInterface)

    def showEvent(self, event):
        super().showEvent(event)
        # 以回调的方式获取窗口id，保证已初始化完成
        globalSignal.guiWinId.emit(self.winId())

    def showTaskInfoBar(self, title, content, duration):
        logger.debug(f"showTaskInfoBar title:{title}, content:{content}, duration:{duration}")
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=duration,
            parent=InfoBar.desktopView()
        )