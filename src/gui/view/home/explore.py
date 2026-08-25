import logging

from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QIcon, QColor, QIntValidator
from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout,
                               QPushButton, QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout)
from qfluentwidgets import (FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
                            InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
                            SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
                            OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
                            SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
                            LineEdit, SettingCard, ComboBox, ConfigItem,
                            PushButton, ToolButton, MessageBox, CardWidget)

from src.gui.common.config import paramConfig
from src.gui.common.globals import globalParam, globalSignal
from src.gui.common.style_sheet import StyleSheet
from src.gui.common.task import TaskId, BaseTask, ValidationResult

logger = logging.getLogger(__name__)


class ExploreTask(BaseTask):

    def __init__(self, id: str, name: str, widget):
        super().__init__(id, name)
        self.widget = widget

    def validate(self, **kwargs) -> ValidationResult:
        return ValidationResult(success=True)

    def submitTask(self, start: bool):
        if start:
            result = self.validate()
            if result.success:
                self._createTopRightInfoBar(self.tr('Task: '), self.name, 5000)
                self.submit(start)
            return result
        self.submit(start)
        return None

    def _createTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self.widget.parent()
        )


class StoryExploreWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.task = ExploreTask(TaskId.ExploreTask, "ExploreTask", self)

        self.mainLayout = QVBoxLayout(self)

        self.autoCombatCheckBox = CheckBox(self.tr("自动战斗:"), self)
        self.autoCombatDescLabel = QLabel(
            self.tr(
                "用法：启动脚本，回到游戏，点击鼠标侧键，将自动战斗，再次点击侧键或ESC键，可停止战斗。\n"
                "适用于日常锄地，跑到怪附近，点侧键后挂机，打完点侧键停下，上车去下一个点。"
            ),
            self
        )
        self.autoCombatDescLabel.setWordWrap(True)
        self.autoCombatLayout = QHBoxLayout(self)
        self.autoCombatLayout.addWidget(self.autoCombatDescLabel)
        self.autoCombatLayout.setContentsMargins(30, 0, 0, 0)

        self.autoPickupCheckBox = CheckBox(self.tr("自动拾取:"), self)
        self.autoPickupDescLabel = QLabel(
            self.tr("自动拾取路过的✅声骸、✅草药、✅食材、✅宝箱。"),
            self
        )
        self.autoPickupDescLabel.setWordWrap(True)
        self.autoPickupLayout = QHBoxLayout(self)
        self.autoPickupLayout.addWidget(self.autoPickupDescLabel)
        self.autoPickupLayout.setContentsMargins(30, 0, 0, 0)

        self.skipStoryCheckBox = CheckBox(self.tr("跳过剧情:"), self)
        self.skipStoryDescLabel = QLabel(
            self.tr("触发剧情后自动帮你点击跳过。"),
            self
        )
        self.skipStoryDescLabel.setWordWrap(True)
        self.skipStoryLayout = QHBoxLayout(self)
        self.skipStoryLayout.addWidget(self.skipStoryDescLabel)
        self.skipStoryLayout.setContentsMargins(30, 0, 0, 0)

        self.autoDialogueCheckBox = CheckBox(self.tr("自动对话:"), self)
        self.autoDialogueDescLabel = QLabel(
            self.tr(
                "触发剧情后可直接双手离开键盘，✅自动播放，✅自动选择对话，直到这段剧情结束。"
            ),
            self
        )
        self.autoDialogueDescLabel.setWordWrap(True)
        self.autoDialogueLayout = QHBoxLayout(self)
        self.autoDialogueLayout.addWidget(self.autoDialogueDescLabel)
        self.autoDialogueLayout.setContentsMargins(30, 0, 0, 0)

        self.mainLayout.addWidget(self.autoCombatCheckBox)
        self.mainLayout.addLayout(self.autoCombatLayout)
        self.mainLayout.addWidget(self.autoPickupCheckBox)
        self.mainLayout.addLayout(self.autoPickupLayout)
        self.mainLayout.addWidget(self.skipStoryCheckBox)
        self.mainLayout.addLayout(self.skipStoryLayout)
        self.mainLayout.addWidget(self.autoDialogueCheckBox)
        self.mainLayout.addLayout(self.autoDialogueLayout)
        self.mainLayout.setContentsMargins(5, 0, 5, 0)

        self.__connectSignalToSlot()
        self.__loadConfig()

    def __connectSignalToSlot(self):
        self.skipStoryCheckBox.stateChanged.connect(
            lambda state: self.__onSkipStoryCheckBoxStateChanged(state))
        self.autoDialogueCheckBox.stateChanged.connect(
            lambda state: self.__onAutoDialogueCheckBoxStateChanged(state))

        self.autoCombatCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.exploreAutoCombat, checked))
        self.autoPickupCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.exploreAutoPickup, checked))
        self.skipStoryCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.exploreSkipStory, checked))
        self.autoDialogueCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.exploreAutoDialogue, checked))

    def __onSkipStoryCheckBoxStateChanged(self, state):
        if state == 2:
            self.autoDialogueCheckBox.setChecked(False)

    def __onAutoDialogueCheckBoxStateChanged(self, state):
        if state == 2:
            self.skipStoryCheckBox.setChecked(False)

    def __loadConfig(self):
        self.autoCombatCheckBox.setChecked(paramConfig.get(paramConfig.exploreAutoCombat))
        self.autoPickupCheckBox.setChecked(paramConfig.get(paramConfig.exploreAutoPickup))
        self.skipStoryCheckBox.setChecked(paramConfig.get(paramConfig.exploreSkipStory))
        self.autoDialogueCheckBox.setChecked(paramConfig.get(paramConfig.exploreAutoDialogue))


class ExploreWidget(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.container = QWidget(self)
        self.mainLayout = QVBoxLayout(self.container)

        self.tipsLabel = QLabel(self.tr("跑图等都需手动操作，不能代肝大世界！"), self.container)
        self.tipsLabel.setWordWrap(True)
        self.tipsLabel2 = QLabel(self.tr("请勾选需要的功能项，支持多选，任意分辨率"), self.container)

        self.storyExploreWidget = StoryExploreWidget(self.container)

        self.__initWidget()

        self.currentTask = self.storyExploreWidget.task

    def __initWidget(self):
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        # self.setObjectName('paramInterface')

        # initialize style sheet
        self.container.setObjectName('view')
        StyleSheet.PARAM_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.mainLayout.addWidget(self.tipsLabel)
        self.mainLayout.addWidget(self.tipsLabel2)
        self.mainLayout.addWidget(self.storyExploreWidget)
        self.mainLayout.addStretch()
        self.mainLayout.setSpacing(20)
        self.mainLayout.setContentsMargins(16, 26, 16, 10)

    def __connectSignalToSlot(self):
        # self.autopickWidget.checkbox.stateChanged.connect(
        #     lambda _: self.__onTaskChecked(self.autopickWidget.checkbox, self.autopickWidget.task))
        # self.autoCombatWidget.checkbox.stateChanged.connect(
        #     lambda _: self.__onTaskChecked(self.autoCombatWidget.checkbox, self.autoCombatWidget.task))
        pass

    def __onTaskChecked(self, checkbox, currentTask):
        # logger.debug(f"echo __onTaskChecked: {checkbox.isChecked()}")
        if checkbox.isChecked():
            self.currentTask = currentTask
            globalSignal.taskChangedSignal.emit(currentTask)
            # logger.debug(f"Current task: {self.currentTask}")
