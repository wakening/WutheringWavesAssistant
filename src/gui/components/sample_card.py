# coding:utf-8
import logging

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup, QSizePolicy

from qfluentwidgets import IconWidget, TextWrap, FlowLayout, CardWidget, SwitchButton, IndicatorPosition, \
    ToggleToolButton, FluentIcon, ProgressRing, IndeterminateProgressRing, InfoBar, InfoBarPosition

from .my_flow_layout import FixFlowLayout
from ..common.config import paramConfig
from ..common.globals import globalSignal
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..view.param_interface import AutoBossParamSettingCard, MacroParamSettingCard, DailyTaskSettingCard

logger = logging.getLogger(__name__)

class SampleCard(CardWidget):
    """ Sample card """

    task_selected = Signal(str)

    def __init__(self, icon, title, content, routeKey, index, parent=None, group_index = None, task_name = None, tooltip = None, checked=False, **kwargs):
        super().__init__(parent=parent)
        self.index = index
        self.routekey = routeKey

        self.iconWidget = IconWidget(icon, self)

        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(TextWrap.wrap(content, 57, False)[0], self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedSize(570, 90)
        self.iconWidget.setFixedSize(48, 48)

        self.hBoxLayout.setSpacing(28)
        self.hBoxLayout.setContentsMargins(20, 0, 20, 0)
        self.vBoxLayout.setSpacing(2)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.switchButton = SwitchButton(self, IndicatorPosition.LEFT)
        self.switchButton.checkedChanged.connect(self.onCheckedChanged)

        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addStretch()  # 添加一个弹性空间，让后面的控件推到最右侧
        self.hBoxLayout.addWidget(self.switchButton)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addStretch(1)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')

        self._parent = parent
        self.group_index = group_index
        self.task_name = task_name

        if tooltip:
            self.setToolTip(tooltip)

        self.setCursor(Qt.PointingHandCursor)

        if checked:
            self.switchButton.setChecked(True)

    def onCheckedChanged(self, isChecked: bool):
        if self.group_index > 7:
            if isChecked:
                self.switchButton.setChecked(False)
                self.createTopRightInfoBar()
            return

        if isChecked:
            # 将其他按钮设置为关闭，限制只能选择一个 TODO后续支持多个
            self._parent.handleSwitchChange(self.group_index)
            emit_task_name = self.task_name
        else:
            emit_task_name = ""
        self.task_selected.emit(emit_task_name)

    def createTopRightInfoBar(self):
        InfoBar.info(
            title=self.tr('Tips'),
            content=self.tr("敬请期待"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2500,
            parent=self.parent().parent().parent()
        )

    def mouseReleaseEvent(self, event):
        # 获取事件位置，判断是否点击了 switchButton
        if self.switchButton.rect().contains(event.pos()):
            # 如果是点击开关按钮，不执行默认的点击行为
            return

        super().mouseReleaseEvent(event)

        is_expand = self._parent.toggle_expand(self.group_index)
        # 展开参数与按钮联动
        if is_expand is None:
            # 没有参数的，直接切换
            current_state = self.switchButton.isChecked()
            self.switchButton.setChecked(not current_state)
        elif is_expand is True:
            # 触发了展开的，若没打开开关就打开
            current_state = self.switchButton.isChecked()
            if not current_state:
                self.switchButton.setChecked(True)
        else:
            # 触发了关闭的，若打开了开关就关闭
            current_state = self.switchButton.isChecked()
            if current_state:
                self.switchButton.setChecked(False)


class RunCard(CardWidget):
    """ Sample card """

    def __init__(self, icon, title, content, routeKey, index, parent=None):
        super().__init__(parent=parent)
        self.index = index
        self.routekey = routeKey

        self.spinner = IndeterminateProgressRing(self, start=False)
        self.spinner.setStrokeWidth(4)

        # self.iconWidget = IconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        # self.contentLabel = QLabel(TextWrap.wrap(content, 45, False)[0], self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedSize(570, 90)
        # self.iconWidget.setFixedSize(40, 40)
        self.spinner.setFixedSize(40, 40)

        self.hBoxLayout.setSpacing(28)
        self.hBoxLayout.setContentsMargins(36, 0, 20, 0)
        self.vBoxLayout.setSpacing(2)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        # self.switchButton = SwitchButton(self.tr('Off'), parent=self, indicatorPos=IndicatorPosition.LEFT)
        # self.switchButton.checkedChanged.connect(self.onCheckedChanged)
        self.button = ToggleToolButton(FluentIcon.PLAY_SOLID, self)
        self.button.clicked.connect(self.onButtonClicked)
        self.button.setFixedSize(100, 50)

        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        # self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addStretch()  # 添加一个弹性空间，让后面的控件推到最右侧
        self.hBoxLayout.addWidget(self.spinner)
        self.hBoxLayout.addWidget(self.button)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel)
        # self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addStretch(1)

        self.titleLabel.setObjectName('titleLabel')
        # self.contentLabel.setObjectName('contentLabel')

        self.checked_task_name = None
        self.running_task_name = None

        globalSignal.taskFinishedSignal.connect(self.on_task_finished)

        self.task_start_notice = {
            # "AutoBossProcessTask": AutoBossProcessTask,
            # "AutoPickupProcessTask": self.tr("Auto Pickup"),
            # "AutoStorySkipProcessTask": self.tr("Skip Life"),
            # "AutoStoryEnjoyProcessTask": self.tr("Enjoy Life"),
            # "DailyActivityProcessTask": DailyActivityProcessTask,
            # "EchoMergeProcessTask": self.tr("Data Merge"),
            # "SoarToTheBeatMacroRecordTask": self.tr("Macro Record"),
            # "SoarToTheBeatMacroReplayTask": self.tr("Macro Replay"),
        }

        self.task_finished_notice = {
            # "AutoBossProcessTask": AutoBossProcessTask,
            # "AutoPickupProcessTask": "Auto Pickup",
            # "AutoStorySkipProcessTask": "Skip Life",
            # "AutoStoryEnjoyProcessTask": "Enjoy Life",
            # "DailyActivityProcessTask": DailyActivityProcessTask,
            # "EchoMergeProcessTask": self.tr("Data Merge Finished"),
            # "SoarToTheBeatMacroRecordTask": self.tr("Macro Record Finished"),
            # "SoarToTheBeatMacroReplayTask": self.tr("Macro Replay Finished"),
        }

    def onButtonClicked(self):
        # if self.button.isChecked():
        if not self.running_task_name:
            if self.checked_task_name:
                logger.info("任务名: %s", self.checked_task_name)

                if self.checked_task_name == "AutoBossProcessTask" and paramConfig and paramConfig.bossName:
                    try:
                        if not paramConfig.bossName.value:
                            self.createTopRightInfoWarningBar(self.tr('Reminder: '), self.tr("未选择Boss"), 3000)
                            self.button.blockSignals(True)
                            self.button.setChecked(False)
                            self.button.blockSignals(False)
                            return
                        boss_name_list = [item.value for item in paramConfig.bossName.value]
                        msg = self.tr("{boss_name}").format(boss_name=str(boss_name_list))
                        self.createTopRightInfoBar(self.tr('Boss Rush: '), msg, 5000)
                    except Exception:
                        pass
                elif self.checked_task_name in self.task_start_notice:
                    msg = self.task_start_notice.get(self.checked_task_name)
                    # msg = msg if msg else "Submit"
                    if msg:
                        self.createTopRightInfoBar(self.tr('Task: '), msg, 3000)

                self.button.setIcon(FluentIcon.PAUSE_BOLD)
                self.spinner.start()
                self.running_task_name = self.checked_task_name

                self.button.blockSignals(True)
                self.button.setChecked(True)
                self.button.blockSignals(False)

                globalSignal.executeTaskSignal.emit(self.running_task_name, "START")
            else:
                self.createTopRightInfoWarningBar(self.tr('Reminder: '), self.tr("没有要运行的任务"), 3000)

                self.button.blockSignals(True)
                self.button.setChecked(False)
                self.button.blockSignals(False)
        else: # stop
            if self.running_task_name:
                globalSignal.executeTaskSignal.emit(self.running_task_name, "STOP")
                self.running_task_name = None

            self.spinner.stop()
            self.spinner.reset()
            self.button.setIcon(FluentIcon.PLAY_SOLID)

            # 同步 UI checked
            self.button.blockSignals(True)
            self.button.setChecked(False)
            self.button.blockSignals(False)

    def on_task_finished(self, task_name):
        logger.debug("on_task_finished: %s", task_name)
        self.running_task_name = None

        self.spinner.stop()
        self.spinner.reset()
        self.button.setIcon(FluentIcon.PLAY_SOLID)

        self.button.blockSignals(True)
        self.button.setChecked(False)
        self.button.blockSignals(False)

        msg = self.task_finished_notice.get(task_name)
        if msg:
            self.createTopRightInfoBar(self.tr('Task: '), msg, 3000)
            # self.createDeskTopTopRightInfoBar(self.tr('Task: '), msg, 4000)

    def update_task(self, task_name: str):
        self.checked_task_name = task_name

    def createTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self.parent().parent().parent()
        )

    def createTopRightInfoWarningBar(self, title: str, content: str, duration: int):
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self.parent().parent().parent()
        )

    def createDeskTopTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=duration,
            parent=InfoBar.desktopView()
        )


