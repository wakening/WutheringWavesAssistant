# coding:utf-8
import logging
import re
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStackedWidget
from packaging.version import Version

from qfluentwidgets import (ScrollArea, ComboBox, TextEdit, Pivot, IndeterminateProgressRing, ToggleToolButton,
                            FluentIcon, CardWidget, InfoBar, InfoBarPosition)

from src import __version__
from src.gui.common.config import paramConfig
from src.gui.common.globals import GlobalSignal, globalSignal
from src.gui.view.home.daily import DailyWidget
from src.gui.common.style_sheet import StyleSheet
from src.gui.view.home.echo import EchoWidget
from src.gui.view.home.events import EventsWidget
from src.gui.view.home.explore import ExploreWidget
from src.gui.view.home.story import StoryWidget

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
            "CUDA",
            "CPU",
        ]
        self.deviceDesc = [
            "自动",
            "GPU-CUDA",
            "CPU",
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
        self.deviceLayout.addWidget(self.deviceLabel)
        self.deviceLayout.addWidget(self.deviceComboBox, 1)
        # self.langLayout.setContentsMargins(0, 0, 0, 0)
        # self.langLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.mainLayout.addWidget(self.titleLabel)
        self.mainLayout.addLayout(self.langLayout)
        self.mainLayout.addLayout(self.deviceLayout)
        self.mainLayout.addWidget(self.messageEdit, 1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        # self.mainLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def __connectSignalToSlot(self):
        self.langComboBox.currentIndexChanged.connect(self.__onLangComboBoxChanged)
        self.deviceComboBox.currentIndexChanged.connect(self.__onDeviceComboBoxChanged)

    def __onLangComboBoxChanged(self, index):
        paramConfig.set(paramConfig.gameLanguage, self.langComboBox.currentData())
        # self.__refreshGridLayout(index)

    def __onDeviceComboBoxChanged(self, index):
        paramConfig.set(paramConfig.device, self.deviceComboBox.currentData())

    def __loadConfig(self):
        self.langComboBox.setCurrentIndex(
            self.langComboBox.findData(paramConfig.get(paramConfig.gameLanguage)))
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
        self.story = StoryWidget(self)
        self.explore = ExploreWidget(self)
        self.events = EventsWidget(self)
        # self.help = QLabel(self.tr("施工中..."), self)
        # self.help.setAlignment(Qt.AlignVCenter| Qt.AlignHCenter)

        # add items to pivot
        self.addSubInterface(self.daily, 'daily', self.tr("日常"))
        self.addSubInterface(self.echo, 'echo', self.tr("声骸"))
        self.addSubInterface(self.explore, 'explore', self.tr("探索"))
        self.addSubInterface(self.story, 'story', self.tr("剧情"))
        self.addSubInterface(self.events, 'events', self.tr("活动"))
        # self.addSubInterface(self.help, 'help', self.tr("帮助"))

        self.currentTask = self.daily
        self.stackedWidget.setCurrentWidget(self.daily)
        self.pivot.setCurrentItem(self.daily.objectName())

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

        self.tipsLabel.setText(self.__tipsText())

    def __on_task_finished(self, task_name):
        logger.debug(f"task_finished: {task_name}")
        self._submittedTask = None

        self.spinner.stop()
        self.spinner.reset()
        self.button.setIcon(FluentIcon.PLAY_SOLID)

        self.button.blockSignals(True)
        self.button.setChecked(False)
        self.button.blockSignals(False)

    def __tipsText(self) -> str:
        # 双倍提醒
        tipsText = ''
        v = Version(re.search(r"\d+(?:\.\d+){0,2}", __version__).group())
        if (v.major, v.minor) == (3, 5):
            if TimeRange.from_str("2026-07-23 04:00", "2026-07-30 04:00").contains():
                tipsText = '<b><font color="red">今日: 双倍材料本</font></b>'
            elif TimeRange.from_str("2026-08-12 04:00", "2026-08-19 04:00").contains():
                tipsText = '<b><font color="red">今日: 双倍无音区</font></b>'
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
        self.middleLayout.addWidget(self.contentWidget, 3)
        self.middleLayout.addWidget(self.basicSettingWidget, 1)
        self.middleLayout.setContentsMargins(6, 0, 0, 0)

        self.mainLayout.addWidget(self.banner)
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
