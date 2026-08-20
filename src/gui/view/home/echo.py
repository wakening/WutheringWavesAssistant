import logging

from PySide6.QtCore import Qt, Signal, QSize, QEvent, QCoreApplication
from PySide6.QtGui import QIcon, QColor, QIntValidator
from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout,
                               QPushButton, QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout)
from qfluentwidgets import (FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
                            InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
                            SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
                            OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
                            SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
                            LineEdit, SettingCard, ComboBox, ConfigItem,
                            PushButton, ToolButton, MessageBox, SearchLineEdit, TransparentPushButton, ToggleToolButton,
                            DropDownPushButton, TogglePushButton)

from src.gui.common.config import paramConfig, BossNameEnum
from src.gui.common.globals import globalParam, globalSignal
from src.gui.common.style_sheet import StyleSheet
from src.gui.common.task import BaseTask, ValidationResult, TaskId
from src.gui.components.check_box import CheckCard

logger = logging.getLogger(__name__)


class EchoTask(BaseTask):

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


class BossRushTask(EchoTask):

    def __init__(self, widget):
        super().__init__(TaskId.AutoBossProcessTask, "BossRush", widget)

    def validate(self, **kwargs) -> ValidationResult:
        context = self.__class__.__name__
        try:
            # logger.debug(f"paramConfig: {paramConfig.toDict}")
            if not paramConfig.bossName.value:
                return ValidationResult(
                    success=False,
                    message=QCoreApplication.translate(context, "未选择boss")
                )
            return ValidationResult(success=True)
        except Exception as e:
            logger.error(e)
        return ValidationResult(
            success=False,
            message=QCoreApplication.translate(context, "参数异常")
        )

    def submitTask(self, start: bool):
        if start:
            result = self.validate()
            if result.success:
                msg = str([x.value for x in paramConfig.bossName.value])
                self._createTopRightInfoBar(self.tr('Boss Rush: '), msg, 5000)
                self.submit(start)
            return result
        self.submit(start)
        return None


class BossRushWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.task = BossRushTask(self)

        self.mainLayout = QVBoxLayout(self)

        self.flowLayout = FlowLayout(isTight=True)
        self.checkCards: dict[BossNameEnum, CheckCard] = {}
        self.selectedBosses: dict[BossNameEnum, bool] = {}

        self.toolbarLayout = QHBoxLayout()
        self.bossNameLabel = QLabel(self.tr("BOSS:"), self)
        self.lineEdit = SearchLineEdit(self)
        self.lineEdit.setEnabled(False)
        self.multipleSelectButton = TogglePushButton(self.tr("多选"), self)
        self.multipleSelectButton.setCheckable(True)
        self.multipleSelectButton.setChecked(False)
        self.aboutButton = PushButton(self.tr("关于"), self)

        # for boss in BossNameEnum:
        new_boss = 1  # TODO 增加boss参数，根据版本区最新版本boss数量
        for i, boss in enumerate(reversed(list(BossNameEnum))):
            checkCard = CheckCard(boss.value, parent=self)
            if i < new_boss or boss == BossNameEnum.NightmareMourningAix:
                checkCard.setBackground()
            self.checkCards[boss] = checkCard
            checkCard.setProperty("boss", boss)

        self.__initWidget()

    def __initWidget(self):
        # initialize style sheet
        self.setObjectName('view')
        # StyleSheet.PARAM_INTERFACE.apply(self)

        self.lineEdit.setMaximumWidth(300)
        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.setPlaceholderText('施工中...')

        for boss, card in self.checkCards.items():
            self.flowLayout.addWidget(card)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        self.flowLayout.setSpacing(0)
        self.flowLayout.setContentsMargins(0, 10, 0, 10)

        self.toolbarLayout.addWidget(self.bossNameLabel)
        self.toolbarLayout.addWidget(self.lineEdit)
        self.toolbarLayout.addWidget(self.multipleSelectButton)
        self.toolbarLayout.addWidget(self.aboutButton)
        self.toolbarLayout.setSpacing(8)
        self.toolbarLayout.addStretch()

        self.mainLayout.addLayout(self.toolbarLayout)
        self.mainLayout.addLayout(self.flowLayout)
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(16, 10, 16, 10)

    def __connectSignalToSlot(self):
        for boss, card in self.checkCards.items():
            card.stateChanged.connect(lambda state, cb=card: self.__on_card_state_changed(cb, state))

        self.multipleSelectButton.toggled.connect(self.__on_multiple_select_button_toggled)
        self.aboutButton.clicked.connect(self.__showAboutFlyout)

    def __loadConfig(self):
        self.setValue(paramConfig.get(paramConfig.bossName))

    def __on_card_state_changed(self, cb, state):
        logger.debug(f"checkbox: {cb.checkbox.text()}, isChecked: {cb.checkbox.isChecked()}")
        if self.multipleSelectButton.isChecked():
            for boss, card in self.checkCards.items():
                if card.isChecked():
                    self.selectedBosses[boss] = True
                else:
                    self.selectedBosses.pop(boss, None)
        else:
            for selectBoss, _ in self.selectedBosses.items():
                card = self.checkCards.get(selectBoss)
                if card != cb:
                    card.blockSignals(True)
                    card.setChecked(False)
                    card.blockSignals(False)
            self.selectedBosses.clear()
            if cb.isChecked():
                self.selectedBosses[cb.property("boss")] = True
        selectedBosses = list(self.selectedBosses.keys())
        # logger.debug(f"selectedBosses: {selectedBosses}")
        paramConfig.set(paramConfig.bossName, selectedBosses)

    def __on_multiple_select_button_toggled(self):
        if self.multipleSelectButton.isChecked():
            return
        if len(self.selectedBosses) > 1:
            self.__on_deselect_all_button_clicked()

    def __on_deselect_all_button_clicked(self):
        for boss, card in self.checkCards.items():
            card.blockSignals(True)
            card.setChecked(False)
            card.blockSignals(False)
        self.selectedBosses.clear()
        paramConfig.set(paramConfig.bossName, [])

    def __showAboutFlyout(self):
        Flyout.create(
            # icon=InfoBarIcon.INFORMATION,
            title='关于:',
            content=self.tr(
                '任意配队，人数不限，建议带奶，建议1280x720最低画质挂机还省电。'
                '\n若游戏内没有1280x720分辨率选项，或修改后游戏微闪一下没有反应，这是游戏的问题，换成其他修改后有效的小分辨率，如1600x900。'
                '\n日常可刷梦魇哀声鸷，通过合成获取1c3c。不建议多选。'
                '\n萌新建议降低索拉等级刷。'
            ),
            target=self.aboutButton,
            parent=self.window()
        )

    def setValue(self, value):
        # logger.warning(f"{value}")
        if value is None:
            value = []
        self.selectedBosses.clear()
        for boss, card in self.checkCards.items():
            card.blockSignals(True)
            card.setChecked(boss in value)
            card.blockSignals(False)
        for v in value:
            self.selectedBosses[v] = True
        if len(value) > 1:
            self.multipleSelectButton.blockSignals(True)
            self.multipleSelectButton.setChecked(True)
            self.multipleSelectButton.blockSignals(False)


