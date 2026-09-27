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
        self.firstEnemy = ""
        self.enemyGroup = QButtonGroup(self)
        self.enemyGroup.setExclusive(True)

        self.toolbarLayout = QHBoxLayout()
        self.bossNameLabel = QLabel(self.tr("BOSS:"), self)
        self.lineEdit = SearchLineEdit(self)
        self.lineEdit.setEnabled(False)
        self.aboutButton = PushButton(self.tr("关于"), self)

        # for boss in BossNameEnum:
        new_boss = 1  # TODO 增加boss参数，根据版本区最新版本boss数量
        for i, boss in enumerate(reversed(list(BossNameEnum))):
            if i == 0:
                self.firstEnemy = boss
            checkCard = CheckCard(boss.value, parent=self)
            checkCard.setChecked(False)
            if i < new_boss or boss == BossNameEnum.NightmareMourningAix:
                checkCard.setBackground()
            self.checkCards[boss] = checkCard
            checkCard.setProperty("boss", boss)
            self.enemyGroup.addButton(checkCard.checkbox)

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

        self.aboutButton.clicked.connect(self.__showAboutFlyout)

    def __loadConfig(self):
        value = paramConfig.get(paramConfig.bossName)
        # logger.warning(f"{value}")
        if value and len(value) > 0:
            card = self.checkCards.get(value[0])
            if len(value) > 1:
                card.setChecked(True)
            else:
                card.blockSignals(True)
                card.setChecked(True)
                card.blockSignals(False)
        else:
            card = self.checkCards.get(BossNameEnum.Dreamless)
            card.setChecked(True)

    def __on_card_state_changed(self, cb, state):
        logger.debug(f"checkbox: {cb.checkbox.text()}, isChecked: {cb.checkbox.isChecked()}")
        paramConfig.set(paramConfig.bossName, [cb.property("boss")])

    def __showAboutFlyout(self):
        Flyout.create(
            # icon=InfoBarIcon.INFORMATION,
            title='关于:',
            content=self.tr(
                '任意配队，人数不限，建议带奶，建议1280x720最低画质挂机还省电。'
                '\n若游戏内没有1280x720分辨率选项，或修改后游戏微闪一下没有反应，这是游戏的问题，换成其他修改后有效的小分辨率，如1600x900。'
                '\n萌新建议降低索拉等级刷梦魇boss，通过5合1获取1c3c。'
            ),
            target=self.aboutButton,
            parent=self.window()
        )

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.flowLayout.invalidate()
        self.flowLayout.activate()


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
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
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
