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
from src.gui.common.task import BaseTask, ValidationResult, TaskId

logger = logging.getLogger(__name__)


class EventsTask(BaseTask):

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


class SoarToTheBeatMacroReplayTask(EventsTask):

    def __init__(self, widget):
        super().__init__(TaskId.SoarToTheBeatMacroReplayTask, "MacroReplay", widget)


class SoarToTheBeatMacroReplayWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.task = SoarToTheBeatMacroReplayTask(self)

        self.defaultTemplate = paramConfig.soarToTheBeat_DefaultTemplate
        self.userTemplate = paramConfig.soarToTheBeat_UserTemplate
        self.useUserTemplate = paramConfig.soarToTheBeat_UseUserTemplate

        self.mainLayout = QVBoxLayout(self)

        self.tipsLabel = QLabel(self.tr("启动脚本，回到游戏点击开始，挂机别动直到结束"), self)
        self.tipsLabel.setWordWrap(True)

        self.defaultTemplateLabel = QLabel(self.tr("预设模板:"), self)

        self.templates = self.getTemplates()
        self.defaultTemplateComboBox = ComboBox(self)
        self.defaultTemplateComboBox.addItems(self.templates)
        self.defaultTemplateComboBox.setCurrentIndex(0)

        self.userTemplateLabel = QLabel(
            self.tr("自定义模板  目录: {dir}").format(dir=str(self.getMacroSoarToTheBeatPath())), self)
        self.userTemplateLabel.setWordWrap(True)

        self.userTemplateComboBox = ComboBox(self)
        self.userTemplateComboBox.addItems(self.getMacroSoarToTheBeatUserFiles())
        self.userTemplateComboBox.setCurrentIndex(-1)

        self.hBoxLayout = QHBoxLayout()

        self.refreshButton = PushButton(self.tr("刷新"), self, FluentIcon.SYNC)
        self.useUserTemplateButton = CheckBox(self.tr('使用自定义模板'), self)
        self.aboutFlyoutButton = PushButton(self.tr('关于'), self)

        self.escLabel = QLabel(self.tr("保存/停止快捷键: ESC"), self)

        self.__initWidget()
        self.__loadConfig()

    def __initWidget(self):
        # initialize style sheet
        self.setObjectName('view')
        StyleSheet.PARAM_INTERFACE.apply(self)

        self.refreshButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

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

        self.mainLayout.addWidget(self.tipsLabel)
        self.mainLayout.addWidget(self.defaultTemplateLabel)
        self.mainLayout.addWidget(self.defaultTemplateComboBox)
        self.mainLayout.addWidget(self.userTemplateLabel)
        self.mainLayout.addWidget(self.userTemplateComboBox)
        self.mainLayout.addLayout(self.hBoxLayout)
        self.mainLayout.setSpacing(11)
        self.mainLayout.setContentsMargins(36, 0, 36, 0)
        self.mainLayout.setAlignment(Qt.AlignVCenter)

    def __connectSignalToSlot(self):
        self.defaultTemplateComboBox.currentTextChanged.connect(self.onDefaultTemplateComboboxTextChanged)
        self.userTemplateComboBox.currentTextChanged.connect(self.onUserTemplateComboboxTextChanged)
        self.refreshButton.clicked.connect(self.onRefreshButtonClicked)
        self.useUserTemplateButton.clicked.connect(self.onUseUserTemplateButtonClicked)
        self.aboutFlyoutButton.clicked.connect(self.showAboutFlyout)

    def __loadConfig(self):
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
                '游戏卡顿，节奏无法对齐的，应降低游戏分辨率和画质，如1600x900极致性能60fps60fps60fps，保证流畅。\n' +
                '请勿直接修改预设模板，有问题先检查选项是否勾选正确'
            ),
            target=self.aboutFlyoutButton,
            parent=self.window()
        )


class SoarToTheBeatMacroRecordTask(EventsTask):

    def __init__(self, widget):
        super().__init__(TaskId.SoarToTheBeatMacroRecordTask, "MacroRecord", widget)


class SoarToTheBeatMacroRecordWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.task = SoarToTheBeatMacroRecordTask(self)

        self.mainLayout = QVBoxLayout(self)

        self.tipsLabel = QLabel(
            self.tr("启动脚本，回到游戏点击开始，正常操作即可，快捷键ESC可退出并保存，直接点停止不保存"), self)
        self.tipsLabel.setWordWrap(True)

        self.savePathLabel = QLabel(
            self.tr("保存目录: {dir}").format(dir=str(self.getMacroSoarToTheBeatPath())), self)
        self.savePathLabel.setWordWrap(True)
        # self.escLabel = QLabel(self.tr("保存/停止快捷键: ESC"), self)

        self.__initWidget()

    def __initWidget(self):
        # initialize style sheet
        self.setObjectName('view')
        StyleSheet.PARAM_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.mainLayout.addWidget(self.tipsLabel)
        self.mainLayout.addWidget(self.savePathLabel)
        # self.mainLayout.addWidget(self.escLabel)
        self.mainLayout.setSpacing(11)
        self.mainLayout.setContentsMargins(36, 0, 36, 0)
        self.mainLayout.setAlignment(Qt.AlignVCenter)

    def __connectSignalToSlot(self):
        pass

    def __loadConfig(self):
        pass

    def getMacroSoarToTheBeatPath(self):
        from src.util import file_util
        path = file_util.get_assets_macro_SoarToTheBeat()
        return path


class EventsWidget(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.container = QWidget(self)
        self.mainLayout = QVBoxLayout(self.container)

        # self.tipsLabel = QLabel(self.tr("活动"), self.container)

        self.soarToTheBeatMacroTitle = QLabel(self.tr("沿着节拍启航:"), self.container)
        self.soarToTheBeatLayout = QVBoxLayout()
        self.soarToTheBeatMacroReplayCheckBox = CheckBox(self.tr("自动音游:"), self.container)
        self.soarToTheBeatMacroReplayWidget = SoarToTheBeatMacroReplayWidget(self.container)
        self.soarToTheBeatMacroReplayCheckBox.setChecked(True)
        self.soarToTheBeatMacroRecordCheckBox = CheckBox(self.tr("录制自定义模板:"), self.container)
        self.soarToTheBeatMacroRecordWidget = SoarToTheBeatMacroRecordWidget(self.container)

        self.group = QButtonGroup(self.container)
        self.group.setExclusive(True)
        self.group.addButton(self.soarToTheBeatMacroReplayCheckBox)
        self.group.addButton(self.soarToTheBeatMacroRecordCheckBox)

        self.__initWidget()

        self.currentTask = self.soarToTheBeatMacroReplayWidget.task

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
        self.__loadConfig()

    def __initLayout(self):
        self.soarToTheBeatLayout.addWidget(self.soarToTheBeatMacroReplayCheckBox)
        self.soarToTheBeatLayout.addWidget(self.soarToTheBeatMacroReplayWidget)
        self.soarToTheBeatLayout.addWidget(self.soarToTheBeatMacroRecordCheckBox)
        self.soarToTheBeatLayout.addWidget(self.soarToTheBeatMacroRecordWidget)
        self.soarToTheBeatLayout.setContentsMargins(16, 10, 16, 10)

        self.mainLayout.addWidget(self.soarToTheBeatMacroTitle)
        self.mainLayout.addLayout(self.soarToTheBeatLayout)
        self.mainLayout.addStretch()
        self.mainLayout.setSpacing(20)
        self.mainLayout.setContentsMargins(16, 26, 16, 10)

    def __connectSignalToSlot(self):
        self.soarToTheBeatMacroReplayCheckBox.stateChanged.connect(
            lambda _: self.__onTaskChecked(self.soarToTheBeatMacroReplayCheckBox,
                                           self.soarToTheBeatMacroReplayWidget.task))
        self.soarToTheBeatMacroRecordCheckBox.stateChanged.connect(
            lambda _: self.__onTaskChecked(self.soarToTheBeatMacroRecordCheckBox,
                                           self.soarToTheBeatMacroRecordWidget.task))

    def __onTaskChecked(self, checkbox, currentTask):
        # logger.debug(f"echo __onTaskChecked: {checkbox.isChecked()}")
        if checkbox.isChecked():
            self.currentTask = currentTask
            globalSignal.taskChangedSignal.emit(currentTask)
            # logger.debug(f"Current task: {self.currentTask}")

    def __loadConfig(self):
        pass
