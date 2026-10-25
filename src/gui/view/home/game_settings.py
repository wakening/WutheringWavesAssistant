import logging

from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QIcon, QColor, QIntValidator, QShortcut, QKeySequence
from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout,
                               QPushButton, QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout)
from qfluentwidgets import (FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
                            InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
                            SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
                            OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
                            SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
                            LineEdit, SettingCard, ComboBox, ConfigItem,
                            PushButton, ToolButton, MessageBox, CardWidget, SimpleCardWidget, BodyLabel, TitleLabel,
                            PillPushButton, TransparentDropDownPushButton, TransparentTogglePushButton)

from src.gui.common.config import paramConfig
from src.gui.common.globals import globalParam, globalSignal
from src.gui.common.style_sheet import StyleSheet
from src.gui.common.task import TaskId, BaseTask, ValidationResult
from src.gui.components.my_shortcut_picker import MyShortcutPicker

logger = logging.getLogger(__name__)


class ShortcutWidget(MyShortcutPicker):

    def __init__(self, keySequence='Ctrl+Shift+A', text='', dialogTitle='', parent=None):
        super().__init__(keySequence, text, parent)
        if dialogTitle:
            self.setDialogTitle(dialogTitle)
        self.setDialogDescription(self.tr('按下按键或组合键以更改此快捷键'))

    def loadKeySequence(self, keySequence):
        if not keySequence:
            return
        self.blockSignals(True)
        self.setKeySequence(keySequence)
        self.blockSignals(False)

