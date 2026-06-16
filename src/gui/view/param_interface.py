# coding:utf-8
import logging
from typing import Union, List

from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QIcon, QColor, QIntValidator
from PySide6.QtWidgets import QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout, QPushButton, \
    QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout
from qfluentwidgets import FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition, \
    InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit
from qfluentwidgets import InfoBar
from qfluentwidgets import (SettingCardGroup, ScrollArea,
                            ExpandLayout, ExpandSettingCard, FluentIconBase,
                            OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
                            SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
                            LineEdit, SettingCard, ComboBox, ConfigItem,
                            PushButton, ToolButton, MessageBox)

from src.gui.common.config import paramConfig, BossNameEnum
from src.gui.common.globals import globalParam, globalSignal
from src.gui.common.style_sheet import StyleSheet
from src.gui.components.my_expand_setting_card import FlowExpandSettingCard

logger = logging.getLogger(__name__)


class TimeLineEdit(LineEdit):
    """ Color line edit """

    def __init__(self, minimum, maximum: int, parent=None):
        super().__init__(parent)
        # self.setText(str(value))
        self.setFixedSize(136, 33)
        self.setClearButtonEnabled(True)
        self.setValidator(QIntValidator(minimum, maximum, self))


class TimeDialog(MaskDialogBase):
    """ Color dialog """

    valueChanged = Signal(list)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.scrollArea = SingleDirectionScrollArea(self.widget)
        self.scrollWidget = QWidget(self.scrollArea)

        self.buttonGroup = QFrame(self.widget)
        self.yesButton = PrimaryPushButton(self.tr('OK'), self.buttonGroup)
        self.cancelButton = QPushButton(self.tr('Cancel'), self.buttonGroup)

        self.titleLabel = QLabel(title, self.scrollWidget)

        self.redLabel = QLabel(self.tr('时'), self.scrollWidget)
        self.greenLabel = QLabel(self.tr('分'), self.scrollWidget)
        self.blueLabel = QLabel(self.tr('秒'), self.scrollWidget)
        self.redLineEdit = TimeLineEdit(0, 999, self.scrollWidget)
        self.greenLineEdit = TimeLineEdit(0, 999999, self.scrollWidget)
        self.blueLineEdit = TimeLineEdit(0, 999999999, self.scrollWidget)

        self.vBoxLayout = QVBoxLayout(self.widget)

        self.__initWidget()

    def __initWidget(self):
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setViewportMargins(48, 24, 0, 24)
        self.scrollArea.setWidget(self.scrollWidget)

        # self.widget.setMaximumSize(488, 696)
        # self.widget.resize(488, 696)
        # self.scrollWidget.resize(440, 560)
        self.widget.setMaximumSize(488, 296 + 25)
        self.widget.resize(488, 296 + 25)
        self.scrollWidget.resize(440, 160 + 25)
        self.buttonGroup.setFixedSize(486, 81)
        self.yesButton.setFixedWidth(216)
        self.cancelButton.setFixedWidth(216)

        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 80))
        self.setMaskColor(QColor(0, 0, 0, 76))

        self.__setQss()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.redLineEdit.move(0, 26 + 30)
        self.greenLineEdit.move(0, 70 + 30)
        self.blueLineEdit.move(0, 115 + 30)
        self.redLabel.move(144, 34 + 30)
        self.greenLabel.move(144, 78 + 30)
        self.blueLabel.move(144, 124 + 30)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addWidget(self.buttonGroup, 0, Qt.AlignBottom)

        self.yesButton.move(24, 25)
        self.cancelButton.move(250, 25)

    def __setQss(self):
        self.titleLabel.setObjectName('titleLabel')
        self.yesButton.setObjectName('yesButton')
        self.cancelButton.setObjectName('cancelButton')
        self.buttonGroup.setObjectName('buttonGroup')
        FluentStyleSheet.COLOR_DIALOG.apply(self)
        self.titleLabel.adjustSize()

    def __onYesButtonClicked(self):
        """ yes button clicked slot """
        try:
            hours = int(self.redLineEdit.text().strip())
        except ValueError:
            hours = 0
        try:
            minutes = int(self.greenLineEdit.text().strip())
        except ValueError:
            minutes = 0
        try:
            seconds = int(self.blueLineEdit.text().strip())
        except ValueError:
            seconds = 0
        if hours * 3600 + minutes * 60 + seconds >= 60:
            self.accept()
            self.valueChanged.emit([hours, minutes, seconds])
        else:
            logger.warning("定时重启游戏时间不可小于60秒")

    def updateStyle(self):
        """ update style sheet """
        self.setStyle(QApplication.style())
        self.titleLabel.adjustSize()
        self.redLabel.adjustSize()
        self.greenLabel.adjustSize()
        self.blueLabel.adjustSize()

    def showEvent(self, e):
        self.updateStyle()
        super().showEvent(e)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        self.cancelButton.clicked.connect(self.reject)
        self.yesButton.clicked.connect(self.__onYesButtonClicked)


class AutoRestartPeriodSettingCard(ExpandGroupSettingCard):
    """ Custom Value setting card """

    autoRestartPeriodChanged = Signal(int)

    def __init__(self, configItem: ConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent=parent)
        # self.enableAlpha = enableAlpha
        self.configItem = configItem
        self.defaultValue = configItem.defaultValue
        self.customValue = paramConfig.get(configItem)
        self.customValueLast = None if self.customValue == self.defaultValue else self.customValue

        self.choiceLabel = QLabel(self)
        # self.choiceLabel.setStyleSheet("""
        #     background-color: lightblue;  /* 背景颜色 */
        #     border-radius: 1px;           /* 可选，圆角边框 */
        # """)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.defaultRadioButton = RadioButton(
            self.tr('默认关闭'), self.radioWidget)
        # self.tr('Default Close'), self.radioWidget)
        self.customRadioButton = RadioButton(
            self.tr('自定义时间'), self.radioWidget)
        # self.tr('Custom Time'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self)

        self.customValueWidget = QWidget(self.view)
        self.customValueLayout = QHBoxLayout(self.customValueWidget)
        self.customLabel = QLabel(
            self.tr('自定义时间'), self.customValueWidget)
        self.chooseTimeButton = QPushButton(
            self.tr('设置时间'), self.customValueWidget)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        if self.defaultValue != self.customValue:
            self.customRadioButton.setChecked(True)
            self.chooseTimeButton.setEnabled(True)
            self._updateChoiceLabel(self.customValue)
        else:
            self.defaultRadioButton.setChecked(True)
            self.chooseTimeButton.setEnabled(False)
            self._updateChoiceLabel(self.defaultValue)

        # self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
        self.choiceLabel.adjustSize()

        self.choiceLabel.setObjectName("titleLabel")
        self.customLabel.setObjectName("titleLabel")
        self.chooseTimeButton.setObjectName('chooseTimeButton')

        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)
        self.chooseTimeButton.clicked.connect(self.__showChooseTimeDialog)

    def __initLayout(self):
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignTop)
        self.radioLayout.setContentsMargins(48, 18, 0, 18)
        self.buttonGroup.addButton(self.customRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.customValueLayout.setContentsMargins(48, 18, 44, 18)
        self.customValueLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        self.customValueLayout.addWidget(self.chooseTimeButton, 0, Qt.AlignRight)
        self.customValueLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customValueWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """ radio button clicked slot """
        # if button.text() == self.choiceLabel.text():
        #     return

        # self.choiceLabel.setText(button.text())
        # self.choiceLabel.adjustSize()

        if button is self.defaultRadioButton:
            if self.choiceLabel.text() != button.text():
                self.choiceLabel.setText(button.text())
                self.choiceLabel.adjustSize()  # 此处设置相同的值label文本会置顶bug
            self.chooseTimeButton.setDisabled(True)
            paramConfig.set(self.configItem, self.defaultValue)
            if self.defaultValue != self.customValue:
                self.autoRestartPeriodChanged.emit(self.defaultValue)
        else:
            if self.customValueLast is not None:
                self.customValue = self.customValueLast
                self._updateChoiceLabel(self.customValue)
            self.chooseTimeButton.setDisabled(False)
            paramConfig.set(self.configItem, self.customValue)
            if self.defaultValue != self.customValue:
                self.autoRestartPeriodChanged.emit(self.customValue)

    def __showChooseTimeDialog(self):
        """ show color dialog """
        w = TimeDialog(self.tr('设置时间'), self.window())
        w.valueChanged.connect(self.__onCustomValueChanged)
        w.exec()

    def _updateChoiceLabel(self, value):
        if not value or value == self.defaultValue:
            self.choiceLabel.setText(self.defaultRadioButton.text())
        else:
            restartPeriod = value.split("#")
            template = self.tr("Restart every {hours} hours, {minutes} minutes, and {seconds} seconds")
            text = template.format(hours=restartPeriod[0], minutes=restartPeriod[1], seconds=restartPeriod[2])
            logger.debug(text)
            self.choiceLabel.setText(text)
        self.choiceLabel.adjustSize()

    def __onCustomValueChanged(self, value: list[int]):
        """ custom color changed slot """
        if not value:
            return
        strValue = "#".join(map(str, value))
        paramConfig.set(self.configItem, strValue)
        self.customValue = strValue
        self.customValueLast = strValue
        self._updateChoiceLabel(strValue)
        self.autoRestartPeriodChanged.emit(strValue)


class AutoCombatSwitchSettingCard(SettingCard):
    """ Setting card with switch button """

    checkedChanged = Signal(bool)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None,
                 configItem: ConfigItem = None, parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        configItem: ConfigItem
            configuration item operated by the card

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.switchButton = SwitchButton(self, IndicatorPosition.RIGHT)

        if configItem:
            self.setValue(paramConfig.get(configItem))
            configItem.valueChanged.connect(self.setValue)

        # add switch button to layout
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def __onCheckedChanged(self, isChecked: bool):
        """ switch button checked state changed slot """
        self.setValue(isChecked)
        self.checkedChanged.emit(isChecked)

    def setValue(self, isChecked: bool):
        if self.configItem:
            paramConfig.set(self.configItem, isChecked)

        self.switchButton.setChecked(isChecked)
        self.switchButton.setText(
            self.tr('On') if isChecked else self.tr('Off'))

    def setChecked(self, isChecked: bool):
        self.setValue(isChecked)

    def isChecked(self):
        return self.switchButton.isChecked()


class ComboSequenceDialog(MaskDialogBase):
    valueChanged = Signal(list)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self.widget)

        self.titleLabel = QLabel(title, self.widget)
        self.contentLabel = QLabel(
            "逗号分隔, e,q,r为技能, l(小写L)为向后闪避, a为普攻(默认连点0.3秒), 数字为间隔时间,a~0.5为普攻按下0.5秒,a(0.5)为连续普攻0.5秒，摩托车短按请用q~0.1",
            self.widget)

        self.comboNameGroup = QHBoxLayout(self.widget)
        self.comboNameLabel = QLabel(self.tr('备注: '), self.widget)
        self.comboNameLineEdit = LineEdit(self.widget)

        self.comboSeqGroup = QHBoxLayout(self.widget)
        self.comboSeqLabel = QLabel(self.tr('连招: '), self.widget)
        self.comboSeqLineEdit = LineEdit(self.widget)

        self.buttonGroup = QFrame(self.widget)
        self.yesButton = PrimaryPushButton(self.tr('OK'), self.buttonGroup)
        self.cancelButton = QPushButton(self.tr('Cancel'), self.buttonGroup)

        self.__initWidget()

    def __initWidget(self):
        self.__setQss()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.comboNameGroup.addWidget(self.comboNameLabel)
        self.comboNameGroup.addWidget(self.comboNameLineEdit)
        self.comboSeqGroup.addWidget(self.comboSeqLabel)
        self.comboSeqGroup.addWidget(self.comboSeqLineEdit)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addLayout(self.comboNameGroup)
        self.vBoxLayout.addLayout(self.comboSeqGroup)
        self.vBoxLayout.addWidget(self.buttonGroup, Qt.AlignBottom)

    def __setQss(self):
        # self.editLabel.setObjectName('editLabel')
        self.titleLabel.setObjectName('titleLabel')
        self.yesButton.setObjectName('yesButton')
        self.cancelButton.setObjectName('cancelButton')
        self.buttonGroup.setObjectName('buttonGroup')

    def __onYesButtonClicked(self):
        """ yes button clicked slot """
        pass

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        self.cancelButton.clicked.connect(self.reject)
        self.yesButton.clicked.connect(self.__onYesButtonClicked)