class EchoMergeTask(EchoTask):

    def __init__(self, widget):
        super().__init__(TaskId.EchoMergeProcessTask, "EchoMerge", widget)


class EchoMergeWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.task = EchoMergeTask(self)

        self.mainLayout = QVBoxLayout(self)

        # self.checkbox = CheckBox(self.tr("声骸融合: "), self)
        self.descLabel = QLabel(self.tr("融合背包内未锁定的声骸，任意分辨率"), self)
        self.descLabel.setWordWrap(True)

        self.descLayout = QHBoxLayout(self)
        self.descLayout.addWidget(self.descLabel)
        self.descLayout.setContentsMargins(16, 0, 0, 0)

        # self.mainLayout.addWidget(self.checkbox)
        self.mainLayout.addLayout(self.descLayout)


class EchoWidget(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.container = QWidget(self)
        self.mainLayout = QVBoxLayout(self.container)

        self.tipsLabel = QLabel(self.tr("请勾选需要的功能项"), self.container)

        self.bossRushCheckBox = CheckBox(self.tr("刷BOSS:"), self.container)
        self.bossRushCheckBox.setChecked(True)
        self.bossRushWidget = BossRushWidget(self.container)

        self.echoMergeCheckBox = CheckBox(self.tr("声骸融合:"), self.container)
        self.echoMergeWidget = EchoMergeWidget(self.container)

        self.group = QButtonGroup(self.container)
        self.group.setExclusive(True)
        self.group.addButton(self.bossRushCheckBox)
        self.group.addButton(self.echoMergeCheckBox)

        self.__initWidget()

        self.currentTask = self.bossRushWidget.task

    def __initWidget(self):
        # self.resize(1000, 800)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        # self.setObjectName('paramInterface')

        # initialize style sheet
        self.bossRushCheckBox.setObjectName("titleCheckBox")
        self.echoMergeCheckBox.setObjectName("titleCheckBox")
        self.container.setObjectName('view')
        StyleSheet.HOME_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        self.mainLayout.addWidget(self.tipsLabel)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addWidget(self.bossRushCheckBox)
        self.mainLayout.addWidget(self.bossRushWidget)
        self.mainLayout.addWidget(self.echoMergeCheckBox)
        self.mainLayout.addWidget(self.echoMergeWidget)
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(16, 10, 16, 10)

    def __connectSignalToSlot(self):
        self.bossRushCheckBox.stateChanged.connect(
            lambda _: self.__onTaskChecked(self.bossRushCheckBox, self.bossRushWidget.task))
        self.echoMergeCheckBox.stateChanged.connect(
            lambda _: self.__onTaskChecked(self.echoMergeCheckBox, self.echoMergeWidget.task))

    def __onTaskChecked(self, checkbox, currentTask):
        # logger.debug(f"echo __onTaskChecked: {checkbox.isChecked()}, {currentTask}")
        if checkbox.isChecked():
            self.currentTask = currentTask
            globalSignal.taskChangedSignal.emit(currentTask)
            # logger.debug(f"Current task: {self.currentTask}")

    def __loadConfig(self):
        pass
