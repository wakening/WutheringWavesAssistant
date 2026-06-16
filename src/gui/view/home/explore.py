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


class AutoPickupProcessTask(ExploreTask):

    def __init__(self, widget):
        super().__init__(TaskId.AutoPickupProcessTask, "AutoPickup", widget)


class AutoPickupWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.task = AutoPickupProcessTask(self)

        self.mainLayout = QVBoxLayout(self)

        self.checkbox = CheckBox(self.tr("自动拾取:"), self)
        self.descLabel = QLabel(
            self.tr("自动拾取路过的声骸、草药、食材、宝箱。任意分辨率"),
            self
        )
        self.descLabel.setWordWrap(True)

        self.descLayout = QHBoxLayout(self)
        self.descLayout.addWidget(self.descLabel)
        self.descLayout.setContentsMargins(30, 0, 0, 0)

        self.mainLayout.addWidget(self.checkbox)
        self.mainLayout.addLayout(self.descLayout)


class ExploreWidget(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.container = QWidget(self)
        self.mainLayout = QVBoxLayout(self.container)

        self.tipsLabel = QLabel(self.tr("战斗、跑图都需手动操作，不能代肝大世界！"), self.container)
        self.tipsLabel.setWordWrap(True)

        self.autopickWidget = AutoPickupWidget(self.container)
        self.autopickWidget.checkbox.setChecked(True)

        self.group = QButtonGroup(self.container)
        self.group.setExclusive(True)
        self.group.addButton(self.autopickWidget.checkbox)

        self.__initWidget()

        self.currentTask = self.autopickWidget.task

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
        self.mainLayout.addWidget(self.autopickWidget)
        self.mainLayout.addStretch()
        self.mainLayout.setSpacing(20)
        self.mainLayout.setContentsMargins(16, 26, 16, 10)

    def __connectSignalToSlot(self):
        self.autopickWidget.checkbox.stateChanged.connect(
            lambda _: self.__onTaskChecked(self.autopickWidget.checkbox, self.autopickWidget.task))

    def __onTaskChecked(self, checkbox, currentTask):
        # logger.debug(f"echo __onTaskChecked: {checkbox.isChecked()}")
        if checkbox.isChecked():
            self.currentTask = currentTask
            globalSignal.taskChangedSignal.emit(currentTask)
            # logger.debug(f"Current task: {self.currentTask}")