class ComboSequenceSettingCard(ExpandGroupSettingCard):
    """ Custom Value setting card """

    autoRestartPeriodChanged = Signal(int)

    def __init__(self, configItem: ConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent=parent)
        # self.enableAlpha = enableAlpha
        self.configItem = configItem
        self.defaultValue = configItem.defaultValue
        self.customValue = paramConfig.get(configItem)
        self.customValueLast = None if self.customValue == self.defaultValue else self.customValue

        self.choiceLabel = QLabel(self)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.defaultRadioButton = RadioButton(
            self.tr('默认'), self.radioWidget)
        # self.tr('Default Close'), self.radioWidget)
        self.customRadioButton = RadioButton(
            self.tr('自定义连招'), self.radioWidget)
        # self.tr('Custom Time'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self)

        self.customValueWidget = QWidget(self.view)
        self.customValueLayout = QHBoxLayout(self.customValueWidget)
        self.customLabel = QLabel(
            self.tr('自定义连招'), self.customValueWidget)
        self.chooseTimeButton = QPushButton(
            self.tr('设置连招'), self.customValueWidget)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        if self.defaultValue != self.customValue:
            self.customRadioButton.setChecked(True)
            self.chooseTimeButton.setEnabled(True)
            self._updateChoiceLabel(self.customValue)
        else:
            self.defaultRadioButton.setChecked(True)
            self.chooseTimeButton.setEnabled(False)
            self._updateChoiceLabel(self.defaultValue)

        # self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
        self.choiceLabel.adjustSize()

        self.choiceLabel.setObjectName("titleLabel")
        self.customLabel.setObjectName("titleLabel")
        self.chooseTimeButton.setObjectName('chooseTimeButton')

        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)
        self.chooseTimeButton.clicked.connect(self.__showChooseTimeDialog)

    def __initLayout(self):
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignTop)
        self.radioLayout.setContentsMargins(48, 18, 0, 18)
        self.buttonGroup.addButton(self.customRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.customValueLayout.setContentsMargins(48, 18, 44, 18)
        self.customValueLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        self.customValueLayout.addWidget(self.chooseTimeButton, 0, Qt.AlignRight)
        self.customValueLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customValueWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """ radio button clicked slot """
        # if button.text() == self.choiceLabel.text():
        #     return

        # self.choiceLabel.setText(button.text())
        # self.choiceLabel.adjustSize()

        if button is self.defaultRadioButton:
            if self.choiceLabel.text() != button.text():
                self.choiceLabel.setText(button.text())
                self.choiceLabel.adjustSize()  # 此处设置相同的值label文本会置顶bug
            self.chooseTimeButton.setDisabled(True)
            paramConfig.set(self.configItem, self.defaultValue)
            if self.defaultValue != self.customValue:
                self.autoRestartPeriodChanged.emit(self.defaultValue)
        else:
            if self.customValueLast is not None:
                self.customValue = self.customValueLast
                self._updateChoiceLabel(self.customValue)
            self.chooseTimeButton.setDisabled(False)
            paramConfig.set(self.configItem, self.customValue)
            if self.defaultValue != self.customValue:
                self.autoRestartPeriodChanged.emit(self.customValue)

    def __showChooseTimeDialog(self):
        """ show color dialog """
        # w = ComboSequenceDialog(self.tr('设置连招'), self.window())
        # w.valueChanged.connect(self.__onCustomValueChanged)
        # w.exec()
        title = 'Are you sure you want to delete the folder?'
        content = """If you delete the "Music" folder from the list, the folder will no longer appear in the list, but will not be deleted."""
        # w = MessageDialog(title, content, self)   # Win10 style message box
        w = MessageBox(title, content, self)

        # close the message box when mask is clicked
        w.setClosableOnMaskClicked(True)

        w.exec()

    def _updateChoiceLabel(self, value):
        if not value or value == self.defaultValue:
            self.choiceLabel.setText(self.defaultRadioButton.text())
        else:
            restartPeriod = value.split("#")
            template = self.tr("Restart every {hours} hours, {minutes} minutes, and {seconds} seconds")
            text = template.format(hours=restartPeriod[0], minutes=restartPeriod[1], seconds=restartPeriod[2])
            logger.debug(text)
            self.choiceLabel.setText(text)
        self.choiceLabel.adjustSize()

    def __onCustomValueChanged(self, value: list[int]):
        """ custom color changed slot """
        if not value:
            return
        strValue = "#".join(map(str, value))
        paramConfig.set(self.configItem, strValue)
        self.customValue = strValue
        self.customValueLast = strValue
        self._updateChoiceLabel(strValue)
        self.autoRestartPeriodChanged.emit(strValue)


class GamePathSettingCard(ExpandGroupSettingCard):
    """ Custom Value setting card """

    gamePathChanged = Signal(int)

    def __init__(self, configItem: ConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent=parent)
        self.configItem = configItem
        self.defaultValue = configItem.defaultValue
        self.customValue = paramConfig.get(configItem)
        self.customValueLast = None if self.customValue == self.defaultValue else self.customValue

        self.choiceLabel = QLabel(self)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)

        if globalParam.gamePath:
            template = self.tr("默认自动获取。例: {gamePath}")
            gamePath = globalParam.gamePath.strip().replace("\\", "/").replace("\\\\", "/")
            gamePathText = template.format(gamePath=gamePath)
        else:
            gamePathText = self.tr("默认自动获取。当前未找到游戏路径，请手动设置")

        self.defaultRadioButton = RadioButton(gamePathText, self.radioWidget)
        # self.tr('Default Close'), self.radioWidget)
        self.customRadioButton = RadioButton(
            self.tr('自定义路径，适合多游戏，同时运行多个游戏时优先操控该路径下的游戏窗口'), self.radioWidget)
        # self.tr('Custom Time'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self)

        self.customValueWidget = QWidget(self.view)
        self.customValueLayout = QHBoxLayout(self.customValueWidget)
        self.customLabel = QLabel(
            # self.tr('自定义路径'), self.customValueWidget)
            self.tr(f"脚本优先操控运行中的游戏窗口，不管这个参数，多开或游戏没启动时才看选了哪个"), self.customValueWidget)
        # self.customLabel.setEnabled(False)
        # self.chooseTimeButton = QPushButton(
        #     self.tr('设置路径'), self.customValueWidget)
        self.chooseTimeButton = PushButton(
            self.tr(f'Add \"Wuthering Waves.exe\"'), self, FIF.FOLDER_ADD)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        if self.defaultValue != self.customValue:
            # self.customLabel.setEnabled(True)
            self.customRadioButton.setChecked(True)
            self.chooseTimeButton.setEnabled(True)
            self._updateChoiceLabel(self.customValue)
        else:
            self.defaultRadioButton.setChecked(True)
            self.chooseTimeButton.setEnabled(False)
            self._updateChoiceLabel(self.defaultValue)

        # self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
        self.choiceLabel.adjustSize()

        self.choiceLabel.setObjectName("titleLabel")
        self.customLabel.setObjectName("titleLabel")
        self.chooseTimeButton.setObjectName('chooseTimeButton')

        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)
        self.chooseTimeButton.clicked.connect(self.__showFolderDialog)

    def __initLayout(self):
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignTop)
        self.radioLayout.setContentsMargins(48, 18, 0, 18)
        self.buttonGroup.addButton(self.customRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.customValueLayout.setContentsMargins(48, 18, 44, 18)
        self.customValueLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        self.customValueLayout.addWidget(self.chooseTimeButton, 0, Qt.AlignRight)
        self.customValueLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customValueWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """ radio button clicked slot """
        # if button.text() == self.choiceLabel.text():
        #     return

        # self.choiceLabel.setText(button.text())
        # self.choiceLabel.adjustSize()

        if button is self.defaultRadioButton:
            # self.customLabel.setEnabled(False)
            if self.choiceLabel.text() != self.defaultValue:
                self.choiceLabel.setText(self.tr(self.defaultValue))
                self.choiceLabel.adjustSize()
            self.chooseTimeButton.setDisabled(True)
            paramConfig.set(self.configItem, self.defaultValue)
            if self.defaultValue != self.customValue:
                self.gamePathChanged.emit(self.defaultValue)
        else:
            # self.customLabel.setEnabled(True)
            if self.customValueLast is not None:
                self.customValue = self.customValueLast
                self._updateChoiceLabel(self.customValue)
            self.chooseTimeButton.setDisabled(False)
            paramConfig.set(self.configItem, self.customValue)
            if self.defaultValue != self.customValue:
                self.gamePathChanged.emit(self.customValue)

    # def __showChooseTimeDialog(self):
    #     """ show color dialog """
    #     w = TimeDialog(self.tr('设置时间'), self.window())
    #     w.valueChanged.connect(self.__onCustomValueChanged)
    #     w.exec()

    def __showFolderDialog(self):
        """ show folder dialog """
        # folder = QFileDialog.getExistingDirectory(
        #     self, self.tr("Choose folder"), self._dialogDirectory)
        # 打开文件对话框，选择文件
        folder, _ = QFileDialog.getOpenFileName(
            self,
            "Choose \"Wuthering Waves.exe\"",
            "./",
            "Executable Files (*.exe);;All Files (*)"  # 过滤器：只显示 .exe 文件及所有文件
            # filter="Wuthering Waves (Wuthering Waves.exe);;Executable Files (*.exe);;All Files (*)"
        )
        if folder:
            logger.debug(f"Selected file: {folder}")
        else:
            logger.debug("No file selected.")

        if not folder or folder == self.customValue:
            return

        # self.__addFolderItem(folder)
        # self.folders.append(folder)
        # paramConfig.set(self.configItem, self.folders)
        # self.folderChanged.emit(self.folders)

        self.__onCustomValueChanged(folder)

    def _updateChoiceLabel(self, value):
        if not value or value == self.defaultValue:
            self.choiceLabel.setText(self.tr(self.defaultValue))
        else:
            logger.debug(value)
            self.choiceLabel.setText(value)
        self.choiceLabel.adjustSize()

    def __onCustomValueChanged(self, value):
        """ custom color changed slot """
        if not value:
            return
        paramConfig.set(self.configItem, value)
        self.customValue = value
        self.customValueLast = value
        self._updateChoiceLabel(value)
        self.gamePathChanged.emit(value)


class ClickableButton(QWidget):
    def __init__(self, button, parent=None):
        super().__init__(parent)
        self.button = button
        self.layout = QHBoxLayout(self)
        # self.layout.setContentsMargins(0, 0, 0, 0)
        # self.layout.setContentsMargins(0, 1, 0, 6)
        self.layout.setContentsMargins(0, 3, 0, 4)
        # self.layout.setAlignment(Qt.AlignVCenter)
        self.layout.addWidget(self.button)
        # self.setStyleSheet("background: rgba(0, 255, 0, 0.1);")

    def mousePressEvent(self, event):
        # 点整个行区域都能切换 checkbox 状态
        self.button.toggle()
        super().mousePressEvent(event)


class BossNameOptionsSettingCard(FlowExpandSettingCard):
    """ setting card with a group of options """

    optionChanged = Signal(OptionsConfigItem)

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, texts=None,
                 parent=None):
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.configName = configItem.name  # 在配置文件中的key
        self.choiceLabel = QLabel(self)  # 右上角展示选中的枚举名称（枚举的value）
        self.buttonGroup = []  # 存储所有的枚举按钮对象
        self.choiceBosses = []  # 存储被选中的枚举

        self.choiceLabel.setObjectName("titleLabel")
        self.addWidget(self.choiceLabel)

        # create buttons
        # self.viewLayout.setSpacing(19)
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(28, 10, 0, 10)

        # TODO 搜索框 筛选条件

        # for boss in BossNameEnum:
        new_boss = 2  # TODO 增加boss参数，根据版本区最新版本boss数量
        for i, boss in enumerate(reversed(list(BossNameEnum))):
            button = CheckBox(boss.value, self.view)  # 按钮上展示枚举的value，即描述，可国际化
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # button.setStyleSheet("background: rgba(0, 255, 0, 0.1);")
            self.buttonGroup.append(button)
            click_button = ClickableButton(button, self)
            if i < new_boss or boss == BossNameEnum.NightmareMourningAix:
                click_button.setStyleSheet("background: rgba(0, 255, 0, 0.1);")
            self.viewLayout.addWidget(click_button)
            button.setProperty(self.configName, boss)
            button.stateChanged.connect(lambda state, cb=button: self.__onButtonClicked(cb))

        # self.setExpand(True)

        self._adjustViewSize()
        self.setValue(paramConfig.get(self.configItem), block_signal=True)  # 调取配置文件中的枚举名列表来初始化当前实例变量的值，并展示到页面上
        configItem.valueChanged.connect(self.setValue) # 配置中的值被其他地方修改了，通知这个页面同步刷新

    def __onButtonClicked(self, button: CheckBox):  # 增量修改，全量刷新和保存
        """ button clicked slot """
        value = button.property(self.configName)  # 按钮绑定的是枚举对象
        self.updateChoiceBosses(value, button.isChecked())
        self.updateChoiceLabel()
        paramConfig.set(self.configItem, [item.name for item in self.choiceBosses])
        self.optionChanged.emit(self.configItem)

    def setValue(self, values, block_signal=False):  # 全量覆盖，全量刷新和保存
        """ select button according to the value """
        # if update_config:
        #     paramConfig.set(self.configItem, values) # 配置文件存的是字符串列表，枚举对象的name
        self.choiceBosses.clear()
        for button in self.buttonGroup:
            value = button.property(self.configName)  # 按钮绑定的是枚举对象
            # isChecked = value.name in values
            isChecked = value in values
            if block_signal:
                button.blockSignals(True)
                button.setChecked(isChecked)
                button.blockSignals(False)
            else:
                button.setChecked(isChecked)
            self.updateChoiceBosses(value, isChecked)  # 这个按钮是否选中，先更新实例变量
        self.updateChoiceLabel()  # 再一次将实例变量中维护的所选枚举值拼接，并展示到页面右上角

    def updateChoiceBosses(self, value: str | BossNameEnum, isChecked: bool):
        if isinstance(value, str):
            value = BossNameEnum[value]
        elif not isinstance(value, BossNameEnum):
            raise TypeError(f"value {value} is not BossNameEnum or str")
        if isChecked:
            if value not in self.choiceBosses:
                self.choiceBosses.append(value)
        else:
            try:
                self.choiceBosses.remove(value)
            except ValueError:
                pass

    def getChoiceLabelText(self):
        return ", ".join(self.tr(item.value) for item in self.choiceBosses)

    def updateChoiceLabel(self):
        # 更新右上展示选择的枚举的值并翻译
        self.choiceLabel.setText(self.getChoiceLabelText())
        self.choiceLabel.adjustSize()

    def createTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self.parent().parent().parent().parent().parent()
        )