class SimpleExpandWidget(QWidget):
    def __init__(self, parent=None, index=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        #  调试边框
        # self.setStyleSheet("border: 2px solid red;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 10)

        # self.label = QLabel("这里是展开区域", self)
        # self.layout.addWidget(self.label)

        if index == 0:
            self.card = AutoBossParamSettingCard(self)
        elif index == 4:
            self.card = MacroParamSettingCard(self)
        elif index == 7:
            self.card = DailyTaskSettingCard(self)

        self.layout.addWidget(self.card)

        self.layout.setAlignment(Qt.AlignTop)


class SampleCardView(QWidget):
    """ Sample card view """

    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.flowLayout = FixFlowLayout(isTight=True)

        self.vBoxLayout.setContentsMargins(36, 0, 36, 0)
        self.vBoxLayout.setSpacing(10)
        self.flowLayout.setContentsMargins(0, 0, 0, 0)
        self.flowLayout.setHorizontalSpacing(12)
        self.flowLayout.setVerticalSpacing(12)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.flowLayout)

        self.titleLabel.setObjectName('viewTitleLabel')
        StyleSheet.SAMPLE_CARD.apply(self)

        self.card_group: list[SampleCard] = []
        self.select_task = None
        self.run = None

        self.current_expand = None
        self.current_index = -1
        self.cache_expand = []

        self.autoBoss = SimpleExpandWidget(self, 0)
        self.autoBoss.setVisible(False)
        self.macro = SimpleExpandWidget(self, 4)
        self.macro.setVisible(False)
        self.daily = SimpleExpandWidget(self, 7)
        self.daily.setVisible(False)

        self.is_init = False

    def addSampleCard(self, icon, title, content, routeKey, index, task_name, **kwargs):
        """ add sample card """
        card = SampleCard(icon, title, content, routeKey, index, self, len(self.card_group), task_name, **kwargs)
        self.flowLayout.addWidget(card)
        self.card_group.append(card)

    def addRun(self, icon, title, content, routeKey, index):
        self.run = RunCard(icon, title, content, routeKey, index, self)
        self.flowLayout.addWidget(self.run)
        return self.run

    # def addStartGame(self, icon, title, content, routeKey, index):
    #     self.run = StartGameCard(icon, title, content, routeKey, index, self)
    #     self.flowLayout.addWidget(self.run)
    #     return self.run

    def handleSwitchChange(self, group_index: int):
        """ Ensure that only one switch button is active at a time """
        for i in range(len(self.card_group)):
            if i == group_index:
                continue
            btn = self.card_group[i].switchButton
            if btn.isChecked():
                btn.setChecked(False)

    def toggle_expand(self, index: int):

        # TODO 改成自动，不写死
        if self.is_init is False:
            self.is_init = True
            self.flowLayout.setExpandWidget(0, self.autoBoss)
            self.flowLayout.setExpandWidget(4, self.macro)
            self.flowLayout.setExpandWidget(7, self.daily)

        # if index not in [0, 4]:
        #     for cache_index in self.cache_expand:
        #         self.flowLayout.toggleExpand(cache_index, False)
        #     return None

        # isVisible = self.flowLayout.toggleExpand(index)
        # if isVisible:
        #     self.cache_expand.append(index)
        # return isVisible

        isVisible = self.flowLayout.toggleExpand(index)
        if isVisible is None:
            for cache_index in self.cache_expand:
                self.flowLayout.toggleExpand(cache_index, False)
        elif isVisible is True:
            for cache_index in self.cache_expand:
                if index != cache_index:
                    self.flowLayout.toggleExpand(cache_index, False)
            if index not in self.cache_expand:
                self.cache_expand.append(index)
        else:
            pass
        return isVisible

        # logger.warning(f"toggle_expand: {index}")
        #
        # # 删除旧的
        # if self.current_expand:
        #     self.current_expand.setVisible(False)
        #     self.current_expand = None
        #     self.flowLayout.invalidate()
        #     self.flowLayout.activate()
        #
        #     if self.current_index == index:
        #         self.current_index = -1
        #         return False
        #
        # # TODO 不写死
        # if index not in [0, 4]:
        #     return None
        #
        # # 1. 找整行范围
        # start_index = self.find_row_start_index(index)
        # end_index = self.find_row_end_index(index)
        #
        # # 2. 算整行真实宽度
        # row_width = self.get_row_width(start_index, end_index)
        #
        # # 3. 创建 expand
        # if index == 0:
        #     self.current_expand = self.autoBoss
        # elif index == 4:
        #     self.current_expand = self.macro
        # self.current_expand.setFixedWidth(row_width)
        # self.current_expand.setVisible(True)
        #
        # if index not in self.cache_expand:
        #     count = len([x for x in self.cache_expand if index > x and index >= 0])
        #     # 4. 插入到“这一行最后”
        #     self.flowLayout.insertWidget(end_index + 1 + count, self.current_expand)
        #
        # self.flowLayout.invalidate()  # 刷新 flowLayout，确保插入的组件在布局中显示
        # self.flowLayout.activate()
        #
        # self.current_index = index
        #
        # self.cache_expand.append(index)
        #
        # # self.parent().scrollArea.ensureWidgetVisible(self.card_group[index])

        return True

    # def find_row_start_index(self, index: int) -> int:
    #     cards = self.card_group
    #
    #     base_y = cards[index].y()
    #     first_index = index
    #
    #     for i in range(index - 1, -1, -1):
    #         y = cards[i].y()
    #
    #         if abs(y - base_y) < 10:
    #             first_index = i
    #         else:
    #             break
    #
    #     return first_index
    #
    # def find_row_end_index(self, index: int) -> int:
    #     cards = self.card_group
    #
    #     base_y = cards[index].y()
    #     last_index = index
    #
    #     for i in range(index + 1, len(cards)):
    #         y = cards[i].y()
    #
    #         if abs(y - base_y) < 10:
    #             last_index = i
    #         else:
    #             break
    #
    #     return last_index
    #
    # def get_row_width(self, start_index: int, end_index: int) -> int:
    #     cards = self.card_group
    #
    #     first = cards[start_index]
    #     last = cards[end_index]
    #
    #     left = first.x()
    #     right = last.x() + last.width()
    #
    #     return right - left