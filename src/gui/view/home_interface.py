# coding:utf-8
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStackedWidget, QButtonGroup, QApplication
from packaging.version import Version

from qfluentwidgets import (ScrollArea, ComboBox, TextEdit, Pivot, IndeterminateProgressRing, ToggleToolButton,
                            FluentIcon, CardWidget, InfoBar, InfoBarPosition, SplitToolButton, RoundMenu, Action,
                            PrimarySplitPushButton, SplitPushButton, PushButton, PopupTeachingTip, InfoBarIcon,
                            TeachingTipTailPosition, TeachingTip, TeachingTipView, ToolButton, TransparentToolButton,
                            FlyoutViewBase, BodyLabel, PrimaryPushButton, SubtitleLabel, TitleLabel, LargeTitleLabel,
                            FluentStyleSheet, TransparentPushButton, CheckBox, FlowLayout, HyperlinkButton, toggleTheme,
                            ToolTipFilter)

from src import __version__
from src.gui.common.config import paramConfig, VERSION, RELEASE_URL, CHANGELOG_URL
from src.gui.common.globals import GlobalSignal, globalSignal
from src.gui.common.signal_bus import signalBus
from src.gui.view.home.daily import DailyWidget
from src.gui.common.style_sheet import StyleSheet
from src.gui.view.home.echo import EchoWidget
from src.gui.view.home.events import EventsWidget
from src.gui.view.home.explore import ExploreWidget
from src.gui.view.home.game_settings import GameSettingsWidget

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimeRange:
    start: datetime
    end: datetime

    def contains(self, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        return self.start <= now < self.end

    @classmethod
    def from_str(cls, start: str, end: str, fmt="%Y-%m-%d %H:%M"):
        return cls(
            datetime.strptime(start, fmt),
            datetime.strptime(end, fmt)
        )


class BannerWidget(QWidget):
    """ Banner widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(80)

        self.mainLayout = QHBoxLayout(self)

        self.galleryLabel = QLabel(f'鸣潮\nWuthering Waves Assistant', self)
        self.galleryLabel.setObjectName('galleryLabel')
        self.galleryLabel.setWordWrap(True)

        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.galleryLabel)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setAlignment(Qt.AlignTop)


class UpdateFlyoutView(FlyoutViewBase):

    closed = Signal()

    def __init__(self, version, new_version, parent=None):
        super().__init__(parent)

        self.version = version
        self.new_version = new_version

        self.vBoxLayout = QVBoxLayout(self)

        self.titleLayout = QHBoxLayout()
        if self.new_version:
            title = f'有新版本 {self.version} -> <span style="color: red;">{self.new_version}</span>'
        else:
            title = f'暂无更新 {self.version}'
        self.titleDownload = TransparentToolButton(FluentIcon.DOWNLOAD, self)
        self.titleDownload.setToolTip(self.tr('Download'))
        self.titleLabel = QLabel(self.tr(title), self)

        # 更新日志
        self.changelogScrollArea = ScrollArea()
        self.changelogContainer = QWidget(self.changelogScrollArea)
        self.changelogLayout = QVBoxLayout(self.changelogContainer)
        self.changelogTitleLabel = QLabel(self.tr("更新日志:"), self.changelogContainer)
        # self.changelog = QLabel("略", self.changelogContainer)
        self.changelog = HyperlinkButton(CHANGELOG_URL, self.tr("在线查看"), self.changelogContainer)

        # git渠道
        self.channelLayout = QVBoxLayout()
        self.channelLabel = QLabel(self.tr("选择更新渠道: "), self)
        self.channelFlowlayout = FlowLayout()
        self.githubCheckBox = CheckBox(self.tr("GitHub"), self)
        self.tencentCheckBox = CheckBox(self.tr("CN-腾讯云"), self)
        self.tencentCheckBox.setToolTip(self.tr("国内加速"))
        self.atomGitCheckBox = CheckBox(self.tr("CN-AtomGit"), self)
        self.atomGitCheckBox.setToolTip(self.tr("国内加速"))

        self.buttonGroup = QButtonGroup(self)
        self.buttonGroup.addButton(self.githubCheckBox)
        self.buttonGroup.addButton(self.tencentCheckBox)
        self.buttonGroup.addButton(self.atomGitCheckBox)
        self.buttonGroup.setExclusive(True)

        self.channelTipLabel = QLabel(self.tr('国内请选择CN源更新，若有异常请及时反馈！'), self)

        self.buttonLayout = QHBoxLayout()
        self.confirmButton = PrimaryPushButton(self.tr('重启更新'), self)
        self.confirmButton.setToolTip(self.tr("需要重启脚本"))
        self.cancelButton = PushButton(self.tr('取消'), self)

        self.__initWidgets()

    def __initWidgets(self):
        self.titleLabel.setObjectName('titleLabel')
        # self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.TEACHING_TIP.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        # self.setStyleSheet("border: 2px solid red;")

        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.titleDownload)
        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.addStretch()
        self.titleLayout.setSpacing(2)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)

        self.channelFlowlayout.addWidget(self.tencentCheckBox)
        self.channelFlowlayout.addWidget(self.atomGitCheckBox)
        self.channelLayout.addWidget(self.channelLabel)
        self.channelLayout.addWidget(self.githubCheckBox)
        self.channelLayout.addLayout(self.channelFlowlayout)

        self.changelogLayout.addWidget(self.changelogTitleLabel)
        self.changelogLayout.addWidget(self.changelog)
        # self.changelogLayout.setContentsMargins(5, 5, 5, 5)
        # self.changelogScrollArea.setMinimumHeight(0)
        self.changelogScrollArea.setMaximumHeight(66)
        self.changelogScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.changelogScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.confirmButton.setFixedWidth(140)
        self.cancelButton.setFixedWidth(140)
        self.buttonLayout.addWidget(self.confirmButton)
        self.buttonLayout.addWidget(self.cancelButton)

        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setContentsMargins(20, 16, 20, 16)
        self.vBoxLayout.addLayout(self.titleLayout)
        self.vBoxLayout.addWidget(self.changelogScrollArea)
        self.vBoxLayout.addLayout(self.channelLayout)
        self.vBoxLayout.addWidget(self.channelTipLabel)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addLayout(self.buttonLayout)

    def __connectSignalToSlot(self):
        self.titleDownload.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(RELEASE_URL)))

        self.confirmButton.clicked.connect(self.__onConfirmButtonClicked)
        self.cancelButton.clicked.connect(self.closed)

        self.githubCheckBox.toggled.connect(
            lambda checked: self.__onRepoClicked(checked, "GitHub"))
        self.tencentCheckBox.toggled.connect(
            lambda checked: self.__onRepoClicked(checked, "Tencent"))
        self.atomGitCheckBox.toggled.connect(
            lambda checked: self.__onRepoClicked(checked, "AtomGit"))

        # 有新的信号来，旧的全部自己关闭，防止多个弹窗
        signalBus.newVersionSignal.connect(self.closed)
        globalSignal.closeMainWindowSignal.connect(self.closed)

    def __loadConfig(self):
        repo = paramConfig.get(paramConfig.repo)
        if repo == "GitHub":
            self.githubCheckBox.setChecked(True)
        elif repo == "Tencent":
            self.tencentCheckBox.setChecked(True)
        elif repo == "AtomGit":
            self.atomGitCheckBox.setChecked(True)
        else:
            self.tencentCheckBox.setChecked(True)

    def __onRepoClicked(self, checked: bool, repo: str):
        if not checked:
            return
        paramConfig.set(paramConfig.repo, repo)

    def __onConfirmButtonClicked(self):
        code = 0
        if self.githubCheckBox.isChecked():
            code = 101
        elif self.tencentCheckBox.isChecked():
            code = 102
        elif self.atomGitCheckBox.isChecked():
            code = 103
        logger.debug(f"exit code: {code}")
        self.closed.emit()
        # sys.exit(code)
        # QApplication.instance().exit(code)
        # QApplication.instance().exit(0)
        globalSignal.sysExitSignal.emit(code)

    def paintEvent(self, e):
        # 不绘制边框和背景
        pass


class ToolbarWidget(QWidget):
    """ Toolbar widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.mainLayout = QHBoxLayout(self)

        self.themeButton = TransparentToolButton(FluentIcon.CONSTRACT, self)
        self.themeButton.setToolTip(self.tr('Toggle theme'))

        self.updateToolButton = TransparentToolButton(FluentIcon.RINGER, self)
        self.updateToolButton.setToolTip(self.tr('Update'))
        self.newVersion = ""
        self.updateView = None

        self.__initWidget()

    def __initWidget(self):
        self.themeButton.installEventFilter(ToolTipFilter(self.themeButton))
        self.updateToolButton.installEventFilter(ToolTipFilter(self.updateToolButton))

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.setObjectName('toolbar')
        self.mainLayout.addWidget(self.themeButton)
        self.mainLayout.addWidget(self.updateToolButton)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setAlignment(Qt.AlignTop)

    def __connectSignalToSlot(self):
        self.themeButton.clicked.connect(lambda: toggleTheme(True, True))
        self.updateToolButton.clicked.connect(self.showUpdateTeachingTip)
        signalBus.newVersionSignal.connect(self.__onNewVersion)

    def __onNewVersion(self, new_version: str):
        logger.debug(f"new_version: {new_version}")
        self.newVersion = new_version
        self.updateToolButton.click()

    def showUpdateTeachingTip(self):
        view = UpdateFlyoutView(VERSION, self.newVersion)

        w = PopupTeachingTip.make(
            target=self.updateToolButton,
            view=view,
            duration=-1,
            tailPosition=TeachingTipTailPosition.RIGHT_TOP,
            parent=self
        )

        view.closed.connect(w.close)


class BasicSettingWidget(QWidget):
    def __init__(self, /, parent=None):
        super().__init__(parent)

        from src.core.i18n import Language

        self.lang = [
            Language.ZH,
            Language.EN,
            Language.ZH_TW,
            Language.JA,
            Language.KO,
            Language.ES,
            Language.FR,
            Language.DE,
            Language.TH,
        ]
        self.langDesc = [
            "简体中文",
            "English",
            "繁體中文",
            "日本語",
            "한국어",
            "Español",
            "Français",
            "Deutsch",
            "ภาษาไทย",
        ]
        self.device = [
            "Auto",
            "Auto",
            "CPU",
        ]
        self.deviceDesc = [
            "自动",
            "GPU",
            "CPU",
        ]
        self.resourceQuality = [
            "UHD",
            "HD",
            "SD",
        ]
        self.resourceQualityDesc = [
            "极致",
            "高清（默认）",
            "流畅",
        ]

        self.mainLayout = QVBoxLayout(self)

        self.titleLabel = QLabel(self.tr("基础设置"), self)

        self.langLayout = QHBoxLayout()
        self.langLabel = QLabel(self.tr("游戏文本:"), self)
        self.langComboBox = ComboBox(self)
        # self.langComboBox.setPlaceholderText(self.tr("{text} - {sign}").format(
        #     text=self.langDesc[0], sign=self.lang[0].value))
        self.langComboBox.setPlaceholderText(self.tr("{text}").format(text=self.langDesc[0]))
        for i in range(len(self.lang)):
            # self.langComboBox.addItem(self.tr("{text} - {sign}").format(
            #     text=self.langDesc[i], sign=self.lang[i].value), userData=self.lang[i].value)
            self.langComboBox.addItem(self.tr("{text}").format(text=self.langDesc[i]), userData=self.lang[i].value)
            if i > 1:
                self.langComboBox.setItemEnabled(self.langComboBox.count() - 1, False)

        self.resourceQualityLayout = QHBoxLayout()
        self.resourceQualityLabel = QLabel(self.tr("资源等级:"), self)
        self.resourceQualityComboBox = ComboBox(self)
        # self.resourceQualityComboBox.setPlaceholderText(self.tr("{text} {level}").format(
        #     text=self.resourceQualityDesc[1], level=self.resourceQuality[1]))
        for i in range(len(self.resourceQuality)):
            self.resourceQualityComboBox.addItem(self.tr("{level} {text}").format(
                text=self.resourceQualityDesc[i], level=self.resourceQuality[i]), userData=self.resourceQuality[i])
        self.resourceQualityComboBox.setCurrentIndex(1)

        self.deviceLayout = QHBoxLayout()
        self.deviceLabel = QLabel(self.tr("运行设备:"), self)
        self.deviceComboBox = ComboBox(self)
        self.deviceComboBox.setPlaceholderText(self.tr("{text}").format(text=self.deviceDesc[0]))
        for i in range(len(self.device)):
            self.deviceComboBox.addItem(self.tr("{text}").format(text=self.deviceDesc[i]), userData=self.device[i])
            if i == 1:
                self.deviceComboBox.setItemEnabled(self.deviceComboBox.count() - 1, False)

        # self.gamePathHLayout = QHBoxLayout()
        # self.gamePathLabel = QLabel(self.tr("游戏路径:"), self.scrollWidget)
        # self.gamePathComboBox = ComboBox(self.scrollWidget)
        # TODO 订阅消息总线，实时写入当前任务消息
        self.messageEdit = TextEdit(self)
        self.messageEdit.setReadOnly(True)

        # self.descriptionEdit.setReadOnly(True)
        # self.descriptionEdit.setHtml("""
        #                 <h3>版本活动</h3>
        #
        #                 <ul>
        #                 <li>双倍无音区</li>
        #                 </ul>
        #                 """)

        self.__initWidget()

    def __initWidget(self):
        self.setObjectName('view')

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        self.langLayout.addWidget(self.langLabel)
        self.langLayout.addWidget(self.langComboBox, 1)
        self.resourceQualityLayout.addWidget(self.resourceQualityLabel)
        self.resourceQualityLayout.addWidget(self.resourceQualityComboBox, 1)
        self.deviceLayout.addWidget(self.deviceLabel)
        self.deviceLayout.addWidget(self.deviceComboBox, 1)
        # self.langLayout.setContentsMargins(0, 0, 0, 0)
        # self.langLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.mainLayout.addWidget(self.titleLabel)
        self.mainLayout.addLayout(self.langLayout)
        self.mainLayout.addLayout(self.resourceQualityLayout)
        self.mainLayout.addLayout(self.deviceLayout)
        self.mainLayout.addWidget(self.messageEdit, 1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        # self.mainLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def __connectSignalToSlot(self):
        self.langComboBox.currentIndexChanged.connect(self.__onLangComboBoxChanged)
        self.resourceQualityComboBox.currentIndexChanged.connect(self.__onResourceQualityChanged)
        self.deviceComboBox.currentIndexChanged.connect(self.__onDeviceComboBoxChanged)
        signalBus.homeMessageSignal.connect(self.__onMessageChanged)

    def __onLangComboBoxChanged(self, index):
        paramConfig.set(paramConfig.gameLanguage, self.langComboBox.currentData())
        # self.__refreshGridLayout(index)

    def __onResourceQualityChanged(self, index):
        paramConfig.set(paramConfig.resourceQuality, self.resourceQualityComboBox.currentData())

    def __onDeviceComboBoxChanged(self, index):
        paramConfig.set(paramConfig.device, self.deviceComboBox.currentData())

    def __onMessageChanged(self, msg):
        scrollbar = self.messageEdit.verticalScrollBar()
        is_at_bottom = scrollbar.value() == scrollbar.maximum()
        # self.messageEdit.append(f"{datetime.now().strftime("%H:%M:%S")} - {msg}")
        self.messageEdit.append(f"{datetime.now().strftime("%H:%M")}: {msg}")
        if is_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def __loadConfig(self):
        self.langComboBox.setCurrentIndex(
            self.langComboBox.findData(paramConfig.get(paramConfig.gameLanguage)))
        if resourceQuality := paramConfig.get(paramConfig.resourceQuality):
            self.resourceQualityComboBox.setCurrentIndex(self.resourceQualityComboBox.findData(resourceQuality))
        self.deviceComboBox.setCurrentIndex(
            self.deviceComboBox.findData(paramConfig.get(paramConfig.device)))


class ContentWidget(QWidget):

    def __init__(self, /, parent=None):
        super().__init__(parent=parent)

        self.mainLayout = QVBoxLayout(self)

        self.pivot = Pivot(self)
        # self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)

        self.daily = DailyWidget(self)
        self.echo = EchoWidget(self)
        self.explore = ExploreWidget(self)
        self.events = EventsWidget(self)
        self.gameSettings = GameSettingsWidget(self)
        # self.help = QLabel(self.tr("施工中..."), self)
        # self.help.setAlignment(Qt.AlignVCenter| Qt.AlignHCenter)

        # add items to pivot
        self.addSubInterface(self.daily, 'daily', self.tr("日常"))
        self.addSubInterface(self.echo, 'echo', self.tr("声骸"))
        self.addSubInterface(self.explore, 'explore', self.tr("探索"))
        self.addSubInterface(self.events, 'events', self.tr("活动"))
        self.addSubInterface(self.gameSettings, 'gameSettings', self.tr("设置"))
        # self.addSubInterface(self.help, 'help', self.tr("帮助"))

        self.currentTask = self.daily
        self.stackedWidget.setCurrentWidget(self.gameSettings)
        self.pivot.setCurrentItem(self.gameSettings.objectName())

        self.__initWidget()

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def __initWidget(self):
        self.setObjectName('view')

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.mainLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        self.mainLayout.addWidget(self.stackedWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

    def __connectSignalToSlot(self):
        self.pivot.currentItemChanged.connect(self.__onCurrentItemChanged)

    def __onCurrentItemChanged(self, k):
        currentWidget = self.findChild(QWidget, k)
        self.stackedWidget.setCurrentWidget(currentWidget)
        globalSignal.taskChangedSignal.emit(currentWidget.currentTask)
        # logger.debug(f"Current task: {currentWidget.currentTask}")

    def refreshDefaultTask(self):
        globalSignal.taskChangedSignal.emit(self.daily.currentTask)


class BottomWidget(CardWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.setFixedSize(570, 70)
        self.setFixedHeight(70)
        self.setMaximumWidth(570)

        self.mainLayout = QHBoxLayout(self)

        self.titleLabel = QLabel(self.tr("运行"), self)
        self.titleLabel.setObjectName('titleLabel')

        # 双倍提醒
        self.tipsLabel = QLabel(self.__tipsText(), self)
        self.tipsLabel.setWordWrap(True)
        self.tipsLabel.setAlignment(Qt.AlignCenter)

        self.spinner = IndeterminateProgressRing(self, start=False)
        self.spinner.setStrokeWidth(3)
        self.spinner.setFixedSize(30, 30)

        self.button = ToggleToolButton(FluentIcon.PLAY_SOLID, self)
        self.button.setChecked(False)
        self.button.setFixedSize(100, 50)

        self.mainLayout.addWidget(self.titleLabel)
        self.mainLayout.addWidget(self.tipsLabel, 1)
        self.mainLayout.addWidget(self.spinner)
        self.mainLayout.addSpacing(28)
        self.mainLayout.addWidget(self.button)
        self.mainLayout.setContentsMargins(36, 0, 20, 0)

        self.currentTask = None
        self._submittedTask = None

        # self.setStyleSheet("border: 2px solid red;")

        self.__connectSignalToSlot()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.__updateTipsText)
        self.timer.start(5000)

    def __connectSignalToSlot(self):
        self.button.clicked.connect(self.__onButtonClicked)
        globalSignal.taskChangedSignal.connect(self.__onTaskChanged)
        globalSignal.taskFinishedSignal.connect(self.__on_task_finished)

    def __onButtonClicked(self):
        # 根据是否有已提交的任务来判断按钮状态
        if self._submittedTask:
            try:
                self._submittedTask.submitTask(False)
            except Exception as e:
                logger.exception(f"submit task error", e)
                return
            self._submittedTask = None
            self.__refreshButton(False)
            return

        if not self.currentTask:
            self.__refreshButton(False)
            return

        self.__refreshButton(True)
        try:
            result = self.currentTask.submitTask(True)
        except Exception as e:
            logger.exception(f"submit task error", e)
            self.__refreshButton(False)
            return

        logger.debug(f"submit task result: {result}")
        if result.success:
            self._submittedTask = self.currentTask
        else:
            # self.button.setChecked(False)
            self.__refreshButton(False)
            self.createTopRightInfoWarningBar(self.tr('Validate: '), result.message, 5000)

    def __refreshButton(self, start: bool):
        if start:
            self.spinner.start()
            self.button.setIcon(FluentIcon.PAUSE_BOLD)
            # self.button.setChecked(True)
        else:
            self.spinner.stop()
            self.spinner.reset()
            self.button.setIcon(FluentIcon.PLAY_SOLID)
            # self.button.setChecked(False)

    def __onTaskChanged(self, currentTask):
        self.currentTask = currentTask
        logger.debug(f"Current task: {self.currentTask}")

        self.__updateTipsText()

    def __on_task_finished(self, task_name):
        logger.debug(f"task_finished: {task_name}")

        if self._submittedTask is not None:
            elapsed = ""
            if self._submittedTask.start_time:
                elapsed_seconds = (datetime.now() - self._submittedTask.start_time).total_seconds()
                hours, remainder = divmod(elapsed_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if int(hours) > 0:
                    elapsed = f", {int(hours)}h {int(minutes)}m {seconds:.2f}s"
                elif int(minutes) > 0:
                    elapsed = f", {int(minutes)}m {seconds:.2f}s"
                else:
                    elapsed = f", {seconds:.2f}s"
            signalBus.homeMessageSignal.emit(f"{self.tr("Stop")} {self._submittedTask.name}{elapsed}")
            self._submittedTask = None

        self.spinner.stop()
        self.spinner.reset()
        self.button.setIcon(FluentIcon.PLAY_SOLID)

        self.button.blockSignals(True)
        self.button.setChecked(False)
        self.button.blockSignals(False)

    def __updateTipsText(self):
        self.tipsLabel.setText(self.__tipsText())

    def __tipsText(self) -> str:
        # 双倍提醒
        tipsText = ''
        try:
            v = Version(re.search(r"\d+(?:\.\d+){0,2}", __version__).group())
        except Exception as e:
            logger.exception(e)
            return tipsText
        if v.major > 3 or v.major == 3 and v.minor >= 7:
            if TimeRange.from_str("2026-10-15 04:00", "2026-10-22 04:00").contains():
                tipsText = f'<b><font color="red">{self.tr("今日: 双倍养成材料")}</font></b>'
                globalSignal.doubleDropSignal.emit(True)
            elif TimeRange.from_str("2026-11-04 04:00", "2026-11-11 04:00").contains():
                tipsText = f'<b><font color="red">{self.tr("今日: 双倍声骸材料")}</font></b>'
                globalSignal.doubleDropSignal.emit(False)
            if tipsText:
                return tipsText
        if v.major > 3 or v.major == 3 and v.minor >= 6:
            if TimeRange.from_str("2026-09-03 04:00", "2026-09-10 04:00").contains():
                tipsText = f'<b><font color="red">{self.tr("今日: 双倍养成材料")}</font></b>'
                globalSignal.doubleDropSignal.emit(True)
            elif TimeRange.from_str("2026-09-22 04:00", "2026-09-29 04:00").contains():
                tipsText = f'<b><font color="red">{self.tr("今日: 双倍声骸材料")}</font></b>'
                globalSignal.doubleDropSignal.emit(False)
            if tipsText:
                return tipsText
        return tipsText

    def createTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self.parent()
        )

    def createTopRightInfoWarningBar(self, title: str, content: str, duration: int):
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self.parent()
        )


class HomeV2Interface(ScrollArea):
    """ Home interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        StyleSheet.HOME_INTERFACE.apply(self)

        self.mainLayout = QVBoxLayout(self)
        self.container = QWidget(self)

        self.banner = BannerWidget(self)
        self.toolbarWidget = ToolbarWidget(self)
        self.topLayout = QHBoxLayout()
        self.middleLayout = QHBoxLayout()

        self.contentWidget = ContentWidget(self.container)
        self.basicSettingWidget = BasicSettingWidget(self.container)

        self.bottomWidget = BottomWidget(self.container)

        # self.setStyleSheet("border: 2px solid red;")

        self.__initWidget()

        self.contentWidget.refreshDefaultTask()

    def __initWidget(self):
        self.container.setObjectName('view')
        self.setObjectName('homeInterface')
        # StyleSheet.HOME_INTERFACE.apply(self)

        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.topLayout.addWidget(self.banner, 1)
        # self.topLayout.addStretch()
        self.topLayout.addWidget(self.toolbarWidget)

        self.middleLayout.addWidget(self.contentWidget, 3)
        self.middleLayout.addWidget(self.basicSettingWidget, 1)
        self.middleLayout.setContentsMargins(6, 0, 0, 0)

        self.mainLayout.addLayout(self.topLayout)
        self.mainLayout.addSpacing(12)
        self.mainLayout.addLayout(self.middleLayout, 1)
        self.mainLayout.addWidget(self.bottomWidget)
        self.mainLayout.setContentsMargins(36, 18, 16, 8)
        self.mainLayout.setSpacing(0)

    def __connectSignalToSlot(self):
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # w = self.width()
        # logger.warning(f"self.width(): {w}")
        #
        # if w < 800:
        #     self.mainLayout.setContentsMargins(36, 12, 16, 8)
        # else:
        #     self.mainLayout.setContentsMargins(36, 12, 16, 8)