class BossLevelOptionsSettingCard(ExpandSettingCard):
    """ setting card with a group of options """

    optionChanged = Signal(OptionsConfigItem)

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, texts=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.texts = texts or []
        self.configItem = configItem
        self.configName = configItem.name
        self.choiceLabel = QLabel(self)
        self.buttonGroup = QButtonGroup(self)

        self.choiceLabel.setObjectName("titleLabel")
        self.addWidget(self.choiceLabel)

        # create buttons
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(48, 18, 0, 18)
        for text, option in zip(texts, configItem.options):
            button = RadioButton(text, self.view)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # button.setStyleSheet("background: rgba(0, 255, 0, 0.1);")
            self.buttonGroup.addButton(button)
            self.viewLayout.addWidget(ClickableButton(button, self))
            # self.viewLayout.addWidget(button)
            button.setProperty(self.configName, option)

        self._adjustViewSize()
        self.setValue(paramConfig.get(self.configItem))
        # configItem.valueChanged.connect(self.setValue)
        self.buttonGroup.buttonClicked.connect(self.__onButtonClicked)

    def __onButtonClicked(self, button: RadioButton):
        """ button clicked slot """
        if button.text() == self.choiceLabel.text():
            return

        value = button.property(self.configName)
        paramConfig.set(self.configItem, value)

        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()
        self.optionChanged.emit(self.configItem)

    def setValue(self, value):
        """ select button according to the value """
        paramConfig.set(self.configItem, value)

        for button in self.buttonGroup.buttons():
            isChecked = button.property(self.configName) == value
            button.setChecked(isChecked)

            if isChecked:
                self.choiceLabel.setText(button.text())
                self.choiceLabel.adjustSize()