class GameSettingsWidget(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.container = QWidget(self)
        self.mainLayout = QVBoxLayout(self.container)

        self.tipsLabel = QLabel(self.tr("Game Settings"), self.container)
        self.tipsLabel2 = QLabel(self.tr("点击按键进行修改，请保持与游戏内一致"), self.container)

        # Game Settings
        # Sounds
        # Volume
        # Installation Directory
        # Open game directory
        # Mute when Game is in the Background
        # Keyboard and Mouse
        # Combat and Exploration

        # Controls
        self.gridLayout = QGridLayout()

        self.movementLabel = QLabel(self.tr('Movement:'), self.container)
        self.movementLayout = FlowLayout(isTight=True)
        self.moveForwardWidget = ShortcutWidget('W', self.tr('Move forward:'), self.tr('Move forward'), self.container)
        self.moveBackwardWidget = ShortcutWidget('A', self.tr('Move backward:'), self.tr('Move backward'), self.container)
        self.moveLeftWidget = ShortcutWidget('S', self.tr('Move left:'), self.tr('Move left'), self.container)
        self.moveRightWidget = ShortcutWidget('D', self.tr('Move right:'), self.tr('Move right'), self.container)

        self.skillLabel = QLabel(self.tr('Skill:'), self.container)
        self.skillLayout = FlowLayout(isTight=True)
        self.resonanceSkillWidget = ShortcutWidget('E', self.tr('Resonance Skill:'), self.tr('Resonance Skill'), self.container)
        self.echoSkillWidget = ShortcutWidget('Q', self.tr('Echo Skill:'), self.tr('Echo Skill'), self.container)
        self.resonanceLiberationWidget = ShortcutWidget('R', self.tr('Resonance Liberation:'), self.tr('Resonance Liberation'), self.container)

        self.memberSwitchLabel = QLabel(self.tr('Member:'), self.container)
        self.memberSwitchLayout = FlowLayout(isTight=True)
        self.member1Widget = ShortcutWidget('1', self.tr('Member 1:'), self.tr('Switch to Team Member 1'), self.container)
        self.member2Widget = ShortcutWidget('2', self.tr('Member 2:'), self.tr('Switch to Team Member 2'), self.container)
        self.member3Widget = ShortcutWidget('3', self.tr('Member 3:'), self.tr('Switch to Team Member 3'), self.container)
        self.member4Widget = ShortcutWidget('4', self.tr('Member 4:'), self.tr('Switch to Team Member 4'), self.container)

        self.otherLabel = QLabel(self.tr('Other:'), self.container)
        self.otherLayout = FlowLayout(isTight=True)
        self.jumpWidget = ShortcutWidget('Space', self.tr('Jump:'), self.tr('Jump'), self.container)
        self.pickUpWidget = ShortcutWidget('F', self.tr('Pick Up/Interact:'), self.tr('Pick Up/Interact'), self.container)
        self.useUtilityWidget = ShortcutWidget('T', self.tr('Use Utility:'), self.tr('Use Utility'), self.container)
        self.mapWidget = ShortcutWidget('M', self.tr('Map:'), self.tr('Map'), self.container)

        # self.shortcutWidgets5 = [
        #     ShortcutWidget(Qt.Key_Control, self.tr('Walk/Run (Toggle):'), self.tr('Walk/Run (Toggle))),
        #     ShortcutWidget('LeftButton', self.tr('Normal Attack:'), self.tr('Normal Attack)),
        #     ShortcutWidget('Shift', self.tr('Dash/Dodge:'), self.tr('Dash/Dodge)),
        #     ShortcutWidget('RightButton', self.tr('Dash/Dodge:'), self.tr('Dash/Dodge)),
        #     ShortcutWidget('X', self.tr('Drop Down when Climbing:'), self.tr('Drop Down when Climbing)),
        #
        #     ShortcutWidget('Tab', self.tr('Utility Wheel:'), self.tr('Utility Wheel)),
        #     ShortcutWidget('G', self.tr('Switch to Aim Mode:'), self.tr('Switch to Aim Mode)),
        #
        #     ShortcutWidget('V', self.tr('Track Quest:'), self.tr('Track Quest)),
        #     ShortcutWidget('P', self.tr('Quit Challenge:'), self.tr('Quit Challenge)),
        #     ShortcutWidget('N', self.tr('Mail:'), self.tr('Mail)),
        #
        #     ShortcutWidget('J', self.tr('Quests:'), self.tr('Quests)),
        #     ShortcutWidget('Esc', self.tr('Terminal:'), self.tr('Terminal)),
        #     ShortcutWidget('L', self.tr('Team:'), self.tr('Team)),
        #     ShortcutWidget('B', self.tr('Backpack:'), self.tr('Backpack)),
        #     ShortcutWidget('C', self.tr('Resonator:'), self.tr('Resonator)),
        #     ShortcutWidget('O', self.tr('Utilities:'), self.tr('Utilities)),
        #     ShortcutWidget('H', self.tr('Tutorial:'), self.tr('Tutorial)),
        # ]

        self.resetButton = PushButton(self.tr('Reset Keyboard'), self.container)

        self.__initWidget()

        self.currentTask = None

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
        self.__loadConfig()

    def __initLayout(self):
        # self.setStyleSheet("border: 2px solid red;")

        self.movementLayout.addWidget(self.moveForwardWidget)
        self.movementLayout.addWidget(self.moveBackwardWidget)
        self.movementLayout.addWidget(self.moveLeftWidget)
        self.movementLayout.addWidget(self.moveRightWidget)
        self.movementLayout.setContentsMargins(6, 0, 0, 0)

        self.skillLayout.addWidget(self.resonanceSkillWidget)
        self.skillLayout.addWidget(self.echoSkillWidget)
        self.skillLayout.addWidget(self.resonanceLiberationWidget)
        self.skillLayout.setContentsMargins(6, 0, 0, 0)

        self.memberSwitchLayout.addWidget(self.member1Widget)
        self.memberSwitchLayout.addWidget(self.member2Widget)
        self.memberSwitchLayout.addWidget(self.member3Widget)
        self.memberSwitchLayout.addWidget(self.member4Widget)
        self.memberSwitchLayout.setContentsMargins(6, 0, 0, 0)

        self.otherLayout.addWidget(self.jumpWidget)
        self.otherLayout.addWidget(self.pickUpWidget)
        self.otherLayout.addWidget(self.useUtilityWidget)
        self.otherLayout.addWidget(self.mapWidget)
        self.otherLayout.setContentsMargins(6, 0, 0, 0)

        row = 0
        self.gridLayout.addWidget(self.movementLabel, row, 0, Qt.AlignVCenter | Qt.AlignLeft)
        self.gridLayout.addLayout(self.movementLayout, row, 1)

        row += 1
        self.gridLayout.addWidget(self.skillLabel, row, 0, Qt.AlignVCenter | Qt.AlignLeft)
        self.gridLayout.addLayout(self.skillLayout, row, 1)

        row += 1
        self.gridLayout.addWidget(self.memberSwitchLabel, row, 0, Qt.AlignVCenter | Qt.AlignLeft)
        self.gridLayout.addLayout(self.memberSwitchLayout, row, 1)

        row += 1
        self.gridLayout.addWidget(self.otherLabel, row, 0, Qt.AlignVCenter | Qt.AlignLeft)
        self.gridLayout.addLayout(self.otherLayout, row, 1)

        self.gridLayout.setColumnStretch(0, 0)
        self.gridLayout.setColumnStretch(1, 1)

        self.resetButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.mainLayout.addWidget(self.tipsLabel)
        self.mainLayout.addWidget(self.tipsLabel2)
        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addWidget(self.resetButton)
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(16, 26, 16, 10)
        # self.mainLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def __connectSignalToSlot(self):
        self.moveForwardWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.moveForwardWidget, paramConfig.shortcutMoveForward))
        self.moveBackwardWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.moveBackwardWidget, paramConfig.shortcutMoveBackward))
        self.moveLeftWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.moveLeftWidget, paramConfig.shortcutMoveLeft))
        self.moveRightWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.moveRightWidget, paramConfig.shortcutMoveRight))
        self.resonanceSkillWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.resonanceSkillWidget, paramConfig.shortcutResonanceSkill))
        self.echoSkillWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.echoSkillWidget, paramConfig.shortcutEchoSkill))
        self.resonanceLiberationWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.resonanceLiberationWidget, paramConfig.shortcutResonanceLiberation))
        self.member1Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.member1Widget, paramConfig.shortcutMember1))
        self.member2Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.member2Widget, paramConfig.shortcutMember2))
        self.member3Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.member3Widget, paramConfig.shortcutMember3))
        self.member4Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.member4Widget, paramConfig.shortcutMember4))
        self.jumpWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.jumpWidget, paramConfig.shortcutJump))
        self.pickUpWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.pickUpWidget, paramConfig.shortcutPickUp))
        self.useUtilityWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.useUtilityWidget, paramConfig.shortcutUseUtility))
        self.mapWidget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.mapWidget, paramConfig.shortcutMap))

        self.resetButton.clicked.connect(self.__showResetDialog)

    def __loadConfig(self):
        self.moveForwardWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutMoveForward))
        self.moveBackwardWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutMoveBackward))
        self.moveLeftWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutMoveLeft))
        self.moveRightWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutMoveRight))
        self.resonanceSkillWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutResonanceSkill))
        self.echoSkillWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutEchoSkill))
        self.resonanceLiberationWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutResonanceLiberation))
        self.member1Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutMember1))
        self.member2Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutMember2))
        self.member3Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutMember3))
        self.member4Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutMember4))
        self.jumpWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutJump))
        self.pickUpWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutPickUp))
        self.useUtilityWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutUseUtility))
        self.mapWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutMap))

    def __showResetDialog(self):
        title = self.tr('Note')
        content = self.tr('Are you sure you want to reset the key bindings to defaults?')
        w = MessageBox(title, content, self.window())
        # w.setTitleBarVisible(False)
        # w.setContentCopyable(True)
        if not w.exec():
            return

        self.moveForwardWidget.reset()
        self.moveBackwardWidget.reset()
        self.moveLeftWidget.reset()
        self.moveRightWidget.reset()
        self.resonanceSkillWidget.reset()
        self.echoSkillWidget.reset()
        self.resonanceLiberationWidget.reset()
        self.member1Widget.reset()
        self.member2Widget.reset()
        self.member3Widget.reset()
        self.member4Widget.reset()
        self.jumpWidget.reset()
        self.pickUpWidget.reset()
        self.useUtilityWidget.reset()
        self.mapWidget.reset()

    def __onKeySequenceChanged(self, keySequence: QKeySequence, shortcutWidget: ShortcutWidget, item):
        keyStr = keySequence.toString(QKeySequence.SequenceFormat.PortableText)
        logger.info(f"{shortcutWidget.textLabel.text()} '{keyStr}'")
        if shortcutWidget.defaultKeySequence() == shortcutWidget.keySequence():
            paramConfig.set(item, None)
        else:
            paramConfig.set(item, keyStr)

    def __onTaskChecked(self, checkbox, currentTask):
        # logger.debug(f"echo __onTaskChecked: {checkbox.isChecked()}")
        if checkbox.isChecked():
            self.currentTask = currentTask
            globalSignal.taskChangedSignal.emit(currentTask)
            # logger.debug(f"Current task: {self.currentTask}")
