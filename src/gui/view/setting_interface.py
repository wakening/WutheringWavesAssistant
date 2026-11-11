# coding:utf-8
import logging
from typing import Union

from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme, Dialog, MessageBox,
                            ExpandSettingCard, FluentIconBase, FluentIcon as FIF, InfoBar, RadioButton, qconfig,
                            TableWidget, ListWidget, PushButton, FluentStyleSheet, PrimaryPushButton,
                            ExpandGroupSettingCard, ConfigItem)
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths
from PySide6.QtGui import QDesktopServices, QIcon, QKeySequence
from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QButtonGroup, QTableWidgetItem, QListWidgetItem,
                               QSizePolicy, QHBoxLayout, QVBoxLayout)

from ..common.config import (cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, isWin11, RELEASE_URL, REPO_URL,
                             VERSION_URLS, paramConfig)
from ..common.globals import globalSignal
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..common.version_control import RemoteVersion
from ..components.my_shortcut_picker import MyShortcutPicker
from ...util import winreg_util

logger = logging.getLogger(__name__)


class ShortcutWidget(MyShortcutPicker):

    def __init__(self, keySequence='Ctrl+Shift+A', text='', dialogTitle='', parent=None):
        super().__init__(keySequence, text, parent)
        if dialogTitle:
            self.setDialogTitle(dialogTitle)
        self.setDialogDescription(self.tr('Press a key or key combination to change this shortcut.'))
        self.setBorderRadius(1)
        row = self.layout()
        row.setContentsMargins(25, 8, 25, 8)
        self.textLabel.setObjectName("textLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)

    def loadKeySequence(self, keySequence):
        if not keySequence:
            return
        self.blockSignals(True)
        self.setKeySequence(keySequence)
        self.blockSignals(False)


class ControlsSettingCard(ExpandSettingCard):
    """ setting card with a group of options """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of setting card

        content: str
            the content of setting card

        parent: QWidget
            parent window
        """
        super().__init__(icon, title, content, parent)

        self.moveForwardWidget = ShortcutWidget('W', self.tr('Move forward'), self.tr('Move forward'), self)
        self.moveBackwardWidget = ShortcutWidget('S', self.tr('Move backward'), self.tr('Move backward'), self)
        self.moveLeftWidget = ShortcutWidget('A', self.tr('Move left'), self.tr('Move left'), self)
        self.moveRightWidget = ShortcutWidget('D', self.tr('Move right'), self.tr('Move right'), self)

        self.resonanceSkillWidget = ShortcutWidget('E', self.tr('Resonance Skill'), self.tr('Resonance Skill'), self)
        self.echoSkillWidget = ShortcutWidget('Q', self.tr('Echo Skill'), self.tr('Echo Skill'), self)
        self.resonanceLiberationWidget = ShortcutWidget('R', self.tr('Resonance Liberation'), self.tr('Resonance Liberation'), self)

        self.teamMember1Widget = ShortcutWidget('1', self.tr('Switch to Team Member 1'), self.tr('Switch to Team Member 1'), self)
        self.teamMember2Widget = ShortcutWidget('2', self.tr('Switch to Team Member 2'), self.tr('Switch to Team Member 2'), self)
        self.teamMember3Widget = ShortcutWidget('3', self.tr('Switch to Team Member 3'), self.tr('Switch to Team Member 3'), self)
        self.teamMember4Widget = ShortcutWidget('4', self.tr('Switch to Team Member 4'), self.tr('Switch to Team Member 4'), self)

        self.jumpWidget = ShortcutWidget('Space', self.tr('Jump'), self.tr('Jump'), self)
        self.pickUpWidget = ShortcutWidget('F', self.tr(r'Pick Up / Interact'), self.tr('Pick Up / Interact'), self)
        self.useUtilityWidget = ShortcutWidget('T', self.tr('Use Utility'), self.tr('Use Utility'), self)
        self.mapWidget = ShortcutWidget('M', self.tr('Map'), self.tr('Map'), self)

        self.resetLayout = QHBoxLayout()
        self.resetButton = PrimaryPushButton(self.tr('Reset All Keybinds'), self)

        self.__initWidget()
        self._adjustViewSize()

    def __initWidget(self):

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        # self.setStyleSheet("border: 2px solid red;")

        self.moveForwardWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.moveBackwardWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.moveLeftWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.moveRightWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.resonanceSkillWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.echoSkillWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.resonanceLiberationWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.teamMember1Widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.teamMember2Widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.teamMember3Widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.teamMember4Widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.jumpWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.pickUpWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.useUtilityWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.mapWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.resetButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.resetLayout.addStretch()
        self.resetLayout.addWidget(self.resetButton)
        self.resetLayout.setContentsMargins(0, 10, 28, 10)

        self.viewLayout.addWidget(self.moveForwardWidget)
        self.viewLayout.addWidget(self.moveBackwardWidget)
        self.viewLayout.addWidget(self.moveLeftWidget)
        self.viewLayout.addWidget(self.moveRightWidget)
        self.viewLayout.addWidget(self.resonanceSkillWidget)
        self.viewLayout.addWidget(self.echoSkillWidget)
        self.viewLayout.addWidget(self.resonanceLiberationWidget)
        self.viewLayout.addWidget(self.teamMember1Widget)
        self.viewLayout.addWidget(self.teamMember2Widget)
        self.viewLayout.addWidget(self.teamMember3Widget)
        self.viewLayout.addWidget(self.teamMember4Widget)
        self.viewLayout.addWidget(self.jumpWidget)
        self.viewLayout.addWidget(self.pickUpWidget)
        self.viewLayout.addWidget(self.useUtilityWidget)
        self.viewLayout.addWidget(self.mapWidget)

        self.viewLayout.addLayout(self.resetLayout)

        # self.viewLayout.addStretch()
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

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
            lambda key: self.__onKeySequenceChanged(key, self.resonanceLiberationWidget,
                                                    paramConfig.shortcutResonanceLiberation))
        self.teamMember1Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.teamMember1Widget, paramConfig.shortcutMember1))
        self.teamMember2Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.teamMember2Widget, paramConfig.shortcutMember2))
        self.teamMember3Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.teamMember3Widget, paramConfig.shortcutMember3))
        self.teamMember4Widget.keySequenceChanged.connect(
            lambda key: self.__onKeySequenceChanged(key, self.teamMember4Widget, paramConfig.shortcutMember4))
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
        self.teamMember1Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutTeamMember1))
        self.teamMember2Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutTeamMember2))
        self.teamMember3Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutTeamMember3))
        self.teamMember4Widget.loadKeySequence(paramConfig.get(paramConfig.shortcutTeamMember4))
        self.jumpWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutJump))
        self.pickUpWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutPickUp))
        self.useUtilityWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutUseUtility))
        self.mapWidget.loadKeySequence(paramConfig.get(paramConfig.shortcutMap))

    def __showResetDialog(self):
        title = self.tr('Reset All Keybinds')
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
        self.teamMember1Widget.reset()
        self.teamMember2Widget.reset()
        self.teamMember3Widget.reset()
        self.teamMember4Widget.reset()
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

        install_path = winreg_util.get_install_path()
        if install_path:
            gamePath = install_path.strip().replace("\\", "/").replace("\\\\", "/")
            gamePathText = self.tr("默认自动获取。例: {gamePath}").format(gamePath=gamePath)
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


class SettingInterface(ScrollArea):
    """ Setting interface """

    remoteVersionFinishedSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        # game setting
        self.gameSettingGroup = SettingCardGroup(self.tr("Game"), self.scrollWidget)
        self.gameKeybindingsCard = ControlsSettingCard(
            FIF.GAME,
            self.tr("Keybindings"),
            self.tr("Please use the same keybindings as in-game"),
            parent=self.gameSettingGroup
        )
        self.gamePathCard = GamePathSettingCard(
            paramConfig.gamePath,
            FIF.FOLDER,
            self.tr("Installation Directory"),
            self.tr("If you play multiple games, configure this accordingly"),
            parent=self.gameSettingGroup
        )

        # personalization
        self.personalGroup = SettingCardGroup(
            self.tr('Personalization'), self.scrollWidget)
        # self.micaCard = SwitchSettingCard(
        #     FIF.TRANSPARENT,
        #     self.tr('Mica effect'),
        #     self.tr('Apply semi transparent to windows and surfaces'),
        #     cfg.micaEnabled,
        #     self.personalGroup
        # )
        self.themeCard = ComboBoxSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personalGroup
        )
        # self.windowSizeCard = OptionsSettingCard(
        #     cfg.windowSize,
        #     FIF.ZOOM,
        #     self.tr("Window size"),
        #     self.tr("Adjust window size"),
        #     texts=[
        #         # "720x720",
        #         self.tr("Default"),
        #     ],
        #     parent=self.personalGroup
        # )
        self.zoomCard = ComboBoxSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('Language'),
            self.tr('Set your preferred language for UI'),
            texts=['简体中文', '繁體中文', 'English', self.tr('Use system setting')],
            parent=self.personalGroup
        )

        # update software
        self.updateSoftwareGroup = SettingCardGroup(
            self.tr("Software update"), self.scrollWidget)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr('Check for updates when the application starts'),
            self.tr('The new version will be more stable and have more features'),
            configItem=cfg.checkUpdateAtStartUpV2,
            parent=self.updateSoftwareGroup
        )

        # application
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        # self.helpCard = HyperlinkCard(
        #     HELP_URL,
        #     self.tr('Open help page'),
        #     FIF.HELP,
        #     self.tr('Help'),
        #     self.tr(
        #         'Discover new features and learn useful tips about wuthering-waves-assistant'),
        #     self.aboutGroup
        # )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'),
            FIF.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve Wuthering Waves Assistant by providing feedback'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('Check update'),
            FIF.INFO,
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + " " + VERSION,
            self.aboutGroup
        )

        self.remoteVersion = RemoteVersion(VERSION_URLS, self.remoteVersionFinishedSignal.emit, self)

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        # self.micaCard.setEnabled(isWin11())

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        # self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        # self.personalGroup.addSettingCard(self.windowSizeCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        self.gameSettingGroup.addSettingCard(self.gameKeybindingsCard)
        self.gameSettingGroup.addSettingCard(self.gamePathCard)

        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        # self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(15)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.gameSettingGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        w = MessageBox(
            self.tr('Restart Required'),
            self.tr('This change requires a restart. Restart now?'),
            self.window()
        )
        if w.exec():
            globalSignal.sysExitSignal.emit(200)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # personalization
        cfg.themeChanged.connect(setTheme)
        # self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
        # self.windowSizeCard.optionChanged.connect(signalBus.windowSizeChanged.emit)

        # about
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))

        self.remoteVersionFinishedSignal.connect(self.showUpdateVersion)
        self.aboutCard.clicked.connect(self.remoteVersion.request)

    def showUpdateVersion(self):
        result = self.remoteVersion.checkVersion()
        if result is None:
            self.remoteVersion.showErrorBar(self.tr("Failed to check for updates"), 5000, self.parent())
            return
        if result is False:
            self.remoteVersion.showInfoBar(self.tr("You're up to date"), 5000, self.parent())
            return
        if result is True:
            msg = self.tr(" * New version available {version}").format(version=self.remoteVersion.version)
            self.remoteVersion.showSuccessBar(msg, 5000, self.parent())