class ParamComboBoxSettingCard(SettingCard):
    """ Setting card with a combo box """

    def __init__(self, configItem: OptionsConfigItem, icon: Union[str, QIcon, FluentIconBase], title, content=None,
                 texts=None, parent=None):
        """
        Parameters
        ----------
        configItem: OptionsConfigItem
            configuration item operated by the card

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        texts: List[str]
            the text of items

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.optionToText = {o: t for o, t in zip(configItem.options, texts)}
        for text, option in zip(texts, configItem.options):
            self.comboBox.addItem(text, userData=option)

        self.comboBox.setCurrentText(self.optionToText[paramConfig.get(configItem)])
        self.comboBox.currentIndexChanged.connect(self._onCurrentIndexChanged)
        configItem.valueChanged.connect(self.setValue)

    def _onCurrentIndexChanged(self, index: int):

        paramConfig.set(self.configItem, self.comboBox.itemData(index))

    def setValue(self, value):
        if value not in self.optionToText:
            return

        self.comboBox.setCurrentText(self.optionToText[value])
        paramConfig.set(self.configItem, value)


class FolderItem(QWidget):
    """ Folder item """

    removed = Signal(QWidget)

    def __init__(self, folder: str, parent=None):
        super().__init__(parent=parent)
        self.folder = folder
        self.hBoxLayout = QHBoxLayout(self)
        self.folderLabel = QLabel(folder, self)
        self.removeButton = ToolButton(FIF.CLOSE, self)

        self.removeButton.setFixedSize(39, 29)
        self.removeButton.setIconSize(QSize(12, 12))

        self.setFixedHeight(53)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.hBoxLayout.setContentsMargins(48, 0, 60, 0)
        self.hBoxLayout.addWidget(self.folderLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.removeButton, 0, Qt.AlignRight)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        self.removeButton.clicked.connect(
            lambda: self.removed.emit(self))


class ParamInterface(ScrollArea):
    """ Config interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Param"), self)

        # Task
        self.bossGroup = SettingCardGroup(
            self.tr('Boss Rush Parameters'), self.scrollWidget)

        # self.bossNameCard = BossNameOptionsSettingCard(
        #     paramConfig.bossName,
        #     FIF.LABEL,
        #     # self.tr('选择刷哪些boss'),
        #     self.tr('Target Boss Names'),
        #     self.tr("可任选。日常可刷梦魇哀声鸷来合成1c3c。梦魇或副本内boss建议单刷。"),
        #     # self.tr("Choose any bosses, suggested: one for instances and nightmare, three for open world"),
        #     texts=None,
        #     parent=self.bossGroup
        # )

        # self.bossLevelCard = ParamComboBoxSettingCard(
        #     paramConfig.bossLevel,
        #     FIF.LABEL,
        #     self.tr('Target Boss Level'),
        #     self.tr('Select the lowest boss level that can drop Echo'),
        #     texts=["40", "50", "60", "70", "80", "90", "Auto"],
        #     parent=self.bossGroup
        # )

        self.bossLevelCard = BossLevelOptionsSettingCard(
            paramConfig.bossLevel,
            FIF.LABEL,
            self.tr('Target Boss Level'),
            self.tr('Default auto is the lowest boss level that drops Echo; changing it makes it faster'),
            texts=["Lv 40", "Lv 50", "Lv 60", "Lv 70", "Lv 80", "Lv 90", "Auto"],
            parent=self.bossGroup
        )

        # self.comboSequenceCard = ComboSequenceSettingCard(
        #     paramConfig.comboSequence,
        #     FIF.CODE,
        #     # self.tr('定时重启游戏'),
        #     # self.tr('每隔一段时间重启一次游戏，仅对刷boss任务有效'),
        #     self.tr("Combo Sequence"),
        #     self.tr("释放技能顺序,逗号分隔,e,q,r为技能,l(小写L)为闪避, a为普攻(默认连点0.3秒),数字为间隔时间,a~0.5为普攻按下0.5秒,a(0.5)为连续普攻0.5秒，摩托车短按用q~0.1"),
        #     self.bossGroup
        # )

        self.autoRestartPeriodCard = AutoRestartPeriodSettingCard(
            paramConfig.autoRestartPeriod,
            FIF.STOP_WATCH,
            # self.tr('定时重启游戏'),
            # self.tr('每隔一段时间重启一次游戏，仅对刷boss任务有效'),
            self.tr("Scheduled Game Restart"),
            self.tr("Restart the game at regular intervals. This only applies to the Boss Rush task"),
            self.bossGroup
        )

        self.autoCombatCard = AutoCombatSwitchSettingCard(
            FIF.LABEL,
            self.tr('智能连招Beta'),
            self.tr('默认开启，支持任意角色，不限人数，建议带一个奶。'),
            configItem=paramConfig.autoCombat,
            parent=self.bossGroup
        )

        # game folders
        self.gameGroup = SettingCardGroup(
            self.tr("Game Parameters"), self.scrollWidget)

        self.gamePathCard = GamePathSettingCard(
            paramConfig.gamePath,
            FIF.FOLDER,
            self.tr("Installation Directory"),
            self.tr("If you play multiple games, configure this accordingly"),
            self.gameGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('paramInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        self.gameGroup.addSettingCard(self.gamePathCard)

        # self.bossGroup.addSettingCard(self.bossNameCard)
        self.bossGroup.addSettingCard(self.bossLevelCard)
        # self.bossGroup.addSettingCard(self.comboSequenceCard)
        self.bossGroup.addSettingCard(self.autoCombatCard)
        self.bossGroup.addSettingCard(self.autoRestartPeriodCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)

        self.expandLayout.addWidget(self.bossGroup)
        self.expandLayout.addWidget(self.gameGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        # cfg.appRestartSig.connect(self.__showRestartTooltip)

        # # music in the pc
        # self.gamePathCard.clicked.connect(
        #     self.__onDownloadFolderCardClicked)
        pass


class SimpleCardGroup(QWidget):
    """ Simple Setting card group """

    # adjustChanged = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = ExpandLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setSpacing(2)

        # self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)

    def addSettingCard(self, card: QWidget):
        """ add setting card to group """
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()

    def addSettingCards(self, cards: List[QWidget]):
        """ add setting cards to group """
        for card in cards:
            self.addSettingCard(card)

    def adjustSize(self):
        # h = self.cardLayout.heightForWidth(self.width()) + 46
        h = self.cardLayout.heightForWidth(self.width()) + 0
        return self.resize(self.width(), h)


class AutoBossParamSettingCard(QWidget):
    """ Config interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.scrollWidget = QWidget()
        # self.expandLayout = ExpandLayout(self.scrollWidget)

        self.expandLayout = ExpandLayout(self)

        # Task
        self.bossGroup = SimpleCardGroup(self)

        self.bossNameCard = BossNameOptionsSettingCard(
            paramConfig.bossName,
            FIF.LABEL,
            # self.tr('选择刷哪些boss'),
            self.tr('Target Boss Names'),
            self.tr("可任选。日常可刷梦魇哀声鸷来合成1c3c。梦魇或副本内boss建议单刷。"),
            # self.tr("Choose any bosses, suggested: one for instances and nightmare, three for open world"),
            texts=None,
            parent=self.bossGroup
        )

        # self.bossNameCard.setExpand(True)

        self.__initWidget()

    def __initWidget(self):
        # self.resize(1000, 800)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setViewportMargins(0, 0, 0, 0)
        # self.setWidget(self.scrollWidget)
        # self.setWidgetResizable(True)
        self.setObjectName('paramInterface')

        # initialize style sheet
        # self.scrollWidget.setObjectName('scrollWidget')
        # self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        # self.__connectSignalToSlot()

    def __initLayout(self):
        # self.settingLabel.move(36, 30)

        # add cards to group
        # self.gameGroup.addSettingCard(self.gamePathCard)

        self.bossGroup.addSettingCard(self.bossNameCard)
        # self.bossGroup.addSettingCard(self.bossLevelCard)
        # self.bossGroup.addSettingCard(self.comboSequenceCard)
        # self.bossGroup.addSettingCard(self.autoCombatCard)
        # self.bossGroup.addSettingCard(self.autoRestartPeriodCard)

        # add setting card group to layout
        # self.expandLayout.setSpacing(28)
        # self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.setAlignment(Qt.AlignTop)

        self.expandLayout.addWidget(self.bossGroup)
        # self.expandLayout.addWidget(self.gameGroup)


class MacroParamSettingCard(ScrollArea):
    """ Config interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # configItem
        self.defaultTemplate = paramConfig.soarToTheBeat_DefaultTemplate
        self.userTemplate = paramConfig.soarToTheBeat_UserTemplate
        self.useUserTemplate = paramConfig.soarToTheBeat_UseUserTemplate

        self.scrollWidget = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        self.defaultTemplateLabel = QLabel(self.tr("预设模板:"), self.scrollWidget)

        self.templates = self.getTemplates()
        self.defaultTemplateComboBox = ComboBox(self.scrollWidget)
        self.defaultTemplateComboBox.addItems(self.templates)
        self.defaultTemplateComboBox.setCurrentIndex(0)

        self.userTemplateLabel = QLabel(
            self.tr("自定义模板  目录: {dir}").format(dir=str(self.getMacroSoarToTheBeatPath())), self.scrollWidget)
        self.userTemplateLabel.setWordWrap(True)

        self.userTemplateComboBox = ComboBox(self.scrollWidget)
        self.userTemplateComboBox.addItems(self.getMacroSoarToTheBeatUserFiles())
        self.userTemplateComboBox.setCurrentIndex(-1)

        self.hBoxLayout = QHBoxLayout()
        # self.hBoxLayout = FlowLayout()

        self.refreshButton = PushButton(self.tr("刷新"), self.scrollWidget, FluentIcon.SYNC)
        self.useUserTemplateButton = CheckBox(self.tr('使用自定义模板'), self.scrollWidget)
        self.aboutFlyoutButton = PushButton(self.tr('关于'), self.scrollWidget)

        self.escLabel = QLabel(self.tr("保存/停止快捷键: ESC"), self.scrollWidget)

        self.__initWidget()
        self.__initParam()

    def __initWidget(self):
        # self.resize(1000, 800)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        # self.setObjectName('paramInterface')

        self.refreshButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        # initialize style sheet
        self.scrollWidget.setObjectName('view')
        StyleSheet.PARAM_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.hBoxLayout.addWidget(self.refreshButton)
        self.hBoxLayout.addWidget(self.useUserTemplateButton)
        self.hBoxLayout.addWidget(self.aboutFlyoutButton)
        self.hBoxLayout.addWidget(self.escLabel)
        self.hBoxLayout.addStretch()
        self.hBoxLayout.setSpacing(15)

        self.vBoxLayout.addWidget(self.defaultTemplateLabel)
        self.vBoxLayout.addWidget(self.defaultTemplateComboBox)
        self.vBoxLayout.addWidget(self.userTemplateLabel)
        self.vBoxLayout.addWidget(self.userTemplateComboBox)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.vBoxLayout.setSpacing(11)
        self.vBoxLayout.setContentsMargins(36, 0, 36, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

    def __connectSignalToSlot(self):
        self.defaultTemplateComboBox.currentTextChanged.connect(self.onDefaultTemplateComboboxTextChanged)
        self.userTemplateComboBox.currentTextChanged.connect(self.onUserTemplateComboboxTextChanged)
        self.refreshButton.clicked.connect(self.onRefreshButtonClicked)
        self.useUserTemplateButton.clicked.connect(self.onUseUserTemplateButtonClicked)
        self.aboutFlyoutButton.clicked.connect(self.showAboutFlyout)
        # globalSignal.taskInfoBarSignal.connect(self.showTaskInfoBar)  # 多个对象会重复多次

    def __initParam(self):
        text = self.defaultTemplate.value
        is_change = False
        if text and text != self.defaultTemplateComboBox.currentText():
            index = self.defaultTemplateComboBox.findText(text)
            if index >= 0:
                self.defaultTemplateComboBox.blockSignals(True)
                self.defaultTemplateComboBox.setCurrentIndex(index)
                self.defaultTemplateComboBox.blockSignals(False)
                is_change = True
        # 没找到匹配的选项，更新成第一个
        if not is_change:
            self.onDefaultTemplateComboboxTextChanged(self.defaultTemplateComboBox.currentText())

        text = self.userTemplate.value
        is_change = False
        if text and text != self.userTemplateComboBox.currentText():
            index = self.userTemplateComboBox.findText(text)
            if index >= 0:
                self.userTemplateComboBox.blockSignals(True)
                self.userTemplateComboBox.setCurrentIndex(index)
                self.userTemplateComboBox.blockSignals(False)
                is_change = True
        # 没找到匹配的选项，更新成空
        if not is_change:
            self.onUserTemplateComboboxTextChanged(None)

        if self.useUserTemplate.value is True:
            self.useUserTemplateButton.blockSignals(True)
            self.useUserTemplateButton.setChecked(True)
            self.useUserTemplateButton.blockSignals(False)

    def onDefaultTemplateComboboxTextChanged(self, text):
        paramConfig.set(self.defaultTemplate, text if text else None)

    def onUserTemplateComboboxTextChanged(self, text):
        paramConfig.set(self.userTemplate, text if text else None)

    def onUseUserTemplateButtonClicked(self):
        paramConfig.set(self.useUserTemplate, self.useUserTemplateButton.isChecked())

    def onRefreshButtonClicked(self):
        fileNames = self.getMacroSoarToTheBeatUserFiles()
        logger.debug(f"fileNames: {fileNames}")
        currentText = self.userTemplateComboBox.currentText()
        logger.debug(f"currentText: {currentText}")
        self.userTemplateComboBox.clear()
        self.userTemplateComboBox.addItems(fileNames)
        if currentText:
            self.userTemplateComboBox.setCurrentText(currentText)
        if self.userTemplateComboBox.currentText() != currentText:
            self.userTemplateComboBox.setCurrentIndex(-1)
            paramConfig.set(self.userTemplate, None)
        self.createTopRightInfoBar(self.tr("Refresh: "), self.tr("Successful"), 300)

    def getMacroSoarToTheBeatPath(self):
        from src.util import file_util
        path = file_util.get_assets_macro_SoarToTheBeat()
        return path

    def getMacroSoarToTheBeatUserFiles(self):
        path = self.getMacroSoarToTheBeatPath()
        fileNames = [f.name for f in path.glob('*.txt')]
        logger.debug(f"fileNames: {fileNames}")
        return fileNames

    def getTemplates(self):
        templates = [
            "02_星云漫游_《论灵魂De Anima》_困难.txt",
            "02_星云漫游_《论灵魂De Anima》_普通.txt",
            "03_星云漫游_《万千星语》_困难.txt",
            "03_星云漫游_《万千星语》_普通.txt",
            "04_星云漫游_《此刻寻光星间》_困难.txt",
            "04_星云漫游_《此刻寻光星间》_普通.txt",
            "05_星云漫游_《致那暖明黄金》_困难.txt",
            "05_星云漫游_《致那暖明黄金》_普通.txt",
            "06_行星探索_《悠忽舞于梦中》_困难.txt",
            "06_行星探索_《悠忽舞于梦中》_普通.txt",
            "07_行星探索_《愿戴荣光坠入天渊》_普通.txt",
            "08_行星探索_《Daisy Crown》_普通.txt",
            "09_行星探索_《逐光筑昼》_普通.txt",
            "10_恒星冒险_《光耀诸天群海》_普通.txt",
            "11_恒星冒险_《于无羁之昼点亮真彩(Throttle Up!)》_普通.txt",
            "12_恒星冒险_《烈阳啊，请见我真名》_普通.txt",
            "13_恒星冒险_《死秽失乐福音》_普通.txt",
            "14_Musedash_《雨后甜点》_普通.txt",
            "15_Musedash_《Final Step！》_普通.txt",
            "16_Musedash_《Cthugha》_普通.txt",
        ]
        # 定义难度优先级映射
        difficulty_order = {"简单": 0, "普通": 1, "困难": 2}

        def sort_key(filename):
            # 提取序号（前两个字符）
            num = int(filename[:2])

            # 提取难度（在最后一个下划线和 .txt 之间）
            parts = filename[:-4].split('_')  # 去掉.txt后按_分割
            difficulty = parts[-1]  # 最后一部分就是难度

            # 返回排序元组
            return num, difficulty_order.get(difficulty, 9)

        templates.sort(key=sort_key)
        return templates

    def createTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_LEFT,
            duration=duration,
            parent=self
        )

    def showAboutFlyout(self):
        Flyout.create(
            # icon=InfoBarIcon.INFORMATION,
            title='关于:',
            content=self.tr(
                '模板为人工录制，本身并不完美，因设备、网络等影响，可能存在极小的正负延迟，对不上轴ESC重跑即可，都能3S全奖励。' +
                '作者也打不出100%，部分歌曲只有90%+，欢迎使用录制功能，将你的模板文件、结算分数、按键设置截图打包分享到群里，由群主校准后合进脚本内。\n' +
                '角色选陆赫斯/莫宁，默认按键0延迟。\n' +
                '请勿直接修改预设模板，有问题先检查选项是否勾选正确'
            ),
            target=self.aboutFlyoutButton,
            parent=self.window()
        )


class DailyTaskSettingCard(ScrollArea):
    """ Config interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__initData()

        self.scrollWidget = QWidget(self)

        self.mainLayout = QHBoxLayout(self.scrollWidget)

        self.contentVLayout = QVBoxLayout()
        self.contentTitleLabel = QLabel(self.tr("任务设置"), self.scrollWidget)
        self.gridLayout = QGridLayout()
        self.__initGridLayout()

        self.sideVLayout = QVBoxLayout()
        self.sideTitleLabel = QLabel(self.tr("基础设置"), self.scrollWidget)
        self.langHLayout = QHBoxLayout()
        self.langLabel = QLabel(self.tr("游戏文本:"), self.scrollWidget)
        self.langComboBox = ComboBox(self.scrollWidget)
        self.langComboBox.setPlaceholderText(self.tr("{text} - {sign}").format(
            text=self.langDesc[0], sign=self.lang[0].value))
        for i in range(len(self.lang)):
            self.langComboBox.addItem(self.tr("{text} - {sign}").format(
                text=self.langDesc[i], sign=self.lang[i].value), userData=self.lang[i].value)
            if i > 1:
                self.langComboBox.setItemEnabled(self.langComboBox.count() - 1, False)
        # self.gamePathHLayout = QHBoxLayout()
        # self.gamePathLabel = QLabel(self.tr("游戏路径:"), self.scrollWidget)
        # self.gamePathComboBox = ComboBox(self.scrollWidget)
        # TODO 订阅消息总线，实时写入当前任务消息
        self.messageEdit = TextEdit(self.scrollWidget)

        # self.descriptionEdit.setReadOnly(True)
        # self.descriptionEdit.setHtml("""
        #                 <h3>版本活动</h3>
        #
        #                 <ul>
        #                 <li>双倍无音区</li>
        #                 </ul>
        #                 """)

        self.contentBottomLayout = QHBoxLayout()
        self.resetButton = PushButton(self.tr("重置"), self.scrollWidget)
        self.aboutFlyoutButton = PushButton(self.tr('关于'), self.scrollWidget)

        self.__initWidget()
        self.__loadConfig()

    def __initData(self):
        from src.core.i18n import I18nText, I18nTr, Language

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
        # try:
        #     self.curLang = Language(paramConfig.get(paramConfig.gameLanguage))
        # except Exception:
        #     self.curLang = Language.ZH
        self.curLang = Language.ZH

        self.i18ntr = I18nTr(self.curLang)

        # 周本副本名，保存用，后端用，倒叙，最新在前
        self.weeklyChallenge = [
            I18nText.SeedOfIllusoryOrigin,
            I18nText.GateOfTheLostStar,
            I18nText.CinderniteApocalypse,
            I18nText.TheWheelOfBrokenFate,
            I18nText.BeyondTheCrimsonCurtain,
            I18nText.TheFatedConfrontation,
            I18nText.StatueOfTheCrownless,
            I18nText.ChaoticJuncture,
            I18nText.BellOfArchaicChants,
        ]
        # 周本boss名，展示用，仅前端用
        self.weeklyBoss = [
            I18nText.WeeklyBossDenia,
            I18nText.WeeklyBossSigillum,
            I18nText.WeeklyBossThrenodianLeviathan,
            I18nText.WeeklyBossFleurdelys,
            I18nText.WeeklyBossHecate,
            I18nText.WeeklyBossJue,
            I18nText.WeeklyBossCrownless,
            I18nText.WeeklyBossScarAberrantNightmare,
            I18nText.WeeklyBossBellBorneGeochelone,
        ]
        # 武器、角色升级素材
        self.weapon = [
            I18nText.Sword,
            I18nText.Rectifier,
            I18nText.Broadblade,
            I18nText.Gauntlets,
            I18nText.Pistols,
        ]
        self.forgeryChallenge = [
            I18nText.FallenSanctum,
            I18nText.LessonInSunset,
            I18nText.StrickenSanctum,
            I18nText.LessonInVoid,
            I18nText.LessonInEmbers,
            I18nText.GardenOfSalvation,
            I18nText.AbyssOfInitiation,
            I18nText.GardenOfAdoration,
            I18nText.AbyssOfSacrifice,
            I18nText.AbyssOfConfession,
            I18nText.FlamingRemnants,
            I18nText.MistyForest,
            I18nText.ErodedRuins,
            I18nText.MoonlitGroves,
            I18nText.MarigoldWoods,
        ]
        self.bossChallenge = [
            I18nText.EnemyNamelessExplorer,
            I18nText.EnemyHyvatia,
            I18nText.EnemyReactorHusk,
            I18nText.EnemyLadyOfTheSea,
            I18nText.EnemyTheFalseSovereign,
            I18nText.EnemyFenrico,
            I18nText.EnemyLionessOfGlory,
            I18nText.EnemyDragonOfDirge,
            I18nText.EnemyLorelei,
            I18nText.EnemySentryConstruct,
            I18nText.EnemyCrownless,
            I18nText.EnemyThunderingMephis,
            I18nText.EnemyTempestMephis,
            I18nText.EnemyInfernoRider,
            I18nText.EnemyFeilianBeringal,
            I18nText.EnemyMourningAix,
            I18nText.EnemyImpermanenceHeron,
            I18nText.EnemyLampylumenMyriad,
            I18nText.EnemyMechAbomination,
            I18nText.EnemyFallacyOfNoReturn,
        ]
        self.tacetSuppression = [
            I18nText.TacetFieldSolisiaLanding,
            I18nText.TacetFieldFrostlandsTransitPort,
            I18nText.TacetFieldMountGjallar,
            I18nText.TacetFieldMawburrowDesert,
            I18nText.TacetFieldStagnantRun,
        ]
        self.nightmarePurification = [
        ]
        self.tacetDiscordNest = [
            I18nText.StarblindCrashsiteTacetDiscordNest,
            I18nText.RebirthUplandsTacetDiscordNest,
            I18nText.StagnantRunTacetDiscordNest,
        ]

    def __initGridLayout(self):
        # self.weeklyChallengeCheckBox.setStyleSheet("QCheckBox { border: 2px solid red; }")
        self.weeklyChallengeCheckBox = CheckBox(self.tr("周本:"), self.scrollWidget)
        self.weeklyChallengeComboBox = ComboBox(self.scrollWidget)
        self.weeklyChallengeComboBox.addItem(self.tr("不选择"), userData=None)
        # self.weeklyChallengeComboBox.addItem(self.tr("自动 - 最新BOSS"), userData="Auto")
        for i in range(len(self.weeklyChallenge)):
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.weeklyChallenge[i]).raw, boss=self.i18ntr(self.weeklyBoss[i]).raw)
            self.weeklyChallengeComboBox.addItem(text, userData=self.weeklyChallenge[i])
            if i > 3:
                self.weeklyChallengeComboBox.setItemEnabled(self.weeklyChallengeComboBox.count() - 1, False)
        self.weeklyChallengeComboBox.setCurrentIndex(0)

        self.tacetSuppressionCheckBox = CheckBox(self.tr("声骸材料:"), self.scrollWidget)
        self.tacetSuppressionComboBox = ComboBox(self.scrollWidget)
        self.tacetSuppressionComboBox.addItem(self.tr("不选择"), userData=None)
        for i in range(len(self.tacetSuppression)):
            text = self.tr(self.i18ntr(self.tacetSuppression[i]).raw)
            self.tacetSuppressionComboBox.addItem(text, userData=self.tacetSuppression[i])
            if i > 1:
                self.tacetSuppressionComboBox.setItemEnabled(self.tacetSuppressionComboBox.count() - 1, False)

        self.forgeryChallengeCheckBox = CheckBox(self.tr("武器及技能材料:"), self.scrollWidget)
        self.forgeryChallengeComboBox = ComboBox(self.scrollWidget)
        self.forgeryChallengeComboBox.addItem(self.tr("不选择"), userData=None)
        for i in range(len(self.forgeryChallenge)):
            text = self.tr("{challenge} - {weapon}").format(
                challenge=self.i18ntr(self.forgeryChallenge[i]).raw,
                weapon=self.i18ntr(self.weapon[i % len(self.weapon)]).raw
            )
            self.forgeryChallengeComboBox.addItem(text, userData=self.forgeryChallenge[i])
            if i > 4:
                self.forgeryChallengeComboBox.setItemEnabled(self.forgeryChallengeComboBox.count() - 1, False)

        self.bossChallengeCheckBox = CheckBox(self.tr("共鸣者突破材料:"), self.scrollWidget)
        self.bossChallengeComboBox = ComboBox(self.scrollWidget)
        self.bossChallengeComboBox.addItem(self.tr("不选择"), userData=None)
        for i in range(len(self.bossChallenge)):
            self.bossChallengeComboBox.addItem(self.i18ntr(self.bossChallenge[i]).raw, userData=self.bossChallenge[i])
            if i > -1:
                self.bossChallengeComboBox.setItemEnabled(self.bossChallengeComboBox.count() - 1, False)

        self.nightmarePurificationCheckBox = CheckBox(self.tr("梦魇聚落:"), self.scrollWidget)
        self.nightmarePurificationComboBox = ComboBox(self.scrollWidget)
        self.nightmarePurificationComboBox.addItem(self.tr("不选择"), userData=None)
        self.nightmarePurificationComboBox.addItem(self.tr("全选"), userData="All")
        self.nightmarePurificationComboBox.setItemEnabled(self.nightmarePurificationComboBox.count() - 1, False)
        for i in range(len(self.nightmarePurification)):
            self.nightmarePurificationComboBox.addItem(
                self.i18ntr(self.nightmarePurification[i]).raw,
                userData=self.nightmarePurification[i])
        self.tacetDiscordNestCheckBox = CheckBox(self.tr("残象聚落:"), self.scrollWidget)
        self.tacetDiscordNestComboBox = ComboBox(self.scrollWidget)
        self.tacetDiscordNestComboBox.addItem(self.tr("不选择"), userData=None)
        self.tacetDiscordNestComboBox.addItem(self.tr("全选"), userData="All")
        # for i in range(len(self.tacetDiscordNest)):
        #     self.tacetDiscordNestComboBox.addItem(self.i18ntr(self.tacetDiscordNest[i]).raw, userData=self.tacetDiscordNest[i])

        self.activityCheckBox = CheckBox(self.tr("活跃度:"), self.scrollWidget)
        self.activityComboBox = ComboBox(self.scrollWidget)
        # self.activityComboBox.addItem(self.tr("不选择"), userData=None)
        self.activityComboBox.addItem(self.tr("自动"), userData="Auto")

        self.mailCheckBox = CheckBox(self.tr("邮件:"), self.scrollWidget)
        self.mailComboBox = ComboBox(self.scrollWidget)
        #         self.mailComboBox.addItem(self.tr("不选择"), userData=None)
        self.mailComboBox.addItem(self.tr("自动"), userData="Auto")

        self.pioneerPodcastCheckBox = CheckBox(self.tr("先约电台:"), self.scrollWidget)
        self.pioneerPodcastComboBox = ComboBox(self.scrollWidget)
        #         self.pioneerPodcastComboBox.addItem(self.tr("不选择"), userData=None)
        self.pioneerPodcastComboBox.addItem(self.tr("自动"), userData="Auto")

        self.buttonGroup = [
            self.tacetSuppressionCheckBox,
            self.forgeryChallengeCheckBox,
            self.bossChallengeCheckBox,
        ]
        self.buttonGroupOpen = [
            paramConfig.tacetSuppressionOpen,
            paramConfig.forgeryChallengeOpen,
            paramConfig.bossChallengeOpen,
        ]
        self.buttonGroupComboBox = [
            self.tacetSuppressionComboBox,
            self.forgeryChallengeComboBox,
            self.bossChallengeComboBox,
        ]

    def __refreshGridLayout(self, index):
        from src.core.i18n import I18nText, I18nTr, Language

        try:
            self.curLang = self.lang[index]
        except Exception:
            self.curLang = Language.ZH

        self.i18ntr = I18nTr(self.curLang)

        for idx in range(self.weeklyChallengeComboBox.count()):
            try:
                i = self.weeklyChallenge.index(self.weeklyChallengeComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.weeklyChallenge[i]).raw, boss=self.i18ntr(self.weeklyBoss[i]).raw)
            self.weeklyChallengeComboBox.setItemText(idx, text)


        for idx in range(self.tacetSuppressionComboBox.count()):
            try:
                i = self.tacetSuppression.index(self.tacetSuppressionComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.tacetSuppression[i]).raw, boss=self.i18ntr(self.tacetSuppression[i]).raw)
            self.tacetSuppressionComboBox.setItemText(idx, text)

        for idx in range(self.forgeryChallengeComboBox.count()):
            try:
                i = self.forgeryChallenge.index(self.forgeryChallengeComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.forgeryChallenge[i]).raw, boss=self.i18ntr(self.forgeryChallenge[i]).raw)
            self.forgeryChallengeComboBox.setItemText(idx, text)

        for idx in range(self.bossChallengeComboBox.count()):
            try:
                i = self.bossChallenge.index(self.bossChallengeComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.bossChallenge[i]).raw, boss=self.i18ntr(self.bossChallenge[i]).raw)
            self.bossChallengeComboBox.setItemText(idx, text)

        for idx in range(self.nightmarePurificationComboBox.count()):
            try:
                i = self.nightmarePurification.index(self.nightmarePurificationComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.nightmarePurification[i]).raw, boss=self.i18ntr(self.nightmarePurification[i]).raw)
            self.nightmarePurificationComboBox.setItemText(idx, text)

        for idx in range(self.tacetDiscordNestComboBox.count()):
            try:
                i = self.tacetDiscordNest.index(self.tacetDiscordNestComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.tacetDiscordNest[i]).raw, boss=self.i18ntr(self.tacetDiscordNest[i]).raw)
            self.tacetDiscordNestComboBox.setItemText(idx, text)


    def __initWidget(self):
        # self.resize(1000, 800)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        # self.setObjectName('paramInterface')

        # self.resetButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        # initialize style sheet
        self.scrollWidget.setObjectName('view')
        StyleSheet.PARAM_INTERFACE.apply(self)

        self.weeklyChallengeCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.tacetSuppressionCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.forgeryChallengeCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.bossChallengeCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.nightmarePurificationCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.tacetDiscordNestCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.activityCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.mailCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.contentBottomLayout.addWidget(self.resetButton)
        self.contentBottomLayout.addWidget(self.aboutFlyoutButton)
        self.contentBottomLayout.addStretch()
        self.contentBottomLayout.setSpacing(15)
        self.contentBottomLayout.setContentsMargins(110, 0, 0, 0)

        # grid
        row = 0
        self.gridLayout.addWidget(self.weeklyChallengeCheckBox, row, 0)
        self.gridLayout.addWidget(self.weeklyChallengeComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.tacetSuppressionCheckBox, row, 0)
        self.gridLayout.addWidget(self.tacetSuppressionComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.forgeryChallengeCheckBox, row, 0)
        self.gridLayout.addWidget(self.forgeryChallengeComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.bossChallengeCheckBox, row, 0)
        self.gridLayout.addWidget(self.bossChallengeComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.nightmarePurificationCheckBox, row, 0)
        self.gridLayout.addWidget(self.nightmarePurificationComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.tacetDiscordNestCheckBox, row, 0)
        self.gridLayout.addWidget(self.tacetDiscordNestComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.activityCheckBox, row, 0)
        self.gridLayout.addWidget(self.activityComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.mailCheckBox, row, 0)
        self.gridLayout.addWidget(self.mailComboBox, row, 1)

        row += 1
        self.gridLayout.addWidget(self.pioneerPodcastCheckBox, row, 0)
        self.gridLayout.addWidget(self.pioneerPodcastComboBox, row, 1)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setHorizontalSpacing(10)
        # self.gridLayout.setVerticalSpacing(8)
        self.gridLayout.setAlignment(Qt.AlignVCenter)

        # column stretch
        self.gridLayout.setColumnStretch(0, 0)
        self.gridLayout.setColumnStretch(1, 0)
        # self.gridLayout.setColumnStretch(2, 1)
        # self.gridLayout.setColumnStretch(3, 0)  # button
        # self.gridLayout.setColumnStretch(4, 2)  # description（最大吃空间）

        self.contentVLayout.addWidget(self.contentTitleLabel)
        self.contentVLayout.addLayout(self.gridLayout)
        self.contentVLayout.addLayout(self.contentBottomLayout)

        self.langHLayout.addWidget(self.langLabel)
        self.langHLayout.addWidget(self.langComboBox, 1)
        self.langHLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.sideVLayout.addWidget(self.sideTitleLabel)
        self.sideVLayout.addLayout(self.langHLayout)
        self.sideVLayout.addWidget(self.messageEdit, 1)

        self.mainLayout.addLayout(self.contentVLayout, 2)
        self.mainLayout.addSpacing(36)
        self.mainLayout.addLayout(self.sideVLayout, 1)
        self.mainLayout.setContentsMargins(48, 10, 48, 10)
        self.mainLayout.setAlignment(Qt.AlignVCenter)

    def __connectSignalToSlot(self):
        self.weeklyChallengeCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.weeklyChallengeOpen, checked))
        for idx, cb in enumerate(self.buttonGroup):
            cb.toggled.connect(lambda checked, c=cb, i=idx: self.onCheckboxGroupChanged(c, i, checked))
        self.nightmarePurificationCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.nightmarePurificationOpen, checked))
        self.tacetDiscordNestCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.tacetDiscordNestOpen, checked))
        self.activityCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.activityOpen, checked))
        self.mailCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.mailOpen, checked))
        self.pioneerPodcastCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.pioneerPodcastOpen, checked))

        self.weeklyChallengeComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.weeklyChallenge, self.weeklyChallengeComboBox.currentData()))
        self.tacetSuppressionComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.tacetSuppression, self.tacetSuppressionComboBox.currentData()))
        self.forgeryChallengeComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.forgeryChallenge, self.forgeryChallengeComboBox.currentData()))
        self.bossChallengeComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.bossChallenge, self.bossChallengeComboBox.currentData()))
        self.nightmarePurificationComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.nightmarePurification, self.nightmarePurificationComboBox.currentData()))
        self.tacetDiscordNestComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.tacetDiscordNest, self.tacetDiscordNestComboBox.currentData()))
        self.activityComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.activity, self.activityComboBox.currentData()))
        self.mailComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.mail, self.mailComboBox.currentData()))
        self.pioneerPodcastComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.pioneerPodcast, self.pioneerPodcastComboBox.currentData()))

        def _onLangComboBoxChanged(index):
            paramConfig.set(paramConfig.gameLanguage, self.langComboBox.currentData())
            # self.__refreshGridLayout(index)

        self.langComboBox.currentIndexChanged.connect(_onLangComboBoxChanged)

        self.resetButton.clicked.connect(self.onResetButtonClicked)
        self.aboutFlyoutButton.clicked.connect(self.showAboutFlyout)

    def __loadConfig(self):
        self.weeklyChallengeCheckBox.setChecked(paramConfig.get(paramConfig.weeklyChallengeOpen))
        self.tacetSuppressionCheckBox.setChecked(paramConfig.get(paramConfig.tacetSuppressionOpen))
        self.forgeryChallengeCheckBox.setChecked(paramConfig.get(paramConfig.forgeryChallengeOpen))
        self.bossChallengeCheckBox.setChecked(paramConfig.get(paramConfig.bossChallengeOpen))
        self.nightmarePurificationCheckBox.setChecked(paramConfig.get(paramConfig.nightmarePurificationOpen))
        self.tacetDiscordNestCheckBox.setChecked(paramConfig.get(paramConfig.tacetDiscordNestOpen))
        self.activityCheckBox.setChecked(paramConfig.get(paramConfig.activityOpen))
        self.mailCheckBox.setChecked(paramConfig.get(paramConfig.mailOpen))
        self.pioneerPodcastCheckBox.setChecked(paramConfig.get(paramConfig.pioneerPodcastOpen))

        self.weeklyChallengeComboBox.setCurrentIndex(
            self.weeklyChallengeComboBox.findData(paramConfig.get(paramConfig.weeklyChallenge)))
        self.tacetSuppressionComboBox.setCurrentIndex(
            self.tacetSuppressionComboBox.findData(paramConfig.get(paramConfig.tacetSuppression)))
        self.forgeryChallengeComboBox.setCurrentIndex(
            self.forgeryChallengeComboBox.findData(paramConfig.get(paramConfig.forgeryChallenge)))
        self.bossChallengeComboBox.setCurrentIndex(
            self.bossChallengeComboBox.findData(paramConfig.get(paramConfig.bossChallenge)))
        self.nightmarePurificationComboBox.setCurrentIndex(
            self.nightmarePurificationComboBox.findData(paramConfig.get(paramConfig.nightmarePurification)))
        self.tacetDiscordNestComboBox.setCurrentIndex(
            self.tacetDiscordNestComboBox.findData(paramConfig.get(paramConfig.tacetDiscordNest)))
        self.activityComboBox.setCurrentIndex(
            self.activityComboBox.findData(paramConfig.get(paramConfig.activity)))
        self.mailComboBox.setCurrentIndex(
            self.mailComboBox.findData(paramConfig.get(paramConfig.mail)))
        self.pioneerPodcastComboBox.setCurrentIndex(
            self.pioneerPodcastComboBox.findData(paramConfig.get(paramConfig.pioneerPodcast)))

        self.langComboBox.setCurrentIndex(
            self.langComboBox.findData(paramConfig.get(paramConfig.gameLanguage)))


    def onResetButtonClicked(self):
        self.weeklyChallengeComboBox.setCurrentIndex(0)
        self.weeklyChallengeCheckBox.setChecked(False)

        self.tacetSuppressionComboBox.setCurrentIndex(0)
        self.tacetSuppressionCheckBox.setChecked(False)

        self.forgeryChallengeComboBox.setCurrentIndex(0)
        self.forgeryChallengeCheckBox.setChecked(False)

        self.bossChallengeComboBox.setCurrentIndex(0)
        self.bossChallengeCheckBox.setChecked(False)

        self.nightmarePurificationComboBox.setCurrentIndex(0)
        self.nightmarePurificationCheckBox.setChecked(False)

        self.tacetDiscordNestComboBox.setCurrentIndex(0)
        self.tacetDiscordNestCheckBox.setChecked(False)

        self.activityComboBox.setCurrentIndex(0)
        self.activityCheckBox.setChecked(False)

        self.mailComboBox.setCurrentIndex(0)
        self.mailCheckBox.setChecked(False)

        self.pioneerPodcastComboBox.setCurrentIndex(0)
        self.pioneerPodcastCheckBox.setChecked(False)

    def onCheckboxGroupChanged(self, cb, idx, checked):
        # logger.info(f"onCheckboxGroupChanged: {cb.text()} {checked}")
        for i in range(len(self.buttonGroup)):
            if checked:
                if i == idx:
                    self.buttonGroupComboBox[i].setEnabled(True)
                    paramConfig.set(self.buttonGroupOpen[i], True)
                else:
                    self.buttonGroupComboBox[i].setEnabled(False)
                    self.buttonGroup[i].blockSignals(True)
                    self.buttonGroup[i].setChecked(False)
                    self.buttonGroup[i].blockSignals(False)
                    paramConfig.set(self.buttonGroupOpen[i], False)
            else:
                self.buttonGroupComboBox[i].setEnabled(True)
                paramConfig.set(self.buttonGroupOpen[i], False)

    def createTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_LEFT,
            duration=duration,
            parent=self
        )

    def showAboutFlyout(self):
        Flyout.create(
            # icon=InfoBarIcon.INFORMATION,
            title='关于:',
            content=self.tr(
                '测试版，仅开放部分关卡。有问题及时群里反馈，最好录屏，或者截图游戏窗口和脚本日志，遮住uid。'
                '\n使用前建议关闭微星小飞机、英伟达统计数据、Mod等，避免遮挡游戏ui影响识别'
            ),
            target=self.aboutFlyoutButton,
            parent=self.window()
        )
