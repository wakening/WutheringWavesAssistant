# import logging
#
# from PySide6.QtCore import Qt, Signal, QSize, QEvent
# from PySide6.QtGui import QIcon, QColor, QIntValidator
# from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout,
#                                QPushButton, QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout)
# from qfluentwidgets import (FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
#                             InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
#                             SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
#                             OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
#                             SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
#                             LineEdit, SettingCard, ComboBox, ConfigItem,
#                             PushButton, ToolButton, MessageBox, CardWidget)
#
# from src.gui.common.globals import globalSignal
# from src.gui.common.style_sheet import StyleSheet
# from src.gui.common.task import BaseTask, TaskId, ValidationResult
# from src.gui.components.check_box import ReadOnlyCheckBox
#
# logger = logging.getLogger(__name__)
#
#
# class StoryTask(BaseTask):
#
#     def __init__(self, id: str, name: str, widget):
#         super().__init__(id, name)
#         self.widget = widget
#
#     def validate(self, **kwargs) -> ValidationResult:
#         return ValidationResult(success=True)
#
#     def submitTask(self, start: bool):
#         if start:
#             result = self.validate()
#             if result.success:
#                 self._createTopRightInfoBar(self.tr('Task: '), self.name, 5000)
#                 self.submit(start)
#             return result
#         self.submit(start)
#         return None
#
#     def _createTopRightInfoBar(self, title: str, content: str, duration: int):
#         InfoBar.success(
#             title=title,
#             content=content,
#             orient=Qt.Horizontal,
#             isClosable=True,
#             position=InfoBarPosition.TOP_RIGHT,
#             duration=duration,
#             parent=self.widget.parent()
#         )
#
#
# class AutoStorySkipProcessTask(StoryTask):
#
#     def __init__(self, widget):
#         super().__init__(TaskId.AutoStorySkipProcessTask, "SkipStory", widget)
#
#
# # class SkipCard(CardWidget):
# class SkipCard(QWidget):
#
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         self.task = AutoStorySkipProcessTask(self)
#
#         self.mainLayout = QVBoxLayout(self)
#
#         self.checkbox = CheckBox(self.tr("跳过剧情"), self)
#         self.descLabel = QLabel(
#             self.tr("触发剧情后自动帮你点击跳过，任意分辨率"),
#             self
#         )
#         self.descLabel.setWordWrap(True)
#
#         self.descLayout = QHBoxLayout(self)
#         self.descLayout.addWidget(self.descLabel)
#         self.descLayout.setContentsMargins(30, 0, 0, 0)
#
#         self.mainLayout.addWidget(self.checkbox)
#         self.mainLayout.addLayout(self.descLayout)
#
#
# class AutoStoryEnjoyProcessTask(StoryTask):
#
#     def __init__(self, widget):
#         super().__init__(TaskId.AutoStoryEnjoyProcessTask, "AutoStory", widget)
#
#
# # class EnjoyCard(CardWidget):
# class EnjoyCard(QWidget):
#
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         self.task = AutoStoryEnjoyProcessTask(self)
#
#         self.mainLayout = QVBoxLayout(self)
#
#         self.checkbox = CheckBox(self.tr("看剧情-自动剧情"), self)
#         self.descLayout = QVBoxLayout()
#
#         self.enjoyStoryDescLabel = QLabel(
#             self.tr(
#                 "触发剧情后可直接双手离开键盘，自动播放，自动选择对话，直到这段剧情结束。任意分辨率"
#             ),
#             self
#         )
#         self.enjoyStoryDescLabel.setWordWrap(True)
#
#         self.optionLayout = QHBoxLayout()
#
#         self.autoDialogueCheckBox = ReadOnlyCheckBox(self.tr("自动对话"), self)
#         self.autoDialogueCheckBox.setChecked(True)
#
#         self.autoPlayCheckBox = ReadOnlyCheckBox(self.tr("自动播放"), self)
#         self.autoPlayCheckBox.setChecked(True)
#
#         self.optionLayout.addWidget(self.autoDialogueCheckBox)
#         self.optionLayout.addWidget(self.autoPlayCheckBox)
#         self.optionLayout.addStretch()
#
#         self.descLayout.addWidget(self.enjoyStoryDescLabel)
#         self.descLayout.addLayout(self.optionLayout)
#         self.descLayout.setContentsMargins(30, 0, 0, 0)
#
#         self.mainLayout.addWidget(self.checkbox)
#         self.mainLayout.addLayout(self.descLayout)
#
#
# class StoryWidget(ScrollArea):
#
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#
#         self.container = QWidget(self)
#
#         self.mainLayout = QVBoxLayout(self.container)
#
#         self.tipsLabel = QLabel(self.tr("战斗、跑图都需手动操作，不能代肝剧情！"), self.container)
#         self.tipsLabel.setWordWrap(True)
#         self.tipsLabel2 = QLabel(self.tr("请勾选需要的功能项"), self.container)
#
#         self.enjoyCard = EnjoyCard(self.container)
#         self.skipCard = SkipCard(self.container)
#
#         self.enjoyCard.checkbox.setChecked(True)
#
#         self.group = QButtonGroup(self.container)
#         self.group.setExclusive(True)
#         self.group.addButton(self.enjoyCard.checkbox)
#         self.group.addButton(self.skipCard.checkbox)
#
#         self.__initWidget()
#
#         self.currentTask = self.enjoyCard.task
#
#     def __initWidget(self):
#         self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self.setViewportMargins(0, 0, 0, 0)
#         self.setWidget(self.container)
#         self.setWidgetResizable(True)
#         # self.setObjectName('paramInterface')
#
#         # initialize style sheet
#         self.container.setObjectName('view')
#         StyleSheet.PARAM_INTERFACE.apply(self)
#
#         # initialize layout
#         self.__initLayout()
#         self.__connectSignalToSlot()
#         self.__loadConfig()
#
#     def __initLayout(self):
#         self.mainLayout.addWidget(self.tipsLabel)
#         self.mainLayout.addWidget(self.tipsLabel2)
#         self.mainLayout.addWidget(self.enjoyCard)
#         self.mainLayout.addWidget(self.skipCard)
#         self.mainLayout.addStretch()
#         self.mainLayout.setSpacing(20)
#         self.mainLayout.setContentsMargins(16, 26, 16, 10)
#
#     def __connectSignalToSlot(self):
#         self.enjoyCard.checkbox.stateChanged.connect(
#             lambda _: self.__onTaskChecked(self.enjoyCard.checkbox, self.enjoyCard.task))
#         self.skipCard.checkbox.stateChanged.connect(
#             lambda _: self.__onTaskChecked(self.skipCard.checkbox, self.skipCard.task))
#
#     def __onTaskChecked(self, checkbox, currentTask):
#         # logger.debug(f"echo __onTaskChecked: {checkbox.isChecked()}")
#         if checkbox.isChecked():
#             self.currentTask = currentTask
#             globalSignal.taskChangedSignal.emit(currentTask)
#             # logger.debug(f"Current task: {self.currentTask}")
#
#     def __loadConfig(self):
#         pass
