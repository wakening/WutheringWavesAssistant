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

        self.autoCombatCheckBox = CheckBox(self.tr("Auto Combat:"), self)
        self.autoCombatDescLabels = [
            QLabel(self.tr(r'Hotkeys: Mouse [Side Button 1], [Side Button 2], Keyboard [5 (above R)], or [`~]. Choose any one of the four options; you do not need to press them all.'), self, wordWrap=True),
            QLabel(self.tr(r'Usage: Start the script and return to the game. Press the assigned hotkey to start auto combat. Press the hotkey again or ESC to stop.'), self, wordWrap=True),
            QLabel(self.tr(r'Suitable for: Overworld farming, story battles, and some event battles.'), self, wordWrap=True),
            QLabel(self.tr(r"Note: When pressing the hotkey, make sure the character portraits on the right side of the screen are visible. Otherwise, the script won't be able to detect your characters or switch between them."), self, wordWrap=True),
        ]
        self.autoCombatLayout = QVBoxLayout()
        for label in self.autoCombatDescLabels:
            self.autoCombatLayout.addWidget(label)
        self.autoCombatLayout.setSpacing(2)
        self.autoCombatLayout.setContentsMargins(30, 0, 0, 0)

        self.autoPickupCheckBox = CheckBox(self.tr("Auto Pickup:"), self)
        self.autoPickupDescLabel = QLabel(
            self.tr("Automatically pick up: ✅Echoes, ✅Herbs, ✅Ingredients, ✅Chests."), self, wordWrap=True)
        self.autoPickupDescLabel.setWordWrap(True)
        self.autoPickupLayout = QVBoxLayout()
        self.autoPickupLayout.addWidget(self.autoPickupDescLabel)
        self.autoPickupLayout.setContentsMargins(30, 0, 0, 0)

        self.skipStoryCheckBox = CheckBox(self.tr("Skip Story:"), self)
        self.skipStoryDescLabels = [
            QLabel(self.tr("Enable this if you prefer to skip the story."), self, wordWrap=True),
            QLabel(self.tr("Automatically clicks the Skip button in the top-left corner when a cutscene starts. If it fails to detect the button against a white background, try clicking it manually."), self, wordWrap=True),
        ]
        self.skipStoryLayout = QVBoxLayout()
        for label in self.skipStoryDescLabels:
            self.skipStoryLayout.addWidget(label)
        self.skipStoryLayout.setSpacing(2)
        self.skipStoryLayout.setContentsMargins(30, 0, 0, 0)

        self.autoDialogueCheckBox = CheckBox(self.tr("Auto Dialogue:"), self)
        self.autoDialogueDescLabels = [
            QLabel(self.tr("Enable this if you want to watch the story."), self, wordWrap=True),
            QLabel(self.tr("Once a dialogue sequence starts, you can take your hands off the keyboard. ✅ Auto-advances dialogue. ✅ Automatically selects dialogue options. Continues until the dialogue sequence ends."), self, wordWrap=True),
        ]
        self.autoDialogueLayout = QVBoxLayout()
        for label in self.autoDialogueDescLabels:
            self.autoDialogueLayout.addWidget(label)
        self.autoDialogueLayout.setSpacing(2)
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

        self.tipsLabels = [
            QLabel(self.tr("Exploration and other open-world activities must be performed manually. Automated open-world farming is not supported!"), self.container, wordWrap=True),
            QLabel(self.tr("Please select the features you want to use. Multiple selections are allowed. Supports any resolution."), self.container, wordWrap=True)
        ]
        self.tipsLayout = QVBoxLayout()

        self.storyExploreWidget = StoryExploreWidget(self.container)

        self.__initWidget()

        self.currentTask = self.storyExploreWidget.task

    def __initWidget(self):
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
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
        for label in self.tipsLabels:
            self.tipsLayout.addWidget(label)
        self.tipsLayout.setSpacing(3)

        self.mainLayout.addLayout(self.tipsLayout)
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
